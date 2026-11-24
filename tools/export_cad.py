"""Վերստեղծել 06-cad փաթեթը նախագծի կոորդինատներով (մ)։"""
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06-cad"
OUT.mkdir(exist_ok=True)
base = json.loads((ROOT / "01-source/base.json").read_text("utf-8"))
design = json.loads((ROOT / "02-design/design.json").read_text("utf-8"))
services = json.loads((ROOT / "04-services/services.json").read_text("utf-8"))


def pairs(*data):
    return list(zip(data[::2], data[1::2]))


class Drawing:
    def __init__(self, reference=None):
        self.layers = {"0": 7}
        self.entities = []
        self.reference = reference
        if reference:
            self.entities.extend(pairs(0, "INSERT", 8, "0", 2, reference, 10, 0, 20, 0, 30, 0, 41, 1, 42, 1, 43, 1))

    def layer(self, name, color):
        self.layers[name] = color
        return name

    def line(self, layer, a, b):
        extra = lambda p: p[2] if len(p) > 2 else 0
        self.entities.extend(pairs(0, "LINE", 8, layer, 10, a[0], 20, a[1], 30, extra(a), 11, b[0], 21, b[1], 31, extra(b)))

    def poly(self, layer, points, close=False):
        self.entities.extend(pairs(0, "POLYLINE", 8, layer, 66, 1, 10, 0, 20, 0, 30, 0, 70, int(close)))
        for x, y in points:
            self.entities.extend(pairs(0, "VERTEX", 8, layer, 10, x, 20, y, 30, 0, 70, 0))
        self.entities.extend(pairs(0, "SEQEND", 8, layer))

    def circle(self, layer, p, radius):
        self.entities.extend(pairs(0, "CIRCLE", 8, layer, 10, p[0], 20, p[1], 30, 0, 40, radius))

    def text(self, layer, p, label, height=.11):
        self.entities.extend(pairs(0, "TEXT", 8, layer, 7, "HY", 10, p[0], 20, p[1], 30, 0, 40, height, 1, label))

    def save(self, name):
        d = pairs(0, "SECTION", 2, "HEADER", 9, "$ACADVER", 1, "AC1009", 9, "$INSBASE", 10, 0, 20, 0, 30, 0, 9, "$INSUNITS", 70, 6, 9, "$LUNITS", 70, 2, 9, "$LUPREC", 70, 4, 0, "ENDSEC", 0, "SECTION", 2, "TABLES", 0, "TABLE", 2, "LTYPE", 70, 1, 0, "LTYPE", 2, "CONTINUOUS", 70, 0, 3, "Continuous", 72, 65, 73, 0, 40, 0, 0, "ENDTAB", 0, "TABLE", 2, "LAYER", 70, len(self.layers))
        for layer, col in self.layers.items():
            d.extend(pairs(0, "LAYER", 2, layer, 70, 0, 62, col, 6, "CONTINUOUS"))
        d.extend(pairs(0, "ENDTAB", 0, "TABLE", 2, "STYLE", 70, 1, 0, "STYLE", 2, "HY", 70, 0, 40, 0, 41, 1, 50, 0, 71, 0, 42, .11, 3, "sylfaen.ttf", 4, "", 0, "ENDTAB", 0, "ENDSEC", 0, "SECTION", 2, "BLOCKS"))
        if self.reference:
            r = self.reference
            d.extend(pairs(0, "BLOCK", 8, "0", 2, r, 70, 4, 10, 0, 20, 0, 30, 0, 3, r, 1, r + ".dwg", 0, "ENDBLK", 8, "0"))
        d.extend(pairs(0, "ENDSEC", 0, "SECTION", 2, "ENTITIES"))
        d.extend(self.entities)
        d.extend(pairs(0, "ENDSEC", 0, "EOF"))
        def encode(v):
            if isinstance(v, float):
                return f"{v:.9f}"
            return "".join(c if ord(c)<128 else "\\U+" + format(ord(c), "04X") for c in str(v))
        (OUT / (name + ".dxf")).write_text("".join(f"{c}\n{encode(v)}\n" for c, v in d), "ascii")


def rectangle(x,y,w,h):
    return [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]


def anchors():
    dr = Drawing()
    f = base["features"]
    dr.poly(dr.layer("X-SITE",8), f["outer_boundary"], True)
    dr.poly(dr.layer("X-COLUMN",6), f["column"], True)
    dr.circle(dr.layer("X-STACK-MARK",2), f["stack_marker"][0], .10)
    # Reference endpoints are separate from the opening geometry of the bearing wall.
    for p in f["bearing_edge"]:
        dr.circle(dr.layer("X-CONTROL",8),p,.025)
    dr.save("X-BASE")


def existing():
    dr = Drawing("X-BASE")
    for k,r in base["rooms"].items():
        dr.poly(dr.layer("E-ROOM-"+k.upper(),7),r["points"],True)
    for obj in base["lines"]:
        dr.line(dr.layer("E-MARK",8),*obj["points"])
    for i in (1,2,3):
        p=base["features"][f"entry{i}"][0]; a=base["features"][f"arrow{i}"][0]
        dr.line(dr.layer("E-ENTRY-MARK",1),a,p)
        dr.text(dr.layer("E-TEXT",7),a,f"Մուտք {i}")
    dr.save("00-Existing")


def architecture():
    dr = Drawing("X-BASE")
    room_layer=dr.layer("A-SPACE",-8)  # closed polygons for area inquiry, off by default
    centers={"B1":(.22,3.91),"B2":(.45,-2.40),"ST":(3.35,1.15),"BA":(4.20,-3.74),"H1":(3.78,-.97),"BAL":(3.1,6.47),"SH":(7.32,-2.06),"SR":(9.78,-2.17)}
    for r in design["rooms"]:
        dr.poly(room_layer,r["points"],True)
        dr.text(dr.layer("A-ROOM-NAME",8),centers[r["id"]],r["name"]+f"  {r['area']:.2f}",.105)
    for wall in design["walls"]:
        a,b,t = wall["a"],wall["b"],wall["t"]
        dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
        ux,uy=dx/length,dy/length
        def at(s,n):
            return (a[0]+ux*s-uy*n,a[1]+uy*s+ux*n)
        spans=[]
        for op in design["openings"]:
            if op["wall"]==wall["id"]:
                spans.append(sorted((p[0]-a[0])*ux+(p[1]-a[1])*uy for p in (op["a"],op["b"])))
        last=0
        for start,end in sorted(spans)+[(length,length)]:
            start=max(0,min(length,start));end=max(0,min(length,end))
            if start-last>1e-6:
                layer=dr.layer("A-WALL-"+wall["kind"].upper(),3 if wall["kind"]=="new" else 7)
                dr.poly(layer,[at(last,-t/2),at(start,-t/2),at(start,t/2),at(last,t/2)],True)
            last=max(last,end)
    for op in design["openings"]:
        a,b=op["a"],op["b"]; kind=op["kind"]
        if kind in ("window","internal_window","glazed_door","sliding"):
            dr.line(dr.layer("A-GLASS" if kind!="sliding" else "A-DOOR",4),a,b)
        if kind in ("door","entry","glazed_door","entry_common"):
            p,q=(b,a) if op.get("hinge")=="b" else (a,b)
            dx,dy=op["swing"]
            radius=math.dist(a,b); ang=math.atan2(q[1]-p[1],q[0]-p[0])
            turn=(math.atan2(dy,dx)-ang+math.pi)%(2*math.pi)-math.pi
            layer=dr.layer("A-DOOR",2)
            dr.line(layer,p,(p[0]+dx*radius,p[1]+dy*radius))
            dr.poly(layer,[(p[0]+radius*math.cos(ang+turn*i/16),p[1]+radius*math.sin(ang+turn*i/16)) for i in range(17)])
    for item in design["furniture"]:
        dr.poly(dr.layer("A-FURN",8),rectangle(item["x"],item["y"],item["w"],item["d"]),True)
    for key, path in design["routes"].items():
        dr.poly(dr.layer("A-ROUTE-"+key.upper(),-2),path)
    f=base["rooms"]["balcony"]["points"]
    dr.poly(dr.layer("A-BAL-GLASS",4),f[4:]+f[:4])
    dr.save("01-Architecture")


GROUPS={
    "02-Water": {"CW":4,"HW":1},
    "03-Drainage":{"DWV":3,"DROP":6,"ACCESS":2,"FLEX":30},
    "04-Power":{"POWER":2,"CABLE":6},
    "05-Lighting":{"LIGHT":2,"SWITCH":5},
    "06-HVAC":{"HVAC":7,"REF":6,"COND":4,"SUP":4,"EXH":1,"TRANSFER":3,"HEAT":30},
}


def systems():
    for name, kinds in GROUPS.items():
        dr=Drawing("01-Architecture")
        for s in services["routes"]:
            if s["system"] in kinds:
                layer=dr.layer("M-"+s["system"],kinds[s["system"]])
                for a,b in zip(s["points"],s["points"][1:]):
                    dr.line(layer,a,b)
        for s in services["elements"]:
            if s["system"] in kinds:
                layer=dr.layer("M-"+s["system"],kinds[s["system"]]); p=s["point"]; w,d,h=s["size"]
                x,y,z=p
                contour=rectangle(x-w/2,y-d/2,w,d)
                for a,b in zip(contour,contour[1:]+contour[:1]):
                    dr.line(layer,[*a,z],[*b,z])
                dr.text(dr.layer("M-ID",8),(x+.07,y+.06),s["id"],.075)
        dr.save(name)


if __name__=="__main__":
    anchors()
    existing()
    architecture()
    systems()
