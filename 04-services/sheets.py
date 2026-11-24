"""Ձևավորել A3 գծագրերը՝ PDF-ի տեղական կոորդինատներից (մ):"""
from pathlib import Path
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for name, font in [('Arm','sylfaen.ttf'),('Sans','segoeui.ttf'),('Bold','segoeuib.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/font)))
W,H=landscape(A3)
INK='#172D39'; GRAY='#536776'; SILVER='#CBDADE'; TEAL='#007C77'
def color(v): return HexColor(v)
def txt(c,x,y,s,size=12,font='Arm',tone=INK):
    c.setFillColor(color(tone)); c.setFont(font,size); c.drawString(x,y,str(s).replace('→','›') if font=='Arm' else str(s))
def ln(c,x1,y1,x2,y2,tone=GRAY,width=1):
    c.setStrokeColor(color(tone)); c.setLineWidth(width); c.line(x1,y1,x2,y2)
def wrap(text,font,size,width):
    lines=[]
    for par in str(text).split('\n'):
        line=''
        for word in par.split():
            new=(line+' '+word).strip()
            if line and pdfmetrics.stringWidth(new,font,size)>width:
                lines.append(line); line=word
            else: line=new
        lines.append(line)
    return lines
def para(c,x,y,text,width,size=12,leading=17,font='Arm',tone=INK):
    for s in wrap(text,font,size,width): txt(c,x,y,s,size,font,tone); y-=leading
    return y
def heading(c,x,y,s,width=None):
    txt(c,x,y,s,15,'Bold',TEAL)
    return y-25
def note(c,x,y,title,text,width):
    y=heading(c,x,y,title)
    return para(c,x,y,text,width,12,17)-15
def table(c,x,y,widths,headers,rows,size=11,leading=15):
    full=sum(widths); margin=7
    for j,row in enumerate([headers]+list(rows)):
        font='Bold' if not j else 'Arm'
        lines=[wrap(a,font,size,w-2*margin) for a,w in zip(row,widths)]
        rh=max(map(len,lines))*leading+10
        if j==0 or j%2==0:
            c.setFillColor(color('#DDEBEA' if not j else '#F2F6F7'))
            c.rect(x,y-rh,full,rh,fill=1,stroke=0)
        xx=x
        for w,ss in zip(widths,lines):
            for i,s in enumerate(ss): txt(c,xx+margin,y-7-size-i*leading,s,size,font)
            xx+=w
        ln(c,x,y-rh,x+full,y-rh,SILVER,.5); y-=rh
    return y-14
def page(c,code,title,subtitle,scale='սխեմա'):
    c.setFillColor(color('#F9FBFB')); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(color(TEAL)); c.rect(35,H-55,5,35,stroke=0,fill=1)
    txt(c,51,H-40,title,24,'Bold')
    txt(c,51,H-63,subtitle,12,'Arm',GRAY)
    ln(c,35,H-78,W-35,H-78,SILVER,.8)
    ln(c,35,48,W-35,48,SILVER,.8)
    txt(c,38,26,code+'    /    '+scale,11,'Bold')
    txt(c,360,26,'Նախնական նախագիծ  ·  Կապակցումները և նիշերը ենթակա են չափագրման',11,'Arm',GRAY)
    txt(c,W-185,26,'23.11.2026    /    R3',11,'Bold')
def pxy(p): return (61+p[0]*72/0.0254/60,352+p[1]*72/0.0254/60)
def path(c,points,tone,width=1.5,dash=(),close=False,fill=None):
    if not points: return
    c.saveState(); c.setStrokeColor(color(tone)); c.setLineWidth(width); c.setDash(dash)
    if fill: c.setFillColor(color(fill))
    p=c.beginPath(); p.moveTo(*pxy(points[0]))
    for b in points[1:]: p.lineTo(*pxy(b))
    if close: p.close()
    c.drawPath(p,fill=int(bool(fill)),stroke=1); c.restoreState()
def arrow(c,a,b,tone):
    x1,y1=pxy(a);x2,y2=pxy(b); dx=x2-x1;dy=y2-y1;length=math.hypot(dx,dy)
    if length<10: return
    u,v=dx/length,dy/length;xx=x1+dx*.6;yy=y1+dy*.6
    ln(c,xx-6*u-3*v,yy-6*v+3*u,xx,yy,tone,1.4)
    ln(c,xx-6*u+3*v,yy-6*v-3*u,xx,yy,tone,1.4)
def dot(c,p,label,tone,dx=5,dy=4,r=3):
    x,y=pxy(p); c.setFillColor(color(tone)); c.circle(x,y,r,stroke=0,fill=1)
    if label:
        tw=pdfmetrics.stringWidth(label,'Bold',8.4)
        c.setFillColor(color('#FFFFFF')); c.rect(x+dx-1,y+dy-1.5,tw+2,10,stroke=0,fill=1)
        txt(c,x+dx,y+dy,label,8.4,'Bold',tone)
def legend(c,x,y,items):
    for label,col,ds in items:
        c.saveState(); c.setDash(ds);ln(c,x,y+3,x+32,y+3,col,2); c.restoreState()
        txt(c,x+42,y,label,11,'Arm');y-=19
    return y-7
def scale_bar(c):
    x,y=65,68; unit=72/0.0254/60
    for i in range(3):
        ln(c,x+i*unit,y,x+(i+1)*unit,y,INK if i!=1 else SILVER,4)
    txt(c,x,y+7,'0',9,'Sans');txt(c,x+unit*3-3,y+7,'3 մ',9,'Sans')
    txt(c,x+unit*3+28,y,'1:60  ·  Տպել A3, 100%',9,'Arm',GRAY)
def draw_base(c,base,arch):
    for key in ['vestibule','wc','balcony']:
        path(c,base['rooms'][key]['points'],SILVER,1,close=True,fill='#F1F4F4')
    for rec in arch['spaces']:
        path(c,rec['poly'],'#A3B5BA',.8,close=True,fill='#FFFFFF')
    for w in arch.get('walls',[]):
        a,b=w['a'],w['b']; length=math.dist(a,b)
        if length==0:continue
        uv=[(b[i]-a[i])/length for i in range(2)]
        def station(v):return (v[0]-a[0])*uv[0]+(v[1]-a[1])*uv[1]
        def xy(t):return [a[i]+uv[i]*t for i in range(2)]
        holes=[sorted((max(0,station(v['a'])),min(length,station(v['b'])))) for v in arch.get('openings',[]) if v['wall']==w['id']]
        last=0
        for lo,hi in sorted(holes)+[(length,length)]:
            if lo>last:path(c,[xy(last),xy(lo)],'#8B9EA4',max(1,w.get('t',.1)*31))
            last=max(last,hi)
    for f in arch.get('furniture',[]):
        x,y,w,d=[f[k] for k in ('x','y','w','d')]
        path(c,[(x,y),(x+w,y),(x+w,y+d),(x,y+d)],'#CDD8D8',.55,close=True)
    for label,p in [('B1',(.21,.25)),('ST',(3.07,.27)),('B2',(.42,-1.18)),('H1',(3.75,-1.92)),('BA',(3.77,-2.65))]:
        txt(c,*pxy(p),label,8,'Bold','#738785')
    txt(c,*pxy((7.12,-1.31)),'№3',8,'Bold','#627A78')
    path(c,base['features']['column'],'#546F77',1,close=True,fill='#9BAFB0')
    txt(c,*pxy((3.9,6.7)),'Պատշգամբ',10,'Arm',GRAY)
    txt(c,*pxy((7.2,-4.65)),'Ընդհանուր',9,'Arm',GRAY)
    scale_bar(c)
