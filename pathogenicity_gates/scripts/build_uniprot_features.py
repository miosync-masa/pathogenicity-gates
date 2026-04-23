#!/usr/bin/env python3
"""
build_uniprot_features.py
=========================
Re-generate <protein>_uniprot_features.json from UniProt REST API.

Usage:
    python -m pathogenicity_gates.scripts.build_uniprot_features \\
        --protein p53 --out pathogenicity_gates/data/p53/p53_uniprot_features.json

    python -m pathogenicity_gates.scripts.build_uniprot_features \\
        --uniprot P01116 --out kras_uniprot_features.json
"""
import json
import urllib.request
import argparse

UNIPROT_URL_TEMPLATE = "https://rest.uniprot.org/uniprotkb/{uid}.json"

PROTEIN_UNIPROT_MAP = {
    'p53':   'P04637',
    'kras':  'P01116',
    'tdp43': 'Q13148',
    'brca1': 'P38398',
}


def fetch_uniprot_entry(uniprot_id: str) -> dict:
    url = UNIPROT_URL_TEMPLATE.format(uid=uniprot_id)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def build_features(entry: dict) -> dict:
    out = {"ptm": {}, "binding": {}, "domains": {}, "active": {}}
    for f in entry.get("features", []):
        t = f["type"]
        loc = f["location"]
        start = loc["start"]["value"]
        end = loc["end"]["value"]
        desc = f.get("description", "")
        if t == "Modified residue":
            out["ptm"][str(start)] = desc
        elif t == "Cross-link":
            out["ptm"][str(start)] = f"CrossLink: {desc}"
        elif t == "DNA binding":
            for p in range(start, end + 1):
                out["binding"][str(p)] = f"DNA_binding: {desc}"
        elif t == "Binding site":
            out["binding"][str(start)] = f"Binding: {desc}"
        elif t == "Domain":
            out["domains"][f"{start}-{end}"] = desc
        elif t == "Active site":
            out["active"][str(start)] = desc
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protein', choices=list(PROTEIN_UNIPROT_MAP.keys()))
    parser.add_argument('--uniprot', help='UniProt ID (if --protein not given)')
    parser.add_argument('--out', required=True, help='Output JSON path')
    args = parser.parse_args()

    uid = args.uniprot or (PROTEIN_UNIPROT_MAP.get(args.protein) if args.protein else None)
    if not uid:
        raise ValueError("Must specify --protein or --uniprot")

    print(f"Fetching UniProt {uid} ...")
    entry = fetch_uniprot_entry(uid)
    print(f"  feature count: {len(entry.get('features', []))}")

    out = build_features(entry)
    print(f"  ptm entries:     {len(out['ptm'])}")
    print(f"  binding entries: {len(out['binding'])}")
    print(f"  domain entries:  {len(out['domains'])}")
    print(f"  active entries:  {len(out['active'])}")

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"Saved: {args.out}")


if __name__ == '__main__':
    main()
