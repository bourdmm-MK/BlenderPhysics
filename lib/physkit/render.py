"""Render settings and saving results into output/<model>/."""

from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "output"


def configure_render(scene, mode: str, height: int = 720):
    """Set up the quick (Workbench) or realistic (Eevee) engine."""
    scene.render.resolution_y = height
    scene.render.resolution_x = round(height * 16 / 9)
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"  # punchier colours than AgX
    if mode == "final":
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except TypeError:  # older/newer Blender naming
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = 32
    else:
        scene.render.engine = "BLENDER_WORKBENCH"
        shading = scene.display.shading
        shading.light = "STUDIO"
        shading.color_type = "MATERIAL"
        shading.show_shadows = True
        shading.show_cavity = True


def finish(scene, model_name: str, args):
    """Save the .blend file and, if asked, render an image or a video."""
    out_dir = OUTPUT_ROOT / model_name
    out_dir.mkdir(parents=True, exist_ok=True)
    blend_path = out_dir / f"{model_name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"[physkit] saved {blend_path}")

    if args.mode == "none":
        return
    configure_render(scene, args.mode, args.resolution)

    if args.still:
        scene.frame_set((scene.frame_start + scene.frame_end) // 2)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(out_dir / f"{model_name}_{args.mode}.png")
        bpy.ops.render.render(write_still=True)
    else:
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.filepath = str(out_dir / f"{model_name}_{args.mode}.mp4")
        bpy.ops.render.render(animation=True)
    print(f"[physkit] rendered {scene.render.filepath}")
