"""'list-proteins' subcommand: list bundled annotations."""
import os
from ..formatters import get_formatter


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        'list-proteins',
        help='List all bundled protein annotations',
    )
    parser.add_argument('--format', '-f', default='table',
                        choices=['json', 'table', 'compact'],
                        help='Output format (default: table)')
    parser.set_defaults(func=run)


def run(args):
    from pathogenicity_gates import Predictor
    from pathogenicity_gates.annotations.loader import load_annotation
    import pathogenicity_gates

    proteins = Predictor.list_bundled_proteins()

    pkg_dir = os.path.dirname(os.path.abspath(pathogenicity_gates.__file__))
    annotations = {}
    for name in proteins:
        try:
            yaml_path = os.path.join(pkg_dir, 'data', name, 'annotation.yaml')
            ann = load_annotation(yaml_path)
            annotations[name] = ann
        except Exception:
            annotations[name] = None

    formatter = get_formatter(args.format)
    print(formatter.format_list_proteins(proteins, annotations))
