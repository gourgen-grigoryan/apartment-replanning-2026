"""Տպագրական թերթեր՝ մոդելի տեսախցիկով և տեղակայման հատակագծով։"""
import json
import math
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

root=Path(__file__).resolve().parents[1]
folder=root/'07-views'
plan=json.loads((root/'02-design/design.json').read_text('utf8'))
cameras=json.loads((folder/'cameras.json').read_text('utf8'))
areas={r['id']:f"{r['area']:.2f}" for r in plan['rooms']}
captions=[
    f"{areas['ST']} մ² միասնական հյուրասենյակ-խոհանոց։ Բազմոցի և ճաշասեղանի գոտիները բաց են միմյանց նկատմամբ։ Հյուրերը պատշգամբ են հասնում այս սենյակով։",
    'Խոհանոցի աշխատանքային շարքը ճակատային ստուդիայի աջ պատի մոտ է։ Սպասք լվացող մեքենան, լվացարանը, սալօջախն ու սառնարանն ընդգրկված են նույն հատակագծում։',
    f"{areas['B1']} մ² ննջասենյակ վերին ձախ հատվածում։ Արտաքին լույսն անցնում է պատշգամբի վիտրաժով և սենյակի առկա լուսամուտով։",
    f"Ստորին ձախ սենյակ։ Աղբյուրում՝ 13.55 մ², ուրվագծով՝ {areas['B2']} մ²։ Սենյակը չունի արտաքին պատուհան։ Սենյակի համար նախատեսված են արհեստական լուսավորություն և մեխանիկական օդափոխություն։",
    f"{areas['BA']} մ² համատեղ սանհանգույցը ստորին աջ հատվածում է։ Մուտքը ներքին միջանցքից է։ Ցնցուղի, զուգարանակոնքի, լվացարանի և լվացքի մեքենայի կետերը կապված են համակարգերի մոդելին։",
    'Վիտրաժային պատշգամբի ներքին դիտակետ։ Մոդելում արտաքին ապակեպատման բարձրությունը պայմանական 2.65 մ է։ Սալը և դրա ամրացումները չափագրվում են տեղում։',
    'Արտաքին դիտակետը ցույց է տալիս վիտրաժի գիծը, դրա ծածկը և բնակարանին հարող բացվածքները։ Հարևան հարկերի ճակատները, տեղանքը և հորիզոնը չափագրված չեն։',
    'Պատերը կտրված են հատակից 1.12 մ բարձրության վրա։ Սլաքը ցույց է տալիս ուղին մուտք №3-ից սեփական միջանցքով և կրող պատի D-LB բացվածքով դեպի բաց ստուդիա ու վիտրաժային պատշգամբ։']

for font,file in [('reg','arial.ttf'),('bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(font,'C:/Windows/Fonts/'+file))
c=Canvas(str(folder/'Views.pdf'),pagesize=landscape(A3))
c.setTitle(plan['revision']+' · Մոդելի ութ դիտակետ')
def txt(x,y,t,size=11,bold=False,color='#213E3B'):
    c.setFillColor(HexColor(color));c.setFont('bold' if bold else 'reg',size);c.drawString(x,y,t)
def paragraph(x,y,t,width):
    line=''
    for word in t.split():
        added=(line+' '+word).strip()
        if line and pdfmetrics.stringWidth(added,'reg',12)>width:
            txt(x,y,line,12);y-=19;line=word
        else:line=added
    txt(x,y,line,12)
def route_line(points,width):
    p=c.beginPath();p.moveTo(*points[0]);
    for v in points[1:]:p.lineTo(*v)
    c.saveState();c.setLineCap(1);c.setLineJoin(1)
    for colour,thick in [('#FCF9EF',width+1.6),('#AB4D28',width)]:
        c.setStrokeColor(HexColor(colour));c.setLineWidth(thick);c.drawPath(p)
    a,b=points[-2:];angle=math.atan2(b[1]-a[1],b[0]-a[0]);size=width*3
    arrow=c.beginPath();arrow.moveTo(*b)
    for delta in (-.58,.58):arrow.lineTo(b[0]-size*math.cos(angle+delta),b[1]-size*math.sin(angle+delta))
    arrow.close();c.setFillColor(HexColor('#AB4D28'));c.drawPath(arrow,fill=1,stroke=0)
    c.circle(*points[0],width*1.2,fill=1,stroke=0);c.restoreState()
def cutaway_route(cam):
    # Perspective projection matches Render.cs and the uncropped 3:2 image frame.
    def unit(v):
        length=math.sqrt(sum(n*n for n in v));return [n/length for n in v]
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    eye=cam['eye'];f=unit([t-e for t,e in zip(cam['target'],eye)]);r=unit([f[1],-f[0],0])
    up=[r[1]*f[2],-r[0]*f[2],r[0]*f[1]-r[1]*f[0]]
    k=824/(2*math.tan(math.radians(cam['horizontal_fov_deg'])/2));points=[]
    for x,y in plan['routes']['guest']:
        v=[x-eye[0],y-eye[1],.055-eye[2]];d=dot(v,f)
        points.append((43+412+k*dot(v,r)/d,126+275+k*dot(v,up)/d))
    route_line(points,2.8)
def inset(cam,i):
    pts=[p for r in plan['rooms'] for p in r['points']]+[cam['eye'][:2]]
    lo=[min(p[k] for p in pts) for k in (0,1)]
    hi=[max(p[k] for p in pts) for k in (0,1)]
    scale=min(239/(hi[0]-lo[0]+1),218/(hi[1]-lo[1]+1))
    def xy(p):return (907+scale*(.5+p[0]-lo[0]),366+scale*(.5+p[1]-lo[1]))
    for r in plan['rooms']:
        p=c.beginPath()
        for j,v in enumerate(r['points']):
            (p.moveTo if j==0 else p.lineTo)(*xy(v))
        p.close()
        c.setFillColor(HexColor({'ST':'#E9CEA8','B1':'#C6D9BD','B2':'#C6D9BD','BA':'#BDDDDB','BAL':'#DCEBE3'}.get(r['id'],'#E4E5E1')))
        c.setStrokeColor(HexColor('#617D72'));c.setLineWidth(.7);c.drawPath(p,fill=1,stroke=1)
    if i==7:
        route_line([xy(v) for v in plan['routes']['guest']],1.55)
    eye=xy(cam['eye']);target=xy(cam['target']);angle=math.atan2(target[1]-eye[1],target[0]-eye[0])
    tip=(eye[0]+14*math.cos(angle),eye[1]+14*math.sin(angle))
    c.setStrokeColor(HexColor('#994C2C'));c.setLineWidth(2);c.line(*eye,*tip)
    c.setFillColor(HexColor('#994C2C'));c.circle(*eye,2.8,fill=1,stroke=0)
for i,cam in enumerate(cameras):
    txt(44,777,'ԲՆԱԿԱՐԱՆԻ ՎԵՐԱՊԼԱՆԱՎՈՐՈՒՄ   /   ՄՈԴԵԼԻ ՏԵՍԱՐԱՆՆԵՐ',11,True,'#258274')
    txt(43,724,cam['name'],30,True)
    c.drawImage(str(folder/cam['file']),43,126,824,550,preserveAspectRatio=True)
    if i==7:cutaway_route(cam)
    txt(907,650,'Տեսախցիկի դիրքը',16,True);inset(cam,i)
    paragraph(907,326,captions[i],235)
    x,y,z=cam['eye']
    txt(907,114,f'X {x:+.2f}   Y {y:+.2f}   Z {z:+.2f} մ',10)
    txt(907,94,f'Հորիզոնական դիտանկյուն՝ {cam["horizontal_fov_deg"]}°',10)
    txt(44,56,f"Տ-{i+1:02}   /   Առանց մասշտաբի   /   23.11.2026   /   {plan['revision']}",10,True)
    txt(555,56,'Նյութերն ու լուսային միջավայրը պայմանական են։',10)
    c.showPage()
c.save()
