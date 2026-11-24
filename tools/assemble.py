"""Միացնել հաստատված տեղական արտահանումները թերթակալված PDF ալբոմի մեջ։"""
import argparse, io, json
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from PIL import Image

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--survey',type=Path,required=True);parser.add_argument('--views',type=Path)
args=parser.parse_args()
W,H=420*mm,297*mm
pdfmetrics.registerFont(TTFont('a','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('b','C:/Windows/Fonts/arialbd.ttf'))
data=json.loads((root/'02-design/design.json').read_text(encoding='utf8'))
def text(c,x,y,txt,size=13,color='#233837',font='a'):
    c.setFillColor(HexColor(color));c.setFont(font,size);c.drawString(x,y,txt)
def para(c,x,y,txt,limit,size=14,lead=21):
    acc=''
    for word in txt.split():
        val=(acc+' '+word).strip()
        if acc and pdfmetrics.stringWidth(val,'a',size)>limit:
            text(c,x,y,acc,size);acc=word;y-=lead
        else: acc=val
    if acc:text(c,x,y,acc,size);y-=lead
    return y
def pagebuf():b=io.BytesIO();return b,Canvas(b,pagesize=(W,H))
def cover():
    b,c=pagebuf()
    c.setFillColor(HexColor('#F1F5EE'));c.rect(0,0,W,H,fill=1,stroke=0)
    text(c,59,774,'ՆԱԽՆԱԿԱՆ ՆԱԽԱԳԻԾ     /     23.11.2026',13,'#047B75','b')
    text(c,56,683,'Բնակարանի',55,'#193B38','b');text(c,56,616,'վերապլանավորում',55,'#193B38','b')
    text(c,60,565,'Ճարտարապետական և ինժեներական գծագրաշար',21)
    facts=[('03','Բնակարանային մուտք'),('28.62 մ²','Ստուդիայի մաքուր մակերես'),('0.00 մ','Ընտրված ընդլայնում')]
    for j,(v,label) in enumerate(facts):
        xx=61+j*211;text(c,xx,453,v,28,'#087E74','b');text(c,xx,428,label,11)
    y=para(c,60,339,'Պատշգամբի առջև են 11.00 մ² ննջասենյակը և 28.62 մ² միասնական հյուրասենյակ-խոհանոցը։ Ստորին 13.55 մ² սենյակը պատվիրատուի ցանկությամբ նախատեսված է քնելու օգտագործման համար։ Այն պատուհան չունի և գծագրում նշված է որպես ներքին օժանդակ սենք։',585,16,24)
    para(c,60,y-44,'Կառուցման համար որոշիչ են ճակատային միջնապատերի կառուցվածքը, կրող պատի գործող անցքը, կոյուղու միացման նիշը, փակ պատշգամբով լույսի հաշվարկը և ճակատային աշխատանքների համաձայնեցումը։',585,13,20)
    s=32; ox=763;oy=319
    palette={'B1':'#B4CBAF','B2':'#B4CBAF','ST':'#D6B778','BA':'#86B5B0','BAL':'#C2D9CF'}
    for room in data['rooms']:
        p=c.beginPath()
        for j,(x,y) in enumerate(room['points']):
            (p.moveTo if j==0 else p.lineTo)(ox+s*x,oy+s*y)
        p.close();c.setFillColor(HexColor(palette.get(room['id'],'#DCE3D9')));c.setStrokeColor(HexColor('#738D84'));c.setLineWidth(.7);c.drawPath(p,fill=1,stroke=1)
    text(c,60,55,'Հ-00    /    Ամփոփագիր    /    սխեմա',10,'#42706A','b');text(c,W-247,55,'R3   •   տեղում չչափագրված',10,'#42706A')
    c.showPage();c.save();b.seek(0);return b
writer=PdfWriter()
for name,src in [('Հանձնման ամփոփագիր',cover()),('Առկա վիճակ և հենակետեր',str(args.survey)),('Մուտքերի համեմատություն և ճարտարապետություն',str(root/'02-design/Architecture.pdf')),('Ինժեներական համակարգեր',str(root/'04-services/Engineering-R3.pdf'))]:
    writer.append(src,outline_item=name)
if args.views:writer.append(str(args.views),outline_item='Եռաչափ տեսախցիկներ')
writer.add_metadata({'/Title':'Բնակարանի վերապլանավորում և ինժեներական նախագծում','/Subject':'23.11.2026 • նախնական R3'})
out=root/'Բնակարանի նախագիծ.pdf';writer.write(str(out));print(str(out),len(PdfReader(out).pages))
