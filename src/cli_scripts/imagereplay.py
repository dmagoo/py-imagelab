"""CLI for imagemutate App.

See image mutate for examples
"""
import sys
import json
import argparse
import os
import pathlib
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from apps import imagereplay    # noqa: E402

DEFAULT_SAVE_TEMPLATE = "%PREFIX-%RUN%FRAME%CHILDREN%GENERATION"


def get_arg_parser():
    """Parse and return command line options for image replay"""
    parser = argparse.ArgumentParser(
        description=""" Runs a saved imagelab file. Arrow keys can scrub through
        the history. Hitting spacebar will save current image.""",
        prog='imagereplay'
    )
    parser.add_argument("input_path", type=pathlib.Path,
                        help="""Path to saved data""")
    parser.add_argument("-d", "--save-directory", default=".",
                        help="location of output [d]irectory")
    parser.add_argument("-t", "--save-template", default=DEFAULT_SAVE_TEMPLATE,
                        help="""[t]emplate for naming output files.
                        Supports simple template naming schemes.
                        %%PREFIX, %%GENERATION, %%CHILDREN, %%FRAME
                        (for movies)"""
                        )
    parser.add_argument("-p", "--prefix", default="img",
                        help="[p]repend output files with this"
                        )
    parser.add_argument("-I", "--iconify", default=False, action="store_true",
                        help="[i]conify (minimize graphic display)")
    parser.add_argument("-v", "--verbose", default=False, action="store_true",
                        help="""[v]erbose - more output."""
                        )

    parser.add_argument(
        '-C',
        '--config-file',
        type=str,
        default=None,
        help="""A base config file, which provides alternate defaults which can
        be overridden with their corresponding options and exit.""",
    )
    parser.add_argument(
        '-O',
        '--output-config',
        action="store_true",
        help="""Output the resulting configuration (excluding this option) and
            exit the application """
    )
    return parser


def run():
    """Run the image mutate app from the CLI"""
    parser = get_arg_parser()
    args = parser.parse_args()
    options = vars(args)

    # TODO: support correct conversion of shapes to Constants
    # right now the constant value gets imported/exported from/to JSON...
    if args.config_file is not None:
        print("loading config")
        print(args.config_file)
        with open(args.config_file, 'r') as f:
            config = json.load(f)
            options.update(config)

    if options.get('output_config'):
        options.pop('output_config')
        print(json.dumps(options, indent=4))
        sys.exit(0)

    app = imagereplay.App(options)
    app.run()
    sys.exit(0)
