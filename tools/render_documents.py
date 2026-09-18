"""Authoring-only PDF builder. Requires ReportLab, not imported by the PIM app."""
from pathlib import Path
import ast
import math
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf'
STYLES = getSampleStyleSheet()
pdfmetrics.registerFont(TTFont('ArialUnicode', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
STYLES.add(ParagraphStyle('BodyPIM', fontName='ArialUnicode', fontSize=10, leading=13.5, spaceAfter=7))
STYLES.add(ParagraphStyle('CodePIM', fontName='Courier', fontSize=7.4, leading=10, spaceAfter=8))
STYLES.add(ParagraphStyle('CellPIM', fontName='ArialUnicode', fontSize=7.4, leading=10))
INK = colors.HexColor('#162b3c')
BLUE = colors.HexColor('#235d82')
for heading in ['Title', 'Heading1', 'Heading2', 'Heading3']:
    STYLES[heading].keepWithNext = True


def styled(text):
    text = escape(text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)
    return text


def box(d, x, y, w, h, label):
    d.add(Rect(x, y, w, h, strokeColor=BLUE, fillColor=colors.HexColor('#eef4f7'), strokeWidth=1))
    for i, line in enumerate(label.split('\n')):
        d.add(String(x+w/2, y+h/2 + (len(label.split('\n'))-1)*5 - i*11, line, textAnchor='middle', fontName='Helvetica', fontSize=8, fillColor=INK))


def arrow(d, x1, y1, x2, y2, inheritance=False):
    d.add(Line(x1,y1,x2,y2,strokeColor=BLUE))
    length = math.hypot(x2-x1, y2-y1)
    ux, uy = (x2-x1)/length, (y2-y1)/length
    pts = [x2,y2,x2-6*ux-3*uy,y2-6*uy+3*ux,x2-6*ux+3*uy,y2-6*uy-3*ux]
    d.add(Polygon(pts,strokeColor=BLUE,fillColor=colors.white if inheritance else BLUE))


def diagram(kind):
    d=Drawing(480, 250 if kind != 'sequence' else 420)
    if kind == 'architecture':
        box(d,185,215,110,28,'main.py')
        box(d,155,156,170,40,'CLI / Repl\nController adapter')
        arrow(d,240,215,240,196)
        for x,label in [(0,'Command parser'),(175,'Storage adapter'),(350,'Printer / View')]:
            box(d,x,90,130,36,label)
            arrow(d,240,156,x+65,126)
        box(d,60,10,360,48,'Independent model package\nPIR hierarchy / Factory / Manager / Search AST')
        for x in [65,240,415]: arrow(d,x,90,x,58)
        arrow(d,155,156,148,58)
    elif kind == 'classes':
        box(d,175,210,130,30,'PIR (abstract)')
        for x,label in [(10,'TextPIR'),(132,'TaskPIR'),(254,'EventPIR'),(376,'ContactPIR')]:
            box(d,x,151,100,28,label)
            d.add(Line(x+50,179,x+50,195,strokeColor=BLUE))
        d.add(Line(60,195,426,195,strokeColor=BLUE))
        arrow(d,240,195,240,210,inheritance=True)
        box(d,10,75,145,40,'PIMManager\nowns 0..* PIR')
        box(d,175,75,130,40,'PIRFactory\nvalidates fields')
        box(d,330,75,145,40,'SearchNode (abstract)\nevaluate(PIR)')
        d.add(Line(0,95,0,225,strokeColor=BLUE))
        d.add(Line(0,95,2,95,strokeColor=BLUE))
        d.add(Polygon([10,95,6,98,2,95,6,92],strokeColor=BLUE,fillColor=BLUE))
        d.add(Line(0,225,175,225,strokeColor=BLUE))
        arrow(d,155,95,175,95)
        for x,label in [(175,'ComparisonNode'),(335,'LogicNode\nowns SearchNode children')]:
            box(d,x,5,140,40,label); arrow(d,x+70,45,402,75,inheritance=True)
        d.add(Line(155,81,165,81,strokeColor=BLUE))
        d.add(Line(165,81,165,130,strokeColor=BLUE))
        d.add(Line(165,130,402,130,strokeColor=BLUE))
        arrow(d,402,130,402,115)
    else:
        actors=[('User',15),('Repl',80),('CommandParser',160),('SearchParser',245),('Manager',325),('Factory',400),('View',470)]
        for name,x in actors:
            d.add(String(x,400,name,textAnchor='middle',fontName='Helvetica-Bold',fontSize=7))
            d.add(Line(x,390,x,8,strokeColor=colors.lightgrey))
        steps=[(15,80,'search type/deadline'),(80,160,'parse(line)'),(160,80,'Command(search, expression)'),
               (80,245,'parse(expression)'),(245,80,'validated AST'),(80,325,'search(AST)'),
               (325,80,'matching records'),(80,470,'print_all(records)'),(470,15,'display task #2 and fields'),
               (15,80,'edit 2 --deadline ...'),(80,160,'parse(line)'),(160,80,'Command(edit, 2, updates)'),
               (80,325,'edit_pir(2, updates)'),(325,400,'create replacement'),(400,325,'validated PIR or error'),
               (325,325,'replace #2 only on success'),(325,80,'replacement / ValidationError'),(80,470,'print update / error')]
        for i,(x1,x2,label) in enumerate(steps):
            y=375-i*20
            if x1 != x2:
                arrow(d,x1,y,x2,y)
            else:
                d.add(Line(x1,y,x1+22,y,strokeColor=BLUE))
                d.add(Line(x1+22,y,x1+22,y-7,strokeColor=BLUE))
                arrow(d,x1+22,y-7,x1,y-7)
            d.add(String(min(x1,x2)+3,y+4,label,fontName='Helvetica',fontSize=7))
    return d


def footer(canvas, doc):
    canvas.setFont('Helvetica',8); canvas.setFillColor(colors.grey)
    canvas.drawString(45,25,'COMP3211 PIM  /  Version 0.2')
    canvas.drawRightString(550,25,str(doc.page))


def api_appendix():
    result=[PageBreak(),Paragraph('Source signature inventory',STYLES['Heading1'])]
    result.append(Paragraph('Generated from the current Python AST. Exception contracts and field definitions are explained in section 3.', STYLES['BodyPIM']))
    for package in ['model','cli','storage','view','controller']:
        for source in sorted((ROOT/package).glob('*.py')):
            tree=ast.parse(source.read_text(encoding='utf-8'))
            entries=[]
            for node in tree.body:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    entries.append(f'{node.name}({ast.unparse(node.args)}) -> {ast.unparse(node.returns) if node.returns else "(see contract)"}')
                elif isinstance(node,ast.ClassDef):
                    entries.append('class '+node.name)
                    for method in node.body:
                        if isinstance(method,ast.FunctionDef):
                            entries.append(f'  {method.name}({ast.unparse(method.args)}) -> {ast.unparse(method.returns) if method.returns else "(see contract)"}')
            if entries:
                result.append(Paragraph(str(source.relative_to(ROOT)),STYLES['Heading2']))
                for entry in entries:
                    result.append(Paragraph(styled(entry),STYLES['CodePIM']))
    return result


def render(source, name):
    content=source.read_text(encoding='utf-8').splitlines()
    story=[]; i=0; figure=0
    while i < len(content):
        line=content[i]; i+=1
        if not line.strip(): continue
        if line.startswith('```'):
            lang=line[3:]; block=[]
            while i < len(content) and not content[i].startswith('```'):
                block.append(content[i]); i+=1
            i+=1
            if lang == 'mermaid':
                kind=['architecture','classes','sequence'][figure]; figure+=1
                story.append(KeepTogether([Paragraph(f'Figure {figure}',STYLES['Heading3']),diagram(kind)]))
            else:
                for code in block:
                    story.append(Paragraph(styled(code),STYLES['CodePIM']))
            continue
        if line.startswith('|'):
            tablelines=[line]
            while i < len(content) and content[i].startswith('|'):
                tablelines.append(content[i]); i+=1
            rows=[]
            for row in tablelines:
                if re.fullmatch(r'[|\s:\-]+',row): continue
                rows.append([Paragraph(styled(cell.strip()),STYLES['CellPIM']) for cell in row.strip('|').split('|')])
            widths= [480/len(rows[0])]*len(rows[0])
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eef4')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([table,Spacer(1,12)]); continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'))
            style=STYLES['Title'] if level == 1 else STYLES['Heading1' if level == 2 else 'Heading2']
            story.append(Paragraph(styled(line.lstrip('#').strip()),style)); continue
        story.append(Paragraph(styled(line),STYLES['BodyPIM']))
    if name == 'design.pdf': story.extend(api_appendix())
    SimpleDocTemplate(str(OUT/name),pagesize=(595.28,841.89),rightMargin=55,leftMargin=55,topMargin=45,bottomMargin=45,
                      title=content[0].lstrip('# '),author='COMP3211 project group (names pending)').build(story,onFirstPage=footer,onLaterPages=footer)


def render_coverage():
    metadata, table = (ROOT/'coverage_report.txt').read_text(encoding='utf-8').split('\n\n', 1)
    story = [Paragraph('Model Line Coverage Report', STYLES['Title'])]
    story.extend(Paragraph(styled(line), STYLES['BodyPIM']) for line in metadata.splitlines())
    story.extend([Spacer(1,12), Preformatted(table, STYLES['CodePIM'])])
    SimpleDocTemplate(str(OUT/'coverage_report.pdf'), pagesize=(595.28,841.89),
                      rightMargin=55,leftMargin=55,topMargin=45,bottomMargin=45,
                      title='Model Line Coverage Report').build(story,onFirstPage=footer,onLaterPages=footer)
    (ROOT/'coverage_report.pdf').write_bytes((OUT/'coverage_report.pdf').read_bytes())


if __name__ == '__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    for source,name in [('docs/SRS.md','SRS.pdf'),('docs/design.md','design.pdf'),('docs/user_manual.md','user_manual.pdf'),
                        ('docs/dev_manual.md','dev_manual.pdf'),('requirements_coverage.md','requirements_coverage.pdf'),
                        ('docs/submission_checklist.md','submission_checklist.pdf'),('docs/ai_usage.md','ai_usage.pdf')]:
        render(ROOT/source,name)
        print(OUT/name)
    # The course requires the requirements report in the source root.
    (ROOT/'requirements_coverage.pdf').write_bytes((OUT/'requirements_coverage.pdf').read_bytes())
    render_coverage()
