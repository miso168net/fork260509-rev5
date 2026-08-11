---
id: "0032"
title: root Cargo.toml「不引 argon2」翻案——引入六支 auth 依賴，後六支續留域外
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 T003④／T004；被翻案的拍板住在 rust-api/Cargo.toml:12 碼註（002-system-settings clarify Q1）與 rust-api/server/Cargo.toml:3-4 之不進清單，無 ADR 承載故 supersedes 留空；版本雙源核對＝research R4（CLAUDE.md §6）"
tags: [rust-api, dependency, version-pinning, decision-reversal]
---

## 背景

兩處碼註承載了同一個拍板：

- `rust-api/Cargo.toml:12`：`# ★不引 argon2（clarify Q1 拍板：seed password＝PHC 定稿常數、無 runtime 雜湊）`
- `rust-api/server/Cargo.toml:3-4`：`# rev4 有而 B12 域外者不進（jsonwebtoken／redis／argon2／captcha／sha2／hex／lettre／toml／arc-swap／once_cell／futures-util／xdb——R1 明確不進清單）`

該拍板的**前提**寫得很清楚：002-system-settings 沒有 runtime 密碼驗證，seed 的 password 只是一個
PHC 定稿常數字串，沒有任何程式碼需要去驗它。前提成立時，結論正確。

003-auth-session 讓這個前提消滅：真登入必須在 runtime 以 argon2 拿使用者送來的密碼去驗 seed 的 PHC。
連帶地，簽發與驗章要 `jsonwebtoken`、denylist 與節流要 `redis`、圖形驗證碼要 `captcha`、token hash 與
答案 MAC 要 `sha2`＋`hex`。

## 決定

1. **引入六支**（版本三段全釘，雙源核對見 research R4）：
   `argon2 0.5.3`／`captcha 1.0.0`／`hex 0.4.3`／`jsonwebtoken 10.4.0`／`redis 1.3.0`／`sha2 0.10.9`。
2. **★`jsonwebtoken` MUST `default-features = false` ＋ 顯式開 `rust_crypto` feature**。漏開不是編譯
   紅，是**decode 在執行期 panic**——這類「編譯過、跑才炸」的 feature 陷阱必須在 manifest 上釘死，
   不能靠記憶。
3. **`redis` 開 `connection-manager` ＋ `tokio-comp`**（連線管理器與 tokio runtime 橋接）。
4. **後六支續留域外**：`lettre`／`toml`／`arc-swap`／`once_cell`／`futures-util`／`xdb` 仍不進——
   它們的前提（郵件、外部設定檔、熱替換、IP 庫）本刀一個都沒成立。`server/Cargo.toml` 的不進清單
   同批改寫為只列這六支。
5. **三處舊拍板註解同批改寫**（T004）：root 檔頭「不引 argon2」／`server/Cargo.toml` 不進清單／
   `state.rs` 恰兩欄封條（後者屬 ADR 0029 射程，此處僅記其同批性）。

## 後果

- 拍板的**判準不變、結論隨前提翻轉**：「域外者不進」這條紀律本身完好，翻的是「argon2 屬域外」這個
  隨刀變動的事實。日後任一支要進，同樣看前提是否成立，不看清單本身。
- `Cargo.lock` 套件數估 `441 → 約 484`，成長記入 T004 的 commit message（依 CLAUDE.md §6 版本紀律：
  裝了什麼、版本多少，要能事後查）。
- **供應鏈面誠實揭露**：`captcha 1.0.0` 是本刀唯一一支非廣泛使用的依賴，且其 crate 名與 rev5 的
  `crate::captcha` 模組**同名**（消歧規則見 T052／research R3-1）。選它而非自繪的理由是內嵌字型與
  失真管線現成；代價是字元集受其內嵌字型 glyph 涵蓋限制（`0`／`o` 無 glyph 會靜默產廢題，故字元集
  收為 34 字並配字型涵蓋測試）。
- 六支全部進 `workspace.dependencies` 單一版本來源，`server/Cargo.toml` 只寫 `{ workspace = true }`
  ＋feature，維持既有的版本單一來源紀律。
