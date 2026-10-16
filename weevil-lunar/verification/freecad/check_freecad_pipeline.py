"""Analytic checks using the actual FreeCAD kernel, not mocked geometry."""
import json
import math
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cad" / "scripts"))
import FreeCAD as App
import Part
from freecad_audit import audit_document, export_verified, metrics, pair_check, world_shape


checks: list[str] = []
def passed(name):
    checks.append(name)


def close(a,b):
    assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-12), (a,b)


box=Part.makeBox(10,20,30)
row=metrics('analytic_box',box,2700)
close(row['mass_kg'],0.0162)
for i,value in enumerate([1.755e-6,1.350e-6,0.675e-6]):
    close(row['inertia_com_world_kg_m2'][i][i],value)
assert row['center_of_mass_m']==[0.005,0.01,0.015]
passed('10x20x30 mm box: analytic mass, COM and inertia')
assert metrics('no_material',box)['mass_kg'] is None
assert metrics('no_material',box)['inertia_com_world_kg_m2'] is None
passed('Unknown density produces no invented physical mass/inertia')
for bad in [0,-1,float('nan'),float('inf')]:
    try: metrics('bad',box,bad)
    except ValueError: pass
    else: raise AssertionError('Invalid density accepted')
passed('Non-positive/non-finite density rejected')

for x,wanted in [(11,'clear'),(10,'below_clearance'),(9,'overlap'),(0,'duplicate')]:
    second=Part.makeBox(10,20,30,App.Vector(x,0,0))
    pair=pair_check('a',box,'b',second,0.1,1e-6)
    assert pair['status']==wanted,pair
    if x==9: close(pair['overlap_volume_mm3'],600)
passed('Gap, touching, overlap and duplicate distinguished')

doc=App.newDocument('AnalyticTest')
parent=doc.addObject('App::Part','Parent')
obj=doc.addObject('Part::Feature','PhysicalBox');obj.Shape=box
parent.addObject(obj)
parent.Placement=App.Placement(App.Vector(100,0,0),App.Rotation(App.Vector(0,0,1),90))
obj.Placement=App.Placement(App.Vector(2,0,0),App.Rotation())
doc.recompute()
shape=world_shape(obj)
row=metrics('rotated',shape,2700)
for actual,expected in zip(row['center_of_mass_m'],[0.09,0.007,0.015]): close(actual,expected)
close(row['inertia_com_world_kg_m2'][0][0],1.350e-6)
close(row['inertia_com_world_kg_m2'][1][1],1.755e-6)
passed('Nested assembly placement and rotated inertia axes applied once')

# A non-axis-aligned case catches transposition/sign errors in inertia export.
obj.Placement=App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),-45))
doc.recompute()
rotated=metrics('45deg',world_shape(obj),2700)
close(rotated['inertia_com_world_kg_m2'][0][0],1.5525e-6)
close(rotated['inertia_com_world_kg_m2'][0][1],0.2025e-6)
close(rotated['inertia_com_world_kg_m2'][1][0],0.2025e-6)
passed('45-degree rotated solid: analytic off-diagonal inertia')

report,shapes=audit_document(doc,{'objects':[{'name':'PhysicalBox'}]})
assert report['passed'],report
report,_=audit_document(doc,{'objects':[{'name':'Missing'}]})
assert not report['passed']
report,_=audit_document(doc,{'objects':[{'name':'Parent'}]})
assert not report['passed']
face=doc.addObject('Part::Feature','Face');face.Shape=Part.makePlane(10,10)
report,_=audit_document(doc,{'objects':[{'name':'Face'}]})
assert not report['passed']
passed('Missing object, aggregate and non-solid rejected')

other=doc.addObject('Part::Feature','SecondBox');other.Shape=Part.makeBox(5,6,7,App.Vector(200,30,10))
report,shapes=audit_document(doc,{'objects':[{'name':'PhysicalBox'},{'name':'SecondBox'}]})
assert report['passed'],report
with tempfile.TemporaryDirectory() as folder:
    target=Path(folder)/'tested.step'
    result=export_verified(shapes,target)
    assert result['solids']==2 and result['spatial_roundtrip']
    assert 'AP242_' in result['file_schema']
    close(result['volume_mm3'],6210)
    try: export_verified(shapes,target)
    except ValueError: pass
    else: raise AssertionError('Overwrote existing output')
passed('AP242 export: header, count, volume and placement round-trip; overwrite refused')
App.closeDocument(doc.Name)

from build_parametric_fixtures import BODY_NAMES, build_document
doc = build_document()
manifest = {'design_status': 'concept', 'minimum_clearance_mm': 0.1,
            'objects': [{'name': name} for name in BODY_NAMES]}
report, shapes = audit_document(doc, manifest)
assert report['passed'], report
assert len(shapes) == 5
assert report['design_limitations']
assert all(row['mass_kg'] is None for row in report['parts'])
assert all(row['design_status'] == 'concept' for row in report['parts'])
close(report['parts'][1]['center_of_mass_m'][0], 0.06)
close(doc.Body_PivotFlange.Shape.Volume, math.pi * (14**2 - 6.1**2 - 4 * 1.6**2) * 4.5)
passed('Five native PartDesign bodies audit as concept geometry, with placements and no invented density')

with tempfile.TemporaryDirectory() as folder:
    saved = Path(folder)/'Fixtures.FCStd'
    doc.saveAs(str(saved))
    App.closeDocument(doc.Name)
    doc = App.openDocument(str(saved))
    sheet = doc.Params
    for alias, body_name in [
        ('flange_thickness_mm', 'Body_PivotFlange'),
        ('servo_mount_height_mm', 'Body_ServoMount'),
        ('ra_leg_b_mm', 'Body_RightAngleMount'),
        ('lever_length_mm', 'Body_ActuationLever25'),
        ('spline_hub_thickness_mm', 'Body_AdapterBlank'),
    ]:
        cell = sheet.getCellFromAlias(alias)
        original = sheet.getContents(cell)
        value = sheet.getPropertyByName(alias).Value
        initial_volume = doc.getObject(body_name).Shape.Volume
        for factor in (0.9, 1.1):
            sheet.set(cell, f'{value * factor} mm')
            doc.recompute()
            report, shapes = audit_document(doc, manifest)
            assert report['passed'], report
            assert not math.isclose(doc.getObject(body_name).Shape.Volume, initial_volume, rel_tol=1e-5)
        sheet.set(cell, original)
        doc.recompute()
        close(doc.getObject(body_name).Shape.Volume, initial_volume)
    passed('Saved/reopened native model: +/-10 percent dimension sweeps rebuild all five bodies')
    sheet.set(sheet.getCellFromAlias('flange_hole_count'), '6')
    doc.recompute()
    assert doc.FlangeBoltPattern.Occurrences == 6
    report, shapes = audit_document(doc, manifest)
    assert report['passed'], report
    result = export_verified(shapes, Path(folder)/'fixtures.step')
    assert result['solids'] == 5 and result['spatial_roundtrip']
    passed('Live bolt-count expression and five-body AP242 export round trip')

    # Cached geometry must not be exported after an upstream expression fails.
    sheet.set(sheet.getCellFromAlias('flange_thickness_mm'), '-1 mm')
    doc.recompute()
    report, _ = audit_document(doc, manifest)
    assert not report['passed'], report
    passed('Broken upstream parameter prevents export of stale body geometry')
App.closeDocument(doc.Name)
print(json.dumps({'passed': len(checks), 'checks': checks, 'freecad': App.Version(), 'occt': Part.OCC_VERSION}, indent=2))
