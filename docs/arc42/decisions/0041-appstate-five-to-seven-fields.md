---
id: "0041"
title: AppState 由恰五欄擴為恰七欄（信任模型＋規則判定面）——翻案 ADR 0029 之五欄封條
date: 2026-08-15
status: accepted
supersedes: ["0029"]
superseded_by: []
provenance: "004-ip-trust-anchor 之 T003①（tasks.md Phase 1 主線任務）；觸發＝ADR 0029 封條逐字要求『要開第六欄＝拍板級翻案（新 ADR），不得逕加』，本刀即該翻案。★T003 於 tasks 字面為一支 ADR，實作期依 CLAUDE.md §4「一決策一檔」拆為本檔與 0042 兩支——兩者各自 supersede 不同舊檔（0029／0039），併檔會使 supersedes 圖語意糊掉"
tags: [rust-api, state, architecture, ip-gate]
---

## 背景

`rust-api/server/src/state.rs` 的檔頭封條（ADR 0029、003-auth-session 落地）逐字釘死：

> ★★恰五欄是拍板釘死的邊界（ADR 0029，翻案 002 時代的恰兩欄封條）：003-auth-session
> 開 `jwt`／`cache`／`captcha_secret` 三欄（T006 落地）；rev4:AppState 其餘那串
> `ip_rules`／`trust_model`／`mailer` 仍不搬——各屬 IP 存取閘刀與郵件刀的域、其前提
> 本刀一個都沒成立。要開第六欄＝拍板級翻案（新 ADR），不得逕加。

004-ip-trust-anchor 使該串裡的**前兩項前提成立**：

- `trust_model`：信任錨判定為純函式，但其六個網段集合須於 boot 一次載入後**唯讀共享**給每個
  請求（middleware 每請求取用）。放在 `AppState` 之外即需另建一條共享通道。
- `ip_rules`：IP 存取閘的判定面 MUST 每請求**零資料庫零快取查詢**（島 F 之 F2），故須為
  記憶體內可熱換版的共享值；`Arc<ArcSwap<RuleSet>>` 的 `.load()` 為 lock-free 讀。

`mailer` 的前提**仍未成立**（rev5 無郵件域），續留域外。

## 決定

1. `AppState` 由**恰五欄**擴為**恰七欄**，新增兩欄：
   - `trust_model: Arc<TrustModel>`——boot 一次載入、建好即不可變。
   - `ip_rules: Arc<ArcSwap<RuleSet>>`——判定面，寫端經 `reload_and_publish` 換版、
     讀端每請求 `.load()`。
2. `state.rs` 檔頭封條註解**改寫**為「恰七欄」，並**保留** `mailer` 續留域外的邊界說明
   不得整段刪除——封條的價值在「下一次開欄仍須拍板」這條規則本身，把說明整段刪掉等於
   把規則一併刪掉。改寫後的封條須續載「要開第八欄＝拍板級翻案（新 ADR），不得逕加」。
3. `AppState` 廉價 clone 的前提**不因本次擴欄而破**：兩個新欄皆為 `Arc` 包覆，clone 只複製
   指標，與既有五欄（連線池句柄／`Arc<RwLock<Enforcer>>`／小型不可變值）同性質。
4. 分級＝**翻案**（依 §4「決策翻案立新 ADR」），轉 accepted 時 `supersedes: ["0029"]`。
   ★本檔**不動** ADR 0029 對 `jwt`／`cache`／`captcha_secret` 三欄的既有論述（含 `cache`
   之 `Option` 語意非「可有可無」的降級鏈論證）——那些論述隨 0029 轉 superseded 後仍是
   `state.rs` 欄級註解的出處，本檔只翻「恰五欄」這一條邊界。

## 後果

- **窮舉式 struct literal 五處必須同步**（加欄即編譯不過、`..Default` 一處都沒有）。
  清單來源＝`grep -rn "AppState {" rust-api/server/`（2026-08-14 實測），排除 `state.rs` 的
  struct 定義本體與三處 `-> AppState {` 函式簽名後得**六處 literal**，其中 `main.rs:77` 的
  boot 建構屬擴欄本體、其餘五處為散布點：
  `router.rs:431`（`mod tests::stub_state`）／`auth/enforce.rs:365`（`mod tests::state_with`）／
  `model/mod.rs:417`（`test_db::real_app_with`）／`throttle/mod.rs:604`（`mod tests::throttle_app`）／
  `tests/common/mod.rs:77`（`stub_state`）。
  ★`handler/system_settings.rs` 之 `real_app()` **不在此列**——B-054 收攏後已是零建構薄轉呼。
- **新依賴 `arc-swap` 因本決定進場**（釘版與三源核對見 004 research R3；ADR 之外的依賴紀律
  沿 CLAUDE.md §6）。
- 擴欄本身**不改變任何既有欄的語意**；既有 321 支測試與 16 case contract 測應僅因 literal
  補欄而變動，行為面零回歸——此即本決定的驗收面。
- 下一個想開第八欄者（`mailer` 或其他）仍須走拍板級翻案；封條規則自此指向本檔。
