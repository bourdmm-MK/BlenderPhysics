# Experiments

First Blender tests (2026-11-22), kept as they were written. They work on their
own and do **not** use `lib/physkit` or `tools/run.ps1`. When one of them becomes
a real model, rebuild it as `models/<name>/build.py` on top of physkit.

They write PNG frames into the folder you give them; join the frames into a
video with ffmpeg (`ffmpeg -framerate 24 -i %04d.png -c:v libx264 -pix_fmt yuv420p out.mp4`).

| Script | What it shows | Run |
|---|---|---|
| `bounce.py` | Ball dropped from 3 m, restitution 0.75, motion computed exactly and keyframed every frame. | `blender -b --python experiments\bounce.py -- OUT_DIR` |
| `pendulum_wave.py` | 12 pendulums; pendulum n makes 8+n swings in 16 s, L = g(T/2π)². | `... -- OUT_DIR [quick] [still FRAME...]` |
| `solar_system.py` | 8 planets + Moon, real relative periods, compressed distances (2.2 + 3.2·√AU), enlarged sizes. | `... -- OUT_DIR [zoom] [phases] [moonview] [still FRAME...]` |

`quick` = fast Workbench preview. In `solar_system.py`: `zoom` follows Earth at 6× slower
time; `phases` lights the planets from the Sun to show lit halves; `moonview`
renders a small "Moon seen from Earth" inset (combined with the main video in ffmpeg).

The rendered test videos are in Dropbox: `PhysicaAid\Blender renders\experiments 2026-11-22`
(the workspace `../README.md` maps it to the real folder).

## Lessons from these tests (this computer, Intel Iris Xe)

- Workbench preview: ≈0.1 s/frame. Use it for every draft.
- Eevee 720p, 32 samples, shadows: ≈2.7 s/frame. Eevee 960×540, 8 samples, no shadows: ≈0.5 s/frame, good enough when the lighting matters.
- `view_transform = "Standard"` gives punchier colours than the default.
- Always render one or two stills and look at them first. That caught off-screen planets, labels that were far too big, and overexposure.
