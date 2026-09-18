"""Authoring only: render actual captured CLI output, without altering its content."""
import json
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'output/demo/session.json').read_text(encoding='utf-8'))
folder = ROOT / 'tmp/demo_frames'
folder.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 25)
title = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 35)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 21)
history = []
manifest = []
for index, segment in enumerate(data['segments']):
    for line in segment['output'].splitlines():
        history.extend(textwrap.wrap(line, 81, replace_whitespace=False, drop_whitespace=False) or [''])
    frame = Image.new('RGB', (1600, 1000), '#101c2a')
    draw = ImageDraw.Draw(frame)
    draw.text((55,40), segment['caption'], font=title, fill='#fafcfd')
    draw.text((55,105), 'COMP3211 PIM  /  Real CLI output replay  /  Python '+data['python'],font=small,fill='#98b6cc')
    for row,line in enumerate(history[-20:]):
        draw.text((55,170+row*36),line,font=font,fill='#d8eee2')
    draw.text((55,945),f'{index+1:02d} / {len(data["segments"]):02d}    Saved data and commands are temporary demonstration records.',font=small,fill='#98b6cc')
    path=folder / f'frame-{index:03d}.png'
    frame.save(path)
    manifest.append({'path':str(path),'seconds':segment['seconds']})
(folder/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
print(folder/'manifest.json')
