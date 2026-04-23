"""
Typed prediction context for Gate & Channel framework.

Provides structured access to per-residue features and global protein
context used by all Channels. The regime-based dispatch lives here:
`get_physics_regime(pos)` decides which Channel set applies to a position.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class PredictionContext:
    """Full prediction context for a single protein.

    All Channels receive this object. They should only access the fields
    relevant to their physical regime.
    """
    # Per-residue structural context (populated by setup_core_domain).
    # Key: residue number (1-indexed). Value: dict with keys such as
    #   aa, bur, pf, ss, nba, hnf, bnf, lf, n_aro, n_sul, n_charged_nb,
    #   dcb, nbr, d_dna, d_zn, hpos
    residue_ctx: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    # PPI (protein-protein interface) information.
    ppi_union: Dict[int, Dict[str, int]] = field(default_factory=dict)
    ppi_nb_count: Dict[int, int] = field(default_factory=dict)

    # Oligomer (tetramer) information.
    tet_interface: Dict[int, float] = field(default_factory=dict)
    tet_exposure: Dict[int, float] = field(default_factory=dict)
    tet_chain_contacts: Dict[int, int] = field(default_factory=dict)

    # Salt bridge partners.
    sb_partners: Dict[int, List[int]] = field(default_factory=dict)

    # Protein annotation (YAML-loaded ProteinAnnotation).
    # Typed as Any to avoid circular import.
    annotation: Optional[Any] = None

    # Cached partner face union (lazy-loaded).
    _partner_face_cache: Optional[set] = None

    def get_residue(self, pos: int) -> Optional[Dict[str, Any]]:
        """Return residue context dict, or None if pos not in primary structure."""
        return self.residue_ctx.get(pos)

    def get_physics_regime(self, pos: int) -> str:
        """Determine the physical regime for a given position.

        Returns 'structural', 'idr', or 'unknown'.

        Rules:
          1. pos in residue_ctx              -> 'structural'
          2. pos in annotation.domains['tet'] -> 'structural'
          3. pos in any annotation.idr_ranges -> 'idr'
          4. otherwise                        -> 'unknown'
        """
        if pos in self.residue_ctx:
            return 'structural'

        if self.annotation is not None and 'tet' in self.annotation.domains:
            lo, hi = self.annotation.domains['tet']
            if lo <= pos <= hi:
                return 'structural'

        if self.is_idr_position(pos):
            return 'idr'

        return 'unknown'

    def is_idr_position(self, pos: int) -> bool:
        """Check if a position is within any IDR range."""
        if self.annotation is None:
            return False
        for rng in self.annotation.idr_ranges.values():
            if rng[0] <= pos <= rng[1]:
                return True
        return False

    def get_partner_face(self) -> set:
        """Return coupled folding partner-face residue set.

        Loads from annotation.partner_face_file on first call, then caches.
        """
        if self._partner_face_cache is not None:
            return self._partner_face_cache
        if self.annotation is None or self.annotation.partner_face_file is None:
            self._partner_face_cache = set()
            return self._partner_face_cache
        import os, json
        if not os.path.exists(self.annotation.partner_face_file):
            self._partner_face_cache = set()
            return self._partner_face_cache
        with open(self.annotation.partner_face_file) as f:
            data = json.load(f)
        self._partner_face_cache = set(data.get('union', []))
        return self._partner_face_cache
