<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=24317d0｜rust-api=60da796

## constitution
- 版本：1.3.1

## 帳面統計
- ADR：37（accepted 37）
- BACKLOG 待辦：27（next：B-072）｜滯後：1
- LESSONS：28 筆（next：L-029）
- events：23 筆（feature_close 3、misc 20）

## 最近事件（尾 3 筆、新在前）
- 2026-08-11｜feature_close｜003-auth-session｜auth 域整批收刀（本代最大一刀、SDD＋Workflow 編排全流程首次走完）：US1 真登入＋角色化 dynamic 選單／US2 refresh rotation＋30 秒 grace 冪等／US3 撤銷矩陣（logout・被踢・閒置）／US4 節流三區＋圖形驗證碼整套首版／US5 替代登入誠實 stub＋三語 i18n 轉譯。ROUTES 4→16（終態）、測試 145→321、tasks 77/77。憲法 1.2.0→1.3.0（ADR 0028：§III.2 首開四條 ★ 軌道八用途＋§I.7 首批五座行為島）；DAY1_EXEMPTIONS 拔最後一項、自此空表。
- 2026-08-09｜misc｜帳面更正批收單（輕量軌、merge ea4a470、★零關帳）：上一批承諾「§5 帳面更正一起收進簿記」只落兩列，本批補完其餘六筆——B-008 補 static 前提／B-022 自助頁在 rev5 是整頁未建（非佔位控件）／B-023 定軌別為輕量軌／B-024 補無 body 通道等三筆／B-029 圖形 captcha 是整套首版非半條／B-030 刪雙卡子項。B-043 兩處置候選經實證推翻、條目改寫並落特性測試＋機器守。新增 L-014。
- 2026-08-09｜misc｜B12 後衛生維護批收單（輕量軌、merge cdf6eb7）：B-049 config 測試暫存檔掛 RAII 清理守衛（/tmp 每輪 +5→0）｜B-052 兩支還原守衛 Drop 抽共用 run_restore_stmt｜B-045 main.rs 改走 ConnectOptions、sqlx 語句 log 自 INFO 降 DEBUG（新增 log 直依賴、lock 套件數 441→441）｜B-011 gate2 seed normalize 擴入環境相依噪音族＋owner 補償守門（ADR 0026）四項關帳；B-042 收其②半，①殘半屬拍板級續留。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
