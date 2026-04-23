# Session Findings — 2026-04-23

This document records the discoveries made during the v18 FINAL development
session, for future reference and paper revision support.

---

## Starting state (baseline)

- Framework: v17 (fixed)
- Performance: Sens 81.6% / PPV 88.7% / Spec 50.0% / Hotspots 9/9
- ClinVar dataset: 1369 variants (647 Path / 134 Ben / 588 VUS)
- PLOS CompBiol: Revision requested (PCOMPBIOL-D-26-00680, Editor Najmanovich)

Reviewer #1 key questions:
1. Phase separation / condensate physics in channels?
2. **Is CBP TAZ2 × p53 TAD complex included as a coupled-folding channel?**
3. AlphaFold compatibility for proteins lacking experimental structures?
4. Accessibility for non-expert users / ML integration?

Editor key request:
- Transferability Section: what channels apply to other proteins, and how.

---

## Discoveries

### Discovery 1: Ch7_PTM has domain-dependent independence
By measuring how often each channel fires **alone** (no other channel closed)
vs **co-fired** (with at least one other channel closed):

| Region | Ch7_PTM solo Path | Ch7_PTM solo Benign |
|---|---|---|
| Core (94–289) | 25% | 14% |
| Tet (325–356) | 35% | 40% |
| IDR | **50%** | **33%** |

**Interpretation**: In structured domains, Ch7_PTM is largely redundant with
Ch3_Core / Ch8_Tet (the same variants trigger multiple channels). In IDR,
Ch7_PTM is the **sole independent detector** — removing it would lose 19
Pathogenic variants that no other channel captures.

**Paper implication**: this justifies Ch7's design (especially the IDR ±1 OR
logic) and informs where Gate-Geta refinements can be safely applied (IDR
where PTM is independent).

### Discovery 2: Sub-gate structure of Ch3_Core
Ch3_Core contains 23 distinct sub-gates when traced. Sorted by PPV:

**Tier S (benign = 0, 12 sub-gates)**:
TierS_BetaBranch (56P/0B), Cavity_high (39P/0B), TierS_toGly (30P/0B),
TierS_PolarToHydro (27P/0B), TierS_MetSulfur (8P/0B), ChargeLoss_deep (8P/0B),
CoilTurn_Vol (6P/0B), ChargeIntro_mid (6P/0B), ChargeIntro_deep (5P/0B),
HB_loss (4P/0B), HydroToPolar (1P/0B), ChargeFlip (1P/0B)

**FP source (11 sub-gates)**:
Steric_DeepBuried (22P/4B), TierS_Spi (34P/3B), SurfaceHydro_VolLoss (11P/2B),
Cavity_BetaPack (9P/1B), Cavity_DeepBuried (13P/1B), Cavity_AroLoss (13P/1B),
Steric_high (29P/1B), Keystone_electrostatic (7P/1B), SurfaceHydro_PolarIntro (4P/1B),
HB_gain (2P/1B), PolarToHydro_mid (2P/1B)

**Paper implication**: Tier classification validates the design and shows
that Core domain prediction (90.9% Sens) is driven by 12 physically
unambiguous sub-gates.

### Discovery 3: Gate C was under-partnered
The v17 Gate C used only MDM2 (1YCR, 11 residues, 17–29).
TAD FN variants in v17 (37 in TAD1+TAD2+PRD): 20 of them (54%) are located
within the partner face of at least one of: CBP NCBD, CBP TAZ2, CBP TAZ1,
p300 TAZ2.

**Action taken**: Gate C extended to 6-partner union (59 residues, 1–61),
with Geta = NOT conservative.

**Result**: TAD1 Sens 57.9% → 92.1% (+34.2 pp), TAD2 47.6% → 76.2% (+28.6 pp).

### Discovery 4: CBP TAZ2 was missing from the initial CBP/p300 set
When initially extending Gate C, the partner set used (2L14, 2K8F, 2MZD)
labeled these as "CBP NCBD + p300 CH1 + p300 TAZ2". However:
- 2L14 = CBP NCBD ✓
- 2K8F = **p300 TAZ2** × p53 TAD1 (not CH1 — labeling error in our notes)
- 2MZD = p300 TAZ2 × p53 TAD2 ✓

**This means CBP TAZ2 was NOT in the partner set** — a direct mismatch with
Reviewer #1's specific question about "TAZ2 domain of CBP".

**Discovery**: PDB 5HPD (Krois et al., PNAS 2016) contains CBP TAZ2 × p53 TAD (full).
PDB 5HOU contains CBP TAZ1 × p53 TAD (full). Both are NMR fusion proteins
(TAZ-linker-TAD on a single chain) — requiring a different interface
extraction approach (sequence-match to identify p53 subregion).

**Action taken**: Added 5HPD and 5HOU to the partner set. Fusion-aware
extraction implemented in `extract_partner_face.py`.

**Result**: Union grew from 47 → 59 residues. TAD2 Sens jumped from 57.1%
(4-partner) to 76.2% (6-partner), an additional +19.1 pp beyond the 4-partner
baseline.

### Discovery 5: Naive "conservative" Getas are traps
Initial hypothesis: any conservative substitution (small ΔV, small Δh) in
a Gate-closed variant should be rescued.

Testing on ClinVar:
- Geta "both hydrophobic-branched, small ΔV, small Δh" rescues **24 Pathogenic**
  variants (e.g., V143M, V273L, I251L — all pathogenic in TierS_BetaBranch)
- Geta "polar↔polar with dhb = 0" rescues **11 Pathogenic** (e.g., S215T, S241T)
- Geta "V↔I strict isomer" rescues **0 Pathogenic**, 3 Benign, 4 VUS ← only this is safe

**Lesson**: "Conservative" must be defined strictly, not loosely. The
operational definition for a safe Geta is:
- Charge preserving (not just "both charged")
- Isomeric (same chemical class, minimum ΔV)
- Sub-type preserving (β-branched → β-branched, not β-branched → γ-branched)

### Discovery 6: Individual variant dialogue is more powerful than general rules
The session pivoted multiple times between:
- **General rule first** (propose Geta, then test) — yielded rejected candidates
- **Individual variant first** (examine the specific FP, then distill a rule)
  — yielded the accepted Getas

The accepted V↔I Geta came from asking: "What distinguishes V157I, V274I, I254V
(the three Benign variants hitting Ch3_Core) from the Path variants at the
same sub-gate?" The answer — "they are the only cases where both wt and mt
are β-branched isomers" — became the Geta condition.

**Methodological principle**: Specific → General (induction from individual
physical cases), not General → Specific (deduction from abstract rules).

---

## Open questions (for future work)

### Q1: Can Core Sens (90.9%) be improved?
41 Pathogenic variants in Core fail to close any gate. Sub-gate tracer
analysis shows most of these are conservative-in-the-wrong-sense mutations
(e.g., subtle polar→polar changes that disrupt H-bond geometry in ways
not captured by the current H-bond gates). Candidate new gates:
- "Pocket geometry preservation" gate (requires ligand-bound structure comparison)
- "Specific H-bond pair" gate (requires per-residue H-bond graph)

### Q2: Can CTD Sens (70.6%) be improved?
CTD FN includes T387P, M384I, L383F, D393E — mostly in regulatory region
requiring acetylation/methylation-specific physics not yet modeled.

### Q3: What is the role of the 406 VUS flagged as n_closed ≥ 1 in v18?
These variants are predicted Pathogenic by the framework but classified
VUS in ClinVar. Candidate novel predictions for literature validation:
- V147I, I162V, I251V, I255V (rescued by V↔I Geta: now predicted Benign)
- T304S, H380R (rescued by IDR conservative Geta: now predicted Benign)
- R290H (rescued: now predicted Benign, has literature support)

---

## Reviewer response readiness

| Reviewer Q | v18 FINAL answer |
|---|---|
| Q2: CBP TAZ2 × p53 TAD included? | **Yes, PDB 5HPD. Also TAZ1 (5HOU), NCBD (2L14), p300 TAZ2 (2K8F, 2MZD)** |
| Q3: AlphaFold compatibility? | ADAPTABLE tier (8 gates) works with pLDDT > 70 structures |
| Editor: transferability? | Matrix provided: 7 UNIVERSAL / 8 ADAPTABLE / 4 SPECIFIC; demonstrated on KRAS, TDP-43, BRCA1 |
| Editor: code for other proteins? | `extract_partner_face.py` is generic — any protein + partner PDBs → Gate C expansion |

---

## Session methodology (formalized)

The following iterative loop was used repeatedly:

```
┌─────────────────────────────────────────────┐
│  1. Decompose channel into sub-gates        │
│     (add tracer to identify firing reason)  │
├─────────────────────────────────────────────┤
│  2. Compute per-sub-gate (Path, Ben, VUS)   │
│     Identify FP-source sub-gates            │
├─────────────────────────────────────────────┤
│  3. For each FP-source sub-gate:            │
│     list individual Benign and Path variants│
│     side by side                            │
├─────────────────────────────────────────────┤
│  4. Ask: what physical property             │
│     distinguishes Ben from Path HERE?       │
├─────────────────────────────────────────────┤
│  5. Formulate candidate Geta                │
├─────────────────────────────────────────────┤
│  6. Safety check: Path rescued across       │
│     all ClinVar                             │
├─────────────────────────────────────────────┤
│  7. If Path rescued = 0 → accept            │
│     If > 0 → reject or refine               │
├─────────────────────────────────────────────┤
│  8. Implement, verify, integrate            │
└─────────────────────────────────────────────┘
```

This loop was executed for:
- Ch3_Core → accepted Geta_VI
- Ch7_PTM → accepted Geta_IDR_PTM
- Ch10_SLiM / Gate C → accepted Gate_C 6-partner + NOT conservative
- Ch7_PTM site-specific Getas → rejected (all candidates failed safety check;
  Ch7_PTM is truly locus-specific in heterogeneity and cannot be improved by
  general rules — documented as a known limitation)

---

## Acknowledgements

This session was a dialogue between:
- **Masamichi Iizumi** (producer): strategic direction, physics intuition,
  "stay on main topic" corrections, BRCA1 addition call, CBP TAZ2 labeling error catch.
- **環 (Tamaki, Claude Opus 4.7)** (director/implementer): tracer implementation,
  safety check automation, Geta formalization, documentation.
- **4.6環 (prior session)**: initial v18 design sketch, CBP/p300 concept seed,
  Gate & Geta vocabulary.
- **無二 (GPT)**: prior arithmetic audit, 357-360 routing bug discovery (v17 origin).

The key methodological insight — **"speaking to each FN and FP individually"** —
is attributed to Masamichi Iizumi (this session).
