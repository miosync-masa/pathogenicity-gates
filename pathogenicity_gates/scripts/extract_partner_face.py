#!/usr/bin/env python3
"""
extract_partner_face.py
=======================
Extract p53 TAD interface residues from 6 partner complex PDB structures.
Output: partner_face.json with the union of interface residues (cutoff 5.0 Å).

Usage:
    python3 extract_partner_face.py

Required PDB files (place in same directory or specify path):
    1YCR.pdb   MDM2 × p53 TAD1                   (X-ray, 2-chain)
    5HPD.pdb   CBP TAZ2 × p53 TAD (full)         (NMR, fusion protein)
    5HOU.pdb   CBP TAZ1 × p53 TAD (full)         (NMR, fusion protein)
    2L14.pdb   CBP NCBD × p53 TAD                (NMR, 2-chain)
    2K8F.pdb   p300 TAZ2 × p53 TAD1              (NMR, 2-chain)
    2MZD.pdb   p300 TAZ2 × p53 TAD2              (NMR, 2-chain)

Download from RCSB: https://files.rcsb.org/download/{PDB_ID}.pdb

Output files:
    partner_face.json      : union of interface residues (p53 standard numbering)
"""
import os
import numpy as np
from collections import defaultdict
import json

THREE_TO_ONE = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C',
    'GLN':'Q','GLU':'E','GLY':'G','HIS':'H','ILE':'I',
    'LEU':'L','LYS':'K','MET':'M','PHE':'F','PRO':'P',
    'SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
}

# Reference sequence for p53 TAD (residues 1-61)
P53_TAD_SEQ = 'MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPD'


def parse_pdb_atoms(path, model=1):
    """Parse heavy atoms from PDB (model 1 only for NMR ensembles)."""
    atoms = []
    current_model = 1
    in_target_model = True
    with open(path) as f:
        for line in f:
            if line.startswith('MODEL'):
                try:
                    current_model = int(line.split()[1])
                    in_target_model = (current_model == model)
                except Exception:
                    pass
                continue
            if line.startswith('ENDMDL'):
                in_target_model = False
                continue
            if not in_target_model:
                continue
            if not line.startswith(('ATOM', 'HETATM')):
                continue
            atom_name = line[12:16].strip()
            if atom_name.startswith('H'):
                continue
            try:
                chain   = line[21]
                resnum  = int(line[22:26])
                resname = line[17:20].strip()
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
            except Exception:
                continue
            if resname not in THREE_TO_ONE:
                continue
            atoms.append({
                'chain': chain, 'resnum': resnum, 'resname': resname,
                'atom': atom_name, 'x': x, 'y': y, 'z': z,
            })
    return atoms


def identify_p53_subregion_in_fusion(atoms):
    """
    For fusion proteins (TAZ-linker-TAD single chain), identify which residues
    belong to the p53 portion by matching to the reference p53 TAD sequence.

    Returns: {chain: {pdb_resnum: p53_standard_resnum}}
    """
    chain_seqs = defaultdict(dict)
    for a in atoms:
        chain_seqs[a['chain']][a['resnum']] = THREE_TO_ONE.get(a['resname'], 'X')

    results = defaultdict(dict)
    for ch, seq_map in chain_seqs.items():
        resnums = sorted(seq_map.keys())
        if not resnums:
            continue
        i = 0
        while i < len(resnums):
            window_residues = [resnums[i]]
            j = i + 1
            while j < len(resnums) and resnums[j] == resnums[j-1] + 1:
                window_residues.append(resnums[j])
                j += 1
            window_seq = ''.join(seq_map[r] for r in window_residues)
            best_start, best_len = None, 0
            for start in range(len(window_seq)):
                for end in range(start + 10, len(window_seq) + 1):
                    if window_seq[start:end] in P53_TAD_SEQ:
                        if end - start > best_len:
                            best_start, best_len = start, end - start
                    else:
                        break
            if best_start is not None:
                matched_seq = window_seq[best_start:best_start + best_len]
                p53_offset = P53_TAD_SEQ.find(matched_seq)
                if p53_offset >= 0:
                    for k in range(best_len):
                        pdb_res = window_residues[best_start + k]
                        p53_std = p53_offset + 1 + k
                        results[ch][pdb_res] = p53_std
            i = j
    return results


def compute_interface_two_chain(atoms, p53_chain, partner_chain, cutoff=5.0):
    """2-chain structures: compute min heavy-atom distance from p53 to partner."""
    p53_atoms = [a for a in atoms if a['chain'] == p53_chain]
    partner_atoms = [a for a in atoms if a['chain'] == partner_chain]
    if not partner_atoms:
        return []
    p_xyz = np.array([[a['x'], a['y'], a['z']] for a in partner_atoms])
    interface = {}
    for a in p53_atoms:
        d = np.sqrt(((p_xyz - np.array([a['x'], a['y'], a['z']]))**2).sum(axis=1)).min()
        if d <= cutoff:
            if a['resnum'] not in interface or d < interface[a['resnum']]['d']:
                interface[a['resnum']] = {
                    'resname': a['resname'],
                    'aa': THREE_TO_ONE.get(a['resname'], 'X'),
                    'd': float(d),
                }
    return sorted(interface.items())


def compute_interface_fusion(atoms, p53_map_by_chain, cutoff=5.0):
    """Fusion proteins: use p53 mapping to separate p53 atoms from partner atoms."""
    p53_atoms, partner_atoms = [], []
    for a in atoms:
        if a['chain'] in p53_map_by_chain and a['resnum'] in p53_map_by_chain[a['chain']]:
            p53_atoms.append(a)
        else:
            partner_atoms.append(a)
    if not partner_atoms:
        return []
    p_xyz = np.array([[a['x'], a['y'], a['z']] for a in partner_atoms])
    interface = {}
    for a in p53_atoms:
        d = np.sqrt(((p_xyz - np.array([a['x'], a['y'], a['z']]))**2).sum(axis=1)).min()
        if d <= cutoff:
            std_res = p53_map_by_chain[a['chain']][a['resnum']]
            if std_res not in interface or d < interface[std_res]['d']:
                interface[std_res] = {
                    'resname': a['resname'],
                    'aa': THREE_TO_ONE.get(a['resname'], 'X'),
                    'd': float(d),
                }
    return sorted(interface.items())


def guess_p53_chain_2chain(atoms):
    """For 2-chain structures, find which chain has p53 by sequence similarity."""
    chain_info = defaultdict(lambda: {'res_nums': set(), 'seq': {}})
    for a in atoms:
        chain_info[a['chain']]['res_nums'].add(a['resnum'])
        chain_info[a['chain']]['seq'][a['resnum']] = THREE_TO_ONE.get(a['resname'], 'X')

    candidates = []
    for ch, info in chain_info.items():
        resnums = sorted(info['res_nums'])
        seq_str = ''.join(info['seq'][r] for r in resnums)
        # k-mer similarity to p53 TAD
        k = 5
        similarity = 0
        if len(seq_str) >= k:
            for i in range(len(seq_str) - k + 1):
                if seq_str[i:i+k] in P53_TAD_SEQ:
                    similarity += 1
        candidates.append((ch, similarity, resnums[0] if resnums else 0))
    candidates.sort(key=lambda x: -x[1])
    return candidates


# ══════════════════════════════════════════════════════════════
# Partner structures to analyze
# ══════════════════════════════════════════════════════════════
STRUCTURES = [
    ('1YCR.pdb', 'MDM2'),
    ('5HPD.pdb', 'CBP_TAZ2'),         # Reviewer #1 直接回答
    ('5HOU.pdb', 'CBP_TAZ1'),
    ('2L14.pdb', 'CBP_NCBD'),
    ('2K8F.pdb', 'p300_TAZ2_TAD1'),
    ('2MZD.pdb', 'p300_TAZ2_TAD2'),
]


def main(pdb_dir='.', cutoff=5.0, out_path='partner_face.json'):
    all_interface = {}
    for pdb, name in STRUCTURES:
        path = os.path.join(pdb_dir, pdb)
        if not os.path.exists(path):
            print(f"[WARNING] {path} not found, skipping")
            continue
        atoms = parse_pdb_atoms(path, model=1)
        print(f"\n====== {pdb} ({name}) ======")
        print(f"Heavy atoms (model 1): {len(atoms)}")

        cands = guess_p53_chain_2chain(atoms)
        if len(cands) >= 2 and cands[0][1] > 0:
            # 2-chain structure
            p53_chain = cands[0][0]
            partner_chain = cands[1][0]
            print(f"  → 2-chain: p53='{p53_chain}', partner='{partner_chain}'")
            interface = compute_interface_two_chain(atoms, p53_chain, partner_chain, cutoff)
        else:
            # fusion protein
            print(f"  → fusion protein: identifying p53 subregion by sequence match")
            p53_map = identify_p53_subregion_in_fusion(atoms)
            if not any(p53_map.values()):
                print(f"  ERROR: cannot identify p53 subregion")
                continue
            for ch, m in p53_map.items():
                if m:
                    pdb_rng = (min(m.keys()), max(m.keys()))
                    std_rng = (min(m.values()), max(m.values()))
                    print(f"    chain {ch}: PDB {pdb_rng[0]}-{pdb_rng[1]} → p53 std {std_rng[0]}-{std_rng[1]} ({len(m)} res)")
            interface = compute_interface_fusion(atoms, p53_map, cutoff)

        positions = [p for p, _ in interface]
        print(f"  Interface residues (cutoff {cutoff} Å): {len(interface)}")
        print(f"    range: {min(positions) if positions else '-'}-{max(positions) if positions else '-'}")
        all_interface[name] = {
            'pdb': pdb,
            'positions': positions,
            'details': [{'pos': p, 'aa': info['aa'], 'dist': info['d']}
                        for p, info in interface],
        }

    # Union
    union = set()
    for name, info in all_interface.items():
        union |= set(info['positions'])

    print("\n" + "="*70)
    print(" UNION of coupled-folding partner faces (p53 standard numbering)")
    print("="*70)
    for name, info in all_interface.items():
        ps = info['positions']
        if ps:
            print(f"  {name:<18} ({info['pdb']}): {len(ps)} residues [{min(ps)}-{max(ps)}]")
    print(f"\n  UNION total: {len(union)} unique residues")
    print(f"  positions: {sorted(union)}")

    with open(out_path, 'w') as f:
        json.dump({
            'union': sorted(union),
            'per_structure': all_interface,
            'cutoff_angstrom': cutoff,
        }, f, indent=2)
    print(f"\n[Saved: {out_path}]")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdb-dir', default='.', help='Directory with PDB files')
    ap.add_argument('--cutoff', type=float, default=5.0, help='Distance cutoff (Å)')
    ap.add_argument('--out', default='partner_face.json')
    args = ap.parse_args()
    main(args.pdb_dir, args.cutoff, args.out)
