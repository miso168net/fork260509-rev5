---
promoted_to: CLAUDE.md §2（看門狗段補「launch 被擋後重發必帶 runId」半句、2026-08-21）
---
- **L-049**｜**Workflow launch 被 hook 擋下後，同回合已發射的無目標看門狗會鎖上一支舊 wf 目錄**：防法前置——①launch 失敗（hook 擋、參數錯）而看門狗已 armed 時，一律 TaskStop 該看門狗、重發 Workflow 後**帶明確 runId 重掛**，絕不沿用「自動發現最新目錄」的舊 Monitor；②判讀訊號＝ARMED 行的冒煙 token 命中數——命中=0 且 run 目錄名非本次＝鎖錯標的；③「原子成對同回合發射」防的是漏掛，防不了「成對的另一半死了」——半邊失敗即整對重來。實暴＝005-role-menu-crud U10 發射（2026-08-21）：Workflow 被 pre-workflow hook 以相對路徑擋下（工作目錄殘留子庫），同回合並發的看門狗照常啟動、自動發現到的「最新 wf 目錄」是上一單元 U9c 的舊 run——冒煙命中=0、且該目錄已完結永無新事件，~780s 後必誤報 stall，而重發後的真 run 零監控。徵狀在 ARMED 首行即可辨（run id 不對＋命中=0），當場攔下。出處＝本 session 實暴、立即改帶 runId 重掛後命中=1。
