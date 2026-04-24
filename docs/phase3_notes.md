# Phase 3 作業メモ

**日付**: 2026-04-23
**担当**: ClaudeCode (メカタマキ)
**結果**: ✅ **51/51 テスト全 pass (22.02 秒)**
  - Phase 1 継続: 15/15
  - Phase 2 継続:  9/9
  - Phase 3 新規: 27/27
    - Phase 3 integration: 8/8 (0 mismatches / 1369 variants)
    - Channel registry:    6/6
    - Channel smoke:      13/13

## Channel 分離の完了状況

### Structural レジーム (8 Channels, 3D-coordinate-based)
- ✅ Ch01_DNA         — DNA contact disruption
- ✅ Ch02_Zn          — Zn coordination (Layered Cascade Model)
- ✅ Ch03_Core        — Core integrity (V<->I v18 patch 埋込み)
- ✅ Ch04_SS          — Secondary structure disruption
- ✅ Ch05_Loop        — Loop Ramachandran constraints
- ✅ Ch06_PPI         — Protein-protein interface
- ✅ Ch08_Oligomer    — Tetramer/oligomer interface
- ✅ Ch09_SaltBridge  — Surface salt bridge network

### IDR レジーム (3 Channels, 1D-sequence-based)
- ✅ Ch10_SLiM        — SLiM motif (v18 multi-partner Gate C 埋込み)
- ✅ Ch11_IDR_Pro     — IDR Pro constraint (旧 Ch5_IDR_Pro)
- ✅ Ch12_IDR_Gly     — IDR Gly backbone freedom (旧 GateB_IDR_Gly)

### Universal レジーム (1 Channel)
- ✅ Ch07_PTM         — PTM site disruption (v18 IDR conservative Geta 埋込み)

## 物理レジーム判定

`PredictionContext.get_physics_regime(pos)` の判定ロジック:
1. `pos in residue_ctx`             → `'structural'` (Core domain)
2. `pos in annotation.domains['tet']` → `'structural'` (tet domain)
3. `pos in annotation.idr_ranges`    → `'idr'`
4. それ以外                         → `'unknown'`

Universal Channel (Ch07_PTM) は structural/idr 両方で発火し、
`ctx.is_idr_position(pos)` で proximity threshold と conservative Geta を調整。

## legacy mode と channels mode の対応確認

`test_n_closed_identity_legacy_vs_channels` で全 1369 variants を両 mode で
実行、n_closed/prediction が完全一致することを検証:

```
LEGACY_TO_P3_CHANNEL_MAP:
  'Ch1_DNA'        → 'Ch01_DNA'
  'Ch2_Zn'         → 'Ch02_Zn'
  'Ch3_Core'       → 'Ch03_Core'
  'Ch4_SS'         → 'Ch04_SS'
  'Ch5_Loop'       → 'Ch05_Loop'
  'Ch6_PPI'        → 'Ch06_PPI'
  'Ch7_PTM'        → 'Ch07_PTM'
  'Ch8_Tet'        → 'Ch08_Oligomer'
  'Ch9_SaltBridge' → 'Ch09_SaltBridge'
  'Ch10_SLiM'      → 'Ch10_SLiM'
  'Ch5_IDR_Pro'    → 'Ch11_IDR_Pro'
  'GateB_IDR_Gly'  → 'Ch12_IDR_Gly'
```

`test_per_channel_identity`: **0 mismatches / 1369 variants**

## 実装中に気づいたこと

### 1. Ch10_SLiM の critical_* アクセス形式差異
v17 SLIM_DEFS は `critical_charged: {305: 'K', 306: 'R'}` (dict with WT aa)。
YAML loader は `critical_charged_positions: [305, 306]` (position list only)。

初期実装では dict 形式のみ check していたため NLS1 位置 (306_R_Q, 306_R_G) で
mismatch が発生。修正として**両形式をサポート**:

```python
ccpos = sdef.get('critical_charged_positions')
if ccpos is None and 'critical_charged' in sdef:
    ccpos = list(sdef['critical_charged'].keys())
if ccpos and pos in ccpos:
    expected = ann.wt_at(pos)  # sequence から取得
    ...
```

WT は `annotation.wt_at(pos)` (UniProt canonical sequence) で取得する。

### 2. V18 patches を Channel ファイルに直接埋込み
Phase 1/2 は legacy の monkey-patch (`v17.gate_ch10_slim = gate_ch10_slim_v18`)
に依存。Phase 3 channel mode では、v18 のロジックを**各 channel ファイルに
直接**コード化:
- **Ch03_Core**: 冒頭で V↔I swap exempt → return 'O'
- **Ch07_PTM**: proximity ループ内で IDR ±1 + conservative pair 時に continue
- **Ch10_SLiM**: COUPLED_FOLDING_PARTNER_FACE (59 res) + is_conservative_substitution

これで Ch10/Ch03/Ch07 は「単一モジュールで v18 完結」。monkey-patch 不要。

### 3. Ch02_Zn と Ch05_Loop の p53 特化定数
- Ch02_Zn: `_P53_ZN_LIGANDS = {176, 238, 242, 179}` ハードコード
- Ch05_Loop: `LOOP_L2_L3 = set(range(163, 176)) | set(range(237, 251))`
            `LOOP_ANCHORS = {245, 249, 163, 236, 164, 248, 175, 242, 176}`

Phase 4 で YAML 化検討 (`annotation.zn_ligand_positions`, `annotation.loop_ranges`)。
Phase 3 ではハードコード維持で v18 再現性を保証。

### 4. registry 重複検知のテスト設計
`test_register_duplicate_id` は実際に `@register_channel(id="Ch01_DNA", ...)` を
発動させて ValueError を捕捉。pytest が別の test 実行時にも副作用が残らないよう
decorator 内で例外 throw 前に state 変更しないように実装。

## Phase 4 以降への申し送り

### Phase 4 で対応すべき
- [ ] **KRAS/TDP-43/BRCA1 の annotation.yaml 作成**
  - UniProt ID: KRAS=P01116, TDP-43=Q13148, BRCA1=P38398
  - PDB 自動取得 + YAML スキャフォールド
- [ ] **experimental/ に新 Channel 追加**:
  - `ch_llps.py` — Liquid-Liquid Phase Separation (TDP-43 LCD)
  - `ch_membrane.py` — CaaX-box / myristoylation (KRAS)
  - `ch_nucleotide_binding.py` — GTP/GDP P-loop (KRAS)
- [ ] **Ch02_Zn / Ch05_Loop の p53 特化定数 → YAML 化**
  - Ch02_Zn の _P53_ZN_LIGANDS → annotation.metal_ligand_positions
  - Ch05_Loop の LOOP_L2_L3 / LOOP_ANCHORS → annotation.loop_* 
  - Phase 3 の v18 再現性を維持しつつ、他蛋白質でも動作するよう抽象化

### Phase 5 で検討
- [ ] channel mode をデフォルトに切り替える (legacy mode は deprecated)
- [ ] PTM position 333 の methyl/dimethyl 解決 (Phase 2 notes 継承)

### 未解決事項 (Phase 1-2 継続)
- [ ] CHARGE_AA の重複定義問題 (ssoc_v332 L117 vs L290) — 真道さま確認待ち
- [ ] 2J0Z 30-model 保持 — Phase 3 で `setup_tetramer` を MODEL 1 処理化する
      選択肢もあったが、v18 再現性優先で先送り (Phase 2 notes 継承)

## ディレクトリ構造

```
pathogenicity_gates/channels/
├── __init__.py              # auto-registration trigger
├── context.py               # PredictionContext (regime 判定)
├── registry.py              # @register_channel + get_applicable_channels
├── structural/  (8 channels)
│   ├── ch01_dna.py
│   ├── ch02_zn.py
│   ├── ch03_core.py         (V<->I v18 patch)
│   ├── ch04_ss.py
│   ├── ch05_loop.py
│   ├── ch06_ppi.py
│   ├── ch08_oligomer.py
│   └── ch09_salt_bridge.py
├── idr/  (3 channels)
│   ├── ch10_slim.py         (v18 multi-partner Gate C)
│   ├── ch11_idr_pro.py
│   └── ch12_idr_gly.py
├── universal/  (1 channel)
│   └── ch07_ptm.py          (v18 IDR conservative Geta)
└── experimental/  (empty, Phase 4+ 用)
    └── README.md
```

## Phase 3 完了判定 (DoD)

- [x] `pip install -e .[dev]` 成功
- [x] `pytest tests/` で 51 テスト全 pass
- [x] `test_n_closed_identity_legacy_vs_channels` で **0 mismatches**
- [x] `test_per_channel_identity` で **0 mismatches**
- [x] 12 Channel 全て registry に登録 (structural=8, idr=3, universal=1)
- [x] `experimental/` ディレクトリ + README 作成
- [x] `phase3_notes.md` 作成済み

**✨ Phase 3 完了。環 に「Phase 3 完了」を報告します。**
