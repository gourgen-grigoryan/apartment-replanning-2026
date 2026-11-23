"""Երկրաչափության բնօրինակ։ Մետրեր, տեղական x/y, z՝ պատրաստի հատակից։"""
from pathlib import Path
import json, math, struct
from collections import defaultdict
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
def read(p):
    return json.loads((PROJECT / p).read_text(encoding="utf-8-sig"))
D = read("02-design/design.json")
S = read("04-services/services.json")
objects = []
def obj(id, typ, name, layer="arch"):
    o = dict(id=id, typ=typ, name=name, layer=layer, meshes=[])
    objects.append(o)
    return o
def mesh(o, mat, pts, faces):
    o["meshes"].append((mat,np.array(pts,float),np.array(faces,int)))
def unit(v):
    return v / np.linalg.norm(v)
def extrude(o, pts, z, h, mat):
    p=np.array(pts,float)
    if len(p)<3 or h<.00001: return
    signed=sum(np.linalg.det([p[i],p[(i+1)%len(p)]]) for i in range(len(p)))
    if signed<0: p=p[::-1]
    n=len(p); ring=list(range(n)); cap=[]
    def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(ring)>3:
        for i,b in enumerate(ring):
            a,c=ring[i-1],ring[(i+1)%len(ring)]
            if cross(p[a],p[b],p[c])<1e-11: continue
            if any(all(cross(p[s],p[t],p[k])>=-1e-10 for s,t in ((a,b),(b,c),(c,a))) for k in ring if k not in [a,b,c]): continue
            cap.append((a,b,c));ring.pop(i);break
        else: raise ValueError((o["id"],ring))
    cap.append(tuple(ring))
    faces=[t[::-1] for t in cap]+[tuple(v+n for v in t) for t in cap]
    for i in range(n):
        j=(i+1)%n; faces.extend([(i,j,j+n),(i,j+n,i+n)])
    mesh(o,mat,[[*xy,zz] for zz in [z,z+h] for xy in p],faces)
def box(o,x,y,z,w,d,h,m):
    extrude(o,[(x,y),(x+w,y),(x+w,y+d),(x,y+d)],z,h,m)
def line(o,a,b,t,z,h,m):
    a,b=np.array(a),np.array(b)
    if np.linalg.norm(b-a)<.00001: return
    u=unit(b-a); n=np.array([-u[1],u[0]])*t/2
    extrude(o,[a-n,b-n,b+n,a+n],z,h,m)
def cyl(o,a,b,r,m,n=12):
    a,b=np.array(a,float),np.array(b,float)
    if np.linalg.norm(b-a)<.00001: return
    axis=unit(b-a); tmp=[1,0,0] if abs(axis[0])<.8 else [0,1,0]
    i=unit(np.cross(axis,tmp)); j=np.cross(axis,i)
    circ=[r*(math.cos(k*math.tau/n)*i+math.sin(k*math.tau/n)*j) for k in range(n)]
    vs=[p+v for p in (a,b) for v in circ]; fs=[]
    for k in range(n):
        l=(k+1)%n;fs.extend([(k,l,l+n),(k,l+n,k+n)])
    for k in range(1,n-1):fs.extend([(0,k+1,k),(n,n+k,n+k+1)])
    mesh(o,m,vs,fs)
def pillow(o,x,y,z,w,d,h,mat,power=.30):
    # Փափուկ կահույքի կլորացված եզրեր՝ պարամետրական մակերևույթով։
    vs=[];fs=[]; nn,mm=20,10
    def s(v):return math.copysign(abs(v)**power,v)
    for j in range(mm+1):
        lat=-math.pi/2+j*math.pi/mm
        for i in range(nn):
            a=math.tau*i/nn
            vs.append((x+w*(1+s(math.cos(lat))*s(math.cos(a)))/2,y+d*(1+s(math.cos(lat))*s(math.sin(a)))/2,z+h*(1+s(math.sin(lat)))/2))
    for j in range(mm):
        for i in range(nn):
            a=j*nn+i;b=j*nn+(i+1)%nn;fs.extend([(a,b,b+nn),(a,b+nn,a+nn)])
    mesh(o,mat,vs,fs)
# Գույներ և նյութերի նույնացուցիչներ՝ միևնույնը IFC-ում և տեսարաններում։
M={"plaster":"e8e2d3","sage":"859484","oak":"bd926a","wood":"936849","parquet":"bb956e","tile":"b8b7a9","fabric":"9b6854","linen":"eee5ce","weave":"818979","black":"353a3b","metal":"aeb7b8","stone":"d9d4c5","ceramic":"edece3","glass":"b5d7d4","mirror":"a8bcbf","light":"fff1c9","concrete":"acaaa0","skyblue":"7199af","red":"bd745e","blue":"649aaf","brass":"bc9a60","darktile":"859286"}
walls={w["id"]:w for w in D["walls"]}; openings=defaultdict(list)
for op in D["openings"]: openings[op["wall"]].append(op)
for w in D["walls"]:
    a,b=np.array(w["a"]),np.array(w["b"]); u=unit(b-a); L=float(np.linalg.norm(b-a))
    o=obj(w["id"],"IFCWALL","Պատ "+w["id"])
    gap=[]
    paint="plaster"
    for op in openings[w["id"]]:
        s,e=sorted(float((np.array(op[p])-a)@u) for p in ["a","b"]);gap.append((max(0,s),min(L,e),op))
    prev=0
    for s,e,op in sorted(gap):
        if s>prev:line(o,a+u*prev,a+u*s,w["t"],0,D["height"],paint)
        z,h=op["sill"],op["height"]
        if z:line(o,a+u*s,a+u*e,w["t"],0,z,paint)
        line(o,a+u*s,a+u*e,w["t"],z+h,D["height"]-z-h,paint)
        prev=e
    if L>prev:line(o,a+u*prev,b,w["t"],0,D["height"],paint)
for op in D["openings"]:
    a,b=np.array(op["a"]),np.array(op["b"]); u=unit(b-a); L=np.linalg.norm(b-a)
    z,h=op["sill"],op["height"];kind=op["kind"]
    hole=obj("O-"+op["id"],"IFCOPENINGELEMENT","Բացվածք "+op["id"],"void");line(hole,a,b,walls[op["wall"]]["t"]+.002,z,h,"plaster")
    if kind=="passage":continue
    glazed=kind in ("glazed_door","window","internal_window")
    o=obj(op["id"],"IFCWINDOW" if "window" in kind else "IFCDOOR","Ապակեպատ բացվածք" if glazed else "Դուռ")
    line(o,a,a+u*.041,.066,z,h,"black" if glazed else "oak")
    line(o,b-u*.041,b,.066,z,h,"black" if glazed else "oak")
    line(o,a,b,.066,z+h-.042,.042,"black" if glazed else "oak")
    if glazed:
        line(o,a,b,.066,z,.042,"black");line(o,a+u*.042,b-u*.042,.012,z+.042,h-.084,"glass")
        if L>1:line(o,(a+b)/2-u*.017,(a+b)/2+u*.017,.05,z,h,"black")
    else:
        line(o,a+.042*u,b-.042*u,.035,z+.015,h-.062,"oak")
        if kind=="sliding":line(o,(a+b)/2-u*.005,(a+b)/2+u*.005,.039,z+.012,h-.059,"black")
        n=np.array([-u[1],u[0]])
        for sign in (-1,1):line(o,b-.18*u+sign*n*.046,b-.07*u+sign*n*.046,.02,1.02,.026,"brass")
col=obj("COL","IFCCOLUMN","Բետոնե սյուն");extrude(col,D["column"],0,D["height"],"concrete")
for r in D["rooms"]:
    tab=r["id"];p=r["points"]
    sp=obj("SPACE-"+tab,"IFCSPACE",r["name"],"space");extrude(sp,p,0,D["height"],"plaster")
    floor=obj("SL-"+tab,"IFCSLAB",r["name"]+"․ հատակ","floor")
    extrude(floor,p,-.12,.12, "tile" if tab in ("BAL","SH","SR","H1","H2") else "darktile" if tab=="BA" else "parquet")
    ceil=obj("CE-"+tab,"IFCCOVERING",r["name"]+"․ առաստաղ","ceiling")
    extrude(ceil,p,D["height"],.105,"plaster")
bal=next(r["points"] for r in D["rooms"] if r["id"]=="BAL")
for idx in [0,1,2,4,5]:
    a,b=np.array(bal[idx]),np.array(bal[(idx+1)%len(bal)]);L=np.linalg.norm(b-a);u=unit(b-a)
    o=obj("BG-"+str(idx),"IFCCURTAINWALL","Պատշգամբի արտաքին ապակեպատում","glazing")
    line(o,a,b,.085,0,.09,"black");line(o,a,b,.085,2.65-.08,.08,"black")
    count=max(1,round(L/1.14)); v=np.array([-u[1],u[0]])
    for k in range(count):
        aa=a+(b-a)*k/count; bb=a+(b-a)*(k+1)/count
        line(o,aa,bb,.018,.09,2.65-.17,"glass")
        line(o,aa,aa+u*min(.045,L/count),.08,.09,2.65-.17,"black")
        line(o,aa,bb,.065,1.05,.037,"black")
    line(o,b-u*min(.045,L/count),b,.08,.09,2.65-.17,"black")

f_names={"bed":"Մահճակալ","sofa":"Բազմոց","table":"Սեղան","bench":"Նստարան","chair":"Աթոռ","sink":"Խոհանոցի լվացարան","dishwasher":"Սպասք լվացող մեքենա","hob":"Սալօջախ","fridge":"Սառնարան","shower":"Ցնցուղ","toilet":"Զուգարանակոնք","basin":"Լվացարան","washer":"Լվացքի մեքենա"}
for f in D["furniture"]:
    id,k,x,y,w,d,h=[f[a] for a in ["id","kind","x","y","w","d","h"]]
    typ="IFCSANITARYTERMINAL" if k in ("sink","basin","toilet","shower") else "IFCELECTRICAPPLIANCE" if k in ("washer","hob","dishwasher","fridge") else "IFCFURNITURE"
    o=obj(id,typ,f_names[k],"furn")
    def legs(zz):
        for i in [.10,.90]:
            for j in [.12,.88]:cyl(o,[x+i*w,y+j*d,.01],[x+i*w,y+j*d,zz],.026,"wood",10)
    if k=="bed":
        legs(.21);pillow(o,x,y,.12,w,d,.20,"wood",.12);pillow(o,x+.014,y+.014,.30,w-.028,d-.028,.21,"linen",.22)
        pillow(o,x+.012,y+.020,.48,w-.024,d*.69,.075,"linen");pillow(o,x+.015,y+.08,.54,w-.03,.44,.036,"weave",.18)
        pillow(o,x+.07,y+d-.49,.50,w-.14,.42,.11,"linen",.53)
        for j in range(6): box(o,x+.034,y+.14+j*.054,.575,w-.068,.003,.002,"weave")
    elif k=="sofa":
        legs(.16);pillow(o,x+.035,y+.018,.12,w-.07,d-.036,.26,"fabric",.22)
        pillow(o,x+.01,y+.02,.28,.16,d-.04,.52,"fabric",.31)
        for yy in (y+.02,y+d-.14):pillow(o,x+.01,yy,.28,w-.02,.12,.36,"fabric",.28)
        for j in range(2):
            pillow(o,x+.15,y+.15+j*(d-.30)/2,.35,w-.16,(d-.31)/2,.14,"fabric")
            pillow(o,x+.13,y+.18+j*(d-.3)/2,.48,.16,(d-.39)/2,.27,"fabric")
        pillow(o,x+.21,y+.23,.49,.19,.35,.29,"linen",.60)
    elif k in ("table","bench","chair"):
        thick=.044
        top=h if k!="chair" else .465;legs(top-.04);pillow(o,x,y,top-thick,w,d,thick,"oak" if k=="table" else "weave",.13)
        if k=="chair":
            pillow(o,x+w-.05,y,h-.23,.045,d,.23,"wood",.18)
            for yy in (y+.05,y+d-.05):cyl(o,[x+w-.023,yy,.39],[x+w-.023,yy,h-.11],.018,"wood")
        if id=="TB1":
            for q in [.23,.74]:cyl(o,[x+w*q,y+d*.51,h+.002],[x+w*q,y+d*.51,h+.016],.112,"ceramic",28)
            cyl(o,[x+w*.50,y+d*.50,h],[x+w*.5,y+d*.50,h+.14],.045,"sage",16)
    elif k in ("sink","dishwasher","hob","fridge","washer","basin"):
        mat="metal" if k in ("fridge","washer") else "sage" if k in ("dishwasher","sink","hob") else "oak"
        box(o,x+.04,y+.025,.015,w-.05,d-.05,.085,"black");box(o,x+.025,y+.005,.10,w-.031,d-.01,h-.13,mat)
        box(o,x,y,h-.032,w,d,.032,"stone" if k not in ("washer","fridge") else "metal")
        levels=[.17,.44,.70] if k in ("hob","sink") else [h*.34] if k=="fridge" else [.76]
        for zz in levels:box(o,x+.020,y+.018,zz,.009,d-.036,.012,"black")
        if k in ("sink","basin"):
            box(o,x+.055,y+.063,h-.002,w-.11,d-.126,.015,"ceramic" if k=="basin" else "metal")
            box(o,x+.10,y+.10,h+.012,w-.20,d-.20,.004,"stone" if k=="basin" else "black")
            xx,yy=x+w-.055,y+d*.5
            cyl(o,[xx,yy,h],[xx,yy,h+.205],.014,"metal");cyl(o,[xx,yy,h+.205],[xx-.11,yy,h+.205],.014,"metal")
            if k=="basin":box(o,x+.012,y,1.06,.016,d,.82,"mirror")
        elif k=="hob":
            box(o,x+.032,y+.08,h,w-.064,d-.16,.012,"black")
            for i in [.30,.72]:
                for j in [.32,.70]:
                    cyl(o,[x+w*i,y+d*j,h+.012],[x+w*i,y+d*j,h+.015],.077,"metal",24)
                    cyl(o,[x+w*i,y+d*j,h+.015],[x+w*i,y+d*j,h+.016],.072,"black",24)
        elif k=="washer":
            cyl(o,[x+.01,y+d/2,.44],[x+.04,y+d/2,.44],.205,"metal",28);cyl(o,[x+.001,y+d/2,.44],[x+.011,y+d/2,.44],.164,"black",28)
    elif k=="shower":
        box(o,x,y,.002,w,d,.035,"ceramic");box(o,x,y,.04,.013,d,h-.04,"glass")
        for yy in [y+.012,y+d-.012]:cyl(o,[x+.006,yy,.04],[x+.006,yy,h],.014,"black")
        cyl(o,[x+w-.06,y+d*.6,.91],[x+w-.06,y+d*.6,2.05],.018,"metal");cyl(o,[x+w-.06,y+d*.6,2.05],[x+w-.24,y+d*.6,2.05],.016,"metal");cyl(o,[x+w-.24,y+d*.6,2.0],[x+w-.24,y+d*.6,2.04],.09,"metal")
    elif k=="toilet":
        pillow(o,x+.09,y+.055,0,w-.20,d-.11,.32,"ceramic",.72);pillow(o,x,y,.25,w,d,.17,"ceramic",.72)
        pillow(o,x+.03,y+.04,.40,w*.70,d-.08,.035,"linen",.76);pillow(o,x+w-.15,y,.38,.15,d,.38,"ceramic",.22)

route_types={"CABLE":"IFCCABLESEGMENT","SUP":"IFCDUCTSEGMENT","EXH":"IFCDUCTSEGMENT","TRANSFER":"IFCDUCTSEGMENT"}
for r in S["routes"]:
    o=obj("MEP-"+r["id"],route_types.get(r["system"],"IFCPIPESEGMENT"),r["name"],"systems");o["element_id"]=r["id"];o["system"]=r["system"]
    mat={"CW":"blue","HW":"red","DWV":"black","CABLE":"brass"}.get(r["system"],"metal")
    for a,b in zip(r["points"],r["points"][1:]):cyl(o,a,b,r["diameter_m"]/2,mat,8)
for e in S["elements"]:
    id,sys=e["id"],e["system"];x,y,z=e["point"];w,d,h=e["size"]
    typ={"LIGHT":"IFCLIGHTFIXTURE","SWITCH":"IFCSWITCHINGDEVICE","POWER":"IFCOUTLET" if id!="DB" else "IFCELECTRICDISTRIBUTIONBOARD","HVAC":"IFCUNITARYEQUIPMENT","SUP":"IFCAIRTERMINAL","EXH":"IFCAIRTERMINAL","HEAT":"IFCSPACEHEATER"}.get(sys,"IFCBUILDINGELEMENTPROXY")
    o=obj("MEP-"+id,typ,e["name"],"fixture" if sys in ("LIGHT","HVAC","HEAT","SUP","EXH","POWER","SWITCH") else "systems");o["system"]=sys;o["element_id"]=id
    if sys=="LIGHT" and .55<w/d<1.7:
        cyl(o,[x,y,z-h/2],[x,y,z+h/2],min(w,d)/2,"light",20)
    else:box(o,x-w/2,y-d/2,z-h/2,w,d,h,"light" if sys=="LIGHT" else "ceramic")
    if sys=="HVAC" and id.startswith("IU"):
        if d<w:box(o,x-w*.44,y-d*.51,z-h*.34,w*.88,.012,.026,"black")
        else:box(o,x-w*.51,y-d*.44,z-h*.34,.012,d*.88,.026,"black")
