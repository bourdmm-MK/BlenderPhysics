"""Empty scene, camera and lights with consistent defaults."""

import math

import bpy


def new_scene(fps: int = 24):
    """Wipe the current file and start an empty scene in SI units (metres)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = fps
    world = bpy.data.worlds.new("World")
    world.color = (0.9, 0.92, 0.95)  # used by the quick preview mode
    world.use_nodes = True           # the realistic mode reads the node below
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1)
        background.inputs["Strength"].default_value = 0.6
    scene.world = world
    return scene


def set_frames(scene, seconds: float):
    """Make the animation last `seconds` at the scene's frame rate."""
    scene.frame_start = 1
    scene.frame_end = max(1, round(seconds * scene.render.fps))


def add_camera(location=(0.0, -4.0, 1.0), look_at=(0.0, 0.0, 1.0), lens=50.0):
    """Add a camera at `location` pointing at `look_at` and make it active."""
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = location

    target = bpy.data.objects.new("CameraTarget", None)
    bpy.context.collection.objects.link(target)
    target.location = look_at
    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    bpy.context.scene.camera = cam
    return cam


def add_lights(strength: float = 2.0):
    """Soft three-point style lighting: a sun plus a large fill area light."""
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = strength
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
    bpy.context.collection.objects.link(sun)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 120
    fill_data.size = 4
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (-3, -3, 3)
    fill.rotation_euler = (math.radians(55), 0, math.radians(-45))
    bpy.context.collection.objects.link(fill)
    return sun, fill
