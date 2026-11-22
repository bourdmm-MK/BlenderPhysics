"""physkit: shared helpers for building physics models in Blender.

Every model script in models/ imports from here so that all models share the
same units (SI: metres, kilograms, seconds), lighting, camera and render
settings.
"""

from .scene import new_scene, add_camera, add_lights, set_frames
from .materials import material
from .render import configure_render, finish
from .cli import parse_args

__all__ = [
    "new_scene",
    "add_camera",
    "add_lights",
    "set_frames",
    "material",
    "configure_render",
    "finish",
    "parse_args",
]
