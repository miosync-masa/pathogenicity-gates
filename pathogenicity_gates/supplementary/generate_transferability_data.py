#!/usr/bin/env python3
"""
Generate supplementary data for the Transferability Matrix demonstration.

Produces:
  - transferability_predictions.json: predictions for all Phase 4 demo variants
  - transferability_predictions.csv: same data in CSV for paper SI
  - tier_summary.json: per-tier statistics

Usage:
    python -m pathogenicity_gates.supplementary.generate_transferability_data \\
        --out-json supplementary/transferability_predictions.json \\
        --out-csv supplementary/transferability_predictions.csv \\
        --out-summary supplementary/tier_summary.json
"""
import argparse
import json
import csv
import os

from pathogenicity_gates import Predictor


# (pos, wt, mt, label, mechanism, tier, expected_fire)
DEMO_VARIANTS = {
    'p53': [
        (175, 'R', 'H', 'R175H', 'DNA contact + Core', 'SPECIFIC+ADAPTABLE', True),
        (248, 'R', 'W', 'R248W', 'DNA contact',        'SPECIFIC',            True),
        (273, 'R', 'H', 'R273H', 'DNA contact',        'SPECIFIC',            True),
    ],
    'kras': [
        (117, 'K', 'N', 'K117N', 'charge loss',        'ADAPTABLE',           True),
        (146, 'A', 'T', 'A146T', 'helix strain',       'ADAPTABLE',           True),
        (12,  'G', 'V', 'G12V',  'catalytic Gly',      'FUTURE (catalytic)',  False),
        (12,  'G', 'D', 'G12D',  'catalytic Gly',      'FUTURE (catalytic)',  False),
        (13,  'G', 'D', 'G13D',  'catalytic Gly',      'FUTURE (catalytic)',  False),
    ],
    'tdp43': [
        (294, 'G', 'A', 'G294A', 'IDR Gly loss',       'UNIVERSAL',           True),
        (295, 'G', 'V', 'G295V', 'IDR Gly loss',       'UNIVERSAL',           True),
        (348, 'G', 'C', 'G348C', 'IDR Gly loss',       'UNIVERSAL',           True),
        (390, 'N', 'D', 'N390D', 'IDR charge intro',   'UNIVERSAL',           True),
        (315, 'A', 'T', 'A315T', 'LCD β-branch',       'FUTURE (LLPS)',       False),
        (382, 'A', 'T', 'A382T', 'LCD β-branch',       'FUTURE (LLPS)',       False),
    ],
    'brca1': [
        (61,   'C', 'G', 'C61G',   'RING Zn via Ch03',      'ADAPTABLE', True),
        (64,   'C', 'R', 'C64R',   'RING Zn + charge',      'ADAPTABLE', True),
        (37,   'T', 'R', 'T37R',   'charge intro',          'ADAPTABLE', True),
        (1696, 'V', 'L', 'V1696L', 'BRCT buried',           'ADAPTABLE', True),
        (1702, 'K', 'N', 'K1702N', 'BRCT charge loss',      'ADAPTABLE', True),
        (1775, 'M', 'R', 'M1775R', 'BRCT sulfur + charge',  'ADAPTABLE', True),
        (1697, 'C', 'R', 'C1697R', 'BRCT charge intro',     'ADAPTABLE', True),
        (1708, 'A', 'E', 'A1708E', 'BRCT charge intro',     'ADAPTABLE', True),
    ],
}


def run_predictions():
    """Run predictions for all demo variants."""
    results = []
    for protein, variants in DEMO_VARIANTS.items():
        pred = Predictor.from_protein(protein)
        for pos, wt, mt, label, mechanism, tier, expected in variants:
            r = pred.predict(pos, wt, mt, mode="channels")
            fired_channels = [
                ch_id for ch_id, state in r['channels'].items() if state == 'C'
            ]
            results.append({
                'protein': protein,
                'variant': label,
                'position': pos,
                'wt': wt,
                'mt': mt,
                'mechanism': mechanism,
                'tier': tier,
                'expected_firing': expected,
                'regime': r.get('regime', 'unknown'),
                'n_closed': r['n_closed'],
                'prediction': r['prediction'],
                'fired_channels': fired_channels,
                'fire_matches_expectation':
                    (r['n_closed'] >= 1) == expected,
            })
    return results


def compute_tier_summary(results):
    """Compute per-tier success statistics."""
    tiers = {}
    for r in results:
        tier = r['tier']
        if tier not in tiers:
            tiers[tier] = {'total': 0, 'fired': 0, 'variants': []}
        tiers[tier]['total'] += 1
        if r['n_closed'] >= 1:
            tiers[tier]['fired'] += 1
        tiers[tier]['variants'].append(f"{r['protein']}:{r['variant']}")

    for tier, data in tiers.items():
        data['success_rate'] = data['fired'] / max(1, data['total'])

    return tiers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-json', required=True)
    parser.add_argument('--out-csv', required=True)
    parser.add_argument('--out-summary', required=True)
    args = parser.parse_args()

    print("Running predictions for all demonstration variants...")
    results = run_predictions()

    os.makedirs(os.path.dirname(os.path.abspath(args.out_json)) or '.', exist_ok=True)
    with open(args.out_json, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {args.out_json}")

    with open(args.out_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'protein', 'variant', 'position', 'wt', 'mt',
            'mechanism', 'tier', 'expected_firing', 'regime',
            'n_closed', 'prediction', 'fired_channels',
            'fire_matches_expectation',
        ])
        writer.writeheader()
        for r in results:
            r_csv = dict(r)
            r_csv['fired_channels'] = ';'.join(r['fired_channels'])
            writer.writerow(r_csv)
    print(f"Saved: {args.out_csv}")

    summary = compute_tier_summary(results)
    with open(args.out_summary, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {args.out_summary}")

    print("\n" + "=" * 60)
    print("Transferability Demonstration Summary")
    print("=" * 60)
    for tier, data in summary.items():
        print(f"\n{tier}:")
        print(f"  {data['fired']}/{data['total']} fired "
              f"({100*data['success_rate']:.1f}%)")


if __name__ == '__main__':
    main()
