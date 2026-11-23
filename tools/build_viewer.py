"""Միավորում է ընթացիկ նախագծային տվյալներն ու անցանց եռաչափ դիտիչը։"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((root / path).read_text(encoding='utf-8-sig'))

data = {'arch': read('02-design/design.json'), 'services': read('04-services/services.json')}
json_text=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
html=(root/'tools/viewer-template.html').read_text(encoding='utf8')
out=root/'05-model/Viewer.html'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(html.replace('___MODEL_JSON___',json_text),encoding='utf8')
print(out.name,out.stat().st_size)
