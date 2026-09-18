// Authoring-only deck builder using the provided Artifact Tool runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const root = process.cwd();
const deps = '/Users/hanyangshen/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=path.join(deps,'node/node_modules');
const skill = '/Users/hanyangshen/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations';
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(deps,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')));
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
let s=slide('Personal Information Management','Opening. Group member names remain pending. Use the allocation in docs/presentation_script.md; every member shows face and student ID at the start of their section.');
text(s,'COMP3211 Software Engineering',64,215,1120,70,36);
text(s,'Notes, tasks, events and contacts\nA local command-line application in Python',64,320,1110,140,34);
text(s,'Group members: TO BE FILLED BY TEAM',64,570,1120,50,26,false,'#596F7F');
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
text(s,'54 tests passed on Python 3.9.6 and 3.12.14.\nModel line coverage: 411 / 413 = 99.52%.',64,463,1160,105,32);
text(s,'Coverage measures execution, not a guarantee of correctness.',64,614,1150,46,25,false,'#596F7F');
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++) {
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
const finalPath=path.join(validated,`validated-${revision}.pptx`);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,
 pythonExecutable:path.join(deps,'python/bin/python3'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 explicitTotalSlideCount:6, requiredNativeTableOwnerSlides:[], requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,`validation-${revision}.json`)});
await fs.copyFile(finalPath,path.join(out,'PIM_presentation.pptx'));
console.log(JSON.stringify(result));
