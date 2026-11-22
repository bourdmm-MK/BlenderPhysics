"""LaTeX labels in Blender, drawn by LaTeX itself, so they look exactly like Manim.

How: LaTeX (+ dvisvgm, both come with MiKTeX) turns the formula into an SVG of
glyph outlines; Blender imports the SVG as a flat curve object. Results are
cached in output/_tex/ (not in git).

Sizes follow Manim: `manim_em(font_size, frame_width_m)` gives the em size in
metres for a Manim font_size in a scene whose camera shows `frame_width_m`
metres across (Manim's frame is 14.22 units wide).

Changing numbers (readouts) cannot be re-run through LaTeX every frame; use a
Blender text object with NUMBER_FONT (Latin Modern = the Computer Modern
design LaTeX uses), which is what Manim's DecimalNumber looks like.
"""
import hashlib
import math
import re
import subprocess
from pathlib import Path

import bpy

from .render import OUTPUT_ROOT

CACHE = OUTPUT_ROOT / "_tex"
NUMBER_FONT = r"C:\Windows\Fonts\lmroman10-regular.otf"
NUMBER_SCALE = 1.42   # Blender text size per em so digits match LaTeX's (measured against Manim)
TEMPLATE = r"""\documentclass[preview]{standalone}
\usepackage{amsmath}
\usepackage{amssymb}
\begin{document}
%s
\end{document}
"""
# Measured: MathTex("M", font_size=48).height = 0.3402 Manim units; 'M' is 6.833 pt
# tall in a 10 pt em  ->  one em = 0.4979 units at font_size 48.
_EM_UNITS_PER_FONT_SIZE = 0.4979 / 48
_MANIM_FRAME_WIDTH = 14.2222


def manim_em(font_size: float, frame_width_m: float) -> float:
    """Em size in metres matching a Manim font_size, for a camera `frame_width_m` wide."""
    return font_size * _EM_UNITS_PER_FONT_SIZE * frame_width_m / _MANIM_FRAME_WIDTH


def _svg(body: str):
    key = hashlib.md5(body.encode("utf-8")).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    svg = CACHE / f"{key}.svg"
    if not svg.exists():
        (CACHE / f"{key}.tex").write_text(TEMPLATE % body, encoding="utf-8")
        for cmd in (["latex", "-interaction=nonstopmode", f"{key}.tex"],
                    ["dvisvgm", "--no-fonts", "--exact-bbox", f"{key}.dvi"]):
            r = subprocess.run(cmd, cwd=CACHE, capture_output=True, text=True)
            if r.returncode != 0 or (cmd[0] == "dvisvgm" and not svg.exists()):
                raise RuntimeError(f"LaTeX failed for {body!r}:\n{r.stdout[-1500:]}")
    height_pt = float(re.search(r"viewBox='([^']+)'", svg.read_text()).group(1).split()[3])
    return svg, height_pt


def tex(body: str, em: float, color, loc=(0.0, 0.0, 0.0), math_mode: bool = True,
        align: str = "CENTER", name: str = "tex"):
    """A LaTeX label as one flat object facing the camera at -y.

    body: LaTeX (math mode by default, e.g. r"\\vec v_1"); math_mode=False for
    text with $...$ inside. em: size of one em in metres (see manim_em).
    align: "CENTER" or "LEFT" (loc is then the left edge, vertically centred).
    Returns the object; its .dimensions give the size for laying out rows.
    """
    svg, height_pt = _svg(f"${body}$" if math_mode else body)
    scene = bpy.context.scene
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(svg))
    new = [o for o in bpy.data.objects if o not in before]
    imported_cols = {c for o in new for c in o.users_collection}
    with bpy.context.temp_override(active_object=new[0], object=new[0],
                                   selected_objects=new, selected_editable_objects=new):
        if len(new) > 1:
            bpy.ops.object.join()
    obj = new[0]
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    scene.collection.objects.link(obj)
    for c in imported_cols:
        if c.name in bpy.data.collections and not c.objects:
            bpy.data.collections.remove(c)
    # centre the origin on the glyphs, then scale pt -> metres and stand it up
    with bpy.context.temp_override(active_object=obj, object=obj,
                                   selected_objects=[obj], selected_editable_objects=[obj]):
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.context.view_layer.update()
    pt_to_bu = obj.dimensions.y / height_pt if height_pt else 1.0
    s = em / (10.0 * pt_to_bu)
    obj.scale = (s, s, s)
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.color = tuple(color) + (1,)
    x, y, z = loc
    if align == "LEFT":
        x += obj.dimensions.x * s / 2
    obj.location = (x, y, z)
    bpy.context.view_layer.update()
    return obj


def width(obj) -> float:
    """Width in metres of a label made by tex() (after scaling)."""
    return obj.dimensions.x


def number(value_text: str, em: float, color, loc=(0.0, 0.0, 0.0), name: str = "num"):
    """A changeable number in the LaTeX (Latin Modern) font; update with obj.data.body."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = value_text
    cu.font = bpy.data.fonts.get("lm_number") or _load_number_font()
    cu.size = em * NUMBER_SCALE
    cu.align_x, cu.align_y = "LEFT", "CENTER"
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (math.radians(90), 0, 0)
    o.color = tuple(color) + (1,)
    return o


def _load_number_font():
    f = bpy.data.fonts.load(NUMBER_FONT)
    f.name = "lm_number"
    return f
