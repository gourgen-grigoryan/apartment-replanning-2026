"""R2 • նախագծային երկրաչափություն, մետր։ Գործարկել Project թղթապանակից։"""
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'01-source/base.json').read_text(encoding='utf-8-sig'))
old=base['rooms']
rooms=[]; walls=[]; openings=[]; furniture=[]
def area(p): return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))/2
def room(id,name,p,orig):
    rooms.append(dict(id=id,name=name,points=p,area=area(p),source=orig))
def wall(id,a,b,t,kind='existing'):
    walls.append(dict(id=id,a=a,b=b,t=t,kind=kind))
def op(id,wall,a,b,kind,height=2.1,sill=0,action='նախագծային'):
    openings.append(dict(id=id,wall=wall,a=a,b=b,kind=kind,height=height,sill=sill,action=action))
def item(id,kind,x,y,w,d,h): furniture.append(dict(id=id,kind=kind,x=x,y=y,w=w,d=d,h=h))
def rect(x,y,X,Y): return [[x,y],[X,y],[X,Y],[x,Y]]
wall('LB',(0,-.285),(5.92,-.285),.57,'bearing')
wall('W-L',(-.125,0),(-.125,4.42),.25)
wall('F1',(0,4.49),(5.644,4.49),.14,'facade')
wall('F2',(5.644,4.525),(8.92,4.525),.28,'facade')
wall('LE1',(6.20485,0),(6.20485,2.726),.5697)
wall('LE2',(5.644,2.725),(6.485,2.725),.236)
wall('LE3',(5.6434,2.609),(5.6434,4.420),.245)
wall('LE4',(6.40,2.25),(6.40,2.84),.18)
wall('E1',(8.884,-.41),(9.035,2.29),.27)
wall('E2',(8.996,2.29),(8.996,4.52),.35)
wall('ENT1',(6.48,-.495),(8.76,-.495),.171)
wall('S1',(.16,-5.30),(6.90,-5.30),.30)
wall('S2',(.151,-.58),(.181,-5.15),.215)
wall('S3',(3.35,-.57),(3.38,-5.15),.24)
wall('ENT23',(6.985,-.58),(6.962,-5.15),.17)
wall('LB-E',(5.92,-.49),(6.91,-.49),.16)
for i,(a,b) in enumerate(zip(old['vestibule']['points'],old['vestibule']['points'][1:]+old['vestibule']['points'][:1])):
    if i not in (3,4): wall('SH'+str(i),a,b,.12)
for i,(a,b) in enumerate(zip(old['wc']['points'],old['wc']['points'][1:]+old['wc']['points'][:1])):
    if i!=2: wall('SR'+str(i),a,b,.10)
