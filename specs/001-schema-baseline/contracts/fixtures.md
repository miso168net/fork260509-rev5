# contracts/fixtures.md — 凍結面（fixtures/）契約

> 檔集＝`specs/001-schema-baseline/fixtures/`；**定稿產物、凍結後永不改寫**、provenance
> 保存。消費者＝gate1（三 json）、gate2 seed 面（seed.sql）、SC-001 重放驗證。

## 1. 檔集（恰五件）

| 檔 | 內容 | 產製 |
|---|---|---|
| `columns.json` | 實庫欄快照（與 refresh 同構、確定性排序） | 基線實庫照相 |
| `indexes.json` | 索引快照（同上） | 同上 |
| `constraints.json` | 約束快照（同上、含 NOT NULL 逐欄形） | 同上 |
| `seed.sql` | `pg_dump --data-only` normalize 版（normalize 全則＝gates.md §2 seed 面：COPY 段整列排序、setval 保留、pg_dump 框架噪音兩類剝除） | 基線實庫 dump |
| `provenance.md` | 產製紀錄（見 §3） | 人寫＋機器值 |

## 2. 產製程序（實作階段執行一次）

1. 一次性 pristine `postgres:18.4-alpine`（獨立 network、零 host 埠）重放 rev5
   m001＋m002。
2. 先驗後凍：實庫 vs `seed-decision.json` 逐列比對零差異＋vs data-model §2 欄序全等＋
   （血緣核對）結構三節經 data-model §4 授權偏離集 normalize（rename／region／trace_id／
   real_ip NN／預設 now()）後 vs rev4 快照全等——三驗全綠才照相落檔。
3. 照相＋dump→normalize→落 fixtures/ 五件→同 commit 凍結。

## 3. provenance.md 必載欄目

產製日期；容器映像（postgres／rust dev）；m001/m002 所在 rust-api commit SHA；
seed-decision.json sha256；三驗紀錄（§2-2 的三綠）；產製與 normalize 命令形。

## 4. 不變式

- 凍結後任何位元變更＝違憲級（pre-commit 不設專閘、由 review 與 gate1 語意承載：fixtures
  變 → gate1 期望變 → 未登記漂移紅之對偶形現形）。
- 「重產 fixtures」唯一合法路徑＝基線翻案新刀（新 ADR supersedes＋新 fixtures 目錄）。
  **具名例外（唯一、已用畢）**：2026-08-06 依 ADR 0008（DB 身分不帶世代後綴、user 拍板
  ＋回滾批計畫過目後「動工」批准）刀內重產一次——重走 §2 先驗後凍三驗、位元射程恰
  pg_dump `Owner:` 註解行（seed.sql ±26；三 json 位元零變）、provenance §1 在案。
  本例外不開放沿用：其後任何重產仍走本條主文。
- 快照三 json 與 `docs/ops/reference-src/schema-snapshot.json`（refresh 產、跨刀前進）
  職責不同：fixtures＝凍結史料（不動）、reference-src＝現況帳（隨刀 refresh）。
