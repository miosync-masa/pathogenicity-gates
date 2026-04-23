"""Tests for the channel registry decorator + dispatch."""
import pytest
from pathogenicity_gates.channels import registry


def test_register_invalid_regime():
    """Invalid regime must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid regime"):
        @registry.register_channel(id="TestCh_Invalid", regime="bogus", order=99)
        def fn(pos, wt, mt, ctx):
            return 'O'


def test_register_duplicate_id():
    """Duplicate id must raise ValueError."""
    with pytest.raises(ValueError, match="already registered"):
        @registry.register_channel(id="Ch01_DNA", regime="structural", order=99)
        def fn2(pos, wt, mt, ctx):
            return 'O'


def test_get_applicable_structural():
    """structural regime -> 8 structural + 1 universal = 9 channels."""
    chs = registry.get_applicable_channels('structural')
    assert len(chs) == 9
    ids = {ch_id for ch_id, _ in chs}
    assert 'Ch07_PTM' in ids  # universal
    assert 'Ch01_DNA' in ids  # structural


def test_get_applicable_idr():
    """idr regime -> 3 idr + 1 universal = 4 channels."""
    chs = registry.get_applicable_channels('idr')
    assert len(chs) == 4
    ids = {ch_id for ch_id, _ in chs}
    assert 'Ch07_PTM' in ids
    assert 'Ch10_SLiM' in ids
    assert 'Ch11_IDR_Pro' in ids
    assert 'Ch12_IDR_Gly' in ids


def test_get_applicable_unknown():
    """unknown regime -> []."""
    assert registry.get_applicable_channels('unknown') == []


def test_channels_sorted_by_order():
    """get_applicable_channels result must be sorted by order field."""
    chs = registry.get_applicable_channels('structural')
    orders = [ch_info['order'] for _, ch_info in chs]
    assert orders == sorted(orders)
