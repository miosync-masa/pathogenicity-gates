"""
Structure-derived features for the Gate & Channel framework.

Computes:
  - Secondary structure assignment (phi/psi-based, H/E/C)
  - PDB-level features (frac_E, frac_H, core_frac, ACO, nc_p90, charge_density)
  - Cofactor detection (heme, metal ions)

Source: SSOC v3.32 (Iizumi 2026).
"""
import math
import numpy as np
from collections import Counter
from ..physics.geometry import sigmoid


def _dihedral_angle(p1, p2, p3, p4):
    """Internal: compute dihedral angle from 4 atoms (degrees)."""
    b1=p2-p1;b2=p3-p2;b3=p4-p3
    n1=np.cross(b1,b2);n2=np.cross(b2,b3)
    m1=np.cross(n1,b2/max(np.linalg.norm(b2),1e-10))
    return -math.degrees(math.atan2(np.dot(m1,n2),np.dot(n1,n2)))


def assign_ss(backbone):
    """Assign secondary structure from backbone phi/psi angles."""
    srnums = sorted(backbone.keys())
    ss = {}
    for i, rnum in enumerate(srnums):
        bb = backbone[rnum]
        if not all(a in bb for a in ('N','CA','C')):
            ss[rnum] = 'C'; continue
        phi = psi = None
        if i > 0:
            prev = srnums[i-1]
            bbp = backbone.get(prev, {})
            if 'C' in bbp and prev == rnum - 1:
                try: phi = _dihedral_angle(bbp['C'], bb['N'], bb['CA'], bb['C'])
                except: pass
        if i < len(srnums) - 1:
            nxt = srnums[i+1]
            bbn = backbone.get(nxt, {})
            if 'N' in bbn and nxt == rnum + 1:
                try: psi = _dihedral_angle(bb['N'], bb['CA'], bb['C'], bbn['N'])
                except: pass
        if phi is None or psi is None:
            ss[rnum] = 'C'; continue
        if -100 < phi < -30 and -80 < psi < -10: ss[rnum] = 'H'
        elif -170 < phi < -50 and (80 < psi < 180 or -180 < psi < -120): ss[rnum] = 'E'
        elif 30 < phi < 100 and -20 < psi < 60: ss[rnum] = 'T'
        else: ss[rnum] = 'C'
    # Smoothing: isolated H/E -> C
    for i, rnum in enumerate(srnums):
        if ss[rnum] in ('H','E'):
            nbr = []
            if i > 0: nbr.append(ss.get(srnums[i-1],'C'))
            if i < len(srnums)-1: nbr.append(ss.get(srnums[i+1],'C'))
            if ss[rnum] not in nbr: ss[rnum] = 'C'
    return ss


def detect_cofactors(pdb_path):
    """Detect heme/metal cofactors from HETATM lines.
    Returns dict with has_heme, has_metal, has_cofactor."""
    has_heme = False; has_metal = False
    HEME_NAMES = {'HEM', 'HEC', 'HEA', 'HEB'}
    METAL_ATOMS = {'FE', 'ZN', 'CU', 'MN', 'CO', 'NI', 'MG'}
    try:
        with open(pdb_path) as f:
            for line in f:
                if line.startswith('HETATM'):
                    resn = line[17:20].strip()
                    if resn in HEME_NAMES: has_heme = True
                    atom_name = line[12:16].strip()
                    if atom_name in METAL_ATOMS: has_metal = True
    except: pass
    return {'has_heme': has_heme, 'has_metal': has_metal,
            'has_cofactor': has_heme or has_metal}


def compute_pdb_features(atoms, ss_map, backbone, nc_p90=None, pdb_path=None):
    """Compute PDB-level features for phase gate.
    Returns dict with frac_E, frac_H, core_frac, ACO, charge_density, N_res, nc_p90."""
    srnums = sorted(backbone.keys())
    ss_counts = Counter(ss_map.get(rn, 'C') for rn in srnums)
    total_ss = max(1, sum(ss_counts.values()))
    frac_E = ss_counts.get('E', 0) / total_ss
    frac_H = ss_counts.get('H', 0) / total_ss
    # Compute nc_p90 for sigmoid burial
    ncs_all = [sum(1 for rn2, aa2, xyz2 in atoms if rn2 != rnum and np.linalg.norm(xyz2 - xyz) < 8.0)
               for rnum, aa, xyz in atoms]
    if nc_p90 is None:
        nc_p90 = max(8.0, np.percentile(ncs_all, 90))
    # Core fraction using sigmoid burial (x0=0.60, k=10)
    n_core = 0
    for nc_i in ncs_all:
        bur_i = sigmoid(nc_i / nc_p90, 0.60, 10.0)
        if bur_i > 0.7:
            n_core += 1
    core_frac = n_core / max(1, len(atoms))
    # ACO
    seq_seps = []
    for i, (rn1, aa1, xyz1) in enumerate(atoms):
        for j, (rn2, aa2, xyz2) in enumerate(atoms):
            if j <= i: continue
            if np.linalg.norm(xyz1 - xyz2) < 8.0:
                seq_seps.append(abs(rn2 - rn1))
    ACO = np.mean(seq_seps) if seq_seps else 0
    # Charge density
    n_charged = sum(1 for _, aa, _ in atoms if aa in ('D', 'E', 'K', 'R'))
    charge_density = n_charged / max(1, len(atoms))
    # Cofactor detection (v3.30)
    cofactor = detect_cofactors(pdb_path) if pdb_path else {'has_heme': False, 'has_metal': False, 'has_cofactor': False}
    return {
        'frac_E': frac_E, 'frac_H': frac_H, 'core_frac': core_frac,
        'ACO': ACO, 'charge_density': charge_density, 'N_res': len(atoms), 'nc_p90': nc_p90,
        'has_heme': cofactor['has_heme'], 'has_metal': cofactor['has_metal'],
        'has_cofactor': cofactor['has_cofactor']
    }
