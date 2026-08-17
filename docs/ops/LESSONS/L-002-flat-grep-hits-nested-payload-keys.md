---
promoted_to: tools/wf-watchdog.py 之「頂層鍵定錨」實作與註（逐行 JSON 解析、只取事件物件 top-level key）
---
L-002｜watchdog 扁平 grep 抽 journal key 撞巢狀 payload 同名鍵：wf-watchdog 以 `grep -oE '"key":…'` 數不重複 agent key，但 workflow journal 的 result 事件內嵌 agent 回傳 JSON——回傳結構帶同名欄（本例 coverage[].key＝"FR-001"…22 筆）即被一併計入，實證 9 支真 agent 被數成 31 → RUNAWAY 誤報、健康工作流被 TaskStop（001 刀 speckit-analyze 首撞、2026-08-05）。防法：①判準抽取一律**頂層鍵定錨**（逐行 JSON 解析、只取事件物件 top-level 欄），絕不對含任意巢狀 payload 的 jsonl 做扁平 regex 計數；②既有「journal 非空卻抽到 0 key＝fail-loud」健全性檢查保留（頂層定錨後它兼任格式漂移哨）；③workflow 回傳 schema 欄名迴避框架頂層語意名（key/type/agentId）屬縱深防禦、非根治。修復自證＝真 journal 舊法 31/新法 9＋合成巢狀鍵 journal 抽 0 觸發健全性告警。

