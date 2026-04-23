"""Smoke tests for individual Channels using minimal mock contexts.

These exercise the basic CLOSED/OPEN logic branches without relying on
the full PDB/YAML pipeline. The main regression coverage lives in
test_phase3_channel_isolation (full pipeline vs legacy).
"""
import pytest
from pathogenicity_gates.channels.context import PredictionContext


# ───────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────
def _make_residue(**overrides):
    """Minimal residue context with sane defaults."""
    base = {
        'aa': 'A', 'bur': 0.8, 'pf': 0.3, 'ss': 'C',
        'nba': [], 'hnf': 0.1, 'bnf': 0.1, 'lf': 0.2,
        'n_aro': 0, 'n_sul': 0, 'n_charged_nb': 0,
        'dcb': 999.0, 'nbr': 0, 'd_dna': 99.0, 'd_zn': 99.0,
        'hpos': 'none',
    }
    base.update(overrides)
    return base


# ───────────────────────────────────────────────────────────────
# Ch01_DNA
# ───────────────────────────────────────────────────────────────
def test_ch01_rk_loss_near_dna_closed():
    from pathogenicity_gates.channels.structural.ch01_dna import gate_ch01_dna
    ctx = PredictionContext()
    ctx.residue_ctx[248] = _make_residue(aa='R', d_dna=3.0)
    assert gate_ch01_dna(248, 'R', 'W', ctx) == 'C'


def test_ch01_far_from_dna_open():
    from pathogenicity_gates.channels.structural.ch01_dna import gate_ch01_dna
    ctx = PredictionContext()
    ctx.residue_ctx[100] = _make_residue(d_dna=20.0)
    assert gate_ch01_dna(100, 'R', 'W', ctx) == 'O'


def test_ch01_no_residue_ctx_open():
    from pathogenicity_gates.channels.structural.ch01_dna import gate_ch01_dna
    assert gate_ch01_dna(999, 'A', 'V', PredictionContext()) == 'O'


# ───────────────────────────────────────────────────────────────
# Ch02_Zn
# ───────────────────────────────────────────────────────────────
def test_ch02_zn_direct_ligand_closed():
    from pathogenicity_gates.channels.structural.ch02_zn import gate_ch02_zn
    ctx = PredictionContext()
    ctx.residue_ctx[176] = _make_residue(aa='C', d_zn=2.3)
    assert gate_ch02_zn(176, 'C', 'F', ctx) == 'C'


def test_ch02_zn_far_open():
    from pathogenicity_gates.channels.structural.ch02_zn import gate_ch02_zn
    ctx = PredictionContext()
    ctx.residue_ctx[100] = _make_residue(d_zn=20.0)
    assert gate_ch02_zn(100, 'A', 'V', ctx) == 'O'


# ───────────────────────────────────────────────────────────────
# Ch03_Core
# ───────────────────────────────────────────────────────────────
def test_ch03_to_gly_buried_closed():
    from pathogenicity_gates.channels.structural.ch03_core import gate_ch03_core
    ctx = PredictionContext()
    ctx.residue_ctx[175] = _make_residue(aa='R', bur=0.95, ss='C')
    assert gate_ch03_core(175, 'R', 'G', ctx) == 'C'


def test_ch03_vi_swap_exempt():
    """V<->I swap exemption (v18 patch)."""
    from pathogenicity_gates.channels.structural.ch03_core import gate_ch03_core
    ctx = PredictionContext()
    ctx.residue_ctx[100] = _make_residue(aa='V', bur=0.9, ss='E')
    assert gate_ch03_core(100, 'V', 'I', ctx) == 'O'
    assert gate_ch03_core(100, 'I', 'V', ctx) == 'O'


def test_ch03_surface_open():
    from pathogenicity_gates.channels.structural.ch03_core import gate_ch03_core
    ctx = PredictionContext()
    ctx.residue_ctx[50] = _make_residue(bur=0.1)
    assert gate_ch03_core(50, 'A', 'V', ctx) == 'O'


# ───────────────────────────────────────────────────────────────
# Ch09_SaltBridge
# ───────────────────────────────────────────────────────────────
def test_ch09_surface_sb_loss_closed():
    from pathogenicity_gates.channels.structural.ch09_salt_bridge import gate_ch09_salt_bridge
    ctx = PredictionContext()
    ctx.residue_ctx[50] = _make_residue(aa='R', bur=0.3)
    ctx.sb_partners[50] = [100]
    assert gate_ch09_salt_bridge(50, 'R', 'A', ctx) == 'C'


def test_ch09_buried_open():
    from pathogenicity_gates.channels.structural.ch09_salt_bridge import gate_ch09_salt_bridge
    ctx = PredictionContext()
    ctx.residue_ctx[150] = _make_residue(bur=0.9)
    ctx.sb_partners[150] = [200]
    assert gate_ch09_salt_bridge(150, 'R', 'A', ctx) == 'O'


# ───────────────────────────────────────────────────────────────
# Ch12_IDR_Gly
# ───────────────────────────────────────────────────────────────
def test_ch12_idr_gly_g_to_a_closed():
    """G->X in IDR must be CLOSED (loss of backbone freedom)."""
    from pathogenicity_gates.channels.idr.ch12_idr_gly import gate_ch12_idr_gly
    ctx = PredictionContext()
    assert gate_ch12_idr_gly(50, 'G', 'A', ctx) == 'C'


def test_ch12_idr_gly_a_to_g_open():
    """X->G is not fired by this channel."""
    from pathogenicity_gates.channels.idr.ch12_idr_gly import gate_ch12_idr_gly
    ctx = PredictionContext()
    assert gate_ch12_idr_gly(50, 'A', 'G', ctx) == 'O'


def test_ch12_idr_gly_unrelated_open():
    """Non-Gly mutation -> OPEN."""
    from pathogenicity_gates.channels.idr.ch12_idr_gly import gate_ch12_idr_gly
    ctx = PredictionContext()
    assert gate_ch12_idr_gly(50, 'K', 'R', ctx) == 'O'
