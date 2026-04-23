# Experimental Channels

This directory is the staging area for Gate & Channel experimental
extensions that have not yet been validated across multiple proteins.

## Planned Channels (Phase 4+)

- `ch_llps.py` — Liquid-Liquid Phase Separation (TDP-43 LCD)
- `ch_aggregation.py` — Prion-like aggregation (TDP-43, α-synuclein)
- `ch_membrane.py` — Membrane binding (KRAS CaaX box, myristoylation)
- `ch_nucleotide_binding.py` — GTP/GDP binding (KRAS P-loop)

## Promotion Criteria

A Channel can move out of `experimental/` to `structural/`, `idr/`, or
`universal/` when:

1. Validated on >= 2 proteins
2. Physical mechanism documented (paper or notes)
3. Unit tests covering CLOSED and OPEN cases
4. Peer review (formal or adversarial)

## Registration

Experimental Channels are **not** auto-registered. To activate:

```python
from pathogenicity_gates.channels.experimental import ch_llps  # noqa: F401
# Now ch_llps is registered.
```

This explicit activation prevents accidental use in production.
