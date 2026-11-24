"""Վերաբացել IFC4 ֆայլը IfcOpenShell-ով և ստուգել մարմինները, մակերեսներն ու ինժեներական հատկանիշները։"""
import json
import math
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.validate

root=Path(__file__).resolve().parents[1]
model=ifcopenshell.open(root/'05-model/apartment.ifc')
design=json.loads((root/'02-design/design.json').read_text('utf8'))
mep=json.loads((root/'04-services/services.json').read_text('utf8'))
log=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(model,log)
assert not log.statements
elements={x.Tag:x for x in model.by_type('IfcElement')}
spaces={o.Name.rsplit(' | SPACE-',1)[-1]:o for o in model.by_type('IfcSpace')}
props=ifcopenshell.util.element.get_psets
for r in design['rooms']:
    assert math.isclose(props(spaces[r['id']])['Qto_SpaceBaseQuantities']['NetFloorArea'],r['area'],rel_tol=0,abs_tol=.000000051)
for r in mep['routes']:
    matches=props(elements['MEP-'+r['id']])['Apartment_ServiceRoute']
    assert math.isclose(matches['GeometryDiameter'],r['diameter_m'],abs_tol=.000000051)
    for field,attr in [('length_plan','PlanLength'),('slope','Slope'),('invert_start','StartInvert'),('invert_end','EndInvert')]:
        if r.get(field) is not None:assert math.isclose(matches[attr],r[field],abs_tol=.000000051)
assert all('MEP-'+e['id'] in elements for e in mep['elements'])
assert props(elements['LB'])['Pset_WallCommon']['LoadBearing']
assert len(model.by_type('IfcOpeningElement'))==len(design['openings']) and 'O-W-LB' not in elements and len(spaces)==8
settings=ifcopenshell.geom.settings()
products=[o for o in model.by_type('IfcProduct') if getattr(o,'Representation',None)]
triangles=sum(len(ifcopenshell.geom.create_shape(settings,o).geometry.faces)//3 for o in products)
print(model.schema,len(products),'products',triangles,'triangles',len(model.by_type('IfcSystem')),'systems',len(log.statements),'schema findings; 8 net areas and 60 route property sets verified')
