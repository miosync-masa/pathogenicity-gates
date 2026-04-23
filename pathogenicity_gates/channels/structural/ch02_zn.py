"""
Ch02_Zn: Zn coordination disruption (Layered Cascade Model).

Physics: p53 core has a structural Zn coordinated by C176, C238, C242, H179.
Disruption of coordination (direct ligand or Layer 2 charge perturbation)
abolishes the core fold.

NOTE: The {176, 238, 242, 179} set is currently hardcoded for p53.
Phase 4 will move this to YAML (annotation.zn_ligand_positions).
"""
from ...physics.constants import AA_CHARGE
from ..registry import register_channel

# p53-specific Zn ligand positions. TODO(Phase 4): move to annotation.yaml.
_P53_ZN_LIGANDS = {176, 238, 242, 179}


@register_channel(id="Ch02_Zn", regime="structural", order=2)
def gate_ch02_zn(pos, wt, mt, ctx):
    """Ch2: Zn coordination disruption (Layered Cascade Model)."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'
    if pos in _P53_ZN_LIGANDS:
        return 'C'
    if c['d_zn'] < 8 and abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0)) > 0.5:
        return 'C'
    return 'O'
