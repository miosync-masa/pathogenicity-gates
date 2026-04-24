"""'predict' subcommand: single variant prediction."""
import sys
from ..utils import parse_mutation_args
from ..formatters import get_formatter


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        'predict',
        help='Predict a single missense variant',
        description='Predict pathogenicity for a single missense variant '
                    'using the Gate & Channel framework.',
    )
    parser.add_argument('--protein', help='Bundled protein name (p53, kras, tdp43, brca1)')
    parser.add_argument('--annotation', help='Path to custom annotation.yaml')
    parser.add_argument('--mutation', '-m', nargs='+', required=True,
                        help="Mutation (e.g. 'R175H' or '175 R H')")
    parser.add_argument('--format', '-f', default='compact',
                        choices=['json', 'table', 'compact'],
                        help='Output format (default: compact)')
    parser.add_argument('--mode', default='channels',
                        choices=['channels', 'legacy'],
                        help='Prediction mode (default: channels)')
    parser.set_defaults(func=run)


def run(args):
    from pathogenicity_gates import Predictor

    if not args.protein and not args.annotation:
        print("ERROR: --protein or --annotation required", file=sys.stderr)
        sys.exit(2)

    try:
        pos, wt, mt = parse_mutation_args(args)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        if args.protein:
            pred = Predictor.from_protein(args.protein)
        else:
            pred = Predictor.from_yaml(args.annotation)
    except Exception as e:
        print(f"ERROR: Failed to load predictor: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = pred.predict(pos, wt, mt, mode=args.mode)
    except Exception as e:
        print(f"ERROR: Prediction failed: {e}", file=sys.stderr)
        sys.exit(1)

    result['protein'] = args.protein or (
        pred._annotation.name.lower() if pred._annotation else '?'
    )
    result['variant'] = f"{wt}{pos}{mt}"

    formatter = get_formatter(args.format)
    print(formatter.format_single(result))
