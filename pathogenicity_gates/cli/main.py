"""
pathogenicity-gates CLI entry point.

Usage:
    pathogenicity-gates <subcommand> [options]

Subcommands:
    predict          Predict a single missense variant
    predict-batch    Predict from a CSV/JSON/TSV file
    explain          Show per-channel firing details
    list-proteins    List bundled protein annotations
"""
import argparse
import sys

from pathogenicity_gates import __version__
from .commands import register_all


def build_parser():
    parser = argparse.ArgumentParser(
        prog='pathogenicity-gates',
        description=(
            'Zero-parameter first-principles pathogenicity prediction '
            'via the Gate & Channel framework.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--version', action='version',
                        version=f'pathogenicity-gates {__version__}')

    subparsers = parser.add_subparsers(
        dest='subcommand', metavar='<subcommand>',
        help='Run `pathogenicity-gates <subcommand> --help` for details'
    )
    register_all(subparsers)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand is None or not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
