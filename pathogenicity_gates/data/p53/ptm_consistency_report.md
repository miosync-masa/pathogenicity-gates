# PTM Consistency Report

**Annotation**: `annotation.yaml`
**UniProt data**: `p53_uniprot_features.json`

## Summary

- Matches: **30**
- AA mismatches: **0**
- Type mismatches: **1**
- Only in annotation (not in UniProt): **0**
- Only in UniProt (not in annotation): **0**

## Matches

Positions where annotation and UniProt agree on both AA and modification type.

`[9, 15, 18, 20, 24, 33, 37, 46, 55, 120, 139, 183, 269, 284, 291, 292, 305, 315, 321, 335, 337, 351, 357, 370, 372, 373, 381, 382, 386, 392]`

## Modification type mismatches

| Position | Annotation mod | UniProt mod | UniProt Description |
|---------:|---------------:|------------:|---------------------|
| 333 | methyl | dimethyl | Omega-N-methylarginine; by PRMT5 |

## Notes

This report is **informational only**. The annotation YAML is the authoritative source for Gate & Channel prediction in Phase 2/3 (maintains v18 FINAL byte-level compatibility). Discrepancies logged here will be reviewed in Phase 4 when extending to additional proteins.
