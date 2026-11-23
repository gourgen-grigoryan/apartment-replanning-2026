"""R2. Երեք բնակարանային տարբերակ նույն աղբյուրային գեոմետրիայով։"""
from copy import deepcopy
from frame import ROOT,base,old,area,rect,walls as frame_walls
import json,math

def length(p):return sum(math.dist(a,b) for a,b in zip(p,p[1:]))
def construct(entry):
    keep_rear=entry==1; low=entry==2
    rooms=[];walls=deepcopy(frame_walls);openings=[];furniture=[]
    def room(id,name,points,source):
        rooms.append(dict(id=id,name=name,points=points,source=source,area=area(points)))
    def wall(id,a,b,t=.10,kind='new'):walls.append(dict(id=id,a=a,b=b,t=t,kind=kind))
    def op(id,wall,a,b,kind='door',height=2.10,sill=0,action='նախնական',hinge='a',swing=[0,1]):
        openings.append(dict(id=id,wall=wall,a=a,b=b,kind=kind,height=height,sill=sill,action=action,hinge=hinge,swing=swing))
    def item(id,kind,x,y,w,d,h):furniture.append(dict(id=id,kind=kind,x=x,y=y,w=w,d=d,h=h))
    dp=4.420046;bx=2.90 if keep_rear else 13.55/dp;by=dp-10/bx if keep_rear else 0
    room('B1','Ննջասենյակ 1',rect(0,by,bx,dp),'living')
    sw=bx+.10
    front=[[sw,0],[5.92,0],[5.92,2.609093],[5.52093,2.609093],[5.52093,dp],[sw,dp]]
    if keep_rear:front=[[0,0]]+front[1:]+[[sw,by-.10],[0,by-.10]]
    room('ST','Ստուդիա · հյուրասենյակ',front,'living')
    wall('B1e',(bx+.05,max(0,by-.05)),(bx+.05,dp))
    if keep_rear:wall('B1s',(0,by-.05),(bx+.05,by-.05))
    yo=by+.15 if keep_rear else .42
    op('D-B1','B1e',(bx+.05,yo),(bx+.05,yo+.85),hinge='b',swing=[-1,0])
    top=[[5.765876,4.365002],[7.535546,4.384268],[7.620865,4.389772],[8.820828,4.378763],[8.820828,2.289837],[8.900642,2.289837]]
    if keep_rear:
        room('ST3','Ստուդիա · ճակատային գոտի',top+[[8.81151,.70],[7.56,.70],[7.56,1.64],[6.489707,1.64],[6.489707,2.843031],[5.765876,2.843031]],'bath+kitchen')
        room('B2','Ննջասենյակ 2',old['bed_w']['points'],'bed_w')
        hall2=[[6.489707,-.410079],[8.74927,-.410079],[8.8059,.6],[7.46,.6],[7.46,1.54],[6.489707,1.54]]
        wall('H2s',(7.51,.65),(8.81,.65));wall('H2r',(7.51,.65),(7.51,1.59))
    else:
        walls=[w for w in walls if w['id']!='S3']
        room('B2','Ննջասենյակ 2',top+[[8.74927,-.410079],[7.56,-.410079],[7.56,1.64],[6.489707,1.64],[6.489707,2.843031],[5.765876,2.843031]],'bath+kitchen')
        hall2=rect(6.489707,-.410079,7.46,1.54);wall('H2r',(7.51,-.41),(7.51,1.59))
    room('H2','Ննջասենյակների անցում' if not keep_rear else 'Ներքին մուտքային միջանցք',hall2,'kitchen')
    wall('H2n',(6.49,1.59),(7.51,1.59))
    op('D-E','H2n',(6.57,1.59),(7.37,1.59),'passage' if keep_rear else 'door')
    op('P-E','LE1',(6.20485,.828415),(6.20485,1.560502),'passage',action='գծագրված անցք․ ճշտել')
    if low:
        ba=rect(3.93,-5.149382,5.64,-2.60)
        h1=[[5.74,-5.149382],[6.864007,-5.149382],[6.910795,-.569707],[5.74,-.569707]]
        wall('BAw',(3.88,-5.15),(3.88,-2.55));wall('BAs',(3.88,-2.55),(5.69,-2.55));wall('H1w',(5.69,-5.15),(5.69,-.57))
        op('D-BA','H1w',(5.69,-4.04),(5.69,-3.24),swing=[-1,0]);bd=(5.69,-3.64);hc=5.69
    else:
        ba=[[5.12,-2.30],[6.8931,-2.30],[6.864007,-5.149382],[5.12,-5.149382]]
        h1=[[5.84,-2.20],[6.89416,-2.20],[6.910795,-.569707],[5.84,-.569707]]
        wall('BAw',(5.07,-5.15),(5.07,-2.25));wall('BAs',(5.07,-2.25),(6.895,-2.25));wall('H1w',(5.79,-2.25),(5.79,-.57))
        op('D-BA','BAs',(5.98,-2.25),(6.78,-2.25),hinge='b',swing=[0,-1]);bd=(6.38,-2.25);hc=5.79
    op('P-H','H1w',(hc,-1.91),(hc,-.94),'passage')
    room('H1','Բնակարանի ներքին միջանցք',h1,'bed_e');room('BA','Համատեղ սանհանգույց',ba,'bed_e')
    top_left=old['bed_e']['points'][1] if keep_rear else old['bed_w']['points'][0]
    lower_left=old['bed_e']['points'][0] if keep_rear else old['bed_w']['points'][1]
    st2=([top_left,[5.64,-.569707],[5.64,-2.50],[3.83,-2.50],[3.83,-5.149382],lower_left] if low else [top_left,[5.74,-.569707],[5.74,-2.20],[5.02,-2.20],[5.02,-5.149382],lower_left])
    if not keep_rear:st2.insert(1,[3.22834,-.569707])
    room('ST2','Ստուդիա · խոհանոց և ճաշասրահ',st2,'bed_e' if keep_rear else 'bed_w+bed_e')
    for id,k,name in [('BAL','balcony','Վիտրաժային պատշգամբ'),('SH','vestibule','Ընդհանուր նախամուտք'),('SR','wc','Խորդանոց՝ նախկին զուգարան')]:room(id,name,old[k]['points'],k)
    if keep_rear:
        op('D1','ENT1',(7.359405,-.495),(7.981404,-.495),'entry',action='գործող․ մաքուր լայնքը ստուգել')
        op('D-R','S3',(3.357,-2.419),(3.357,-1.269),swing=[-1,0])
    else:
        ey=-3.811 if low else -1.219;op('D'+str(entry),'ENT23',(6.978,ey-.45),(6.978,ey+.45),'entry',swing=[-1,0])
    op('D-LB','LB',(4.469586,-.285),(5.749363,-.285),'passage',action='գծագրված անցք․ տեղում հաստատել')
    op('W-LB','LB',(1.09,-.285),(2.361,-.285),'internal_window',.95,1.02,'բացվածքի բնույթը ստուգել')
    op('D-BAL','F1',(3.91,4.49),(4.81,4.49),'glazed_door',2.15,0)
    op('W1','F1',(.25,4.49),(2.06 if not keep_rear else 1.69,4.49),'window',1.12,.90)
    op('W-ST','F1',(3.28,4.49),(3.89,4.49),'window',2.14,.06)
    op('W-ST2','F1',(4.83,4.49),(5.43,4.49),'window',2.14,.06)
    op('W2a','F2',(6.905,4.525),(7.365,4.525),'window',1.13,.90)
    op('W2b','F2',(7.731,4.525),(8.821,4.525),'window',1.13,.90)
    op('D-SH','SH1',(8.715,-4.478),(8.715,-3.278),'entry_common',swing=[1,0])
    op('D-SR','SH7',(9.60,-2.441),(9.60,-1.772),'door',swing=[1,0])
    item('BED1','bed',.74,1.98,1.40,2,.53)
    if keep_rear:item('BED2','bed',.48,-4.83,1.4,2,.53)
    else:item('BED2','bed',7.66,1.80,1,2,.53)
    item('SO1','sofa',sw+.03,2.08,.84,2.0,.80)
    kt=3.20 if low else 4.40
    if keep_rear:
        # The narrow south-eastern wing serves as a pantry-free connector;
        # its dining and cooking furniture fits in the lit eastern alcove.
        item('KS','sink',8.12,2.30,.60,.56,.91);item('DW','dishwasher',8.12,2.86,.60,.45,.91);item('HB','hob',8.12,3.31,.60,.55,.91);item('FR','fridge',7.48,3.76,.60,.60,2.05)
        item('TB1','table',5.98,3.10,1.05,.70,.75);item('CH1','chair',6.16,2.57,.45,.45,.82)
    else:
        for id,k,y,d,h in [('FR','fridge',-5.08,.60,2.06),('HB','hob',-4.48,.62,.91),('DW','dishwasher',-3.86,.45,.91),('KS','sink',-3.41,.62,.91)]:
            item(id,k,kt,y,.60,d,h)
        item('TB1','table',.96,-3.45,1.50,.85,.75)
        for i,(x,y) in enumerate([(1.02,-3.97),(1.85,-3.97),(1.02,-2.53),(1.85,-2.53)]):item('CH'+str(i+1),'chair',x,y,.43,.43,.82)
        item('SO2','bench',.33,-5.04,2.10,.43,.47)
    if low:
        item('SHW','shower',3.95,-5.12,.90,.90,2.10);item('WC','toilet',4.99,-4.98,.59,.39,.76);item('BS','basin',3.95,-3.41,.43,.55,.86);item('WM','washer',4.62,-3.26,.60,.60,.85)
    else:
        item('SHW','shower',5.94,-5.12,.90,.90,2.10);item('WC','toilet',6.24,-3.78,.59,.40,.76);item('BS','basin',5.13,-3.14,.42,.54,.86);item('WM','washer',5.14,-5.08,.60,.60,.85)
    item('BT','table',6.70,6.86,.75,.75,.74)
    v=(5.11,-.285);bc=(4.36,4.49);mid=(hc,-1.425)
    guest=([(7.6704,-.495),(7.10,.32),(6.96,1.19),(6.205,1.19),(5.43,1.19),(4.45,1.51),bc] if keep_rear else ([(6.978,-3.811),(6.32,-3.811),(6.32,-1.425)] if low else [(6.978,-1.219),(6.44,-1.425)])+[mid,(5.11,-1.425),v,(4.55,.70),(4.55,1.72),bc])
    after=[v,(5.11,-1.425),mid,(6.32,-1.425)]+([(6.32,-3.64),bd] if low else [bd])
    night1=[(bx+.05,yo+.425),(3.70,yo+.425),(4.72,.64)]+after
    night2=([(3.357,-1.844),(4.11,-1.42),(5.11,-1.425),mid,(6.32,-1.425),bd] if keep_rear else [(6.97,1.59),(6.97,1.19),(6.205,1.19),(5.72,1.19),(5.11,.50)]+after)
    guest2=guest+[(4.36,4.83)]
    R=base['features']['stack_marker'][0];j=(5.42,-3.50) if low else (6.62,-2.48)
    sink=next(x for x in furniture if x['id']=='KS');k=(sink['x']+.30,sink['y']+sink['d']/2)
    arm=([k,(7.02,k[1]),(7.02,1.19),(5.45,1.19),(5.45,-1.98),j] if keep_rear else [k,(j[0],k[1]),j])
    tail=[j,(6.82,j[1]),(7.31,R[1]),R];sewer=dict(branch=arm,collector=tail,length=length(arm)+length(tail),drop=.03*length(arm)+.02*length(tail),available=None)
    return dict(revision='R2',units='m',height=2.8,selected=entry,entry=entry,rooms=rooms,walls=walls,openings=openings,furniture=furniture,column=base['features']['column'],stack=R,routes=dict(guest=guest2,night1=night1,night2=night2),lengths=dict(guest=length(guest),night1=length(night1),night2=length(night2)),sewer=sewer,circulation=sum(v['area'] for v in rooms if v['id'] in ('H1','H2')),studio=sum(v['area'] for v in rooms if v['id'] in ('ST','ST2','ST3')))
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
