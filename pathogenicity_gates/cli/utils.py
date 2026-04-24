"""
Utility functions for the CLI.

Parsing mutation strings and variant file formats.
"""
import re
from typing import List, Tuple


MUTATION_PATTERN = re.compile(r'^([A-Z])(\d+)([A-Z])$')

_POS_ALIASES = {'position', 'pos', 'residue'}
_WT_ALIASES = {'wt', 'wildtype', 'wild_type', 'wild-type', 'reference', 'ref'}
_MT_ALIASES = {'mt', 'mutant', 'alt', 'alternative', 'alternate'}


def parse_mutation_string(mutation: str) -> Tuple[int, str, str]:
    """Parse 'R175H' into (175, 'R', 'H').

    Raises:
        ValueError: if format is invalid.
    """
    mutation = mutation.strip().upper()
    match = MUTATION_PATTERN.match(mutation)
    if not match:
        raise ValueError(
            f"Invalid mutation format: '{mutation}'. "
            f"Expected <WT><POS><MT>, e.g. 'R175H'."
        )
    wt, pos, mt = match.groups()
    return int(pos), wt, mt


def parse_mutation_args(args) -> Tuple[int, str, str]:
    """Parse mutation from argparse Namespace (args.mutation is a list).

    Accepts:
      --mutation R175H      (1 arg: single string)
      --mutation 175 R H    (3 args: pos/wt/mt)
      --mutation R 175 H    (3 args: wt/pos/mt)
    """
    m = args.mutation
    if len(m) == 1:
        return parse_mutation_string(m[0])
    if len(m) == 3:
        a, b, c = m
        try:
            return int(a), b.upper(), c.upper()
        except ValueError:
            try:
                return int(b), a.upper(), c.upper()
            except ValueError:
                raise ValueError(
                    f"Cannot parse --mutation args {m}. "
                    f"Expected 'R175H' or '175 R H' or 'R 175 H'."
                )
    raise ValueError(
        f"--mutation accepts 1 or 3 arguments, got {len(m)}: {m}"
    )


def parse_variants_csv(path: str) -> List[Tuple[int, str, str]]:
    """Parse CSV/TSV into a list of (pos, wt, mt).

    Header row required with columns matching _POS/WT/MT_ALIASES.
    Delimiter auto-detected (',' or '\\t').
    """
    import csv

    with open(path, newline='') as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',\t')
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)

        fieldnames = {fn.lower().strip(): fn for fn in (reader.fieldnames or [])}
        pos_col = next((fn for low, fn in fieldnames.items() if low in _POS_ALIASES), None)
        wt_col = next((fn for low, fn in fieldnames.items() if low in _WT_ALIASES), None)
        mt_col = next((fn for low, fn in fieldnames.items() if low in _MT_ALIASES), None)

        if not (pos_col and wt_col and mt_col):
            raise ValueError(
                f"CSV must have columns for position/wt/mt. "
                f"Found: {list(fieldnames.values())}"
            )

        variants = []
        for row in reader:
            pos = int(row[pos_col])
            wt = row[wt_col].strip().upper()
            mt = row[mt_col].strip().upper()
            variants.append((pos, wt, mt))
    return variants


def parse_variants_json(path: str) -> List[Tuple[int, str, str]]:
    """Parse JSON into a list of (pos, wt, mt)."""
    import json

    with open(path) as f:
        data = json.load(f)

    variants = []
    for entry in data:
        if isinstance(entry, dict):
            pos = int(entry.get('position') or entry.get('pos'))
            wt_raw = entry.get('wt') or entry.get('wildtype') or entry.get('reference') or entry.get('ref')
            mt_raw = entry.get('mt') or entry.get('mutant') or entry.get('alt')
            if wt_raw is None or mt_raw is None:
                raise ValueError(f"Entry missing wt/mt: {entry}")
            variants.append((pos, wt_raw.upper(), mt_raw.upper()))
        elif isinstance(entry, str):
            variants.append(parse_mutation_string(entry))
        else:
            raise ValueError(f"Unknown variant entry format: {entry}")
    return variants


def parse_variants_file(path: str) -> List[Tuple[int, str, str]]:
    """Auto-detect and parse a variant file (.json, .csv, .tsv)."""
    lower = path.lower()
    if lower.endswith('.json'):
        return parse_variants_json(path)
    if lower.endswith(('.csv', '.tsv', '.txt')):
        return parse_variants_csv(path)
    try:
        return parse_variants_csv(path)
    except Exception:
        return parse_variants_json(path)
