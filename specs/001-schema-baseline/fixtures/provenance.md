# fixtures/provenance.md — 凍結面產製紀錄（contracts/fixtures.md §3 六欄目）

> 本目錄五件＝001-schema-baseline 定稿凍結產物，**凍結後永不改寫**（重產唯一合法路徑＝
> 基線翻案新刀、新 ADR supersedes）。

## 1. 產製日期

2026-08-05（先驗後凍三驗同日全綠後照相落檔）。

## 2. 容器映像

- postgres：`postgres:18.4-alpine`（一次性 pristine 容器 `rev5-u3-fixpg`、獨立 network
  `rev5-u3-fixnet`、零 host 埠發布、用畢即拆；`SHOW timezone`＝`UTC`、UTC+0 拍板）
- rust dev（migration 重放）：`rev5-admin-rust-api:dev`

## 3. m001／m002 所在 rust-api commit SHA

`68be986`（rust-api worktree HEAD；migration 序列＝m001_baseline_schema＋
m002_baseline_seeds、重放輸出兩支 applied 零錯）

## 4. seed-decision.json sha256

`438e25664b4b85a1ee0ddf6064776537edbe58ead900bd1678ea7f7b295802e2`
（`specs/001-schema-baseline/seed-decision.json`＝m002 唯一內容權威）

## 5. 三驗紀錄（contracts/fixtures.md §2-2；三綠才照相落檔）

1. **vs seed-decision 逐列**（check-m002.py --container rev5-u3-fixpg）：
   `check-m002：綠——15 表逐列全等（266 列＝定稿 266 列、零豁免欄含 password／created_at／
   protected）；sequences 名冊 11 支、落值 casbin_rule_id_seq=163/sys_menu_id_seq=78/
   sys_role_id_seq=3/sys_user_id_seq=3、其餘 7 支未動用；timezone=UTC（UTC+0）`
2. **vs data-model §2 欄序**（check-m001.py 同容器、A 面）：
   `check-m001：綠——15 表在場；§2 欄序 14 表全等；…總量 columns=169／indexes=38／
   constraints=101`
3. **血緣核對 vs rev4 快照**（check-m001.py 同輪、B 面；rev4 repo
   `docs/ops/reference-src/schema-snapshot.json` 經 data-model §4 授權偏離集全項
   normalize——rename map 4 組＋region 新增＋trace_id 改 text＋real_ip NN＋預設統一
   now()）：`血緣 normalize 後 columns／indexes／constraints 全等`

## 6. 產製與 normalize 命令形

```sh
# 一次性 pristine（零 host 埠、獨立 network）
docker network create rev5-u3-fixnet
docker run -d --name rev5-u3-fixpg --network rev5-u3-fixnet \
  -e POSTGRES_USER=soybean_rev5 -e POSTGRES_PASSWORD=<拋棄式> \
  -e POSTGRES_DB=soybean_admin_rust_rev5 postgres:18.4-alpine
# 重放（容器內、serial）
docker run --rm --network rev5-u3-fixnet -v <repo>/rust-api:/app \
  -v rev5-admin_rust_api_cargo_cache:/usr/local/cargo/registry \
  -v rev5-admin_rust_api_target:/app/target \
  -e APP_DATABASE_URL=postgres://soybean_rev5:<拋棄式>@rev5-u3-fixpg:5432/soybean_admin_rust_rev5 \
  --entrypoint cargo rev5-admin-rust-api:dev run --bin migration up
# 照相三 json＝tools/schema-gate.py 之三查詢（docs-sync refresh 同構）＋確定性排序
#（columns 依 table,ordinal；indexes/constraints 依 table,name）、json indent 2 落檔
# seed.sql＝pg_dump -U soybean_rev5 -d soybean_admin_rust_rev5 --data-only（PGTZ=UTC）
# 經 tools/schema-gate.py normalize_seed_dump（gates.md §2 全則：COPY 段整列排序＋setval
# 原位＋剝除 \restrict／\unrestrict token 行＋seaql_migrations COPY 段）；冪等斷言＋
# setval 名冊 vs seed-decision sequences 節斷言後落檔
```
