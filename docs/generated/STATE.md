<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=ae1ac0c｜rust-api=041a87c

## constitution
- 版本：1.8.0

## 帳面統計
- ADR：59（accepted 57、superseded 2）
- BACKLOG 待辦：35（next：B-131）｜滯後：7
- LESSONS：61 筆（next：L-062）
- events：37 筆（feature_close 6、misc 31）

## 最近事件（尾 3 筆、新在前）
- 2026-08-25｜misc｜B-057 裁決落帳（輕量軌、merge d0bcd2a）：user 親決選候選 (a)——logout 呈遞 rotated 票維持 0000 靜默 no-op、撤銷射程恆為單列不擴 revoke_family，立 ADR 0059 關帳。★落點自條目原寫的 data-model §1 改為 ADR：003 收刀後 specs/ 樹成史料不可改（ADR 0058 決定 3 逐字），依 CLAUDE.md §4「won't-fix／by-design 也立 ADR」。logout.rs 兩處碼註（原記「歸主線裁」）改指 ADR 0059。
- 2026-08-25｜misc｜BACKLOG 滯後卷搬移（輕量軌、merge c57a0d5）：判準沿滯後卷先例 B-034「觸發權不在近期 roadmap 內」，六條整行搬入 BACKLOG-DEFERRED.md 附滯後戳記（B-033／B-043／B-059／B-070／B-076／B-077）；★滯後≠完成故不帶 backlog_done。配套補三處入口指針（主檔檔頭／README 地圖＋快查表／CLAUDE.md 快查去處）——搬移前三入口皆單向指涉、主檔少六條即無從得知另有一卷。BACKLOG 42→36、滯後 1→7。
- 2026-08-25｜misc｜刀 B 前置維護批收單（輕量軌、merge 53d7a67）：11 筆關帳——活書單節配額放寬＋停損絆線（B-083／ADR 0058）；rust 收攏四件（B-106 消 N+1／B-108／B-115 穩定序／B-123）；rust 守門三道（B-111 wire i64 守衛 lint／B-075 serve 備線 lint／B-074 mapped 網段告警）；前端三件（B-100／B-116 請求世代／B-117 4xx 走譯文，皆 CDP 實證含反例）。rust 測試 793→829、LESSONS 五則（L-057～L-061）、零 migration、ROUTES 恆 49。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
