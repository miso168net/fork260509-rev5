# Implementation Plan: 波 0 schema 基線（rev4 終態壓平＋定稿制）

**Branch**: `001-schema-baseline` | **Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-schema-baseline/spec.md`

## Summary

rev5 資料庫基線＝rev4 終態 15 表壓平為 m001（結構）＋m002（seed 定稿、完全決定性）；
同刀重建三閘（結構全等／欄序＋seed／audit archetype）為 Day-1 受管演進帳契約、落 entity
對應層與漂移防線、完成 refresh 首跑與參考真表 DoD 鏈。定稿權威已凍結：欄序＝
data-model.md §2（169 欄機器轉錄）、seed＝seed-decision.json（clarify 簽核）。

## Technical Context

**Language/Version**: Rust 1.96.1（`deploy/Dockerfile.rust-api` 既定 `rust:1.96.1-slim`
dev stage；rust-toolchain.toml 同值）＋ Python 3（repo 治理工具、標準庫單檔紀律）

**Primary Dependencies**: sea-orm-migration 1.1.20（sqlx-postgres／runtime-tokio-rustls／
cli）、sea-orm 1.1.20（entity：macros／with-chrono／with-json／with-ipnetwork）、
casbin 2.20.0＋async-trait 0.1.89（vendored sea-orm-adapter）、tokio 1.52.3——整組承
rev4 已驗證 pins（research R1；不引 argon2——Q1 拍板 PHC 常數、無 runtime 雜湊）

**Storage**: PostgreSQL 18.4（`postgres:18.4-alpine`、compose 既定；dev DB＝
`soybean_admin_rust`／user `soybean`）

**Testing**: cargo test（容器內、全程 serial）＋python 工具自帶 test 子命令＋三閘
self-test／negative 注入（SC-002）＋pristine 重放逐列 diff（SC-001）

**Target Platform**: Linux 容器（compose stack；dev 機 aarch64）

**Project Type**: DB migration／entity crates（rust-api workspace 首批工件）＋repo 治理
工具重建（單 repo 多工件）

**Performance Goals**: pre-commit 全鏈 ≤20s 警戒／45s 硬擋（既有門檻、新閘不得破線）；
三閘單跑秒級；migration 容器首建 ~數分鐘（冷 registry）

**Constraints**: host 無 rust toolchain（一切 build/test 容器內、serial）；rev4 repo 唯讀
（素材已於 clarify 產製完畢）；fixtures 凍結後永不改寫；secrets 掃描防線在跑（PHC 字面
若誤報→ADR 0003 白名單處置）；pristine 驗證容器零 host 埠

**Scale/Scope**: 15 表 169 欄、索引 38／約束 101、seed 266 列（casbin 163）、
migration 兩支、閘三道、entity 檔 15 支

## Constitution Check

*GATE: 對照 constitution v1.0.0 §IV 九題（初檢＝Phase 0 前；複檢＝Phase 1 設計後）。*

| # | 題 | 判定 | 依據 |
|---|---|---|---|
| 1 | 違反 §I.1 base-web 權威？ | **否** | 本刀零 endpoint 面（server 不入刀）；schema 忠實壓平、無設計範圍縮減；wire-schema 維持 fail-open 警告態（spec Out of Scope 載明） |
| 2 | 動 base-web inline？ | **否** | base-web 全程不動；本刀全在 rust-api worktree＋外層 docs/tools |
| 3 | menu 顯示走 Casbin enforce？ | **是（seed 面）** | 本刀無 route 過濾邏輯；seed 落 demo menu 全集入 sys_menu＋casbin menu 政策（§I.2 機制前提）；toggle-auth 示範鏈三角色初始勾選（4 列）與 hide_in_menu 原樣值（6 列）＝§I.2 例外與釋義條款（ADR 0005、Amendment v1.1.0） |
| 4 | wire 對齊 §I.3？ | **是（射程內）** | 本刀無 wire；凡帶自增主鍵之 11 表 id 皆 bigint（i64 自增）＝§I.3 DB 側不變式（餘 4 表自然鍵／複合鍵、無 id 欄）、data-model §2 機器斷言在案 |
| 5 | 拷貝前代 code？ | **例外內** | sea-orm-adapter 整檔拷貝＝§I.5 例外清單；migration／entity 全新打字（參照不拷貝）；防回歸條款落 data-model §10（operator_ 前綴／varchar(64)／簡體值／runtime 雜湊不得帶回） |
| 6 | 抵觸 §II 拍板？ | **否** | #1 unknown header／#2 auth route mode／#3 路徑前綴皆不涉 |
| 7 | 觸及 §III ★ 軌道？ | **否** | 不動 base-web；★ 軌道零觸及 |
| 8 | 新建業務表含 §I.6 六審計欄？ | **是** | 15 表逐表 archetype 歸屬＝data-model §1（A×5 六欄全、B×4 禁 updated_*/deleted_*、C×4、D×2）；建表即帶終態欄、零 retrofit；audit 閘機器守門 |
| 9 | 觸及 §I.7 行為島？ | **否** | v1.0.0 尚無已入憲島；本刀純 schema 落地、零行為邏輯；行為島（token rotation 等）隨對應域刀進場入憲，其表結構先行落地不構成「該入憲而未入憲」 |

**初檢結論**：九題全過、零違規。
**Phase 1 複檢（設計後）**：data-model／contracts 產出後重走九題——判定不變（設計無新增
違規面；第 8 題由 audit 閘契約機器化、第 3 題 seed 面由 clarify 簽核紀錄承載）。**通過**。

## Project Structure

### Documentation (this feature)

```text
specs/001-schema-baseline/
├── spec.md / plan.md / research.md / data-model.md / quickstart.md
├── checklists/requirements.md
├── seed-review.md               # clarify 工作坊素材＋定稿紀錄（簽核在案）
├── seed-net-effect.json         # rev4 淨效果素材（血緣）
├── seed-decision.json           # seed 定稿機器檔（m002 唯一來源）
├── contracts/
│   ├── gates.md                 # 三閘行為契約
│   ├── schema-evolution.md      # 演進登記檔契約
│   └── fixtures.md              # 凍結面契約
├── fixtures/                    # 【實作階段產】columns/indexes/constraints.json＋seed.sql＋provenance.md
└── tasks.md                     # /speckit-tasks 產（非本命令）
```

### Source Code (repository root)

```text
rust-api/                        # worktree（現況空殼）——首批程式工件
├── Cargo.toml                   # workspace: members = [migration, entity, sea-orm-adapter]
├── Cargo.lock
├── rust-toolchain.toml          # 1.96.1
├── migration/                   # m001_baseline_schema＋m002_baseline_seeds＋main/lib
├── entity/                      # 15 entity 檔＋lib.rs（rename 後定稿欄名）
└── sea-orm-adapter/             # vendored（§I.5 例外、整檔拷貝、除檔頭 provenance 行外零改寫）

tools/
└── schema-gate.py               # 整組重建（rev5 座標＋演進帳契約；白名單模型移除）

docs/ops/reference-src/
├── archetype-map.json           # 初版（data-model §1 轉錄）
├── schema-evolution.json        # 初版（空 entries）
├── schema-snapshot.json         # refresh 首跑產
└── accounts-snapshot.json       # refresh 首跑產

docs/arc42/decisions/            # 0006（基線＝壓平＋定稿制）、0007（閘契約＝演進帳）；0005＝§I.2 Amendment（已落）
docs/arc42/ARCHITECTURE.md       # 資料慣例節＋memo 家族一行（活書隨刀）
docs/ops/RUNBOOK.md              # migration 操作節＋Day-1 登記紀律
tools/docs-sync.py               # DAY1_EXEMPTIONS 拔 gen.snapshots（謂詞成立後）
```

**Structure Decision**: rust-api＝Cargo workspace 首建、members 僅本刀三 crate（server／
xdb 隨後續刀加入）；兩段式 commit 紀律（worktree 內 commit → 外層即時 bump pin）；
repo 治理工件（閘／登記檔／快照／ADR／活書）全在外層。實作順序與相依由 /speckit-tasks
展開；預期執行單元切分＝①workspace＋migration（m001/m002）＋pristine 驗證
②schema-gate 重建＋演進帳＋fixtures 凍結 ③entity crate＋drift 恢復實跑
④DoD 鏈（refresh／archetype-map／拔項／generate）＋ADR×2＋活書／RUNBOOK。

## Complexity Tracking

Constitution Check 九題全過、零違規——本節免填。
