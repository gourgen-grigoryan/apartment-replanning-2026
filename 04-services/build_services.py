"""Վերահաշվարկել վեց ինժեներական թերթախմբերի ելակետերը R3 մոդելից։"""
from pathlib import Path
import json, math, csv
from collections import defaultdict

DIR=Path(__file__).resolve().parent
BASE=json.loads((DIR.parent/'01-source/base.json').read_text(encoding='utf8'))
DATA=DIR.parent/'02-design/design.json'
R=tuple(BASE['features']['stack_marker'][0])
routes=[]; elements=[]; drains=[]; demand=[]; lights=[]
def route(id,system,points,d,name,**kwargs):
    points=[list(map(float,p)) for p in points]
    pts=[p for i,p in enumerate(points) if i==0 or math.dist(p,points[i-1])>1e-7]
    o=dict(id=id,system=system,points=pts,diameter_m=d,name=name,**kwargs)
    routes.append(o); return o
def item(id,system,p,size,name,**kwargs):
    o=dict(id=id,system=system,point=list(p),size=list(size),name=name,**kwargs)
    elements.append(o);return o
def line_length(points): return sum(math.dist(a[:2],b[:2]) for a,b in zip(points,points[1:]))
def summed3(line): return sum(math.dist(a,b) for a,b in zip(line,line[1:]))
def at_z(line,z): return [(*p[:2],z) for p in line]
def area(poly): return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2
def save(name,obj): (DIR/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
def csvfile(name,headers,rows):
    with (DIR/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)

def make_data(arch,spaces,fixtures,location):
    # Ռաստրի/տեղում չափագրման բացակայության դեպքում արտաքին կապերը պայմանական են։
    wc,sh,b,k,dw,wm=[fixtures[key] for key in ('WC','SH','B','K','DW','WM')]
    scheme=arch['sewer']; common=[tuple(p) for p in scheme['collector']]; j=common[0]
    # Այս Z-ը միայն հատույթի փորձնական նիշ է: Իրական ցանցին միացումը բաց է։
    zr=-.31;dj=.110;zj=zr+.02*line_length(common)
    def drain(id,name,points,d,slope,down,tag):
        run=line_length(points);z0=down+slope*run;L=0;zp=[]
        for i,p in enumerate(points):
            if i:L+=math.dist(p,points[i-1])
            zp.append([*p,z0-slope*L+d/2])
        r=route(id,'DWV',zp,d,name,slope=slope,invert_end=round(down,5),invert_start=round(z0,5),length_plan=run,endpoint=tag)
        return r
    m=drain('D00','Ընդհանուր հավաքիչ',common,dj,.02,zr,'R')
    # Յուրաքանչյուր ճյուղ՝ մինչև առանձին հասանելի եռաբաշխիչ կամ հավաքիչ։

    kpath=[tuple(p) for p in scheme['branch']]
    bpaths=[
        ('D01','Խոհանոցի լվացարան',kpath,.050,.03),
        ('D02','Զուգարանակոնք',[wc,(6.81,wc[1]),(7.35,-2.72),j],.110,.02),
        ('D03','Ցնցուղ',[sh,(6.75,sh[1]),(6.75,-2.94),(7.35,-2.72),j],.050,.03),
        ('D04','Սանհանգույցի լվացարան',[b,(6.56,b[1]),(7.35,-2.72),j],.050,.03),
    ]
    for id,n,pts,d,i in bpaths:
        r=drain(id,n,pts,d,i,zj,'J')
        drains.append(dict(id=id,name=n,len=r['length_plan'],total=r['length_plan']+m['length_plan'],h=r['invert_start']-zr,z0=r['invert_start'],end=zj,d=d,s=i))
        outlet={'D01':.50,'D02':.18,'D03':-.09+d/2,'D04':.50}[id]
        route('V'+id[1:],'DROP',[[*pts[0],outlet],r['points'][0]],d,'Սիֆոնից կամ սարքի ելքից ուղղաձիգ կապ',endpoint=id)
    for id,name,src in [('D05','Սպասք լվացող մեքենա',dw),('D06','Լվացքի մեքենա',wm)]:
        if id=='D05':
            receiving=k;base_row=drains[0];dest='D01'; target='K'
        else:
            receiving=b;base_row=drains[3];dest='D04';target='B'
        flex=[(*src,.48),(*src,.68),(*receiving,.68),(*receiving,.50)]
        route(id,'FLEX',flex,.025,name,endpoint=dest)
        drains.append(dict(id=id,name=name,len=line_length(flex),total=line_length(flex)+base_row['total'],h=base_row['h'],z0=flex[0][2],high_loop=.68,end=.50,d=.025,s=None,pump_to=target,downstream=dest))
    item('R','DWV',(*R,.32),(.15,.15,.64),'Կանգնակի պայմանական ծավալ')
    item('J','DWV',(*j,zj+.06),(.20,.20,.14),'Հավաքման հանգույց')
    for id,pt in [('CO1',j),('CO2',k),('CO3',R)]:
        item(id,'ACCESS',(*pt,.30),(.22,.10,.28),'Մաքրման և ստուգման կետ')

    man=(6.65,-2.62)
    item('MC','CW',(*man,.64),(.40,.13,.35),'Սառը ջրի կոլեկտոր')
    item('MH','HW',(man[0],man[1]+.12,.91),(.40,.13,.22),'Տաք ջրի կոլեկտոր')
    for system,provider,dist in [('CW','WS-C',0),('HW','WS-H',.10)]:
        source=(6.70+dist,-2.78)
        p=(*source,.70+dist)
        item(provider,system,p,(.09,.09,.24),'Պայմանական մուտքային հանգույց')
        mz=.64 if system=='CW' else .91
        manifold=(man[0],man[1]+(.12 if system=='HW' else 0),mz)
        route('F-'+system,system,[p,(manifold[0],source[1],p[2]),manifold],.026,'Մուտքից մինչև կոլեկտոր',unverified_source=True)
        consumers=[('K',k,.55),('B',b,.55),('SH',sh,1.10)]
        if system=='CW':consumers += [('WC',wc,.24),('DW',dw,.55),('WM',wm,.65)]
        for n,pt,h in consumers:
            z=-.05 if system=='CW' else -.075
            if pt[1]>=0:
                plan=[man,(6.65+dist,man[1]),(6.65+dist,-2.35),(6.65+dist,-.90),(6.65+dist,pt[1]),pt]
            else:plan=[man,(6.49+dist,man[1]),(6.49+dist,pt[1]),pt]
            route(system+'-'+n,system,[manifold,*at_z(plan,z),(*pt,h)],.016,'Ջրաբաժան կետ '+n)

    # Միաֆազ համեմատական սցենար, հաշվարկային ընդհանուր հզորությունը ըստ պայմանագրի հաստատվում է առանձին։
    consumer_rows=[
        ('Q1','Լուսավորում, բնակելի գոտի',.20,1.0,10,1.5),
        ('Q2','Լուսավորում, օժանդակ գոտի',.16,1.,10,1.5),
        ('Q3','Ստուդիայի և ճաշասենյակի վարդակներ',2.00,.50,16,2.5),
        ('Q4','Ննջասենյակի և ներքին սենյակի վարդակներ',2.00,.40,16,2.5),
        ('Q5','Խոհանոցի սեղանի վարդակներ',2.50,.70,16,2.5),
        ('Q6','Ինդուկցիոն սալօջախ',7.20,.60,32,6),
        ('Q7','Ջեռոց',3.00,.70,16,2.5),
        ('Q8','Սպասք լվացող մեքենա',2.00,.60,16,2.5),
        ('Q9','Լվացքի մեքենա',2.20,.60,16,2.5),
        ('Q10','Սառնարան և օդաքաշ',.40,1.,10,2.5),
        ('Q11','Ջերմային պոմպի արտաքին բլոկ',2.20,.90,16,2.5),
        ('Q12','Օդափոխություն և սրբիչաչորացուցիչ',.72,.90,10,1.5),
        ('Q13','Ճաշասրահի լրացուցիչ վարդակներ',1.50,.40,16,2.5),
    ]
    for id,n,kw,fusek,cb,s in consumer_rows:
        demand.append(dict(id=id,name=n,kw=kw,simult=fusek,design_kw=kw*fusek,amps=kw*1000/230,cb=cb,mm2=s))
    panel=location['panel']
    item('DB','POWER',(*panel,1.45),(.12,.38,.55),'Բնակարանային վահանակ՝ արևելյան պատին')
    for n,key,pt,h,cid in location['sockets']:
        item(n,'POWER',(*pt,h),(.08,.055,.08),key,circuit=cid)
        z=2.55
        # Դեպի վերին գոտի բոլոր գծերն անցնում են կրող պատի արևելյան ծայրից այն կողմ։
        path=[panel]
        if n in ('E1','E2','E3','E5','E6','E7','E8','E10','E11','E13','E14'):
            path += [(6.65,panel[1]),(6.65,.25)]
        if n=='E11':
            path += [(6.65,4.10),(6.65,7.94),(pt[0],7.94)]
        elif n=='E14':
            path += [(6.65,2.70),(5.22,2.70),(5.22,pt[1])]
        elif n in ('E1','E3','E13'):
            path += [(3.15,.25),(3.15,pt[1])]
        else:
            path += [(pt[0],path[-1][1])]
        route('EL-'+n,'CABLE',[(*panel,1.45),*at_z(path,z),(*pt,z),(*pt,h)],.016,key,circuit=cid)

    for rid,v in location['lightzones'].items():
        pts,names,area_val,target,each,g,role=v
        uf,mf=.60,.80
        lamps=math.ceil(target*area_val/(each*uf*mf))
        flux=lamps*each
        if len(pts)!=lamps:
            raise ValueError(f'{rid}: {len(pts)} plan, {lamps} needed; area {area_val}')
        for i,p in enumerate(pts):
            item(f'{rid}-{i+1:02}','LIGHT',(*p,2.72),(.18,.18,.06),names,group=g,flux_lm=each)
        lights.append(dict(zone=names,id=rid,area=area_val,target=target,count=lamps,each=each,required=target*area_val/(uf*mf),calc=flux*uf*mf/area_val,plane='0.00',role=role))
    for id,grp,pt in location['switches']:
        item(id,'SWITCH',(*pt,1.00),(.075,.05,.08),'Կառավարման կետ',group=grp)
    for id,pt,z,sz,lm,name,group in location['extra_lights']:
        item(id,'LIGHT',(*pt,z),sz,name,flux_lm=lm,group=group)
    for e in elements:
        if e['system'] in ('LIGHT','SWITCH'):
            groups=e['group'].split('/')
            e['circuit']='Q1' if all(g in {'G1','G2','G3','G7','G8'} for g in groups) else 'Q2'
    return zr,zj,common

def make_hvac(arch,loc,fixtures):
    out=(8.19,8.49,1.05)
    item('HP-OD','HVAC',out,(.78,.34,.70),'Արտաքին բլոկ · բաց օդ, հաստատել հենարանը')
    k=fixtures['K'];f=(*k,.67)
    item('CD-F','COND',f,(.09,.09,.12),'Սիֆոնավոր ձագար, օդային խզում')
    for code,p in loc['indoor'].items():
        size=(.22,.70,.30) if code in ('B1','B2') else (.72,.23,.30)
        item('IU-'+code,'HVAC',(*p,2.29),size,'Երկռեժիմ ներքին բլոկ')
        if code=='B2':
            head=[p,(3.56,p[1]),(3.56,-1.04),(6.58,-1.04),(6.58,.34)]
        elif code=='B1':
            head=[p,(2.73,p[1]),(2.73,3.70)]
        else:head=[p,(p[0],3.70)]
        end=head[-1];rf=head+[(end[0],4.53),(end[0],7.92),(out[0],7.92),out[:2]]
        route('RF-'+code,'REF',[(*p,2.29),*at_z(rf,2.48),out],.045,'Մեկուսացված սառնագենտի զույգ')
        plan=head+[(end[0],k[1]),k];length=0;pts=[]
        for i,v in enumerate(plan):
            if i:length+=math.dist(v,plan[i-1])
            pts.append((*v,2.15-.012*length))
        route('CD-'+code,'COND',[*pts,f],.025,'Կոնդենսատ, i=1.2%, վերջում ուղղաձիգ իջեցում')
    # Միակ դրսի օդամուտք, օդամշակման բլոկ և բաշխիչ հանգույց՝ ընդհանուր բեռնվածքով։
    z=2.52; intake=(5.22,8.22);ahu=(5.22,6.90);plenum=(5.22,3.70)
    item('OA','SUP',(*intake,z),(.26,.10,.18),'Արտաքին եզրի օդամուտք',flow=110)
    item('AHU','SUP',(*ahu,z),(.53,.70,.33),'Մշտագործ ներհոսքի EC օդափոխիչ, ֆիլտր և խլացուցիչ',flow=110,circuit='Q12')
    item('PL','SUP',(*plenum,z),(.26,.26,.18),'Բաշխիչ հանգույց',flow=110)
    route('OA-AHU','SUP',at_z([intake,ahu],z),.16,'Դրսի օդ՝ մինչև օդամշակման բլոկ',flow=110)
    route('AHU-PL','SUP',at_z([ahu,plenum],z),.16,'Մեկուսացված բաշխիչ մայրուղի',flow=110)
    for code,p,val in loc['supply']:
        if code=='B2':
            plan=[plenum,(6.65,3.70),(6.65,-1.10),(3.0,-1.10),(3.0,p[1]),p]
        else:plan=[plenum,(p[0],plenum[1]),p]
        route('SA-'+code,'SUP',at_z(plan,z),.125,'Դրսի օդի ներհոսք',flow=val)
        item('SD-'+code,'SUP',(*p,z),(.18,.18,.10),'Կարգավորվող ներհոսքի վանդակ',flow=val)
    for code,p,val,e in loc['exhaust']:
        mid=(p[0],(p[1]+e[1])/2)
        route('EA-'+code,'EXH',at_z([p,mid,(p[0],e[1]),e],2.43),.125,'Մշտագործ արտածում դեպի հաստատվող հորան',flow=val)
        item('EX-'+code,'EXH',(*p,2.43),(.17,.17,.10),'Արտածման վանդակ',flow=val)
        item('EF-'+code,'EXH',(*mid,2.43),(.20,.20,.20),'Արտածող EC օդափոխիչ՝ թույլատրելի միացումով',flow=val,circuit='Q12')
        item('SV-'+code,'EXH',(*e,2.43),(.18,.18,.18),'Ստուգման կետ՝ մինչև գործող հորան',flow=val)
    for code,pts,val in loc['transfers']:
        # Չափավորումը՝ երկու քնողի հոսքի և իրական ազատ հատույթի համար։
        boosted={'B1-ST':35,'B2-H1':60,'ST-H1':10,'H1-BA':70}[code]
        diameter={'B1-ST':.16,'B2-H1':.20,'ST-H1':.10,'H1-BA':.20}[code]
        route('TF-'+code,'TRANSFER',at_z(pts,1.90),diameter,'Փակ դռներով փոխանցում · ակուստիկ անցուղի',flow=val,boost_flow=boosted,free_area_cm2=math.ceil(max(val,boosted)/3600*10000))
    boost={'OA':135,'OA-AHU':135,'AHU':135,'AHU-PL':135,'PL':135,
        'SA-B1':35,'SD-B1':35,'SA-B2':60,'SD-B2':60,'SA-ST':40,'SD-ST':40}
    for code,flow in [('K',65),('BA',70)]:
        for prefix in ('EA','EX','EF','SV'):boost[prefix+'-'+code]=flow
    for obj in [*elements,*routes]:
        if obj['id'] in boost:obj['boost_flow']=boost[obj['id']]

    item('TR-B','HEAT',(6.75,-2.90,1.12),(.10,.40,.65),'Էլեկտրական սրբիչաչորացուցիչ, 0.4 կՎտ',circuit='Q12')

    # Վերջնական ֆիքսված սպառիչները՝ հստակ նշված անջատիչից կամ վահանակից։
    by_id={e['id']:e['point'] for e in elements}
    hood=(8.54,fixtures['K'][1]-1.08,1.96)
    item('HD','POWER',hood,(.08,.055,.08),'Շրջանառու օդաքաշի ելք',circuit='Q10')
    wm=(*fixtures['WM'],.67)
    item('WM-P','POWER',wm,(.08,.055,.08),'Լվացքի մեքենայի ֆիքսված ելք',circuit='Q9')
    for prefix,end,point,wire in [('E9','WM-P',wm,'Q9'),('E10','HD',hood,'Q10'),('E11','HP-OD',out,'Q11'),('E12','TR-B',by_id['TR-B'],'Q12'),('E14','AHU',by_id['AHU'],'Q12'),('E12','EF-BA',by_id['EF-BA'],'Q12'),('E14','EF-K',by_id['EF-K'],'Q12')]:
        start=by_id[prefix]
        plan=[start[:2],(start[0],point[1]),point[:2]]
        route('EL-'+prefix+'-'+end,'CABLE',[start,*at_z(plan,2.55),point],.016,'Ֆիքսված սարքի սնուցում',circuit=wire)

def inside(p,poly):
    x,y=p;result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x < a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]):result=not result
    return result
def layout_lights(poly,n,ducts):
    # Բազմակետի ընտրություն՝ եզրերից նահանջով և օդատարներից հեռու։
    def dseg(p,a,b):
        ux,uy=b[0]-a[0],b[1]-a[1]; t=max(0,min(1,((p[0]-a[0])*ux+(p[1]-a[1])*uy)/(ux*ux+uy*uy or 1)))
        return math.dist(p,(a[0]+t*ux,a[1]+t*uy))
    edges=list(zip(poly,poly[1:]+poly[:1]));xs=[p[0] for p in poly];ys=[p[1] for p in poly]
    pts=[(round(min(xs)+i*.22,2),round(min(ys)+j*.22,2)) for i in range(1,math.ceil((max(xs)-min(xs))/.22)) for j in range(1,math.ceil((max(ys)-min(ys))/.22))]
    pts=[p for p in pts if inside(p,poly)]
    if not pts: pts=[(sum(xs)/len(xs),sum(ys)/len(ys))]
    margin={p:min(dseg(p,a,b) for a,b in edges) for p in pts}
    valid=[p for p in pts if margin[p]>=min(.34,max(margin.values())*.6) and min([dseg(p,a,b) for a,b in ducts] or [100])>.25]
    if not valid:valid=pts
    picked=[]
    for i in range(n):
        p=max(valid,key=lambda p:min([2.2*margin[p]]+[math.dist(p,q) for q in picked]))
        picked.append(p);valid=[v for v in valid if v!=p] or [p]
    return picked

def export_dxf(arch):
    """Միլիմետրերով 3D LINE եզրեր և տեղադրման խաչեր՝ ըստ համակարգի։"""
    groups={'02-water':['CW','HW'],'03-drain':['DWV','DROP','FLEX','ACCESS'],'04-power':['POWER','CABLE'],'05-light':['LIGHT','SWITCH'],'06-hvac':['HVAC','HEAT','REF','COND','SUP','EXH','TRANSFER']}
    for file,systems in groups.items():
        entries=[]
        def pair(a,b):entries.extend([str(a),str(b)])
        def line(layer,a,b):
            pair(0,'LINE');pair(8,layer)
            for group,p in ((10,a),(11,b)):
                for axis in range(3): pair(group+axis*10,round((p[axis] if axis<len(p) else 0)*1000,4))
        pair(0,'SECTION');pair(2,'HEADER');pair(9,'$ACADVER');pair(1,'AC1009');pair(0,'ENDSEC')
        pair(0,'SECTION');pair(2,'TABLES');pair(0,'TABLE');pair(2,'LAYER');pair(70,len(systems)+1)
        for i,n in enumerate(['A-REFERENCE']+systems):
            pair(0,'LAYER');pair(2,n);pair(70,0);pair(62,[8,4,1,3,6,5,2,7][i]);pair(6,'CONTINUOUS')
        pair(0,'ENDTAB');pair(0,'ENDSEC');pair(0,'SECTION');pair(2,'ENTITIES')
        for s in arch['spaces']:
            for a,b in zip(s['poly'],s['poly'][1:]+s['poly'][:1]):line('A-REFERENCE',a,b)
        for obj in routes:
            if obj['system'] in systems:
                for a,b in zip(obj['points'],obj['points'][1:]):line(obj['system'],a,b)
        for obj in elements:
            if obj['system'] in systems:
                x,y,z=obj['point'];s=obj['system'];line(s,(x-.055,y,z),(x+.055,y,z));line(s,(x,y-.055,z),(x,y+.055,z))
                pair(0,'TEXT');pair(8,s);pair(10,1000*x+70);pair(20,1000*y+45);pair(30,1000*z);pair(40,65);pair(1,obj['id'])
        pair(0,'ENDSEC');pair(0,'EOF')
        (DIR/(file+'.dxf')).write_text('\n'.join(entries)+'\n',encoding='ascii')

ROOMS={'ST':'Բաց ստուդիա','B1':'Լուսավոր ննջասենյակ','B2':'Ներքին օժանդակ սենյակ','BA':'Սանհանգույց','H1':'Ներքին միջանցք','BAL':'Պատշգամբ','SR':'Խորդանոց'}

def operating_points(areas,fl,furn,openings):
    def center(key):
        f=furn[key]
        return (f['x']+f['w']/2,f['y']+f['d']/2)
    def east(key):
        f=furn[key]
        return (f['x']+f['w']-.04,f['y']+f['d']/2)
    def near_wall(zone,key):
        f=furn[key];poly=areas[zone]
        return (min(x for x,y in poly)+.12,min(max(y for x,y in poly)-.16,f['y']+f['d']-.12))
    def cross(door,start,end,along='y'):
        o=openings[door];x=(o['a'][0]+o['b'][0])/2;y=(o['a'][1]+o['b'][1])/2
        return [(x+v,y) if along=='x' else (x,y+v) for v in (start,end)]
    hall_to_bath=cross('D-BA',.14,-.14)
    b1door=next(o['id'] for o in openings.values() if o['id']=='D-B1')
    b2door=next(o['id'] for o in openings.values() if o['wall']=='S3' and o['kind']=='door')
    hall_to_b2=cross(b2door,.16,-.16,'x')
    loc=dict(panel=(6.79,-1.99))
    sofa=furn['SO1'];so=(sofa['x']+.12,sofa['y']+.10)
    b1=near_wall('B1','BED1');b2=near_wall('B2','BED2')
    table=center('TB1');fr=east('FR');hob=east('HB');dw=east('DW')
    loc['sockets']=[
        ('E1','Բազմոց',so,.30,'Q3'),('E2','Ճաշասեղանի գոտի',(8.75,3.20),.30,'Q3'),
        ('E3','Ննջասենյակի մահճակալ',b1,.58,'Q4'),('E4','Ներքին սենյակի մահճակալ',b2,.58,'Q4'),
        ('E5','Խոհանոցի սեղան',(8.72,min(2.32,hob[1]+.36)),1.12,'Q5'),('E6','Սալօջախ',hob,.48,'Q6'),
        ('E7','Ջեռոցի կողային ելք',(hob[0],hob[1]+.12),.48,'Q7'),('E8','Սպասք լվացողի ելք',(dw[0],dw[1]-.12),.48,'Q8'),
        ('E9','Լվացքի մեքենայի անջատիչ',(hall_to_bath[0][0]-.55,-2.12),1.05,'Q9'),('E10','Սառնարան',fr,1.95,'Q10'),
        ('E11','Արտաքին բլոկի անջատիչ',(8.18,8.09),1.25,'Q11'),('E12','Սրբիչաչորացուցիչի անջատիչ',(6.62,-2.13),1.0,'Q12'),
        ('E13','Ստուդիայի լրացուցիչ վարդակ',(4.89,.16),.30,'Q13'),('E14','Օդամշակման բլոկի անջատիչ',(5.22,6.64),1.48,'Q12')]
    loc['supply']=[('B1',(1.32,3.53),35),('B2',(.72,-4.16),35),('ST',(6.91,3.45),40)]
    loc['exhaust']=[('K',(8.10,1.46),60,(8.58,.16)),('BA',(5.83,-4.35),50,(6.63,-2.57))]
    loc['transfers']=[('B1-ST',cross(b1door,-.15,.15,'x'),35),('B2-H1',list(reversed(hall_to_b2)),35),('ST-H1',cross('D-LB',.38,-.41),15),('H1-BA',hall_to_bath,50)]
    loc['airflow_scenarios']={'one_person_B2':{'supply_m3h':{'B1':35,'B2':35,'ST':40},'exhaust_m3h':{'K':60,'BA':50}},'two_people_B2':{'supply_m3h':{'B1':35,'B2':60,'ST':40},'exhaust_m3h':{'K':65,'BA':70}}}
    loc['airtable']=[['Լուսավոր ննջասենյակ','35','—','35 դեպի ստուդիա'],['Ներքին օժանդակ սենյակ','35','—','35 դեպի միջանցք'],['Բաց ստուդիա','40','60','35 ներս՝ B1-ից, 15 դեպի H1'],['Միջանցք','—','—','35 + 15 դեպի սանհանգույց'],['Սանհանգույց','—','50','50 միջանցքից'],['Ընդամենը','110','110','շուրջօրյա նախագծային ռեժիմ']]
    loc['indoor']={'B1':(max(v[0] for v in areas['B1'])-.14,3.70),'B2':(3.08,-3.22),'ST':(6.06,4.17)}
    loc['switches']=[('T1','G1/G7/G8',(4.29,.14)),('T2','G2',(2.35,1.60)),('T3','G3',(3.10,-1.03)),('T4','G4/G9',(hall_to_bath[0][0]+.53,-2.13)),('T5','G5',(6.69,-1.81)),('T7','G11',(3.86,4.27)),('T8','G12',(9.91,-1.95))]
    loc['extra_lights']=[('L-K1',(8.55,.62),1.52,(.035,.86,.035),590,'Աշխատանքային LED 1','G7'),('L-K2',(8.55,1.52),1.52,(.035,.90,.035),610,'Աշխատանքային LED 2','G7'),('L-T',table,1.83,(.35,.35,.15),900,'Ճաշասեղանի լուսատու','G8'),('L-M',fl['B'],1.72,(.36,.05,.08),650,'Հայելու լուսատու','G9')]
    loc['lightzones']={}
    dummy=[((p[0],3.70),p) for tag,p,v in loc['supply']]+[(p,end) for tag,p,v,end in loc['exhaust']]
    for rid,g,t,each in [('ST','G1',150,1350),('B1','G2',150,1100),('B2','G3',150,1100),('BA','G4',100,800),('H1','G5',100,800),('BAL','G11',55,1000),('SR','G12',80,250)]:
        p=areas[rid];av=area(p);count=math.ceil(t*av/(each*.6*.8))
        loc['lightzones'][rid]=(layout_lights(p,count,dummy),ROOMS[rid],av,t,each,g,'ընդհանուր')
    return loc

def thermal_balance(raw,areas):
    heights=raw['height']
    room_width=max(x for x,y in areas['B1']);front_end=max(x for x,y in areas['ST'] if y>4.3)
    glazed={'B1':0.,'ST':0.}
    for opening in raw['openings']:
        if opening['kind'] not in ('window','glazed_door') or opening['wall'] not in ('F1','F2'):continue
        x=.5*(opening['a'][0]+opening['b'][0]);rid='B1' if x<room_width else 'ST'
        glazed[rid]+=math.dist(opening['a'],opening['b'])*opening['height']
    rows=[]
    for rid,q,inner,width in [('ST',40,1050,front_end-room_width-.10),('B1',35,150,room_width),('B2',35,150,0),('H1',0,30,0),('BA',0,80,0)]:
        ag=glazed.get(rid,0);ao=max(0,width*heights-ag);conduct=ag*1.5+ao*.7+q*.34
        rows.append(dict(id=rid,name=ROOMS[rid],ag=ag,ao=ao,q=q,internal_W=inner,heat=conduct*36,cool=conduct*12+ag*420*.52*.65+inner))
    return rows

def make_register(zr,common):
    def line(id):return next(r for r in routes if r['id']==id)
    ducttop=max(p[2]+r['diameter_m']/2+.025 for r in routes if r['system'] in ('SUP','EXH') for p in r['points'])
    flat=[e for e in elements if e['system']=='LIGHT' and e['point'][2]==2.72]
    # Ուղղահայաց բացակը համեմատվում է բոլոր սովորական առաստաղային լուսատուների ցածր եզրի հետ։
    minlight=min(e['point'][2]-e['size'][2]/2 for e in flat); dz=minlight-ducttop
    main=line('D00');length=main['length_plan']

    checks=[
       ['C01','D00 և նախամուտքի սալ',f'R-ի սցենարային նիշը {zr:+.3f} մ է։ Հիմնական ճյուղը Ø110 մմ է, L={length:.2f} մ։','Լազերային համատեղ չափում J, R և հատման տեղերում։ Հաստատել վերին պաշտպանիչ շերտն ու ստորին բարձիկը։','Կոնստրուկտոր և ջրահեռացման ինժեներ','Բաց. սալի մակերևույթի չափ չկա։'],
       ['C02','Ներհոսքի խողովակ / առաստաղ',f'Ընդունված վերին եզրը՝ +{ducttop:.3f} մ, սենյակի առաստաղը՝ +2.800 մ։',f'Մնում է {1000*(2.80-ducttop):.0f} մմ։ Չափել հեծանները, վերնամասերը և կցամասերը։','HVAC նախագծող','Սցենարը տեղավորվում է։ Կառույցները չչափագրված են։'],
       ['C03','Օդատար / առաստաղի լուսատու',f'Լուսատուների ստորին եզր՝ +{minlight:.3f} մ։ Օդատարի վերին եզր՝ +{ducttop:.3f} մ։',f'Հարթ տեղամասի նիշերի բացակը {dz*1000:.0f} մմ է։ LED սնուցման բլոկի և տեղային կախիչի ծավալը ստուգել առանձին։','Լուսատեխնիկ և HVAC նախագծող','Ուղղաձիգ բացակը ստուգված է պայմանական նիշերով։'],
       ['C04','Խոհանոցի ինքնահոս ճյուղ',f"D01-ի երկարությունը մինչև J {line('D01')['length_plan']:.2f} մ է։ Նոր խոհանոցը ստուդիայի արևելյան պատին է։",'Ստուգել սալը, խողովակատակը և հասանելի ծառայողական փակոցը։ Կրող պատը նախապես չծակել։','Ջրահեռացման ինժեներ','Բաց՝ իրական շերտերը և միացման նիշը։'],
       ['C05','Մուտք №3 / վահանակ և կահույք','Վահանակը նախատեսվում է չոր նախասրահում՝ մուտքի մոտ։','Ստուգել դռան ամբողջ բացման աղեղը, վահանակի կափարիչը, կահույքն ու սպասարկողի կանգնելու տեղը՝ տեղադրման շաբլոնով։','Ճարտարապետ և էլեկտրանախագծող','Դռան իրական ծխնին և պատի հաստությունը բաց են։'],
       ['C06','Արտաքին բլոկ / պատշգամբ','Արտաքին բլոկը՝ օդափոխվող արտաքին կողմում, ցուրտ ժամանակ հալոցքի ջրով։','Ճշտել ճակատին տեղադրման թույլտվությունը, ամրացման հիմքը, օդի ետշրջումը, շահագործման մուտքը և ստորև մարդկանց պաշտպանությունը։','Կոնստրուկտոր և HVAC նախագծող','Արտաքին հենարանը և դիրքը բաց են։'],
    ]
    checks.extend([
        ['C07','B2 ներհոսք և վերադարձ','Մշտագործ 35 մ³/ժ ներքին սենյակին։ Փոխանցում դեպի H1՝ փակ դռնով։','Հավասարակշռել վանդակներով, ստուգել ձայնը գիշերը և չափել հոսքը փակ դռներով։','Օդափոխության մասնագետ','Հաստատվող չափագրում և շահագործման փորձարկում։'],
        ['C08','Ստուդիա / միջանցք · օդուղիներ','SA-B2-ը կրող պատի արևելյան եզրը շրջանցում է x=6.65 մ-ով։','Չափագրել առկա միջնապատի և ճակատի անցանելի հանգույցները, ստանալ թույլտվություն։','Կոնստրուկտոր և HVAC նախագծող','Պայմանական միջանցք՝ առանց կրող պատի նոր անցքի։'],
    ])
    specs=[]
    for sys,name,typ in [('CW','Սառը ջուր','բազմաշերտ PE-X'),('HW','Տաք ջուր','մեկուսացված PE-X'),('DWV','Կոյուղի','ձայնամեկուսացված PP'),('SUP','Ներհոսք','մեկուսացված օդատար'),('EXH','Արտածում','կոշտ օդատար'),('REF','Սառնագենտ','պղնձե զույգ'),('COND','Կոնդենսատ','սպասարկվող խողովակ')]:
        by=defaultdict(float)
        for r in routes:
            if r['system']==sys:by[r['diameter_m']]+=summed3(r['points'])
        for dm,l in sorted(by.items()):
            kind=(f'Ø{dm*1000:.0f} մմ' if sys!='REF' else 'ըստ սարքի')
            specs.append([name,typ+' · '+kind,f'{l:.1f} մ','Մոդելի կենտրոնագծերը, առանց հավելավճարի և պաշարի։','Ճշտել ընտրած արտադրանքի հետ, ավելացնել կցամասեր և պահուստ։'])
    for cat,name,qty,condition in [('Էլեկտրական','Բնակարանային վահանակ + RCBO','1 + 13','Տարբերակել տիպը, բևեռները, ջերմային բեռն ու խափանման հոսանքը։'),('Լուսավորում','Ընդհանուր և տեղային LED',f"{sum(e['system']=='LIGHT' for e in elements)} հատ",'Սպեկտր, IP և լուսաչափական ֆայլ։'),('HVAC','Արտաքին / ներքին բլոկ','1 / 3','Վերահաշվել փաստացի ձմեռային հզորությունը և սառնագենտի ծավալը։'),('Ջրամատակարարում','Կոլեկտորներ և հասանելի փականներ','2 հավաքածու','6 սառը, 3 տաք ելք, փակող փական յուրաքանչյուր ճյուղում։')]:
        specs.append([cat,name,qty,'Ըստ տարրերի և վերջնակետերի ցանկի։',condition])
    specs.append(['Օդափոխություն','1 օդամշակման բլոկ + 2 արտածող օդափոխիչ','1 + 2','Ներհոսք 110/135, արտածում 60+50 / 65+70 մ³/ժ։','Ընտրել ըստ դիմադրության, աղմուկի և հասանելի սպասարկման։'])
    return checks,specs

def main():
    global DIR
    import argparse
    parser=argparse.ArgumentParser(description='Վերահաշվել ինժեներական գծագրաշարը')
    parser.add_argument('--architecture',type=Path,default=DATA)
    parser.add_argument('--output',type=Path,default=DIR)
    args=parser.parse_args()
    raw=json.loads(args.architecture.read_text(encoding='utf8'))
    DIR=args.output.resolve();DIR.mkdir(parents=True,exist_ok=True)
    arch=dict(spaces=[dict(id=r['id'],name=r['name'],poly=r['points']) for r in raw['rooms']],walls=raw.get('walls',[]),openings=raw.get('openings',[]),furniture=raw.get('furniture',[]))
    arch['sewer']=raw['sewer']
    assert raw['revision']=='R3' and raw['selected']==3
    areas={v['id']:v['points'] for v in raw['rooms']}
    assert set(areas)=={'B1','B2','ST','H1','BA','SH','SR','BAL'}
    furn={v['id']:v for v in raw['furniture']};openings={v['id']:v for v in raw['openings']}
    ids={'WC':'WC','SH':'SHW','B':'BS','K':'KS','DW':'DW','WM':'WM'}
    def center(id):
        v=next(t for t in raw['furniture'] if t['id']==id);return (v['x']+v['w']/2,v['y']+v['d']/2)
    fl={k:center(id) for k,id in ids.items()}
    loc=operating_points(areas,fl,furn,openings)
    zr,zj,common=make_data(arch,areas,fl,loc)
    make_hvac(arch,loc,fl)
    checks,specs=make_register(zr,common)
    thermal=thermal_balance(raw,areas)
    # Գծագրերի ստեղծումից առաջ ստուգել ելակետերը և ճյուղերի հաշվեկշիռը։
    route_map={v['id']:v for v in routes};elem_map={v['id']:v for v in elements}
    assert len(route_map)==len(routes) and len(elem_map)==len(elements)
    assert not set(elem_map).intersection(route_map)
    assert set(v['id'] for v in lights)=={'ST','B1','B2','BA','H1','BAL','SR'}
    assert math.dist(common[-1],R)<1e-7 and math.dist(route_map['D01']['points'][0][:2],fl['K'])<1e-7
    assert abs(drains[0]['total']-raw['sewer']['length'])<1e-7
    assert abs(drains[0]['h']-raw['sewer']['drop'])<1e-5
    for k,v in fl.items():assert inside(v,areas['ST' if k in ('K','DW') else 'BA']),k
    for k,pt in loc['indoor'].items():assert inside(pt,areas[k]),k
    for key,p,q in loc['supply']:
        assert inside(p,areas[key]);r=route_map['SA-'+key]
        assert r['points'][0]==elem_map['PL']['point'] and r['points'][-1]==elem_map['SD-'+key]['point']
    assert sum(q for _,_,q in loc['supply'])==110==sum(q for _,_,q,_ in loc['exhaust'])
    for code,points,qty in loc['transfers']:
        src,dst=code.split('-')
        assert inside(points[0],areas[src]) and inside(points[-1],areas[dst]),(code,points)
    for mode in loc['airflow_scenarios'].values():
        assert sum(mode['supply_m3h'].values())==sum(mode['exhaust_m3h'].values())
    for code,r in route_map.items():
        assert len(r['points'])>=2 and summed3(r['points'])>0,code
    d=dict(revision='R3',entry=3,status='Նախնական նախագծային R3, տեղում չչափագրված, հաստատման ենթակա',units='m',origin=BASE['origin'],fixtures=fl,routes=routes,elements=elements,drains=drains,loads=demand,lighting=lights,thermal=thermal,clashes=checks,specs=specs,loc=loc,zr=zr,zj=zj,common=common)
    save('services.json',d)
    csvfile('drainage.csv',['Գիծ','Սարք','Ճյուղ L, մ','Ընդհանուր L մինչև R, մ','Ինքնահոս անկում, մ','Սկզբի սցենարային նիշ, մ','Ինքնահոս թեքություն','Ընդունիչ'],[[r['id'],r['name'],round(r['len'],4),round(r['total'],4),round(r['h'],5),r['z0'],r['s'],r.get('downstream','J → R')] for r in drains])
    csvfile('coordination.csv',['Տող','Տեղ / տարրեր','Ստուգում','Պայման կամ ուղղում','Պատասխանատու','Կարգավիճակ'],checks)
    csvfile('specifications.csv',['Բաժին','Նյութ կամ սարք','Քանակ','Չափման հիմք','Ընտրության պայման'],specs)
    csvfile('elements.csv',['Նույնացուցիչ','Համակարգ','Նշանակություն','X, մ','Y, մ','Z, մ','Կառավարման խումբ','Շղթա','Հոսք, լմ'],[[e['id'],e['system'],e['name'],*e['point'],e.get('group',''),e.get('circuit',''),e.get('flux_lm','')] for e in elements])
    export_dxf(arch)
    from report import write_report
    write_report(DIR/'Engineering-R3.pdf',BASE,arch,d)
    print(f'{len(routes)} գիծ, {len(elements)} կետ, {len(lights)} լուսային գոտի, {len(demand)} շղթա')

if __name__=='__main__':main()
