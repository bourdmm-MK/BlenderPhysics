# Solar system with the Moon - quick preview (Workbench).
# Real: orbital periods (relative), Moon's period, approximate positions at year 2000.
# Not to scale: sizes enlarged, distances compressed (square root of real distance), time sped up.
# Usage: blender -b --python solar_system.py -- OUT_DIR [zoom] [still FRAME ...]
#   zoom = camera follows Earth up close, time 6x slower
import bpy, math, sys, os

args = sys.argv[sys.argv.index("--") + 1:]
out_dir = args[0]
stills = [int(a) for a in args if a.isdigit()] if "still" in args else []
phases = "phases" in args        # realistic mode: real sunlight, Moon phases
moonview = "moonview" in args    # render the "Moon seen from Earth" inset instead
zoom = "zoom" in args or phases

FPS = 24
SEC_PER_YEAR = 48.0 if zoom else 8.0   # seconds of video per Earth year
YEARS = 0.25 if zoom else 3.0          # length of the clip in Earth years
DIST, OFFSET = 3.2, 2.2      # display distance = OFFSET + DIST * sqrt(real distance in AU)

# name, distance (AU), period (Earth years), display radius, colour, start angle (deg, approx J2000)
PLANETS = [
    ("Mercury", 0.387, 0.241, 0.15, (0.6, 0.58, 0.55), 252),
    ("Venus",   0.723, 0.615, 0.25, (0.9, 0.75, 0.45), 182),
    ("Earth",   1.000, 1.000, 0.27, (0.15, 0.4, 0.9), 100),
    ("Mars",    1.524, 1.881, 0.19, (0.85, 0.3, 0.15), 355),
    ("Jupiter", 5.203, 11.86, 0.60, (0.85, 0.7, 0.5), 34),
    ("Saturn",  9.537, 29.46, 0.50, (0.9, 0.8, 0.55), 50),
    ("Uranus",  19.19, 84.01, 0.32, (0.55, 0.85, 0.9), 314),
    ("Neptune", 30.07, 164.8, 0.31, (0.25, 0.4, 0.95), 304),
]
MOON_PERIOD = 27.32 / 365.25
MOON_DIST, MOON_R = 0.55, 0.09

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, int(YEARS * SEC_PER_YEAR * FPS)

def mat(name, color, emit=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    if phases:   # realistic material; emit > 0 makes it glow (Sun, labels, orbit lines)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = 0.8
        if emit:
            b.inputs["Emission Color"].default_value = (*color, 1)
            b.inputs["Emission Strength"].default_value = emit
    return m

def sphere(name, radius, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat(name, color))
    return o

# camera first (labels turn to face it)
bpy.ops.object.camera_add(location=(0, -33, 25))
cam = bpy.context.object
cam.data.lens = 27
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, -1.0, 0)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

labels, rings = [], []
def label(text, parent, size, offset):
    bpy.ops.object.text_add()
    t = bpy.context.object
    t.data.body = text
    t.data.size = size * (0.4 if zoom and text != "Moon" else 1)
    t.data.align_x = "CENTER"
    t.data.materials.append(mat("Label", (0.95, 0.95, 0.95), emit=1.0))
    t.parent = parent
    t.location = (0, 0, (offset - 0.2) if zoom and text != "Moon" else offset)
    cr = t.constraints.new("COPY_ROTATION")
    cr.target = cam
    labels.append(t)
    return t

orbit_mat = mat("Orbit", (0.22, 0.25, 0.32), emit=0.25)
def orbit_ring(radius):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.004 if zoom else 0.02,
                                     major_segments=192, minor_segments=6)
    bpy.context.object.data.materials.append(orbit_mat)
    rings.append(bpy.context.object)

sun = sphere("Sun", 1.2, (1.0, 0.8, 0.2))
if phases:
    sun.data.materials[0] = mat("SunGlow", (1.0, 0.8, 0.2), emit=6.0)
label("Sun", sun, 0.45, 1.6)

bodies = []   # (object, display distance, period, start angle)
for name, a, T, r, col, ang in PLANETS:
    d = OFFSET + DIST * math.sqrt(a)
    orbit_ring(d)
    p = sphere(name, r, col)
    label(name, p, 0.4, r + 0.35)
    bodies.append((p, d, T, math.radians(ang)))
    if name == "Earth":
        earth = p
    if name == "Saturn":   # tilted ring
        bpy.ops.mesh.primitive_torus_add(major_radius=r * 1.8, minor_radius=r * 0.35,
                                         major_segments=64, minor_segments=12)
        ring = bpy.context.object
        ring.scale = (1, 1, 0.08)
        ring.rotation_euler = (math.radians(27), 0, 0)
        ring.data.materials.append(mat("Ring", (0.8, 0.72, 0.55)))
        ring.parent = p

moon = sphere("Moon", MOON_R, (0.75, 0.75, 0.75))
label("Moon", moon, 0.14, MOON_R + 0.1)
bpy.ops.mesh.primitive_torus_add(major_radius=MOON_DIST, minor_radius=0.006,
                                 major_segments=96, minor_segments=6)
moon_ring = bpy.context.object
moon_ring.data.materials.append(orbit_mat)
moon_ring.parent = earth
rings.append(moon_ring)

# second camera: stands on Earth's surface and looks at the Moon (for the phases inset)
bpy.ops.object.camera_add()
mooncam = bpy.context.object
mooncam.name = "MoonCam"
mooncam.data.lens = 30
mt = mooncam.constraints.new("TRACK_TO")
mt.target, mt.track_axis, mt.up_axis = moon, "TRACK_NEGATIVE_Z", "UP_Y"

if zoom:   # camera rides along with Earth, looking at it from slightly above
    cam.location = (0, -1.6, 3.4) if phases else (0, -3.4, 2.0)   # phases: view more from above
    cam.data.lens = 32
    cl = cam.constraints.new("COPY_LOCATION")
    cl.target, cl.use_offset = earth, True
    cam.constraints.move(1, 0)          # follow first, then aim
    tl = target.constraints.new("COPY_LOCATION")
    tl.target = earth

# motion: circular orbits, angle = start + 2*pi*t/T (counter-clockwise seen from above)
for f in range(scene.frame_start, scene.frame_end + 1):
    yrs = (f - 1) / (SEC_PER_YEAR * FPS)
    for p, d, T, a0 in bodies:
        a = a0 + 2 * math.pi * yrs / T
        p.location = (d * math.cos(a), d * math.sin(a), 0)
        p.keyframe_insert("location", frame=f)
    am = 2 * math.pi * yrs / MOON_PERIOD
    ex, ey, _ = earth.location
    moon.location = (ex + MOON_DIST * math.cos(am), ey + MOON_DIST * math.sin(am), 0)
    moon.keyframe_insert("location", frame=f)
    ux, uy = math.cos(am), math.sin(am)          # direction Earth -> Moon
    mooncam.location = (ex + 0.3 * ux, ey + 0.3 * uy, 0)
    mooncam.keyframe_insert("location", frame=f)

# world + quick render engine
world = bpy.data.worlds.new("World"); scene.world = world
world.color = (0.01, 0.012, 0.03)
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light, sh.color_type = "STUDIO", "MATERIAL"
sh.show_shadows, sh.show_cavity = False, False
scene.display.render_aa = "8"
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.image_settings.file_format = "PNG"
if phases:   # realistic engine, one light at the Sun's centre
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng; break
        except TypeError:
            pass
    scene.eevee.taa_render_samples = 8
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 0))
    sunlight = bpy.context.object.data
    sunlight.energy = 700
    sunlight.use_shadow = False      # light passes out through the Sun sphere
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.004, 0.005, 0.012, 1)
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    if moonview:
        scene.camera = mooncam
        for o in labels + rings:
            o.hide_render = True
        scene.render.resolution_x, scene.render.resolution_y = 300, 300

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "solar_system.blend"))

if stills:
    for f in stills:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(out_dir, f"still_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(out_dir, "frame_")
    bpy.ops.render.render(animation=True)





