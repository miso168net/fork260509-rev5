<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=5089c28｜rust-api=ced6ac6

## constitution
- 版本：1.3.0

## 帳面統計
- ADR：34（accepted 34）
- BACKLOG 待辦：24（next：B-054）｜滯後：1
- LESSONS：14 筆（next：L-015）
- events：22 筆（feature_close 2、misc 20）

## 最近事件（尾 3 筆、新在前）
- 2026-08-09｜misc｜帳面更正批收單（輕量軌、merge ea4a470、★零關帳）：上一批承諾「§5 帳面更正一起收進簿記」只落兩列，本批補完其餘六筆——B-008 補 static 前提／B-022 自助頁在 rev5 是整頁未建（非佔位控件）／B-023 定軌別為輕量軌／B-024 補無 body 通道等三筆／B-029 圖形 captcha 是整套首版非半條／B-030 刪雙卡子項。B-043 兩處置候選經實證推翻、條目改寫並落特性測試＋機器守。新增 L-014。
- 2026-08-09｜misc｜B12 後衛生維護批收單（輕量軌、merge cdf6eb7）：B-049 config 測試暫存檔掛 RAII 清理守衛（/tmp 每輪 +5→0）｜B-052 兩支還原守衛 Drop 抽共用 run_restore_stmt｜B-045 main.rs 改走 ConnectOptions、sqlx 語句 log 自 INFO 降 DEBUG（新增 log 直依賴、lock 套件數 441→441）｜B-011 gate2 seed normalize 擴入環境相依噪音族＋owner 補償守門（ADR 0026）四項關帳；B-042 收其②半，①殘半屬拍板級續留。
- 2026-08-08｜misc｜maint-l013 收單（merge c59251f）：002-system-settings 凍結期遺漏待辦補登——交接前核對該刀 scratchpad 16 筆待辦，4 筆無 in-repo 落點。補為 LESSONS L-013（DatabaseConnection::Disconnected 不是統一失敗態、get_database_backend() 是唯一 panic 點）＋BACKLOG B-050（sys_user_role 次段查詢的 DbErr 落地無機器守）／B-051（test_kit 寄居）／B-052（兩個 RAII guard 的 Drop 逐字重複）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
