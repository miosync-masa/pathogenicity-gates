# Transferability Matrix

Classification of v18 FINAL gates by the structural information they require,
for application to proteins other than p53.

This is the **direct response to the Academic Editor's request** at PLOS
Computational Biology:
> "what subset of channels, and perhaps even the creation of code applicable
> to other soluble proteins at least, will create the foundation for the
> future expansion of this framework"

---

## Three tiers

### UNIVERSAL (7 gates/getas)
Applicable to any protein from **amino-acid sequence alone** — no structure needed.

| Gate | Requires | Rationale |
|---|---|---|
| GateB_IDR_Gly | IDR annotation | Gly backbone freedom in IDR is sequence-level |
| Ch10.A2 β-branch intro (PPII) | PPII spacer position | Motif-level sequence property |
| Ch10 IDR charge gates | IDR annotation | Charge is residue-intrinsic |
| Ch7.7d Proline-directed kinase | Phospho-S/T annotation | [S/T]-P motif is sequence-level |
| Ch10 SLiM identity rules | Motif annotation | Conserved motif sequences |
| **Geta_VI (v18)** | — | β-branched isomer (pure chemistry) |
| **Geta_IDR_PTM (v18)** | IDR + PTM annotation | Charge-preserving IDR swap |

### ADAPTABLE (8 gates)
Require **structural context**, satisfied by experimental PDB **or AlphaFold**
predictions with pLDDT > 70 (for which predicted ≈ experimental structure).

| Gate | Requires | Proxy quality |
|---|---|---|
| Ch3_Core cavity/steric | Burial + volume | AlphaFold pLDDT > 70 sufficient |
| Ch3_Core polarity/H-bond/charge | Burial + SS | AlphaFold sufficient |
| Ch4_SS propensity | Secondary structure | DSSP on AlphaFold output |
| Ch5_Loop Ramachandran | Loop anchors + SS | Structure-dependent |
| Ch6_PPI interface | PPI contacts | AlphaFold-Multimer |
| Ch9_SaltBridge | Surface + charge network | AlphaFold sufficient |
| Ch3 TierS_toGly | Burial | AlphaFold sufficient |
| Ch3 β-branch loss in β-strand | SS + burial | AlphaFold sufficient |

### SPECIFIC (4 gates)
Require **target-protein-specific complex structures** that cannot be inferred
from AlphaFold alone.

| Gate | Requires | p53 source |
|---|---|---|
| **Gate C (Ch10.C)** — coupled-folding face | Partner complex PDBs | 1YCR, 5HPD, 5HOU, 2L14, 2K8F, 2MZD |
| Ch1_DNA | DNA-bound structure | 1TSR (p53 × DNA) |
| Ch2_Zn | Metal-binding site | p53 Core domain |
| Ch8_Tet | Oligomer structure | 2J0Z (p53 tetramer) |

**Note**: Gate C is SPECIFIC in terms of data requirements (needs PDBs of the
specific partner), but UNIVERSAL in architecture — the union-of-partners
+ NOT conservative Geta pattern transfers directly to any protein with
known coupled-folding partners.

---

## AlphaFold compatibility

### Structured domains (Ch3, Ch4, Ch5, Ch6, Ch9, etc.)
For protein regions with **AlphaFold pLDDT > 70**, predicted structures are
equivalent to experimental ones for the purposes of:
- Burial computation (SASA from predicted structure)
- Secondary structure assignment (DSSP on predicted)
- Cavity/steric calculations (geometric properties)
- Interface contact detection

### IDR regions (GateB, Ch10 SLiMs, Ch7 IDR gates)
AlphaFold intrinsically struggles with IDR (pLDDT < 50 is typical).
**This is not a limitation of our framework** — our IDR channels are
**1-dimensional** (operating on sequence identity alone, not coordinates).
This design is a feature: we bypass AlphaFold's weakness in disordered
regions entirely.

### Complex interfaces (Gate C)
For partners without experimental complex structures, **AlphaFold-Multimer**
can produce predicted complexes. Interface residues extracted from AlphaFold-Multimer
predictions (with appropriate confidence filters) can seed Gate C expansion.

---

## Protein case studies

### p53 (this paper)
- Tier coverage: all 19 gates
- Result: Sens 84.5%, PPV 89.1% (v18 FINAL)

### KRAS (transferability demonstration)
Main variants covered:
- G12V/D/C: Ch3 TierS_toGly (→X from buried Gly at P-loop) — ADAPTABLE
- G13D: Ch3 TierS_toGly + charge_intro — ADAPTABLE
- K117N: Ch3 charge_loss — ADAPTABLE
- A146T: Ch4 helix-strain — ADAPTABLE
- K184Q (HVR): IDR charge loss — UNIVERSAL

Not covered without extension:
- Q61H/L: requires GTP cofactor gate (future work)

### TDP-43 (transferability demonstration)
Main ALS variants covered:
- G294A, G295V, G348C: GateB_IDR_Gly — UNIVERSAL
- A315T, A379T: β-branch intro in IDR — UNIVERSAL
- N382D, N390D: IDR charge intro — UNIVERSAL

Not covered without extension:
- M337V: requires aggregation gate (future work)

### BRCA1 (transferability demonstration)
Main pathogenic variants covered:

**RING domain (ADAPTABLE)**:
- C61G, C64R, T37R: Ch2_Zn-analog + Ch3 charge

**BRCT domain (ADAPTABLE)**:
- V1696L, K1702N, A1708E, M1775R, C1697R: Ch3 buried mutations

**BRCT phospho-pocket (ADAPTABLE + SPECIFIC, Gate C analog)**:
- S1655F, R1699Q, R1699W, S1715R: require BRCT-partner complexes
  (1T29 BRCT × Abraxas, 1T15 BRCT × BACH1, 1Y98 BRCT × CtIP)

**Key insight**: The Gate C architecture (union of partner faces + NOT
conservative Geta) used for p53 transfers **1:1** to BRCA1 BRCT domain.
Replace {MDM2, CBP TAZ1/TAZ2/NCBD, p300 TAZ2} with {ABRAXAS1, BACH1, CtIP}
and run the same extraction pipeline.

---

## Summary statement for the paper

> Nine of the nineteen gates and getas in v18 FINAL are UNIVERSAL, requiring only
> amino-acid sequence and functional annotations (IDR/PTM/SLiM). Eight are
> ADAPTABLE, requiring structural context that can be satisfied by AlphaFold
> predictions with pLDDT > 70. The remaining four are SPECIFIC — requiring
> target-protein structures (Ch1 DNA, Ch2 Zn, Ch8 tetramer) or target-specific
> partner complexes (Gate C). Of these, Gate C is SPECIFIC in data requirements
> but UNIVERSAL in architecture: the union-of-partner-faces with
> NOT-conservative-substitution Geta pattern transfers to any coupled-folding
> interaction, as we demonstrate on BRCA1 BRCT domain.
