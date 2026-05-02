# pathogenicity-gates

**Zero-parameter, first-principles Gate & Channel framework for missense variant interpretation**

[![PyPI](https://img.shields.io/pypi/v/pathogenicity-gates)](https://pypi.org/project/pathogenicity-gates/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19214739.svg)](https://doi.org/10.5281/zenodo.19214739)

**v18 FINAL** — 12 channels, 2 Getas, 4 bundled proteins, zero fitted parameters.

---

## What is this?

`pathogenicity-gates` is a first-principles framework that classifies missense variants by explicit IF-THEN physical rules — not by regression, not by learned weights, not by latent scores. Each prediction names the specific physical constraint that is violated: a destroyed zinc-binding site, a lost nuclear localization signal, a disrupted coupled-folding interface, a broken proline-directed kinase motif, or any of dozens of other auditable physical gates.

The framework is not a model of biology but a **transcription** of it: the physical laws have been established by generations of structural biologists, biochemists, and polymer physicists. What this package provides is their translation into IF-THEN rules — one mechanism at a time.

---

## Quick Start

```bash
pip install pathogenicity-gates
```

### Single variant
```bash
pathogenicity-gates predict --protein p53 --mutation R175H
# → Pathogenic (Ch02_Zn, Ch03_Core, Ch05_Loop)
```

### Batch prediction
```bash
pathogenicity-gates predict-batch --protein p53 --input variants.csv --output results.json
```

### Explain a call
```bash
pathogenicity-gates explain --protein p53 --mutation R175H
# → Ch02_Zn: Direct Zn ligand (H179 coordination shell). H→R disrupts...
# → Ch03_Core: Buried charge introduction. R175H places +0.1 charge...
# → Ch05_Loop: Loop anchor disruption at L2/L3 junction...
```

### List bundled proteins
```bash
pathogenicity-gates list-proteins
# → p53, kras, tdp43, brca1
```

### Add a new protein
No code modification required. Supply a YAML annotation file + a PDB or AlphaFold structure:
```bash
pathogenicity-gates predict --protein my_protein --config my_protein.yaml --structure my_protein.pdb --mutation G12V
```

---

## 4 Principles

1. **Thresholds are derived from physics, not from data fitting.**
   Ramachandran angles, van der Waals radii, pKa values — all from textbooks.

2. **Gates are IF-THEN, not continuous scores.**
   Binary decisions. No regression. No weighting. Parameters = ZERO.

3. **Missed variants = missing Gate, not a threshold problem.**
   When a pathogenic variant escapes, it names the next IF-THEN to be written.

4. **Incidental closures → physical Geta exception, not threshold relaxation.**
   When a gate expansion creates false positives on legitimately tolerated variants, a Geta (post-closure exception rule) is added. Getas must be protein-independent, rescue zero ClinVar Pathogenic variants, and generalize to any protein where the primary gate applies.

---

## Architecture: 12 Channels + 2 Getas

The framework evaluates each variant across independent channels. A variant is predicted **Pathogenic** if any gate in any channel closes: `n_closed ≥ 1`.

A second hierarchical layer (**Geta**) reverses specific closures whose physical condition predicts tolerance. Gates and Getas operate on **disjoint variant populations** — there is no coverage-vs-tolerance trade-off.

### Structured-domain channels (from 3D coordinates)

| Channel | Physical target | Input |
|---------|----------------|-------|
| **Ch01_DNA** | DNA-contact disruption | Side-chain → DNA distance (1TSR) |
| **Ch02_Zn** | Metal coordination (Zn²⁺) | Cα → Zn distance, charge logic |
| **Ch03_Core** | Symmetry-complete core integrity | Burial, volume, charge, H-bond, aromaticity, sulfur |
| **Ch04_SS** | Secondary-structure incompatibility | Helix/β propensity, backbone strain |
| **Ch05_Loop** | Ramachandran endpoint constraints | Pro→X, Gly→X, loop anchors |
| **Ch06_PPI** | Protein-protein interface | Union of 16 p53 complex structures (66 residues) |
| **Ch07_PTM** | PTM-site chemistry + proximity | 31 UniProt sites, MECE structured/IDR split |
| **Ch08_Oligomer** | Tetramer-interface disruption | Exposure asymmetry, rigid multi-chain hub |
| **Ch09_SaltBridge** | Surface salt-bridge networks | Charged pairs within 10 Å at surface |

### IDR-specific channels (1D, no coordinates)

| Channel | Physical target | Mechanism |
|---------|----------------|-----------|
| **Ch10_SLiM** | Short linear motif disruption | Gate C (6-partner coupled folding), PPII, NLS, aromatic anchor, CT-reg |
| **Ch11_IDR_Pro** | Context-dependent Pro→X | PPII, SLiM interior, SLiM boundary, PTM-proximal, isolated |
| **Ch12_IDR_Gly** | IDR glycine constraint | G→X: side-chain introduction constrains required backbone freedom |

### Geta layer (post-closure exceptions)

| Geta | Acts on | Condition | Rescue |
|------|---------|-----------|--------|
| **Geta_VI** | Ch03_Core | V↔I: both β-branched aliphatic, differ by one CH₂ | 0 Path rescued |
| **Geta_IDR_PTM** | Ch07_PTM (IDR) | Charge-preserving K↔R, R↔H, S↔T within ±1 of PTM site | 0 Path rescued |

### Transferability

| Tier | Channels | Input requirement |
|------|----------|-------------------|
| **UNIVERSAL** | Ch07, Ch10, Ch11, Ch12, Geta_VI, Geta_IDR_PTM | Sequence + annotation only |
| **ADAPTABLE** | Ch03, Ch04, Ch05, Ch06, Ch09 | PDB or AlphaFold (pLDDT > 70) |
| **SPECIFIC** | Ch01 (DNA-bound), Ch02 (metal site) | Target-specific structural input |

---

## Performance (p53, v18 FINAL)

| Metric | Value |
|--------|-------|
| Variants evaluated | 1,369 |
| **Sensitivity** | **84.5%** |
| **PPV** | **89.1%** |
| Core domain sensitivity | 90.9% |
| Hotspots captured | 9/9 |
| VUS reclassified | 407/578 (70.4%) |
| Mol-adjusted PPV | 92.2% |
| **Fitted parameters** | **0** |

### Per-region sensitivity

| Region | Gate type | Sensitivity | PPV |
|--------|-----------|-------------|-----|
| Core (94–289) | 3D | 90.9% | 94.7% |
| Tet (325–356) | 3D | 67.5% | 71.1% |
| TAD1 (1–40) | 1D | 92.1% | 81.5% |
| TAD2 (41–61) | 1D | 76.2% | 71.4% |
| PRD (62–93) | 1D | 66.7% | 76.9% |
| Linker (290–324) | 1D | 41.9% | 65.0% |
| CTD (357–393) | 1D | 70.6% | 70.6% |

### Hotspot capture (9/9)

| Variant | Channels closed |
|---------|----------------|
| R175H | Ch02_Zn, Ch03_Core, Ch05_Loop |
| C176F | Ch02_Zn, Ch03_Core, Ch05_Loop |
| H179R | Ch02_Zn |
| Y220C | Ch03_Core |
| G245S | Ch03_Core, Ch05_Loop |
| R248W | Ch01_DNA, Ch05_Loop, Ch06_PPI |
| R249S | Ch03_Core, Ch05_Loop |
| R273H | Ch01_DNA, Ch03_Core |
| R280K | Ch01_DNA, Ch03_Core |

---

## Cross-protein validation

The same channels — without modification — capture the dominant pathogenic mechanisms in three additional cancer-relevant proteins. Where they fail, the failure names a specific gate yet to be written.

### KRAS
- **Captured:** G12V/D/C, G13D (Ch03_Core, Ch04_SS); K117N, A146T (Ch03_Core); K184Q (IDR charge logic)
- **Gate yet to be written:** Q61H/L → catalytic / cofactor channel (transition-state geometry around Mg²⁺/GTP)

### TDP-43
- **Captured:** G294A, G295V, G348C (Ch12_IDR_Gly); A315T, A382T (Ch10 PPII spacer β-branch); N382D, N390D (Ch10 IDR charge)
- **Gate yet to be written:** M337V → aggregation / LLPS channel (aromatic spacing, charge patterning)

### BRCA1
- **RING domain:** C61G, C64R, T37R (Ch02_Zn analog, Ch03_Core)
- **BRCT buried:** V1696L, K1702N, A1708E, M1775R, C1697R (Ch03_Core)
- **BRCT phospho-pocket:** S1655F, R1699Q, R1699W, S1715R (Gate C with ABRAXAS1 + BACH1 + CtIP; PDBs 1T29, 1T15, 1Y98)

### Gate C architectural portability

The "union of partner faces + non-conservative filter" pattern is protein-independent:

```
p53 TAD  × {MDM2, CBP TAZ2, CBP TAZ1, NCBD, p300 TAZ2}  → 59 union residues, 6 PDBs
BRCA1 BRCT × {ABRAXAS1, BACH1, CtIP}                     → working Gate C, 3 PDBs
```

Replace the partner set → Gate C works. No logic change required.

---

## Gate Specifications

### Channel 1: DNA-contact disruption (Ch01_DNA)

Side-chain heavy-atom to DNA heavy-atom distance from 1TSR (Chain B → Chains E/F).

```
Gate 1.1 — Direct contact (d < 3.5 Å):
  IF wt ∈ {R,K} AND mt ∉ {R,K}  → CLOSED
  IF ΔHB_capacity ≥ 1            → CLOSED
  IF |ΔQ| > 0.5                  → CLOSED

Gate 1.2 — Proximal contact (3.5 ≤ d < 6.0 Å):
  IF ΔQ < -0.5                    → CLOSED
  IF wt ∈ {R,K} AND mt ∉ {R,K,H} → CLOSED
  IF ΔHB_capacity ≥ 2             → CLOSED
```

### Channel 2: Zn coordination (Ch02_Zn)

Layered cascade model. Direct ligands: C176, H179, C238, C242.

```
Gate 2.1 — Direct coordination (Layer 1):
  IF pos ∈ {176, 238, 242, 179} → CLOSED

Gate 2.2 — Electrostatic environment (d_Cα_Zn < 8.0 Å):
  IF d_Cα_Zn < 8.0 AND |ΔQ| > 0.5 → CLOSED
```

### Channel 3: Core integrity (Ch03_Core)

Symmetry-complete packing logic with burial-dependent thresholds.

**Tier S (benign = 0):**
```
S1: X→Gly  — Ramachandran freedom explosion (buried)
S2: S...π  — Chalcogen interaction loss (M/C → non-M/C, aromatic neighbor)
S3: Met sulfur network — Zn seismic isolation (M → non-M/C, n_sul ≥ 3)
S4: β-branch loss in β-strand — interlock collapse (V/I/T → non-V/I/T, buried β)
S5: polar→hydrophobic — H-bond partner loss (deeply buried)
```

**Tier A (symmetric pairs):**
- Volume: cavity ⇄ steric clash
- Charge: loss ⇄ introduction ⇄ sign reversal
- Hydrophobicity: hydro→polar ⇄ polar→hydro
- H-bond: loss ⇄ gain
- Aromatic: gain in buried sites
- Surface hydrophobic exposure
- Electrostatic keystone (≥4 charged neighbors)

**Geta_VI:** V↔I substitutions at buried β-branched positions are rescued — both rotamers fit the same cavity.

### Channel 4: Secondary structure (Ch04_SS)

```
Helix: ΔP_helix < -0.30, backbone strain < -0.5, Pro disruption
Beta:  ΔP_beta < -0.30 (buried), Pro loss in β-structure
```

### Channel 5: Structured loop/Pro/Gly (Ch05_Loop)

```
Pro→X in structured regions → CLOSED (Tier S, position-independent)
Gly→X in L2/L3 loops → CLOSED
X→Pro in helices/strands → CLOSED
Loop anchor large perturbation → CLOSED
```

### Channel 6: PPI interface (Ch06_PPI)

Union of 16 p53 complex structures (66 interface residues in core domain).

```
IF n_pdbs ≥ 3 AND physicochemical_change     → CLOSED
IF min_d < 3.5 AND charge/hydro_change       → CLOSED
IF PPI_nb ≥ 5 AND charge/volume_change       → CLOSED
```

### Channel 7: PTM logic (Ch07_PTM) — MECE split

31 UniProt P04637 sites. Structured and IDR sub-gates have different proximity radii.

```
7a: Direct PTM site hit — any domain
7b: Proximity ±2 — structured domains (OR logic: charge OR volume)
7c: Proximity ±1 — IDR (OR logic: charge OR volume)
7d: [S/T]-P proline-directed kinase motif — Pro ring = recognition element
```

**Confirmed [S/T]-P motifs:**

| Phosphosite | Pro | Kinase | Validation |
|-------------|-----|--------|------------|
| S33 | P34 | CDK5/CDK7 | P34A/T/R/S = all Path (4/4) |
| S46 | P47 | CDK5/DYRK2/HIPK2 | P47T/R = Path (2/2) |
| S315 | P316 | CDK1/CDK2 | P316L/S = Path (2/2) |

**Geta_IDR_PTM:** Charge-preserving substitutions (K↔R, R↔H, S↔T) within ±1 of a PTM site in IDR are rescued — disordered backbone absorbs local geometry, charge and H-bond chemistry preserved.

### Channel 8: Oligomer interface (Ch08_Oligomer)

Tetramerization domain (2J0Z). Exposure asymmetry + rigid multi-chain hub logic.

```
Rigid hub (Tier S): IF n_chains_contacted ≥ 2 → CLOSED
```

### Channel 9: Surface salt bridge (Ch09_SaltBridge)

```
IF burial < 0.5 AND opposite_charge_partner < 10 Å AND |ΔQ| > 0.5 → CLOSED
```

### Channel 10: SLiM motif disruption (Ch10_SLiM)

| Sub-gate | Mechanism | Key variants |
|----------|-----------|-------------|
| **Gate C** | Coupled folding: 6-partner union face (1YCR/5HPD/5HOU/2L14/2K8F/2MZD; 59 residues). Non-conservative substitution at union-face residue → CLOSED | F19X, W23X, L26X, D49H, I50T |
| **Gate A** | PPII incompatibility: aromatic intro in PRD → CLOSED | X→W/F/Y in PRD |
| **Gate A2** | PPII spacer β-branch: {A,G}→{V,I,T} → CLOSED | A69V, A83V, A86V |
| **Gate NLS** | NLS charge loss: basic→neutral → CLOSED | R379C, K373N |
| **Gate ARO** | Aromatic anchor loss in binding pocket → CLOSED | W53L, F54L |
| **Gate CT_reg** | C-terminal regulatory charge pattern disruption → CLOSED | D391N, T387R |

### Channel 11: IDR proline (Ch11_IDR_Pro)

Context-dependent Pro→X in disordered regions. P72 (rs1042522) explicitly excluded.

```
1. PRD polyproline motif → CLOSED (PPII structure)
2. SLiM interior → CLOSED (binding interface geometry)
3. SLiM boundary N-cap (±2) → CLOSED (Pro lacks amide H → helix breaker)
4. PTM proximity (±2) → CLOSED (backbone constrains enzyme access)
5. Isolated IDR Pro → OPEN (no defined functional context)
```

### Channel 12: IDR glycine (Ch12_IDR_Gly)

```
IF is_IDR AND wt == G AND mt ≠ G → CLOSED
```

In disordered regions, backbone freedom **is** the function. G→X introduces a side chain → constrains the conformational space required for coupled folding, flexible linker behavior, or PTM accessibility. The absence of structure is the information.

---

## Symmetry verification (all pairs confirmed)

| Forward | Reverse | Status |
|---------|---------|--------|
| Cavity | Steric clash | ✅ |
| Gly→X | X→Gly | ✅ |
| Pro→X | X→Pro | ✅ |
| Charge loss | Charge intro | ✅ |
| Charge flip | (self-symmetric) | ✅ |
| Hydro→polar | Polar→hydro | ✅ |
| H-bond loss | H-bond gain | ✅ |
| Aromatic loss | Aromatic gain | ✅ |
| β-branch loss | ≈ steric | ✅ |
| PPII compat→incompat | Gate A | ✅ |
| PPII spacer→β-branch | Gate A2 | ✅ |

---

## Tier S summary

### Structured domains (benign = 0)

| # | Gate | Physics |
|---|------|---------|
| 1 | X→Gly (Ch03) | Ramachandran freedom explosion |
| 2 | Pro→X (Ch05) | Ramachandran constraint release |
| 3 | β-branch loss in β-strand (Ch03) | Interlock collapse |
| 4 | Surface salt bridge (Ch09) | Electrostatic zipper disruption |
| 5 | Polar→hydrophobic buried (Ch03) | H-bond partner loss |
| 6 | Met sulfur network (Ch03) | Chalcogen network / Zn seismic isolation |
| 7 | Rigid hub ≥2 chains (Ch08) | Tetramer-interface rigidity |

### IDR hard constraints (1D, no coordinates)

| # | Gate | Physics |
|---|------|---------|
| 8 | Coupled folding (Ch10 Gate C) | 6-partner union face: non-conservative subst. → CLOSED |
| 9 | [S/T]-P kinase motif (Ch07d) | Pro ring loss → kinase substrate unrecognizable |
| 10 | PPII spacer β-branch (Ch10 A2) | {A,G}→{V,I,T} restricts φ-angle |
| 11 | IDR Gly→X (Ch12) | Side-chain introduction constrains required backbone freedom |
| 12 | NLS charge loss (Ch10 NLS) | Basic→neutral abolishes nuclear import signal |

### Geta layer (post-closure exceptions)

| # | Geta | Physics | ClinVar Path rescued |
|---|------|---------|---------------------|
| 13 | Geta_VI | V↔I in buried β-branched positions | 0 |
| 14 | Geta_IDR_PTM | Charge-preserving K↔R, R↔H, S↔T within ±1 of PTM in IDR | 0 |

---

## Next gates to be written

Where the framework fails, it names what to add:

| Category | Example | Gate needed | Data required |
|----------|---------|-------------|---------------|
| Conservative substitutions | D21E, D49E | Partner-pocket fingerprint | Additional complex structures |
| PRD non-Pro positions | A78V, T81I | SH3-like binding pocket | SH3-PRD complex structure |
| Linker orphans | N310K, Q317H | Dynamics / persistence | NMR or cryo-EM dynamics |
| CTD 360–362 cluster | G360V, S362N | SLiM boundary extension | Mutational scanning |
| Isolated IDR Pro→X | P4R, P58R | Polymer compaction | SAXS / smFRET measurements |
| **KRAS Q61H/L** | Q61H | Catalytic / cofactor channel | Transition-state geometry (Mg²⁺/GTP) |
| **TDP-43 M337V** | M337V | Aggregation / LLPS channel | Aromatic spacing, charge patterning |

---

## Repository structure

```
pathogenicity_gates/          # Installable Python package
  ├── channels/               # Channel and Geta logic
  ├── data/                   # Bundled per-protein annotations
  │   ├── p53/                # YAML + PDB + partner_face.json (59 residues)
  │   ├── kras/
  │   ├── tdp43/
  │   └── brca1/
  └── cli.py                  # Command-line interface

tests/                        # pytest suite
Result/                       # Per-variant prediction outputs and run logs
supplementary/                # Machine-readable CSV/JSON (S1–S6 Tables)
paper_markdown/               # Design rationale and gate specifications
```

---

## AlphaFold compatibility

- **ADAPTABLE channels** (Ch03, Ch04, Ch05, Ch06, Ch09): accept AlphaFold structures with pLDDT > 70.
- **UNIVERSAL channels** (Ch07, Ch10, Ch11, Ch12, Getas): operate from sequence and annotation alone — AlphaFold confidence is irrelevant.
- **Gate C extension**: AlphaFold-Multimer predictions can supply partner-complex interfaces where experimental structures are unavailable.

---

## Reproducibility

The framework is deterministic and rule-based. The archived Zenodo release and PyPI package v0.5.1 provide the version-locked snapshot:

```bash
pip install pathogenicity-gates==0.5.1
pathogenicity-gates predict-batch --protein p53 \
    --input <bundled tp53_clinvar_missense.csv> \
    --output v18_final_results.json
```

Any change in outputs is traceable to a changed input file, an altered gate definition, or a scope correction — never to stochastic optimization.

---

## Citation

If you use this framework, please cite:

> M.Iizumi. A zero-parameter first-principles gate framework for full-length TP53 missense variant interpretation. *PLOS Computational Biology* (under review). 2026.

**Zenodo DOI:** [10.5281/zenodo.19214741](https://doi.org/10.5281/zenodo.19214741)

**ORCID:** [0009-0007-0755-403X](https://orcid.org/0009-0007-0755-403X)

---

## Acknowledgments

AI tools were used in a limited, supervised manner to support framework development, manuscript drafting, code inspection, and hypothesis exploration. Specific contributions:
No AI tool was used as a substitute for scientific judgment. All framework definitions, analyses, and interpretations were reviewed and approved by the author.

---

## License

MIT

---

*"If you can turn a classifier into a puzzle game, it's not a black box."*

Credits: Ramachandran (1963) · Flory (1969) · Barlow & Thornton (1983) · Burley & Petsko (1985)
