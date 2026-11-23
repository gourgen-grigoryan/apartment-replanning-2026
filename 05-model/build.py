"""IFC4-ի և նույն եռանկյունային մոդելից տեսախցիկների արտահանում։"""
from scene import *
import datetime,re,uuid,gzip,sys

lines=[]
def ent(name,*args):
    lines.append(name+"("+",".join(str(a) for a in args)+")")
    return "#"+str(len(lines))
def arr(a):return "("+",".join(map(str,a))+")"
def string(s):
    # Համատեղելի ISO-10303-21՝ հայերեն անվանումները կոդավորված UTF-16BE։
    return "'"+("".join(c if ord(c)<128 and c not in "'\\" else "\\X2\\"+c.encode("utf-16-be").hex().upper()+"\\X0\\" for c in str(s)))+"'"
def num(v):
    s=("%.7f"%v).rstrip("0")
    return "0." if s in ("-0.","0.") else s
def gid(name):
    a="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
    n=uuid.uuid5(uuid.NAMESPACE_URL,"app:refit2026:"+name).int
    return string("".join(a[(n>>(6*i))&63] for i in reversed(range(22))))
def point(p):return ent("IFCCARTESIANPOINT",arr(num(v) for v in p))
ax=ent("IFCAXIS2PLACEMENT3D",point((0,0,0)),"$","$")
ctx=ent("IFCGEOMETRICREPRESENTATIONCONTEXT","$","'Model'","3","0.00001",ax,"$")
units=ent("IFCUNITASSIGNMENT",arr([ent("IFCSIUNIT","*",".LENGTHUNIT.","$",".METRE."),ent("IFCSIUNIT","*",".AREAUNIT.","$",".SQUARE_METRE."),ent("IFCSIUNIT","*",".VOLUMEUNIT.","$",".CUBIC_METRE.")]))
project=ent("IFCPROJECT",gid("project"),"$",string("Բնակարանի վերապլանավորում"),"$","$","$","$",arr([ctx]),units)
loc=ent("IFCLOCALPLACEMENT","$",ax)
building=ent("IFCBUILDING",gid("building"),"$",string("Բազմաբնակարան շենք"),"$","$",loc,"$","$",".ELEMENT.","$","$","$")
storey=ent("IFCBUILDINGSTOREY",gid("storey"),"$",string("Բնակարան․ պայմանական ±0.000"),"$","$",loc,"$","$",".ELEMENT.","0.")
def rel(a,bs,id):return ent("IFCRELAGGREGATES",gid("agg"+id),"$","$","$",a,arr(bs))
rel(project,[building],"project");rel(building,[storey],"building")
styles={}
for name,hx in M.items():
    rgb=ent("IFCCOLOURRGB","$",*[num(int(hx[i:i+2],16)/255) for i in (0,2,4)])
    shading=ent("IFCSURFACESTYLESHADING",rgb,"0.82" if name=="glass" else "0.")
    styles[name]=ent("IFCSURFACESTYLE",string(name),".BOTH.",arr([shading]))
ids={}; contained=[]; spaces=[]; systems=defaultdict(list);expected={}
for o in objects:
    chunks=defaultdict(list)
    for m,vs,fs in o["meshes"]:
        chunks[m].append((vs,fs))
    shapes=[]
    for m,parts in chunks.items():
        pts=[];faces=[];unique={}
        for vs,fs in parts:
            remap=[]
            for p in vs:
                v=tuple(round(float(k),7) for k in p)
                if v not in unique:unique[v]=len(pts)+1;pts.append(v)
                remap.append(unique[v])
            for face in fs:
                ii=[remap[j] for j in face]
                if len(set(ii))==3:faces.append(ii)
        if not faces:continue
        p=ent("IFCCARTESIANPOINTLIST3D",arr(arr(num(n) for n in v) for v in pts))
        t=ent("IFCTRIANGULATEDFACESET",p,"$","$",arr(arr(v) for v in faces),"$")
        ent("IFCSTYLEDITEM",t,arr([styles[m]]),"$");shapes.append(t)
    if not shapes:continue
    representation=ent("IFCPRODUCTDEFINITIONSHAPE","$","$",arr([ent("IFCSHAPEREPRESENTATION",ctx,"'Body'","'Tessellation'",arr(shapes))]))
    id,typ=o["id"],o["typ"];nm=string(o["name"]+" | "+id)
    args=[gid("product:"+id),"$",nm,"$","$",loc,representation]
    if typ=="IFCSPACE":args.extend(["$",".ELEMENT.",".INTERNAL.","$"])
    else:
        args+=[string(id)]
        if typ in ("IFCDOOR","IFCWINDOW"):
            op=next(k for k in D["openings"] if k["id"]==id)
            args += [num(op["height"]),num(np.linalg.norm(np.array(op["a"])-op["b"])), ".DOOR." if typ=="IFCDOOR" else ".WINDOW.",".NOTDEFINED.","$"]
        else:
            args += [{"IFCOPENINGELEMENT":".OPENING.","IFCCOVERING":".CEILING.","IFCSLAB":".FLOOR."}.get(typ,".NOTDEFINED.")]
    e=ent(typ,*args);ids[id]=e
    if typ=="IFCSPACE":spaces.append(e)
    elif typ!="IFCOPENINGELEMENT":contained.append(e)
    if "system" in o:systems[o["system"]].append(e)
    expected[id]=dict(typ=typ,representation=representation)
rel(storey,spaces,"spaces")
ent("IFCRELCONTAINEDINSPATIALSTRUCTURE",gid("contain"),"$","$","$",arr(contained),storey)
for op in D["openings"]:
    k=op["id"];ent("IFCRELVOIDSELEMENT",gid("void"+k),"$","$","$",ids[op["wall"]],ids["O-"+k])
    if k in ids:ent("IFCRELFILLSELEMENT",gid("fill"+k),"$","$","$",ids["O-"+k],ids[k])
for k,p in systems.items():
    sg=ent("IFCSYSTEM",gid("system"+k),"$",string(k),"$","$")
    ent("IFCRELASSIGNSTOGROUP",gid("group"+k),"$","$","$",arr(p),"$",sg)
head="""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2]'),'2;1');
FILE_NAME('apartment.ifc','2026-11-23T12:00:00',('Design team'),('Apartment project'),'Python model compiler','Apartment R2','Concept design');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
"""
out=HERE/"apartment.ifc"
out.write_text(head+"".join("#%i=%s;\n"%(i+1,s) for i,s in enumerate(lines))+"ENDSEC;\nEND-ISO-10303-21;\n",encoding="ascii")
# Առանձին վերաընթերցում՝ STEP գրառում/հղում/տեսակ և հիմնական քանակներ։
raw=out.read_text(encoding="ascii"); statements=re.findall(r"^#(\d+)=(IFC\w+)\((.*)\);$",raw,re.M)
assert len(statements)==len(lines)
numbers={int(i) for i,_,_ in statements}
assert all(int(n) in numbers for _,_,a in statements for n in re.findall(r"#(\d+)",a))
assert len(spaces)==len(D["rooms"]) and len({o["id"] for o in objects})==len(objects)
assert len(systems)>10 and sum(1 for i in expected if i.startswith("O-"))==len(D["openings"])
print(out.name, out.stat().st_size, "bytes;", len(expected),"products;",len(lines),"STEP records")

cams=[
 ("01-studio","Ստուդիա", [4.26,.36,1.54],[3.98,3.64,1.02],77),
 ("02-kitchen","Խոհանոց",[1.09,-1.12,1.54],[4.66,-3.96,.93],76),
 ("03-bedroom-1","Ննջարան 1",[2.65,1.69,1.48],[.60,3.43,.89],76),
 ("04-bedroom-2","Ննջարան 2",[6.68,2.04,1.50],[8.12,3.63,.99],82),
 ("05-bathroom","Սանհանգույց",[5.56,-2.48,1.58],[6.42,-4.29,1.03],77),
 ("06-balcony","Ապակեպատ պատշգամբ",[1.15,7.64,1.48],[6.72,6.15,1.23],78),
 ("07-facade","Արտաքին դիտակետ",[12.4,17.35,5.32],[4.39,6.05,1.05],51),
 ("08-cutaway","Վերևից եռաչափ կտրվածք",[10.9,-9.0,20.5],[5.0,1.20,.10],56)]
viewdir=PROJECT/"07-views";viewdir.mkdir(exist_ok=True)
(viewdir/"cameras.json").write_text(json.dumps([dict(file=k+".jpg",name=n,eye=p,target=t,horizontal_fov_deg=f,up=[0,0,1],model="05-model/apartment.ifc") for k,n,p,t,f in cams],ensure_ascii=False,indent=2),encoding="utf-8")
work=PROJECT.parent/"tmp"/"model";work.mkdir(parents=True,exist_ok=True)
with (work/"triangles.dat").open("wb") as stream:
    for o in objects:
        if o["layer"] in ("void","space","systems"):continue
        for m,pts,faces in o["meshes"]:
            vs=pts[faces];v1,v2=vs[:,1]-vs[:,0],vs[:,2]-vs[:,0]
            vs=vs[np.linalg.norm(np.cross(v1,v2),axis=1)>1e-10]
            flags=dict(ceiling=1,arch=2,glazing=3,furn=4,fixture=5,floor=6).get(o["layer"],0)
            vals=np.column_stack([vs.reshape(-1,9),np.full(len(vs),list(M).index(m)),np.full(len(vs),flags)]).astype("<f4")
            stream.write(vals.tobytes())
with (work/"cameras.txt").open("w",encoding="ascii") as f:
    for i,(k,n,eye,target,fov) in enumerate(cams):
        f.write(" ".join(map(str,[k,*eye,*target,fov,i]))+"\n")
with (work/"lights.txt").open("w",encoding="ascii") as f:
    for e in S["elements"]:
        if e["system"]=="LIGHT":
            power=16 if e["id"] in ("L-T","L-M","L-K1","L-K2") else 10
            f.write(" ".join(map(str,[*e["point"],power]))+"\n")
print("Cameras:",len(cams),"; triangles:",(work/"triangles.dat").stat().st_size//44)
