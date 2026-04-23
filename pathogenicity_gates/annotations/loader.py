"""
Annotation loader: parse YAML into a typed ProteinAnnotation object.

Supports relative path resolution:
  - PDB/JSON paths in YAML are resolved relative to the YAML file's directory
  - Allows both packaged data (data/p53/annotation.yaml) and user-provided
    external annotations.
"""
import os
import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any


@dataclass
class ProteinAnnotation:
    """Typed representation of a protein annotation YAML."""

    # Protein identity
    name: str
    uniprot: str

    # Structure paths (resolved to absolute paths)
    primary_pdb: str
    primary_chain: str
    oligomer_pdb: Optional[str]
    oligomer_chains: Optional[List[str]]
    coupled_folding_pdbs: List[Dict[str, str]]

    # Domain and IDR ranges
    domains: Dict[str, Tuple[int, int]]
    idr_ranges: Dict[str, Tuple[int, int]]

    # PTM sites: {pos: {'aa': 'S', 'mod': 'phospho', 'enzyme': '...'}}
    ptm_sites: Dict[int, Dict[str, str]]

    # SLiM definitions
    slim_defs: Dict[str, Dict[str, Any]]

    # Special position sets
    benign_pro_poly: List[int] = field(default_factory=list)

    # Data file paths (resolved to absolute paths)
    ppi_union_file: Optional[str] = None
    ppi_interface_file: Optional[str] = None
    partner_face_file: Optional[str] = None
    uniprot_features_file: Optional[str] = None
    clinvar_file: Optional[str] = None
    sequence_file: Optional[str] = None

    # Canonical sequence (loaded lazily via load_sequence)
    _sequence: Optional[str] = None

    def load_sequence(self) -> str:
        """Load UniProt canonical sequence from sequence_file.

        Returns the 1-indexed sequence as a string.
        Position i (1-based) is accessed via seq[i-1].
        """
        if self._sequence is not None:
            return self._sequence
        if self.sequence_file is None:
            raise ValueError(f"No sequence_file defined in annotation for {self.name}")
        with open(self.sequence_file) as f:
            data = json.load(f)
        self._sequence = data['sequence']
        return self._sequence

    def wt_at(self, pos: int) -> Optional[str]:
        """Return the WT amino acid (1-letter) at position `pos` (1-based).

        Returns None if position is out of range or sequence unavailable.
        """
        try:
            seq = self.load_sequence()
        except (ValueError, FileNotFoundError):
            return None
        if 1 <= pos <= len(seq):
            return seq[pos - 1]
        return None


def _resolve_path(base_dir: str, rel_path: Optional[str]) -> Optional[str]:
    """Resolve a path relative to the annotation YAML's directory."""
    if rel_path is None:
        return None
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.abspath(os.path.join(base_dir, rel_path))


def load_annotation(yaml_path: str) -> ProteinAnnotation:
    """Load a protein annotation YAML file.

    Args:
        yaml_path: path to annotation.yaml

    Returns:
        ProteinAnnotation with all file paths resolved to absolute paths.

    Raises:
        FileNotFoundError: if YAML is missing.
        ValueError: if required fields are absent.
    """
    yaml_path = os.path.abspath(yaml_path)
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Annotation YAML not found: {yaml_path}")

    yaml_dir = os.path.dirname(yaml_path)

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # --- Parse protein section ---
    protein = data.get('protein', {})
    name = protein.get('name')
    uniprot = protein.get('uniprot')
    if not name or not uniprot:
        raise ValueError(f"protein.name and protein.uniprot required in {yaml_path}")

    # --- Parse structures section ---
    # Phase 4: primary/oligomer are both OPTIONAL (IDR-only proteins allowed).
    structures = data.get('structures') or {}
    primary = structures.get('primary') or {}
    primary_pdb = _resolve_path(yaml_dir, primary.get('pdb'))
    primary_chain = primary.get('chain', 'A')

    oligomer = structures.get('oligomer') or {}
    oligomer_pdb = _resolve_path(yaml_dir, oligomer.get('pdb'))
    oligomer_chains = oligomer.get('chains')

    coupled_folding_raw = structures.get('coupled_folding', [])
    coupled_folding_pdbs = [
        {
            'pdb': _resolve_path(yaml_dir, cf.get('pdb')),
            'partner': cf.get('partner', ''),
        }
        for cf in coupled_folding_raw
    ]

    # --- Parse domains / idr_ranges (convert list -> tuple) ---
    domains = {k: tuple(v) for k, v in data.get('domains', {}).items()}
    idr_ranges = {k: tuple(v) for k, v in data.get('idr_ranges', {}).items()}

    # --- Parse ptm_sites (ensure int keys) ---
    ptm_raw = data.get('ptm_sites', {})
    ptm_sites = {int(k): v for k, v in ptm_raw.items()}

    # --- Parse slim_defs (convert list -> tuple in range field) ---
    slim_defs = {}
    for slim_name, sdef in data.get('slim_defs', {}).items():
        parsed = dict(sdef)
        if 'range' in parsed:
            parsed['range'] = tuple(parsed['range'])
        slim_defs[slim_name] = parsed

    benign_pro_poly = list(data.get('benign_pro_poly', []))

    ppi_union_file = _resolve_path(yaml_dir, data.get('ppi_union_file'))
    ppi_interface_file = _resolve_path(yaml_dir, data.get('ppi_interface_file'))
    partner_face_file = _resolve_path(yaml_dir, data.get('partner_face_file'))
    uniprot_features_file = _resolve_path(yaml_dir, data.get('uniprot_features_file'))
    clinvar_file = _resolve_path(yaml_dir, data.get('clinvar_file'))
    sequence_file = _resolve_path(yaml_dir, data.get('sequence_file'))

    return ProteinAnnotation(
        name=name,
        uniprot=uniprot,
        primary_pdb=primary_pdb,
        primary_chain=primary_chain,
        oligomer_pdb=oligomer_pdb,
        oligomer_chains=oligomer_chains,
        coupled_folding_pdbs=coupled_folding_pdbs,
        domains=domains,
        idr_ranges=idr_ranges,
        ptm_sites=ptm_sites,
        slim_defs=slim_defs,
        benign_pro_poly=benign_pro_poly,
        ppi_union_file=ppi_union_file,
        ppi_interface_file=ppi_interface_file,
        partner_face_file=partner_face_file,
        uniprot_features_file=uniprot_features_file,
        clinvar_file=clinvar_file,
        sequence_file=sequence_file,
    )
