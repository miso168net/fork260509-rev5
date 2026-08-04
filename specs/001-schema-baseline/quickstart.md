# quickstart — 001-schema-baseline 驗證指南

> 端到端驗證場景（US1～US4 對應）；細節指向 data-model.md 與 contracts/、不重複轉錄。
> 全部 rust 操作容器內、serial；host 無 toolchain。

## 前置

- `bash tools/bootstrap.sh` 綠（掃描防線就位）；docker 可用。
- 映像：`postgres:18.4-alpine`（本機已有）；`rev5-admin-rust-api:dev`
  （`docker compose build rust-api` 自 `deploy/Dockerfile.rust-api` 建）。

## A. 基線重放（US1／US2 主流程）

```sh
# dev stack 路徑（named volume、日常）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait postgres
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm migrate   # ＝ migration up
```

預期：`m001_baseline_schema`／`m002_baseline_seeds` 兩支 applied、零錯。
pristine 驗證路徑（SC-001／fixtures 產製）＝一次性容器＋獨立 network（形同 clarify 素材
產製流程；命令形載 fixtures/provenance.md）。

## B. 三閘全跑（US3）

```sh
python3 tools/schema-gate.py check     # gate1＋gate2＋audit；先自證 self-test
python3 tools/schema-gate.py test      # 合成自測＋negative 注入（四類假漂移必紅）
```

預期：check rc 0（三閘綠、輸出逐閘一行摘要）；test 全綠（含 SC-002 四類注入全紅之斷言）。

## C. 演進帳往返驗證（US3 場景 2～4）

1. 對實庫注入未登記漂移（如 `ALTER TABLE sys_user ADD COLUMN tmp_x text`）→ check rc 1、
   指名 `columns/sys_user/tmp_x`。
2. 於 `docs/ops/reference-src/schema-evolution.json` 補登記該欄（帶來源刀編號）→ check
   rc 0。
3. 改壞登記檔（刪 `date` 欄）→ check rc 2、啟動斷言指名。
4. 還原（撤登記＋DROP COLUMN）→ check rc 0。

## D. SC-001 逐列全等（fixtures 凍結後）

pristine 重放 → 照相＋dump normalize → 與 fixtures/ 五件比對：三 json 全等＋seed.sql
diff 零行（含 id、password、created_at、setval 落值——零豁免欄）。

## E. DoD 鏈（US4；順序固定）

```sh
python3 tools/docs-sync.py refresh     # 需 dev stack；產兩快照
# archetype-map.json 初版入版（data-model §1 轉錄）
# DAY1_EXEMPTIONS／DAY1_EXEMPT_SCOPE 拔 gen.snapshots（謂詞已成立、到期即紅強制）
python3 tools/docs-sync.py generate    # schema／accounts 真表首算
python3 tools/docs-sync.py lint        # 全綠；跳過明細零 gen.snapshots
git commit（任一）                      # pre-commit 全鏈綠（含 entity-drift 實跑）
```

entity 防線演練：暫移 `rust-api/entity/src` → 對 rust-api pin bump 的 commit 應被
entity-drift-gate rc 2 擋下 → 還原後綠。

## 驗收對照

| 場景 | spec 錨 |
|---|---|
| A 重放零錯＋欄序全等 | US1、SC-003 |
| B/C 三閘＋演進帳往返 | US3、SC-005 |
| D 逐列全等零豁免 | US2、SC-001、SC-002 |
| E DoD 鏈全綠＋防線演練 | US4、SC-006 |
| seed 簽核紀錄在案 | SC-004（clarify 已完成） |
