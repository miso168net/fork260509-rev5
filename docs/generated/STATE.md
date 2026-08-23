<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=673f206｜rust-api=dc1cc8c

## constitution
- 版本：1.8.0

## 帳面統計
- ADR：56（accepted 54、superseded 2）
- BACKLOG 待辦：51（next：B-117）｜滯後：1
- LESSONS：53 筆（next：L-054）
- events：32 筆（feature_close 5、misc 27）

## 最近事件（尾 3 筆、新在前）
- 2026-08-23｜misc｜授權治理刀起手維護批收單（輕量軌、merge 524d8b9）：B-094 handler／facade 共用件收攏（新檔 handler/common.rs＋facade violated_constraint）＋B-101 AppState 測試建構點收攏（test_db::test_state 單一字面＋(Router, AppState) 變體）＋B-085 IpRuleCleanup 自證測＋B-102 空字串→NULL 三測＋B-098 RoleAdmin／MenuAdmin 十二裁判（IpRule 留帳）；測試 650→682、零行為變更、零 migration
- 2026-08-22｜feature_close｜005-role-menu-crud｜role＋menu 管理 CRUD 寫端縱切（本代第五刀）：16 支端點全上、ROUTES 22→38 終態；選單序列化域／casbin rebuild-swap 熱重載（觸發恰移除面三支）／授權歸檔寫入面（掃描前置於軟刪）三底座；前端 role/menu 兩頁＋回收桶＋memo 欄（兩顆授權 modal 零 diff）；零繼承端到端雙斷言（島 H2 in-memory 機器證）。rust 測試 512→650、backend 樹 50 鍵、憲法 1.6.2→1.7.0（島 H）、零 migration。
- 2026-08-18｜misc｜治理工具鏈整併批收單（輕量軌、merge d72553b）：B-080 納冊（TOOLS_PY 12→14、pre-commit 迴圈＋HOOK_TEST_LOOP_EXEMPT 豁免、route-artifact-gate 只接 test）＋B-081 Lint27（README 樹 vs tools/＋deploy/ 腳本檔集對賬、兩向紅）＋B-086 compose anchor 消抄本（ADR 0046）＋B-092 bootstrap ROOT 物理化＋B-087 半關（ADR 0047 引量三形紀律）；L-048、docs-sync 自測 524、lint 條款 26

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
