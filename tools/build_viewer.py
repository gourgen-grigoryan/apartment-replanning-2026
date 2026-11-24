"""Միավորում է ընթացիկ նախագծային տվյալներն ու անցանց եռաչափ դիտիչը։"""
import base64
import json
import sys
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((root / path).read_text(encoding='utf-8-sig'))

sys.path.insert(0,str(root/'05-model'))
from scene import objects, M

def model_mesh(services):
    # Millimetre coordinates and shaded material colours, packed once for offline WebGL.
    packed=bytearray()
    groups=[]
    route_ids={r['id'] for r in services['routes']}
    dtype=np.dtype([('position','<i2',(3,)),('colour','u1',(4,))])
    for obj in objects:
        key,layer=obj['id'],obj['layer']
        if layer in ('space','void','ceiling'):
            continue
        if layer=='floor': key=key.removeprefix('SL-')
        elif key=='COL': key='C01'
        elif layer=='glazing': key='GL'
        elif 'system' in obj:
            ident=obj['element_id']
            key=('S-' if ident in route_ids else 'E-')+ident
            layer=obj['system']
        for is_glass in (False,True):
            start=len(packed)//dtype.itemsize
            for material,vertices,faces in obj['meshes']:
                if (material=='glass')!=is_glass:
                    continue
                triangles=vertices[faces]
                normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
                lengths=np.linalg.norm(normals,axis=1)
                valid=lengths>1e-10
                if not np.any(valid): continue
                normals=normals[valid]/lengths[valid,None]
                shade=.77+.23*np.clip(normals@[-.40,-.55,.74],-1,1)
                colour=np.array([int(M[material][i:i+2],16) for i in (0,2,4)])
                rows=np.empty((sum(valid),3),dtype=dtype)
                rows['position']=np.rint(triangles[valid]*1000)
                rows['colour'][:,:,:3]=np.rint(shade[:,None]*colour)[:,None,:]
                rows['colour'][:,:,3]=49 if is_glass else 255
                packed.extend(rows.tobytes())
            count=len(packed)//dtype.itemsize-start
            if count: groups.append([key,layer,start,count,is_glass])
    return {'vertices':base64.b64encode(packed).decode('ascii'),'parts':groups}

data = {'arch':read('02-design/design.json'),'services':read('04-services/services.json')}
data['mesh']=model_mesh(data['services'])
json_text=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
html=(root/'tools/viewer-template.html').read_text(encoding='utf8')
out=root/'05-model/Viewer.html'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(html.replace('___MODEL_JSON___',json_text).replace('___REVISION___',data['arch']['revision']),encoding='utf8')
print(out.name,out.stat().st_size,'bytes;',sum(p[3] for p in data['mesh']['parts'])//3,'triangles')
