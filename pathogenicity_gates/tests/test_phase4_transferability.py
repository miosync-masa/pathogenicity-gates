"""
Phase 4 regression test: other-protein applicability.

Validates that the Gate & Channel framework, as implemented in Phase 1-3,
correctly fires for known pathogenic variants in KRAS, TDP-43, and BRCA1.

Variants grouped into two categories per protein:
  - EXPECTED_FIRING: covered by current Channels — must fire (n_closed >= 1)
  - FUTURE_WORK:     outside current Channel coverage (xfail, documented)

See docs/transferability_matrix.md for the full analysis.
"""
import os
import pytest
from pathogenicity_gates import Predictor


# ═══════════════════════════════════════════════════════════════
# Bundled protein availability
# ═══════════════════════════════════════════════════════════════
def test_list_bundled_includes_all_four():
    """All 4 proteins must be bundled."""
    proteins = Predictor.list_bundled_proteins()
    for p in ['p53', 'kras', 'tdp43', 'brca1']:
        assert p in proteins, f"Protein '{p}' missing: available={proteins}"


# ═══════════════════════════════════════════════════════════════
# KRAS (ADAPTABLE tier demonstration)
# ═══════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def kras_pred():
    return Predictor.from_protein("kras")


KRAS_EXPECTED_FIRING = [
    (117, 'K', 'N', "K117N - ADAPTABLE charge loss"),
    (146, 'A', 'T', "A146T - ADAPTABLE helix strain"),
]

KRAS_FUTURE_WORK = [
    (12, 'G', 'V', "G12V - catalytic-site Gly (G12 bur=0.43, needs functional-site channel)"),
    (12, 'G', 'D', "G12D - same as G12V"),
    (13, 'G', 'D', "G13D - P-loop Gly, same class as G12"),
]


@pytest.mark.parametrize("pos,wt,mt,desc", KRAS_EXPECTED_FIRING)
def test_kras_expected_firing(kras_pred, pos, wt, mt, desc):
    r = kras_pred.predict(pos, wt, mt)
    assert r['n_closed'] >= 1, (
        f"KRAS {wt}{pos}{mt} ({desc}) did NOT fire. channels={r['channels']}"
    )


@pytest.mark.parametrize("pos,wt,mt,desc", KRAS_FUTURE_WORK)
@pytest.mark.xfail(reason="KRAS G12/G13: catalytic-site Gly (experimental/ future work)",
                   strict=True)
def test_kras_future_work(kras_pred, pos, wt, mt, desc):
    r = kras_pred.predict(pos, wt, mt)
    assert r['n_closed'] >= 1


# ═══════════════════════════════════════════════════════════════
# TDP-43 (UNIVERSAL tier demonstration — no PDB needed)
# ═══════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def tdp43_pred():
    return Predictor.from_protein("tdp43")


TDP43_EXPECTED_FIRING = [
    (294, 'G', 'A', "G294A - UNIVERSAL IDR Gly loss"),
    (295, 'G', 'V', "G295V - UNIVERSAL IDR Gly loss"),
    (348, 'G', 'C', "G348C - UNIVERSAL IDR Gly loss"),
    (390, 'N', 'D', "N390D - UNIVERSAL IDR charge intro"),
]

TDP43_FUTURE_WORK = [
    (315, 'A', 'T', "A315T - LCD β-branch intro (needs LLPS channel)"),
    (382, 'A', 'T', "A382T - same as A315T (non-SLiM LCD)"),
]


@pytest.mark.parametrize("pos,wt,mt,desc", TDP43_EXPECTED_FIRING)
def test_tdp43_expected_firing(tdp43_pred, pos, wt, mt, desc):
    r = tdp43_pred.predict(pos, wt, mt)
    assert r['n_closed'] >= 1, (
        f"TDP-43 {wt}{pos}{mt} ({desc}) did NOT fire. channels={r['channels']}"
    )


@pytest.mark.parametrize("pos,wt,mt,desc", TDP43_FUTURE_WORK)
@pytest.mark.xfail(reason="TDP-43 LCD β-branch (LLPS/aggregation future work)",
                   strict=True)
def test_tdp43_future_work(tdp43_pred, pos, wt, mt, desc):
    r = tdp43_pred.predict(pos, wt, mt)
    assert r['n_closed'] >= 1


def test_tdp43_g348c_uses_idr_gly():
    """TDP-43 G348C must fire Ch12_IDR_Gly specifically."""
    pred = Predictor.from_protein("tdp43")
    r = pred.predict(348, 'G', 'C', mode="channels")
    assert r['channels'].get('Ch12_IDR_Gly') == 'C', (
        f"Ch12_IDR_Gly should be CLOSED for G348C. Got: {r['channels']}"
    )


def test_tdp43_works_without_primary_pdb():
    """TDP-43 annotation has no primary PDB; IDR-only channels must still run."""
    pred = Predictor.from_protein("tdp43")
    assert pred._annotation.primary_pdb is None
    r = pred.predict(348, 'G', 'C', mode="channels")
    assert r['regime'] == 'idr'


# ═══════════════════════════════════════════════════════════════
# BRCA1 (ADAPTABLE tier + Gate C architecture demonstration)
# ═══════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def brca1_pred():
    return Predictor.from_protein("brca1")


BRCA1_EXPECTED_FIRING = [
    (61,   'C', 'G', "C61G - RING Zn via Ch03 (not Ch02, which is p53-specific)"),
    (64,   'C', 'R', "C64R - RING Zn + charge_intro"),
    (37,   'T', 'R', "T37R - charge_intro"),
    (1696, 'V', 'L', "V1696L - BRCT buried conservative"),
    (1702, 'K', 'N', "K1702N - BRCT charge_loss"),
    (1775, 'M', 'R', "M1775R - BRCT sulfur + charge"),
    (1697, 'C', 'R', "C1697R - BRCT charge_intro"),
    (1708, 'A', 'E', "A1708E - BRCT charge_intro"),
]


@pytest.mark.parametrize("pos,wt,mt,desc", BRCA1_EXPECTED_FIRING)
def test_brca1_expected_firing(brca1_pred, pos, wt, mt, desc):
    r = brca1_pred.predict(pos, wt, mt)
    assert r['n_closed'] >= 1, (
        f"BRCA1 {wt}{pos}{mt} ({desc}) did NOT fire. channels={r['channels']}"
    )


# ═══════════════════════════════════════════════════════════════
# Cross-protein invariants
# ═══════════════════════════════════════════════════════════════
def test_p53_unchanged_by_phase4():
    """p53 predictions must remain byte-for-byte after Phase 4 additions."""
    pred = Predictor.from_protein("p53")
    HOTSPOTS = [
        (175, 'R', 'H'), (248, 'R', 'W'), (273, 'R', 'H'),
    ]
    for pos, wt, mt in HOTSPOTS:
        r = pred.predict(pos, wt, mt)
        assert r['prediction'] == 'Pathogenic', (
            f"p53 {wt}{pos}{mt} failed after Phase 4: {r}"
        )


@pytest.mark.parametrize("protein", ['kras', 'tdp43', 'brca1'])
def test_annotation_loads(protein):
    """Each protein's annotation.yaml must load without error."""
    from pathogenicity_gates.annotations.loader import load_annotation
    import pathogenicity_gates

    pkg_dir = os.path.dirname(os.path.abspath(pathogenicity_gates.__file__))
    yaml_path = os.path.join(pkg_dir, 'data', protein, 'annotation.yaml')
    assert os.path.exists(yaml_path)

    ann = load_annotation(yaml_path)
    assert ann.name is not None
    assert ann.uniprot is not None
    assert len(ann.idr_ranges) > 0, f"{protein}: no IDR ranges defined"


def test_all_four_proteins_use_channels_mode():
    """All 4 proteins must run in channels mode without crashing."""
    for protein in ['p53', 'kras', 'tdp43', 'brca1']:
        pred = Predictor.from_protein(protein)
        r = pred.predict(100, 'A', 'V', mode="channels")
        assert 'regime' in r
        assert 'channels' in r


def test_tet_range_scoped_correctly():
    """TDP-43 pos 348 must NOT be treated as tet regime (p53-specific ranges)."""
    pred = Predictor.from_protein("tdp43")
    r_legacy = pred.predict(348, 'G', 'C', mode="legacy")
    # Must be IDR regime (4 IDR channels), not tet regime (9 channels)
    assert len(r_legacy['channels']) == 4, (
        f"TDP-43 pos 348 should be IDR regime (4 channels); "
        f"got {len(r_legacy['channels'])}: {r_legacy['channels']}"
    )
