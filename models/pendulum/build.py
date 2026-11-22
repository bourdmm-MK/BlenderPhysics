"""Simple pendulum: stand, string and bob, swinging with real physics.

The motion is not hand-animated: it solves the full pendulum equation
    theta'' = -(g / L) * sin(theta)
step by step (Runge-Kutta 4) and keyframes the angle on every frame.

Run:  .\\tools\\run.ps1 pendulum -mode preview
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import bpy  # noqa: E402

import physkit  # noqa: E402
from physkit.materials import assign, material  # noqa: E402

# ---- Physics parameters (SI units) ----------------------------------------
LENGTH = 1.0                  # string length, m
G = 9.81                      # gravity, m/s^2
THETA0 = math.radians(30)     # starting angle
OMEGA0 = 0.0                  # starting angular speed, rad/s
DURATION = 6.0                # seconds of animation
BOB_RADIUS = 0.06             # m
PIVOT_HEIGHT = 1.6            # m above the floor


def swing_angles(fps: int, seconds: float):
    """Angle (rad) at each frame, from RK4 integration of the pendulum."""
    substeps = 20
    dt = 1.0 / (fps * substeps)

    def accel(theta):
        return -(G / LENGTH) * math.sin(theta)

    theta, omega = THETA0, OMEGA0
    angles = []
    for _ in range(round(seconds * fps) + 1):
        angles.append(theta)
        for _ in range(substeps):
            k1t, k1w = omega, accel(theta)
            k2t, k2w = omega + 0.5 * dt * k1w, accel(theta + 0.5 * dt * k1t)
            k3t, k3w = omega + 0.5 * dt * k2w, accel(theta + 0.5 * dt * k2t)
            k4t, k4w = omega + dt * k3w, accel(theta + dt * k3t)
            theta += dt / 6 * (k1t + 2 * k2t + 2 * k3t + k4t)
            omega += dt / 6 * (k1w + 2 * k2w + 2 * k3w + k4w)
    return angles


def build_stand():
    """Base, upright post and top arm holding the pivot."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.02))
    base = bpy.context.object
    base.name = "Base"
    base.scale = (0.9, 0.4, 0.04)
    assign(base, material("wood"))

    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=PIVOT_HEIGHT + 0.05,
                                        location=(-0.4, 0, (PIVOT_HEIGHT + 0.05) / 2))
    post = bpy.context.object
    post.name = "Post"
    assign(post, material("dark_metal"))

    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.45,
                                        location=(-0.2, 0, PIVOT_HEIGHT),
                                        rotation=(0, math.radians(90), 0))
    arm = bpy.context.object
    arm.name = "Arm"
    assign(arm, material("dark_metal"))


def build_pendulum():
    """Pivot (an empty that rotates) with the string and bob as its children."""
    pivot = bpy.data.objects.new("Pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = (0, 0, PIVOT_HEIGHT)
    pivot.empty_display_size = 0.05

    bpy.ops.mesh.primitive_cylinder_add(radius=0.003, depth=LENGTH,
                                        location=(0, 0, -LENGTH / 2))
    string = bpy.context.object
    string.name = "String"
    string.parent = pivot
    assign(string, material("string"))

    bpy.ops.mesh.primitive_uv_sphere_add(radius=BOB_RADIUS, segments=48, ring_count=24,
                                         location=(0, 0, -LENGTH))
    bob = bpy.context.object
    bob.name = "Bob"
    bob.parent = pivot
    bpy.ops.object.shade_smooth()
    assign(bob, material("red"))
    return pivot


def animate(pivot, scene):
    """Keyframe the pivot's rotation about the Y axis on every frame."""
    for i, theta in enumerate(swing_angles(scene.render.fps, DURATION)):
        pivot.rotation_euler = (0, theta, 0)
        pivot.keyframe_insert("rotation_euler", index=1, frame=scene.frame_start + i)


def main():
    args = physkit.parse_args("Simple pendulum")
    scene = physkit.new_scene(fps=24)
    physkit.set_frames(scene, DURATION)

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    assign(bpy.context.object, material("floor"))

    build_stand()
    pivot = build_pendulum()
    animate(pivot, scene)

    physkit.add_camera(location=(0.6, -4.2, 1.3), look_at=(-0.1, 0, 0.82), lens=35)
    physkit.add_lights()
    physkit.finish(scene, "pendulum", args)


main()
