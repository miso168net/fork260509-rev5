<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0af3690｜rust-api=47e8a67

## constitution
- 版本：1.7.0

## 帳面統計
- ADR：52（accepted 50、superseded 2）
- BACKLOG 待辦：46（next：B-110）｜滯後：1
- LESSONS：51 筆（next：L-052）
- events：31 筆（feature_close 5、misc 26）

## 最近事件（尾 3 筆、新在前）
- 2026-08-22｜feature_close｜005-role-menu-crud｜role＋menu 管理 CRUD 寫端縱切（本代第五刀）：16 支端點全上、ROUTES 22→38 終態；選單序列化域／casbin rebuild-swap 熱重載（觸發恰移除面三支）／授權歸檔寫入面（掃描前置於軟刪）三底座；前端 role/menu 兩頁＋回收桶＋memo 欄（兩顆授權 modal 零 diff）；零繼承端到端雙斷言（島 H2 in-memory 機器證）。rust 測試 512→650、backend 樹 50 鍵、憲法 1.6.2→1.7.0（島 H）、零 migration。
- 2026-08-18｜misc｜治理工具鏈整併批收單（輕量軌、merge d72553b）：B-080 納冊（TOOLS_PY 12→14、pre-commit 迴圈＋HOOK_TEST_LOOP_EXEMPT 豁免、route-artifact-gate 只接 test）＋B-081 Lint27（README 樹 vs tools/＋deploy/ 腳本檔集對賬、兩向紅）＋B-086 compose anchor 消抄本（ADR 0046）＋B-092 bootstrap ROOT 物理化＋B-087 半關（ADR 0047 引量三形紀律）；L-048、docs-sync 自測 524、lint 條款 26
- 2026-08-18｜misc｜Lint27 README 目錄樹對賬閘上線（B-081、治理批 U1）：tools/／deploy/ 兩目錄 *.py／*.sh 實檔集 vs README 樹列名相等斷言、漏列與幽靈兩向紅、紅只報不改（樹屬人寫面）；同單元 B-080 納冊——view-render-guard／route-artifact-gate 入 TOOLS_PY（12→14）、bootstrap 體檢與 pre-commit 迴圈同步接線（view-render-guard 走具名豁免不入迴圈）；名冊三檔範圍字串同 commit bump 至 Lint03～Lint27；本筆即新名冊承載事件

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
