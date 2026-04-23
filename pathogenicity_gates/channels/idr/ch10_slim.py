"""
Ch10_SLiM: SLiM (Short Linear Motif) disruption.

Physics: IDR regions contain functional SLiMs (coupled-folding, PPII,
NLS, aromatic anchors). This channel implements the v18 multi-partner
Gate C as the primary discriminator, plus per-SLiM sub-gates.

V18 patches embedded directly:
  - Gate C uses COUPLED_FOLDING_PARTNER_FACE (6-partner union = 59 res)
  - Conservative-substitution Geta at partner face (dQ<0.3 AND dV<30 AND dh<1.5)
"""
from ...physics.constants import AA_CHARGE, AA_VOLUME, AA_HYDRO
from ..registry import register_channel

PPII_INCOMPATIBLE = {'W', 'F', 'Y'}


def _is_conservative_substitution(wt: str, mt: str) -> bool:
    """V18 Gate C Geta: preserve side-chain chemistry (dQ AND dV AND dh)."""
    if wt == mt:
        return True
    dQ = abs(AA_CHARGE.get(wt, 0) - AA_CHARGE.get(mt, 0))
    dV = abs(AA_VOLUME.get(wt, 130) - AA_VOLUME.get(mt, 130))
    dH = abs(AA_HYDRO.get(wt, 0) - AA_HYDRO.get(mt, 0))
    return (dQ < 0.3) and (dV < 30) and (dH < 1.5)


@register_channel(id="Ch10_SLiM", regime="idr", order=10)
def gate_ch10_slim(pos, wt, mt, ctx):
    """Ch10: SLiM motif disruption (IDR, 1D-based; v18 multi-partner Gate C)."""
    ann = ctx.annotation
    if ann is None:
        return 'O'

    # ── Gate C: multi-partner coupled folding face (v18) ──
    partner_face = ctx.get_partner_face()
    if pos in partner_face and wt != mt:
        if not _is_conservative_substitution(wt, mt):
            return 'C'
        # Conservative -> fall through to other gates

    # ── Gate BND: SLiM boundary Pro (helix breaker) ──
    if wt == 'P' and mt != 'P':
        for sdef in ann.slim_defs.values():
            r = sdef['range']
            if pos == r[0] - 1 or pos == r[1] + 1:
                return 'C'

    # ── Per-SLiM sub-gates ──
    for slim_name, sdef in ann.slim_defs.items():
        r = sdef['range']
        if not (r[0] <= pos <= r[1]):
            continue

        slim_type = sdef.get('type', '')

        # Gate A: PPII incompatibility in PRD
        if slim_type == 'sh3_polyproline':
            if wt not in PPII_INCOMPATIBLE and mt in PPII_INCOMPATIBLE:
                return 'C'
            if wt == 'P' and mt != 'P' and pos not in ann.benign_pro_poly:
                return 'C'

        # Gate A2: PPII spacer beta-branch disruption
        if slim_type == 'sh3_polyproline':
            PPII_SPACER = {'A', 'G'}
            BETA_BRANCHED = {'V', 'I', 'T'}
            if wt in PPII_SPACER and mt in BETA_BRANCHED:
                return 'C'

        # NLS: charge-required signal peptide
        # Accept both YAML position-list form and v17 dict form.
        ccpos = sdef.get('critical_charged_positions')
        if ccpos is None and 'critical_charged' in sdef:
            ccpos = list(sdef['critical_charged'].keys())
        if ccpos and pos in ccpos:
            expected = ann.wt_at(pos)
            if expected is not None and wt == expected:
                q_wt = abs(AA_CHARGE.get(wt, 0))
                q_mt = abs(AA_CHARGE.get(mt, 0))
                if q_wt > 0.5 and q_mt < 0.5:
                    return 'C'

        # Aromatic anchor loss
        capos = sdef.get('critical_aromatic_positions')
        if capos is None and 'critical_aromatic' in sdef:
            capos = list(sdef['critical_aromatic'].keys())
        if capos and pos in capos:
            expected = ann.wt_at(pos)
            if expected is not None and wt == expected and mt not in ('W', 'F', 'Y'):
                return 'C'

        # Protein interaction motif: charge loss
        if slim_type == 'protein_interaction':
            q_wt = abs(AA_CHARGE.get(wt, 0))
            q_mt = abs(AA_CHARGE.get(mt, 0))
            if q_wt > 0.5 and q_mt < 0.3:
                return 'C'

        # CT_reg: charge pattern gate
        if slim_type == 'regulatory_tail':
            dq = abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0))
            if dq > 0.5:
                return 'C'

    return 'O'
