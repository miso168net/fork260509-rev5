---
id: "0031"
title: 動詞不符回 4040＋HTTP 404——B-047 兩候選取①，正面處置「13 碼矩陣無動詞不符語意」的張力
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 T003③／T014／FR-024；處置對象＝BACKLOG B-047（條目自書「兩候選皆屬拍板級」）；axum 組裝次序實證＝research R1"
tags: [wire, error-code, router, axum, backlog-disposition]
---

## 背景

B-047 記錄的事實：已註冊路徑收到未宣告動詞時，axum `MethodRouter` 回**框架預設 405＋零長度裸 body**
（`allow` 標頭正確、`content-length: 0`、無 `data`／`code`／`msg`），是憲法 §I.3「envelope universal
例外僅 2」（`/health` 與 `/metrics`）之外的**第三種非信封形**。pre-existing、非某一刀引入。

該條目自己寫下了處置的難處，值得逐字正視：

> 需先拍該情境用哪個碼——**13 碼矩陣現無「動詞不符」語意的碼、硬塞 2222 或 4040 皆有語意張力**，
> 屬拍板級。

兩個候選：①掛 `method_not_allowed_fallback` 回 13 碼信封（要選碼）②維持現狀、在憲法 §I.3 例外集
明文加註「405 為框架層、非應用層信封面」。

## 決定

**取候選①，碼＝`4040`（`system.notFound`），HTTP status＝404。**

四條理由，逐條回應 B-047 自書的張力：

1. **可行動性一致**：對 client 而言，「這條路徑不接受這個動詞」與「這個資源不存在」導出的下一步是同一
   件事——不要用同一組合重試。`4040` 的既有語意涵蓋得住，不是硬塞。
2. **status 一致性零成本**：`4040` 已是 13 碼矩陣中**唯一**映射 HTTP 404 的碼（§I.3 明列的兩個 status
   例外之一）。掛在動詞不符上，信封 code 與 HTTP status 天然一致，不需為此新增任何例外。
3. **`2222` 會污染業務碼語意**：`2222`＝業務驗證錯誤（§I.3 明文「業務驗證 error code＝2222」）。動詞
   不符是**路由層事實**、不是任何業務規則被違反；塞 `2222` 會讓「業務驗證失敗」這個語意從此不可靠。
4. **新增碼的代價遠大於收益**：§I.3 明文「13 碼矩陣**整組凍結**」，加第 14 碼＝§V.3 的 MAJOR
   （鐵紀律改變）。為一個 client 行為與 404 完全相同的情境付 MAJOR，不划算。

**★零存在性洩漏（本 ADR 的硬條款）**：未認證與已認證的動詞不符 MUST 回**同碼同 status**。若未認證時
先被 authn 層攔成 `8888`、已認證才得 `4040`，攻擊者即可用「換一個動詞」探測路徑是否存在。這要求
`method_not_allowed_fallback` 在組裝鏈上排在 `enforce_mw` layer **之後**（research R1 已實證組裝次序
決定 405 歸屬），且該次序須有反例測試釘住。

## 後果

- **憲法 §I.3 不需改**：405 自此不再出現在應用層，「envelope universal 例外僅 2」回復為真陳述。
  候選②原本要在憲法例外集加註，本決定使該加註不必要——這是取①而非②的附帶收益。
- **B-047 關帳**：走本刀收刀事件，不另立 won't-fix ADR。
- **組裝次序成為 load-bearing 事實**：`route 註冊 → 各子 router enforce_mw layer → merge →
  .fallback() → .method_not_allowed_fallback() → 最外側 metric layer`。次序錯了不會編譯紅、只會行為
  錯，故 T014 要求兩條反例測試（①mnaf 後才 merge 進來的 route 回框架 405 ②mnaf 排在 layer 前則未認證
  動詞不符變 8888）。碼註同時釘在 `router.rs` 與 `contract.rs`。
- **動詞探測閘 MUST 永遠裸掛 router**：改走共用 `build()` 即恆綠（L-010 形的 vacuous 陷阱）——測試若
  經由與 production 相同的組裝函式取得 router，就驗不到組裝次序本身。
- 已知殘留：`405` 仍可能由 front-nginx 或更外層基建回出，那不在應用層信封面內、與本 ADR 無涉。
