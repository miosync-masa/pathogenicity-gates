# Gate Design Philosophy

This document records the physical reasoning behind each Channel and Gate
in the v18 FINAL framework.

## Guiding Principles

### Principle 1 — Zero New Constructs
All gates are built from established physical quantities (volume, hydrophobicity,
charge, burial, secondary structure, H-bond capacity, Ramachandran angles).
No new empirical constants are introduced; no thresholds are optimized to fit
ClinVar. The framework's power comes from **connecting existing tools in new
combinations**, not from inventing new machinery.

### Principle 2 — Thresholds come from physics, not data
If a variant is missed (FN), the response is to discover a new gate, not to
lower an existing threshold. Thresholds are set from textbook physics
(e.g., hydrophobic desolvation cost, β-strand packing geometry, Ramachandran
conformational entropy) and remain fixed across all analyses.

> **「閾値は人が勝手に動かすもんじゃない」**
> — Thresholds are not something humans should move arbitrarily.

### Principle 3 — Physical channels are independent axes
Each channel captures one distinct physical mechanism. Failure to close a gate
(= Path escapes as FN) is interpreted as **physics absent from the current
channel set**, not as a tuning failure. This principle drives the discovery
of new channels rather than parameter adjustment.

---

## Channel Summary (v18 FINAL — 19 gates/getas total)

| ID | Physics | Requires | Transferability |
|---|---|---|---|
| Ch1 | DNA contact | p53 × DNA complex (1TSR) | SPECIFIC |
| Ch2 | Zn coordination (Layered Cascade) | p53 Core Zn site | ADAPTABLE* |
| Ch3 | Core integrity (cavity, H-bond, charge, etc.) | Burial & SS | ADAPTABLE |
| Ch4 | Secondary structure propensity | SS assignment | ADAPTABLE |
| Ch5 | Loop & Pro/Gly (Ramachandran) | Loop anchor & SS | ADAPTABLE |
| Ch6 | PPI interface (structured) | p53 PPI complexes | ADAPTABLE |
| Ch7 | PTM site & proximity | PTM annotation (UniProt) | UNIVERSAL |
| Ch8 | Tetramer interface | p53 tetramer (2J0Z) | SPECIFIC |
| Ch9 | Surface salt bridge network | Surface & charge | ADAPTABLE |
| Ch10 | SLiM motif (incl. Gate C multi-partner) | Partner complexes | UNIVERSAL + SPECIFIC |
| GateB | IDR Gly constraint | IDR annotation | UNIVERSAL |
| Geta_VI | V↔I isomer exception | — | UNIVERSAL |
| Geta_IDR_PTM | IDR conservative PTM proximity | IDR + PTM site | UNIVERSAL |

\* Ch2_Zn is ADAPTABLE in architecture but p53-specific in current implementation;
  transferable to any Zn-binding protein with known coordinating residues.

---

## Detailed design per channel

### Ch1 — DNA contact
- **Physics**: Side-chain atoms within 5 Å of DNA phosphate/base, weighted by
  H-bond and electrostatic complementarity.
- **Why this works**: DNA recognition in the p53 core requires specific contacts
  (e.g., K120, R248, R273). Disruption of these contacts directly abolishes
  sequence-specific binding.
- **Thresholds from physics**: H-bond donor/acceptor requirement; side-chain
  charge at contact position.

### Ch2 — Zn coordination (Layered Cascade Model)
- **Physics**: Zn(II) tetrahedral coordination requires three Cys + one His (HCCC-motif
  in p53). The Cys sulfur donors have a specific 2.3–2.5 Å geometry. Disruption
  propagates in layers: Layer 1 (direct coordinators) = immediate loss;
  Layer 2 (3–5 Å from Zn) = network disruption; Layer 3 (5–8 Å) = indirect.
- **Why this works**: Zn is the structural core of the p53 DNA-binding domain.
  Loss of any layer corrupts fold stability.
- **PPV in p53**: 100% (40 Path / 0 Benign). Zn gate is categorical.

### Ch3 — Core integrity
The workhorse channel, with 23 sub-gates partitioned by physics:

**Tier S (benign=0 for all subgates — no conformational flexibility can save them)**:
- →Gly in buried site: Ramachandran freedom explosion
- Pro→X: Ramachandran constraint release  
- β-branch loss in β-strand: interlock collapse
- polar→hydro buried: H-bond partner loss
- Met sulfur network: chalcogen bonding loss
- Charge loss deep: desolvation cost

**Tier A (PPV ≥ 95%)**:
- Cavity gates (ΔV, burial, pv, E_cav thresholds)
- Steric clash gates (mirror of cavity)
- Aromatic loss in buried site
- Salt bridge network member

**Tier B (PPV 85–95%)**:
- Moderate volume + burial + hydrophobicity

**Tier D — FP source, requires Geta refinement**:
- Several sub-gates have 1–4 Benign closures; these motivated the V↔I Geta (v18).

### Ch4 — Secondary structure
- **Physics**: Chou-Fasman propensity + backbone strain. Mutations that place
  disfavored residues in helix/β-strand contexts disrupt folding.
- **Why this works**: SS propensity is a measurable, local signal; backbone
  strain at the helix N-cap/C-cap has well-characterized energy penalty.

### Ch5 — Loop & Pro/Gly (Ramachandran unified)
- **Physics**: Pro constrains φ ≈ −60°; Gly allows the full Ramachandran map.
  Loop regions have anchor residues with specific (φ,ψ) requirements.
- **Unified principle**: →Gly and Pro→X are both Ramachandran **endpoints** —
  their disruption is categorical (PPV approaches 100% in loops).

### Ch6 — PPI interface (structured)
- **Physics**: Interface residues identified from multiple PDB structures,
  ranked by number of contacts (n_pdbs_at_position).
- **Implementation**: sub-gate architecture — deeper interface = stricter gate.

### Ch7 — PTM site & proximity (MECE split)
Four mechanistically distinct sub-gates:

- **7a Direct**: Variant at the PTM residue itself (e.g., K→R at a ubiquitin site
  loses the K sidechain required for isopeptide bond formation).
- **7b Structured proximity** (±2 residues): rigid backbone transmits
  perturbation to the PTM site.
- **7c IDR proximity** (±1 residue only): flexible backbone absorbs ±2
  perturbation; only immediate neighbors matter.
- **7d Proline-directed kinase** ([S/T]-P motif): CDK/DYRK/HIPK family kinases
  recognize Pro. P→X adjacent to a phospho-S/T abolishes substrate recognition
  regardless of the X identity.

**Key finding (v18 session)**: Ch7_PTM is **independent in IDR** (50% solo firing
= not co-fired with other channels) but **redundant in Core** (25% solo).
This motivated the IDR-only conservative Geta (Geta_IDR_PTM).

### Ch8 — Tetramer interface
- **Physics**: 2J0Z tetramer structure, SCC exposure gate with burial_asymmetry.
  Rigid hub residues (≥2 chain contacts) are treated as Tier S.

### Ch9 — Surface salt bridge network
- **Physics**: Opposite-charge pairs on the solvent-exposed surface form
  an "electrostatic zipper". Breaking one pair destabilizes the network.
- **PPV**: 100% (12 Path / 0 Benign). Categorical physical signal.

### Ch10 — SLiM motif (incl. Gate C)
Seven sub-gates corresponding to distinct SLiM physics:

- **10.C — Gate C (coupled folding partner face)**:
  In v18, extended from MDM2-only (11 residues, 1YCR) to a 6-partner union
  (59 residues) covering MDM2 + CBP TAZ2/TAZ1/NCBD + p300 TAZ2×2.
  **Geta**: NOT conservative (ΔQ ≥ 0.3 OR ΔV ≥ 30 OR Δh ≥ 1.5) → CLOSED.
- **10.BND — SLiM boundary Pro** (helix breaker at N-cap/C-cap)
- **10.A — PPII incompatibility** (aromatic intro in PRD)
- **10.A2 — PPII spacer β-branch disruption** (A/G → V/I/T)
- **10.NLS — Charge loss at nuclear localization signal**
- **10.ARO — Aromatic anchor loss** (W53, F54)
- **10.PRO — Pro loss in polyproline PPII motif**

### GateB — IDR Gly constraint
- **Physics**: In IDR, Gly provides backbone freedom that is functionally
  required at coupled-folding hinges. Gly→X introduces a sidechain that
  restricts backbone sampling — **"the absence of structure IS function"**.

### Geta_VI — V↔I isomer exception (v18)
- **Physics**: V (Cβ-branched, 2 methyls) and I (Cβ-branched, 1 methyl + 1 ethyl)
  differ by one methylene group. Both are aliphatic, both β-branched, both
  similarly hydrophobic (ΔhW = 0.3), similar volume (ΔV = 26.7 Å³).
- **Mechanism**: applied as a post-closure exception in Ch3_Core.
  If Ch3_Core returns CLOSED AND variant is V→I or I→V, return OPEN.
- **Safety**: 0 Pathogenic variants in ClinVar are affected.
- **Transferability**: UNIVERSAL (applies to any β-branched buried position
  in any protein).

### Geta_IDR_PTM — IDR conservative PTM-proximity exception (v18)
- **Physics**: In IDR, no 3D constraint anchors the side-chain identity.
  For positions adjacent to PTM sites (±1), charge-preserving swaps
  (K↔R, R↔H, S↔T) do not disrupt enzyme recognition.
- **Mechanism**: applied as post-closure exception in Ch7_PTM IDR proximity gates.
- **Safety**: 0 Pathogenic variants affected. Specifically excludes D↔N and E↔Q
  because charge is lost (−1 → 0), which does disrupt PTM recognition.
- **Transferability**: UNIVERSAL (applies to any IDR-adjacent PTM site
  in any protein).

---

## Why Gate C matters for transferability

The Gate C design — **union-of-partner-faces with conservative-substitution
exception** — is the most transferable architecture in the framework:

1. It requires only PDB structures (or AlphaFold-Multimer predictions) of
   protein-partner complexes.
2. The conservative filter uses only amino-acid physicochemical properties
   (no protein-specific parameters).
3. Adding a new partner = adding a new PDB to the extraction script.

This architecture applies directly to:
- **BRCA1 BRCT** × {ABRAXAS1, BACH1, CtIP} (PDB: 1T29, 1T15, 1Y98)
- **BRCA1 RING** × BARD1 (PDB: 1JM7)
- **KRAS** × effector complexes (Raf-RBD, PI3K, RalGDS)
- Any IDR-mediated coupled-folding interaction

See `04_transferability_matrix.md` for the full classification.
