<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=ae1ac0c｜rust-api=1193bb9

## constitution
- 版本：1.8.0

## 帳面統計
- ADR：58（accepted 56、superseded 2）
- BACKLOG 待辦：36（next：B-131）｜滯後：7
- LESSONS：61 筆（next：L-062）
- events：36 筆（feature_close 6、misc 30）

## 最近事件（尾 3 筆、新在前）
- 2026-08-25｜misc｜BACKLOG 滯後卷搬移（輕量軌、merge c57a0d5）：判準沿滯後卷先例 B-034「觸發權不在近期 roadmap 內」，六條整行搬入 BACKLOG-DEFERRED.md 附滯後戳記（B-033／B-043／B-059／B-070／B-076／B-077）；★滯後≠完成故不帶 backlog_done。配套補三處入口指針（主檔檔頭／README 地圖＋快查表／CLAUDE.md 快查去處）——搬移前三入口皆單向指涉、主檔少六條即無從得知另有一卷。BACKLOG 42→36、滯後 1→7。
- 2026-08-25｜misc｜刀 B 前置維護批收單（輕量軌、merge 53d7a67）：11 筆關帳——活書單節配額放寬＋停損絆線（B-083／ADR 0058）；rust 收攏四件（B-106 消 N+1／B-108／B-115 穩定序／B-123）；rust 守門三道（B-111 wire i64 守衛 lint／B-075 serve 備線 lint／B-074 mapped 網段告警）；前端三件（B-100／B-116 請求世代／B-117 4xx 走譯文，皆 CDP 實證含反例）。rust 測試 793→829、LESSONS 五則（L-057～L-061）、零 migration、ROUTES 恆 49。
- 2026-08-25｜misc｜刀 B 起手維護批（批次 A：測試設施＋工具鏈、輕量軌、merge 3d72756）：九筆關帳（B-121／B-122 守衛面結構性修正＝L-055 兩次弄紅收刀閘的根因；B-109／B-110 測試建構點收攏；B-051／B-056 test_kit 遷位與 PG 層 fault-injection seam；B-114／B-118 乾跑案與註記；B-112 rust 格式守門上線）。rust 測試 793、docs-sync 自測 524→527、治理工具名冊 15→16 支、ADR 0057、L-056、零 migration。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
