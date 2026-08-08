<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=5089c28｜rust-api=fb41d9d

## constitution
- 版本：1.2.0

## 帳面統計
- ADR：25（accepted 25）
- BACKLOG 待辦：27（next：B-053）｜滯後：1
- LESSONS：13 筆（next：L-014）
- events：20 筆（feature_close 2、misc 18）

## 最近事件（尾 3 筆、新在前）
- 2026-08-08｜misc｜maint-l013 收單（merge c59251f）：002-system-settings 凍結期遺漏待辦補登——交接前核對該刀 scratchpad 16 筆待辦，4 筆無 in-repo 落點。補為 LESSONS L-013（DatabaseConnection::Disconnected 不是統一失敗態、get_database_backend() 是唯一 panic 點）＋BACKLOG B-050（sys_user_role 次段查詢的 DbErr 落地無機器守）／B-051（test_kit 寄居）／B-052（兩個 RAII guard 的 Drop 逐字重複）
- 2026-08-08｜misc｜maint-l011-l012 收單（輕量軌、merge 737f8d8）：maint-l010 收單後核對出的三件「說了但沒真正落實」一併補齊——LESSONS L-011（workflow 編排 script 把已完成的工作誤報成失敗：狀態欄跨角色語意複用／fix 迴圈跑滿無確認輪）＋L-012（submodule 內檔案的還原在外層 repo 執行會靜默失敗）＋CLAUDE.md §2 防呆六件套 ④⑤ 補強（user 拍板）＋rust-api 的 DECISION_SUFFIXES 版本錨（把「升版 casbin 記得回核」機器化）
- 2026-08-08｜misc｜maint-l010 收單（輕量軌、merge fac52b0）：守門自證紀律成文化——LESSONS L-010（判準對被判對象某類變動結構性無感＝恆綠、四種致因）＋ADR 0024（守門機制必附 non-vacuous 生效自證：合成正例／判準不共變／落地破壞性驗證）＋ADR 0025（憲法 §I.5 註解射程釋義，B-046 消化）；首批消費者同刀落地＝B-048 strip 引擎單一來源化＋B-044 授權判定進入點閘＋entity_behavior_lint 掃描面完整性補強。衍生 B-049

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
