"""
Phase 5 fix guard: ensure channels mode never loads legacy modules.

Also verifies that p53 predictions are byte-for-byte identical between
the legacy-backed path (legacy_impl=True) and the pure path
(legacy_impl=False) when run in channels mode.
"""
import json
import os
import subprocess
import sys
import shutil
import tempfile
import pytest


def _run_python(code: str) -> dict:
    """Run `python -c code` in a subprocess and return the single JSON line."""
    out = subprocess.check_output(
        [sys.executable, '-c', code],
        text=True,
        timeout=180,
    )
    return json.loads(out.strip().splitlines()[-1])


# ═══════════════════════════════════════════════════════════════
# 1. Channels mode must not leak legacy imports
# ═══════════════════════════════════════════════════════════════
def test_channels_mode_no_legacy_import():
    """Predictor.from_protein(..., legacy_impl=False) must not touch legacy."""
    code = (
        "import sys, json;"
        "from pathogenicity_gates import Predictor;"
        "pred = Predictor.from_protein('kras', legacy_impl=False);"
        "r = pred.predict(117, 'K', 'N', mode='channels');"
        "leaked = sorted(m for m in sys.modules if 'pathogenicity_gates.legacy' in m);"
        "print(json.dumps({'n_closed': r['n_closed'], 'leaked': leaked}))"
    )
    data = _run_python(code)
    assert data['n_closed'] >= 1, f"KRAS K117N should fire: {data}"
    assert data['leaked'] == [], (
        f"channels mode must not import legacy, but found: {data['leaked']}"
    )


def test_channels_mode_p53_no_legacy_import():
    """Same guarantee for p53: channels+legacy_impl=False stays clean."""
    code = (
        "import sys, json;"
        "from pathogenicity_gates import Predictor;"
        "pred = Predictor.from_protein('p53', legacy_impl=False);"
        "r = pred.predict(175, 'R', 'H', mode='channels');"
        "leaked = sorted(m for m in sys.modules if 'pathogenicity_gates.legacy' in m);"
        "print(json.dumps({'n_closed': r['n_closed'], 'leaked': leaked}))"
    )
    data = _run_python(code)
    assert data['n_closed'] == 3, f"p53 R175H expected n_closed=3, got {data}"
    assert data['leaked'] == [], (
        f"channels mode must not import legacy, but found: {data['leaked']}"
    )


# ═══════════════════════════════════════════════════════════════
# 2. direct vs legacy_impl must produce identical channel states (p53)
# ═══════════════════════════════════════════════════════════════
@pytest.mark.parametrize("pos,wt,mt", [
    (175, 'R', 'H'),
    (248, 'R', 'W'),
    (273, 'R', 'H'),
    (47,  'P', 'S'),
    (72,  'P', 'R'),
    (305, 'K', 'R'),
    (336, 'R', 'W'),
])
def test_p53_channels_mode_identical_legacy_impl_flag(pos, wt, mt):
    """Channels mode must give identical results regardless of legacy_impl flag."""
    from pathogenicity_gates import Predictor
    p_true = Predictor.from_protein('p53', legacy_impl=True)
    p_false = Predictor.from_protein('p53', legacy_impl=False)
    r_true = p_true.predict(pos, wt, mt, mode='channels')
    r_false = p_false.predict(pos, wt, mt, mode='channels')
    assert r_true['n_closed'] == r_false['n_closed'], (
        f"{wt}{pos}{mt}: legacy_impl True={r_true['n_closed']} vs "
        f"False={r_false['n_closed']}"
    )
    assert r_true['channels'] == r_false['channels'], (
        f"{wt}{pos}{mt}: channel states differ"
    )


# ═══════════════════════════════════════════════════════════════
# 3. Clean environment (no partner_face.json anywhere legacy can find)
# ═══════════════════════════════════════════════════════════════
@pytest.fixture
def clean_env_no_legacy_partner_face():
    """Temporarily move any partner_face.json that legacy would discover."""
    import pathogenicity_gates
    pkg = os.path.dirname(os.path.abspath(pathogenicity_gates.__file__))
    hidden = []
    for rel in ['legacy/partner_face.json',
                '../partner_face.json']:
        path = os.path.abspath(os.path.join(pkg, rel))
        if os.path.exists(path):
            stash = path + '.phase5_test_stash'
            shutil.move(path, stash)
            hidden.append((path, stash))
    # Also CWD
    cwd_pf = os.path.abspath('partner_face.json')
    if os.path.exists(cwd_pf) and cwd_pf not in {p for p, _ in hidden}:
        stash = cwd_pf + '.phase5_test_stash'
        shutil.move(cwd_pf, stash)
        hidden.append((cwd_pf, stash))
    yield
    for orig, stash in hidden:
        shutil.move(stash, orig)


@pytest.mark.parametrize("protein,pos,wt,mt", [
    ('kras',  117, 'K', 'N'),
    ('tdp43', 348, 'G', 'C'),
    ('brca1', 1696, 'V', 'L'),
])
def test_clean_env_non_p53_predicts(clean_env_no_legacy_partner_face,
                                     protein, pos, wt, mt):
    """Non-p53 proteins must predict in channels mode even when no
    partner_face.json is reachable by the legacy loader."""
    from pathogenicity_gates import Predictor
    pred = Predictor.from_protein(protein, legacy_impl=False)
    r = pred.predict(pos, wt, mt, mode='channels')
    assert r['n_closed'] >= 1, f"{protein} {wt}{pos}{mt}: {r}"


def test_clean_env_p53_via_bundled_data(clean_env_no_legacy_partner_face):
    """p53 must still work in clean env: legacy_impl=False uses
    annotation.partner_face_file directly (bundled in data/p53/)."""
    from pathogenicity_gates import Predictor
    pred = Predictor.from_protein('p53', legacy_impl=False)
    r = pred.predict(175, 'R', 'H', mode='channels')
    assert r['prediction'] == 'Pathogenic'
    assert r['n_closed'] == 3
