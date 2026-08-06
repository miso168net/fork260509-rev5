# research — 001-schema-baseline（Phase 0）

> Technical Context 零 NEEDS CLARIFICATION（座標幾乎全由既有 repo 工件定死）；本檔記
> 施工級拍板（工程判斷、回報備查）與其依據。全部 Decision 均已接地實查（來源檔逐一開過）。

## R1 版本策略＝整組沿用 rev4 已驗證組合

- **Decision**: rust toolchain `1.96.1`（rust-toolchain.toml 同值）；workspace pins：
  `sea-orm` / `sea-orm-migration` 1.1.20（features 同 rev4：migration＝sqlx-postgres,
  runtime-tokio-rustls, cli；entity＝macros, with-chrono, with-json, with-ipnetwork）、
  `casbin` 2.20.0（default-features=false）、`async-trait` 0.1.89、`tokio` 1.52.3。
  **不引入 `argon2`**（rev4 migration 有、rev5 不需——Q1 拍板 PHC 寫死常數、無 runtime 雜湊）。
- **Rationale**: ①rust 1.96.1 已由 rev4:001-compose-stack 移植定版（deploy/Dockerfile.rust-api
  `FROM rust:1.96.1-slim`、Debian trixie 對齊義務註解在案）——toolchain 非本刀新拍板；
  ②其餘 pins 全數為 rev4 workspace 註解載明之 user 拍板值（「完整三段版號釘死」制度）、
  已驗證組合、與 dev 映像同代；③版本紀律（CLAUDE.md §6）之「雙源對照」以 rev4 lockfile
  為 trusted reference——沿用即承已驗證拍板、非默選新值。
- **Alternatives considered**: 逐項升 crates.io 最新 stable——放棄：基線刀求零變因；
  升版屬日後維護批（統一升＋容器內全量回歸），不與壓平混刀。

## R2 建置／執行容器策略

- **Decision**: 日常路徑走 compose 既有 `migrate` 服務（`rev5-admin-rust-api:dev`、
  entrypoint `cargo run --bin migration`、command `up`——b10 移植時已預接線）。
  pristine 驗證（gate 素材／SC-001 diff）另起**一次性 postgres:18.4-alpine 容器＋獨立
  docker network、零 host 埠發布**，用畢即拆——本刀 clarify 素材產製已實證此流程可行。
- **Rationale**: dev stack 的 postgres 帶 named volume（非 pristine）；驗證鏈語意要求
  乾淨初始化；獨立 network 免碰 dev stack 與埠治理（ADR 0004）。
- **Alternatives considered**: 對 dev stack 的 postgres 重放——放棄（volume 殘留＝非 pristine、
  且 refresh 快照面會被驗證流程污染）。

## R3 m001／m002 施工形

- **Decision**:
  - `m001_baseline_schema`：單支含全結構——`CREATE EXTENSION IF NOT EXISTS pg_trgm`（GIN
    trigram 索引前置、承 rev4:m009 淨效果）→ casbin_rule 委派 adapter 建基底＋同檔 ALTER
    補 3 治理欄（承 rev4:m001 形）→ 14 表 CREATE（欄序＝data-model §2 定稿）→ 全索引／
    約束（含 partial-uniq 活性唯一、GIN trigram）。`down`＝全量反向清理。
  - `m002_baseline_seeds`：全 seed 一支，**完全決定性**（clarify Q1）——INSERT 一律
    **明示 id**＋**明示 `created_at`＝`2026-08-05T00:00:00+00:00`**（不吃欄 default now()）＋
    password 寫死定稿 PHC 常數；casbin_rule 163 列含 protected 值明示；收尾 `setval`
    對齊 sequence 落值（casbin_rule=163、sys_menu=78、sys_role=3、sys_user=3；其餘序列
    不動＝未動用態）。內容唯一來源＝`seed-decision.json`（禁止手抄、施工時機器轉錄）。
- **Rationale**: 明示 id＋setval 使重放結果與凍結 fixtures 逐列全等（含 sequence 落值）
  ——SC-001 字面成立；單支 m001／m002 對齊「壓平」語意與 migration 短編號紀律（下一刀
  自 m003 起編）。
- **Alternatives considered**: 隱式 id（吃 nextval、沿 rev4:m002 形〔rev4 隱式 id 語境、非 rev5 m002〕）——放棄：決定性繫於
  插入順序、且 fixtures 的 id 已定稿，明示更可稽核。

## R4 reaper DB role／GRANTs 不入基線

- **Decision**: rev4:m012／rev4:m013 的 reaper role（NOLOGIN）＋恰好集 GRANTs **不入** rev5 基線。
- **Rationale**: spec 範圍聲明之忠實射程＝「型別／nullable／default／約束／索引」＋seed
  （表資料）——DB role／GRANT 屬 cluster 級運維工件、不在三節快照面，亦非 seed；其歸屬
  域＝observability／audit-retention（隨該域刀重進場、provenance rev4:ADR 0072）。基線閘
  三節比對不涉 role，射程自洽。
- **Alternatives considered**: 忠實搬入 m001——放棄：把運維權限面夾進 schema 壓平刀＝
  擴刀；且 reaper 服務（compose 已有殼）要到 server／reaper 刀才有消費者。

## R5 fixtures 凍結格式

- **Decision**: `specs/001-schema-baseline/fixtures/` ＝ `columns.json`／`indexes.json`／
  `constraints.json`（與 refresh 三查詢同構、自基線實庫照相）＋`seed.sql`（`pg_dump
  --data-only` normalize 版：COPY 段整列排序、保留 setval 行）＋`provenance.md`（產製
  日期／映像／來源 SHA／比對紀錄）。凍結後永不改寫。
- **Rationale**: 三 json 與照相管線同構＝gate1 直接可比、零轉換層；data-only dump 天然
  含 COPY 資料與 setval（sequence 落值入比對面）；rev4 的 varchar 長度 sidecar（rev4:B-055）
  不需要——本格式 `format_type` 已含長度修飾、無資訊損失。
- **Alternatives considered**: 全 pg_dump（含 DDL）當唯一 fixture——放棄：DDL 文字形對
  重排噪音敏感、且結構面已有三 json 全等比對，重複承載。

## R6 三閘重建設計（tools/schema-gate.py 整組重建）

- **Decision**: 重建為 rev5 座標＋演進帳契約（細節＝contracts/gates.md）：
  gate1 結構全等（fixtures 三 json ⊕ schema-evolution.json 合成期望 → vs 實庫照相，
  非容差剝除、未登記漂移一律紅）；gate2 欄序＋seed（欄序 vs data-model §2 定稿逐表全等、
  casbin_rule 欄序豁免；seed vs fixtures/seed.sql 未排序逐列 diff、COPY 段整列排序
  normalize、★禁全檔排序後雜湊）；audit archetype（archetype-map.json 15 表 × §I.6 四變體
  規則逐表驗）。rev4 白名單三段鑿洞模型（rev4:ADR 0032/rev4:0039/rev4:0064 殘留）**整組移除**；
  check 入口無條件合成 self-test（沿 entity-drift-gate 模式：健康對必綠＋注入假漂移必紅、
  self-test 敗＝rc 2 不讀真檔）。退出碼語意沿 repo 工具慣例（0 綠／1 漂移／2 環境結構
  異常／64 用法）。rename map 對賬僅用於「vs rev4 快照」的血緣核對場景（工具內建
  對照表）；rev5 自家管線（fixtures／快照／entity）一律新欄名、不再帶映射。
- **Rationale**: 承 K1-32／K1-39 重審——凍結模型必須配受管演進帳，否則重演三段鑿洞；
  B3 殘留 rev4 字面（`specs/002-…` 座標等）同刀清償。
- **Alternatives considered**: 只補丁改路徑字面——放棄：白名單模型與演進帳模型互斥、
  留白名單＝留鑿洞介面。

## R7 演進登記檔 schema

- **Decision**: `docs/ops/reference-src/schema-evolution.json`（單一登記檔、與快照同家）；
  形＝`{"next_id", "entries":[{id:"E-NNN", knife:"NNN-slug", kind:enum, table, detail,
  date}]}`；kind 枚舉＝add_table／add_column／alter_column／add_index／add_constraint／
  seed_add／seed_update／seed_delete；啟動斷言＝頂層鍵恰集＋逐筆欄位齊全非空＋knife 格式
  `^\d{3}-[a-z0-9-]+$`＋kind 入枚舉＋id 格式遞增不回收。基線初始態＝空 entries。
  細節＝contracts/schema-evolution.md。
- **Rationale**: 「凍結＋登記」合成全等比對（brainstorm §3 拍板）；specs/ 下屬凍結史料、
  放彼處違時態語意——演進面住 reference-src（跨刀更新）。

## R8 entity crate 形制

- **Decision**: 15 個 entity 檔（含 casbin_rule.rs——drift 比對豁免該表、但 entity 面
  完整）＋lib.rs 匯出；sea-orm features 恰四項（macros／with-chrono→timestamptz／
  with-json→jsonb／with-ipnetwork→inet，承 rev4 R6）；欄名＝rename 後 rev5 定稿名。
  全新打字（§I.5、參照 rev4 對照驗證但不拷貝）；entity-drift-gate 既建（rev4:B-110 階段 0）
  ——快照就位後 pre-commit 自動恢復實跑、毋需改 hook。
- **Rationale**: entity-drift 左源＝rev5 快照（rename 後欄名）→ entity 必同名，否則
  drift 紅；casbin_rule entity 面在場（rev4 同形）供後續 server 刀消費。

## R9 DoD 鏈與 Day-1 拔項的機器形

- **Decision**: refresh 首跑（dev stack、`soybean`/`soybean_admin_rust`）→
  兩快照＋archetype-map 就位 → `gen.snapshots` 解除謂詞（三檔存在）成立 → 依「到期即紅」
  自 `DAY1_EXEMPTIONS`／`DAY1_EXEMPT_SCOPE` 雙表拔項（留日期註解、循 gen.compose／
  gen.screens 前例）→ generate 重算 schema／accounts 真表 → pre-commit 全綠。
  entity-drift Day-1 跳過＝pre-commit 既有分支（快照缺席才跳）——快照就位**自動恢復
  實跑、零改碼**；「entity 目錄缺席擋 commit」演練依其觸發面（rust-api gitlink 或快照
  staged 時）驗證 rc 2。
- **Rationale**: 全部機制 b8a／b10 已就位且經突變實證（拔項會翻紅）；本刀只負責讓
  謂詞成立並執行拔項。
