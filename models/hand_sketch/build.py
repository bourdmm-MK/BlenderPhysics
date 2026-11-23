"""Quick look: a smoother, skin-coloured version of the PhysicsLearn 3D hand kit
(tools/whiteboard/hand3d.js), three-finger pose for F = q v x B (right hand):
index = v, middle = B (bent 90 deg toward the palm), thumb = F, exactly
perpendicular to both. Sizes and pose maths copied from hand3d.js (hand length ~1).

The kit's capsules are fused into one skin with a voxel remesh + smoothing.
A sketch for deciding the look, not the final hand.

Run:  .\\tools\\run.ps1 hand_sketch     (saves the .blend and renders two still views)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import physkit  # noqa: E402
from physkit.latex import tex  # noqa: E402
from physkit.render import OUTPUT_ROOT  # noqa: E402
from physkit.style import COURSE  # noqa: E402

# ---- hand kit dimensions (hand3d.js, scale 1) ----
PALM = dict(w=0.46, l=0.40, t=0.13)
KNUCKLE_Y = dict(index=0.165, middle=0.055, ring=-0.055, pinky=-0.165)
FINGERS = dict(
    index=([0.17, 0.110, 0.080], [0.047, 0.042, 0.038]),
    middle=([0.19, 0.120, 0.085], [0.049, 0.044, 0.039]),
    ring=([0.17, 0.110, 0.080], [0.046, 0.041, 0.037]),
    pinky=([0.13, 0.090, 0.065], [0.040, 0.036, 0.032]),
)
THUMB = ([0.16, 0.13], [0.058, 0.050])
WRIST = dict(len=0.18, rad=0.105)
FOLDED = [1.25, 1.55, 0.95]
THETA = math.radians(90)          # angle between v and B

# Pose: "three-finger" (this model) or "flat-palm" (models/hand_palm runs this script with
# HAND_POSE set). Same frame for both: v along +x, B along -z (out of the palm face in the
# open palm), F = v x B along +y (thumb).
POSE = globals().get("HAND_POSE", "three-finger")
FLAT = POSE == "flat-palm"
NAME = "hand_palm" if FLAT else "hand_sketch"

SKIN = (0.80, 0.52, 0.38)         # linear RGB of a warm skin tone
NAIL = (0.98, 0.84, 0.82)

args = physkit.parse_args("Hand sketch")
sc = physkit.new_scene(fps=24)
parts = []


def capsule(p, d, length, r):
    """Cylinder + two spheres from point p along unit direction d."""
    c = p + d * (length / 2)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length, location=c, vertices=24)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    parts.append(o)
    for q in (p, p + d * length):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=q, segments=24, ring_count=12)
        parts.append(bpy.context.object)


def chain(base, d0, axis, lens, rads, curls):
    """Like buildChain in hand3d.js: each curl rotates the direction about `axis`."""
    from mathutils import Matrix
    d, p = d0.normalized(), base.copy()
    for i, (L, r, c) in enumerate(zip(lens, rads, curls)):
        d = (Matrix.Rotation(c, 3, axis) @ d).normalized()
        if i > 0:                                   # slight swelling at each finger joint
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 1.13, location=p, segments=24, ring_count=12)
            parts.append(bpy.context.object)
        capsule(p, d, L, r)
        p = p + d * L
    return p, d


X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# palm: rounded slab (knuckle edge at x ~ 0, body toward -x, palm faces -z)
bpy.ops.mesh.primitive_cube_add(location=(-PALM["l"] / 2 + 0.02, 0, 0))
palm = bpy.context.object
palm.scale = (PALM["l"] / 2 + 0.02, PALM["w"] / 2, PALM["t"] / 2)
bpy.ops.object.transform_apply(scale=True)
bev = palm.modifiers.new("bevel", "BEVEL")
bev.width, bev.segments = 0.05, 4
parts.append(palm)
for k, y in KNUCKLE_Y.items():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=PALM["t"] * 0.47, location=(0.01, y, 0.022))
    parts.append(bpy.context.object)
# rounder palm: a gentle dome on the back of the hand and a soft pad on the palm side
for loc, sc_ in (((-0.17, -0.01, 0.035), (0.21, 0.21, 0.055)),
                 ((-0.20, -0.03, -0.035), (0.19, 0.19, 0.05))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc)
    o = bpy.context.object
    o.scale = sc_
    bpy.ops.object.transform_apply(scale=True)
    parts.append(o)
# tendons: faint ridges on the back of the hand, from each knuckle toward the wrist
for k, y in KNUCKLE_Y.items():
    a = Vector((-0.03, y, 0.062))
    b = Vector((-0.34, y * 0.4, 0.07))
    capsule(a, (b - a).normalized(), (b - a).length, 0.011)# wrist -> forearm: oval (wider than thick), narrowing at the wrist, then widening
for x0, x1, r0, r1 in ((-0.36, -0.47, 0.125, 0.108),):   # the hand ends at the wrist
    L = abs(x1 - x0)
    bpy.ops.mesh.primitive_cone_add(radius1=r0, radius2=r1, depth=L, vertices=32,
                                    location=((x0 + x1) / 2, 0, -0.005))
    o = bpy.context.object
    o.rotation_euler = (0, math.radians(-90), 0)     # cone axis along -x
    o.scale = (1, 1, 1)
    bpy.ops.object.transform_apply(rotation=True)
    o.scale = (1, 1.0, 0.62)                         # flatten: thinner than wide
    bpy.ops.object.transform_apply(scale=True)
    parts.append(o)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.108, location=(-0.47, 0, -0.005))
cap = bpy.context.object
cap.scale = (0.3, 1.0, 0.62)          # soft rounded end, same oval as the forearm
bpy.ops.object.transform_apply(scale=True)
parts.append(cap)
tips = {}
tips["index"] = chain(Vector((0, KNUCKLE_Y["index"], 0)), X, Y, *FINGERS["index"], [0, 0, 0])
tips["middle"] = chain(Vector((0, KNUCKLE_Y["middle"], 0)), X, Y, *FINGERS["middle"],
                       [0, 0, 0] if FLAT else [THETA, 0, 0])
for k in ("ring", "pinky"):                     # folded in the three-finger pose, straight in the open palm
    t_ = chain(Vector((0, KNUCKLE_Y[k], 0)), X, Y, *FINGERS[k], [0, 0, 0] if FLAT else FOLDED)
    if FLAT:
        tips[k] = t_
tips["thumb"] = chain(Vector((-0.17, 0.20, 0)), Y, Z, *THUMB, [0, 0])
# fleshy base of the thumb (thenar), so the thumb grows out of the palm
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(-0.2, 0.13, -0.01))
thenar = bpy.context.object
thenar.scale = (1.3, 0.8, 0.6)
parts.append(thenar)

# fuse everything into one skin
for o in parts:
    for m in o.modifiers:
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier=m.name)
with bpy.context.temp_override(active_object=parts[0], object=parts[0],
                               selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
hand = parts[0]
hand.name = "hand"
rm = hand.modifiers.new("remesh", "REMESH")
rm.mode, rm.voxel_size = "VOXEL", 0.008
sm = hand.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
sm.factor, sm.iterations, sm.smooth_type = 0.8, 12, "LENGTH_WEIGHTED"
sm.use_only_smooth = True
sub = hand.modifiers.new("subsurf", "SUBSURF")
sub.levels = sub.render_levels = 1
bpy.ops.object.shade_smooth()

# ---- soft glow: each finger that carries a vector takes on that vector's colour ----
# Bake the fused skin first (so we can paint its vertices), then store per vertex:
#   "glow"       = vector colour + strength (alpha), fading out toward the knuckle
#   "export_col" = the final skin+tint colour, for the interactive viewer
for mname in ("remesh", "smooth"):
    with bpy.context.temp_override(object=hand, active_object=hand):
        bpy.ops.object.modifier_apply(modifier=mname)
GLOW = {   # finger axis start, direction, length (to the tip), radius, colour
    "index": (Vector((0, KNUCKLE_Y["index"], 0)), X, sum(FINGERS["index"][0]) + 0.05, 0.047,
              COURSE["velocity"]),
    "middle": (Vector((0, KNUCKLE_Y["middle"], 0)), Vector((math.cos(THETA), 0, -math.sin(THETA))),
               sum(FINGERS["middle"][0]) + 0.05, 0.049, COURSE["position"]),
    "thumb": (Vector((-0.17, 0.20, 0)), Y, sum(THUMB[0]) + 0.06, 0.058, COURSE["force"]),
}
if FLAT:   # all four straight fingers carry v; B is marked by a spot where it leaves the palm face
    GLOW = {k: (Vector((0, KNUCKLE_Y[k], 0)), X, sum(FINGERS[k][0]) + 0.05, FINGERS[k][1][0],
                COURSE["velocity"]) for k in KNUCKLE_Y}
    GLOW["thumb"] = (Vector((-0.17, 0.20, 0)), Y, sum(THUMB[0]) + 0.06, 0.058, COURSE["force"])
PALM_SPOT = Vector((-0.2, 0, -0.07))     # palm face, where B exits (open palm only)
GLOW_TINT = 0.7          # how far the skin colour moves toward the vector colour


def smooth01(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


glow_attr = hand.data.color_attributes.new("glow", "FLOAT_COLOR", "POINT")
exp_attr = hand.data.color_attributes.new("export_col", "FLOAT_COLOR", "POINT")
mw = hand.matrix_world
for i, vert in enumerate(hand.data.vertices):
    co = mw @ vert.co
    best_w, best_col = 0.0, (0.0, 0.0, 0.0)
    for start, d, L, r, col in GLOW.values():
        rel = co - start
        t = rel.dot(d)
        radial = (rel - d * t).length
        w = smooth01(0.02, 0.17, t) * (1 - smooth01(r * 1.2, r * 1.8, radial))
        if w > best_w:
            best_w, best_col = w, col
    if FLAT and co.z < -0.02:
        w = 1 - smooth01(0.05, 0.09, (co - PALM_SPOT).length)
        if w > best_w:
            best_w, best_col = w, COURSE["position"]
    glow_attr.data[i].color = (*best_col, best_w)
    k = GLOW_TINT * best_w
    exp_attr.data[i].color = tuple(min(1.0, SKIN[j] * (1 - k) + best_col[j] * k * 1.35) for j in range(3)) + (1.0,)


def material(name, color, rough=0.5, sss=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.03
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*color, 1)
    return m


def skin_material():
    """Skin: subsurface scattering, faint colour blotches, fine pore bump."""
    m = material("skin", SKIN, 0.5, sss=0.3)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    blotch = nt.nodes.new("ShaderNodeTexNoise")
    blotch.inputs["Scale"].default_value = 18
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.74, 0.45, 0.33, 1)
    ramp.color_ramp.elements[1].color = (0.84, 0.56, 0.42, 1)
    nt.links.new(blotch.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    pores = nt.nodes.new("ShaderNodeTexNoise")
    pores.inputs["Scale"].default_value = 450
    pores.inputs["Detail"].default_value = 4
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(pores.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # soft vector-colour glow from the "glow" attribute: tint the skin + a gentle emission
    ga = nt.nodes.new("ShaderNodeAttribute")
    ga.attribute_name = "glow"
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = GLOW_TINT
    nt.links.new(ga.outputs["Alpha"], k.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(k.outputs[0], mix.inputs[0])
    nt.links.new(ramp.outputs["Color"], mix.inputs[6])
    nt.links.new(ga.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    es = nt.nodes.new("ShaderNodeMath")
    es.operation = "MULTIPLY"
    es.inputs[1].default_value = 0.9
    nt.links.new(ga.outputs["Alpha"], es.inputs[0])
    nt.links.new(ga.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(es.outputs[0], b.inputs["Emission Strength"])
    return m


hand.data.materials.append(skin_material())

# fingernails: an oval patch shrink-wrapped onto the skin near each fingertip,
# then given a little thickness, so it sits ON the finger like a real nail
import bmesh  # noqa: E402
nail_mat = material("nail", NAIL, 0.12)
nail_mat.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.6
for k in tips:
    tip, d = tips[k]
    up = X if (k == "middle" and not FLAT) else Z      # back of the finger (bent middle faces +x)
    r = FINGERS[k][1][-1] if k != "thumb" else THUMB[1][-1]
    a, b_ = r * 0.95, r * 0.8            # half-length along the finger, half-width
    me = bpy.data.meshes.new("nail")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=40, y_segments=40, size=1.0)
    for vert in list(bm.verts):
        if (vert.co.x) ** 2 + (vert.co.y) ** 2 > 1.0:
            bm.verts.remove(vert)
    for vert in bm.verts:
        vert.co.x *= a
        vert.co.y *= b_
    bm.to_mesh(me)
    bm.free()
    n = bpy.data.objects.new("nail_" + k, me)
    sc.collection.objects.link(n)
    side = d.cross(up).normalized()      # finger frame: x along finger, z = back normal
    from mathutils import Matrix
    n.matrix_world = Matrix((
        (d.x, side.x, up.x, 0), (d.y, side.y, up.y, 0), (d.z, side.z, up.z, 0), (0, 0, 0, 1)))
    n.location = tip - d * (r * 0.25) + up * (r * 1.1)   # right behind the rounded tip
    sw = n.modifiers.new("onto_skin", "SHRINKWRAP")
    sw.target, sw.wrap_method, sw.wrap_mode, sw.offset = hand, "NEAREST_SURFACEPOINT", "OUTSIDE_SURFACE", 0.0008
    so = n.modifiers.new("thickness", "SOLIDIFY")
    so.thickness, so.offset = 0.0045, 1.0
    ss = n.modifiers.new("smooth", "SUBSURF")
    ss.levels = ss.render_levels = 1
    n.data.materials.append(nail_mat)
    for poly in n.data.polygons:
        poly.use_smooth = True
# vectors in course colours, each running along its finger and out past the tip
VEC = {"index": ("v", COURSE["velocity"]), "middle": ("B", COURSE["position"]),
       "thumb": ("F", COURSE["force"])}
starts = {"index": Vector((0, KNUCKLE_Y["index"], 0)),
          "middle": Vector((0, KNUCKLE_Y["middle"], 0)) ,
          "thumb": Vector((-0.17, 0.20, 0))}
dirs = {"index": X, "middle": Vector((math.cos(THETA), 0, -math.sin(THETA))), "thumb": Y}
if FLAT:   # v along the middle of the four fingers; B comes in at the back of the palm and leaves its face
    starts["index"] = Vector((0, 0, 0))
    starts["middle"] = Vector((-0.2, 0, 0.45))
    dirs["middle"] = -Z
cam_objs = []
labels = []
label_pts = []
for k, (sym, col) in VEC.items():
    m = material("vec_" + sym, col, 0.4, emit=0.6)
    d = dirs[k]
    L = 0.75
    p0 = starts[k]                      # on the finger's own axis, so it exits the fingertip centre
    shaft_len = L - 0.09
    bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=shaft_len, location=p0 + d * shaft_len / 2)
    s = bpy.context.object
    s.rotation_mode = "QUATERNION"
    s.rotation_quaternion = Z.rotation_difference(d)
    s.data.materials.append(m)
    bpy.ops.mesh.primitive_cone_add(radius1=0.04, depth=0.09, location=p0 + d * (L - 0.045))
    c = bpy.context.object
    c.rotation_mode = "QUATERNION"
    c.rotation_quaternion = Z.rotation_difference(d)
    c.data.materials.append(m)
    lab = tex(rf"\vec {sym}", 0.11, col, tuple(p0 + d * (L + 0.08)))
    lab.data.materials.clear()          # the SVG import brings a black material
    lab.data.materials.append(m)
    labels.append(lab)
    label_pts.append((sym, col, p0 + d * (L + 0.08)))

# black course background, soft studio light
w = sc.world
w.color = (0, 0, 0)
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
physkit.add_lights(strength=3.0)
# warm rim light from behind, so the hand's outline stands out from the black
rim_d = bpy.data.lights.new("rim", type="AREA")
rim_d.energy, rim_d.size, rim_d.color = 45, 1.5, (1.0, 0.9, 0.8)
rim = bpy.data.objects.new("rim", rim_d)
sc.collection.objects.link(rim)
rim.location = (-0.6, 1.8, 1.4)
rt = rim.constraints.new("TRACK_TO")
rim_target = bpy.data.objects.new("rim_target", None)
sc.collection.objects.link(rim_target)
rim_target.location = (-0.1, 0.1, -0.1)
rt.target, rt.track_axis, rt.up_axis = rim_target, "TRACK_NEGATIVE_Z", "UP_Y"

center = Vector((-0.02, 0.12, -0.2))
views = {"front": Vector((1.1, -1.45, 0.75)), "side": Vector((-0.9, 1.6, 0.9))}
target = bpy.data.objects.new("target", None)
sc.collection.objects.link(target)
target.location = center
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 28
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
tr = cam.constraints.new("TRACK_TO")
tr.target, tr.track_axis, tr.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = cam
for lab in labels:                      # labels always face the camera
    cr = lab.constraints.new("TRACK_TO")
    cr.target, cr.track_axis, cr.up_axis = cam, "TRACK_Z", "UP_Y"

out = OUTPUT_ROOT / NAME
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{NAME}.blend"))

try:
    sc.render.engine = "BLENDER_EEVEE"
except TypeError:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = 32
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = "PNG"
for name, loc in views.items():
    cam.location = center + loc
    sc.render.filepath = str(out / f"{NAME}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("[hand] rendered", sc.render.filepath)

# ---------------- interactive viewer: .glb + a rotatable web page ----------------
# Export a lighter copy of the look (procedural skin texture -> flat skin colour,
# fewer polygons), then write hand_viewer.html with the labels as floating tags.
skin = hand.data.materials[0]
bsdf = skin.node_tree.nodes["Principled BSDF"]
for inp in ("Base Color", "Normal", "Emission Color", "Emission Strength"):
    for link in list(bsdf.inputs[inp].links):
        skin.node_tree.links.remove(link)
bsdf.inputs["Emission Strength"].default_value = 0.0
ca = skin.node_tree.nodes.new("ShaderNodeVertexColor")      # baked skin + soft tint
ca.layer_name = "export_col"
skin.node_tree.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
hand.data.color_attributes.active_color = hand.data.color_attributes["export_col"]
sub.levels = 0
dec = hand.modifiers.new("lighter", "DECIMATE")
dec.ratio = 0.35
dec.show_render = False
for o in bpy.data.objects:
    o.select_set(o.type == "MESH")
bpy.ops.export_scene.gltf(filepath=str(out / f"{NAME}.glb"), export_format="GLB",
                          use_selection=True, export_apply=True, export_yup=True)
# a second copy with only the hand (skin + nails, no arrows or labels) for PhysicsLearn
# whiteboards, which draw their own vectors along the fingers
for o in bpy.data.objects:
    o.select_set(o.type == "MESH" and (o.name == "hand" or o.name.startswith("nail_")))
bpy.ops.export_scene.gltf(filepath=str(out / f"{NAME}_board.glb"), export_format="GLB",
                          use_selection=True, export_apply=True, export_yup=True)


def hexcol(c):
    to_srgb = lambda x: 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return "#" + "".join(f"{round(255 * to_srgb(x)):02X}" for x in c)


hotspots = "\n".join(
    f'  <div class="hs" slot="hotspot-{sym}" data-position="{q.x:.3f} {q.z:.3f} {-q.y:.3f}" '
    f'data-normal="0 1 0" style="color:{hexcol(col)}"><span class="vec">{sym}</span></div>'
    for sym, col, q in label_pts)
(out / "hand_viewer.html").write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Hand sketch - rotate me</title>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
<style>
 html,body {{ margin:0; height:100%; background:#000; color:#DDD; font-family:"Times New Roman",serif; }}
 model-viewer {{ width:100%; height:100%; background:#000; --poster-color:#000; }}
 .hs {{ font-style:italic; font-size:30px; pointer-events:none; transform:translate(8px,-8px); }}
 .vec {{ position:relative; display:inline-block; }}
 .vec::before {{ content:"\\2192"; position:absolute; left:0; right:0; top:-0.55em; font-size:0.6em;
                font-style:normal; text-align:center; }}
 .bar {{ position:fixed; bottom:10px; left:0; right:0; text-align:center; font-size:15px; color:#999; }}
 button {{ font:inherit; background:#222; color:#DDD; border:1px solid #555; border-radius:6px; padding:4px 12px; cursor:pointer; }}
</style></head>
<body>
<model-viewer id="mv" src="{NAME}.glb?{int(__import__('time').time())}" camera-controls
  camera-orbit="35deg 65deg 2.2m" field-of-view="35deg" exposure="0.95" environment-image="neutral"
  shadow-intensity="0" interaction-prompt="none">
{hotspots}
</model-viewer>
<div class="bar">drag = rotate &nbsp;·&nbsp; scroll = zoom &nbsp;·&nbsp; right-drag = move &nbsp;
 <button onclick="const m=document.getElementById('mv'); m.autoRotate=!m.autoRotate">spin on/off</button></div>
</body></html>
""", encoding="utf-8")
print("[hand] viewer", out / "hand_viewer.html")