"""
Ch12_IDR_Gly: IDR Gly backbone freedom (renamed from legacy GateB_IDR_Gly).

Physics: In IDR, Gly provides maximum backbone freedom (no sidechain).
This freedom is functionally required for coupled folding hinges,
entropic chain behavior, and PTM enzyme access.
G->X introduces sidechain = steric constraint on backbone.
"""
from ..registry import register_channel


@register_channel(id="Ch12_IDR_Gly", regime="idr", order=12)
def gate_ch12_idr_gly(pos, wt, mt, ctx):
    """Ch12: G->X in IDR (loss of backbone freedom)."""
    if wt == 'G' and mt != 'G':
        return 'C'
    return 'O'
