"""Երեք մուտքով R3 էսքիզներ՝ նշումներով PDF-ի մետրային համակարգում։"""
from copy import deepcopy
from frame import ROOT, base, old, area, rect, walls as frame_walls
import json
import math

def run(points):
    return sum(math.dist(a,b) for a,b in zip(points,points[1:]))

def construct(entry):
    first, lower = entry==1, entry==2
    rooms=[]; walls=[deepcopy(w) for w in frame_walls if w['id'] not in ('LE1','LE2','LE3','LE4')]
    openings=[]; furniture=[]
    def room(id,name,points,source):
        rooms.append(dict(id=id,name=name,points=points,source=source,area=area(points)))
    def wall(id,a,b,t=.10):
        walls.append(dict(id=id,a=a,b=b,t=t,kind='new'))
    def op(id,wall,a,b,kind='door',height=2.1,sill=0,action='նախագծային',hinge='a',swing=(0,1)):
        openings.append(dict(id=id,wall=wall,a=a,b=b,kind=kind,height=height,sill=sill,action=action,hinge=hinge,swing=swing))
    def item(id,kind,x,y,w,d,h):
        furniture.append(dict(id=id,kind=kind,x=x,y=y,w=w,d=d,h=h))
    dp=old['living']['points'][4][1]; bx=11/dp; sw=bx+.10
    room('B1','Ննջասենյակ',rect(0,0,bx,dp),'living')
    wall('B1e',(bx+.05,0),(bx+.05,dp))
    op('D-B1','B1e',(bx+.05,.42),(bx+.05,1.27),hinge='b',swing=(-1,0))
    north=[[8.900642,2.289837],[8.820828,2.289837],[8.820828,4.378763],[7.620865,4.389772],[5.765876,4.365002],[5.520930,dp],[sw,dp]]
    south=[[sw,0],[5.92,0],[5.92,-.410079],[8.74927,-.410079]]
    if first:
        south=[[sw,0],[4.31,0],[4.31,.81],[8.8177,.81]]
        room('H2','Մուտքի առջևի միջանցք',[[4.41,0],[5.92,0],[5.92,-.410079],[8.74927,-.410079],[8.8119,.71],[4.41,.71]],'living+kitchen')
        wall('H2w',(4.36,0),(4.36,.76));wall('H2n',(4.36,.76),(8.815,.76))
        op('P-E','H2n',(4.53,.76),(5.45,.76),'passage')
    room('ST','Հյուրասենյակ-խոհանոց',south+north,'living+bath+kitchen')
    room('B2','Ներքին սենյակ · քնելու օգտագործում',old['bed_w']['points'],'bed_w')
    upper_l, lower_l=old['bed_e']['points'][1],old['bed_e']['points'][0]
    upper_r, lower_r=old['bed_e']['points'][2],old['bed_e']['points'][3]
    def xat(a,b,y):return a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1])
    ywall=-2.25;yt=ywall+.05;yb=ywall-.05
    xl=lambda y:xat(upper_l,lower_l,y)
    xr=lambda y:xat(upper_r,lower_r,y)
    hall=[[*upper_l],[*upper_r],[xr(yt),yt]]
    if lower:
        hall.extend([[*lower_r],[5.88,lower_r[1]],[5.88,yt]])
        hall.pop(2)
        ba=[[xl(yb),yb],[5.78,yb],[5.78,lower_l[1]],[*lower_l]]
        wall('BAr',(5.83,ywall),(5.83,lower_l[1]))
        wall('BAs',(xl(ywall),ywall),(5.83,ywall))
        op('D-BA','BAs',(4.70,ywall),(5.50,ywall),hinge='b',swing=(0,-1));bathdoor=(5.10,ywall)
    else:
        ba=[[xl(yb),yb],[xr(yb),yb],[*lower_r],[*lower_l]]
        wall('BAs',(xl(ywall),ywall),(xr(ywall),ywall))
        op('D-BA','BAs',(5.87,ywall),(6.67,ywall),hinge='b',swing=(0,-1));bathdoor=(6.27,ywall)
    hall.append([xl(yt),yt])
    room('H1','Բնակարանի սեփական միջանցք',hall,'bed_e')
    room('BA','Համատեղ սանհանգույց',ba,'bed_e')
    def s3(y):return 3.35+.03*(y+.57)/(-5.15+.57)
    op('D-R','S3',(s3(-2.045),-2.045),(s3(-1.195),-1.195),hinge='b',swing=(-1,0),action='միջնապատի բացվածքը ստուգել')
    if first:
        op('D1','ENT1',(7.359405,-.495),(7.981404,-.495),'entry',action='գործող բացվածք․ չափագրել')
    else:
        y=-3.811 if lower else -1.219
        op('D'+str(entry),'ENT23',(6.978,y-.45),(6.978,y+.45),'entry',swing=(-1,0))
    op('D-LB','LB',(4.469586,-.285),(5.749363,-.285),'passage',action='գծագրված․ մաքուր լայնքն ու շեմը չափագրել')
    op('D-BAL','F1',(3.91,4.49),(4.81,4.49),'glazed_door',2.15)
    for id,host,a,b,y,h,s in [('W1','F1',.25,1.70,4.49,1.12,.9),('W-ST','F1',3.28,3.89,4.49,1.12,.90),('W-ST2','F1',4.83,5.43,4.49,1.12,.90),('W2a','F2',6.905,7.365,4.525,1.13,.90),('W2b','F2',7.731,8.821,4.525,1.13,.90)]:
        op(id,host,(a,y),(b,y),'window',h,s)
    op('D-SH','SH1',(8.715,-4.478),(8.715,-3.278),'entry_common',swing=(1,0))
    op('D-SR','SH7',(9.60,-2.441),(9.60,-1.772),'door',swing=(1,0))
    for id,key,name in [('BAL','balcony','Վիտրաժային պատշգամբ'),('SH','vestibule','Ընդհանուր նախամուտք'),('SR','wc','Նախկին փոքր զուգարանի խորդանոց')]:
        room(id,name,old[key]['points'],key)
    item('BED1','bed',.35,1.93,1.0,2.0,.54)
    item('BED2','bed',1.0,-4.77,1.4,2.0,.54)
    item('SO1','sofa',sw+.15,1.83,.84,1.94,.80)
    ky=.93 if first else .05
    for id,kind,off,depth,h in [('FR','fridge',0,.60,2.0),('HB','hob',.60,.62,.91),('DW','dishwasher',1.22,.45,.91),('KS','sink',1.67,.62,.91)]:
        item(id,kind,8.10,ky+off,.60,depth,h)
    item('TB1','table',5.90,2.16,1.42,.80,.75)
    for i,(x,y) in enumerate([(6.03,1.65),(6.82,1.65),(6.03,3.04),(6.82,3.04)]):item('CH'+str(i+1),'chair',x,y,.43,.43,.82)
    if lower:
        item('SHW','shower',3.59,-5.07,.90,.90,2.1);item('WM','washer',4.66,-5.05,.6,.6,.85)
        item('BS','basin',3.55,-3.36,.46,.54,.86);item('WC','toilet',5.11,-4.22,.58,.40,.76)
    else:
        item('SHW','shower',5.91,-5.08,.90,.90,2.1);item('WM','washer',3.64,-5.04,.6,.6,.85)
        item('BS','basin',3.57,-3.54,.46,.60,.86);item('WC','toilet',6.20,-3.85,.59,.40,.76)
    item('BT','table',6.70,6.86,.75,.75,.74)
    v=(5.11,-.285);bc=(4.36,4.49);rdoor=(s3(-1.62),-1.62)
    if first:guest=[(7.6704,-.495),(7.48,.28),(5.08,.28),(5.00,.76),(4.58,1.60),bc]
    else:
        guest=([(6.978,-3.811),(6.36,-3.811),(6.36,-1.26)] if lower else [(6.978,-1.219),(6.31,-1.18)])+[(5.11,-1.18),v,(4.78,.64),(4.43,1.60),bc]
    night1=[(bx+.05,.845),(3.66,1.21),(4.98,1.14),(5.00,.76),v,(5.11,-1.28),bathdoor]
    night2=[rdoor,(4.10,-1.62),(bathdoor[0],-1.63),bathdoor]
    routes=dict(guest=guest+[(4.36,4.86)],night1=night1,night2=night2)

    R=base['features']['stack_marker'][0]
    sink=next(f for f in furniture if f['id']=='KS');k=(sink['x']+.3,sink['y']+sink['d']/2)
    j=(k[0],R[1])  # հանգույց՝ ընդհանուր նախամուտքի հատակի գոտում, պայմանական համաձայնեցման ենթակա
    branch=[k,j]
    collector=[j,R]
    sewer=dict(branch=branch,collector=collector,length=run(branch)+run(collector),drop=.03*run(branch)+.02*run(collector),available=None)
    return dict(revision='R3',units='m',height=2.80,selected=entry,entry=entry,rooms=rooms,walls=walls,openings=openings,furniture=furniture,column=base['features']['column'],stack=R,routes=routes,lengths=dict(guest=run(guest),night1=run(night1),night2=run(night2)),sewer=sewer,circulation=sum(r['area'] for r in rooms if r['id'].startswith('H')),studio=next(r['area'] for r in rooms if r['id']=='ST'),windowless='B2',reported_sleeping_area=13.55)

opts=[construct(i) for i in [1,2,3]]
out=ROOT/'02-design';(out/'options').mkdir(parents=True,exist_ok=True)
for v in opts:(out/'options'/f'entry-{v["entry"]}.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
data=deepcopy(opts[-1])
data['options']=[{k:o[k] for k in ['entry','lengths','sewer','circulation','studio']} for o in opts]
bal=old['balcony']['points']; p,q=bal[3],bal[4]
length=math.dist(p,q); normal=[-(q[1]-p[1])/length,(q[0]-p[0])/length]
# Parallel offset one metre. Intersections with both sloping side edges.
def hit(a,b):
    t=(1-sum((a[j]-p[j])*normal[j] for j in (0,1)))/sum((b[j]-a[j])*normal[j] for j in (0,1))
    return [a[j]+t*(b[j]-a[j]) for j in (0,1)]
left,right=hit(p,bal[2]),hit(q,bal[5]); strip=[p,q,right,left]
def offset_hit(a,b,dist):
    f=dist/sum((b[j]-a[j])*normal[j] for j in (0,1));return [a[j]+f*(b[j]-a[j]) for j in (0,1)]
innerl,innerr=offset_hit(p,bal[2],.88),offset_hit(q,bal[5],.88)
def clip(poly,threshold):
    out=[]
    for a,b in zip(poly[-1:]+poly[:-1],poly):
        da=sum((a[j]-p[j])*normal[j] for j in (0,1))-threshold;db=sum((b[j]-p[j])*normal[j] for j in (0,1))-threshold
        if (da>=0)!=(db>=0):out.append([a[j]+(b[j]-a[j])*da/(da-db) for j in (0,1)])
        if db>=0:out.append(b)
    return out
column_overlap=area(clip(data['column'],0))
data['extension']=dict(strip=strip,inner=[p,q,innerr,innerl],residual=[left,right,bal[5],bal[0],bal[1],bal[2]],gross=area(strip),net=area([p,q,innerr,innerl])-column_overlap,column_overlap=column_overlap,frame=area(strip)-area([p,q,innerr,innerl]),balcony_left=area(bal)-area(strip),depth=1.0)

(out/'design.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
for o in opts:print(o['entry'],[(v['id'],round(v['area'],3)) for v in o['rooms']],o['studio'],o['lengths'],o['sewer']['length'],o['sewer']['drop'])
