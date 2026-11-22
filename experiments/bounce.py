# Bouncing ball test: motion computed from physics (g, restitution), then keyframed in Blender.
import bpy, math, sys, os

out_dir = sys.argv[sys.argv.index("--") + 1]
FPS, SECONDS = 24, 4
g, e, h0, r = 9.81, 0.75, 3.0, 0.3   # gravity, bounce factor, drop height (m), ball radius

# --- clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, FPS * SECONDS

# --- physics: height of ball bottom over time (free fall + bounces)
def height(t):
    v, tt = math.sqrt(2 * g * h0), t
    first = math.sqrt(2 * h0 / g)
    if tt < first:
        return h0 - 0.5 * g * tt ** 2
    tt -= first
    v *= e
    while v > 0.05:
        flight = 2 * v / g
        if tt < flight:
            return v * tt - 0.5 * g * tt ** 2
        tt -= flight
        v *= e
    return 0.0

# --- materials
def mat(name, color, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m

# --- floor, ball
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.context.object.data.materials.append(mat("Floor", (0.8, 0.8, 0.82), 0.8))

bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24)
ball = bpy.context.object
bpy.ops.object.shade_smooth()
ball.data.materials.append(mat("Ball", (0.9, 0.25, 0.1), 0.3))

for f in range(scene.frame_start, scene.frame_end + 1):
    t = (f - 1) / FPS
    ball.location = (-1.5 + 0.8 * t, 0, r + height(t))   # slow drift sideways
    ball.keyframe_insert("location", frame=f)

# --- light, camera, world
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30)))
bpy.context.object.data.energy = 3
bpy.ops.object.camera_add(location=(0.5, -8, 2.2), rotation=(math.radians(83), 0, 0))
scene.camera = bpy.context.object
world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.7, 0.85, 1)

# --- render settings (Eevee = fast engine)
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng; break
    except TypeError:
        pass
scene.render.resolution_x, scene.render.resolution_y = 960, 540
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(out_dir, "frame_")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "bounce.blend"))
bpy.ops.render.render(animation=True)
