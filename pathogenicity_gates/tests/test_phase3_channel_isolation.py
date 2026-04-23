"""
Phase 3 regression test: channel-mode prediction produces IDENTICAL
results to legacy mode for all 1369 ClinVar variants.

Core guarantee:
  predict(..., mode="channels") n_closed == predict(..., mode="legacy") n_closed
  predict(..., mode="channels") prediction == predict(..., mode="legacy") prediction

Channel IDs differ between modes (legacy: Ch1_DNA, Phase 3: Ch01_DNA).
LEGACY_TO_P3_CHANNEL_MAP documents the mapping.
"""
import pytest
from pathogenicity_gates import Predictor


LEGACY_TO_P3_CHANNEL_MAP = {
    'Ch1_DNA':         'Ch01_DNA',
    'Ch2_Zn':          'Ch02_Zn',
    'Ch3_Core':        'Ch03_Core',
    'Ch4_SS':          'Ch04_SS',
    'Ch5_Loop':        'Ch05_Loop',
    'Ch6_PPI':         'Ch06_PPI',
    'Ch7_PTM':         'Ch07_PTM',
    'Ch8_Tet':         'Ch08_Oligomer',
    'Ch9_SaltBridge':  'Ch09_SaltBridge',
    'Ch10_SLiM':       'Ch10_SLiM',
    'Ch5_IDR_Pro':     'Ch11_IDR_Pro',
    'GateB_IDR_Gly':   'Ch12_IDR_Gly',
}


@pytest.fixture(scope="module")
def predictor():
    return Predictor.from_protein("p53")


def test_channel_mode_works(predictor):
    """channel mode must work and identify structural regime."""
    r = predictor.predict(175, 'R', 'H', mode="channels")
    assert r['prediction'] == 'Pathogenic'
    assert r['n_closed'] >= 1
    assert r['regime'] == 'structural'


def test_channel_mode_idr(predictor):
    """channel mode correctly identifies IDR regime."""
    r = predictor.predict(47, 'P', 'S', mode="channels")
    assert r['regime'] == 'idr'
    expected_idr_channels = {'Ch07_PTM', 'Ch10_SLiM', 'Ch11_IDR_Pro', 'Ch12_IDR_Gly'}
    assert set(r['channels'].keys()) == expected_idr_channels


def test_channel_mode_structural(predictor):
    """channel mode correctly identifies structural regime (core)."""
    r = predictor.predict(175, 'R', 'H', mode="channels")
    assert r['regime'] == 'structural'
    expected_structural = {
        'Ch01_DNA', 'Ch02_Zn', 'Ch03_Core', 'Ch04_SS', 'Ch05_Loop',
        'Ch06_PPI', 'Ch07_PTM', 'Ch08_Oligomer', 'Ch09_SaltBridge',
    }
    assert set(r['channels'].keys()) == expected_structural


def test_channel_mode_tet(predictor):
    """tet domain (325-356) must be structural regime."""
    r = predictor.predict(336, 'R', 'W', mode="channels")
    assert r['regime'] == 'structural'
    expected_structural = {
        'Ch01_DNA', 'Ch02_Zn', 'Ch03_Core', 'Ch04_SS', 'Ch05_Loop',
        'Ch06_PPI', 'Ch07_PTM', 'Ch08_Oligomer', 'Ch09_SaltBridge',
    }
    assert set(r['channels'].keys()) == expected_structural


def test_n_closed_identity_legacy_vs_channels(predictor, in_scope_variants):
    """CRITICAL: n_closed must match between legacy and channels modes."""
    mismatches = []
    for key in in_scope_variants:
        pos, wt, mt = key.split('_')
        pos = int(pos)
        r_legacy = predictor.predict(pos, wt, mt, mode="legacy")
        r_ch = predictor.predict(pos, wt, mt, mode="channels")
        if r_legacy['n_closed'] != r_ch['n_closed']:
            mismatches.append(
                f"{key}: legacy={r_legacy['n_closed']}, channels={r_ch['n_closed']}"
            )
        if r_legacy['prediction'] != r_ch['prediction']:
            mismatches.append(
                f"{key}: legacy pred={r_legacy['prediction']}, channels pred={r_ch['prediction']}"
            )
    assert not mismatches, (
        f"Found {len(mismatches)} mismatches (first 10):\n" +
        "\n".join(mismatches[:10])
    )


def test_per_channel_identity(predictor, in_scope_variants):
    """Per-channel states must match between modes via name mapping."""
    mismatches = []
    for key in in_scope_variants:
        pos, wt, mt = key.split('_')
        pos = int(pos)
        r_legacy = predictor.predict(pos, wt, mt, mode="legacy")
        r_ch = predictor.predict(pos, wt, mt, mode="channels")
        for legacy_id, legacy_state in r_legacy['channels'].items():
            p3_id = LEGACY_TO_P3_CHANNEL_MAP.get(legacy_id)
            if p3_id is None:
                continue
            if p3_id not in r_ch['channels']:
                mismatches.append(f"{key}: {legacy_id}->{p3_id} missing in channels mode")
                continue
            ch_state = r_ch['channels'][p3_id]
            if legacy_state != ch_state:
                mismatches.append(
                    f"{key}: {legacy_id}({legacy_state}) vs {p3_id}({ch_state})"
                )
    assert not mismatches, (
        f"Found {len(mismatches)} channel-level mismatches (first 10):\n" +
        "\n".join(mismatches[:10])
    )


def test_registry_has_all_channels():
    """Registry must contain all 12 Phase 3 Channels."""
    from pathogenicity_gates.channels.registry import get_all_channels
    all_chs = get_all_channels()
    ids = {ch_id for ch_id, _ in all_chs}
    expected = {
        'Ch01_DNA', 'Ch02_Zn', 'Ch03_Core', 'Ch04_SS', 'Ch05_Loop',
        'Ch06_PPI', 'Ch07_PTM', 'Ch08_Oligomer', 'Ch09_SaltBridge',
        'Ch10_SLiM', 'Ch11_IDR_Pro', 'Ch12_IDR_Gly',
    }
    assert ids == expected, f"Missing: {expected - ids}, Extra: {ids - expected}"


def test_registry_regime_distribution():
    """Registry must have correct regime distribution."""
    from pathogenicity_gates.channels.registry import list_channels_by_regime
    dist = list_channels_by_regime()
    assert len(dist['structural']) == 8
    assert len(dist['idr']) == 3
    assert len(dist['universal']) == 1
    assert 'Ch07_PTM' in dist['universal']
