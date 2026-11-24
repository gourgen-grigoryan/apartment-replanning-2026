"""Ստուգել հանձնման հիմնական պայմանները միայն Python-ի ստանդարտ գրադարանով։"""
import hashlib
import json
import math
import re
from urllib.parse import unquote
from xml.etree import ElementTree
from pathlib import Path
from zipfile import ZipFile

root=Path(__file__).resolve().parents[1]
def read(name):return json.loads((root/name).read_text(encoding='utf-8-sig'))
def close(a,b,eps=1e-5):assert abs(a-b)<eps,(a,b)
def area(p):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))/2
def run(p):return sum(math.dist(a[:2],b[:2]) for a,b in zip(p,p[1:]))
d=read('02-design/design.json');base=read('01-source/base.json');m=read('04-services/services.json')
assert d['revision']=='R3' and d['selected']==3
rooms={v['id']:v for v in d['rooms']}
assert set(rooms)=={'B1','B2','ST','BA','H1','SH','SR','BAL'}
for v in rooms.values():close(area(v['points']),v['area'])
close(rooms['B1']['area'],11.0);close(rooms['B2']['area'],area(base['rooms']['bed_w']['points']))
assert d['windowless']=='B2' and d['reported_sleeping_area']==13.55
close(rooms['ST']['area'],d['studio'])
assert d['column']==base['features']['column'] and d['stack']==base['features']['stack_marker'][0]
lb=next(w for w in d['walls'] if w['kind']=='bearing');close(math.dist(lb['a'],lb['b']),5.92)
for entry in (1,2,3):
    opt=read(f'02-design/options/entry-{entry}.json')
    assert opt['entry']==entry and sum(o['kind']=='entry' for o in opt['openings'])==1
    for kind,path in opt['routes'].items():close(run(path[:-1] if kind=='guest' else path),opt['lengths'][kind])
    sew=opt['sewer'];close(.03*run(sew['branch'])+.02*run(sew['collector']),sew['drop'])
    assert sew['collector'][-1]==d['stack']
ex=d['extension'];close(area(ex['strip']),ex['gross']);close(ex['gross']+ex['balcony_left'],rooms['BAL']['area'])
close(ex['net']+ex['frame']+ex['column_overlap'],ex['gross'])
assert m['revision']=='R3' and len(m['drains'])==6
assert len(m['routes'])==60 and len(m['elements'])==80
assert sum(v['id']=='B2' and v['ag']==0 for v in m['thermal'])==1
dr={r['id']:r for r in m['drains']};close(dr['D01']['total'],d['sewer']['length']);close(dr['D01']['h'],d['sewer']['drop'])
for name in ['Բնակարանի նախագիծ.pdf','02-design/Architecture.pdf','04-services/Engineering-R3.pdf']:
    assert (root/name).read_bytes().startswith(b'%PDF-'),name
with ZipFile(root/'03-calculations/Areas.xlsx') as z:
    assert z.testzip() is None
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    worksheet=ElementTree.fromstring(z.read('xl/worksheets/sheet1.xml'))
    for cell,value in [('C13',66.15),('D13',66.1785426),('E13',68.38182871)]:
        close(float(worksheet.find(f'.//x:c[@r="{cell}"]/x:v',ns).text),value)
    for path in [n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)]:
        assert not ElementTree.fromstring(z.read(path)).findall('.//x:c[@t="e"]',ns)
for name in ['entry-01.png','entry-02.png','entry-03.png','furniture.png']:
    assert (root/'docs/diagrams'/name).read_bytes().startswith(b'\x89PNG')
cad=root/'06-cad'
for name in ['00-Existing','01-Architecture','02-Water','03-Drainage','04-Power','05-Lighting','06-HVAC','X-BASE']:
    assert (cad/(name+'.dwg')).read_bytes()[:6]==b'AC1032',name
    source=(cad/(name+'.dxf')).read_text('ascii')
    if name!='X-BASE':
        assert ('X-BASE.dwg' if name.startswith(('00','01')) else '01-Architecture.dwg') in source
model=(root/'05-model/apartment.ifc').read_text('ascii')
assert "FILE_SCHEMA(('IFC4'))" in model and model.count('=IFCSPACE(')==len(rooms)
assert model.count('=IFCRELVOIDSELEMENT(')==len(d['openings'])
views=read('07-views/cameras.json')
assert len(views)==8
for cam in views:
    assert (root/'07-views'/cam['file']).read_bytes()[:3]==b'\xff\xd8\xff'
assert len(re.findall(rb'/Type\s*/Page\b',(root/'Բնակարանի նախագիծ.pdf').read_bytes()))==36
for md in root.rglob('*.md'):
    if '.git' in md.parts:continue
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',md.read_text('utf-8-sig')):
        if '://' not in target and not target.startswith('#'):
            assert (md.parent/unquote(target.split('#')[0])).exists(),(md.name,target)
checksums=read('08-review/checksums.json')
for required in ('Բնակարանի նախագիծ.pdf','05-model/apartment.ifc','07-views/Views.pdf','03-calculations/Areas.xlsx','02-design/Architecture.pdf','04-services/Engineering-R3.pdf'):
    assert required in checksums,required
for name,expected in checksums.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
print('R3. Երեք տարբերակ, լուսավոր ննջասենյակ և առանց պատուհանի ներքին սենյակ, մեկ մուտք, կահավորված ուղիներ, վեց սարքի կոյուղի և մակերեսների հաշվեկշիռ՝ ստուգված։')
