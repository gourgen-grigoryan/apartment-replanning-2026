"""Վավերացնել աղբյուրի ընթերցումը և պատրաստել գծագրաշարի առաջին երկու թերթերը։"""
import math, json, subprocess, tempfile
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from PIL import Image
from reportlab.lib.utils import ImageReader
P=Path(__file__).resolve().parents[1];D=json.loads((P/'01-source/base.json').read_text(encoding='utf8'));r=D['rooms']
pdfmetrics.registerFont(TTFont('A','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('B','C:/Windows/Fonts/arialbd.ttf'))
W,H=420*mm,297*mm
c=Canvas(str(P/'01-source/Source-atlas.pdf'),pagesize=(W,H));c.setTitle('Նշումներով հատակագծի հենակետեր և չափագրում')
teal='#087973';dark='#243B38';grey='#536A69'
def txt(x,y,t,s=11,color=dark,font='A'):
    c.setFont(font,s);c.setFillColor(HexColor(color));c.drawString(x,y,t.replace('․','.'))
def seg(a,b,col,w=1):
    c.setStrokeColor(HexColor(col));c.setLineWidth(w);c.line(*a,*b)
def block(x,y,title,st,w):
    txt(x,y,title,14,teal,'B');y-=23;ln=''
    for wd in st.split():
        v=(ln+' '+wd).strip()
        if ln and pdfmetrics.stringWidth(v,'A',12)>w:txt(x,y,ln,12);ln=wd;y-=17
        else:ln=v
    if ln:txt(x,y,ln,12);y-=17
    return y-15
def header(id,t,sub,scale):
    seg((0,H-4),(W,H-4),teal,8);txt(34,H-39,'ԵԼԱԿԵՏԱՅԻՆ ՀԵՏԱԶՈՏՈՒՄ',12,teal,'B');txt(34,H-77,t,26,dark,'B');txt(35,H-98,sub,11,grey)
    seg((35,44),(W-35,44),'#B6C8C5',.8);txt(35,26,id+'   /   '+scale,10,teal,'B');txt(400,26,'Ծանոթագրություններով PDF • տեղում չչափագրված',10,grey);txt(W-190,26,'23.11.2026   /   R0',10)
header('Ե-00','Ընթերցման բանալի','Առաջին էջն ամբողջությամբ՝ միացված ծանոթագրություններով և երեք խոշորացված հատվածով։','աղբյուրային պատկեր • ազատ մասշտաբ')
source=next((P/'00-input').glob('*.pdf'))
with tempfile.TemporaryDirectory() as work:
    target=Path(work)/'marked';subprocess.run(['pdftoppm','-f','1','-l','1','-scale-to','2150','-singlefile','-png',str(source),str(target)],check=True,capture_output=True)
    im=Image.open(target.with_suffix('.png')).convert('RGB')
    c.drawImage(ImageReader(im),33,80,443,627,preserveAspectRatio=True,anchor='c')
    def crop(bounds,x,y,w,h):
        ox,oy=im.size;b=tuple(round(v*(ox if i%2==0 else oy)) for i,v in enumerate(bounds))
        c.drawImage(ImageReader(im.crop(b)),x,y,w,h,preserveAspectRatio=True,anchor='c')
    crop((.605,.569,.955,.811),481,475,258,231)
    crop((.26,.319,.482,.387),481,355,258,92)
    crop((.115,.535,.58,.606),481,207,258,116)
    for yy,lab in [(473,'Մուտքերի ուղղություններ և կանգնակ'),(352,'Սյան փոքր քառակուսին'),(203,'Կրող պատ և խաչվող նշաններ')]:txt(483,yy,lab,10,teal,'B')
y=block(760,679,'Տարածքների համարներ','№1 և №2 համարները կրկնվում են։ Մուտք №1-ի 8.84 մ² ընդհանուր նախամուտքը պատկերված է բնակարանի 8.71 մ² միջանցք-խոհանոցից առանձին։ Փոքր 0.80 մ² զուգարանի աջ կողմում դեղին նշանով ցույց է տրված կոյուղու կանգնակը։',393)
y=block(760,y,'Շարժման սահմաններ','Մուտքի կարմիր սլաքները ներկայացնում են ընտրության երեք դիրք։ Միակ լուսային կողմը բաց պատշգամբն է՝ թերթի վերևում։ Ստորին եզրին նշված է հարևանի տարածքի հետ համընկնում։',393)
y=block(760,y,'Կառուցվածքային երկու հենակետ','Հյուրասենյակի ստորին եզրը 5.92 մ անփոփոխ կրող պատն է։ Փոքր քառակուսին 5.52 մ չափագրի մոտ բետոնե սյուն է։ Ոչ պատը, ոչ սյունը տեղում չեն զննվել։',393)
block(760,y,'Աղբյուրի կարգավիճակ','Թվերը սկզբնաղբյուրի մակագրություններ են։ Սենյակների գործառույթները լրացված են տեխնիկական առաջադրանքից։ Մյուս՝ արխիվային հատակագիծը նախագծման մեջ չի օգտագործվել։',393)
c.showPage()
header('Ե-01','Առկա վիճակի վերակազմություն','Միավոր՝ մետր, տպել A3՝ 100%։ Կոորդինատների զրոն՝ կրող պատի հյուրասենյակի կողմից ձախ ծայրը։','1:60 • A3')
s=1000*mm/60
def xy(p):return (105+p[0]*s,337+p[1]*s)
def poly(points,line,fill=None):
    path=c.beginPath();path.moveTo(*xy(points[0]))
    for p in points[1:]:path.lineTo(*xy(p))
    path.close();c.setStrokeColor(HexColor(line));c.setFillColor(HexColor(fill or '#FFFFFF'));c.setLineWidth(.8);c.drawPath(path,fill=int(bool(fill)),stroke=1)
poly(D['features']['outer_boundary'],dark,'#D7DEDB')
loc={'bed_w':(.78,-3.05),'bed_e':(4.34,-3.05),'living':(1.66,2.12),'kitchen':(6.83,.40),'bath':(6.09,3.53),'balcony':(3.43,6.59),'wc':(9.80,-2.08),'vestibule':(7.12,-3.08)}
for k,room in r.items():
    poly(room['points'],dark,'#F0F5EC' if k=='balcony' else '#FFFFFF');x,y=xy(loc[k]);label={'kitchen':'№1 միջանցք-խոհանոց','vestibule':'№1 ընդհանուր','wc':'№2 ԶՍ'}.get(k,room['name'])
    txt(x,y,label,8,dark,'B');txt(x,y-11,f"{room['stated_area']:.2f} մ²",8)
for ln in D['lines']:
    a,b=ln['points'];seg(xy(a),xy(b),'#637572',.65)
poly(D['features']['column'],teal,teal)
for k,label in [('entry1','1'),('entry2','2'),('entry3','3'),('stack_marker','R')]:
    x,y=xy(D['features'][k][0]);c.setFillColor(HexColor('#9C532C'));c.circle(x,y,5,fill=1,stroke=0);txt(x+7,y+5,label,10,'#9C532C','B')
for a,b,lab,dx,dy in [((0,0),(5.92,0),'5.92',0,5),((0,0),(0,4.420046),'4.42',-26,0),((0,4.420046),(5.52093,4.420046),'5.52',0,-13),(r['balcony']['points'][3],r['balcony']['points'][4],'8.78',0,10),(r['balcony']['points'][0],r['balcony']['points'][5],'8.59',0,-13),(r['balcony']['points'][4],r['balcony']['points'][5],'3.51',5,0)]:
    a,b=xy(a),xy(b);txt((a[0]+b[0])/2+dx,(a[1]+b[1])/2+dy,lab,10,teal,'B')
xx,yy=xy((0,0));txt(xx-25,yy-16,'O',9,teal);seg((xx-2,yy),(xx+17,yy),teal,1.2);seg((xx,yy-2),(xx,yy+17),teal,1.2)
txt(705,692,'Մասշտաբի անկախ ստուգում',16,teal,'B')
def dis(k,i,j):return math.dist(r[k]['points'][i],r[k]['points'][j])
bal=r['balcony']['points']
rows=[('Կրող պատ',5.92,dis('living',0,5)),('Հյուրասենյակի կող',4.42,dis('living',4,5)),('Ճակատի ուղիղ մաս',5.52,dis('living',3,4)),('Պատշգամբի արտաքին եզր',8.59,math.dist(bal[0],bal[5])),('Բնակարանին կից եզր',8.78,math.dist(bal[3],bal[4])),('Աջ շեղված կող',3.51,math.dist(bal[4],bal[5])),('Ձախ կողմի ընդհանուր խորք',3.66,math.dist(bal[0],bal[3]))]
for X,lab in [(705,'Հենակետ'),(895,'PDF, մ'),(976,'Մոդել, մ'),(1071,'Δ, մմ')]:txt(X,661,lab,10,teal,'B')
for i,(lab,a,b) in enumerate(rows):
    yy=636-i*24;txt(705,yy,lab,10);txt(895,yy,f'{a:.2f}',11);txt(976,yy,f'{b:.4f}',11);txt(1071,yy,f'{(b-a)*1000:+.1f}',11)
y=block(705,426,'Ձախ կողի առանձնահատկություն','3.66 մ-ը խորքի ընդհանուր չափն է։ Վերին մասում կա կարճ խորշ։ Հաշվարկի համար պահվում են նրա բոլոր գագաթները։ Չի կիրառվում ուղղանկյուն պատշգամբի մոտարկում։',450)
y=block(705,y,'Ազդեցությունը նախագծի վրա','5.92 մ-ն մասշտաբի սահմանումն է։ Մնացած ստուգումները միլիմետրերի կարգի թվայնացման տարբերություն են ցույց տալիս։ Սա թերթի ներքին համահունչություն է․ պատերի կառուցվածքային բնույթը, բացվածքի անցանելիությունն ու տեղում հարդարված սահմանները դեռ չափագրված չեն։',450)
block(705,y,'Մակերեսների հսկում','Հինգ ներքին տարածքի գրված գումարը՝ 66.15 մ²։ Փակ ուրվագծերի գումարը՝ 66.18 մ²։ Պատահատվածների բոլոր թվայնացված երկարությունները՝ edges.csv, նոր վիճակի երկարությունները՝ after-edges.csv։',450)
c.showPage();c.save()
