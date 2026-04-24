# Phase 2 作業メモ

**日付**: 2026-04-23
**担当**: ClaudeCode (メカタマキ)
**結果**: ✅ **全テスト pass (Phase1: 15/15, Phase2: 9/9, 計 24/24 in 18.24s)**

## テスト結果

### Phase 1 継続動作確認 (15/15 pass)
| テスト                              | 結果 |
|------------------------------------|------|
| test_variant_count                 | ✅   |
| test_confusion_matrix_exact        | ✅   |
| test_all_hotspots_caught           | ✅   |
| test_region_exact_metrics (×7)     | ✅   |
| test_exact_identity_with_legacy    | ✅   |
| test_partner_face_size             | ✅   |
| test_physics_constants_match_ssoc  | ✅   |
| test_physics_functions_match_ssoc  | ✅   |
| test_public_api_smoke              | ✅   |

### Phase 2 新規テスト (9/9 pass)
| テスト                                 | 結果 |
|---------------------------------------|------|
| test_list_bundled_proteins            | ✅   |
| test_from_protein_smoke               | ✅   |
| test_from_yaml_smoke                  | ✅   |
| test_hotspots_via_yaml                | ✅   |
| test_yaml_identity_with_legacy        | ✅   (0 mismatches / 1369 variants) |
| test_yaml_confusion_matrix            | ✅   (TP=547, FP=67, FN=100, TN=67) |
| test_annotation_loader                | ✅   |
| test_wt_extraction_from_sequence      | ✅   |
| test_ptm_consistency_report_generated | ✅   |

## PTM Consistency Report 概要

| 指標                   | 件数 |
|-----------------------|------|
| Matches               | 30   |
| AA mismatches         |  0   |
| Type mismatches       |  1   |
| Only in annotation    |  0   |
| Only in UniProt       |  0   |

**Type mismatch 1件**: Position 333 — v17 baseline は `methyl`、UniProt REST は
`Omega-N-methylarginine; by PRMT5` (= dimethyl 扱い)。
Phase 4 で v17 baseline を UniProt 定義に合わせるか審議対象。今 Phase では
**v18 再現性優先で v17 baseline 維持**。

## 作成データの棚卸し

### PDB (data/p53/pdb/ — 合計 ~6.7MB)
- [x] 1TSR.pdb — 526 KB (p53 core + DNA, chain B)
- [x] 1YCR.pdb —  94 KB (p53-MDM2, chain B=p53 A=MDM2)
- [x] **2J0Z.pdb — 5.1 MB (30 NMR models all kept)**
  - ⚠️ Task.md では MODEL 1 抽出指示 (170KB 目安) だったが、v17 の
    `setup_tetramer()` は MODEL 処理を実装しておらず**全モデル ATOM を読む**
    実装。Phase 1 の legacy は CWD から 30モデル版を読んで動作している。
    Phase 2 で MODEL 1 版にすると Ch8_Tet の挙動が legacy と食い違うため、
    **再現性優先で 30モデル版を保持**。この判断は Phase 3 で `setup_tetramer`
    を refactor する際に見直し予定 (phase3 申し送り)。
- [x] 5HPD.pdb — 226 KB (CBP TAZ2, MODEL 1)
- [x] 5HOU.pdb — 241 KB (CBP TAZ1, MODEL 1)
- [x] 2L14.pdb — 159 KB (CBP NCBD, MODEL 1)
- [x] 2K8F.pdb — 184 KB (p300 TAZ2 TAD1, MODEL 1)
- [x] 2MZD.pdb — 185 KB (p300 TAZ2 TAD2, MODEL 1)

### JSON (data/p53/)
- [x] p53_ppi_union.json (PPI 16 構造 union)
- [x] p53_ppi_interface.json (詳細版、Phase 4 用)
- [x] p53_uniprot_features.json (UniProt REST v3.32 時点のダンプ)
- [x] partner_face.json (Gate C 6-partner union = 59 residues)
- [x] tp53_clinvar_missense.json (ClinVar 1374 variants)
- [x] **p53_sequence.json** — NEW: UniProt P04637 canonical (393 aa)

### Generated
- [x] annotation.yaml (v17 baseline と完全一致)
- [x] ptm_consistency_report.md (Matches 30/31, Type mismatch 1)

## 実装中に気づいたこと

### 1. Task.md 想定と実装の不整合 (2J0Z MODEL 抽出)
Task.md Step 1-1 は 2J0Z を MODEL 1 抽出して縮小 (~170KB) を指示するが、
`setup_tetramer` の実装 (legacy v17 L357-420) は MODEL 判定なしで全 ATOM を
素朴に読んで chain A/B/C/D に分類する。このため:

- 元の 2J0Z (30 モデル): chain A に 522 × 30 = 15,660 atoms
- MODEL 1 のみ版:        chain A に 522 atoms

→ interface 距離計算、exposure 計算、chain_contacts 全てが変わる。
legacy が後者を使うよう変更するのは**ロジック変更**に当たるため Phase 2 では
禁止 (v18 再現性が壊れる)。**30 モデル版を保持する選択**を採った。

**Phase 3 への申し送り**: `setup_tetramer` を refactor して MODEL 1 のみを
使うように変更する際は、v18 再現メトリクスが変わるためテストベースライン
(TP=547 等) も更新する必要がある (= Phase 1/2 ベースラインと Phase 3 ベース
ラインで異なる数値になる)。

### 2. SLIM critical_* 位置は UniProt canonical sequence から WT 取得
1TSR (94-289) のみで SLIM の critical 位置 (53, 54, 305, 306, 370, 372, 373,
379) は PDB カバー範囲外。Task.md の `_reconstruct_slim_defs` は PDB 抽出
前提だったが、本実装では **UniProt canonical sequence (p53_sequence.json)
から wt_at() で取得**。v17 hardcoded と完全一致を確認 (test_wt_extraction_from_sequence)。

### 3. Monkey-patch override は二重呼び出しに注意
`from_legacy_v18()` は最初に `restore_legacy_constants()` を呼んで pristine
状態に戻す。これで `from_yaml()` → `from_legacy_v18()` の順で呼んでも前者の
override が残らない。`_ORIGINAL_LEGACY_CONSTANTS` はプロセス初回の
`override_legacy_constants_from_annotation()` で一度だけスナップショット。

### 4. Python 3.10 での tuple 比較
`ann.domains['core'] == (94, 289)` は YAML `[94, 289]` list → loader で
tuple 変換しているのでOK。slim_defs['range'] も同様 tuple 化 (v17 は tuple
を期待)。

## Phase 3 以降への申し送り

### Phase 3 で対応すべき
- [ ] **`setup_tetramer` の MODEL 1 処理化** (data 軽量化の正道)
- [ ] Channel 分離 (ch01_ligand.py, ..., ch10_slim.py)
- [ ] experimental/ ディレクトリ導入 (LLPS, aggregation 等)
- [ ] Channel registry の動的登録

### Phase 4 で検討
- [ ] PTM position 333: v17 `methyl` vs UniProt `dimethyl` の解決
- [ ] p53_ppi_interface.json を Ch6_PPI sub-gate に統合
- [ ] KRAS/TDP-43/BRCA1 annotation.yaml 作成
- [ ] `COUPLED_FOLDING_MDM2` の PDB 自動抽出検証 (現在は fallback 経由)

### 未解決事項 (Phase 1 から継続)
- [ ] CHARGE_AA の重複定義問題 (ssoc_v332 L117 vs L290) — 真道さま確認待ち

## 困った点・疑問点

1. **2J0Z MODEL 処理**: Task.md と実装の不整合により判断を要した。
   **採った選択: 30モデル版保持 (再現性優先)**。Phase 3 で refactor 時に再考。

2. **PTM 333 の methyl/dimethyl 揺らぎ**: UniProt は Omega-N-methylarginine
   (= mono-methyl) と記述しているが、parse_uniprot_description は
   `'dimethyl' in d or 'omega-n' in d` の OR 条件で dimethyl 扱いしている。
   parser の規則を調整すべきか Phase 4 で検討。現状は v17 baseline 維持で影響なし。

## Phase 2 完了判定 (DoD チェック)

- [x] `pip install -e .[dev]` が成功
- [x] `pytest tests/` で全 24 テスト pass
- [x] `test_yaml_identity_with_legacy` で **0 mismatches**
- [x] `test_yaml_confusion_matrix` で TP=547, FP=67, FN=100, TN=67
- [x] `data/p53/` に全データ配置完了 (8 PDB + 6 JSON + 1 YAML + 1 MD)
- [x] `scripts/` に 3 スクリプト配置完了
  - build_uniprot_features.py
  - extract_partner_face.py
  - verify_ptm_consistency.py
- [x] `ptm_consistency_report.md` 生成済み
- [x] `phase2_notes.md` 作成済み

**✨ Phase 2 完了。環 に「Phase 2 完了」を報告します。**
