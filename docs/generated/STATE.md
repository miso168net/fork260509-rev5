<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=b827063｜rust-api=515177e

## constitution
- 版本：1.9.1

## 帳面統計
- ADR：75（accepted 73、superseded 2）
- BACKLOG 待辦：24（next：B-156）｜滯後：7
- LESSONS：74 筆（next：L-075）
- events：95 筆（feature_close 7、misc 52、perf 36）

## 最近事件（尾 3 筆、新在前）
- 2026-08-31｜misc｜微批收單（merge c008aea）：M1＝B-154 DRILL_IMAGE×compose postgres image parity 測（backup-db 自測 49→50）；M2＝B-098 收官——wire_schema.rs 補 Api.IpRule.* 七 definition 裁判 15 測（容器全量 1000→1015、fixture 未動）；fhr 雙透鏡 3 筆＝RUNBOOK §12 案數註兩處併本簿記顆修＋一則前批 629→633 順手訂正
- 2026-08-31｜misc｜微批 M2（獨立單元）：wire_schema.rs 補齊 Api.IpRule.* 七 definition 裁判（15 測、每 definition 正向＋反例；毋須重抽快照、fixture 未動）＋檔頭與節註三處現在式句改對——B-098 收官關帳；觸發器拉前＝user 2026-08-31 口令；rust 容器測試 1000→1015（failed 0／ignored 2＝基線既有 env-gate 對）
- 2026-08-31｜misc｜微批 M1（主線直改）：deploy/backup-db.py 補 DRILL_IMAGE×docker-compose.yml postgres image 字面 parity 測（第六面 parity；stdlib 正則、compose 恰一處斷言；此前唯一釘子屬套套邏輯、對 compose 面零覆蓋）——B-154 關帳；觸發器拉前＝user 2026-08-31 口令

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-31 15.62s、2026-08-31 11.96s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
