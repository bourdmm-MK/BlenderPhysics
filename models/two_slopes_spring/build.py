"""Exam question: two blocks (m, 2m) slide down frictionless 60 deg slopes, are
released at different times so they hit m3 = 3m (resting on a spring,
k = 72 mg/h) at the same moment. Plastic collision -> the 6m body oscillates.

Everything moves from the real equations (no hand-placed keyframes):
slide with a = g sin(theta), impact speeds sqrt(2 g y), vertical momentum
gives U, then y(t) = y0 (1 - cos wt) - (U/w) sin wt with w = sqrt(k / 6m).
The slopes end at m3, so horizontal momenta cancel when y2 = h/4.

Drawn in the shared course style (physkit.style; PhysicsAid knowledge/visual-style.md).
A Manim twin of this scene lives in PhysicsAid:
expermients/two_slopes_spring/two_slopes_spring_manim.py

Run:  .\tools\run.ps1 two_slopes_spring -mode preview -still   (impact frame)
      .\tools\run.ps1 two_slopes_spring -mode preview          (video, ~30 s)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import bpy  # noqa: E402

import physkit  # noqa: E402
from physkit.style import COURSE, label_font  # noqa: E402
# ---------------- physics ----------------
g, h, m = 9.81, 1.0, 1.0
theta = math.radians(60)
k = 72 * m * g / h
yb = 0.0                 # height of the slope bottoms above the collision point (0 = slopes end at m3, as in the exam answer y2 = h/4)
# Horizontal momentum must cancel: m*vb1 = 2m*vb2  ->  (h-yb) = 4 (y2-yb)
y2 = yb + (h - yb) / 4
SLOW = 3.0               # slow motion factor (video seconds per real second)
FPS = 24
T_AFTER = 2.5            # real seconds shown after the collision
T_WAIT = 0.25            # real seconds before m1 is released

# block sizes (visual only, bigger = heavier)
b1, b2, b3 = 0.11, 0.14, 0.20


def path_params(y_start):
    """Return (t_slide, t_fly, vb, dx_fly) for a block released at height y_start."""
    L = (y_start - yb) / math.sin(theta)
    a = g * math.sin(theta)
    t_slide = math.sqrt(2 * L / a)
    vb = a * t_slide
    vy0 = vb * math.sin(theta)
    # yb = vy0 t + g t^2/2
    t_fly = (-vy0 + math.sqrt(vy0**2 + 2 * g * yb)) / g
    dx = vb * math.cos(theta) * t_fly
    return t_slide, t_fly, vb, dx


p1 = path_params(h)
p2 = path_params(y2)
T1 = p1[0] + p1[1]
T2 = p2[0] + p2[1]
t_col = T_WAIT + max(T1, T2)
t_rel1 = t_col - T1
t_rel2 = t_col - T2

# impact velocities (vertical parts add, horizontal parts cancel)
v1y = math.sqrt((p1[2] * math.sin(theta))**2 + 2 * g * yb)
v2y = math.sqrt((p2[2] * math.sin(theta))**2 + 2 * g * yb)
U = (m * v1y + 2 * m * v2y) / (6 * m)
w = math.sqrt(k / (6 * m))
y0 = -3 * m * g / k      # new equilibrium shift (= -h/24)

# collision points (centre of each small block at impact): at m3's top corners
xc1 = -(b3 / 2)
xc2 = +(b3 / 2)
zc1 = 0.5 * b1
zc2 = 0.5 * b2
m3_top0 = 0.0            # m3 top surface at the collision moment
m3_c0 = m3_top0 - b3 / 2

L0 = 0.45                                  # spring natural length
L_eq3 = L0 - 3 * m * g / k                 # length with m3 resting on it
floor_z = m3_c0 - b3 / 2 - L_eq3

print(f"y2 = {y2:.3f} h   (exam answer with no gap: h/4)")
print(f"v1 = {math.hypot(v1y, p1[2]*math.cos(theta)):.2f}, v2 = {math.hypot(v2y, p2[2]*math.cos(theta)):.2f} m/s")
print(f"U = {U:.3f} m/s, omega = {w:.2f} rad/s, y0 = {y0:.4f}")


def block_pos(t, t_rel, p, side, xc, zc, y_start):
    """Centre path of a sliding/flying block (side = -1 left slope, +1 right slope)."""
    t_slide, t_fly, vb, dx = p
    x_bot = xc + side * dx
    z_bot = zc + yb
    dirx = -side * math.cos(theta)    # travel direction along slope
    dirz = -math.sin(theta)
    L = (y_start - yb) / math.sin(theta)
    x_top = x_bot - dirx * L
    z_top = z_bot - dirz * L
    tau = t - t_rel
    if tau <= 0:
        return x_top, z_top
    if tau <= t_slide:
        s = 0.5 * g * math.sin(theta) * tau**2
        return x_top + dirx * s, z_top + dirz * s
    if tau <= t_slide + t_fly:
        tf = tau - t_slide
        return (x_bot + dirx * vb * tf,
                z_bot + dirz * vb * tf - 0.5 * g * tf**2)
    return None


def y_after(t):
    """Displacement of the 6m body after the collision (t from impact)."""
    return y0 * (1 - math.cos(w * t)) - (U / w) * math.sin(w * t)


# ---------------- scene (course style: flat colours on black) ----------------
args = physkit.parse_args("Two slopes + spring exam question")
sc = physkit.new_scene(fps=FPS)
def box(name, size, color, loc=(0, 0, 0), rot_y=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.rotation_euler = (0, rot_y, 0)
    o.color = color + (1,)
    return o


SAND = COURSE["body"]
DARK = COURSE["aux"]         # helper text, dashed lines
STRUCT = COURSE["structure"]  # slopes, floor, spring
AXES = COURSE["axes"]
INSIDE = COURSE["body_text"]  # labels inside bodies (project rule)
m1 = box("m1", (b1, b1, b1), SAND)
m2 = box("m2", (b2, b2, b2), SAND)
m3 = box("m3", (b3, b3, b3), SAND)

# slopes: thin boards under each block path
for name, p, side, xc, zc, ys, bs in (("slope1", p1, -1, xc1, zc1, h, b1),
                                      ("slope2", p2, +1, xc2, zc2, y2, b2)):
    t_slide, t_fly, vb, dx = p
    x_bot = xc + side * dx
    z_bot = zc + yb
    L = (ys - yb) / math.sin(theta)
    dirx, dirz = -side * math.cos(theta), -math.sin(theta)
    nx, nz = -side * math.sin(theta), math.cos(theta)    # outward normal (up)
    # block centre sits b/2 above the board surface
    cx = x_bot - dirx * L / 2 - nx * (bs / 2 + 0.01)
    cz = z_bot - dirz * L / 2 - nz * (bs / 2 + 0.01)
    ang = math.atan2(dirz, dirx)
    box(name, (L + bs, 0.15, 0.02), STRUCT, (cx, 0, cz), rot_y=-ang)

# floor
box("floor", (0.8, 0.3, 0.03), STRUCT, (0, 0, floor_z - 0.015))

# spring: helix curve from z=0 to z=1, scaled in z to the current length
cu = bpy.data.curves.new("spring", "CURVE")
cu.dimensions = "3D"
cu.bevel_depth = 0.006
sp = cu.splines.new("POLY")
turns, n_pts, R = 9, 9 * 24, 0.04
sp.points.add(n_pts)
for i in range(n_pts + 1):
    u = i / n_pts
    a = 2 * math.pi * turns * u
    sp.points[i].co = (R * math.cos(a), R * math.sin(a), u, 1)
spring = bpy.data.objects.new("spring", cu)
spring.color = STRUCT + (1,)
sc.collection.objects.link(spring)
spring.location = (0, 0, floor_z)

# camera
cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = 3.5
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
cam.location = (0, -5, 0.27)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.camera = cam

# ---------------- animation (one keyframe per frame) ----------------
t_end = t_col + T_AFTER
n_frames = int(t_end * SLOW * FPS) + 1
sc.frame_start, sc.frame_end = 1, n_frames

ang1 = -math.atan2(-math.sin(theta), math.cos(theta))
ang2 = -math.atan2(-math.sin(theta), -math.cos(theta)) + math.pi


def set_key(o, loc, rot=None, f=1):
    o.location = loc
    o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = (0, rot, 0)
        o.keyframe_insert("rotation_euler", frame=f)


# ---------------- labels, axes, dashed lines ----------------
FONT = label_font()
RED = COURSE["force"]
FRONT = -0.3            # y-position in front of the blocks (camera is at -y): text
BACK = 0.3              # behind the blocks: axes, dashed lines, arrows


def text(body, loc, size=0.1, color=DARK, align="CENTER"):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = body
    cu.font = FONT
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    o = bpy.data.objects.new("txt_" + body, cu)
    sc.collection.objects.link(o)
    o.location = (loc[0], FRONT, loc[1])
    o.rotation_euler = (math.radians(90), 0, 0)
    o.color = color + (1,)
    return o


def label(main, sub, loc, size=0.1, color=DARK):
    """Text like m_1: a main letter plus a smaller subscript, moved together."""
    o = text(main, loc, size, color)
    if sub:
        s = text(sub, (0, 0), size * 0.6, color)
        s.parent = o
        s.rotation_euler = (0, 0, 0)
        s.location = (size * 0.42, -size * 0.25, 0)   # in the text's own plane
    return o


def seg(p, q, width=0.006, color=DARK):
    dx, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dz)
    return box("seg", (L, 0.005, width), color,
               ((p[0] + q[0]) / 2, BACK, (p[1] + q[1]) / 2),
               rot_y=-math.atan2(dz, dx))


def dashed(p, q, dash=0.03, gap_=0.02, color=DARK):
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uz = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    s = 0.0
    while s < L:
        e = min(s + dash, L)
        seg((p[0] + ux * s, p[1] + uz * s), (p[0] + ux * e, p[1] + uz * e), 0.004, color)
        s += dash + gap_


def arrow(p, q, color=DARK, width=0.008, head=0.045):
    dx, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    seg(p, (q[0] - ux * head, q[1] - uz * head), width, color)
    bpy.ops.mesh.primitive_cone_add(radius1=head * 0.45, depth=head,
                                    location=(q[0] - ux * head / 2, BACK, q[1] - uz * head / 2))
    c = bpy.context.object
    c.rotation_euler = (0, math.atan2(dx, dz), 0)   # cone points along +z by default
    c.color = color + (1,)


# axes through m3's starting centre (as in the question's drawing)
ox, oz = 0.0, m3_c0
arrow((-0.75, oz), (0.75, oz), AXES)
arrow((ox, floor_z + 0.02), (ox, h + 0.2), AXES)
text("x", (0.78, oz - 0.07), color=AXES)
text("y", (-0.07, h + 0.17), color=AXES)

# start heights y1, y2 (measured from the impact level) + slope-bottom line
s1 = block_pos(0, 1, p1, -1, xc1, zc1, h)
s2 = block_pos(0, 1, p2, +1, xc2, zc2, y2)
z_y1 = zc1 + h
z_y2 = zc2 + y2
dashed((0, z_y1), (s1[0], z_y1))
dashed((0, z_y2), (s2[0], z_y2))
label("y", "1", (0.11, z_y1 - 0.06))
label("y", "2", (-0.1, z_y2 + 0.06))
z_bot = 0.5 * (zc1 + zc2) + yb - 0.05
dashed((-0.6, z_bot), (0.6, z_bot))
# theta labels at the bottom of each slope (angle between slope and horizontal)
x_b1 = xc1 - p1[3]
x_b2 = xc2 + p2[3]
text("θ", (x_b1 - 0.36, z_bot + 0.05), 0.09)
text("θ", (x_b2 + 0.36, z_bot + 0.05), 0.09)
# gravity and spring constant
arrow((1.0, 0.85), (1.0, 0.55), RED, 0.01, 0.05)
text("g", (0.91, 0.70), 0.11, RED)
text("k", (-0.14, 0.5 * (floor_z + m3_c0 - b3 / 2)), 0.11)

# moving labels for the three masses
L1 = label("m", "1", (0, 0), 0.07, INSIDE)
L2 = label("m", "2", (0, 0), 0.085, INSIDE)
L3 = label("m", "3", (0, 0), 0.1, INSIDE)
# mass labels sit INSIDE their blocks (project rule); small shift left for the subscript
OFF1, OFF2, OFF3 = (-0.01, 0.0), (-0.012, 0.0), (-0.016, 0.0)


def key_label(L, x, z, off, f):
    L.location = (x + off[0], FRONT, z + off[1])
    L.keyframe_insert("location", frame=f)


for f in range(1, n_frames + 1):
    t = (f - 1) / (FPS * SLOW)
    if t < t_col:
        dz = 0.0
        for o, t_rel, p, side, xc, zc, ys, bs, ang in (
                (m1, t_rel1, p1, -1, xc1, zc1, h, b1, ang1),
                (m2, t_rel2, p2, +1, xc2, zc2, y2, b2, ang2)):
            pos = block_pos(t, t_rel, p, side, xc, zc, ys)
            set_key(o, (pos[0], 0, pos[1]), ang, f)
    else:
        dz = y_after(t - t_col)
        set_key(m1, (xc1, 0, zc1 + dz), ang1, f)
        set_key(m2, (xc2, 0, zc2 + dz), ang2, f)
    set_key(m3, (0, 0, m3_c0 + dz), None, f)
    key_label(L1, m1.location.x, m1.location.z, OFF1, f)
    key_label(L2, m2.location.x, m2.location.z, OFF2, f)
    key_label(L3, 0, m3_c0 + dz, OFF3, f)
    spring.scale = (1, 1, (m3_c0 - b3 / 2 + dz) - floor_z)
    spring.keyframe_insert("scale", frame=f)

f_col = int(t_col * SLOW * FPS) + 1
print(f"frames: {n_frames}, collision at frame {f_col}")
physkit.finish(sc, "two_slopes_spring", args, style="question", still_frame=f_col)
