# BACKLOG-DEFERRED — 滯後卷

條目格式同主檔 `BACKLOG.md`；本卷收 user 拍板滯後的待辦——不排入 NOTES 近期 roadmap、STATE
分開計數（**滯後≠完成**、lint 一律視為仍開放）。配號永遠只在主檔（本卷無 next-id）；移入／移回
＝整行搬＋滯後戳記；完成＝照舊刪列＋事件 `backlog_done`；各條目觸發欄寫回收時點。

- B-034｜`alert_webhook_url` 填真值＋回寫密文（現值＝公開佔位字面 `https://CHANGE-ME.invalid/…`、經 ADR 0003 列入 secret-value-guard 白名單故不擋 commit；填真值後自動納回值比對；連動＝`deploy/secrets.dev.enc.yaml` 重加密、RUNBOOK §15 機密營運流程）｜起 observability 軌前（grafana 告警投遞實測時）｜★滯後 2026-08-06 user 拍板：創世收官時**直接立於滯後卷、未曾入主檔**——真值需人工提供且 obs 軌未排程，觸發權不在近期 roadmap 內
