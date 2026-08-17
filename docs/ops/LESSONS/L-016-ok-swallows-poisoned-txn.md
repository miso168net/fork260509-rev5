---
promoted_to: rust-api/server/src/handler/auth/login.rs 之 find_by_key 兩腿分開碼註（L-016 全 repo 版）；refresh.rs 已改 commit 後交易外讀（結構性免疫）
---
- **L-016**｜**`.ok()` 吞掉的可能是「交易已被毒化」那一腿，而 PG 會把其後的 COMMIT 靜默降級成
  ROLLBACK 卻回 `Ok`**：003-auth-session U-J 的 `handler/auth/refresh.rs` 之 `detect_reuse`
  原本在 txn 內以 `jwt::ttl_from_settings(&txn).await.ok()` 讀 denylist TTL——該函式的 `Err`
  有兩腿，而回傳型別把它們壓成同一個 `AppError::Internal`：①設定列缺失／值不可 parse＝純判斷、
  交易乾淨（`.ok()` 吞它完全正確，正是當時註解寫的那個情境）；②`system_settings::find_by_key`
  查庫失敗＝SQL 已送出且失敗、交易被 PG 推入 aborted 態。吞掉②之後，其後的 `txn.commit()` 會
  被 PG 回以命令標籤 `ROLLBACK`（不是 ErrorResponse），而 sqlx／sea-orm 不檢查命令標籤 ⇒
  `commit()` 回 `Ok(())` ⇒ `revoke_family`（全鏈→revoked）與 `session_event(reuse)` 兩筆一起
  蒸發、denylist 亦未寫，handler 卻照常回 `8888`：**疑似被盜的整條 token 家族原封不動存活、
  可無限重放，稽核面零紀錄**（fail-open，與憲法 §I.7 島 C 相反）。★真正的教訓不是這個機制
  ——`handler/auth/login.rs` 步驟⑩早已用一整段註解把它寫死在案，並據以刻意**不吞**
  `record_attempt` 的錯——而是**那段註解只住在 login.rs、沒有跨檔傳遞**：同一把刀、同一個
  crate、隔四個檔，同一個坑再踩一次，且四輪 code review 才抓到。防法：①凡在 txn 內呼叫
  「回傳型別會把查庫失敗與純判斷失敗壓成同一個錯」的函式，一律**不得 `.ok()`**——要嘛 `?`
  出去 fail-loud，要嘛把該呼叫移到 commit **之後**、走交易外連線（結構性免疫，不靠註解自律）；
  ②寫出這類註解的當下就 append 一條 LESSONS——**檔內註解是給改那個檔的人看的，LESSONS 才是
  給全 repo 看的**；③判準是問「這個 `.ok()` 吞得到的**最壞**那一腿是什麼」，不是「它通常吞到
  什麼」。
