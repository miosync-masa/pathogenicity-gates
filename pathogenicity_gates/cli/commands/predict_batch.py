"""'predict-batch' subcommand: batch prediction from file or stdin."""
import sys
import os
from ..utils import parse_variants_file
from ..formatters import get_formatter


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        'predict-batch',
        help='Predict multiple variants from a CSV/JSON/TSV file',
        description='Batch prediction. Reads variants from file or stdin.',
    )
    parser.add_argument('--protein', help='Bundled protein name')
    parser.add_argument('--annotation', help='Path to custom annotation.yaml')
    parser.add_argument('--input', '-i', required=True,
                        help='Input file (CSV/JSON/TSV). Use "-" for stdin.')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--format', '-f', default='json',
                        choices=['json', 'table', 'compact', 'csv'],
                        help='Output format (default: json)')
    parser.add_argument('--mode', default='channels',
                        choices=['channels', 'legacy'])
    parser.set_defaults(func=run)


def run(args):
    from pathogenicity_gates import Predictor

    if not args.protein and not args.annotation:
        print("ERROR: --protein or --annotation required", file=sys.stderr)
        sys.exit(2)

    if args.input == '-':
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as tf:
            tf.write(sys.stdin.read())
            tmp_path = tf.name
        try:
            variants = parse_variants_file(tmp_path)
        except Exception as e:
            print(f"ERROR: Failed to parse stdin: {e}", file=sys.stderr)
            sys.exit(2)
        finally:
            os.unlink(tmp_path)
    else:
        try:
            variants = parse_variants_file(args.input)
        except Exception as e:
            print(f"ERROR: Failed to parse {args.input}: {e}", file=sys.stderr)
            sys.exit(2)

    if not variants:
        print("ERROR: no variants found in input", file=sys.stderr)
        sys.exit(2)

    try:
        if args.protein:
            pred = Predictor.from_protein(args.protein)
        else:
            pred = Predictor.from_yaml(args.annotation)
    except Exception as e:
        print(f"ERROR: Failed to load predictor: {e}", file=sys.stderr)
        sys.exit(1)

    protein_name = args.protein or (
        pred._annotation.name.lower() if pred._annotation else '?'
    )

    results = []
    for pos, wt, mt in variants:
        try:
            r = pred.predict(pos, wt, mt, mode=args.mode)
            r['protein'] = protein_name
            r['variant'] = f"{wt}{pos}{mt}"
            results.append(r)
        except Exception as e:
            results.append({
                'protein': protein_name,
                'variant': f"{wt}{pos}{mt}",
                'pos': pos, 'wt': wt, 'mt': mt,
                'prediction': 'Error',
                'n_closed': 0,
                'channels': {},
                'error': str(e),
            })

    if args.format == 'csv':
        output = _format_csv(results)
    else:
        formatter = get_formatter(args.format)
        output = formatter.format_batch(results)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
            if not output.endswith('\n'):
                f.write('\n')
        print(f"Saved: {args.output}", file=sys.stderr)
    else:
        print(output)


def _format_csv(results: list) -> str:
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['protein', 'variant', 'position', 'wt', 'mt',
                     'prediction', 'n_closed', 'regime', 'fired_channels'])
    for r in results:
        fired = [ch for ch, s in r.get('channels', {}).items() if s == 'C']
        writer.writerow([
            r.get('protein', ''),
            r.get('variant', ''),
            r.get('pos', ''),
            r.get('wt', ''),
            r.get('mt', ''),
            r.get('prediction', ''),
            r.get('n_closed', 0),
            r.get('regime', ''),
            ';'.join(fired),
        ])
    return buf.getvalue()
