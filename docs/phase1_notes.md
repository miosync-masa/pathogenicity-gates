# Phase 1 作業メモ

**日付**: 2026-04-23
**担当**: ClaudeCode (メカタマキ)
**結果**: ✅ **全テスト pass (15/15 in 8.52s)**

## 実測メトリクス (v18 再現確認)

| 指標           | 期待値  | 実測値  | 一致 |
|----------------|---------|---------|------|
| N in scope     | 1369    | 1369    | ✅   |
| TP             | 547     | 547     | ✅   |
| FP             | 67      | 67      | ✅   |
| FN             | 100     | 100     | ✅   |
| TN             | 67      | 67      | ✅   |
| Sensitivity    | 84.5%   | 84.5%   | ✅   |
| PPV            | 89.1%   | 89.1%   | ✅   |
| Hotspots       | 9/9     | 9/9     | ✅   |
| Partner face   | 59 res  | 59 res  | ✅   |

## Region別メトリクス (全一致)

| Region           | N   | TP  | FP | FN  | TN |
|------------------|-----|-----|----|----|----|
| Core (94-289)    | 821 | 412 | 20 | 41 | 20 |
| Tet (325-356)    | 106 |  27 | 11 | 13 |  7 |
| TAD1 (1-40)      |  89 |  35 |  7 |  3 |  4 |
| TAD2 (41-61)     |  57 |  16 |  7 |  5 |  2 |
| PRD (62-93)      |  98 |  20 |  6 | 10 | 11 |
| Linker (290-324) |  99 |  13 |  6 | 18 | 16 |
| CTD (357-393)    |  99 |  24 | 10 | 10 |  7 |

## test_exact_identity_with_legacy: **0 mismatches / 1369 variants**

Predictor.from_legacy_v18("p53") の出力が、legacy v17/v18 直接呼び出しと
`n_closed`/`prediction`/`channels` の全フィールドで完全一致。

## 実装中に気づいたこと

1. **`CHARGE_AA` の重複定義**:
   `ssoc_v332.py` に `CHARGE_AA` が2箇所に定義されている:
   - L117: `{'D','E','K','R'}` (4要素、charge gate/rigidity用)
   - L290: `{'D','E','K','R','H'}` (5要素、backbone_strain用、後勝ち)
   Python のスコープ規則により、後者が実効値。`physics/constants.py` には
   **5要素版 (H含む)** を採用。test_physics_constants_match_ssoc で検証済み。

2. **Test 実行時間が予想より速い**:
   Task.md は 90s 目安だが実測 8.52s (~10x 高速)。
   `@pytest.fixture(scope="module")` の予測結果キャッシュが効いており、
   Predictor の setup と 1369 変異予測がテスト間で1回のみ実行される。

3. **v18 の partner_face.json ローダ**:
   元コードは `os.path.dirname(os.path.abspath(__file__))` 基準で探すため、
   legacy/ 内に partner_face.json をコピー配置すると動作するが、
   Task.md 推奨の `_load_partner_face()` (CWD優先 → legacy/ 内 →
   3階層上の候補探索) で実装。テストは autouse fixture `chdir_to_data_root`
   でCWDを data root に固定するため第1候補で解決。

## 作業手順の概要

```
Step 1: pyproject.toml, README.md, .gitignore, __init__.py
Step 2: legacy/ に ssoc_v332, p53_gate_v17_idr, p53_gate_v18_final をコピー
        → v17 の sys.path + import sys 削除、from .ssoc_v332 に修正
        → v18 の sys 削除、相対import化、_load_partner_face() 追加
Step 3: physics/{constants,geometry,corrections}.py
Step 4: structure/{parser,features}.py (dihedral_angle → _dihedral_angle)
Step 5: predictor.py (Predictor.from_legacy_v18)
Step 6: tests/{conftest,test_phase1_v18_regression}.py (9テスト, parametrize で15展開)
Step 7: pip install -e . + pytest → 15 passed in 8.52s
Step 8: このドキュメント
```

## 次 Phase への申し送り

- [ ] **Phase 2 で対応すべき事項**:
  - YAML ローダの実装 (`Predictor.from_yaml("p53.yaml")`)
  - タンパク非依存のゲート定義 (ch1-ch10, GateA-GateC, IDR subchannels)
  - データ/コード分離: PPI union・partner face・PTM sites・SLIM defs を YAML に
  - `Predictor.predict_batch([(pos, wt, mt), ...])` API
  - 新タンパク (例: KRAS, BRCA1) に対する YAML 定義の検証

- [ ] **実運用での拡張候補**:
  - `extract_partner_face.py` を再実装 (現在は `pathogenicity-gates-main/` 直下)
  - Gate C の自動拡張: PDB 取得 → interface 検出 → YAML 生成パイプライン

- [ ] **注意**: v17/v18 legacy 側には Phase 1 で修正しなかったロジック
  (`setup_core_domain` 内の 1TSR.pdb chain='B' 既定値等) が残っている。
  Phase 2 の汎用化時には、これらを YAML で指定できる形に抽象化。

## 困った点・疑問点

特になし。Task.md が非常に詳細かつ正確で、探索フェーズで確認した実コードと
完全に整合していた。実装中の判断迷いは発生しなかった。

## Phase 1 完了判定 (DoD チェック)

- [x] `pip install -e .` 成功
- [x] `pytest tests/` で 15 テスト全 pass
- [x] `test_exact_identity_with_legacy` で **0 mismatches**
- [x] `test_confusion_matrix_exact` で TP=547, FP=67, FN=100, TN=67
- [x] `test_all_hotspots_caught` で 9/9 全員 Pathogenic
- [x] `test_partner_face_size` で 59 residues
- [x] ディレクトリ構造が仕様通り
- [x] `phase1_notes.md` 作成済み

**✨ Phase 1 完了。環 に「Phase 1 完了」を報告します。**
