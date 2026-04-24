"""'explain' subcommand: detailed per-channel diagnostics."""
import sys
import json
from ..utils import parse_mutation_args


CHANNEL_DESCRIPTIONS = {
    'Ch01_DNA':        'DNA contact disruption',
    'Ch02_Zn':         'Zn coordination',
    'Ch03_Core':       'Core structural integrity',
    'Ch04_SS':         'Secondary structure propensity',
    'Ch05_Loop':       'Loop Ramachandran',
    'Ch06_PPI':        'PPI interface disruption',
    'Ch07_PTM':        'PTM site (universal)',
    'Ch08_Oligomer':   'Oligomer interface',
    'Ch09_SaltBridge': 'Salt bridge network',
    'Ch10_SLiM':       'SLiM motif (IDR)',
    'Ch11_IDR_Pro':    'IDR Pro constraint',
    'Ch12_IDR_Gly':    'IDR Gly freedom',
}


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        'explain',
        help='Show per-channel firing details for a variant',
        description='Detailed diagnostic output: per-channel states, '
                    'residue context, and physical interpretation.',
    )
    parser.add_argument('--protein', help='Bundled protein name')
    parser.add_argument('--annotation', help='Path to custom annotation.yaml')
    parser.add_argument('--mutation', '-m', nargs='+', required=True)
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Dump full residue context as JSON')
    parser.add_argument('--channels-only', action='store_true',
                        help='Suppress residue context section')
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

    # Phase 5 fix: explain always uses channels mode -> legacy-free build.
    try:
        if args.protein:
            pred = Predictor.from_protein(args.protein, legacy_impl=False)
        else:
            pred = Predictor.from_yaml(args.annotation, legacy_impl=False)
    except Exception as e:
        print(f"ERROR: Failed to load predictor: {e}", file=sys.stderr)
        sys.exit(1)

    result = pred.predict(pos, wt, mt, mode='channels')
    protein_name = args.protein or (
        pred._annotation.name.lower() if pred._annotation else '?'
    )
    variant = f"{wt}{pos}{mt}"
    pred_str = result['prediction']
    marker = '*' if pred_str == 'Pathogenic' else ' '

    bar = '=' * 60
    print(bar)
    print(f"  Variant: {variant} ({protein_name})")
    print(f"  Position: {pos}  WT: {wt}  MT: {mt}")
    print(f"  Regime: {result.get('regime', '-')}")
    print(f"  Prediction: {marker} {pred_str}")
    print(f"  n_closed: {result['n_closed']}")
    print(bar)

    print()
    regime = result.get('regime', '-')
    print(f"Active Channels (regime={regime} + universal):")
    channels = result.get('channels', {})
    fired = []
    for ch_id in sorted(channels.keys()):
        state = channels[ch_id]
        desc = CHANNEL_DESCRIPTIONS.get(ch_id, '')
        word = {'C': 'CLOSED', 'P': 'PARTIAL', 'O': 'OPEN'}.get(state, state)
        print(f"  [{state}] {ch_id:16s} {word:8s} - {desc}")
        if state == 'C':
            fired.append(ch_id)

    if not args.channels_only:
        print()
        ctx_obj = pred._ctx_obj
        if ctx_obj is None:
            print("(Residue context unavailable in legacy mode)")
        else:
            c = ctx_obj.get_residue(pos)
            if c is not None:
                print(f"Residue Context (pos={pos}):")
                print(f"  WT amino acid:     {c.get('aa', '-')}")
                print(f"  Secondary:         {c.get('ss', '-')} ({_ss_desc(c.get('ss'))})")
                print(f"  Burial:            {c.get('bur', 0):.2f} ({_bur_desc(c.get('bur', 0))})")
                if c.get('d_dna', 999) < 20:
                    print(f"  Distance to DNA:   {c['d_dna']:.1f} A")
                if c.get('d_zn', 999) < 20:
                    print(f"  Distance to Zn:    {c['d_zn']:.1f} A")
                nba = c.get('nba', [])
                if nba:
                    tail = '...' if len(nba) > 10 else ''
                    print(f"  Neighbors:         {nba[:10]}{tail}")
                if args.verbose:
                    print()
                    print("Full residue context:")
                    clean = {k: (list(v) if isinstance(v, list) else v)
                             for k, v in c.items()}
                    print(json.dumps(clean, indent=2, default=str))
            else:
                print(f"Residue Context: (position {pos} not in primary structure)")
                if ctx_obj.is_idr_position(pos):
                    print("  -> Position is in IDR region (no 3D coords needed)")

    print()
    print("Summary:")
    if fired:
        print(f"  {len(fired)} channel(s) fired: {', '.join(fired)}")
    else:
        print("  No channels fired (predicted Benign/VUS)")


def _bur_desc(bur: float) -> str:
    if bur > 0.85: return "deeply buried"
    if bur > 0.60: return "buried"
    if bur > 0.40: return "semi-buried"
    return "exposed"


def _ss_desc(ss: str) -> str:
    return {'H': 'helix', 'E': 'strand', 'C': 'coil', 'T': 'turn'}.get(ss, ss or '-')
