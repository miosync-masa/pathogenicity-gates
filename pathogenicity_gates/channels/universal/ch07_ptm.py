"""
Ch07_PTM: PTM site disruption.

UNIVERSAL regime: applies to both structural and IDR regimes, with
is_idr-dependent logic adjustment.

MECE split:
  7a: Direct PTM site hit
  7b: Structured PTM proximity (+/- 2, OR logic)
  7c: IDR PTM proximity (+/- 1, OR logic)
  7d: Proline-directed kinase motif [S/T]-P destruction

V18 patch embedded: IDR +/- 1 conservative swap (K<->R, R<->H, S<->T)
does not disrupt PTM recognition due to backbone flexibility.
"""
from ...physics.constants import AA_CHARGE, AA_VOLUME
from ..registry import register_channel

PROLINE_DIRECTED_KINASES = {
    'CDK1', 'CDK2', 'CDK5', 'CDK7',
    'DYRK2', 'HIPK2', 'HIPK4', 'MAPK',
}

CONSERVATIVE_PAIRS_IDR = frozenset({
    frozenset({'K', 'R'}),
    frozenset({'R', 'H'}),
    frozenset({'S', 'T'}),
})


@register_channel(id="Ch07_PTM", regime="universal", order=7)
def gate_ch07_ptm(pos, wt, mt, ctx):
    """Ch7: PTM site disruption (v17 base + v18 IDR conservative Geta)."""
    ann = ctx.annotation
    if ann is None:
        return 'O'

    is_idr = ctx.is_idr_position(pos)
    ptm_sites = ann.ptm_sites  # {pos: {'aa': ..., 'mod': ..., 'enzyme': ...}}

    # 7a: Direct PTM site
    if pos in ptm_sites:
        entry = ptm_sites[pos]
        expected_aa = entry['aa']
        if wt == expected_aa and mt != expected_aa:
            return 'C'
        return 'P'

    # 7d: Proline-directed kinase [S/T]-P
    if wt == 'P' and mt != 'P':
        prev_pos = pos - 1
        if prev_pos in ptm_sites:
            entry = ptm_sites[prev_pos]
            if entry['mod'] == 'phospho':
                enzymes = set(k.strip() for k in entry['enzyme'].split('/'))
                if enzymes & PROLINE_DIRECTED_KINASES:
                    return 'C'

    # 7b/7c: Proximity (OR logic)
    proximity = 1 if is_idr else 2
    for pp in ptm_sites:
        if 0 < abs(pos - pp) <= proximity:
            if (abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0)) > 0.5
                    or abs(AA_VOLUME.get(mt, 130) - AA_VOLUME.get(wt, 130)) > 50):
                # V18 patch: IDR +/- 1 conservative swap Geta
                if is_idr and abs(pos - pp) == 1:
                    if frozenset({wt, mt}) in CONSERVATIVE_PAIRS_IDR:
                        continue
                return 'C'

    return 'O'
