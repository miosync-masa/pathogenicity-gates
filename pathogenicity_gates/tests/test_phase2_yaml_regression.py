"""
Phase 2 regression test: YAML-driven API produces IDENTICAL predictions
to legacy v18 (Phase 1) for all 1369 ClinVar variants.

Tests:
  1. list_bundled_proteins includes 'p53'
  2. from_protein("p53") works (smoke)
  3. from_yaml(bundled_path) works (smoke)
  4. All 9 hotspots fire via YAML
  5. YAML ≡ legacy v18 byte-for-byte
  6. Confusion matrix via YAML matches v18 FINAL exactly
  7. Annotation loader parses YAML correctly
  8. WT extraction from canonical sequence matches v17 hardcoded SLIM_DEFS
  9. PTM consistency report exists
"""
import os
import pytest
from pathogenicity_gates import Predictor


@pytest.fixture(scope="module")
def bundled_yaml_path():
    """Path to the bundled p53 annotation."""
    import pathogenicity_gates
    pkg_dir = os.path.dirname(os.path.abspath(pathogenicity_gates.__file__))
    return os.path.join(pkg_dir, 'data', 'p53', 'annotation.yaml')


@pytest.fixture(scope="module")
def predictor_yaml(bundled_yaml_path):
    """Predictor built from bundled YAML."""
    return Predictor.from_yaml(bundled_yaml_path)


@pytest.fixture(scope="module")
def predictor_protein():
    """Predictor built via from_protein('p53')."""
    return Predictor.from_protein("p53")


@pytest.fixture(scope="module")
def predictor_legacy():
    """Reference legacy predictor (Phase 1)."""
    return Predictor.from_legacy_v18("p53")


# ═══════════════════════════════════════════════════════════════
def test_list_bundled_proteins():
    """Bundled proteins list must include p53."""
    proteins = Predictor.list_bundled_proteins()
    assert 'p53' in proteins, f"p53 not in bundled proteins: {proteins}"


def test_from_protein_smoke(predictor_protein):
    """Predictor.from_protein('p53') must return a working predictor."""
    r = predictor_protein.predict(175, 'R', 'H')
    assert r['prediction'] == 'Pathogenic'
    assert r['n_closed'] >= 1


def test_from_yaml_smoke(predictor_yaml):
    """Predictor.from_yaml(bundled_path) must return a working predictor."""
    r = predictor_yaml.predict(175, 'R', 'H')
    assert r['prediction'] == 'Pathogenic'
    assert r['n_closed'] >= 1


def test_hotspots_via_yaml(predictor_yaml):
    """All 9 hotspots must fire via YAML-driven predictor."""
    HOTSPOTS = [
        (175, 'R', 'H'), (176, 'C', 'F'), (179, 'H', 'R'),
        (220, 'Y', 'C'), (245, 'G', 'S'), (248, 'R', 'W'),
        (249, 'R', 'S'), (273, 'R', 'H'), (280, 'R', 'K'),
    ]
    missed = []
    for pos, wt, mt in HOTSPOTS:
        r = predictor_yaml.predict(pos, wt, mt)
        if r['n_closed'] < 1:
            missed.append(f"{wt}{pos}{mt}")
    assert not missed, f"Hotspots missed via YAML: {missed}"


# ═══════════════════════════════════════════════════════════════
# Core guarantee: from_yaml ≡ from_legacy_v18
# ═══════════════════════════════════════════════════════════════
def test_yaml_identity_with_legacy(predictor_yaml, predictor_legacy, in_scope_variants):
    """Every prediction from YAML-driven must match legacy v18 exactly."""
    mismatches = []
    for key in in_scope_variants:
        pos, wt, mt = key.split('_')
        pos = int(pos)

        legacy_r = predictor_legacy.predict(pos, wt, mt)
        yaml_r = predictor_yaml.predict(pos, wt, mt)

        if legacy_r['n_closed'] != yaml_r['n_closed']:
            mismatches.append(
                f"{key}: legacy n_closed={legacy_r['n_closed']}, "
                f"yaml n_closed={yaml_r['n_closed']}"
            )
        if legacy_r['prediction'] != yaml_r['prediction']:
            mismatches.append(
                f"{key}: legacy pred={legacy_r['prediction']}, "
                f"yaml pred={yaml_r['prediction']}"
            )
        for ch in legacy_r.get('channels', {}):
            if legacy_r['channels'].get(ch) != yaml_r['channels'].get(ch):
                mismatches.append(
                    f"{key}: channel {ch} legacy={legacy_r['channels'].get(ch)} "
                    f"yaml={yaml_r['channels'].get(ch)}"
                )
    assert not mismatches, (
        f"Found {len(mismatches)} mismatches (first 10):\n" +
        "\n".join(mismatches[:10])
    )


def test_yaml_confusion_matrix(predictor_yaml, in_scope_variants):
    """YAML-driven predictions must produce identical TP/FP/FN/TN."""
    tp = fp = fn = tn = 0
    for key, cs in in_scope_variants.items():
        pos, wt, mt = key.split('_')
        pos = int(pos)
        r = predictor_yaml.predict(pos, wt, mt)
        if r['n_closed'] >= 1:
            if cs == 'Pathogenic': tp += 1
            elif cs == 'Benign':   fp += 1
        else:
            if cs == 'Pathogenic': fn += 1
            elif cs == 'Benign':   tn += 1
    assert tp == 547, f"TP: expected 547, got {tp}"
    assert fp == 67,  f"FP: expected 67, got {fp}"
    assert fn == 100, f"FN: expected 100, got {fn}"
    assert tn == 67,  f"TN: expected 67, got {tn}"


def test_annotation_loader(bundled_yaml_path):
    """Annotation YAML must parse correctly."""
    from pathogenicity_gates.annotations.loader import load_annotation
    ann = load_annotation(bundled_yaml_path)
    assert ann.name == 'TP53'
    assert ann.uniprot == 'P04637'
    assert ann.primary_chain == 'B'
    assert 'core' in ann.domains
    assert ann.domains['core'] == (94, 289)
    assert 'TAD1' in ann.idr_ranges
    assert len(ann.ptm_sites) == 31
    assert 15 in ann.ptm_sites
    assert ann.ptm_sites[15] == {'aa': 'S', 'mod': 'phospho', 'enzyme': 'CDK5/ATM/AMPK'}
    assert 'MDM2_binding' in ann.slim_defs
    assert ann.slim_defs['MDM2_binding']['range'] == (17, 29)
    assert 72 in ann.benign_pro_poly
    assert os.path.exists(ann.primary_pdb)
    assert os.path.exists(ann.partner_face_file)
    assert os.path.exists(ann.sequence_file)
    assert ann.wt_at(53) == 'W'
    assert ann.wt_at(54) == 'F'


def test_wt_extraction_from_sequence(bundled_yaml_path):
    """Reconstructed SLIM_DEFS critical_* must match v17 hardcoded values."""
    from pathogenicity_gates.annotations.loader import load_annotation
    from pathogenicity_gates.adapters.v18_adapter import _reconstruct_slim_defs

    ann = load_annotation(bundled_yaml_path)
    slim = _reconstruct_slim_defs(ann)

    assert slim['BOX_II']['critical_aromatic'] == {53: 'W', 54: 'F'}
    assert slim['NLS1']['critical_charged']    == {305: 'K', 306: 'R'}
    assert slim['NLS2']['critical_charged']    == {370: 'K', 372: 'K', 373: 'K'}
    assert slim['NLS3']['critical_charged']    == {379: 'R'}


def test_ptm_consistency_report_generated():
    """ptm_consistency_report.md must exist after Phase 2."""
    import pathogenicity_gates
    pkg_dir = os.path.dirname(os.path.abspath(pathogenicity_gates.__file__))
    report_path = os.path.join(pkg_dir, 'data', 'p53', 'ptm_consistency_report.md')
    assert os.path.exists(report_path), (
        f"PTM consistency report not found: {report_path}\n"
        f"Generate via: python -m pathogenicity_gates.scripts.verify_ptm_consistency "
        f"--annotation {pkg_dir}/data/p53/annotation.yaml "
        f"--out {report_path}"
    )
