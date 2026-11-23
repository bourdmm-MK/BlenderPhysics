"""Colliding blocks count pi.

A small block (m = 1 kg) rests between a wall and a big block (M) that slides
towards it at 1 m/s. Every collision is perfectly elastic and there is no
friction. Counting all the collisions (block-block and block-wall) gives

    M/m = 1      ->  3 collisions
    M/m = 10^2   ->  31
    M/m = 10^4   ->  314
    ...          ->  the first digits of pi.

The video runs the system for M/m = 100^n, n = 0 ... N_STAGES-1, one after the
other. The graph of how far N / 10^n is from pi (in percent, log scale: each
step down is 10x closer) is always on screen and fills in after each run.

Physics: exact event-by-event simulation (no time step): between collisions
the blocks move at constant speed; each collision uses the elastic-collision
formulas (momentum + kinetic energy conserved); the wall reverses the small
block's velocity. Positions in each video frame are read from that solution.

Sound: one short "tock" per collision. When the collisions come faster than the
ear can separate (hundreds per second) the sound turns into a tone whose pitch
follows the collision rate, and a bell note rings as each new graph point lands.

Run:  .\\tools\\run.ps1 collision_pi -mode preview -still
      .\\tools\\run.ps1 collision_pi -mode preview     (video with sound, ~1 min)
"""
import math
import sys
import wave
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import physkit  # noqa: E402
from physkit.latex import manim_em, number, tex  # noqa: E402
from physkit.render import OUTPUT_ROOT  # noqa: E402
from physkit.style import COURSE  # noqa: E402

NAME = "collision_pi"

# ---------------- physics (SI units) ----------------
M_SMALL = 1.0              # kg
RATIO_BASE = 100.0         # M/m = RATIO_BASE**n
N_STAGES = 7               # n = 0..6  ->  up to 3 141 592 collisions
V_BIG = -1.0               # m/s, big block's starting velocity (towards the wall)
SMALL_SIDE = 0.30          # m
SMALL_START = 0.60         # m, small block's left face (wall face at x = 0)
BIG_START = 1.90           # m, big block's left face

# ---------------- timing ----------------
FPS = 24
T_INTRO = 0.8              # s, blocks shown at rest before each run
T_MAX_RUN = 9.0            # s, longest run (video time)
X_EXIT = 4.4               # m, run ends once the big block's left face passes this
T_AFTER = 0.7              # s, after the last collision before the run may end
T_OUTRO = 4.0              # s, final hold with the full graph
T_BURST = 2.0              # s of video over which a big pile-up of collisions is spread


def big_side(n):
    return 0.45 + 0.10 * n


def simulate(ratio, n_frames, rate_cap):
    """Exact elastic-collision solution, sampled in video time.

    Slow motion: every collision adds 1/rate_cap seconds of video, so video time
    is tau = t + (collisions so far) / rate_cap and the screen never shows more
    than about rate_cap collisions per second. Where collisions are rare this is
    real time.

    Returns (frames, hits): frames[i] = (x_small, x_big, count, t_physical) at
    video time i/FPS (left faces, metres); hits = video times of all collisions.
    """
    m, M = M_SMALL, M_SMALL * ratio
    w = SMALL_SIDE
    t, s, L = 0.0, SMALL_START, BIG_START - w   # L = room for the small block's left face
    vs, vb = 0.0, V_BIG
    count = 0
    hits = array("d")
    frames = []
    fi = 0
    while fi < n_frames:
        dt = math.inf
        kind = None
        if vs < 0:
            dt, kind = -s / vs, "wall"
        rel = vb - vs
        if rel < 0 and (L - s) / -rel < dt:
            dt, kind = (L - s) / -rel, "block"
        # frames that fall before the next collision (in video time)
        t_next = t + dt
        lag = count / rate_cap
        while fi < n_frames and fi / FPS <= t_next + lag:
            tau = max(0.0, fi / FPS - lag - t)
            frames.append((max(0.0, s + vs * tau), L + vb * tau + w, count, t + tau))
            fi += 1
        if kind is None:
            continue
        t, s, L = t_next, s + vs * dt, L + vb * dt
        if kind == "wall":
            s, vs = 0.0, -vs
        else:
            s = L
            vs, vb = ((m - M) * vs + 2 * M * vb) / (m + M), ((M - m) * vb + 2 * m * vs) / (m + M)
        count += 1
        hits.append(t + lag)
    return frames, hits


def run_length(frames, hits):
    """Seconds of video the run lasts."""
    t_last = hits[-1] if hits else 0.0
    t_exit = next((i / FPS for i, f in enumerate(frames) if f[1] > X_EXIT), T_MAX_RUN)
    return min(T_MAX_RUN, max(t_last + T_AFTER, t_exit))


print("[collision_pi] simulating ...")
STAGES = []
t0 = 0.0
for n in range(N_STAGES):
    rate_cap = max(40.0, math.pi * 10 ** n / T_BURST)   # collisions per video second
    frames, hits = simulate(RATIO_BASE ** n, int(T_MAX_RUN * FPS) + 2, rate_cap)
    T_run = run_length(frames, hits)
    STAGES.append(dict(n=n, frames=frames, hits=hits, count=len(hits),
                       start=t0, run_start=t0 + T_INTRO, run=T_run))
    print(f"   M/m = 100^{n}: {len(hits)} collisions, run {T_run:.2f} s")
    t0 += T_INTRO + T_run
T_TOTAL = t0 + T_OUTRO

# ---------------- scene ----------------
args = physkit.parse_args("Colliding blocks count pi")
sc = physkit.new_scene(fps=FPS)
physkit.set_frames(sc, T_TOTAL)
F_END = sc.frame_end


def frame_of(t):
    return 1 + round(t * FPS)


def box(name, size, center, color):
    hx, hy, hz = (c / 2 for c in size)
    verts = [(sx * hx, sy * hy, sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = center
    o.color = tuple(color) + (1,)
    return o


STRUCT = COURSE["structure"]
BODY = COURSE["body"]
DEPTH = 1.6                     # floor depth (m)
# floor (top at z = 0) and wall (face at x = 0), with hatch marks outside
box("floor", (7.6, DEPTH, 0.04), (3.6, 0, -0.02), STRUCT)
box("wall", (0.06, DEPTH, 1.9), (-0.03, 0, 0.95), STRUCT)
for i in range(13):
    z = 0.08 + i * 0.145
    h = box(f"hatch_w{i}", (0.15, 0.012, 0.012), (-0.10, -DEPTH / 2 - 0.006, z - 0.05), STRUCT)
    h.rotation_euler = (0, math.radians(-45), 0)

# blocks (sand fill, black LaTeX label on the front face)
def labelled_block(name, side, label):
    b = box(name, (side, side, side), (0, 0, side / 2), BODY)
    em = 0.32 * side
    lab = tex(label, em, COURSE["body_text"], name=f"{name}_label")
    if lab.dimensions.x > 0.82 * side:
        lab.scale *= 0.82 * side / lab.dimensions.x
    lab.parent = b
    lab.location = (0, -side / 2 - 0.003, 0)
    return b


small = labelled_block("small", SMALL_SIDE, r"1\,\mathrm{kg}")
bigs = []
for n in range(N_STAGES):
    lbl = r"1\,\mathrm{kg}" if n == 0 else rf"10^{{{2 * n}}}\,\mathrm{{kg}}"
    bigs.append(labelled_block(f"big_{n}", big_side(n), lbl))

AWAY = (0, 0, -60)
def key_loc(o, loc, f):
    o.location = loc
    o.keyframe_insert("location", frame=f)


for n, b in enumerate(bigs):
    st = STAGES[n]
    if n > 0:
        key_loc(b, AWAY, 1)
    nxt = STAGES[n + 1]["start"] if n + 1 < N_STAGES else T_TOTAL + 1
    f_a, f_b = frame_of(st["start"]), frame_of(nxt)
    side = big_side(n)
    for f in range(f_a, min(f_b, F_END + 1)):
        i = min(max(0, f - frame_of(st["run_start"])), len(st["frames"]) - 1)
        xs, xb = st["frames"][i][:2]
        key_loc(b, (xb + side / 2, 0, side / 2), f)
        key_loc(small, (xs + SMALL_SIDE / 2, 0, SMALL_SIDE / 2), f)
    if n + 1 < N_STAGES:
        key_loc(b, AWAY, f_b)

# ---------------- camera (slow drift so the 3D shows) ----------------
REEL = args.reel           # vertical 9:16 frame for reels
cam_data = bpy.data.cameras.new("Camera")
cam_data.sensor_fit = "HORIZONTAL"     # lens/angle refer to the frame width in both formats
cam_data.lens = 26 if REEL else 35
cam = bpy.data.objects.new("Camera", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
# reel: look well above the blocks so they sit in the lower part of the tall frame
LOOK = Vector((2.7, 0.0, 3.9)) if REEL else Vector((3.0, 0.0, 1.75))
for f in range(1, F_END + 1):
    u = (f - 1) / max(1, F_END - 1)
    e = 0.5 - 0.5 * math.cos(math.pi * u)
    pos = (Vector((3.5 - 1.2 * e, -7.2, 2.0 + 0.3 * e)) if REEL
           else Vector((4.6 - 1.6 * e, -8.6, 3.0 + 0.4 * e)))
    cam.location = pos
    cam.rotation_euler = (LOOK - pos).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)

# ---------------- HUD: text and graph, fixed in front of the camera ----------------
HUD_W_WIDE = 2 * 4.0 * math.tan(math.atan(18 / 35))  # landscape HUD width: text sizes refer to it
HUD_W = 2.7 if REEL else HUD_W_WIDE                    # visible HUD width (HUD metres)
HUD_D = HUD_W / (2 * math.tan(cam_data.angle / 2))     # distance in front of the camera
EM = lambda fs: manim_em(fs, HUD_W_WIDE)               # noqa: E731
hud = []


def hud_obj(o, x, y, rot0=True):
    o.location = (x, y, -HUD_D)
    if rot0:
        o.rotation_euler = (0, 0, 0)
    hud.append(o)
    return o


def hud_tex(body, fs, color, x, y, align="LEFT", name="hudtex", math_mode=True):
    o = tex(body, EM(fs), color, math_mode=math_mode, name=name)
    if align == "LEFT":
        x += o.dimensions.x / 2
    elif align == "RIGHT":
        x -= o.dimensions.x / 2
    return hud_obj(o, x, y)


def hud_mesh(name, verts, faces, color):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(*v, 0.0) for v in verts], [], faces)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.color = tuple(color) + (1,)
    hud.append(o)
    return o


def hud_seg(name, p, q, width, color, z=-HUD_D):
    (x1, y1), (x2, y2) = p, q
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln * width / 2, dx / ln * width / 2
    o = hud_mesh(name, [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)],
                 [(0, 1, 2, 3)], color)
    o.location = (0, 0, z)
    return o


def hud_arrow(name, p, q, color, width=0.008, head=0.05):
    (x1, y1), (x2, y2) = p, q
    ln = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
    bx, by = x2 - ux * head, y2 - uy * head
    hud_seg(name, p, (bx, by), width, color)
    o = hud_mesh(name + "_head", [(x2, y2), (bx - uy * head * 0.45, by + ux * head * 0.45),
                                  (bx + uy * head * 0.45, by - ux * head * 0.45)], [(0, 1, 2)], color)
    o.location = (0, 0, -HUD_D)


def hud_disc(name, x, y, r, color):
    k = 24
    o = hud_mesh(name, [(r * math.cos(2 * math.pi * i / k), r * math.sin(2 * math.pi * i / k)) for i in range(k)],
                 [tuple(range(k))], color)
    o.location = (x, y, -HUD_D + 0.002)
    return o


AXES, AUX, WHITE = COURSE["axes"], COURSE["aux"], COURSE["time"]
OFF = COURSE["displacement"]     # orange: the distance from the goal (pi)
HALF_W = HUD_W / 2
HALF_H = HUD_W * (16 / 18 if REEL else 9 / 32)

# layout anchors: (landscape) readouts top-left, graph right, blocks below;
# (reel) title, readouts, full-width graph, blocks, all kept out of the reel's
# top bar, right-hand buttons and bottom caption area
if REEL:
    LX = -HALF_W + 0.15
    ROW = [1.40, 1.18, 1.00, 0.83]                 # collisions, pi, estimate, off by
    STAGE_POS = (HALF_W - 0.15, ROW[0], "RIGHT")   # M/m on the counter's line
    GX0, GY0 = -HALF_W + 0.55, -0.32
    SLOW_POS = (LX + 0.80, -0.62)        # over the empty space right of the wall
    hud_tex(r"\text{Counting collisions gives }\pi", 42, WHITE, 0, 1.72, align="CENTER", name="title")
else:
    LX, TOP = -HALF_W + 0.18, HALF_H - 0.20
    ROW = [TOP - 0.24, TOP - 0.44, TOP - 0.61, TOP - 0.78]
    STAGE_POS = (LX, TOP, "LEFT")
    GX0, GY0 = 0.12, -0.08
    SLOW_POS = (GX0, GY0 - 0.30)

# --- left: mass ratio, live counter, pi, result of the last run
stage_labels = []
for n in range(N_STAGES):
    body = r"\frac{M}{m} = 1" if n == 0 else rf"\frac{{M}}{{m}} = 10^{{{2 * n}}}"
    stage_labels.append(hud_tex(body, 34, WHITE, STAGE_POS[0], STAGE_POS[1], align=STAGE_POS[2], name=f"stage_{n}"))
hud_tex(r"\text{Collisions:}", 34, AUX, LX, ROW[0], name="lbl_collisions")
counter = number("0", EM(44), WHITE, name="counter")
hud_obj(counter, LX + 0.58, ROW[0])
hud_tex(r"\pi = 3.14159265\ldots", 30, AUX, LX, ROW[1], name="lbl_pi")


def error_pct(n):
    """How far N/10^n is from pi, in percent of pi."""
    return abs(STAGES[n]["count"] / 10 ** n - math.pi) / math.pi * 100


def pct_text(e):
    """Two significant figures, plain decimals (no 1e-5 notation)."""
    return f"{e:.{max(0, 1 - math.floor(math.log10(e)))}f}"


# the result of each run: the estimate and how far it is from pi
est_labels, off_labels = [], []
for n, st in enumerate(STAGES):
    est = f"{st['count'] / 10 ** n:.{n}f}"
    est_labels.append(hud_tex(rf"\text{{estimate}} = {est}", 30, WHITE, LX, ROW[2], name=f"est_{n}"))
    off_labels.append(hud_tex(rf"\text{{off by }} {pct_text(error_pct(n))}\,\%", 30, OFF, LX,
                              ROW[3], name=f"off_{n}"))

# --- right: graph of the distance from pi (percent, log scale) against M/m
GW, GH = (1.60, 0.95) if REEL else (1.73, 1.10)     # axes size (HUD metres)
DEC_TOP, DEC_BOT = 1, -5               # 10 % ... 0.00001 %


def gx(n):
    return GX0 + 0.16 + n * (GW - 0.32) / (N_STAGES - 1)


def gy(err_pct):
    return GY0 + 0.07 + (math.log10(err_pct) - DEC_BOT) / (DEC_TOP - DEC_BOT) * (GH - 0.20)


hud_arrow("x_axis", (GX0, GY0), (GX0 + GW, GY0), AXES)
hud_arrow("y_axis", (GX0, GY0), (GX0, GY0 + GH), AXES)
for d in range(DEC_BOT, DEC_TOP + 1):
    y = gy(10.0 ** d)
    hud_seg(f"ytick{d}", (GX0 - 0.025, y), (GX0 + 0.025, y), 0.006, AXES)
    lab = "1" if d == 0 else (f"{10 ** d}" if d > 0 else f"0.{'0' * (-d - 1)}1")
    hud_tex(rf"{lab}\,\%", 20, AUX, GX0 - 0.05, y, align="RIGHT", name=f"ylab{d}")
for n in range(N_STAGES):
    hud_seg(f"xtick{n}", (gx(n), GY0 - 0.025), (gx(n), GY0 + 0.025), 0.006, AXES)
    hud_tex("1" if n == 0 else f"10^{{{2 * n}}}", 20, AUX, gx(n), GY0 - 0.08, align="CENTER", name=f"xlab{n}")
hud_tex(r"M/m", 26, AUX, GX0 + GW, GY0 - 0.17, align="RIGHT", name="x_name")
hud_tex(r"\text{off from }\pi\quad(\text{lower} = \text{closer})", 24, AUX, GX0 + 0.06, GY0 + GH + 0.03,
        name="y_name")

slow = number("", EM(28), COURSE["velocity"], name="slow_motion")
hud_obj(slow, *SLOW_POS)

points, links, values = [], [], []
for n, st in enumerate(STAGES):
    e = error_pct(n)
    p = hud_disc(f"point_{n}", gx(n), gy(e), 0.022, OFF)
    points.append(p)
    if n:
        links.append(hud_seg(f"link_{n}", (gx(n - 1), gy(error_pct(n - 1))), (gx(n), gy(e)), 0.006, OFF,
                             z=-HUD_D + 0.001))
    else:
        links.append(None)
    val = hud_tex(rf"{pct_text(e)}\,\%", 20, OFF, gx(n) + 0.03, gy(e) + 0.06, align="LEFT", name=f"value_{n}")
    values.append(val)

for o in hud:
    o.parent = cam
    o.matrix_parent_inverse.identity()


def pop(o, f_on, f_off=None, full=None):
    """Scale an object from 0 to full over 5 frames at f_on (and back to 0 at f_off)."""
    full = tuple(o.scale) if full is None else full
    o.scale = (0, 0, 0)
    o.keyframe_insert("scale", frame=1)
    for k, a in enumerate((0.3, 0.7, 1.12, 1.0)):
        o.scale = tuple(c * a for c in full)
        o.keyframe_insert("scale", frame=f_on + k)
    if f_off is not None:
        o.scale = (0, 0, 0)
        o.keyframe_insert("scale", frame=f_off)


for n, st in enumerate(STAGES):
    f_done = frame_of(st["run_start"] + st["run"]) - 2
    for o in (points[n], links[n], values[n]):
        if o is not None:
            pop(o, f_done)
    f_off = frame_of(STAGES[n + 1]["start"]) if n + 1 < N_STAGES else None
    pop(stage_labels[n], frame_of(st["start"]), f_off)
    f_next = frame_of(STAGES[n + 1]["run_start"] + STAGES[n + 1]["run"]) - 2 if n + 1 < N_STAGES else None
    pop(est_labels[n], f_done, f_next)
    pop(off_labels[n], f_done, f_next)

# live counter value per frame
counts_by_frame = [0] * (F_END + 2)
slow_by_frame = [1.0] * (F_END + 2)
for n, st in enumerate(STAGES):
    f_a = frame_of(st["start"])
    f_b = frame_of(STAGES[n + 1]["start"]) if n + 1 < N_STAGES else F_END + 1
    fr = st["frames"]
    for f in range(f_a, f_b):
        i = f - frame_of(st["run_start"])
        if i < 0:
            continue
        i = min(i, len(fr) - 1)
        counts_by_frame[f] = fr[i][2]
        # slow-motion factor = video time / physical time over +-2 frames
        j0, j1 = max(0, i - 2), min(len(fr) - 1, i + 2)
        dphys = fr[j1][3] - fr[j0][3]
        if j1 > j0:
            slow_by_frame[f] = (j1 - j0) / FPS / max(dphys, 1e-12)


def slow_text(k):
    if k < 1.5:
        return ""
    digits = 10 ** max(0, int(math.log10(k)) - 1)       # two significant figures
    return f"slow motion ×{round(k / digits) * digits:,}"


def update(scene, *_):
    f = min(max(scene.frame_current, 1), F_END)
    counter.data.body = f"{counts_by_frame[f]:,}"
    slow.data.body = slow_text(slow_by_frame[f])


bpy.app.handlers.frame_change_pre.append(update)


def fcurves(action):
    """All F-curves of an action (Blender 5 layered actions, or the old list)."""
    if hasattr(action, "layers") and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    yield from bag.fcurves
    else:
        yield from getattr(action, "fcurves", [])


# every key holds its value until the next one (positions are given for every frame;
# hidden things must not glide in); only the camera drifts smoothly
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action and ob is not cam:
        for fc in fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"

# ---------------- sound ----------------
SR = 44100


def make_sound(path):
    n_samp = int(T_TOTAL * SR) + SR
    imp = np.zeros(n_samp)
    for st in STAGES:
        idx = ((np.frombuffer(st["hits"], dtype=np.float64) + st["run_start"]) * SR).astype(np.int64)
        np.add.at(imp, idx[idx < n_samp], 1.0) if len(idx) < 50000 else \
            imp.__iadd__(np.bincount(idx[idx < n_samp], minlength=n_samp)[:n_samp])
    # collision rate (per second), smoothed over 25 ms
    win = int(0.025 * SR)
    rate = np.convolve(imp, np.ones(win) / win, mode="same") * SR
    # 1) the tock of each collision (wood-like: two decaying partials)
    kt = np.arange(int(0.03 * SR)) / SR
    tock = np.exp(-kt * 180) * (np.sin(2 * np.pi * 1900 * kt) + 0.6 * np.sin(2 * np.pi * 820 * kt))
    nfft = 1 << (n_samp + len(tock)).bit_length()
    clicks = np.fft.irfft(np.fft.rfft(imp, nfft) * np.fft.rfft(tock, nfft), nfft)[:n_samp]
    # limit dense bursts to a steady loudness
    env = np.sqrt(np.convolve(clicks ** 2, np.ones(win) / win, mode="same")) + 1e-9
    clicks *= np.minimum(1.0, 0.35 / env)
    # 2) when collisions come too fast to hear one by one: a tone that follows the rate
    lr = np.log10(np.maximum(rate, 1.0))
    wgt = np.clip((lr - 2.0) / 1.0, 0, 1)            # 100/s -> 0, 1000/s -> 1
    wgt = wgt * wgt * (3 - 2 * wgt)
    freq = 180.0 * np.clip(rate / 100.0, 1, None) ** 0.18
    freq = np.minimum(freq, 1400.0)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    tone = (np.sin(phase) + 0.35 * np.sin(2 * phase) + 0.15 * np.sin(3 * phase)) * 0.28 * wgt
    mix = clicks * (1 - 0.75 * wgt) + tone
    # 3) a bell note as each graph point lands (rising pentatonic), chord at the end
    notes = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.5, 1174.7]
    bt = np.arange(int(2.5 * SR)) / SR

    def bell(f0, amp):
        return amp * np.exp(-bt * 2.2) * (np.sin(2 * np.pi * f0 * bt) + 0.4 * np.sin(2 * np.pi * 2.76 * f0 * bt)
                                           * np.exp(-bt * 3) + 0.25 * np.sin(2 * np.pi * 5.4 * f0 * bt) * np.exp(-bt * 6))

    def add(sig, t):
        a = int(t * SR)
        b = min(n_samp, a + len(sig))
        mix[a:b] += sig[:b - a]

    for n, st in enumerate(STAGES):
        add(bell(notes[n % len(notes)], 0.22), st["run_start"] + st["run"] - 2 / FPS)
    t_end = STAGES[-1]["run_start"] + STAGES[-1]["run"] + 0.6
    for f0 in (523.25, 659.25, 783.99, 1046.5):
        add(bell(f0, 0.12), t_end)
    mix /= max(1e-9, np.abs(mix).max()) / 0.89
    pcm = (mix * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


out_dir = OUTPUT_ROOT / NAME
out_dir.mkdir(parents=True, exist_ok=True)
wav = out_dir / f"{NAME}_sound.wav"
if not args.still:
    print("[collision_pi] making sound ...")
    make_sound(wav)
if wav.exists():
    sc.sequence_editor_create()
    se = sc.sequence_editor
    strips = se.strips if hasattr(se, "strips") else se.sequences
    strips.new_sound("collisions", str(wav), 1, 1)

# still: the moment the 5-digit run is in full swing
st4 = STAGES[min(4, N_STAGES - 1)]
still = frame_of(st4["run_start"] + st4["hits"][len(st4["hits"]) // 2])
update(sc)


TAG = "_reel" if REEL else ""
SCENE_EXPOSURE = 0.7     # brightens the shaded 3D layer back towards the course colours


def render_two_layers(scene, still_frame):
    """Render the 3D scene (shaded) and the text/graph (flat, full colour) separately,
    then lay the text over the 3D picture with ffmpeg. One Workbench lighting for both
    would dim the text; this keeps the blocks solid-looking and the labels crisp.
    """
    import shutil
    import subprocess
    from physkit.render import configure_render
    from physkit.style import apply_question_style

    hud_set = set(hud) | {counter, slow}
    world_objs = [o for o in scene.objects if o not in hud_set and o.type != "CAMERA"]
    configure_render(scene, args.mode, args.resolution, style="question3d", reel=REEL)
    settings = scene.render.image_settings

    def as_png(path):
        if hasattr(settings, "media_type"):
            settings.media_type = "IMAGE"
        settings.file_format = "PNG"
        settings.color_mode = "RGBA"
        scene.render.filepath = str(path)

    tmp = out_dir / "_layers"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    # layer 1: 3D blocks with shading, no text
    for o in hud_set:
        o.hide_render = True
    scene.view_settings.exposure = SCENE_EXPOSURE
    if still_frame:
        scene.frame_set(still_frame)
        as_png(tmp / "scene.png")
        bpy.ops.render.render(write_still=True)
    else:
        if hasattr(settings, "media_type"):
            settings.media_type = "VIDEO"
        settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "HIGH"
        scene.render.ffmpeg.audio_codec = "AAC"
        scene.render.ffmpeg.audio_bitrate = 192
        scene.render.filepath = str(tmp / "scene.mp4")
        bpy.ops.render.render(animation=True)
    # layer 2: text and graph only, flat full colours on a transparent background
    for o in hud_set:
        o.hide_render = False
    for o in world_objs:
        o.hide_render = True
    apply_question_style(scene, "FLAT")
    scene.view_settings.exposure = 0.0
    scene.render.film_transparent = True
    if still_frame:
        scene.frame_set(still_frame)
        as_png(tmp / "hud.png")
        bpy.ops.render.render(write_still=True)
        src, hud_in, out = ["-i", str(tmp / "scene.png")], ["-i", str(tmp / "hud.png")],             out_dir / f"{NAME}{TAG}_{args.mode}.png"
        extra = []
    else:
        as_png(tmp / "hud_")
        bpy.ops.render.render(animation=True)
        src = ["-i", str(tmp / "scene.mp4")]
        hud_in = ["-framerate", str(FPS), "-start_number", "1", "-i", str(tmp / "hud_%04d.png")]
        out = out_dir / f"{NAME}{TAG}_{args.mode}.mp4"
        extra = ["-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
                 "-c:a", "copy"]
    for o in world_objs:
        o.hide_render = False
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *src, *hud_in,
           "-filter_complex", "[0:v][1:v]overlay=0:0[v]" if extra else "[0:v][1:v]overlay=0:0",
           *extra, str(out)]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[collision_pi] rendered {out}")


mode = args.mode
args.mode = "none"                      # finish() only saves the .blend; rendering is below
physkit.finish(sc, NAME, args, style="question3d")
args.mode = mode
if mode != "none":
    render_two_layers(sc, still if args.still else None)
