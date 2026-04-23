# Hierarchical Gate-Geta Architecture

## The 2-layer IF pattern

Classical pathogenicity gates operate as single-layer IF statements:
```
if (physical_condition_X):
    return CLOSED
```

This produces false positives (FP) when the physical condition is satisfied
but the variant is actually tolerated due to a **secondary physical context**
not captured by the primary condition.

The Gate-Geta architecture introduces a **second layer** that can rescue
specific closure cases as OPEN:
```
# Layer 1: Primary gate
if (physical_condition_X):
    state = CLOSED

# Layer 2: Geta (下駄 — "wooden sandal lift")
if state == CLOSED and (secondary_physical_condition_Y):
    state = OPEN   # rescue
```

## Why "Geta" (下駄)?

In Japanese typesetting, 〓 (called "geta mark" after the wooden sandal) is used
as a placeholder for missing characters. Here, the metaphor extends:
the Geta "lifts" a variant out of closure when secondary physics indicates
tolerance — raising it above the Gate threshold.

## Design constraints for a valid Geta

A Geta is considered valid **only if all three conditions hold**:

### 1. Physical basis, not data fitting
The Geta condition must be expressible purely in terms of physical/chemical
quantities (volume, charge, hydrophobicity, burial, etc.). It must NOT
reference ClinVar labels, variant frequencies, or statistical priors.

### 2. Safety-checked against Pathogenic variants
Before implementation, verify on ClinVar Pathogenic set that **no Path variant
is rescued** by the proposed Geta. If any Path variant matches the Geta
condition, the Geta is invalid — the condition does not cleanly separate
Path from Benign and would cause TP loss.

### 3. Transferable across proteins
The Geta condition must be protein-independent (no residue numbers,
no protein-specific partner identities). It must generalize to any protein
where the primary gate applies.

## Cases examined in this session

### ✅ Accepted: Geta_VI (V↔I swap on Ch3_Core)
- **Condition**: wt = V AND mt = I, OR wt = I AND mt = V
- **Physics**: Both β-branched aliphatic, ΔV = 26.7 Å³, ΔhW = 0.3
- **Safety check**: Path rescued = 0, Benign rescued = 3, VUS rescued = 4
- **Transferable?** YES (applies to any buried β-branched position)

### ✅ Accepted: Geta_IDR_PTM (IDR conservative near PTM site)
- **Condition**: is_idr AND ±1 of PTM site AND {wt,mt} ∈ {{K,R},{R,H},{S,T}}
- **Physics**: Charge-preserving swaps in IDR do not disrupt enzyme recognition
- **Safety check**: Path rescued = 0, Benign rescued = 1 (R290H), VUS rescued = 2
- **Transferable?** YES (applies to any IDR-adjacent PTM site in any protein)

### ✅ Accepted: Geta_GateC_Conservative (not conservative → CLOSE at Gate C)
This is the **inverse Geta pattern**: instead of rescuing to OPEN,
it adds a filter to Gate C that prevents closure for conservative variants.
- **Condition (for closure)**: pos ∈ partner_face AND (ΔQ ≥ 0.3 OR ΔV ≥ 30 OR Δh ≥ 1.5)
- **Physics**: Coupled folding can accommodate side-chain chemistry-preserving
  swaps via induced-fit plasticity
- **Transferable?** YES (applies to any coupled-folding interface)

### ❌ Rejected: Geta_Conservative_Hydro (naive generalization)
- **Condition**: wt AND mt both ∈ {V,I,L,M} with small ΔV, Δh
- **Safety check**: Path rescued = **24** (e.g., V143M, V273L, I251L — all pathogenic in TierS_BetaBranch)
- **Verdict**: Naive hydrophobic-branched grouping fails because V→M, V→L, I→L
  pairs disrupt β-strand packing despite superficial similarity.
- **Lesson**: "Conservative" must be defined strictly (charge-preserving,
  isomeric V↔I), not loosely (any hydrophobic → any hydrophobic).

### ❌ Rejected: Geta_Polar_Conservative (S↔T etc. in Core)
- **Condition**: S↔T or N↔S etc. in Ch3_Core polar positions
- **Safety check**: Path rescued = 11 (e.g., S215T, S241T — Pathogenic in Steric_DeepBuried)
- **Verdict**: Polar→polar is not conservative in Core contexts because
  H-bond geometry and steric fit require exact side-chain identity in deep
  cavities.

### ❌ Rejected: Geta_D↔N and E↔Q at Ch7_PTM±1
- **Safety check**: D391N, D393N are Pathogenic. These are charge-loss events
  (Q: −1 → 0), not conservative swaps.
- **Lesson**: "Conservative" requires **charge preservation**, not just
  isosteric similarity.

---

## Methodology: speaking to each FN and FP individually

The development of v18 Getas followed a strict methodology:

### Step 1 — Decompose each channel into sub-gates
For each channel, identify the distinct sub-conditions that can trigger CLOSED.
Instrument each sub-gate with a tracer that records which variant fires which
sub-gate.

### Step 2 — Identify FP-source sub-gates
For each sub-gate, compute (Path-C, Benign-C, VUS-C). Sub-gates with Benign-C > 0
are **FP sources**. Prioritize those with the largest Benign-C.

### Step 3 — Speak to individual variants
For each FP-source sub-gate, list the Benign variants it fires on AND list
a matched sample of Path variants. Ask:
> "What physical property distinguishes these particular Benign variants
> from the Path variants at the same sub-gate?"

### Step 4 — Propose a candidate Geta
The answer from Step 3 is a candidate Geta condition.

### Step 5 — Safety check
Run the candidate Geta across all ClinVar Pathogenic variants. Count Path rescued.
If > 0, reject or refine.

### Step 6 — Implement and verify
If safety check passes, implement as a post-closure exception and verify
on full evaluation that TP, FP, FN, TN change as predicted.

---

## Philosophical underpinning

> **"FN と FP 両方に1個ずつ なぜ？ 他のとどう違うの？ って語りかけていくしかない"**
> — One must speak to each FN and each FP individually, asking "why?" and
> "how does this differ from the others?"
> (Masamichi Iizumi, 2026-04-23)

This principle rejects **generalized-rule-first** approaches in favor of
**dialogue-with-data-first** methodology. Generalized rules emerge *after*
individual variants are understood physically. The Gate-Geta architecture
is the formalization of this dialogue: Gates encode the general rule;
Getas encode the individualized exceptions that the general rule misses.

## Claim for the paper

The hierarchical Gate-Geta architecture allows **improvement of both
sensitivity and specificity simultaneously** by acting on **different**
variant populations:

- Gates (new channels or expanded faces) increase coverage → +TP
- Getas (exception rules) remove miss-fires → +TN

Because the two layers act orthogonally, they can be developed independently
and stacked. The v18 FINAL stack — Gate C expansion + V↔I Geta + IDR conservative Geta —
demonstrates this additivity empirically (the three changes produce the sum
of their individual effects with no interaction).
