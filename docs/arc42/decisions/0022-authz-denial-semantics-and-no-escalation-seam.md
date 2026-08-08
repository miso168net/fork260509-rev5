---
id: "0022"
title: 授權拒絕語意與 no-escalation seam 定形——5003＋純 i18n key 起步、掛點簽章預留 async 與 db
date: 2026-08-08
status: accepted
supersedes: []
superseded_by: []
provenance: "002-system-settings spec FR-013／FR-014（「拒絕語意與錯誤明細粒度 MUST 以刀內 ADR 定死」）＋tasks T025；user 拍板 2026-08-08（三題全採推薦案，於 U1 執行期間預先定案）；背景＝BACKLOG B-024 三件套之前置、casbin seed 現況必然發生的「R_ADMIN 有 user:edit 鈕、無設定域政策」組合"
tags: [authz, wire, seam, security]
---

## 背景

casbin seed 現況保證一個組合必然發生：R_ADMIN 持有 `user:edit` 按鈕（政策列 44），卻對設定域
零政策——它打寫端一定會被拒。spec FR-014 明定這個拒絕的語意與錯誤明細粒度必須以刀內 ADR
定死，否則「第一支寫端落地即隱含定死」全 repo 的授權拒絕行為，等於默拍。

同時 spec FR-013 要求授權判定收斂於單一純函式進入點，並留一個空的 no-escalation 掛點
（B-024 seam、本刀不實作其邏輯）。掛點只留名字很容易，難的是留對「形」——B-024 的真邏輯是
「不得授予超出自身權限的角色」，那幾乎確定要查庫（查操作者現有角色、查目標角色）。若現在
把掛點定成同步、不帶連線的最小簽章，B-024 接手時必然要改簽章與所有呼叫端，這個 seam 就只
預留了名字、沒預留形。

## 決定

1. **拒絕碼**＝`5003`＋HTTP 403（轉錄 spec FR-019 碼表，非新決策）。

2. **錯誤明細粒度＝Biz 純 i18n key 形起步**。回包恰為
   `{data: null, code: "5003", msg: "system.forbidden"}`——不揭露缺哪一條政策、不揭露操作者
   持有哪些角色。理由三條：①向確定無權者描述授權模型，等於送他一張權限地圖；②`AppError`
   已有 `BizData` 變體形可供日後擴充，現在不做不是單程門；③B-024 條目本文既已排入「業務錯誤
   明細通道受眾邊界重評」，起步用純 key、受眾邊界一次拍歸 B-024，兩者一致。

   **後果**：前端現階段只能顯示通用拒絕語，無法引導使用者「去找誰開權限」。這個缺口是刻意
   的，解法歸 B-024 的受眾邊界重評。

3. **no-escalation 掛點形定死**：

   ```rust
   /// B-024 seam：不得授予超出自身權限之角色的上限檢查。
   /// 本刀恆放行（空掛點）；真邏輯由 B-024 填充。
   pub(crate) async fn no_escalation_check(
       _db: &DatabaseConnection,
       _actor_uid: i64,
       _path: &str,
       _method: &str,
   ) -> Result<(), AppError> {
       Ok(())
   }
   ```

   ★簽章刻意預留 `async` 與 `&DatabaseConnection`：B-024 接手時零簽章變更、零呼叫端改動，
   這才兌現 spec FR-013 的「auth 刀接真 session 時判定進入點介面不變」。四個參數於本刀內
   全數未用，以 `_` 前綴標記並在註解說明係 seam 預留——★此為拍板結果，不得被 review 報為
   死參數。呼叫位置＝enforce 判定進入點的**唯一**呼叫（判定收斂於單一純函式進入點＝FR-013）。

4. **掛點的可觀察形＝`#[cfg(test)]` 旗標覆寫**：

   ```rust
   pub(crate) async fn no_escalation_check(...) -> Result<(), AppError> {
       #[cfg(test)]
       if NO_ESCALATION_FORCE_DENY.with(|f| f.get()) {
           return Err(AppError::PermissionDenied);
       }
       Ok(())
   }
   ```

   T026 的授權矩陣據此驗「掛點確實在判定鏈上、不是裝飾」——把旗標掰開，請求必須真的被 5003
   擋下。選此形而非參數注入或源碼掃描的理由：生產建置編譯期即剔除該段；`AppState` 維持
   data-model §5 釘死的「恰兩欄」不必為測試開第三欄；enforce 進入點的簽章不受影響。
   ★`#[cfg(test)]` 必須是獨立一行的標準形——`tools/docs-sync.py` 的 `rs_production_lines`
   對 `cfg(all(test,…))` 與同行屬性形一律 fail-loud（Lint24 掃描面的圈界保證）。

## 後果

- B12 的授權面自首刀起即以真實組合驗證：R_SUPER 讀寫皆 `0000`、R_ADMIN 讀寫皆 `5003`、
  未攜標頭 `8888`（SC-004）。
- B-024 接手時只需把 `Ok(())` 換成真邏輯，簽章、呼叫端、判定鏈位置皆不動。
- 掛點的 metrics 面：`casbin_enforce_total` 的 `decision` 取值恰三（allow／deny／error），
  掛點拒絕併入 `deny`——兩者對外都是 5003、受眾與處置相同。
- 若日後判定「純 i18n key 太粗、前端需要可操作的引導」，翻案＝B-024 的受眾邊界重評出結論後
  立新 ADR supersede 本檔第 2 款；掛點形（第 3、4 款）不受影響。
- 一筆已知的施工註記交棒 B-024：`require_policy` 目前在**持有 enforcer 讀鎖的臨界區內**
  await 本掛點。本刀掛點恆 `Ok(())` ＝零成本無實害，但 B-024 填入查庫邏輯後，每次受保護請求
  都會在讀鎖內多一趟 DB round-trip——屆時應把掛點呼叫移到取讀鎖之前（進入點內的順序與唯一
  呼叫點語意不變，只縮 `require_policy` 的鎖範圍）。
