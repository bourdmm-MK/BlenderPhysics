"""The shared PhysicsAid visual style for physics-question scenes.

Source of truth: `style/visual-style.md` in the AnimateSystem repository (it
inherits the Manim course style). Black background, flat colours by meaning,
serif italic labels, mass labels inside bodies, axes behind objects.

3D object models (metal, wood...) keep the realistic look from materials.py;
use this style for scenes that reproduce a physics question.
"""

import bpy


def hexc(hx: str):
    """Course colour as hex (sRGB) -> Blender linear RGB tuple."""
    v = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v)


# Colours by meaning (Manim constant names in comments).
COURSE = {
    "position": hexc("#58C4DD"),      # BLUE
    "displacement": hexc("#FF862F"),  # ORANGE
    "distance": hexc("#D147BD"),      # PINK
    "velocity": hexc("#F7D96F"),      # YELLOW
    "acceleration": hexc("#5CD0B3"),  # TEAL
    "axes": hexc("#83C167"),          # GREEN
    "aux": hexc("#DDDDDD"),           # GRAY_A: helper text, dashed guide lines
    "time": hexc("#FFFFFF"),          # WHITE
    "force": hexc("#FC6255"),         # RED: g and forces
    "structure": hexc("#BBBBBB"),     # GREY_B: slopes, floor, strings, springs
    "body": hexc("#C8BD99"),          # block / cart fill
    "body_text": (0.0, 0.0, 0.0),     # labels inside bodies
}

LABEL_FONT = r"C:\Windows\Fonts\timesi.ttf"   # closest installed serif italic to LaTeX


def apply_question_style(scene, lighting: str = "FLAT"):
    """Flat Workbench colours on black, exactly as in the Manim course.

    lighting="STUDIO" keeps the course colours but shades the faces, for
    question scenes shown in 3D (style "question3d").
    """
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.view_settings.view_transform = "Standard"
    shading = scene.display.shading
    shading.light = lighting
    if lighting == "STUDIO":
        shading.studio_light = "basic.sl"   # clearest of the built-in studio lights
    shading.color_type = "OBJECT"
    shading.show_shadows = False
    shading.show_cavity = False
    shading.show_object_outline = True
    shading.background_type = "VIEWPORT"
    shading.background_color = (0.0, 0.0, 0.0)


def label_font():
    """The serif italic font, loaded once."""
    return bpy.data.fonts.get("course_label") or _load_font()


def _load_font():
    f = bpy.data.fonts.load(LABEL_FONT)
    f.name = "course_label"
    return f
