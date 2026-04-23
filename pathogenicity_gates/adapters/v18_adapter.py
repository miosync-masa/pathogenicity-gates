"""
Legacy v18 adapter: convert ProteinAnnotation -> setup_*() context.

This is the bridge between Phase 2 YAML-driven API and Phase 1 legacy
implementation. By driving the legacy `setup_core_domain` etc. with YAML-
sourced paths, we achieve byte-for-byte compatibility with v18 FINAL.

Key guarantee: for p53 annotation, this adapter produces context IDENTICAL
to `Predictor.from_legacy_v18("p53")`.
"""
import os
import json
from typing import Dict, Any

from ..annotations.loader import ProteinAnnotation


# Backup of the original (hardcoded) legacy constants, captured on first
# `override_legacy_constants_from_annotation` call. Used by
# `restore_legacy_constants` to revert the modules to their pristine state
# so that `from_legacy_v18()` always sees the original values.
_ORIGINAL_LEGACY_CONSTANTS: Dict[str, Any] = {}


def build_context_from_annotation(ann: ProteinAnnotation) -> Dict[str, Any]:
    """Build the prediction context dict from a ProteinAnnotation.

    Drives legacy v17/v18 setup pipeline using YAML-sourced paths.
    Returns a dict with the same shape as Predictor.from_legacy_v18 internals.
    """
    # Importing v18_final triggers the monkey-patch of v17.
    from ..legacy import p53_gate_v18_final  # noqa: F401
    from ..legacy import p53_gate_v17_idr as v17

    # Primary PDB is OPTIONAL (IDR-only proteins such as TDP-43 skip this).
    if ann.primary_pdb is not None and os.path.exists(ann.primary_pdb):
        ctx, ss_map, backbone, atoms, all_heavy, atom_xyz_lookup = \
            v17.setup_core_domain(pdb_path=ann.primary_pdb, chain=ann.primary_chain)
    else:
        ctx, atom_xyz_lookup = {}, {}

    if ann.oligomer_pdb is not None and os.path.exists(ann.oligomer_pdb):
        tet_interface, tet_exposure, tet_chain_contacts = \
            v17.setup_tetramer(pdb_path=ann.oligomer_pdb)
    else:
        tet_interface, tet_exposure, tet_chain_contacts = {}, {}, {}

    if ann.ppi_union_file is not None and os.path.exists(ann.ppi_union_file):
        PPI, ppi_nb_count = v17.setup_ppi(
            ppi_json=ann.ppi_union_file,
            atom_xyz_lookup=atom_xyz_lookup,
        )
    else:
        PPI, ppi_nb_count = {}, {}

    if ctx:
        sb_partners = v17.setup_salt_bridge(ctx, atom_xyz_lookup)
    else:
        sb_partners = {}

    return {
        'ctx': ctx,
        'PPI': PPI,
        'ppi_nb_count': ppi_nb_count,
        'tet_interface': tet_interface,
        'tet_exposure': tet_exposure,
        'tet_chain_contacts': tet_chain_contacts,
        'sb_partners': sb_partners,
    }


def _backup_originals_once():
    """Snapshot the original hardcoded v17/v18 constants on first call."""
    global _ORIGINAL_LEGACY_CONSTANTS
    if _ORIGINAL_LEGACY_CONSTANTS:
        return
    from ..legacy import p53_gate_v17_idr as v17
    from ..legacy import p53_gate_v18_final as v18
    _ORIGINAL_LEGACY_CONSTANTS = {
        'v17.PTM_SITES':                    dict(v17.PTM_SITES),
        'v17.IDR_RANGES':                   dict(v17.IDR_RANGES),
        'v17.SLIM_DEFS':                    {k: dict(v) for k, v in v17.SLIM_DEFS.items()},
        'v17.BENIGN_PRO_POLY':              set(v17.BENIGN_PRO_POLY),
        'v17.COUPLED_FOLDING_MDM2':         dict(v17.COUPLED_FOLDING_MDM2),
        'v17.TET_RANGE':                    v17.TET_RANGE,
        'v18.COUPLED_FOLDING_PARTNER_FACE': set(v18.COUPLED_FOLDING_PARTNER_FACE),
        # v18 also binds SLIM_DEFS/BENIGN_PRO_POLY/PTM_SITES at import time via
        # `from .p53_gate_v17_idr import ...`. These must be overridden too so
        # gate_ch10_slim_v18/gate_ch7_ptm_v18 see per-protein data.
        'v18.SLIM_DEFS':                    {k: dict(v) for k, v in v18.SLIM_DEFS.items()},
        'v18.BENIGN_PRO_POLY':              set(v18.BENIGN_PRO_POLY),
        'v18.PTM_SITES':                    dict(v18.PTM_SITES),
    }


def override_legacy_constants_from_annotation(ann: ProteinAnnotation):
    """Override legacy v17/v18 module-level constants from YAML.

    This mutates v17 and v18 module namespaces so subsequent calls to
    `predict_pathogenicity` use the YAML-derived data.

    Idempotent: safe to call multiple times.
    """
    from ..legacy import p53_gate_v17_idr as v17
    from ..legacy import p53_gate_v18_final as v18

    _backup_originals_once()

    # ── PTM_SITES ──
    # YAML:  {15: {'aa': 'S', 'mod': 'phospho', 'enzyme': '...'}}
    # v17:   {15: ('S', 'phospho', '...')}
    v17.PTM_SITES = {
        pos: (info['aa'], info['mod'], info['enzyme'])
        for pos, info in ann.ptm_sites.items()
    }

    # ── IDR_RANGES ──
    v17.IDR_RANGES = dict(ann.idr_ranges)

    # ── TET_RANGE (Phase 4: per-protein tet/oligomer domain) ──
    if 'tet' in ann.domains:
        v17.TET_RANGE = tuple(ann.domains['tet'])
    else:
        v17.TET_RANGE = None

    # ── SLIM_DEFS ──
    v17.SLIM_DEFS = _reconstruct_slim_defs(ann)

    # ── BENIGN_PRO_POLY ──
    v17.BENIGN_PRO_POLY = set(ann.benign_pro_poly)

    # ── COUPLED_FOLDING_PARTNER_FACE (v18) ──
    if ann.partner_face_file is not None and os.path.exists(ann.partner_face_file):
        with open(ann.partner_face_file) as f:
            pf_data = json.load(f)
        v18.COUPLED_FOLDING_PARTNER_FACE = set(pf_data['union'])

    # ── COUPLED_FOLDING_MDM2 (v17 hardcoded dict -> PDB-derived) ──
    v17.COUPLED_FOLDING_MDM2 = _extract_coupled_folding_mdm2_from_pdb(ann)

    # ── v18 module-local rebinds (must mirror v17.* for gate_ch*_v18) ──
    v18.SLIM_DEFS = v17.SLIM_DEFS
    v18.BENIGN_PRO_POLY = v17.BENIGN_PRO_POLY
    v18.PTM_SITES = v17.PTM_SITES


def restore_legacy_constants():
    """Restore legacy v17/v18 module constants to their original values.

    Called by `Predictor.from_legacy_v18()` to ensure it always observes the
    pristine hardcoded values, even after `from_yaml()` was called.
    """
    if not _ORIGINAL_LEGACY_CONSTANTS:
        return
    from ..legacy import p53_gate_v17_idr as v17
    from ..legacy import p53_gate_v18_final as v18

    v17.PTM_SITES = dict(_ORIGINAL_LEGACY_CONSTANTS['v17.PTM_SITES'])
    v17.IDR_RANGES = dict(_ORIGINAL_LEGACY_CONSTANTS['v17.IDR_RANGES'])
    v17.SLIM_DEFS = {
        k: dict(v) for k, v in _ORIGINAL_LEGACY_CONSTANTS['v17.SLIM_DEFS'].items()
    }
    v17.BENIGN_PRO_POLY = set(_ORIGINAL_LEGACY_CONSTANTS['v17.BENIGN_PRO_POLY'])
    v17.COUPLED_FOLDING_MDM2 = dict(_ORIGINAL_LEGACY_CONSTANTS['v17.COUPLED_FOLDING_MDM2'])
    v17.TET_RANGE = _ORIGINAL_LEGACY_CONSTANTS['v17.TET_RANGE']
    v18.COUPLED_FOLDING_PARTNER_FACE = set(
        _ORIGINAL_LEGACY_CONSTANTS['v18.COUPLED_FOLDING_PARTNER_FACE']
    )
    v18.SLIM_DEFS = {
        k: dict(v) for k, v in _ORIGINAL_LEGACY_CONSTANTS['v18.SLIM_DEFS'].items()
    }
    v18.BENIGN_PRO_POLY = set(_ORIGINAL_LEGACY_CONSTANTS['v18.BENIGN_PRO_POLY'])
    v18.PTM_SITES = dict(_ORIGINAL_LEGACY_CONSTANTS['v18.PTM_SITES'])


def _reconstruct_slim_defs(ann: ProteinAnnotation) -> Dict[str, Dict[str, Any]]:
    """Reconstruct v17 SLIM_DEFS from YAML + canonical sequence.

    v17 format:
      'BOX_II': {
          'range': (41, 55),
          'critical_aromatic': {53: 'W', 54: 'F'},
          'type': 'protein_interaction',
      }

    YAML provides positions only; WT identity is read from the UniProt
    canonical sequence (p53_sequence.json).
    """
    result = {}
    for slim_name, sdef in ann.slim_defs.items():
        reconstructed = {
            'range': sdef['range'],
            'type': sdef['type'],
        }
        if 'critical_aromatic_positions' in sdef:
            ca = {}
            for pos in sdef['critical_aromatic_positions']:
                wt = ann.wt_at(pos)
                if wt is not None:
                    ca[pos] = wt
            reconstructed['critical_aromatic'] = ca
        if 'critical_charged_positions' in sdef:
            cc = {}
            for pos in sdef['critical_charged_positions']:
                wt = ann.wt_at(pos)
                if wt is not None:
                    cc[pos] = wt
            reconstructed['critical_charged'] = cc
        result[slim_name] = reconstructed
    return result


def _extract_coupled_folding_mdm2_from_pdb(ann: ProteinAnnotation) -> Dict[int, str]:
    """Extract COUPLED_FOLDING_MDM2 {pos: WT_aa} from the 1YCR PDB.

    Scans p53 sidechain heavy atoms against MDM2 heavy atoms in the
    MDM2 entry of ann.coupled_folding_pdbs, returning residues with
    any sidechain heavy atom within 5 A of any MDM2 atom.

    Falls back to v17 hardcoded values if PDB cannot be parsed.
    """
    from ..structure.parser import parse_pdb
    import numpy as np

    fallback = {17: 'E', 18: 'T', 19: 'F', 20: 'S', 22: 'L', 23: 'W',
                25: 'L', 26: 'L', 27: 'P', 28: 'E', 29: 'N'}

    ycr_entry = next(
        (cf for cf in ann.coupled_folding_pdbs if cf.get('partner') == 'MDM2'),
        None,
    )
    if ycr_entry is None or not ycr_entry.get('pdb') or not os.path.exists(ycr_entry['pdb']):
        return fallback

    # Determine which chain is p53 (should contain pos 19 = F) vs MDM2.
    p53_atoms = None
    mdm2_heavy = None
    aa_map = {}
    for p53_chain, partner_chain in [('B', 'A'), ('A', 'B')]:
        try:
            _, atoms_p53, heavy_p53 = parse_pdb(ycr_entry['pdb'], chain=p53_chain)
            _, _, heavy_mdm2 = parse_pdb(ycr_entry['pdb'], chain=partner_chain)
            if len(atoms_p53) < 5 or len(heavy_mdm2) < 5:
                continue
            cand_aa_map = {rnum: aa for rnum, aa, _ in atoms_p53}
            if cand_aa_map.get(19) == 'F':
                p53_atoms = atoms_p53
                mdm2_heavy = heavy_mdm2
                aa_map = cand_aa_map
                # Also fetch p53 heavy atoms
                p53_heavy = heavy_p53
                break
        except Exception:
            continue
    if p53_atoms is None:
        return fallback

    # Distance scan: sidechain heavy atoms of p53 vs any heavy atom of MDM2
    mdm2_coords = np.array([xyz for _, _, xyz in mdm2_heavy])
    if mdm2_coords.size == 0:
        return fallback

    residue_sc = {}
    for rnum, atom_name, xyz in p53_heavy:
        if atom_name in ('N', 'CA', 'C', 'O'):
            continue
        residue_sc.setdefault(rnum, []).append(xyz)

    result = {}
    for rnum, sc_coords in residue_sc.items():
        if rnum not in aa_map:
            continue
        sc_arr = np.array(sc_coords)
        # Pairwise min distance
        diffs = mdm2_coords[:, None, :] - sc_arr[None, :, :]
        dists = np.sqrt((diffs ** 2).sum(axis=2))
        if dists.min() < 5.0:
            result[rnum] = aa_map[rnum]

    return result if result else fallback
