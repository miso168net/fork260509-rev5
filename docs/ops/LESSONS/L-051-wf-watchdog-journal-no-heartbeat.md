---
promoted_to: CLAUDE.md §2（「完成通知一到→TaskStop 該 Monitor（防誤觸 stall）」既有句＝防法本體；本條補殘因與閾值語意）
---
- **L-051**｜**wf-watchdog 的 stall 判定源（workflow journal）沒有心跳——它只在 agent 邊界寫入**：防法前置——①完成通知一到立即 TaskStop 該 Monitor（run 結束後 journal 永不再動、掛著必然誤報 stall；CLAUDE.md §2 既有句）；②調 stall 閾值時記住其語意＝「**agent 邊界間隔**上限」而非「無活動時間」——單支長跑 agent（implementer 動輒 >1000s）期間 journal 零新行是健康態，閾值壓太低＝健康長跑被誤殺；③要真心跳得另闢訊號源（agent transcript 檔 mtime 隨工具呼叫更新），非 journal 所能。實暴＝005-role-menu-crud 執行期（2026-08-18~19）兩次 stall 假警報：皆為 run 已完成、Monitor 未 TaskStop，~13 分鐘後誤觸——journal 靜止在 watchdog 眼裡與「卡死」不可分。盲點屬結構性：journal 是結果帳（一 agent 一列）不是活動流；watchdog 於單元執行中能分辨「慢」與「死」的唯一憑據是閾值放寬，誤殺與漏報的取捨繫於此。
