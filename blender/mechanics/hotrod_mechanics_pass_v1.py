# BlackMamba Hot Rod — Mechanical Pass v1
# Blender 5.x
# Adds: 4 brake/hub assemblies with 5 lugs each, front double-wishbone suspension,
# steering rack/tie rods, rear solid axle + diff + driveshaft, rear links/Panhard,
# and engine-mount crossbar. Designed from coordinates read from hotrod.blend.

import bpy
import math
import os
from mathutils import Vector

ROOT_NAME = 'BM_Mechanics_v1'
AUTO_SAVE_COPY = True

# ---------------------------- utilities ----------------------------

def ensure_collection(name, parent=None):
    owner = parent or bpy.context.scene.collection
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    # Link if needed (important after a previous generated collection was removed).
    if c not in list(owner.children):
        owner.children.link(c)
    return c


def _delete_collection_recursive(c):
    for child in list(c.children):
        _delete_collection_recursive(child)
    for obj in list(c.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(c)


def delete_collection(name):
    c = bpy.data.collections.get(name)
    if c:
        _delete_collection_recursive(c)


def move_to_collection(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def mat(name, base_color, metallic=0.0, roughness=0.45):
    m = bpy.data.materials.get(name)
    if not m:
        m = bpy.data.materials.new(name)
    m.diffuse_color = (*base_color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
    return m


def smooth(obj):
    if obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True


def add_cylinder_between(name, p1, p2, radius, collection, material=None, vertices=24):
    p1, p2 = Vector(p1), Vector(p2)
    vec = p2 - p1
    length = vec.length
    if length < 1e-6:
        return None
    mid = (p1 + p2) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    # Cylinder local Z -> target vector.
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(vec.normalized())
    obj.rotation_mode = 'XYZ'
    smooth(obj)
    if material:
        obj.data.materials.append(material)
    move_to_collection(obj, collection)
    return obj


def add_box(name, center, extents, collection, material=None, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = extents
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new('EdgeSoftening', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    if material:
        obj.data.materials.append(material)
    move_to_collection(obj, collection)
    return obj


def add_uv_sphere(name, center, scale, collection, material=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(obj)
    if material:
        obj.data.materials.append(material)
    move_to_collection(obj, collection)
    return obj


def world_loc(name, fallback):
    obj = bpy.data.objects.get(name)
    if obj:
        return obj.matrix_world.translation.copy()
    return Vector(fallback)

# ---------------------------- scene data ----------------------------

# The uploaded file currently has these wheel references:
front_r = world_loc('Torus.002', ( 2.385, 2.879, -1.992))
front_l = world_loc('Torus.003', (-2.376, 2.879, -2.042))
rear_l  = world_loc('Torus.001', (-2.338,-5.232, -1.733))
# Mirror rear-left across X for the missing/opposite rear side reference.
rear_r  = Vector((-rear_l.x, rear_l.y, rear_l.z))

# Rebuild cleanly if script is run more than once.
delete_collection(ROOT_NAME)
root = ensure_collection(ROOT_NAME)
brakes = ensure_collection('BM_Brakes_Hubs', root)
front_susp = ensure_collection('BM_Front_Suspension_Steering', root)
rear_susp = ensure_collection('BM_Rear_Axle_Suspension', root)
drive = ensure_collection('BM_Drivetrain_Mounts', root)

steel = mat('BM_Steel', (0.22, 0.24, 0.27), metallic=0.8, roughness=0.28)
dark = mat('BM_DarkSteel', (0.055, 0.065, 0.075), metallic=0.72, roughness=0.32)
rotor = mat('BM_Rotor', (0.34, 0.34, 0.35), metallic=0.9, roughness=0.22)
caliper_mat = mat('BM_Caliper', (0.18, 0.03, 0.02), metallic=0.45, roughness=0.30)

# ---------------------------- brakes / hubs ----------------------------

def wheel_hardware(prefix, c, sign, disc_r):
    c = Vector(c)
    axis = Vector((1,0,0))
    add_cylinder_between(prefix+'_BrakeDisc', c-axis*0.06, c+axis*0.06, disc_r, brakes, rotor, 40)
    add_cylinder_between(prefix+'_Hub', c-axis*0.13, c+axis*0.13, 0.24, brakes, steel, 32)
    bolt_circle = 0.17
    for i in range(5):
        a = math.radians(90 + i*72)
        bc = c + Vector((0, math.cos(a)*bolt_circle, math.sin(a)*bolt_circle)) + axis*(sign*0.12)
        add_cylinder_between(f'{prefix}_Lug_{i+1}', bc-axis*0.08, bc+axis*0.08, 0.045, brakes, dark, 16)
    add_box(prefix+'_Caliper', c + Vector((sign*0.02, -0.43, 0.18)), (0.22,0.20,0.38), brakes, caliper_mat, 0.04)

for side, c in [('L',front_l), ('R',front_r)]:
    wheel_hardware('Front_'+side, c, -1 if side=='L' else 1, 0.56)
for side, c in [('L',rear_l), ('R',rear_r)]:
    wheel_hardware('Rear_'+side, c, -1 if side=='L' else 1, 0.60)

# ---------------------------- front suspension ----------------------------

def front_corner(side, c):
    c = Vector(c)
    sign = -1 if side == 'L' else 1
    xw = c.x - sign*0.18
    add_cylinder_between(f'Front_{side}_Knuckle', (xw,c.y,c.z-0.46), (xw,c.y,c.z+0.46), 0.085, front_susp, steel, 20)
    up = Vector((xw,c.y,c.z+0.32))
    lo = Vector((xw,c.y,c.z-0.34))
    upper_a = Vector((sign*0.78,c.y+0.32,c.z+0.58))
    upper_b = Vector((sign*0.78,c.y-0.48,c.z+0.58))
    lower_a = Vector((sign*0.90,c.y+0.42,c.z-0.42))
    lower_b = Vector((sign*0.90,c.y-0.62,c.z-0.42))
    add_cylinder_between(f'Front_{side}_UpperArm_A', up, upper_a, 0.065, front_susp, dark)
    add_cylinder_between(f'Front_{side}_UpperArm_B', up, upper_b, 0.065, front_susp, dark)
    add_cylinder_between(f'Front_{side}_LowerArm_A', lo, lower_a, 0.075, front_susp, dark)
    add_cylinder_between(f'Front_{side}_LowerArm_B', lo, lower_b, 0.075, front_susp, dark)
    damper_bottom = lo + Vector((-sign*0.06,-0.10,0.08))
    damper_top = Vector((sign*0.62,c.y-0.18,c.z+0.94))
    mid = damper_bottom*0.56 + damper_top*0.44
    add_cylinder_between(f'Front_{side}_CoiloverBody', damper_bottom, mid, 0.095, front_susp, steel)
    add_cylinder_between(f'Front_{side}_CoiloverRod', mid, damper_top, 0.048, front_susp, rotor)
    hub_tie = Vector((xw,c.y-0.22,c.z+0.02))
    rack_end = Vector((sign*0.62,2.56,-2.02))
    add_cylinder_between(f'Front_{side}_TieRod', hub_tie, rack_end, 0.045, front_susp, steel, 18)

front_corner('L', front_l)
front_corner('R', front_r)
add_cylinder_between('SteeringRack', (-0.78,2.56,-2.02), (0.78,2.56,-2.02), 0.075, front_susp, steel, 24)
add_box('FrontCrossmember', (0.0,2.28,-2.30), (1.95,0.28,0.24), front_susp, dark, 0.05)

# ---------------------------- rear axle / links ----------------------------
ry, rz = rear_l.y, rear_l.z
add_cylinder_between('RearAxleTube', (-2.18,ry,rz), (2.18,ry,rz), 0.13, rear_susp, dark, 28)
add_uv_sphere('RearDifferential', (0,ry,rz), (0.55,0.43,0.43), rear_susp, dark)
add_cylinder_between('RearDiffNose', (0,ry+0.28,rz), (0,ry+0.72,rz+0.03), 0.16, rear_susp, dark, 24)
add_cylinder_between('DriveShaft', (0,ry+0.62,rz+0.02), (0,-0.65,-1.55), 0.085, drive, steel, 24)

for side in ('L','R'):
    sign = -1 if side == 'L' else 1
    axle_pick = Vector((sign*1.58,ry,rz-0.08))
    chassis_pick_a = Vector((sign*1.10,-2.95,-1.28))
    chassis_pick_b = Vector((sign*0.68,-3.18,-1.08))
    add_cylinder_between(f'Rear_{side}_TrailingArm', axle_pick, chassis_pick_a, 0.075, rear_susp, dark)
    add_cylinder_between(f'Rear_{side}_UpperLink', (sign*0.78,ry,rz+0.25), chassis_pick_b, 0.060, rear_susp, dark)
    add_cylinder_between(f'Rear_{side}_Coilover', (sign*1.78,ry,rz+0.10), (sign*1.05,-4.12,-0.58), 0.085, rear_susp, steel)

add_cylinder_between('RearPanhard', (-1.70,ry,rz+0.22), (1.25,ry+0.10,rz+0.43), 0.050, rear_susp, steel, 20)

# ---------------------------- drivetrain mounts ----------------------------
add_box('EngineMountCrossbar', (0.0,0.55,-1.70), (1.62,0.22,0.18), drive, dark, 0.04)
add_cylinder_between('EngineMount_L', (-0.78,0.55,-1.70), (-0.58,1.38,-1.38), 0.07, drive, steel)
add_cylinder_between('EngineMount_R', (0.78,0.55,-1.70), (0.58,1.38,-1.38), 0.07, drive, steel)

# Mark root collection in scene custom properties.
bpy.context.scene['BM_MECHANICS_PASS'] = 'v1'
bpy.context.scene['BM_WHEEL_PATTERN'] = '5-lug'
bpy.context.scene['BM_MECHANICS_COMPONENTS'] = 64

# Save a non-destructive copy next to the current .blend.
if AUTO_SAVE_COPY and bpy.data.filepath:
    src = bpy.data.filepath
    base, ext = os.path.splitext(src)
    dst = base + '_mechanical_pass' + ext
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print('BlackMamba mechanical pass saved:', dst)
else:
    print('BlackMamba mechanical pass built. Save the file when ready.')
