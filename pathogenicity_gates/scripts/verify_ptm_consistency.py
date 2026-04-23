#!/usr/bin/env python3
"""
verify_ptm_consistency.py
=========================
Compare v17-baseline PTM_SITES (from annotation.yaml) against
UniProt REST-derived features (from *_uniprot_features.json).

Generates a markdown report with:
  - Matches (aa + mod_type agree)
  - AA mismatches
  - Type mismatches
  - Only in v17 (not annotated by UniProt)
  - Only in UniProt (v17 may be missing sites)

Usage:
    python -m pathogenicity_gates.scripts.verify_ptm_consistency \\
        --annotation pathogenicity_gates/data/p53/annotation.yaml \\
        --out pathogenicity_gates/data/p53/ptm_consistency_report.md

Output is INFORMATIONAL. The v17 baseline is authoritative for Phase 2/3
(v18 reproducibility must be preserved). Discrepancies are logged for
Phase 4 review and Methods section of the paper.
"""
import argparse
import json
import os
import sys


def parse_uniprot_description(desc: str) -> dict:
    """Parse a UniProt feature description to structured fields."""
    d = desc.lower()
    result = {'aa_letter': None, 'mod_type': None, 'enzymes': []}

    if 'phosphoserine' in d:
        result['aa_letter'] = 'S'; result['mod_type'] = 'phospho'
    elif 'phosphothreonine' in d:
        result['aa_letter'] = 'T'; result['mod_type'] = 'phospho'
    elif 'phosphotyrosine' in d:
        result['aa_letter'] = 'Y'; result['mod_type'] = 'phospho'
    elif 'acetyllysine' in d or 'n6-acetyllysine' in d:
        result['aa_letter'] = 'K'; result['mod_type'] = 'acetyl'
    elif ('methyllysine' in d) or ('dimethylated lysine' in d) or ('n6-methyl' in d and 'lysine' in d) or ('n6,n6' in d):
        result['aa_letter'] = 'K'
        result['mod_type'] = 'dimethyl' if 'dimethyl' in d or 'n6,n6' in d else 'methyl'
    elif 'methylarginine' in d or ('methylated' in d and 'arginine' in d) or ('omega' in d and 'arginine' in d):
        result['aa_letter'] = 'R'
        result['mod_type'] = 'dimethyl' if ('dimethyl' in d or 'omega-n' in d) else 'methyl'
    elif 'crosslink' in d or 'cross-link' in d:
        result['aa_letter'] = 'K'
        if 'sumo' in d:
            result['mod_type'] = 'sumo'
        elif 'ubiquitin' in d or 'isopeptide' in d:
            result['mod_type'] = 'ubiquitin'
    elif 'lactoyl' in d:
        result['aa_letter'] = 'K'; result['mod_type'] = 'lactoyllysine'

    if '; by ' in desc.lower():
        enzyme_str = desc.lower().split('; by ')[1]
        parts = enzyme_str.replace(' and ', ',').split(',')
        result['enzymes'] = [p.strip().upper() for p in parts if p.strip()]

    return result


def verify(yaml_ptm: dict, uniprot_ptm: dict) -> dict:
    matches = []
    aa_mismatches = []
    type_mismatches = []
    only_in_v17 = []
    only_in_uniprot = []

    for pos, yaml_entry in yaml_ptm.items():
        pos_str = str(pos)
        if pos_str not in uniprot_ptm:
            only_in_v17.append({'pos': pos, **yaml_entry})
            continue

        desc = uniprot_ptm[pos_str]
        parsed = parse_uniprot_description(desc)

        if parsed['aa_letter'] is None:
            only_in_v17.append({'pos': pos, **yaml_entry, 'uniprot_raw': desc})
            continue

        if parsed['aa_letter'] != yaml_entry['aa']:
            aa_mismatches.append({
                'pos': pos,
                'yaml_aa': yaml_entry['aa'],
                'uniprot_aa': parsed['aa_letter'],
                'uniprot_desc': desc,
            })
        elif parsed['mod_type'] != yaml_entry['mod']:
            type_mismatches.append({
                'pos': pos,
                'yaml_mod': yaml_entry['mod'],
                'uniprot_mod': parsed['mod_type'],
                'uniprot_desc': desc,
            })
        else:
            matches.append(pos)

    v17_positions = set(yaml_ptm.keys())
    for pos_str, desc in uniprot_ptm.items():
        pos = int(pos_str)
        if pos not in v17_positions:
            only_in_uniprot.append({'pos': pos, 'uniprot_desc': desc})

    return {
        'matches': matches,
        'aa_mismatches': aa_mismatches,
        'type_mismatches': type_mismatches,
        'only_in_v17': only_in_v17,
        'only_in_uniprot': only_in_uniprot,
    }


def generate_markdown_report(result: dict, yaml_path: str, uniprot_path: str) -> str:
    lines = [
        "# PTM Consistency Report",
        "",
        f"**Annotation**: `{os.path.basename(yaml_path)}`",
        f"**UniProt data**: `{os.path.basename(uniprot_path)}`",
        "",
        "## Summary",
        "",
        f"- Matches: **{len(result['matches'])}**",
        f"- AA mismatches: **{len(result['aa_mismatches'])}**",
        f"- Type mismatches: **{len(result['type_mismatches'])}**",
        f"- Only in annotation (not in UniProt): **{len(result['only_in_v17'])}**",
        f"- Only in UniProt (not in annotation): **{len(result['only_in_uniprot'])}**",
        "",
    ]

    lines.append("## Matches")
    lines.append("")
    lines.append("Positions where annotation and UniProt agree on both AA and modification type.")
    lines.append("")
    lines.append(f"`{sorted(result['matches'])}`")
    lines.append("")

    if result['aa_mismatches']:
        lines.append("## AA mismatches")
        lines.append("")
        lines.append("| Position | Annotation AA | UniProt AA | UniProt Description |")
        lines.append("|---------:|--------------:|-----------:|---------------------|")
        for m in result['aa_mismatches']:
            lines.append(
                f"| {m['pos']} | {m['yaml_aa']} | {m['uniprot_aa']} | {m['uniprot_desc']} |"
            )
        lines.append("")

    if result['type_mismatches']:
        lines.append("## Modification type mismatches")
        lines.append("")
        lines.append("| Position | Annotation mod | UniProt mod | UniProt Description |")
        lines.append("|---------:|---------------:|------------:|---------------------|")
        for m in result['type_mismatches']:
            lines.append(
                f"| {m['pos']} | {m['yaml_mod']} | {m['uniprot_mod']} | {m['uniprot_desc']} |"
            )
        lines.append("")

    if result['only_in_v17']:
        lines.append("## Only in annotation (not annotated by UniProt)")
        lines.append("")
        lines.append("These PTM sites are in the v17 baseline but not in UniProt data.")
        lines.append("They may be literature-derived or experimental-only annotations.")
        lines.append("")
        lines.append("| Position | AA | Modification | Enzyme |")
        lines.append("|---------:|---:|:-------------|:-------|")
        for entry in sorted(result['only_in_v17'], key=lambda e: e['pos']):
            lines.append(
                f"| {entry['pos']} | {entry['aa']} | {entry['mod']} | {entry.get('enzyme', '-')} |"
            )
        lines.append("")

    if result['only_in_uniprot']:
        lines.append("## Only in UniProt (not in annotation)")
        lines.append("")
        lines.append("These PTM sites are in UniProt but not in the v17 baseline annotation.")
        lines.append("**Consider adding these in Phase 4.**")
        lines.append("")
        lines.append("| Position | UniProt Description |")
        lines.append("|---------:|---------------------|")
        for entry in sorted(result['only_in_uniprot'], key=lambda e: e['pos']):
            lines.append(f"| {entry['pos']} | {entry['uniprot_desc']} |")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "This report is **informational only**. The annotation YAML is the "
        "authoritative source for Gate & Channel prediction in Phase 2/3 "
        "(maintains v18 FINAL byte-level compatibility). Discrepancies logged "
        "here will be reviewed in Phase 4 when extending to additional proteins."
    )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation', required=True, help='Path to annotation.yaml')
    parser.add_argument('--out', required=True, help='Output markdown report path')
    args = parser.parse_args()

    from ..annotations.loader import load_annotation
    ann = load_annotation(args.annotation)

    if ann.uniprot_features_file is None:
        print("ERROR: annotation.yaml has no uniprot_features_file reference")
        sys.exit(1)

    with open(ann.uniprot_features_file) as f:
        uniprot_data = json.load(f)
    uniprot_ptm = uniprot_data.get('ptm', {})

    result = verify(ann.ptm_sites, uniprot_ptm)
    report = generate_markdown_report(result, args.annotation, ann.uniprot_features_file)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w') as f:
        f.write(report)

    print(f"Saved: {args.out}")
    print(f"\nSummary:")
    print(f"  Matches:          {len(result['matches'])}")
    print(f"  AA mismatches:    {len(result['aa_mismatches'])}")
    print(f"  Type mismatches:  {len(result['type_mismatches'])}")
    print(f"  Only in v17:      {len(result['only_in_v17'])}")
    print(f"  Only in UniProt:  {len(result['only_in_uniprot'])}")


if __name__ == '__main__':
    main()
