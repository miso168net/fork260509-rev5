<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0fee6c0｜rust-api=4bbc989

## constitution
- 版本：1.1.0

## 帳面統計
- ADR：12（accepted 12）
- BACKLOG 待辦：37（next：B-040）｜滯後：1
- LESSONS：6 筆（next：L-007）
- events：8 筆（feature_close 1、misc 7）

## 最近事件（尾 3 筆、新在前）
- 2026-08-07｜misc｜Lint25 跨代裸編號閘上線（ADR 0012 決定 7；B-004 防復發面）：19 族樣式單 pass＋registry 掃源現算＋防恆綠自測＋具名豁免七類；day1 降級 WARN、清償完轉 ERROR；bootstrap 名冊斷言改「末筆 lint-roster 勝」（append-only 帳的條款入冊通道＝append 新事件、絕不改創世列）；本筆即新名冊承載事件
- 2026-08-07｜misc｜前代裸編號全樹審計收束＋七題拍板：6-agent workflow 逐筆判定 881 筆（機械 740 零缺口＋人工補掃 141）——foreign 621／68 檔、gray 93 歸邊；撞號已實發（nginx 裸 B-037 對撞 rev5 已配號 B-037）、近兩 commit 新引入 7 筆＝防復發必要性實證；拍板＝血緣前綴 rev4:/rev3:/rev2:、裸刀號只加前綴、逐 token 合規、fixture 遷假號段、LESSONS 勘誤級可修／events 不動、已收刀 spec 限前綴化可動、Lint25 與清償同刀；產出＝ADR 0012＋B-004 射程改寫
- 2026-08-06｜misc｜bash→python 選擇性轉換評估收束：5-agent workflow 逐檔實查全 repo bash 面 24 支 4164 行＋grilling 19 題逐題拍板；定案＝選擇性轉 5 支（10.3~12 人日 vs 全轉 26.8）、stdlib-only與等價驗收兩硬約束、hooks 全組／bootstrap 等 16 支明文不做、age 產鑰改容器化、外部工具版本三分類政策（一次性輔助工具沿 latest）；產出＝ADR 0010/0011＋B-035~B-039＋B-004/B-005 補記

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
