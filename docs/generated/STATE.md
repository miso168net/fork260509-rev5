<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=854a72e｜rust-api=041a87c

## constitution
- 版本：1.8.0

## 帳面統計
- ADR：61（accepted 59、superseded 2）
- BACKLOG 待辦：36（next：B-134）｜滯後：7
- LESSONS：62 筆（next：L-063）
- events：39 筆（feature_close 6、misc 33）

## 最近事件（尾 3 筆、新在前）
- 2026-08-25｜misc｜B-130 關帳（輕量軌、merge a3cd9f8、ADR 0061）：pre-commit 全鏈 43.46s→13.09s（3.3×）。★原列三處置面全數證偽——都假設成本在條款邏輯，實測是 drvfs I/O 稅（lint 的檔案系統原語佔 64%、邏輯僅 7%；fork-delta 的 select.poll 佔 99%）。A＝閘並行派發（機密面序列前導、fail-fast 改 run-all）；B＝_read 作用域快取＋EAFP＋git show 並行預取。守門三調整＋三變異紅證，529 案全綠。
- 2026-08-25｜misc｜B-097 收單（輕量軌、merge d3b57d6）：menu 治理清單分頁列改「凍結」而非抽除或接真（user 拍板、ADR 0060）——UI 位置不動、頁碼 1／每頁 0／整列上鎖，prefix 續顯真實筆數；回收桶模式一行不動。★itemCount 必須讓位 pageCount：保留它而設 pageSize=0 會令 pageCount=Infinity、createRange(8,Infinity) 凍死瀏覽器（POC 實證）。B-030 首項同一事同批出列；殘餘另立 B-131（>100 列不可達）／B-132（回收桶每頁殘留 100）。
- 2026-08-25｜misc｜B-057 裁決落帳（輕量軌、merge d0bcd2a）：user 親決選候選 (a)——logout 呈遞 rotated 票維持 0000 靜默 no-op、撤銷射程恆為單列不擴 revoke_family，立 ADR 0059 關帳。★落點自條目原寫的 data-model §1 改為 ADR：003 收刀後 specs/ 樹成史料不可改（ADR 0058 決定 3 逐字），依 CLAUDE.md §4「won't-fix／by-design 也立 ADR」。logout.rs 兩處碼註（原記「歸主線裁」）改指 ADR 0059。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
