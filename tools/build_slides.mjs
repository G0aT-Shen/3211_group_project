// Authoring-only deck builder using the provided Artifact Tool runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
if (process.argv.includes('--help')) {
  console.log('Usage: node tools/build_slides.mjs\nOptional environment variables:\n'
    + '  PIM_RUNTIME_DEPS       Authoring runtime dependencies directory\n'
    + '  PIM_PRESENTATION_SKILL Presentation tools directory (contains container_tools/)\n'
    + '  PIM_PYTHON             Python executable for presentation validators\n'
    + '  PIM_SOFFICE            LibreOffice executable for the paired PDF export\n'
    + 'Team names come from docs/team_members.json. Empty members keep the deck a draft.');
  process.exit(0);
}
const deps = path.resolve(process.env.PIM_RUNTIME_DEPS
  || path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies'));
const pythonExecutable = process.env.PIM_PYTHON || path.join(deps, 'python/bin/python3');
const soffice = process.env.PIM_SOFFICE || path.join(deps, 'bin/override/soffice');
const artifactModule = path.join(deps,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs');
try { await fs.access(artifactModule); await fs.access(pythonExecutable); }
catch { throw new Error('Authoring runtime not found. Set PIM_RUNTIME_DEPS and optionally PIM_PYTHON; see --help.'); }
try { await promisify(execFile)(soffice, ['--version'], {timeout:30000}); }
catch { throw new Error('LibreOffice not found or could not start. Set PIM_SOFFICE; see --help.'); }
process.env.RUNTIME_NODE_MODULES=path.join(deps,'node/node_modules');
let skill = process.env.PIM_PRESENTATION_SKILL;
if (!skill) {
  const presentationCache = path.join(process.env.CODEX_HOME || path.join(os.homedir(), '.codex'),
    'plugins/cache/openai-primary-runtime/presentations');
  let versions = [];
  try { versions = (await fs.readdir(presentationCache)).filter(v=>/^\d+(\.\d+)+$/.test(v))
    .sort((a,b)=>b.localeCompare(a,undefined,{numeric:true})); } catch {}
  for (const version of versions) {
    const candidate=path.join(presentationCache,version,'skills/presentations');
    try { await fs.access(path.join(candidate,'container_tools/artifact_tool_utils.mjs')); skill=candidate; break; } catch {}
  }
}
if (!skill) throw new Error('Presentation tools not found. Set PIM_PRESENTATION_SKILL; see --help.');
skill = path.resolve(skill);
for (const resource of ['artifact_tool_utils.mjs', 'inspect_presentation_package_integrity.py',
                        'inspect_presentation_layout_geometry.py']) {
  try { await fs.access(path.join(skill, 'container_tools', resource)); }
  catch { throw new Error(`Missing ${resource}. Check PIM_PRESENTATION_SKILL; see --help.`); }
}
const team = JSON.parse(await fs.readFile(path.join(root, 'docs/team_members.json'), 'utf8'));
if (!team || Array.isArray(team) || Object.keys(team).join() !== 'members' || !Array.isArray(team.members)
  || team.members.some(name=>typeof name !== 'string' || !name.trim() || name !== name.trim()
    || /[\u0000-\u001f]/.test(name) || name.includes('TO BE FILLED BY TEAM')
    || Buffer.from(name, 'utf8').toString('utf8') !== name)
  || new Set(team.members).size !== team.members.length) {
  throw new Error('docs/team_members.json must contain members: an array of unique, nonblank names.');
}
const memberLabel = team.members.length ? team.members.join(', ') : 'TO BE FILLED BY TEAM';
const coverage = await fs.readFile(path.join(root, 'coverage_report.txt'), 'utf8');
const testMatch = coverage.match(/^Tests: (\d+), failures: 0, errors: 0$/m);
const totalMatch = coverage.match(/^TOTAL\s+(\d+)\s+(\d+)\s+([\d.]+)%$/m);
const pythonMatch = coverage.match(/^Python (\S+)$/m);
if (!testMatch || !totalMatch || !pythonMatch) throw new Error('Regenerate a passing coverage_report.txt first.');
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactModule));
const { finalizePresentation } = await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const build=path.join(root,'tmp/slides');
const validated=path.join(build,'published');
const out=path.join(root,'output/presentation');
const revision=Date.now().toString();
await fs.mkdir(validated,{recursive:true}); await fs.mkdir(out,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const font='Arial';
function text(s, value, x,y,w,h,size=30,bold=false,color='#173247') {
  const shape=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=value; shape.text.style={typeface:font,fontSize:size,bold,color,autoFit:'none'};
  return shape;
}
function slide(title, notes) {
  const s=p.slides.add();s.background.fill='#FAFCFD';
  text(s,title,64,48,1152,94,48,true);
  s.speakerNotes.textFrame.setText(notes+'\nSource: Course Project Description, Appendix B and Deliverables 2/5; docs/SRS.md; docs/design.md; coverage_report.txt. AI-assisted draft: disclose in the official declaration.');
  return s;
}
function node(s,label,x,y,w=230,h=80) {
  const shape=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:'#EAF1F5',line:{fill:'#52758D',width:1}});
  shape.text=label;shape.text.style={typeface:font,fontSize:26,color:'#173247',autoFit:'none'};
  return shape;
}
let s=slide('Personal Information Management',`Opening. Group members: ${memberLabel}. Use the allocation in docs/presentation_script.md; every member shows face and student ID at the start of their section.`);
text(s,'COMP3211 Software Engineering',64,215,1120,70,36);
text(s,'Notes, tasks, events and contacts\nA local command-line application in Python',64,320,1110,140,34);
text(s,`Group members: ${memberLabel}`,64,570,1120,85,26,false,'#596F7F');
s=slide('Creating a record','Explain FR-01 and FR-03: required description/deadline, validation before assigning a unique ID. Show the user-visible success and invalid-date result.');
text(s,'FR-03: a task requires a description and deadline',64,172,1150,70,32,true);
text(s,'add task "Submit report"\n    --deadline 2026-11-19 20:00',64,280,1150,130,34);
text(s,'Successful creation returns an ID.\nAn invalid date leaves the collection unchanged.',64,460,1140,120,32);
s=slide('Defining and applying a criterion','Explain the second/third required presentation requirements: define a typed criterion, then search and print ordered matches. Missing fields are False; NOT reverses the result.');
text(s,'FR-07: type and field conditions',64,166,1130,55,32,true);
text(s,'type = task && deadline < 2027-01-01',64,260,1160,80,34);
text(s,'FR-08: combine conditions and search records',64,376,1150,60,32,true);
text(s,'Precedence: ! before && before ||\nParentheses change grouping. Results retain their IDs.',64,478,1150,110,30);
s=slide('Model ownership and independent tests','Describe MVC instantiated in code. Model owns records, factory, collection and search AST. Repl is the controller adapter. IO stays in Storage and Printer. The diagram is editable.');
const main=node(s,'CLI / Repl\nController adapter',466,162,350,95);
const m=node(s,'model\nPIR + manager + search',64,395,350,105);
const st=node(s,'storage\nJSON / atomic save',465,395,350,105);
const v=node(s,'view\nPrinter',866,395,350,105);
for (const target of [m,st,v]) s.shapes.connect(main,target,{kind:'elbow',fromSide:'bottom',toSide:'top',line:{fill:'#52758D',width:2},tail:{type:'arrow',width:'med',length:'med'}});
text(s,'Model contains business rules and has no console or file IO.',64,577,1150,60,30);
s=slide('Searching and updating a record','Walk through the combined example required by Deliverable 2: search for a task, print its ID, edit it, validate a replacement, commit only when all fields pass.');
text(s,'1   User searches by type and deadline',64,180,1130,55,30);
text(s,'2   Parser creates a validated search tree',64,255,1130,55,30);
text(s,'3   Manager returns matches; Printer shows record #2',64,330,1140,55,30);
text(s,'4   User edits #2; Factory validates every changed field',64,405,1140,55,30);
text(s,'5   Manager replaces #2 only after validation succeeds',64,480,1140,55,30);
text(s,'Failed validation preserves the original record.',64,595,1140,50,30,true);
s=slide('A lesson from boundary testing','Explain actual defects: 12 tests originally passed but print abc crashed, unknown edit reported success, quotes were lost. New tests prove boundary behavior. Old trace summary omitted missed lines; corrected coverage includes all model executable lines. Mention no score or correctness guarantee.');
text(s,'Passing tests can leave interface defects undiscovered',64,178,1150,90,34,true);
text(s,'Regression cases now cover invalid IDs, quoted searches,\nfailed edits and failed disk replacement.',64,309,1160,110,30);
text(s,`${testMatch[1]} tests pass locally on Python ${pythonMatch[1]}.\nModel line coverage: ${totalMatch[1]} / ${totalMatch[2]} = ${totalMatch[3]}%.`,64,463,1160,105,32);
text(s,'Coverage measures execution, not a guarantee of correctness.',64,614,1150,46,25,false,'#596F7F');
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++) {
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
const finalPath=path.join(validated,`validated-${revision}.pptx`);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,
 pythonExecutable,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 explicitTotalSlideCount:6, requiredNativeTableOwnerSlides:[], requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,`validation-${revision}.json`)});
await promisify(execFile)(soffice, ['--headless', '--convert-to', 'pdf', '--outdir', validated, finalPath], {timeout:60000});
const pdfPath = finalPath.replace(/\.pptx$/, '.pdf');
const pdf = await fs.readFile(pdfPath);
if (pdf.subarray(0,5).toString() !== '%PDF-') throw new Error('Presentation PDF export is invalid.');
await fs.copyFile(finalPath,path.join(out,'PIM_presentation.pptx'));
await fs.copyFile(pdfPath,path.join(out,'PIM_presentation.pdf'));
const inputs = ['output/presentation/PIM_presentation.pptx', 'output/presentation/PIM_presentation.pdf',
                'docs/team_members.json', 'coverage_report.txt'];
const sha256 = {};
for (const name of inputs) sha256[name] = createHash('sha256').update(await fs.readFile(path.join(root,name))).digest('hex');
await fs.writeFile(path.join(out,'build_manifest.json'), JSON.stringify({schema_version:1,sha256},null,2)+'\n');
console.log(JSON.stringify(result));
