"""Թարմացնել հանձնվող ֆայլերի ցանկը և փոխանցման ստուգիչ գումարները։"""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

root=Path(__file__).resolve().parents[1]
index=root/'docs/FILES.md'
manifest=root/'08-review/checksums.json'
index.touch(exist_ok=True)
manifest.touch(exist_ok=True)
files=sorted(p.relative_to(root) for p in root.rglob('*') if p.is_file()
             and not {'.git','__pycache__','node_modules'}.intersection(p.relative_to(root).parts))
sections={'00-input':'Մուտքային նյութեր','01-source':'Առկա վիճակ','02-design':'Վերապլանավորման տարբերակներ',
          '03-calculations':'Հաշվարկներ','04-services':'Ինժեներական նախագծում','05-model':'Խմբագրվող մոդել',
          '06-cad':'CAD գծագրեր','07-views':'Դիտակետեր','08-review':'Ստուգում','docs':'Փաստաթղթեր և դիագրամներ',
          'tools':'Վերարտադրման գործիքներ','.github':'GitHub-ի աշխատանքային ընթացք'}
lines=['# Հանձնման ամբողջական ֆայլացանկ','',
       'Ստորև բերված են պահոցի բոլոր աշխատանքային ֆայլերը։ [Հանձնման ստուգումը](../08-review/DELIVERY.md) պարունակում է վերաընթերցման արդյունքները։','']
for group,title in [('', 'Հիմնական ֆայլեր'),*sections.items()]:
    entries=[p for p in files if (p.parts[0] if len(p.parts)>1 else '')==group]
    lines+=['## '+title,'']
    for p in entries:
        path=p.as_posix()
        lines.append('- ['+path+'](../'+quote(path,safe='/-.')+')')
    lines.append('')
index.write_text('\n'.join(lines),'utf8')
assets={p.as_posix():hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files
        if p.suffix.lower() in {'.pdf','.dwg','.ifc','.jpg','.xlsx','.png'} or p.parts[0]=='00-input'}
manifest.write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n','utf8')
print(len(files),'ֆայլ,',len(assets),'ստուգիչ գումար')
