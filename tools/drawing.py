"""Հայերեն ճարտարապետական ալբոմ. տվյալները կարդացվում են ընդհանուր մոդելից։"""
import json, math, csv
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

P=Path(__file__).resolve().parents[1]
db=json.loads((P/'02-design/design.json').read_text(encoding='utf8'))
base=json.loads((P/'01-source/base.json').read_text(encoding='utf-8-sig'))
for n,f in [('reg','arial.ttf'),('bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
r={a['id']:a for a in db['rooms']}
f={a['id']:a for a in db['furniture']}
W,H=420*mm,297*mm
C=Canvas(str(P/'02-design/Architecture.pdf'),pagesize=(W,H))
C.setTitle('Բնակարանի վերապլանավորում | Ճարտարապետական ալբոմ')
ink='#20373B'; teal='#007E80'; red='#B3473D'; gold='#A76C18'; blue='#3461AC'; grey='#67797A'; paper='#F8F8F3'
def col(v):return HexColor(v)
def txt(x,y,t,s=11,c=ink,font='reg',align='left'):
    C.setFillColor(col(c));C.setFont(font,s)
    getattr(C,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,y,str(t).replace('․','.').replace('↗','→'))
def line(a,b,color=ink,w=1,dash=()):
    C.setLineWidth(w);C.setLineCap(0);C.setStrokeColor(col(color));C.setDash(dash);C.line(*a,*b);C.setDash([])
def box(x,y,w,h,fill,outline=None,lw=1):
    C.setFillColor(col(fill));C.setStrokeColor(col(outline or fill));C.setLineWidth(lw);C.rect(x,y,w,h,fill=1,stroke=int(bool(outline)))
def path(ps,color=ink,w=1,fill=None,close=False,dash=()):
    C.setStrokeColor(col(color));C.setLineWidth(w);C.setDash(dash);p=C.beginPath();p.moveTo(*ps[0])
    for q in ps[1:]:p.lineTo(*q)
    if close:p.close()
    if fill:C.setFillColor(col(fill))
    C.drawPath(p,stroke=1,fill=int(bool(fill)));C.setDash([])
def wrap(x,y,words,width,s=12,lead=18,color=ink,font='reg'):
    row=''
    for w in words.split():
        test=(row+' '+w).strip()
        if row and pdfmetrics.stringWidth(test,font,s)>width:
            txt(x,y,row,s,color,font);y-=lead;row=w
        else:row=test
    if row:txt(x,y,row,s,color,font);y-=lead
    return y
def pg(code,title,subtitle,scale='սխեմա'):
    box(0,0,W,H,'#FFFFFF');box(0,H-9,W,9,teal)
    txt(35,H-40,'ԲՆԱԿԱՐԱՆԻ ՎԵՐԱՊԼԱՆԱՎՈՐՈՒՄ    /    ՃԱՐՏԱՐԱՊԵՏՈՒԹՅՈՒՆ',11,teal,'bold')
    txt(35,H-77,title,27,ink,'bold');txt(36,H-100,subtitle,11,grey)
    line((35,44),(W-35,44),'#B0C3BE',.65)
    txt(35,26,code+'   /   '+scale,10,teal,'bold')
    txt(W/2,26,'Նախնական նախագիծ  •  դաշտային չափագրումն ու մասնագիտական հաստատումը բաց են',9,grey,align='center')
    txt(W-35,26,'23.11.2026    /    R2',10,ink,align='right')
def note(x,y,title,body,width=380):
    txt(x,y,title,14,teal,'bold');return wrap(x,y-22,body,width,12,18)-19
def table(x,y,widths,rows,size=10):
    for i,row in enumerate(rows):
        lines=[]
        for val,width in zip(row,widths):
            acc=[];ln=''
            for w in str(val).split():
                v=(ln+' '+w).strip()
                if ln and pdfmetrics.stringWidth(v,'bold' if not i else 'reg',size)>width-17:acc.append(ln);ln=w
                else:ln=v
            acc.append(ln);lines.append(acc)
        h=max(map(len,lines))*(size+4)+14
        box(x,y-h,sum(widths),h,teal if i==0 else ('#F2F6F3' if i%2 else '#FFFFFF'))
        xx=x
        for ls,ww in zip(lines,widths):
            for j,v in enumerate(ls):txt(xx+8,y-size-7-j*(size+4),v,size,'#FFFFFF' if i==0 else ink,'bold' if i==0 else 'reg')
            xx+=ww
        y-=h
    return y
S=1000*mm/60
def xy(p):return (95+p[0]*S,338+p[1]*S)
def world(points,c=ink,w=1,fill=None,closed=False,dash=()):path([xy(v) for v in points],c,w,fill,closed,dash)
def mark(p,t,s=9,dy=0,clr=ink):x,y=xy(p);txt(x,y+dy,t,s,clr,'bold','center')
def cut(a,b,u):return [a[i]+(b[i]-a[i])*u for i in (0,1)]
def arr(seq,color,w=2,dash=()):
    ps=[xy(p) for p in seq];path(ps,color,w,dash=dash)
    a,b=ps[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0]);verts=[b]+[(b[0]-8*math.cos(ang+k),b[1]-8*math.sin(ang+k)) for k in (-.46,.46)];path(verts,color,.5,color,True)
def scale():
    x,y=45,62
    for j in range(3):box(x+j*S,y,S,3,ink if j%2==0 else '#AEBBB8')
    txt(x,y+7,'0',8,grey);txt(x+3*S,y+7,'3 մ',8,grey)
def show():C.showPage()
