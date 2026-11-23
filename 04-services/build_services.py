"""Վերահաշվարկել վեց ինժեներական թերթախմբերի ելակետերը R2 մոդելից։"""
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
    via=(5.45,-1.98)
    kpath=[tuple(p) for p in scheme['branch']]
    bpaths=[
        ('D01','Խոհանոցի լվացարան',kpath,.050,.03),
        ('D02','Զուգարանակոնք',[wc,(6.62,wc[1]),j],.110,.02),
        ('D03','Ցնցուղ',[sh,(6.31,sh[1]),(6.31,-2.96),j],.050,.03),
        ('D04','Սանհանգույցի լվացարան',[b,(b[0],-2.82),j],.050,.03),
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

    man=(6.67,-3.13)
    item('MC','CW',(*man,.64),(.40,.13,.35),'Սառը ջրի կոլեկտոր')
    item('MH','HW',(man[0],man[1]+.12,.91),(.40,.13,.22),'Տաք ջրի կոլեկտոր')
    for system,provider,dist in [('CW','WS-C',0),('HW','WS-H',.10)]:
        source=(6.68+dist,-3.57)
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
                plan=[man,(6.56+dist,-2.47),via,(5.51+dist,-.70),(5.51+dist,pt[1]),pt]
            else:plan=[man,(6.49+dist,man[1]),(6.49+dist,pt[1]),pt]
            route(system+'-'+n,system,[manifold,*at_z(plan,z),(*pt,h)],.016,'Ջրաբաժան կետ '+n)

    # Միաֆազ համեմատական սցենար, հաշվարկային ընդհանուր հզորությունը ըստ պայմանագրի հաստատվում է առանձին։
    consumer_rows=[
        ('Q1','Լուսավորում, բնակելի գոտի',.20,1.0,10,1.5),
        ('Q2','Լուսավորում, օժանդակ գոտի',.16,1.,10,1.5),
        ('Q3','Ստուդիայի և ճաշասենյակի վարդակներ',2.00,.50,16,2.5),
        ('Q4','Ննջասենյակների վարդակներ',2.00,.40,16,2.5),
        ('Q5','Խոհանոցի սեղանի վարդակներ',2.50,.70,16,2.5),
        ('Q6','Ինդուկցիոն սալօջախ',7.20,.60,32,6),
        ('Q7','Ջեռոց',3.00,.70,16,2.5),
        ('Q8','Սպասք լվացող մեքենա',2.00,.60,16,2.5),
        ('Q9','Լվացքի մեքենա',2.20,.60,16,2.5),
        ('Q10','Սառնարան և օդաքաշ',.40,1.,10,2.5),
        ('Q11','Ջերմային պոմպի արտաքին բլոկ',2.20,.90,16,2.5),
        ('Q12','Օդափոխություն և սրբիչաչորացուցիչ',.65,.90,10,1.5),
        ('Q13','Ճաշասրահի լրացուցիչ վարդակներ',1.50,.40,16,2.5),
    ]
    for id,n,kw,fusek,cb,s in consumer_rows:
        demand.append(dict(id=id,name=n,kw=kw,simult=fusek,design_kw=kw*fusek,amps=kw*1000/230,cb=cb,mm2=s))
    panel=location['panel']
    item('DB','POWER',(*panel,1.45),(.12,.38,.55),'Բնակարանային վահանակ՝ արևելյան պատին')
    for n,key,pt,h,cid in location['sockets']:
        item(n,'POWER',(*pt,h),(.08,.055,.08),key,circuit=cid)
        # Կարճ պայմանական ուղիներ՝ բացվածքների միջով, առաստաղի վրայով և ուղղաձիգ իջեցումներով։
        if pt[1]<-.6 and pt[0]<6.9:
            path=[panel,(6.74,-1.26),(5.10,-1.26)]
            if pt[0]<3.28:path +=[(3.36,-1.82),(3.15,-1.82)]
        elif pt[1]>0:
            path=[panel,(5.18,-1.15),(5.18,.18)]
            if pt[0]<3: path +=[(2.60,.62)]
        else:path=[panel]
        z=2.55
        if pt[1]>0:
            neck=[(*panel,1.45),(*panel,z),(5.18,-1.15,z),(5.18,-.77,z),(5.18,-.77,-.040),(5.18,.18,-.040),(5.18,.18,z)]
            xyz=neck+at_z(path[3:],z)
        else:xyz=[(*panel,1.45),*at_z(path,z)]
        if n=='E4':
            xyz += [(5.72,.18,z),(5.72,1.19,z),(5.72,1.19,-.040),(6.67,1.19,-.040),(6.67,1.19,z),(6.97,1.19,z),(6.97,pt[1],z)]
        if n=='E11':
            xyz += [(4.32,.18,z),(4.32,4.40,z),(4.32,4.40,1.99),(4.32,4.65,1.99),(4.32,4.65,z),(4.32,8.13,z)]
        route('EL-'+n,'CABLE',[*xyz,(pt[0],xyz[-1][1],z),(*pt,z),(*pt,h)],.016,key,circuit=cid)

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
    out=(8.23,8.57,1.05)
    item('HP-OD','HVAC',out,(.85,.38,.73),'Արտաքին բլոկ, տեղը՝ համաձայնեցման ենթակա')
    for code,p in loc['indoor'].items():
        item('IU-'+code,'HVAC',(*p,2.29),(.72,.23,.30),'Երկռեժիմ ներքին բլոկ')
        plan=[p,(p[0],4.58),(p[0],7.95),(8.24,7.95),out[:2]]
        route('RF-'+code,'REF',[(*p,2.29),*at_z(plan,2.48),out],.045,'Մեկուսացված սառնագենտի զույգ')
    # Կոնդենսատը հասնում է խոհանոցի բաց ձագարին՝ սիֆոնով ու օդային խզումով։
    k=fixtures['K'];f=(k[0],k[1],.67)
    item('CD-F','COND',f,(.09,.09,.12),'Սիֆոնավոր ձագար, օդային խզում')
    for code,p in loc['indoor'].items():
        if code=='S':plan=[p,(p[0],3.72),(5.22,3.72),(5.22,k[1]),k]
        else:
            facade_x={'B1':.55,'B2':7.05}[code]
            plan=[p,(facade_x,p[1]),(facade_x,4.80),(3.76,4.80),(3.76,3.72),(5.22,3.72),(5.22,k[1]),k]
        l=0; pts=[]
        for i,v in enumerate(plan):
            if i:l+=math.dist(v,plan[i-1])
            pts.append((*v,2.15-.012*l))
        route('CD-'+code,'COND',[*pts,f],.025,'Կոնդենսատ, i=1.2%, վերջում ուղղաձիգ իջեցում')
    for code,p,val in loc['supply']:
        path=[(p[0],8.22),(p[0],4.53),p]
        if p[1]<0: path=[(4.94,8.22),(4.94,4.53),(5.10,.25),(5.10,-1.10),(5.10,-1.83)]
        if p[1]<0 and p[0]<3.3:path +=[(3.34,-1.83)]
        if tuple(path[-1]) != tuple(p): path.append(p)
        diameter=.125 if val>=25 else .08
        route('SA-'+code,'SUP',at_z(path,2.52),diameter,'Դրսի օդի ներհոսք',flow=val)
        item('SD-'+code,'SUP',(*p,2.52),(.18,.18,.10),'Կարգավորվող ներհոսքի վանդակ',flow=val)
    for code,p,val,e in loc['exhaust']:
        path=[p,(p[0],e[1]),e]
        route('EA-'+code,'EXH',at_z(path,2.48),.125,'Առանձին արտածման ճյուղ',flow=val)
        item('EX-'+code,'EXH',(*p,2.48),(.17,.17,.10),'Արտածման վանդակ',flow=val)
        item('SV-'+code,'EXH',(*e,2.48),(.18,.18,.18),'Ստուգման կետ՝ մինչև գործող հորան',flow=val)
    for code,pts,val in [('H1',[(5.64,-1.43),(5.96,-1.43)],50),('BA',[(6.35,-2.15),(6.35,-2.40)],50)]:
        route('TF-'+code,'TRANSFER',at_z(pts,1.90),.10,'Ներքին օդափոխման փոխանցում',flow=val)
    item('TR-B','HEAT',(6.68,-3.05,1.12),(.10,.48,.65),'Էլեկտրական սրբիչաչորացուցիչ, 0.4 կՎտ')

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

ROOMS={'S':'Ստուդիա · հյուրասենյակ','B1':'Ննջասենյակ 1','B2':'Ննջասենյակ 2','BA':'Համատեղ սանհանգույց','HL':'Ներքին մուտքային միջանցք','H2':'Ննջասենյակի անցում','KT':'Ստուդիա · խոհանոց և ճաշասրահ','BL':'Վիտրաժային պատշգամբ','SC':'Խորդանոց'}
def operating_points(areas,fl):
    loc=dict(panel=(6.85,-1.98));k=fl['K']
    loc['sockets']=[
        ('E1','Բազմոցի վարդակներ',(3.21,2.04),.30,'Q3'),('E2','Ճաշասեղանի սպասարկում',(.37,-3.45),.30,'Q3'),
        ('E3','Մահճակալ 1',(.19,3.77),.58,'Q4'),('E4','Մահճակալ 2',(8.74,3.89),.58,'Q4'),
        ('E5','Խոհանոցային աշխատանքային սեղան',(4.92,-2.85),1.12,'Q5'),('E6','Սալօջախի սեղմակ',(4.93,-4.22),.48,'Q6'),
        ('E7','Ջեռոց՝ կողային միացում',(4.93,-3.96),.48,'Q7'),('E8','Սպասք լվացողի կողային միացում',(4.95,-3.12),.48,'Q8'),
        ('E9','Լվացքի մեքենա․ հասանելի անջատիչ՝ չոր կողմից',(4.98,-4.68),.95,'Q9'),('E10','Սառնարան և օդաքաշ',(4.94,-4.83),1.95,'Q10'),
        ('E11','Արտաքին բլոկի անջատիչ',(8.23,8.20),1.25,'Q11'),('E12','Չոր գոտու անջատիչ',(6.68,-2.17),1.0,'Q12'),
        ('E13','Ճաշասրահի լրացուցիչ վարդակ',(3.63,-5.09),.30,'Q13')]
    loc['supply']=[('B1',(1.44,3.90),35),('B2',(7.97,3.91),35),('S',(4.46,3.94),40)]
    loc['exhaust']=[('K',(4.73,-4.23),60,(5.0,-3.90)),('B',(6.31,-4.44),50,(6.45,-2.82))]
    loc['airtable']=[['Ննջասենյակ 1','35','—','35 դեպի հյուրասենյակ'],['Ննջասենյակ 2','35','—','35՝ ներքին անցքով դեպի հյուրասենյակ'],['Հյուրասենյակ','40','—','ընդհանուր 110 դեպի խոհանոց-ճաշասրահ'],['Խոհանոց և ճաշասրահ','—','60','50 դեպի մուտքային միջանցք'],['Մուտքային միջանցք','—','—','50 դեպի սանհանգույց'],['Սանհանգույց','—','50','50 միջանցքից'],['Բնակարան, գումար','110','110','նախնական հաշվեկշիռ'],['Պատշգամբ / խորդանոց','—','—','բացվող փեղկեր / պասիվ օդանցք']]
    loc['indoor']={'B1':(.43,4.27),'B2':(7.14,4.27),'S':(3.50,4.29)}
    loc['switches']=[('T1','G1/G7/G8',(4.42,.12)),('T2','G2',(2.97,1.32)),('T3','G3',(7.40,1.73)),('T4','G4/G9',(6.46,-2.13)),('T5','G5/G6',(6.70,-.69)),('T7','G11',(3.88,4.26)),('T8','G12',(9.88,-1.91)),('T9','G13',(6.62,.76))]
    loc['extra_lights']=[('L-K1',(4.8,-3.16),1.52,(.035,.88,.035),590,'Աշխատանքային LED 1','G7'),('L-K2',(4.8,-4.08),1.52,(.035,.92,.035),610,'Աշխատանքային LED 2','G7'),('L-T',(1.71,-3.025),1.83,(.35,.35,.15),900,'Ճաշասեղանի լուսատու','G8'),('L-M',fl['B'],1.72,(.36,.05,.08),650,'Հայելու լուսատու','G9')]
    zone_specs=[('S','S','G1',150,1350),('B1','B1','G2',150,1100),('B2','B2','G3',150,1100),('BA','BA','G4',100,800),('HL','HL','G5',100,800),('H2','H2','G13',100,800),('KT','KT','G6',150,1350),('BL','BL','G11',55,1000),('SC','SC','G12',80,250)]
    loc['lightzones']={}
    dummy=[((p[0],8.22),p) for tag,p,v in loc['supply'] if p[1]>0]+[(p,end) for tag,p,v,end in loc['exhaust']]
    for id,r,g,t,each in zone_specs:
        if r not in areas:continue
        p=areas[r];av=area(p);count=math.ceil(t*av/(each*.6*.8))
        loc['lightzones'][id]=(layout_lights(p,count,dummy),ROOMS[r],av,t,each,g,'ընդհանուր')
    return loc

def thermal_balance():
    # Ag և Ao՝ պայմանական ուղղաձիգ ապակու և անթափանց պատի մակերես, մ²։
    rows=[]
    for name,ag,ao,q,inner in [
        ('Ստուդիա · հյուրասենյակ',4.5244,2.35535*2.8-4.5244,40,180),('Ննջասենյակ 1',2.0272,3.0656*2.8-2.0272,35,150),('Ննջասենյակ 2',1.7515,3.055*2.8-1.7515,35,150),
        ('Ստուդիա · խոհանոց և ճաշասրահ',0,0,0,900),('Ներքին միջանցքներ',0,0,0,30),('Սանհանգույց',0,0,0,80)]:
        conduct=ag*1.5+ao*.7+q*.34
        rows.append(dict(name=name,ag=ag,ao=ao,q=q,internal_W=inner,heat=conduct*36,cool=conduct*12+ag*420*.52*.65+inner))
    return rows

def make_register(zr,common):
    def line(id):return next(r for r in routes if r['id']==id)
    ducttop=max(p[2]+r['diameter_m']/2+.025 for r in routes if r['system'] in ('SUP','EXH') for p in r['points'])
    flat=[e for e in elements if e['system']=='LIGHT' and e['point'][2]==2.72]
    # Ուղղահայաց բացակը համեմատվում է բոլոր սովորական առաստաղային լուսատուների ցածր եզրի հետ։
    minlight=min(e['point'][2]-e['size'][2]/2 for e in flat); dz=minlight-ducttop
    main=line('D00');length=main['length_plan']
    beam=[p for p in line('D01')['points'] if -.60<=p[1]<=.60]
    checks=[
       ['C01','D00 և նախամուտքի սալ',f'R-ի սցենարային նիշը {zr:+.3f} մ է։ Հիմնական ճյուղը Ø110 մմ է, L={length:.2f} մ։','Լազերային համատեղ չափում J, R և հատման տեղերում։ Հաստատել վերին պաշտպանիչ շերտն ու ստորին բարձիկը։','Կոնստրուկտոր և ջրահեռացման ինժեներ','Բաց. սալի մակերևույթի չափ չկա։'],
       ['C02','Ներհոսքի խողովակ / առաստաղ',f'Ընդունված վերին եզրը՝ +{ducttop:.3f} մ, սենյակի առաստաղը՝ +2.800 մ։',f'Մնում է {1000*(2.80-ducttop):.0f} մմ։ Չափել հեծանները, վերնամասերը և կցամասերը։','HVAC նախագծող','Սցենարը տեղավորվում է։ Կառույցները չչափագրված են։'],
       ['C03','Օդատար / առաստաղի լուսատու',f'Լուսատուների ստորին եզր՝ +{minlight:.3f} մ։ Օդատարի վերին եզր՝ +{ducttop:.3f} մ։',f'Հարթ տեղամասի նիշերի բացակը {dz*1000:.0f} մմ է։ LED սնուցման բլոկի և տեղային կախիչի ծավալը ստուգել առանձին։','Լուսատեխնիկ և HVAC նախագծող','Ուղղաձիգ բացակը ստուգված է պայմանական նիշերով։'],
       ['C04','D01 և թաց գոտու միջնորմ','Խոհանոցի ճյուղը ստորին գոտում անցնում է ST2-ից BA-ի կից նոր պատով։','Ստուգել անցքի թևքը, ջրամեկուսացումը և հատակի շերտերի բավարարությունը։','Ջրահեռացման ինժեներ','R2-ում 5.92 մ պատը D01-ը չի հատում։'],
       ['C05','Մուտք №3 / վահանակ և կահույք','Վահանակը նախատեսվում է չոր նախասրահում՝ մուտքի մոտ։','Ստուգել դռան ամբողջ բացման աղեղը, վահանակի կափարիչը, կահույքն ու սպասարկողի կանգնելու տեղը՝ տեղադրման շաբլոնով։','Ճարտարապետ և էլեկտրանախագծող','Դռան իրական ծխնին և պատի հաստությունը բաց են։'],
       ['C06','Արտաքին բլոկ / պատշգամբ','Արտաքին բլոկը՝ օդափոխվող արտաքին կողմում, ցուրտ ժամանակ հալոցքի ջրով։','Ճշտել ճակատին տեղադրման թույլտվությունը, ամրացման հիմքը, օդի ետշրջումը, շահագործման մուտքը և ստորև մարդկանց պաշտպանությունը։','Կոնստրուկտոր և HVAC նախագծող','Արտաքին հենարանը և դիրքը բաց են։'],
    ]
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
    codes={'S':'ST','KT':'ST2','B1':'B1','B2':'B2','BA':'BA','HL':'H1','H2':'H2','BL':'BAL','SC':'SR'}
    areas={k:next(v['points'] for v in raw['rooms'] if v['id']==rid) for k,rid in codes.items()}
    ids={'WC':'WC','SH':'SHW','B':'BS','K':'KS','DW':'DW','WM':'WM'}
    def center(id):
        v=next(t for t in raw['furniture'] if t['id']==id);return (v['x']+v['w']/2,v['y']+v['d']/2)
    fl={k:center(id) for k,id in ids.items()}
    loc=operating_points(areas,fl)
    zr,zj,common=make_data(arch,areas,fl,loc)
    make_hvac(arch,loc,fl)
    checks,specs=make_register(zr,common)
    thermal=thermal_balance()
    d=dict(status='Նախնական նախագծային R2, տեղում չչափագրված, հաստատման ենթակա',units='m',origin=BASE['origin'],fixtures=fl,routes=routes,elements=elements,drains=drains,loads=demand,lighting=lights,thermal=thermal,clashes=checks,specs=specs,loc=loc,zr=zr,zj=zj,common=common)
    save('services.json',d)
    csvfile('drainage.csv',['Գիծ','Սարք','Ճյուղ L, մ','Ընդհանուր L մինչև R, մ','Ինքնահոս անկում, մ','Սկզբի սցենարային նիշ, մ','Ինքնահոս թեքություն','Ընդունիչ'],[[r['id'],r['name'],round(r['len'],4),round(r['total'],4),round(r['h'],5),r['z0'],r['s'],r.get('downstream','J → R')] for r in drains])
    csvfile('coordination.csv',['Տող','Տեղ / տարրեր','Ստուգում','Պայման կամ ուղղում','Պատասխանատու','Կարգավիճակ'],checks)
    csvfile('specifications.csv',['Բաժին','Նյութ կամ սարք','Քանակ','Չափման հիմք','Ընտրության պայման'],specs)
    csvfile('elements.csv',['Նույնացուցիչ','Համակարգ','Նշանակություն','X, մ','Y, մ','Z, մ','Կառավարման խումբ','Շղթա','Հոսք, լմ'],[[e['id'],e['system'],e['name'],*e['point'],e.get('group',''),e.get('circuit',''),e.get('flux_lm','')] for e in elements])
    export_dxf(arch)
    from report import write_report
    write_report(DIR/'Engineering-R2.pdf',BASE,arch,d)
    print(f'{len(routes)} գիծ, {len(elements)} կետ, {len(lights)} լուսային գոտի, {len(demand)} շղթա')

if __name__=='__main__':main()
