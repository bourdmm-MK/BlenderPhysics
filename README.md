# BlenderPhysics

3D models of objects and physical systems for physics teaching, built in
**Blender 5.3** with Python scripts.

Every model is a script, not a hand-saved `.blend` file. The script builds the
scene from scratch: shapes, materials, camera, lights and, when it moves, the
motion computed from the real physics equations. So a model can be read,
changed (a longer string, a steeper slope…) and rebuilt in seconds.

## Folder layout

| Folder | What is in it |
|---|---|
| `models/<name>/build.py` | One folder per model. `build.py` builds it. Notes or reference images for that model go next to it. |
| `lib/physkit/` | Shared building blocks used by all models: empty scene in metres, camera, lights, material palette, render settings. |
| `experiments/` | First standalone tests (bouncing ball, pendulum wave, solar system), kept as written. See its README. |
| `tools/run.ps1` | Builds a model without opening Blender, and can render it. |
| `output/<name>/` | Results: the `.blend` file, images, videos. **Not stored in git** (it is rebuilt from the scripts). Final videos worth keeping go to Dropbox. |

## Using it

Run these from the `BlenderPhysics` folder in PowerShell.

Build the model and save `output\pendulum\pendulum.blend`:

```powershell
.\tools\run.ps1 pendulum
```

Build it and open it in Blender to look around or keep modelling by hand:

```powershell
.\tools\run.ps1 pendulum -open
```

Quick preview image, or video (≈0.1 s per frame):

```powershell
.\tools\run.ps1 pendulum -mode preview -still
```

```powershell
.\tools\run.ps1 pendulum -mode preview
```

Realistic video (Eevee, ≈2–3 s per frame at 720p, so ≈1 minute per second of video):

```powershell
.\tools\run.ps1 pendulum -mode final
```

Add `-resolution 1080` for full HD.

If PowerShell refuses to run the script, start it with
`powershell -ExecutionPolicy Bypass -File .\tools\run.ps1 pendulum`.

## Models

| Model | What it shows |
|---|---|
| `pendulum` | Stand, string and bob. The swing comes from solving θ'' = −(g/L)·sin θ, not from hand animation. Length, start angle and gravity are at the top of the script. |
| `collision_pi` | Colliding blocks count π: a big block (M = 100ⁿ kg) pushes a 1 kg block against a wall; all elastic collisions are counted (3, 31, 314 … 3 141 592) for n = 0…6, while a graph of how far each estimate is from π (in %, log scale) steps down. Exact event-by-event solution; labelled slow motion where collisions pile up; generated sound track (a "tock" per collision, a tone when they come too fast to hear, a bell per graph point). 3D course style (`style="question3d"`); the text and graph are rendered as a separate flat layer so they stay crisp and full-colour. ≈30 s video; `-mode preview -resolution 1080` takes ≈5 min; add `-reel -resolution 1920` for a vertical 1080×1920 reel (title on top, layout kept clear of the reel buttons and caption). |
| `two_slopes_spring` | Exam question: m and 2m slide down 60° slopes, hit m₃ = 3m on a spring at the same moment, stick, and oscillate. Drawn in the course style (flat 2D look on black). A Manim twin is in PhysicsAid `expermients/two_slopes_spring/`. `-mode preview -still` renders the impact frame. |
| `hand_sketch` | Smooth, skin-coloured right hand for the right-hand rule, **three fingers**: index = v, middle = B (bent 90°), thumb = F = v×B. The fingers carrying vectors glow in their course colours. Builds in ≈25 s: two stills, `hand_sketch.glb` + `hand_viewer.html` (rotatable), and `hand_sketch_board.glb` (hand only, no arrows) for PhysicsLearn whiteboards. |
| `hand_palm` | The same hand in the **open-palm** pose: four straight fingers = v, B enters the back of the palm and leaves the palm face (blue spot), thumb = F. Same script as `hand_sketch` with the pose switched; same frame, so boards place both hands the same way. Outputs `output/hand_palm/` incl. `hand_palm_board.glb`. |

## Two looks

- **Object models** (like `pendulum`): realistic materials from `physkit/materials.py`.
- **Physics-question scenes** (like `two_slopes_spring`): the shared course style from
  `physkit/style.py` — black background, flat colours by meaning, serif italic labels,
  mass labels inside bodies, axes behind objects. Call
  `physkit.finish(scene, name, args, style="question")`. The full rules are in
  AnimateSystem `style/visual-style.md`. `style="question3d"` (like `collision_pi`)
  keeps the same colours but shades the faces, for scenes seen in 3D.

## Adding a new model

1. Copy `models/pendulum/` to `models/<new-name>/`.
2. Change the parameters and shapes in `build.py`; keep the
   `physkit.finish(scene, "<new-name>", args)` line at the end.
3. Run `.\tools\run.ps1 <new-name> -mode preview -still` and look at the image.
4. Add a line to the Models table above.

Units are SI throughout: 1 Blender unit = 1 metre, time in seconds.
