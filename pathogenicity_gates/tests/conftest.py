"""Pytest fixtures for pathogenicity-gates Phase 1 regression tests.

IMPORTANT:
  Tests require PDB/JSON files in pathogenicity-gates-main/ (data root).
  The fixture `chdir_to_data_root` automatically chdir there so that
  legacy code's relative file references work.
"""
import os
import json
import pytest


@pytest.fixture(scope="session")
def data_root():
    """Path to pathogenicity-gates-main/ where PDBs/JSONs live."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))

    required = [
        "1TSR.pdb", "2J0Z.pdb", "1YCR.pdb",
        "p53_ppi_union.json", "partner_face.json",
        "tp53_clinvar_missense.json",
    ]
    missing = [f for f in required if not os.path.exists(os.path.join(root, f))]
    if missing:
        pytest.skip(f"Required data files not found in {root}: {missing}")
    return root


@pytest.fixture(scope="session")
def clinvar_variants(data_root):
    """Load all ClinVar variant classifications (1374 total)."""
    with open(os.path.join(data_root, "tp53_clinvar_missense.json")) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def in_scope_variants(clinvar_variants):
    """Filter to Phase 1 in-scope variants (1369 total).

    In-scope regions: Core (94-289), Tet (325-356), IDR (1-93, 290-324, 357-393).
    """
    IDR_RANGES = [(1, 40), (41, 61), (62, 93), (290, 324), (357, 393)]
    in_scope = {}
    for k, v in clinvar_variants.items():
        pos = int(k.split('_')[0])
        if 94 <= pos <= 289:
            in_scope[k] = v
        elif 325 <= pos <= 356:
            in_scope[k] = v
        elif any(lo <= pos <= hi for lo, hi in IDR_RANGES):
            in_scope[k] = v
    return in_scope


@pytest.fixture(scope="session", autouse=True)
def chdir_to_data_root(data_root):
    """Chdir to data root so legacy relative paths work.

    Legacy code uses bare filenames like open('1TSR.pdb').
    This fixture ensures those resolve correctly during tests.
    """
    orig_cwd = os.getcwd()
    os.chdir(data_root)
    yield
    os.chdir(orig_cwd)
