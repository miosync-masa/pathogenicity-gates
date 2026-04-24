# Phase 5 作業メモ

**日付**: 2026-04-24
**担当**: ClaudeCode (メカタマキ)
**結果**: ✅ **98 passed + 5 xfailed (87.5 秒)**

## テスト結果

### Phase 1-4 継続 (74 pass + 5 xfail)
- Phase 1: 15/15
- Phase 2:  9/9
- Phase 3: 27/27
- Phase 4: 23 pass + 5 xfail (期待通り)

### Phase 5 新規 CLI テスト (24/24 pass)
- Basic invocation: 3/3 (`--version`, `--help`, no-subcommand)
- list-proteins:    3/3 (table/json/compact)
- predict:          9/9 (compact/json/table/split-format/kras/tdp43/invalid/nonexistent/missing-arg)
- predict-batch:    4/4 (csv/json/stdin/csv-output)
- explain:          4/4 (default/idr/channels-only/verbose)
- API parity:       1/1 (CLI output == direct Predictor call)

## 実装した CLI サブコマンド

| Command | Purpose | 主要 flags |
|---------|---------|-----------|
| `predict`        | 単一変異予測 | `--protein` / `--annotation` / `--mutation` / `--format` / `--mode` |
| `predict-batch`  | 複数変異バッチ (CSV/JSON/TSV/stdin) | `--input` / `--output` / `--format` |
| `explain`        | 詳細診断 (channel states + residue context) | `--verbose` / `--channels-only` |
| `list-proteins`  | 同梱タンパク一覧 | `--format` |

## 実装した出力フォーマット

- `json`    - 機械可読 (pipeline-friendly)
- `table`   - ASCII box drawing (人間可読)
- `compact` - 1行要約
- `csv`     - predict-batch 専用 (flat row)

## pip install 後の動作確認

```
$ pip install -e .
Successfully installed pathogenicity-gates-0.5.0.dev0

$ which pathogenicity-gates
/Users/iizumimamichi/.pyenv/shims/pathogenicity-gates

$ pathogenicity-gates --version
pathogenicity-gates 0.5.0-dev

$ pathogenicity-gates list-proteins
Bundled proteins in pathogenicity-gates:
  brca1    P38398
           Breast cancer type 1 susceptibility protein (tumor suppressor)
  kras     P01116
           GTPase KRas (proto-oncogene)
  p53      P04637
           Cellular tumor antigen p53 (tumor suppressor)
  tdp43    Q13148
           TAR DNA-binding protein 43 (ALS/FTLD associated)

$ pathogenicity-gates predict --protein p53 --mutation R175H
* R175H  (p53)  Pathogenic   n_closed=3

$ pathogenicity-gates predict --protein tdp43 --mutation G348C --format json
{
  "prediction": "Pathogenic",
  "n_closed": 1,
  "channels": { "Ch07_PTM": "O", "Ch10_SLiM": "O",
                "Ch11_IDR_Pro": "O", "Ch12_IDR_Gly": "C" },
  "regime": "idr", ...
}
```

すべて正常動作。

## 依存性: ゼロ追加

Python 標準ライブラリのみ使用:
- `argparse` (CLI parser)
- `json`, `csv`, `io`, `tempfile` (data I/O)
- `re`, `os`, `sys`, `subprocess` (utility)

pyproject.toml の dependencies に追加なし。

## 実装中に気づいたこと

### 1. ProteinAnnotation に description フィールドが未存在
Phase 2 の loader では `protein.description` を読んでいなかったため、
CLI の `list-proteins` で description が欠落。追加 (default None で後方互換):

```python
# loader.py
description: Optional[str] = None  # dataclass の default 有り field は後置
```

YAML 側の `protein.description` は Phase 2 時点で書かれているので
値はそのまま拾える。

### 2. dataclass の field 順序制約
`description: Optional[str] = None` は default 有り field なので、
default なし field の前に置くと `non-default argument follows default argument` エラー。
`benign_pro_poly` の default 有り field の後に配置して解決。

### 3. CLI test 時間
subprocess 起動 + Predictor setup が 1 テストあたり 2-3 秒 × 24 テスト =
約 60 秒 追加。Phase 4 までの 36 秒から 87 秒へ増加。許容範囲。

## 論文 Revision への申し送り

### Methods セクション追記案
> The package is available via `pip install pathogenicity-gates` (PyPI) and
> provides a command-line interface (`pathogenicity-gates`) with four
> subcommands (`predict`, `predict-batch`, `explain`, `list-proteins`).
> A non-expert user can evaluate any variant with a single command, e.g.
> `pathogenicity-gates predict --protein p53 --mutation R175H`. This
> directly addresses Reviewer #1's concern about framework accessibility.

### Data Availability / Code Availability
- GitHub: (Phase 6 で作成)
- PyPI: `pathogenicity-gates` (Phase 6 で公開)
- Zenodo DOI: (Phase 6 で取得)
- CLI docs: `docs/cli_usage.md`

## 次ステップ (Phase 6: PyPI 公開) への申し送り

- [ ] GitHub repo セットアップ (本番用 README)
- [ ] GitHub Actions CI (pytest on push)
- [ ] Zenodo DOI 取得
- [ ] PyPI パッケージ公開 (`twine upload`)
- [ ] 論文本文に CLI 紹介追加

## Phase 5 完了判定 (DoD)

- [x] `pip install -e .` で `pathogenicity-gates` コマンドが PATH に入る
- [x] `pathogenicity-gates --version` が `0.5.0-dev` 表示
- [x] 4 サブコマンド (predict, predict-batch, explain, list-proteins) 全動作
- [x] 3 出力フォーマット (json/table/compact) + csv 全動作
- [x] Phase 1-4 の 79 テスト継続 pass (74 + 5 xfail)
- [x] Phase 5 新規 24 CLI テスト全 pass
- [x] `docs/cli_usage.md` 作成
- [x] `README.md` に CLI セクション追加
- [x] `phase5_notes.md` 作成

**✨ Phase 5 完了。環 に「Phase 5 完了」を報告します。**
研究者が `pip install pathogenicity-gates` 一発で使える状態が完成。
Reviewer #1 の使用容易性指摘への最終的な回答を実装レベルで達成。

---

## Addendum (2026-04-24): Post-Phase 5 legacy-leak fix (v0.5.1-dev)

**Issue**: 環 レビュー指摘 — `pathogenicity-gates predict --protein kras --mutation G12V`
が clean env (legacy/partner_face.json 未配置) で `FileNotFoundError: partner_face.json
not found` で落ちる。依存追跡で原因判明: Phase 2 の `build_context_from_annotation`
が `legacy.p53_gate_v18_final` を強制 import し、module-level で
`_pf = _load_partner_face()` が実行されるため、p53 以外の protein でも p53 用
JSON を要求していた。

**修正 (A案 + C案)**:

### C案: legacy の partner_face を lazy-load 化
- `legacy/p53_gate_v18_final.py`: module-level `_pf = _load_partner_face()` を削除し、
  `_ensure_partner_face_loaded()` 関数経由の lazy 読み込みに変更。
- adapter が `v18.COUPLED_FOLDING_PARTNER_FACE` を明示的にセット済みなら skip
  (per-protein override 保護)。
- `_load_partner_face()` の候補 path に `data/p53/partner_face.json` を追加
  (legacy が bundled data で自己完結)。
- adapter の `_backup_originals_once` で snapshot 前に populate するよう修正。

### A案: `adapters/direct_builder.py` 新設 (legacy-free context builder)
- v17 の `setup_core_domain` / `setup_tetramer` / `setup_ppi` / `setup_salt_bridge`
  を**ロジック逐語コピー**で移植。
- import は `physics/`, `structure/` のみ。`legacy/` を一切触らない。
- 返り値は `PredictionContext` オブジェクトを直接構築。
- p53 で legacy path と byte-for-byte 一致確認 (residue_ctx 194 / ppi 66 /
  tet_interface 29 / sb_partners 18 全一致)。

### `Predictor` に `legacy_impl` フラグ追加
- `Predictor.from_yaml(yaml_path, legacy_impl=True)` — default True (Phase 2 test 互換)。
- `legacy_impl=False` で direct_builder 経由、`_impl=None, _context=None, _ctx_obj=<direct>`。
- `Predictor.from_protein(protein, legacy_impl=True)` も同フラグ。
- `predict(mode='legacy')` で `_impl is None` のとき明確な例外。

### CLI 改修
- `predict` / `predict-batch`: `args.mode == 'legacy'` のみ `legacy_impl=True`。
  default は `channels` なので `legacy_impl=False`。
- `explain`: 常に `legacy_impl=False` (channels mode 専用)。

### 新規テスト: `tests/test_no_legacy_leak.py` (13 tests)
- `test_channels_mode_no_legacy_import`: KRAS の channels mode で
  `sys.modules` に `pathogenicity_gates.legacy.*` が一切含まれないこと
- `test_channels_mode_p53_no_legacy_import`: p53 でも同じ保証
- `test_p53_channels_mode_identical_legacy_impl_flag` (7 params):
  channels mode で `legacy_impl=True/False` が byte-for-byte 一致
- `test_clean_env_non_p53_predicts` (3 proteins x fixture): clean env
  (partner_face.json 退避後) で kras/tdp43/brca1 が予測成功
- `test_clean_env_p53_via_bundled_data`: 同状態でも p53 は `data/p53/`
  の bundled data 経由で動作

### テスト結果
- Phase 1-5 継続: 98 passed + 5 xfailed (変更なし)
- Phase 5 addendum: 13 passed (新規)
- **合計: 111 passed + 5 xfailed (141.5 秒)**

### Clean-env CLI 動作確認
`legacy/partner_face.json` と `partner_face.json` (CWD) 両方不在状態で:
```
kras K117N: * K117N  (kras)  Pathogenic   n_closed=1
tdp43 G348C: * G348C  (tdp43)  Pathogenic   n_closed=1
brca1 V1696L: * V1696L (brca1) Pathogenic   n_closed=2
p53 R175H: * R175H  (p53)  Pathogenic   n_closed=3
```
すべて成功。

### Phase 6 公開への布石
- `legacy/` ディレクトリは `from_legacy_v18()` / `mode='legacy'` でしか使われず、
  channels mode (CLI default) は完全に独立。
- 将来的に `legacy/` を optional 配布に降格可能 (p53 byte-for-byte
  regression 用の検証データのみ同梱、通常 CLI 利用では不要)。
- 真のフレームワーク独立性が確立: p53 は「最初に実装された protein」に過ぎず、
  構造的特権なし。
