"""R3 գծագրային համադրման ստուգում։ Միայն Python-ի ստանդարտ գրադարան։"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load = lambda name: json.loads((ROOT / name).read_text(encoding='utf-8-sig'))
plan = load('02-design/design.json')
base = load('01-source/base.json')
mep = load('04-services/services.json')
rooms = {v['id']:v for v in plan['rooms']}
walls = {v['id']:v for v in plan['walls']}
doors = {v['id']:v for v in plan['openings']}
objects = {v['id']:v for v in plan['furniture']}
pipes = {v['id']:v for v in mep['routes']}
epsilon = 1e-8

def polygon_area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2

def project(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    return ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)

def seg_dist(p,a,b):
    t = max(0,min(1,project(p,a,b)))
    return math.dist(p,(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))

def inside(p,poly):
    state=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if seg_dist(p,a,b)<epsilon:return True
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0] < a[0]+(p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1]):
            state=not state
    return state

def rect(v):
    a,b,w,d=v['x'],v['y'],v['w'],v['d']
    return [(a,b),(a+w,b),(a+w,b+d),(a,b+d)]

def min_rect_dist(p,v):
    x=max(v['x']-p[0],p[0]-v['x']-v['w'],0)
    y=max(v['y']-p[1],p[1]-v['y']-v['d'],0)
    return math.hypot(x,y)

def samples(points,step=.01):
    for a,b in zip(points,points[1:]):
        n=max(1,math.ceil(math.dist(a,b)/step))
        for i in range(n):
            yield tuple(a[j]+(b[j]-a[j])*i/n for j in (0,1))
    yield points[-1]

def length(pts):return sum(math.dist(a[:2],b[:2]) for a,b in zip(pts,pts[1:]))

def point_in_wall(p,w):
    a,b=w['a'],w['b']; t=project(p,a,b)
    if not (0 < t < 1 and seg_dist(p,a,b) < w['t']/2-0.001):return False
    for d in doors.values():
        if d['wall']!=w['id'] or d['kind'] in ['window','internal_window']:continue
        lo,hi=sorted(project(d[k],a,b) for k in ('a','b'))
        if lo-0.001<=t<=hi+0.001:return False
    return True

notes=['# Երկրաչափական համադրում և վերաստուգում',
       '', '23.11.2026 · R3 · Նշումներով PDF-ի հիմքի վրա մշակված նախագծի անկախ թվային ստուգում։ Բոլոր հեռավորությունները մետրերով են, եթե այլ միավոր նշված չէ։',
       '', '## Կահույք և դռներ','']
ownership={
 'B1':['BED1'], 'B2':['BED2'], 'ST':['SO1','FR','HB','DW','KS','TB1','CH1','CH2','CH3','CH4'],
 'BA':['SHW','WC','BS','WM'], 'BAL':['BT']}
assert {k for group in ownership.values() for k in group} == set(objects)
bad=[];counts=0
for room,ids in ownership.items():
    for name in ids:
        shape=rect(objects[name]);counts+=1
        if any(not inside(p,rooms[room]['points']) for p in samples(shape+shape[:1])):
            bad.append(name+' / '+room)
notes.append(f'- {counts} կահույքային կամ սանտեխնիկական տարրի եզրագիծը համադրվել է նշանակված սենքի մաքուր ուրվագծին՝ առավելագույնը 10 մմ քայլով։ Սահմանից դուրս գտնվող տարրեր՝ '+(', '.join(bad) if bad else '0')+'։')

# Բացման քառորդ սկավառակի հատումը ուղղանկյուն կահույքին։ Սահմանները
# հաշվարկվում են հենց Ճ-03 թերթի ծխնիով և բաց դիրքի ուղղությամբ։
swing={}
for key,d in doors.items():
    if d['kind'] not in ('door','entry','entry_common','glazed_door'): continue
    hinge=d['hinge']; h=d[hinge]; end=d['b' if hinge=='a' else 'a']
    radius=math.dist(h,end)
    dx,dy=[(end[i]-h[i])/radius+d['swing'][i] for i in (0,1)]
    swing[key]=(hinge,1 if dx>0 else -1,1 if dy>0 else -1)
pairhits=[]
for key,(hinge,sx,sy) in swing.items():
    d=doors[key];h=d[hinge];rad=math.dist(d['a'],d['b'])
    for name,item in objects.items():
        local=[((v[0]-h[0])*sx,(v[1]-h[1])*sy) for v in rect(item)]
        if max(t[0] for t in local)<=0 or max(t[1] for t in local)<=0: continue
        nearest=math.hypot(max(0,min(t[0] for t in local)),max(0,min(t[1] for t in local)))
        if nearest<rad-.001:pairhits.append(key+' / '+name)
notes.append(f'- {len(swing)} փեղկի 90° բացման գոտին ստուգվել է ստատիկ կահույքի նկատմամբ։ Հատումներ՝ '+(', '.join(pairhits) if pairhits else '0')+'։')
overlaps=[]
items=list(objects.values())
for i,a in enumerate(items):
    for b in items[i+1:]:
        if min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x'])>.001 and min(a['y']+a['d'],b['y']+b['d'])-max(a['y'],b['y'])>.001:
            overlaps.append(a['id']+' / '+b['id'])
notes.append('- Կահույք-կահույք հատումներ՝ '+(', '.join(overlaps) if overlaps else '0')+'։ Սարքերի իրական դռներն ու սպասարկման գոտիները հաստատել ընտրված մոդելներով։')
notes.extend(['','## Մարդկանց ուղիներ','','| Ուղի | Դռնից դուռ, մ | Դռներ կամ անցքեր | Ստուդիա | Ննջարանով անցում | Պատի / կահույքի առանցքային հատում |','|---|---:|---|---|---|---|'])
gate={'guest':'D3 → D-LB → D-BAL','night1':'D-B1 → D-LB → D-BA','night2':'D-R → D-BA'}
short={'guest':'Հյուր','night1':'Գիշերային 1','night2':'Գիշերային 2'}
route_errors=[]
for name,raw in plan['routes'].items():
    pts=raw[:-1] if name=='guest' else raw
    walk=list(samples(pts))
    def hits(poly):return any(inside(p,poly) for p in walk[1:-1])
    s=hits(rooms['ST']['points']);bed=[b for b in ['B1','B2'] if hits(rooms[b]['points'])]
    hits_wall=[w['id'] for w in walls.values() if any(point_in_wall(p,w) for p in walk)]
    hits_it=[k for k,v in objects.items() if any(inside(p,rect(v)) for p in walk)]
    if hits_wall or hits_it: route_errors.append((name,hits_wall,hits_it))
    notes.append(f"| {short[name]} | {length(pts):.2f} | {gate[name]} | {'այո' if s else 'ոչ'} | {', '.join(bed) or 'ոչ'} | {', '.join(hits_wall+hits_it) or '0'} |")
notes.append('')
notes.append('Հյուրի չափումը եզրափակվում է պատշգամբի դռան առանցքին։ Անցքերի արագ ստուգումը 10 մմ քայլով ուղու առանցքը համեմատում է պատի լիակատար և անցանելի մասերի հետ։ Անիվավոր սայլակի շրջադարձը և տարհանման համապատասխանությունը առանձին ստուգման հարցեր են։ Մուտք №3-ը միակ բնակարանային դուռն է՝ D3։ D-SH-ը ընդհանուր նախամուտքի դուռն է, D-SR-ը՝ խորդանոցի։')
notes.extend(['','## Սյուն, բացվածք և լույս','','| Սենք | Բացվածք | Անվանական մակերես, մ² | Սենք, մ² | Բացվածք/հատակ | Լույսի ուղի |','|---|---|---:|---:|---:|---|'])
for k,ids in [('B1',['W1']),('ST',['W-ST','W-ST2','D-BAL','W2a','W2b']),('B2',[])]:
    glazing=sum(math.dist(doors[id]['a'],doors[id]['b'])*doors[id]['height'] for id in ids)
    surface=polygon_area(rooms[k]['points'])
    ratio=f'1:{surface/glazing:.2f}' if glazing else '0'
    path='Դուրս → վիտրաժային պատշգամբ → սեփական բացվածք' if glazing else 'Արտաքին բացվածք չկա'
    notes.append(f"| {rooms[k]['name']} | {' + '.join(ids) or 'չկա'} | {glazing:.3f} | {surface:.2f} | {ratio} | {path} |")
column=plan['column']
open_lines=[(doors[id]['a'],doors[id]['b']) for id in ['W1','W-ST','W-ST2','D-BAL','W2a','W2b']]
dist=min(min(seg_dist(v,a,b) for v in column) for a,b in open_lines)
dist=min(dist,min(seg_dist(p,a,b) for line in open_lines for p in line for a,b in zip(column,column[1:]+column[:1])))
notes.extend(['',f'Արտաքին բացվածք ունեն B1-ը և ստուդիան։ B2-ում մեխանիկական օդափոխությունն ու արհեստական լույսը բնական լուսավորում չեն ապահովում։ Սյան թվայնացված եզրից մինչև ամենամոտ լուսային բացվածքի գծի հեռավորությունը մոտ {dist*1000:.0f} մմ է։ Կոնստրուկտորը պետք է հաստատի հարող պրոֆիլի և ամրացման տեղը։ Հասանելի երկինքը, քիվի ստվերը, ապակու լուսաթափանցումը, բնական լուսավորվածության գործակիցը և ինսոլյացիան այս հարթ չափումից չեն ստացվում։',''])
wall=walls['LB'];opening=doors['D-LB']
# Գծերի համարները անկախ են դրանց ֆայլային դասավորումից։
line_by_id={z['id']:z['points'] for z in base['lines']}
x_source=sorted(line_by_id[i][0][0] for i in (2,3))
notes.append(f"Կրող պատի առանցքի երկարությունը {math.dist(wall['a'],wall['b']):.2f} մ է։ Գործող անցք համարված եզրերն են x={opening['a'][0]:.3f}–{opening['b'][0]:.3f} մ։ PDF-ի վեկտորների նկատմամբ ամենամեծ տարբերությունը {max(abs(x_source[i]-opening[k][0]) for i,k in [(0,'a'),(1,'b')])*1000:.2f} մմ է։ Անցքի մաքուր լայնքը, բարձրությունը և հատակին հասնելը պահանջում են տեղում չափագրում։")
notes.extend(['','## Սարքից մինչև կանգնակ','','| Սարք / շղթա | Հաշվարկված ընդհանուր հորիզոնական երկարություն, մ | Ինքնահոս պահանջվող անկում, մմ | Ուղու ստուգում |','|---|---:|---:|---|'])
main=pipes['D00'];data={r['id']:r for r in mep['drains']}
stat=[];mismatches=[]
for num in range(1,7):
    key='D0'+str(num);v=data[key];branch=pipes[key]
    gravity=v.get('downstream',key);g=pipes[gravity];vertical=pipes['V0'+gravity[-1]]
    expected=g['slope']*length(g['points'])+main['slope']*length(main['points'])
    extra=length(branch['points']) if key!=gravity else 0
    total=length(g['points'])+length(main['points'])+extra
    # Նույն ջրագծի խողովակատակի շարունակականությունը ստուգվում է՝ անկախ տարբեր OD-ից։
    err=max(abs(g['points'][-1][2]-g['diameter_m']/2-main['points'][0][2]+main['diameter_m']/2),
            math.dist(g['points'][-1][:2],main['points'][0][:2]),math.dist(main['points'][-1][:2],plan['stack']),
            math.dist(vertical['points'][-1],g['points'][0]))
    if key!=gravity:
        err=max(err,math.dist(branch['points'][-1],vertical['points'][0]))
        start_error=abs(branch['points'][0][2]-v['z0'])
        if start_error>.001:mismatches.append(f"{key} մոդելի մեկնարկային Z={branch['points'][0][2]:+.3f} մ, աղյուսակում Z={v['z0']:+.3f} մ։")
    err=max(err,abs(total-v['total']),abs(expected-v['h']))
    stat.append(err)
    chain=' → '.join(([key] if key!=gravity else [])+['V0'+gravity[-1],gravity,'D00','R'])
    notes.append(f"| {v['name']} · {chain} | {total:.2f} | {expected*1000:.0f} | "+('Կապերի շեղումը <1 մմ' if err<.001 else f'Շեղում {err*1000:.1f} մմ')+' |')
notes.extend(['',f'Ճյուղերի երկարությունները վերահաշվվել են բոլոր գագաթներով։ Ընդհանուր J→R մասը {length(main["points"]):.2f} մ է, թեքությունը 2%։ Խոհանոցի և սանհանգույցի ճյուղերը միանում են նույն կոլեկտորին։ Նիշերը և հատակի շերտերի հասանելի հաստությունը չափվում են տեղում։',
  'Նիշերի ստուգում․ '+(' '.join(mismatches) if mismatches else 'D05 և D06 մեքենաների մեկնարկային և սիֆոնին միացման նիշերը համընկնում են մոդելին։'),
  'Սպասք և լվացք լվացող մեքենաների ճկուն խողովակները ճնշումային են։ Աղյուսակի անկումը վերաբերում է սիֆոնից հետո ինքնահոս մասին։ Խողովակների երկարությունները հորիզոնական նախագծումներն են։ Փաստացի հասանելի անկումը բաց է մինչև նիշերի չափագրում։',
  '', '## Վերաստուգման ֆայլեր',''])
for name in ['01-source/base.json','02-design/design.json','04-services/services.json']:
    digest=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    notes.append(f'- `{name}` · SHA-256 `{digest}`')
notes+=['','Գործարկում՝ `python tools/check_geometry.py`։ Փոփոխված բացվածքից, կահավորումից կամ ինժեներական երթուղուց հետո ելքը վերարտադրել նույն տվյալների նոր խմբագրությամբ։']
report=ROOT/'08-review/geometry-checks.md'
report.write_text('\n'.join(notes)+'\n',encoding='utf8')
print('Ստուգված կահույք',counts,'/ ուրվագծային շեղումներ',bad,'/ փեղկերի բախումներ',pairhits)
print('Կոյուղու առավելագույն շեղում, մ',max(stat),'/ նիշերի լրացուցիչ տարբերություններ',mismatches)
assert not any((bad,pairhits,overlaps,route_errors,mismatches)) and max(stat)<.001, (bad,pairhits,overlaps,route_errors,mismatches,stat)
