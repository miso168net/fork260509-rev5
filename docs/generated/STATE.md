<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev5-admin-root
- pins：base-web=0fee6c0｜rust-api=4bbc989

## constitution
- 版本：1.1.0

## 帳面統計
- ADR：11（accepted 11）
- BACKLOG 待辦：37（next：B-040）｜滯後：1
- LESSONS：5 筆（next：L-006）
- events：6 筆（feature_close 1、misc 5）

## 最近事件（尾 3 筆、新在前）
- 2026-08-06｜misc｜bash→python 選擇性轉換評估收束：5-agent workflow 逐檔實查全 repo bash 面 24 支 4164 行＋grilling 19 題逐題拍板；定案＝選擇性轉 5 支（10.3~12 人日 vs 全轉 26.8）、stdlib-only與等價驗收兩硬約束、hooks 全組／bootstrap 等 16 支明文不做、age 產鑰改容器化、外部工具版本三分類政策（一次性輔助工具沿 latest）；產出＝ADR 0010/0011＋B-035~B-039＋B-004/B-005 補記
- 2026-08-06｜misc｜sops wrapper 單檔選鑰修正（輕量軌）：加人致 recipient 1→2 後跨代並存機 decrypt 失效——wrapper 掛整個 ~/.config/sops/age 使容器內存在兩把 identity，sops 遂對「每 recipient× 每鑰」各索一次不可見 passphrase、任一次空答即整體失敗且訊息指向錯方向；改為單檔掛到容器內預設尋鑰路徑、容器內恆恰一把 identity。decrypt 預告行改自密文現算 recipient 數、不再寫死「恰 1 次」；RUNBOOK 四節與 generate-age-key.sh 訊息同步；L-005 入帳
- 2026-08-06｜misc｜創世收官（B8b＋B11）：移植驗收後段全過——bootstrap 幂等零改動＋生成檔八檔全刪逐位元重算＋假 feature 以 001 真刀充抵＋router／msg_dict 兩表拔項突變實證；K1／K2 處置流水總帳 ADR 0009 accepted——K1 改隨刀重審機制、K2 二十二筆三分流（15 轉 BACKLOG／2 拍板待答／5 創世期已兌現）＋樣板回灌帳 B-033 開立；創世 DoD 全數關帳

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
