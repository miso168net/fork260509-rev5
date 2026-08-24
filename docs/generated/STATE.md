<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=673f206｜rust-api=d940d03

## constitution
- 版本：1.8.0

## 帳面統計
- ADR：57（accepted 55、superseded 2）
- BACKLOG 待辦：48（next：B-126）｜滯後：1
- LESSONS：56 筆（next：L-057）
- events：34 筆（feature_close 6、misc 28）

## 最近事件（尾 3 筆、新在前）
- 2026-08-25｜misc｜刀 B 起手維護批（批次 A：測試設施＋工具鏈、輕量軌、merge 3d72756）：九筆關帳（B-121／B-122 守衛面結構性修正＝L-055 兩次弄紅收刀閘的根因；B-109／B-110 測試建構點收攏；B-051／B-056 test_kit 遷位與 PG 層 fault-injection seam；B-114／B-118 乾跑案與註記；B-112 rust 格式守門上線）。rust 測試 793、docs-sync 自測 524→527、治理工具名冊 15→16 支、ADR 0057、L-056、零 migration。
- 2026-08-24｜feature_close｜006-authz-governance｜三維授權治理縱切（本代第六刀、B-088 關帳）：三維讀寫六支＋支撐讀三支＋回收桶兩支共 11 端點、ROUTES 38→49 終態；結構性封死（謂詞式鎖內現查）＋全量替換射程＝候選集＋restore 五腿固定序；前端三顆授權 modal 接真（protected 雙保險＋就緒守）＋roleHome＋policy-archive 頁＋B-099；seed-view-gate 對賬閘。rust 測試 682→793、wire-schema 57→75＋16 裁判、憲法 1.8.0（島 G＋(iii)(iv)）、ADR 0053～0056、零 migration；CDP 30 步零缺陷。
- 2026-08-23｜misc｜授權治理刀起手維護批收單（輕量軌、merge 524d8b9）：B-094 handler／facade 共用件收攏（新檔 handler/common.rs＋facade violated_constraint）＋B-101 AppState 測試建構點收攏（test_db::test_state 單一字面＋(Router, AppState) 變體）＋B-085 IpRuleCleanup 自證測＋B-102 空字串→NULL 三測＋B-098 RoleAdmin／MenuAdmin 十二裁判（IpRule 留帳）；測試 650→682、零行為變更、零 migration

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
