---
promoted_to: rust-api/server/src/router.rs 組裝次序寫死碼註＋tests/contract.rs 成對載明（走真 build() 的行為測）
---
- **L-024**｜**middleware／fallback 的組裝相對次序是行為、不是風格——次序錯不會編譯紅，
  只會把「誰來答 405」整個換人，且每個錯序各有不同的靜默壞法**：003-auth-session 的
  `router.rs::build` 實證三個失效形——①`method_not_allowed_fallback` 排在 merge **之前**
  ＝它只掃「先前已註冊」的 MethodRouter，之後 merge 進來的 route 全數漏保護、動詞不符回
  框架 405 零長度裸 body（13 碼矩陣外的第三種出口）；②排在 enforce_mw layer **之內**＝
  405 fallback 被 authn 包住、未認證動詞不符先吃 8888，於是「換個動詞」就能探測受保護路徑
  存在性（ADR 0031 零洩漏硬條款破功）；③axum 的 `allow` 標頭是 `RouteFuture` 末段才插
  （在所有 endpoint layer 外側），剝除殼從鏈內側掛 `map_response` 剝不掉、且信封三欄仍
  全等＝**靜默**失效。防法：①這類鏈序用「production 組裝函式的行為測」守（走真 `build()`
  的 contract 案），**不要**只用裸掛合成 router 的反例測——後者釘的是框架語意、production
  次序寫錯時它們恆綠（兩類守門的歸屬勿倒記，router.rs 碼註與 contract.rs 節首成對載明）；
  ②改組裝鏈前先讀「次序寫死」碼註並跑該 contract 案，紅了看是哪一個失效形；③凡「掛在鏈上
  的東西」都問一句「它掃的是掛當下的快照、還是之後的終態」——mnaf 屬前者，一切 layer 屬
  逐 endpoint 施加，兩者對次序的敏感方向相反。
