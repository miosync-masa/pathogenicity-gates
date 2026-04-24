"""
Legacy-free PredictionContext builder for Phase 3 channels mode.

This module ports v17's setup_core_domain / setup_tetramer / setup_ppi /
setup_salt_bridge logic verbatim, but:
  - imports only from `pathogenicity_gates.structure` and `pathogenicity_gates.physics`
  - does NOT import `pathogenicity_gates.legacy`
  - returns a `PredictionContext` object directly (no intermediate dict)

The logic is **byte-for-byte identical** to the legacy setup functions for
p53, so Phase 3 channels mode produces identical channel states whether
the context is built via `v18_adapter.build_context_from_annotation`
(legacy path) or `direct_builder.build_context_direct` (this path).

Verified by tests/test_no_legacy_leak.py.
"""
import os
import json
import numpy as np

from ..annotations.loader import ProteinAnnotation
from ..channels.context import PredictionContext
from ..physics.constants import AA_CHARGE, POLAR_SET
from ..physics.geometry import sigmoid, place_virtual_CB
from ..physics.corrections import get_helix_position
from ..structure.parser import parse_pdb
from ..structure.features import assign_ss, compute_pdb_features


def build_context_direct(ann: ProteinAnnotation) -> PredictionContext:
    """Build a PredictionContext from a ProteinAnnotation without any
    legacy module imports.

    For proteins without a primary PDB (e.g. TDP-43, IDR-only), the
    returned context has `residue_ctx={}` and IDR channels remain fully
    functional via `annotation.idr_ranges`.
    """
    residue_ctx, atom_xyz_lookup = _build_core_context(ann)
    tet_interface, tet_exposure, tet_chain_contacts = _build_tetramer_context(ann)
    ppi_union, ppi_nb_count = _build_ppi_context(ann, atom_xyz_lookup)
    sb_partners = _build_salt_bridge_context(residue_ctx, atom_xyz_lookup)

    return PredictionContext(
        residue_ctx=residue_ctx,
        ppi_union=ppi_union,
        ppi_nb_count=ppi_nb_count,
        tet_interface=tet_interface,
        tet_exposure=tet_exposure,
        tet_chain_contacts=tet_chain_contacts,
        sb_partners=sb_partners,
        annotation=ann,
    )


# ═══════════════════════════════════════════════════════════════
# Core domain (ports v17.setup_core_domain verbatim)
# ═══════════════════════════════════════════════════════════════

def _build_core_context(ann: ProteinAnnotation):
    """Parse primary PDB, compute per-residue context dict.

    Ported from legacy.p53_gate_v17_idr.setup_core_domain (L266-354).
    Returns (residue_ctx_dict, atom_xyz_lookup).
    """
    if ann.primary_pdb is None or not os.path.exists(ann.primary_pdb):
        return {}, {}

    pdb_path = ann.primary_pdb
    chain = ann.primary_chain or 'A'

    backbone, atoms, all_heavy = parse_pdb(pdb_path, chain=chain)
    ss_map = assign_ss(backbone)
    pdb_feat = compute_pdb_features(atoms, ss_map, backbone, pdb_path=pdb_path)
    nc_p90 = pdb_feat['nc_p90']

    # Zn coordination (p53-specific but generalised: any HETATM ZN on the chain)
    zn_coord = None
    with open(pdb_path) as f:
        for line in f:
            if line.startswith('HETATM') and line[12:16].strip() == 'ZN' and line[21] == chain:
                zn_coord = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
                break

    # Per-residue heavy atoms (for SC->DNA distance computation)
    residue_heavy = {}
    with open(pdb_path) as f:
        for line in f:
            if not line.startswith('ATOM') or line[21] != chain:
                continue
            a = line[12:16].strip()
            if a.startswith('H'):
                continue
            try:
                r = int(line[22:26])
                x = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except Exception:
                continue
            residue_heavy.setdefault(r, []).append((a, x))

    # DNA atoms (chains E/F convention used by 1TSR)
    dna_atoms = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith('ATOM') and line[21] in ('E', 'F'):
                a = line[12:16].strip()
                if a.startswith('H'):
                    continue
                try:
                    dna_atoms.append(np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])]))
                except Exception:
                    continue
    dna_arr = np.array(dna_atoms) if dna_atoms else np.empty((0, 3))

    # Robust to DNA-free structures (Phase 4 guard)
    sc_dna = {}
    has_dna = len(dna_arr) > 0
    for r in {r for r, _, _ in atoms}:
        if has_dna and r in residue_heavy:
            sc_dna[r] = min(np.min(np.linalg.norm(dna_arr - x, axis=1)) for _, x in residue_heavy[r])
        else:
            sc_dna[r] = 999

    atom_xyz_lookup = {r: xyz for r, _, xyz in atoms}

    ctx = {}
    for rn, aa, ca in atoms:
        nb = [(r2, a2, x2) for r2, a2, x2 in atoms if r2 != rn and np.linalg.norm(x2 - ca) < 8.0]
        nc = len(nb)
        nba = [a for _, a, _ in nb]
        bur = sigmoid(nc / nc_p90, 0.60, 10.0)
        npol = sum(1 for a in nba if a in POLAR_SET)
        pf = npol / max(1, nc)
        ss = ss_map.get(rn, 'C')
        nss = [ss_map.get(r2, 'C') for r2, _, _ in nb]
        hnf = sum(1 for s in nss if s == 'H') / max(1, nc)
        bnf = sum(1 for s in nss if s == 'E') / max(1, nc)
        lf = sum(1 for a in nba if a in {'W', 'F', 'Y', 'I', 'L'}) / max(1, nc)
        n_aro = sum(1 for a in nba if a in {'F', 'W', 'Y', 'H'})
        n_sul = sum(1 for a in nba if a in ('M', 'C'))
        n_charged_nb = sum(1 for a in nba if a in 'DEKR')
        dcb = 999.
        nbr = 0
        bb = backbone.get(rn, {})
        if aa == 'G' and all(a in bb for a in ('N', 'CA', 'C')):
            vCB = place_virtual_CB(bb['N'], bb['CA'], bb['C'])
            dcb = min((np.linalg.norm(vCB - x2) for r2, a2, x2 in all_heavy if r2 != rn), default=999)
            nbr = sum(1 for a in nba if a in ('V', 'I', 'T'))
        hpos = get_helix_position(ss_map, rn) if ss == 'H' else 'none'

        ctx[rn] = {
            'aa': aa, 'bur': bur, 'pf': pf, 'ss': ss, 'nba': nba,
            'hnf': hnf, 'bnf': bnf, 'lf': lf, 'n_aro': n_aro, 'n_sul': n_sul,
            'n_charged_nb': n_charged_nb,
            'dcb': dcb, 'nbr': nbr,
            'd_dna': sc_dna.get(rn, 999),
            'd_zn': np.linalg.norm(ca - zn_coord) if zn_coord is not None else 999,
            'hpos': hpos,
        }

    return ctx, atom_xyz_lookup


# ═══════════════════════════════════════════════════════════════
# Tetramer / oligomer (ports v17.setup_tetramer verbatim)
# ═══════════════════════════════════════════════════════════════

def _build_tetramer_context(ann: ProteinAnnotation):
    """Parse oligomer PDB and compute interface/exposure/chain_contacts.

    Ported from legacy.p53_gate_v17_idr.setup_tetramer (L359-422).
    Returns (tet_interface, tet_exposure, tet_chain_contacts).
    """
    if ann.oligomer_pdb is None or not os.path.exists(ann.oligomer_pdb):
        return {}, {}, {}

    pdb_path = ann.oligomer_pdb
    chains = {}
    with open(pdb_path) as f:
        for line in f:
            if not line.startswith('ATOM'):
                continue
            ch = line[21]
            atom = line[12:16].strip()
            resn = line[17:20].strip()
            if atom.startswith('H'):
                continue
            try:
                rnum = int(line[22:26])
                xyz = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except Exception:
                continue
            chains.setdefault(ch, []).append((rnum, atom, resn, xyz))

    # Require at least chains A + B + C + D (tetramer assumption)
    if not all(c in chains for c in ('A', 'B', 'C', 'D')):
        return {}, {}, {}

    partner_arr = np.array([xyz for ch in ['B', 'C', 'D'] for _, _, _, xyz in chains[ch]])

    tet_interface = {}
    tet_ca = {}
    for rnum, atom, resn, xyz in chains['A']:
        if atom == 'CA':
            tet_ca[rnum] = xyz
        d = np.min(np.linalg.norm(partner_arr - xyz, axis=1))
        if d < 4.5:
            if rnum not in tet_interface or d < tet_interface[rnum]:
                tet_interface[rnum] = d

    b_com = np.mean([xyz for _, a, _, xyz in chains['B'] if a == 'CA'], axis=0)
    tet_exposure = {}
    for rnum in tet_ca:
        xyz = tet_ca[rnum]
        vec = b_com - xyz
        n = np.linalg.norm(vec)
        if n < 0.1:
            continue
        vec /= n
        nbs = [(r2, tet_ca[r2]) for r2 in tet_ca
               if r2 != rnum and np.linalg.norm(tet_ca[r2] - xyz) < 8.0]
        nt = sum(1 for _, x2 in nbs if np.dot((x2 - xyz) / np.linalg.norm(x2 - xyz), vec) > 0.3)
        na = sum(1 for _, x2 in nbs if np.dot((x2 - xyz) / np.linalg.norm(x2 - xyz), vec) < -0.3)
        tet_exposure[rnum] = 1.0 - (nt / max(1, nt + na))

    tet_chain_contacts = {}
    for rnum in tet_ca:
        xyz = tet_ca[rnum]
        chains_contacted = set()
        for ch in ['B', 'C', 'D']:
            ch_atoms = np.array([x for _, _, _, x in chains[ch]])
            if np.min(np.linalg.norm(ch_atoms - xyz, axis=1)) < 5.0:
                chains_contacted.add(ch)
        tet_chain_contacts[rnum] = len(chains_contacted)

    return tet_interface, tet_exposure, tet_chain_contacts


# ═══════════════════════════════════════════════════════════════
# PPI (ports v17.setup_ppi verbatim)
# ═══════════════════════════════════════════════════════════════

def _build_ppi_context(ann: ProteinAnnotation, atom_xyz_lookup):
    """Load PPI union JSON and compute neighbor counts.

    Ported from legacy.p53_gate_v17_idr.setup_ppi (L431-446).
    Returns (PPI, ppi_nb_count).
    """
    if ann.ppi_union_file is None or not os.path.exists(ann.ppi_union_file):
        return {}, {}

    with open(ann.ppi_union_file) as f:
        PPI = {int(k): v for k, v in json.load(f).items()}

    ppi_nb_count = {}
    if atom_xyz_lookup:
        for pos in PPI:
            if pos not in atom_xyz_lookup:
                continue
            ppi_nb_count[pos] = sum(
                1 for r2 in PPI if r2 != pos and r2 in atom_xyz_lookup
                and np.linalg.norm(atom_xyz_lookup[r2] - atom_xyz_lookup[pos]) < 8.0
            )

    return PPI, ppi_nb_count


# ═══════════════════════════════════════════════════════════════
# Salt bridge (ports v17.setup_salt_bridge verbatim)
# ═══════════════════════════════════════════════════════════════

def _build_salt_bridge_context(residue_ctx, atom_xyz_lookup):
    """Identify surface salt-bridge partner pairs.

    Ported from legacy.p53_gate_v17_idr.setup_salt_bridge (L449-463).
    Returns sb_partners dict.
    """
    if not residue_ctx or not atom_xyz_lookup:
        return {}

    surface_charged = {
        rn: residue_ctx[rn]['aa'] for rn in residue_ctx
        if residue_ctx[rn]['bur'] < 0.5 and residue_ctx[rn]['aa'] in 'DEKR'
    }
    sb_partners = {}
    for r1 in surface_charged:
        q1 = AA_CHARGE.get(surface_charged[r1], 0)
        sb_partners[r1] = [
            r2 for r2 in surface_charged if r2 != r1
            and AA_CHARGE.get(surface_charged[r2], 0) * q1 < 0
            and np.linalg.norm(atom_xyz_lookup[r1] - atom_xyz_lookup[r2]) < 10
        ]
    return sb_partners
