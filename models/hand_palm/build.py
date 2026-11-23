"""Open-palm right hand for F = q v x B: the four straight fingers = v, B enters the back
of the palm and leaves the palm face, thumb = F (exact at any angle between v and B).

Same script, sizes and look as models/hand_sketch (the three-finger hand); this file only
selects the pose. Outputs go to output/hand_palm/ (hand_palm.glb, hand_palm_board.glb,
two stills, hand_viewer.html).

Run:  .\tools\run.ps1 hand_palm
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parents[1] / "hand_sketch" / "build.py"),
               init_globals={"HAND_POSE": "flat-palm"}, run_name="__main__")
