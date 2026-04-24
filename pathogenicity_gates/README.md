# pathogenicity-gates

Zero-parameter first-principles pathogenicity prediction for missense variants
using the Gate & Channel framework.

**Status**: Phase 5 (CLI ready). Bundled proteins: p53, KRAS, TDP-43, BRCA1.

Reference: Iizumi M. & Iizumi T. (2026) *PLOS Computational Biology* (under review).

## Installation

```bash
pip install -e .
pathogenicity-gates --version
```

## Python API

```python
from pathogenicity_gates import Predictor

pred = Predictor.from_protein("p53")
result = pred.predict(175, 'R', 'H', mode='channels')
print(result['prediction'])   # 'Pathogenic'
print(result['n_closed'])     # 3
```

## Command-Line Interface

Once installed, `pathogenicity-gates` is available on your `PATH`:

```bash
# Single variant
pathogenicity-gates predict --protein p53 --mutation R175H

# Batch from file
pathogenicity-gates predict-batch --protein p53 --input variants.csv

# Detailed diagnostics
pathogenicity-gates explain --protein p53 --mutation R175H

# List available proteins
pathogenicity-gates list-proteins
```

See [`docs/cli_usage.md`](docs/cli_usage.md) for the full CLI reference.

## Documentation

- [`docs/cli_usage.md`](docs/cli_usage.md) — CLI reference
- [`docs/transferability_matrix.md`](docs/transferability_matrix.md) — Three-tier gate classification (UNIVERSAL / ADAPTABLE / SPECIFIC)
- [`docs/phase1_notes.md`](docs/phase1_notes.md) through `phase5_notes.md` — Development notes
