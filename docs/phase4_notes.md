# Phase 4 作業メモ

**日付**: 2026-04-24
**担当**: ClaudeCode (メカタマキ)
**結果**: ✅ **74 passed + 5 xfailed (32 秒)**

## テスト結果

### Phase 1-3 継続 (51/51 pass)
- Phase 1: 15/15
- Phase 2:  9/9
- Phase 3: 27/27

### Phase 4 新規 (23 passed, 5 xfailed)
- Bundled proteins check: 1/1
- KRAS expected firing:    2/2
- KRAS future work:        3 xfail (期待通りの未カバー)
- TDP-43 expected firing:  4/4
- TDP-43 future work:      2 xfail (期待通りの未カバー)
- TDP-43 regime/primary-PDB-free: 2/2
- BRCA1 expected firing:   8/8
- p53 unchanged:           1/1
- YAML loads (3 proteins): 3/3
- Channels mode (4 proteins): 1/1
- Tet range scoping:       1/1

## タンパク別実装サマリ

### KRAS (P01116)
- [x] 4OBE.pdb 配置 (X-ray, 2.0Å, GTP analog)
- [x] `kras_uniprot_features.json` 生成 (UniProt API)
- [x] `kras_sequence.json` 生成 (canonical isoform 4B, 189 aa)
- [x] annotation.yaml 作成
- [x] ADAPTABLE 発火: K117N, A146T (2/2)
- [ ] FUTURE (catalytic): G12V/D, G13D (3 xfail)

### TDP-43 (Q13148)
- [x] `tdp43_uniprot_features.json` 生成
- [x] `tdp43_sequence.json` 生成 (414 aa)
- [x] annotation.yaml 作成 (**primary PDB なし**)
- [x] UNIVERSAL 発火: G294A, G295V, G348C, N390D (4/4)
- [ ] FUTURE (LLPS): A315T, A382T (2 xfail)

### BRCA1 (P38398)
- [x] 1JM7 (RING) + 1JNX (BRCT) merge → `brca1_ring_brct.pdb`
- [x] `brca1_uniprot_features.json` 生成
- [x] `brca1_sequence.json` 生成 (1863 aa)
- [x] annotation.yaml 作成
- [x] ADAPTABLE 発火: 8/8 (C61G, C64R, T37R, V1696L, K1702N, M1775R, C1697R, A1708E)

## Transferability 実測値

| Tier | 目標 | 実測 |
|------|-----|------|
| UNIVERSAL | 4/4 | **4/4 (100%)** |
| ADAPTABLE | 10/10 | **10/10 (100%)** |
| SPECIFIC | 2/2 | **2/2 (100%)** |
| FUTURE (catalytic, LLPS) | n/a | 0/5 (期待通り未カバー) |

## 実装中に気づいたこと (3件の修正を要した)

### 1. DNA-free structures で broadcasting エラー
`setup_core_domain` (legacy) が `dna_arr` (DNA atom array) を常に使う
コードで、KRAS/BRCA1 のような DNA なし PDB で numpy broadcasting 失敗。
修正: `has_dna = len(dna_arr) > 0` フラグで分岐。p53 (1TSR) では
dna_arr 非空なので動作は従来通り。

### 2. Tet regime のハードコード境界
`predict_pathogenicity` が p53 特化 `325 <= pos <= 356` を hardcode。
TDP-43 pos 348 が偶然この範囲内で structural regime 扱いされ、IDR
channels 呼ばれず → G348C 不発火。
修正: `v17.TET_RANGE` モジュール変数に抽出し、adapter で
`annotation.domains['tet']` から per-protein 設定。未定義なら None
で tet branch 無効化。

### 3. v18 モジュールの SLIM_DEFS/BENIGN_PRO_POLY/PTM_SITES 二重バインド
v18 `from .p53_gate_v17_idr import SLIM_DEFS, ...` は import 時に
p53 hardcoded を v18 namespace に bind。adapter が v17.SLIM_DEFS を
override しても v18 内は更新されない。gate_ch10_slim_v18 が古い SLIM で
動作し、TDP-43 N390D が p53 CT_reg (363-393) で誤発火。
修正: adapter で v18 内の 3 変数も同時に override/restore。

## アーキテクチャ改善

### TET_RANGE 抽象化
p53 特化の「325-356 = tet domain」ハードコード判定を
`annotation.domains['tet']` から駆動するよう汎用化。他タンパクで
`domains.tet` 未定義なら自動的に tet branch 無効化。

### primary PDB 任意化
TDP-43 のような IDR-only protein では `structures.primary` を省略可能。
adapter は primary_pdb=None の場合 `residue_ctx={}` で初期化し、
IDR/Universal channels のみで動作。

## Supplementary 生成データ

`supplementary/` に配置:
- `transferability_predictions.json` - 23 variants x 12 fields
- `transferability_predictions.csv`  - paper SI 用 flat CSV
- `tier_summary.json`                - tier 別統計

## 論文 Revision への申し送り

### Methods 追加セクション案: "Generalization to other soluble proteins"
本文に以下を記載:
- v18 の 19 gates/getas を UNIVERSAL (9), ADAPTABLE (8), SPECIFIC (4) に
  三層分類 (docs/transferability_matrix.md)
- UNIVERSAL: 配列のみで動作 (TDP-43 で実証、PDB 不要)
- ADAPTABLE: 実験 PDB or AlphaFold pLDDT>70 で動作 (KRAS/BRCA1 で実証)
- SPECIFIC: 標的固有構造必要、Gate C は architecture が転用可能

### Supplementary Table 候補
`supplementary/transferability_predictions.csv` を Table S4 として添付。

### Discussion 追加
- KRAS G12/G13: 既知の機能的 (catalytic GTPase activity) 変異で、
  Ch03 structural gate では発火しない。experimental/ch_catalytic_site
  (Phase 5+) で対応予定。
- TDP-43 A315T, M337V: LLPS/aggregation 変異で、Ch10 A2 は
  sh3_polyproline-scoped。experimental/ch_llps (Phase 5+) で対応予定。
- BRCA1 BRCT phospho-pocket (S1655F, R1699Q/W): Gate C architecture
  transfer の典型例。partner_face.json を ABRAXAS1/BACH1/CtIP complexes で
  再生成すれば既存 Ch10 コードで発火。

## 困った点・疑問点

- v18 の import 時バインド問題 (#3) は設計ミスというより Python 言語の
  動作。Phase 5 で legacy を deprecate する際に `v18.SLIM_DEFS` 等の
  直接参照を `v17.SLIM_DEFS` 経由 (or annotation from ctx) に書き換え
  推奨。

## Phase 4 完了判定 (DoD)

- [x] `pip install -e .[dev]` 成功
- [x] 4 proteins bundled: p53, kras, tdp43, brca1
- [x] Phase 1-3 tests 全 pass 継続 (51)
- [x] Phase 4 transferability tests 全 pass (23) + 5 xfail (期待通り)
- [x] Supplementary data 生成済み (JSON/CSV/summary)
- [x] `docs/transferability_matrix.md` 配置済み
- [x] `docs/phase4_notes.md` 作成済み

**✨ Phase 4 完了。環 に「Phase 4 完了」を報告します。**
論文 Revision に向けた準備完了。
