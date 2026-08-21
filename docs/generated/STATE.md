<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0af3690｜rust-api=3ecc9a5

## constitution
- 版本：1.7.0

## 帳面統計
- ADR：50（accepted 48、superseded 2）
- BACKLOG 待辦：43（next：B-101）｜滯後：1
- LESSONS：49 筆（next：L-050）
- events：30 筆（feature_close 4、misc 26）

## 最近事件（尾 3 筆、新在前）
- 2026-08-18｜misc｜治理工具鏈整併批收單（輕量軌、merge d72553b）：B-080 納冊（TOOLS_PY 12→14、pre-commit 迴圈＋HOOK_TEST_LOOP_EXEMPT 豁免、route-artifact-gate 只接 test）＋B-081 Lint27（README 樹 vs tools/＋deploy/ 腳本檔集對賬、兩向紅）＋B-086 compose anchor 消抄本（ADR 0046）＋B-092 bootstrap ROOT 物理化＋B-087 半關（ADR 0047 引量三形紀律）；L-048、docs-sync 自測 524、lint 條款 26
- 2026-08-18｜misc｜Lint27 README 目錄樹對賬閘上線（B-081、治理批 U1）：tools/／deploy/ 兩目錄 *.py／*.sh 實檔集 vs README 樹列名相等斷言、漏列與幽靈兩向紅、紅只報不改（樹屬人寫面）；同單元 B-080 納冊——view-render-guard／route-artifact-gate 入 TOOLS_PY（12→14）、bootstrap 體檢與 pre-commit 迴圈同步接線（view-render-guard 走具名豁免不入迴圈）；名冊三檔範圍字串同 commit bump 至 Lint03～Lint27；本筆即新名冊承載事件
- 2026-08-17｜misc｜B-090 LESSONS 分檔制遷移收單（輕量軌 maint-b090、merge ae5c24d）：分卷制→分檔制——47 條 byte-diff 逐位遷入 docs/ops/LESSONS/、主檔改寫手寫索引（47 行逐條精寫 hook）、晉升必答欄 promoted_to 落值（實值 35／佔位 12→B-091 承載）、刪 LESSONS-001-028.md；工具面（U1 commit 8b0cd9e）＝Lint26 分檔對賬＋Lint07 單條上限＋Lint09 head 視野聯集＋ADR 0045、docs-sync 自測 496→517；衍生 B-092

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
