"""Read the options passed after `--` on the Blender command line."""

import argparse
import sys


def parse_args(description: str = ""):
    """Options every model script understands.

    --mode preview  quick Workbench render (~0.1 s/frame) for drafts
    --mode final    realistic Eevee render (~2-3 s/frame at 720p)
    --mode none     only build and save the .blend file (default)
    --still         render one image (the middle frame) instead of the video
    """
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--mode", choices=["none", "preview", "final"], default="none")
    parser.add_argument("--still", action="store_true")
    parser.add_argument("--resolution", type=int, default=720, help="height in pixels")
    return parser.parse_args(argv)
