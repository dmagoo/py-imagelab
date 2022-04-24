"""CLI for merge App.

"""
import sys
import pathlib
import argparse
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from apps import imagemerge    # noqa: E402


def get_arg_parser():
    """Parse and return command line options for image merger"""
    parser = argparse.ArgumentParser(
        description=""" Runs merger on all images in a directory or
        a list of file.""",
        prog='averager'
    )
    parser.add_argument("target_path", nargs="+", type=pathlib.Path,
                        help="""Paths to images or a directory""")
    parser.add_argument("-o", "--output_file",
                        help="""[o]utput file name. Will try to create image in
                         the format of the given extension (png, bmp, jpg)"""
                        )
    parser.add_argument("-I", "--iconify", default=False, action="store_true",
                        help="[i]conify (minimize graphic display)")
    parser.add_argument("-v", "--verbose", default=False, action="store_true",
                        help="""[v]erbose - more output."""
                        )
    parser.add_argument("-N", "--no-display", default=False,
                        action="store_true", help="""[N]o display.
                        Don't show results in realtime"""
                        )
    return parser


def run():
    """Run the image merger app from the CLI"""
    parser = get_arg_parser()
    args = parser.parse_args()
    app = imagemerge.App(vars(args))
    app.run()
    sys.exit(0)
