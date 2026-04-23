"""
Main Predictor API for pathogenicity-gates.

Phase 1 API (legacy compat):
    Predictor.from_legacy_v18("p53")
Phase 2 API (YAML-driven, adapter-based):
    Predictor.from_yaml("annotation.yaml")
    Predictor.from_protein("p53")
Phase 3 API (regime-based channel dispatch, opt-in):
    pred = Predictor.from_protein("p53")
    pred.predict(pos, wt, mt, mode="channels")
"""
import os
from typing import Dict, Any, List, Optional

# Force channel registration on import (side effect via __init__).
from . import channels  # noqa: F401


class Predictor:
    """Gate & Channel pathogenicity predictor.

    Three entry points produce BYTE-FOR-BYTE identical predictions for p53:
        Predictor.from_legacy_v18("p53")       # Phase 1
        Predictor.from_yaml("annotation.yaml") # Phase 2
        Predictor.from_protein("p53")          # Phase 2

    Phase 3 adds a regime-based channel dispatch mode (opt-in):
        pred.predict(pos, wt, mt, mode="channels")
    """

    def __init__(self, _impl=None, _context=None, _annotation=None, _ctx_obj=None):
        self._impl = _impl
        self._context = _context
        self._annotation = _annotation
        self._ctx_obj = _ctx_obj

    # ─────────────────────────────────────────────────────────────
    # Phase 1 API
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def from_legacy_v18(cls, protein: str = "p53") -> "Predictor":
        """Phase 1: wrap legacy v18 implementation (hardcoded data)."""
        if protein.lower() != "p53":
            raise NotImplementedError(
                f"Phase 1 legacy supports 'p53' only (got '{protein}')."
            )

        from .adapters.v18_adapter import restore_legacy_constants
        restore_legacy_constants()

        from .legacy import p53_gate_v18_final  # noqa: F401 (v18 patches)
        from .legacy import p53_gate_v17_idr as v17

        ctx, ss_map, backbone, atoms, all_heavy, atom_xyz_lookup = \
            v17.setup_core_domain()
        tet_interface, tet_exposure, tet_chain_contacts = \
            v17.setup_tetramer()
        PPI, ppi_nb_count = v17.setup_ppi(atom_xyz_lookup=atom_xyz_lookup)
        sb_partners = v17.setup_salt_bridge(ctx, atom_xyz_lookup)

        context = {
            'ctx': ctx,
            'PPI': PPI,
            'ppi_nb_count': ppi_nb_count,
            'tet_interface': tet_interface,
            'tet_exposure': tet_exposure,
            'tet_chain_contacts': tet_chain_contacts,
            'sb_partners': sb_partners,
        }
        return cls(_impl=v17.predict_pathogenicity, _context=context)

    # ─────────────────────────────────────────────────────────────
    # Phase 2 API (also builds Phase 3 PredictionContext)
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Predictor":
        """Phase 2: YAML-driven (adapter + legacy predict). Also builds
        a PredictionContext object for Phase 3 channel mode access."""
        from .annotations.loader import load_annotation
        from .adapters.v18_adapter import (
            build_context_from_annotation,
            override_legacy_constants_from_annotation,
        )
        from .channels.context import PredictionContext

        ann = load_annotation(yaml_path)
        override_legacy_constants_from_annotation(ann)
        context = build_context_from_annotation(ann)

        ctx_obj = PredictionContext(
            residue_ctx=context['ctx'],
            ppi_union=context['PPI'],
            ppi_nb_count=context['ppi_nb_count'],
            tet_interface=context['tet_interface'],
            tet_exposure=context['tet_exposure'],
            tet_chain_contacts=context['tet_chain_contacts'],
            sb_partners=context['sb_partners'],
            annotation=ann,
        )

        from .legacy import p53_gate_v17_idr as v17
        return cls(
            _impl=v17.predict_pathogenicity,
            _context=context,
            _annotation=ann,
            _ctx_obj=ctx_obj,
        )

    @classmethod
    def from_protein(cls, protein: str) -> "Predictor":
        """Phase 2: load from bundled annotation."""
        bundled_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data', protein.lower()
        )
        yaml_path = os.path.join(bundled_dir, 'annotation.yaml')
        if not os.path.exists(yaml_path):
            raise NotImplementedError(
                f"Bundled annotation for protein '{protein}' not found. "
                f"Available: {cls.list_bundled_proteins()}"
            )
        return cls.from_yaml(yaml_path)

    @classmethod
    def list_bundled_proteins(cls) -> List[str]:
        """List all proteins with bundled annotations."""
        data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data'
        )
        if not os.path.isdir(data_dir):
            return []
        return sorted([
            d for d in os.listdir(data_dir)
            if os.path.isdir(os.path.join(data_dir, d))
            and os.path.exists(os.path.join(data_dir, d, 'annotation.yaml'))
        ])

    # ─────────────────────────────────────────────────────────────
    # Prediction API (shared; Phase 3 adds `mode` parameter)
    # ─────────────────────────────────────────────────────────────
    def predict(self, pos: int, wt: str, mt: str,
                mode: str = "legacy") -> Dict[str, Any]:
        """Predict pathogenicity for a single missense variant.

        Args:
            pos, wt, mt: variant definition
            mode: "legacy" (default; calls v17 predict_pathogenicity) or
                  "channels" (Phase 3 regime-based channel dispatch).
                  Both modes MUST produce identical n_closed and prediction
                  for p53 (verified by test_phase3_channel_isolation).
        """
        if mode == "legacy":
            return self._predict_legacy(pos, wt, mt)
        elif mode == "channels":
            return self._predict_channels(pos, wt, mt)
        else:
            raise ValueError(f"Unknown mode: {mode!r}. Use 'legacy' or 'channels'.")

    def _predict_legacy(self, pos: int, wt: str, mt: str) -> Dict[str, Any]:
        """Phase 1/2 path: legacy predict_pathogenicity call."""
        if self._impl is None:
            raise RuntimeError("Predictor not initialized.")
        result = self._impl(pos, wt, mt, **self._context)
        result['pos'] = pos
        result['wt'] = wt
        result['mt'] = mt
        return result

    def _predict_channels(self, pos: int, wt: str, mt: str) -> Dict[str, Any]:
        """Phase 3 path: regime-based channel dispatch."""
        if self._ctx_obj is None:
            raise RuntimeError(
                "PredictionContext not available. Use from_yaml() or "
                "from_protein() to enable channel mode."
            )

        from .channels.registry import get_applicable_channels

        regime = self._ctx_obj.get_physics_regime(pos)
        if regime == 'unknown':
            return {
                'prediction': 'Unknown',
                'n_closed': 0,
                'channels': {},
                'pos': pos, 'wt': wt, 'mt': mt,
                'regime': regime,
            }

        ch_states: Dict[str, str] = {}
        for ch_id, ch_info in get_applicable_channels(regime):
            ch_states[ch_id] = ch_info['fn'](pos, wt, mt, self._ctx_obj)

        n_closed = sum(1 for s in ch_states.values() if s == 'C')
        prediction = 'Pathogenic' if n_closed >= 1 else 'Benign/VUS'

        return {
            'prediction': prediction,
            'n_closed': n_closed,
            'channels': ch_states,
            'pos': pos, 'wt': wt, 'mt': mt,
            'regime': regime,
        }
