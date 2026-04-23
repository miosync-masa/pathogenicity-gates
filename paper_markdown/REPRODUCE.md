# Reproducibility Instructions

## Quick reproduction (assuming v17 base is cloned)

### Prerequisites
```bash
# 1. Clone v17 base
git clone https://github.com/miosync-masa/ZERO_parameter_1st_principles_GateFramework
cd ZERO_parameter_1st_principles_GateFramework

# 2. Install the only dependency
pip install numpy
```

### Step 1: Set up working directory
```bash
mkdir -p work && cd work

# Copy v17 base files
cp ../scr/p53_gate_v17_idr.py .
cp ../scr/ssoc_v332.py .
cp ../Data/tp53_clinvar_missense.json .
cp ../Data/p53_ppi_union.json .
cp ../pdb/1TSR.pdb .

# Copy v18 FINAL code
cp /path/to/p53_v18_final/code/p53_gate_v18_final.py .
cp /path/to/p53_v18_final/code/extract_partner_face.py .
cp /path/to/p53_v18_final/data/partner_face.json .  # precomputed
```

### Step 2: Download required partner PDBs
```bash
# v17 base needs these (not all in GitHub repo)
for id in 2J0Z 1YCR; do
    curl -sSL -o ${id}.pdb "https://files.rcsb.org/download/${id}.pdb"
done

# v18 Gate C expansion needs these
for id in 5HPD 5HOU 2L14 2K8F 2MZD; do
    curl -sSL -o ${id}.pdb "https://files.rcsb.org/download/${id}.pdb"
done

# Verify all PDBs are present
ls -la *.pdb
# Expected: 1TSR, 1YCR, 2J0Z, 2L14, 2K8F, 2MZD, 5HPD, 5HOU
```

### Step 3: (Optional) Re-generate partner_face.json
If you want to verify the partner face extraction from scratch:
```bash
python3 extract_partner_face.py --pdb-dir . --out partner_face.json

# Expected output includes:
#   MDM2           (1YCR.pdb): 11 residues [17-29]
#   CBP_TAZ2       (5HPD.pdb): 33 residues [2-58]
#   CBP_TAZ1       (5HOU.pdb): 45 residues [1-61]
#   CBP_NCBD       (2L14.pdb): 24 residues [19-54]
#   p300_TAZ2_TAD1 (2K8F.pdb): 22 residues [7-35]
#   p300_TAZ2_TAD2 (2MZD.pdb): 22 residues [1-24]
#   UNION total: 59 unique residues
```

### Step 4: Run v18 FINAL evaluation
```bash
python3 p53_gate_v18_final.py
```

**Expected output (numerical)**:
```
p53 Gate & Channel v17 — FULL-LENGTH RESULTS
  Variants evaluated:  1369
  TP: 547   FP: 67   FN: 100   TN: 67
  Sensitivity:   84.5%
  Specificity:   50.0%
  PPV:           89.1%
  NPV:           40.1%
  Hotspots:      9/9
  Parameters:    ZERO
  VUS candidates: 406

Region breakdown:
  Core (94-289)    ... 90.9%
  Tet (325-356)    ... 67.5%
  TAD1 (1-40)      ... 92.1%
  TAD2 (41-61)     ... 76.2%
  PRD (62-93)      ... 66.7%
  Linker (290-324) ... 41.9%
  CTD (357-393)    ... 70.6%
```

## Validation checksums

Expected regional arithmetic:
```
TAD1 + TAD2 + PRD + Core + Linker + Tet + CTD
= 89 + 57 + 98 + 821 + 99 + 106 + 99
= 1369 ✓
```

Confusion matrix total:
```
TP + FP + FN + TN = 547 + 67 + 100 + 67 = 781
Pathogenic = TP + FN = 547 + 100 = 647 ✓
Benign     = FP + TN =  67 +  67 = 134 ✓
VUS        = 1369 - 781 = 588 ✓
```

## Troubleshooting

### "DNS cache overflow" when downloading PDBs
Retry with a short delay; RCSB occasionally rate-limits new connections:
```bash
for attempt in 1 2 3 4 5; do
    curl -sSL -o ${PDB_ID}.pdb "https://files.rcsb.org/download/${PDB_ID}.pdb"
    [[ $(wc -c < ${PDB_ID}.pdb) -gt 1000 ]] && break
    sleep 2
done
```

### FP count differs from expected
Check that `partner_face.json` was generated with all 6 partner structures.
Missing 5HPD or 5HOU (the CBP TAZ2/TAZ1 structures) will cause the union
to be smaller (47 residues instead of 59), and TAD2 Sens will drop.

### Import errors on v17 base
Ensure `p53_gate_v17_idr.py` and `ssoc_v332.py` are in the same directory
as `p53_gate_v18_final.py`.

## Environment used for the reference run

- Python 3.12
- numpy 2.4.4
- Ubuntu 24 container
- Single-threaded, no GPU required
- Total runtime: ~5–10 seconds for full evaluation on 1369 variants
