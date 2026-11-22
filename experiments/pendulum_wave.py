# Pendulum wave: N pendulums whose lengths are chosen so pendulum n makes (K + n)
# swings in CYCLE seconds. They start together, drift into "snake" and wave patterns,
# and all line up again after CYCLE seconds.
# Usage: blender -b --python pendulum_wave.py -- OUT_DIR [still FRAME ...]
import bpy, math, sys, os, colorsys

args = sys.argv[sys.argv.index("--") + 1:]
out_dir = args[0]
stills = [int(a) for a in args[2:] if a.isdigit()] if len(args) > 1 and args[1] == "still" else []

FPS = 24
g = 9.81
N, K, CYCLE = 12, 8, 16.0          # 12 pendulums; 8..19 swings per 16 s
THETA0 = math.radians(15)           # small starting angle (small-angle motion)
SPACING, BAR_Z = 0.12, 1.5

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, int(CYCLE * FPS) + 1

def mat(name, color, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*color, 1)      # colour used by the quick preview engine
    return m

steel = mat("Steel", (0.75, 0.75, 0.78), 0.25, 1.0)
wood = mat("Wood", (0.35, 0.2, 0.1), 0.6)

def cylinder(radius, depth, loc, rot=(0, 0, 0), material=steel, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=24)
    o = bpy.context.object
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o

# --- floor and frame (two posts + top bar along x)
bpy.ops.mesh.primitive_plane_add(size=30)
bpy.context.object.data.materials.append(mat("Floor", (0.55, 0.57, 0.6), 0.7))
half = (N - 1) * SPACING / 2 + 0.15
for x in (-half, half):
    cylinder(0.025, BAR_Z, (x, 0, BAR_Z / 2), material=wood)
cylinder(0.02, 2 * half, (0, 0, BAR_Z), rot=(0, math.radians(90), 0), material=wood)

# --- pendulums: an empty at the pivot carries rod + bob; we rotate the empty
pivots = []
for n in range(N):
    T = CYCLE / (K + n)                       # period of pendulum n
    L = g * (T / (2 * math.pi)) ** 2          # length that gives that period
    x = -(N - 1) * SPACING / 2 + n * SPACING
    piv = bpy.data.objects.new(f"Pivot{n}", None)
    scene.collection.objects.link(piv)
    piv.location = (x, 0, BAR_Z)
    cylinder(0.003, L, (0, 0, -L / 2), parent=piv)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0, 0, -L), segments=32, ring_count=16)
    bob = bpy.context.object
    bpy.ops.object.shade_smooth()
    hue = n / N * 0.8
    bob.data.materials.append(mat(f"Bob{n}", colorsys.hsv_to_rgb(hue, 0.85, 0.9), 0.3))
    bob.parent = piv
    pivots.append((piv, T))

# --- motion: theta(t) = theta0 * cos(2*pi*t/T)  (swing in the y-z plane)
for f in range(scene.frame_start, scene.frame_end + 1):
    t = (f - 1) / FPS
    for piv, T in pivots:
        piv.rotation_euler = (THETA0 * math.cos(2 * math.pi * t / T), 0, 0)
        piv.keyframe_insert("rotation_euler", index=0, frame=f)

# --- lights
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(35), math.radians(15), math.radians(-30)))
bpy.context.object.data.energy = 3.5
bpy.context.object.data.angle = math.radians(3)
bpy.ops.object.light_add(type="AREA", location=(-2, -3, 3))
bpy.context.object.data.energy = 300
bpy.context.object.data.size = 3
bpy.context.object.rotation_euler = (math.radians(50), 0, math.radians(-35))

# --- camera looking at the middle of the pendulums from the front-side
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, 0, 1.0)
bpy.ops.object.camera_add(location=(2.3, -1.6, 2.5))
cam = bpy.context.object
cam.data.lens = 40
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.3, 0.4, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

# --- render settings
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng; break
    except TypeError:
        pass
scene.eevee.taa_render_samples = 32
scene.view_settings.view_transform = "Standard"   # stronger, truer colours
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.image_settings.file_format = "PNG"

if "quick" in args:   # fast preview: simple studio lighting, same motion
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type = "STUDIO", "MATERIAL"
    sh.show_shadows, sh.show_cavity = True, False
    scene.display.render_aa = "8"
    scene.render.resolution_x, scene.render.resolution_y = 960, 540

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "pendulum_wave.blend"))

if stills:
    for f in stills:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(out_dir, f"still_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(out_dir, "frame_")
    bpy.ops.render.render(animation=True)
