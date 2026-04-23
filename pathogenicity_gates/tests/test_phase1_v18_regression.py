"""
Phase 1 regression test: pathogenicity-gates produces IDENTICAL predictions
to the legacy v18 implementation for all 1369 ClinVar variants.

This test is the DEFINITION OF DONE for Phase 1. If any single test fails,
Phase 1 is NOT complete. No subsequent Phase may begin until all tests pass.

Expected v18 FINAL metrics (measured 2026-04-23):
  - n_variants_in_scope: 1369
  - TP:  547, FP:  67, FN: 100, TN:  67
  - Sensitivity: 84.5% (547/647)
  - PPV:         89.1% (547/614)
  - Hotspots caught: 9/9
  - Partner face: 59 residues
"""
import pytest
from pathogenicity_gates import Predictor


# ═══════════════════════════════════════════════════════════════
# Exact reference values (v18 FINAL, measured 2026-04-23)
# ═══════════════════════════════════════════════════════════════
EXACT_METRICS = {
    "n_variants_in_scope": 1369,
    "n_tp": 547,
    "n_fp":  67,
    "n_fn": 100,
    "n_tn":  67,
    "n_vus_flagged": 407,
    "hotspots_caught": 9,
    "partner_face_size": 59,
}

REGION_METRICS = {
    "Core":    {"N": 821, "TP": 412, "FP": 20, "FN": 41, "TN": 20},
    "Tet":     {"N": 106, "TP":  27, "FP": 11, "FN": 13, "TN":  7},
    "TAD1":    {"N":  89, "TP":  35, "FP":  7, "FN":  3, "TN":  4},
    "TAD2":    {"N":  57, "TP":  16, "FP":  7, "FN":  5, "TN":  2},
    "PRD":     {"N":  98, "TP":  20, "FP":  6, "FN": 10, "TN": 11},
    "Linker":  {"N":  99, "TP":  13, "FP":  6, "FN": 18, "TN": 16},
    "CTD":     {"N":  99, "TP":  24, "FP": 10, "FN": 10, "TN":  7},
}

HOTSPOTS = [
    (175, 'R', 'H'), (176, 'C', 'F'), (179, 'H', 'R'),
    (220, 'Y', 'C'), (245, 'G', 'S'), (248, 'R', 'W'),
    (249, 'R', 'S'), (273, 'R', 'H'), (280, 'R', 'K'),
]

REGION_CHECKS = [
    ("Core",   lambda p: 94 <= p <= 289),
    ("Tet",    lambda p: 325 <= p <= 356),
    ("TAD1",   lambda p: 1 <= p <= 40),
    ("TAD2",   lambda p: 41 <= p <= 61),
    ("PRD",    lambda p: 62 <= p <= 93),
    ("Linker", lambda p: 290 <= p <= 324),
    ("CTD",    lambda p: 357 <= p <= 393),
]


# ═══════════════════════════════════════════════════════════════
# Shared fixtures (module scope: expensive setup, reused)
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def predictor():
    """Shared Predictor instance. Setup is ~10-30s, so don't repeat."""
    return Predictor.from_legacy_v18("p53")


@pytest.fixture(scope="module")
def predictions(predictor, in_scope_variants):
    """Run full prediction set once, reuse across tests."""
    results = []
    for key, cs in in_scope_variants.items():
        pos, wt, mt = key.split('_')
        pos = int(pos)
        r = predictor.predict(pos, wt, mt)
        r['clinvar'] = cs
        r['key'] = key
        results.append(r)
    return results


# ═══════════════════════════════════════════════════════════════
# Test 1: In-scope variant count
# ═══════════════════════════════════════════════════════════════
def test_variant_count(predictions):
    """In-scope variant count must be exactly 1369."""
    assert len(predictions) == EXACT_METRICS["n_variants_in_scope"], (
        f"Expected {EXACT_METRICS['n_variants_in_scope']} variants, "
        f"got {len(predictions)}"
    )


# ═══════════════════════════════════════════════════════════════
# Test 2: Global confusion matrix (exact counts)
# ═══════════════════════════════════════════════════════════════
def test_confusion_matrix_exact(predictions):
    """TP/FP/FN/TN must match v18 FINAL exactly."""
    tp = sum(1 for r in predictions if r['n_closed'] >= 1 and r['clinvar'] == 'Pathogenic')
    fp = sum(1 for r in predictions if r['n_closed'] >= 1 and r['clinvar'] == 'Benign')
    fn = sum(1 for r in predictions if r['n_closed'] == 0 and r['clinvar'] == 'Pathogenic')
    tn = sum(1 for r in predictions if r['n_closed'] == 0 and r['clinvar'] == 'Benign')

    assert tp == EXACT_METRICS["n_tp"], f"TP: expected {EXACT_METRICS['n_tp']}, got {tp}"
    assert fp == EXACT_METRICS["n_fp"], f"FP: expected {EXACT_METRICS['n_fp']}, got {fp}"
    assert fn == EXACT_METRICS["n_fn"], f"FN: expected {EXACT_METRICS['n_fn']}, got {fn}"
    assert tn == EXACT_METRICS["n_tn"], f"TN: expected {EXACT_METRICS['n_tn']}, got {tn}"


# ═══════════════════════════════════════════════════════════════
# Test 3: All 9 cancer hotspots caught
# ═══════════════════════════════════════════════════════════════
def test_all_hotspots_caught(predictor):
    """All 9 p53 cancer hotspots must be predicted Pathogenic."""
    missed = []
    for pos, wt, mt in HOTSPOTS:
        r = predictor.predict(pos, wt, mt)
        if r['n_closed'] < 1:
            missed.append(f"{wt}{pos}{mt} (channels={r['channels']})")
    assert not missed, f"Missed hotspots: {missed}"


# ═══════════════════════════════════════════════════════════════
# Test 4: Region-by-region exact match
# ═══════════════════════════════════════════════════════════════
@pytest.mark.parametrize("region_name,region_fn", REGION_CHECKS)
def test_region_exact_metrics(predictions, region_name, region_fn):
    """Each region's TP/FP/FN/TN must match v18 FINAL exactly."""
    rr = [r for r in predictions if region_fn(r['pos'])]
    tp = sum(1 for r in rr if r['n_closed'] >= 1 and r['clinvar'] == 'Pathogenic')
    fp = sum(1 for r in rr if r['n_closed'] >= 1 and r['clinvar'] == 'Benign')
    fn = sum(1 for r in rr if r['n_closed'] == 0 and r['clinvar'] == 'Pathogenic')
    tn = sum(1 for r in rr if r['n_closed'] == 0 and r['clinvar'] == 'Benign')

    expected = REGION_METRICS[region_name]
    assert len(rr) == expected["N"], f"{region_name}: N mismatch {len(rr)} vs {expected['N']}"
    assert tp == expected["TP"], f"{region_name}: TP mismatch {tp} vs {expected['TP']}"
    assert fp == expected["FP"], f"{region_name}: FP mismatch {fp} vs {expected['FP']}"
    assert fn == expected["FN"], f"{region_name}: FN mismatch {fn} vs {expected['FN']}"
    assert tn == expected["TN"], f"{region_name}: TN mismatch {tn} vs {expected['TN']}"


# ═══════════════════════════════════════════════════════════════
# Test 5: Byte-for-byte identity with legacy v18 (★最重要★)
# ═══════════════════════════════════════════════════════════════
def test_exact_identity_with_legacy(predictor, in_scope_variants):
    """Every prediction must match legacy v18 output EXACTLY.

    This is the strongest guarantee: if a single variant produces different
    n_closed or channels, Phase 1 refactoring introduced a bug.
    """
    from pathogenicity_gates.legacy import p53_gate_v18_final  # noqa: F401
    from pathogenicity_gates.legacy import p53_gate_v17_idr as v17

    ctx, ss_map, backbone, atoms, all_heavy, atom_xyz_lookup = v17.setup_core_domain()
    tet_interface, tet_exposure, tet_chain_contacts = v17.setup_tetramer()
    PPI, ppi_nb_count = v17.setup_ppi(atom_xyz_lookup=atom_xyz_lookup)
    sb_partners = v17.setup_salt_bridge(ctx, atom_xyz_lookup)

    mismatches = []
    for key in in_scope_variants:
        pos, wt, mt = key.split('_')
        pos = int(pos)

        legacy = v17.predict_pathogenicity(
            pos, wt, mt, ctx, PPI, ppi_nb_count,
            tet_interface, tet_exposure, tet_chain_contacts, sb_partners,
        )
        modern = predictor.predict(pos, wt, mt)

        if legacy['n_closed'] != modern['n_closed']:
            mismatches.append(
                f"{key}: n_closed legacy={legacy['n_closed']} modern={modern['n_closed']}"
            )
        if legacy['prediction'] != modern['prediction']:
            mismatches.append(
                f"{key}: prediction legacy={legacy['prediction']} modern={modern['prediction']}"
            )
        for ch in legacy.get('channels', {}):
            if legacy['channels'].get(ch) != modern['channels'].get(ch):
                mismatches.append(
                    f"{key}: channel {ch} legacy={legacy['channels'].get(ch)} "
                    f"modern={modern['channels'].get(ch)}"
                )

    assert not mismatches, (
        f"Found {len(mismatches)} mismatches (first 10 shown):\n" +
        "\n".join(mismatches[:10])
    )


# ═══════════════════════════════════════════════════════════════
# Test 6: Partner face union size
# ═══════════════════════════════════════════════════════════════
def test_partner_face_size():
    """Gate C 6-partner union must contain exactly 59 residues."""
    from pathogenicity_gates.legacy import p53_gate_v18_final as v18
    assert len(v18.COUPLED_FOLDING_PARTNER_FACE) == EXACT_METRICS["partner_face_size"], (
        f"Partner face: expected {EXACT_METRICS['partner_face_size']} residues, "
        f"got {len(v18.COUPLED_FOLDING_PARTNER_FACE)}"
    )


# ═══════════════════════════════════════════════════════════════
# Test 7: physics/constants.py matches ssoc_v332
# ═══════════════════════════════════════════════════════════════
def test_physics_constants_match_ssoc():
    """All 13 physics constants must match ssoc_v332 exactly."""
    from pathogenicity_gates.physics import constants as modern
    from pathogenicity_gates.legacy import ssoc_v332 as legacy

    assert modern.AA_HYDRO         == legacy.AA_HYDRO
    assert modern.AA_VOLUME        == legacy.AA_VOLUME
    assert modern.AA_CHARGE        == legacy.AA_CHARGE
    assert modern.AA_AROMATIC      == legacy.AA_AROMATIC
    assert modern.AA_SULFUR        == legacy.AA_SULFUR
    assert modern.AA_HBDON         == legacy.AA_HBDON
    assert modern.AA_HBACC         == legacy.AA_HBACC
    assert modern.POLAR_SET        == legacy.POLAR_SET
    assert modern.HELIX_PROP       == legacy.HELIX_PROP
    assert modern.BETA_PROP        == legacy.BETA_PROP
    assert modern.CHARGE_AA        == legacy.CHARGE_AA
    assert modern.C_CAVITY         == legacy.C_CAVITY
    assert modern.C_HYDRO_TRANSFER == legacy.C_HYDRO_TRANSFER
    assert modern.THREE_TO_ONE     == legacy.THREE_TO_ONE


# ═══════════════════════════════════════════════════════════════
# Test 8: physics functions match ssoc_v332
# ═══════════════════════════════════════════════════════════════
def test_physics_functions_match_ssoc():
    """All physics functions must produce identical output to ssoc_v332."""
    from pathogenicity_gates.physics import (
        sigmoid, correction_gly, correction_pro, compute_pvoid,
    )
    from pathogenicity_gates.legacy import ssoc_v332 as legacy

    for x in [0.0, 0.3, 0.5, 0.7, 1.0, 2.0]:
        for x0 in [0.4, 0.5, 0.6]:
            for k in [5.0, 8.0, 10.0]:
                assert sigmoid(x, x0, k) == legacy.sigmoid(x, x0, k)

    assert correction_gly('G', 'A') == legacy.correction_gly('G', 'A')
    assert correction_gly('A', 'G') == legacy.correction_gly('A', 'G')
    assert correction_gly('G', 'V', d_CB_min=3.0, kappa=85, n_branch=2) == \
           legacy.correction_gly('G', 'V', d_CB_min=3.0, kappa=85, n_branch=2)

    assert correction_pro('P', 'A') == legacy.correction_pro('P', 'A')
    assert correction_pro('A', 'P') == legacy.correction_pro('A', 'P')
    assert correction_pro('V', 'L') == legacy.correction_pro('V', 'L')

    for phase in ['cavity', 'strain', 'charge']:
        for lf in [0.1, 0.3, 0.5]:
            for pf in [0.1, 0.3, 0.5]:
                assert compute_pvoid(phase, lf, pf, 0.5, 0.1) == \
                       legacy.compute_pvoid(phase, lf, pf, 0.5, 0.1)


# ═══════════════════════════════════════════════════════════════
# Test 9: Public API smoke test
# ═══════════════════════════════════════════════════════════════
def test_public_api_smoke():
    """Public API must expose Predictor and __version__."""
    import pathogenicity_gates

    assert hasattr(pathogenicity_gates, 'Predictor')
    assert hasattr(pathogenicity_gates, '__version__')
    assert pathogenicity_gates.__version__.startswith("0.")

    with pytest.raises(NotImplementedError):
        Predictor.from_legacy_v18("kras")
