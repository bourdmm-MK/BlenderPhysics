# BlenderPhysics agent instructions

Read [README.md](README.md) for the layout and commands.

## Rules

- **Models are scripts.** Each model lives in `models/<name>/build.py` and builds the whole scene from an empty file using `lib/physkit`. Do not commit hand-edited `.blend` files as the source of a model. If the user models something by hand, ask before adding it, and keep it under ~10 MB.
- **Never put renders, videos or large `.blend` files in git.** `output/` is ignored on purpose. Final videos go to Dropbox (see the workspace `../README.md`); ask before writing, moving or deleting anything in Dropbox or Google Drive.
- **Physics must be real.** Motion comes from the equations of motion (integrated in the script) or from Blender's physics engines with stated parameters, never from hand-placed keyframes that only look right. Put the physical parameters (SI units) as named constants at the top of the script.
- **Units:** 1 Blender unit = 1 metre; seconds; kilograms.
- **Check your work visually.** After changing a model, run `.\tools\run.ps1 <name> -mode preview -still` and look at the PNG before saying it is done. Use `-mode final` only for finished videos.
- **Speed on this computer** (Intel Iris Xe, no separate graphics card): preview (Workbench) ≈0.1 s/frame; final (Eevee) ≈2–3 s/frame at 720p. Give the user a time estimate before rendering.
- **Visual style:** follow the shared style in the AnimateSystem repository, `style/visual-style.md` (locally `../AnimateSystem/style/visual-style.md`): black background, colours by meaning (axes green, velocity yellow, g/forces red, structure grey, bodies sand), serif italic labels (no handwriting unless asked), mass labels inside their bodies, axes and guide lines behind the objects. The realistic look of `lib/physkit` materials (metal, wood) is for 3D object models; physics-question scenes use the shared style.
- **Blender:** 5.3 at `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe` (override with the `BLENDER_EXE` environment variable). Scripts run with `--factory-startup`, so they must not rely on the user's Blender preferences or add-ons.

## Workspace context

This project sits in the local `PhysicsWork` folder next to:

- **PhysicsLearn** (`bourdmm-MK/PhysticsLearn`): the brain: teaching knowledge, Marianna's method, AI-tutor rules.
- **PhysicsAid** (`bourdmm-MK/PhysicsAid`): the studio: Manim animation code for the course.

BlenderPhysics is the 3D workshop: models of objects and physical systems, which can later feed course videos.

The user is a teacher, not a developer: explain in plain words and make technical choices (git, branches, environments) yourself.
