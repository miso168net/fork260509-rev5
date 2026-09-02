<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=9833308｜rust-api=92919b9

## constitution
- 版本：1.10.0

## 帳面統計
- ADR：79（accepted 77、superseded 2）
- BACKLOG 待辦：28（next：B-165）｜滯後：7
- LESSONS：87 筆（next：L-088）
- events：97 筆（feature_close 8、misc 52、perf 37）

## 最近事件（尾 3 筆、新在前）
- 2026-09-02｜feature_close｜008-audit-settings-pages｜稽核中心與系統設定頁：B-008 餘兩張管理頁全數兌現——settings 頁純前端接線、audit 頁四源四分頁與水平線清理，新開五端點（ROUTES 61→66、POLICY 45→50、零 migration）。機器守三條：purge 單交易原子性 fault-injection、logout TTL 次序同形測、Lint24 第三腿。憲法 1.9.1→1.10.0（第十座行為島 J 入憲）、ADR 0077～0079。rust 1015→1108、docs-sync 自測 633→654、wire definitions 89→101、seed-view-gate 豁免表 2→0。
- 2026-08-31｜misc｜微批收單（merge c008aea）：M1＝B-154 DRILL_IMAGE×compose postgres image parity 測（backup-db 自測 49→50）；M2＝B-098 收官——wire_schema.rs 補 Api.IpRule.* 七 definition 裁判 15 測（容器全量 1000→1015、fixture 未動）；fhr 雙透鏡 3 筆＝RUNBOOK §12 案數註兩處併本簿記顆修＋一則前批 629→633 順手訂正
- 2026-08-31｜misc｜微批 M2（獨立單元）：wire_schema.rs 補齊 Api.IpRule.* 七 definition 裁判（15 測、每 definition 正向＋反例；毋須重抽快照、fixture 未動）＋檔頭與節註三處現在式句改對——B-098 收官關帳；觸發器拉前＝user 2026-08-31 口令；rust 容器測試 1000→1015（failed 0／ignored 2＝基線既有 env-gate 對）

## 效能引信（ADR 0044）
- 狀態：未觸發｜最近兩筆 close_bookkeeping：2026-08-31 11.96s、2026-09-02 11.59s｜判準＝連續兩筆 wall_s ≥ 60s（只採收刀簿記型實測；全序列→reference/perf）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
- reference/perf：真表（來源＝docs/ops/events.jsonl 的 perf 事件、由 generate 重算；ADR 0070 效能資料點序列、引信機器判見上方效能引信行）
