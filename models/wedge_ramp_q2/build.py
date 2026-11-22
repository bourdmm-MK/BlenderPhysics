"""Exam question 2: m1 = m (speed v to the left) meets the frictionless ramp of
m2 = 3m (speed 3v to the right), slides up it with a smooth transition, reaches
its highest point and slides back down until it separates. sin(theta) = 2/3.

Everything moves from the real equations (no hand-placed keyframes):
- horizontal momentum 8mv and energy 14mv^2 are conserved;
- on the ramp, m1's acceleration relative to m2 is constant:
  a = 4 g sin(theta) / (3 + sin^2(theta)) = 24g/31;
- just after contact the relative speed up the ramp is U = v sqrt(12 / (1 - cos^2(theta)/4));
- at the top both move at 2v and h = 6v^2/g; after separation v1 = 5v, v2 = v.

Drawn in the shared course style (physkit.style; PhysicsAid knowledge/visual-style.md).
Twins with the same timing: PhysicsAid expermients/wedge_ramp_q2/ (Manim + whiteboard).

Run:  .\\tools\\run.ps1 wedge_ramp_q2 -mode preview -still   (highest point)
      .\\tools\\run.ps1 wedge_ramp_q2 -mode preview          (video, ~30 s)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import bpy  # noqa: E402

import physkit  # noqa: E402
from physkit.style import COURSE, label_font  # noqa: E402

# ---------------- physics (SI units, m = 1 kg) ----------------
g = 9.81
SIN = 2 / 3
COS = math.sqrt(1 - SIN ** 2)
H2, H1 = 1.0, 0.45          # heights of m2's ramp and of m1 (m)
H_MAX = 0.4                 # chosen rise of m1 (m)  ->  v from h = 6 v^2 / g
v = math.sqrt(g * H_MAX / 6)
A = 4 * g * SIN / (3 + SIN ** 2)
U = v * math.sqrt(12 / (1 - COS ** 2 / 4))
W = (8 * v + U * COS) / 4   # m2's speed just after contact
GAP = 1.6                   # starting distance between the touching corners (m)
T_CONTACT = GAP / (4 * v)
T_RIDE = 2 * U / A
T_AFTER = 0.7
T_TOTAL = T_CONTACT + T_RIDE + T_AFTER
SLOW, FPS = 5, 24           # slow motion x5 -> about 10 s of video


def state(t):
    """X2 (m2's ramp foot), x1, z1 (m1's lower corner), (v1x, v1z), v2x, phase."""
    if t <= T_CONTACT:
        return 3 * v * t, GAP - v * t, 0.0, (-v, 0.0), 3 * v, "before"
    X2c = 3 * v * T_CONTACT
    tau = t - T_CONTACT
    if tau <= T_RIDE:
        s = U * tau - 0.5 * A * tau ** 2           # distance up the ramp
        sd = U - A * tau
        X2 = X2c + W * tau + (COS / 4) * (s - U * tau)
        X2d = W + (COS / 4) * (sd - U)
        phase = "top" if abs(sd) < 0.12 * U else ("up" if sd > 0 else "down")
        return X2, X2 - s * COS, s * SIN, (X2d - sd * COS, sd * SIN), X2d, phase
    X2e = X2c + W * T_RIDE - (COS / 4) * U * T_RIDE
    te = tau - T_RIDE
    return X2e + v * te, X2e + 5 * v * te, 0.0, (5 * v, 0.0), v, "after"


CAPTIONS = {
    "before": "Before contact",
    "up": "m1 slides up the ramp (no friction)",
    "top": "Highest point: both move at 2v,  h = 6v²/g",
    "down": "m1 slides back down",
    "after": "After separation: v1 = 5v,  v2 = v",
}

# ---------------- scene (course style: flat colours on black) ----------------
args = physkit.parse_args("Exam question 2: block on a moving ramp")
sc = physkit.new_scene(fps=FPS)
N_FRAMES = int(T_TOTAL * SLOW * FPS) + 1
sc.frame_start, sc.frame_end = 1, N_FRAMES

SAND, INSIDE = COURSE["body"], COURSE["body_text"]
AUX, STRUCT, AXES, VEL = COURSE["aux"], COURSE["structure"], COURSE["axes"], COURSE["velocity"]
FONT = label_font()
DEPTH = 0.5
FRONT, BACK = -0.4, 0.4


def prism(name, pts, color):
    """Extrude a 2D outline (x, z) along y."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    fr = [bm.verts.new((x, -DEPTH / 2, z)) for x, z in pts]
    bk = [bm.verts.new((x, DEPTH / 2, z)) for x, z in pts]
    bm.faces.new(fr[::-1])
    bm.faces.new(bk)
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.color = color + (1,)
    return o


def text(body, loc, size=0.2, color=AUX, align="CENTER", y=FRONT):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body, cu.font, cu.size = body, FONT, size
    cu.align_x, cu.align_y = align, "CENTER"
    o = bpy.data.objects.new("txt", cu)
    sc.collection.objects.link(o)
    o.location = (loc[0], y, loc[1])
    o.rotation_euler = (math.radians(90), 0, 0)
    o.color = color + (1,)
    return o


def label(main, sub, loc, size, color):
    """Letter with a real (smaller, lower) subscript, e.g. m_1."""
    o = text(main, loc, size, color)
    s = text(sub, (0, 0), size * 0.6, color)
    s.parent = o
    s.rotation_euler = (0, 0, 0)
    s.location = (size * 0.45, -size * 0.25, 0)
    return o


def box(name, size, color, loc, rot_y=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name, o.scale, o.rotation_euler = name, size, (0, rot_y, 0)
    o.color = color + (1,)
    return o


def arrow_static(p, q, color, width=0.02, head=0.12):
    dx, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    e = (q[0] - ux * head, q[1] - uz * head)
    box("seg", (math.hypot(e[0] - p[0], e[1] - p[1]), 0.01, width), color,
        ((p[0] + e[0]) / 2, BACK, (p[1] + e[1]) / 2), rot_y=-math.atan2(dz, dx))
    bpy.ops.mesh.primitive_cone_add(radius1=head * 0.45, depth=head,
                                    location=(q[0] - ux * head / 2, BACK, q[1] - uz * head / 2))
    c = bpy.context.object
    c.rotation_euler = (0, math.atan2(dx, dz), 0)
    c.color = color + (1,)


# bodies (same outlines as the question figure)
c2, c1 = H2 * COS / SIN, H1 * COS / SIN
m2 = prism("m2", [(0, 0), (-c2, H2), (-c2 - 1.3, H2), (-c2 - 1.3, 0)], SAND)
m1 = prism("m1", [(0, 0), (0.45, 0), (0.45, H1), (-c1, H1)], SAND)
L2 = label("m", "2", (-c2 - 0.7, 0.5), 0.55, INSIDE)
L1 = label("m", "1", (0.17, 0.2), 0.27, INSIDE)
for L, body in ((L2, m2), (L1, m1)):
    L.parent = body
th2 = text("θ", (-0.55, 0.12), 0.26, INSIDE)        # angle at m2's ramp foot
th2.parent = m2
th1 = text("θ", (-c1 + 0.42, H1 - 0.12), 0.22, INSIDE)  # matching angle on m1
th1.parent = m1

# velocity arrows (yellow), starting on top of their body: root -> scaled shaft + head
ARROW_K = 1.3 / (5 * v)


def make_arrow(name):
    root = bpy.data.objects.new(name, None)
    sc.collection.objects.link(root)
    pivot = bpy.data.objects.new(name + "_pivot", None)
    sc.collection.objects.link(pivot)
    pivot.parent = root
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.5, 0, 0))
    shaft = bpy.context.object
    shaft.scale = (1, 0.02, 0.035)
    bpy.ops.object.transform_apply(location=True, scale=True)
    shaft.color = VEL + (1,)
    shaft.parent = pivot
    bpy.ops.mesh.primitive_cone_add(radius1=0.075, depth=0.16, vertices=16)
    head = bpy.context.object
    head.rotation_euler = (0, math.radians(90), 0)
    head.color = VEL + (1,)
    head.parent = root
    return root, pivot, head


arr1, arr2 = make_arrow("v1"), make_arrow("v2")
lab1 = label("v", "1", (0, 0), 0.34, VEL)
lab2 = label("v", "2", (0, 0), 0.34, VEL)


def key_arrow(parts, lab, origin, vx, vz, f):
    root, pivot, head = parts
    L = max(math.hypot(vx, vz) * ARROW_K, 0.001)
    ang = math.atan2(vz, vx)
    root.location = (origin[0], FRONT + 0.1, origin[1])
    root.rotation_euler = (0, -ang, 0)
    pivot.scale = (max(L - 0.15, 0.001), 1, 1)
    head.location = (L - 0.08, 0, 0)
    lab.location = (origin[0] + 0.5 * L * math.cos(ang) - 0.28 * math.sin(ang), FRONT,
                    origin[1] + 0.5 * L * math.sin(ang) + 0.28 * math.cos(ang))
    for o, p in ((root, "location"), (root, "rotation_euler"), (pivot, "scale"),
                 (head, "location"), (lab, "location")):
        o.keyframe_insert(p, frame=f)


xs = []
for f in range(1, N_FRAMES + 1):
    t = (f - 1) / (FPS * SLOW)
    X2, x1, z1, (v1x, v1z), v2x, _ = state(t)
    m2.location = (X2, 0, 0)
    m2.keyframe_insert("location", frame=f)
    m1.location = (x1, 0, z1)
    m1.keyframe_insert("location", frame=f)
    key_arrow(arr2, lab2, (X2 - c2 - 0.65, H2 + 0.08), v2x, 0, f)
    key_arrow(arr1, lab1, (x1 + 0.1, z1 + H1 + 0.08), v1x, v1z, f)
    xs += [X2 - c2 - 1.3, x1 + 0.45 + max(v1x, 0) * ARROW_K + 0.3]

# frame the whole motion (orthographic front view, like the question figure)
xmin, xmax = min(xs) - 0.4, max(xs) + 0.4
cx, width = (xmin + xmax) / 2, xmax - xmin
cz = 1.0
half_h = width * 9 / 16 / 2
cam_d = bpy.data.cameras.new("cam")
cam_d.type, cam_d.ortho_scale = "ORTHO", width
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
cam.location = (cx, -10, cz)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.camera = cam

# floor with hatching (structure grey), axes (green, behind)
box("floor", (60, 0.3, 0.03), STRUCT, (cx, 0, -0.015))
for i in range(int(width / 0.25) + 2):
    hx = xmin + i * 0.25
    box("hatch", (0.18, 0.01, 0.015), STRUCT, (hx, BACK, -0.08), rot_y=math.radians(55))
ax0 = (xmax - 1.6, cz + half_h - 2.1)
arrow_static(ax0, (ax0[0] + 0.6, ax0[1]), AXES)
arrow_static(ax0, (ax0[0], ax0[1] + 0.6), AXES)
text("x", (ax0[0] + 0.78, ax0[1] - 0.05), 0.4, AXES)
text("y", (ax0[0] - 0.16, ax0[1] + 0.66), 0.4, AXES)

# live text: stage caption (top) and readouts (bottom), helper colour
caption = text("", (cx, cz + half_h - 0.5), 0.5)
readout = text("", (xmin + 0.3, cz - half_h + 0.75), 0.36, align="LEFT")
text(f"slow motion x{SLOW}", (xmax - 0.3, cz - half_h + 0.45), 0.3, align="RIGHT")


def update(scene, *_):
    t = (scene.frame_current - 1) / (FPS * SLOW)
    X2, x1, z1, (v1x, v1z), v2x, phase = state(t)
    caption.data.body = CAPTIONS[phase]
    ke = 0.5 * (v1x ** 2 + v1z ** 2) + 1.5 * v2x ** 2
    pe = g * z1
    readout.data.body = (
        f"v1 = ({v1x / v:+.2f}, {v1z / v:+.2f}) v        v2 = {v2x / v:+.2f} v\n"
        f"p_x = {(v1x + 3 * v2x) / v:.2f} mv        E = {(ke + pe) / v ** 2:.2f} mv²"
        f"  (kinetic {ke / v ** 2:.1f} + potential {pe / v ** 2:.1f})")


bpy.app.handlers.frame_change_pre.append(update)
update(sc)

f_top = int((T_CONTACT + T_RIDE / 2) * SLOW * FPS) + 1
print(f"v = {v:.3f} m/s, U = {U:.3f}, a = {A:.3f}, frames = {N_FRAMES}, top at frame {f_top}")
physkit.finish(sc, "wedge_ramp_q2", args, style="question", still_frame=f_top)
