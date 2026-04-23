"""
Ch11_IDR_Pro: IDR Pro constraint (renamed from legacy Ch5_IDR_Pro).

Physics: In IDR, Pro->X is NOT universal Tier S (unlike structured regions).
Mechanisms:
  1. PRD: PPII helix requires Pro
  2. SLiM interior: Pro constrains binding interface
  3. SLiM boundary (+/- 2): helix N-cap / folding delimiter
  4. PTM +/- 2: Pro backbone constrains enzyme access
  5. Pure tether: no constraint -> OPEN

P72 excluded (rs1042522, known benign polymorphism).
"""
from ...physics.corrections import correction_pro
from ..registry import register_channel


@register_channel(id="Ch11_IDR_Pro", regime="idr", order=11)
def gate_ch11_idr_pro(pos, wt, mt, ctx):
    """Ch11: Pro<->X in IDR (differentiated from structural Ch5_Loop)."""
    ann = ctx.annotation
    if ann is None:
        return 'O'

    if wt == 'P' and mt != 'P':
        if pos in ann.benign_pro_poly:
            return 'O'
        # 1. PRD
        if 62 <= pos <= 93:
            return 'C'
        # 2. Any SLiM interior
        for sdef in ann.slim_defs.values():
            r = sdef['range']
            if r[0] <= pos <= r[1]:
                return 'C'
        # 3. SLiM boundary +/- 2
        for sdef in ann.slim_defs.values():
            r = sdef['range']
            if not (r[0] <= pos <= r[1]):
                if abs(pos - r[0]) <= 2 or abs(pos - r[1]) <= 2:
                    return 'C'
        # 4. PTM +/- 2
        for pp in ann.ptm_sites:
            if 0 < abs(pos - pp) <= 2:
                return 'C'
        # 5. Isolated IDR Pro: OPEN
        return 'O'

    if mt == 'P' and wt != 'P':
        ep = abs(correction_pro(wt, 'P'))
        if ep > 0.3:
            return 'C'
    return 'O'
