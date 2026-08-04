<!-- next: L-002 -->
# LESSONS — 教訓 registry

一教訓一段（`L-NNN｜坑＋防法`）、append-only；配號取檔頭 next-id 後 bump、號碼永不回收。
rev5 自空白起家、只記親歷坑；前代教訓為候選承襲清單（docs/brainstorms/000-doc-architecture.md §5 K3）、撞到對應域時挑選引用、不整批搬入。

L-001｜macOS bash 3.2 全形字黏變數名：`"$VAR全形字"` 在 UTF-8 locale 下會把全形字首位元組黏進變數名，`set -u` 直接炸 unbound variable（首暴＝preflight-secrets.sh 末行、B5b 移植期；且**選擇性觸發**——同檔他處同形卻沒炸，繫於後接字元的位元組值，不能靠「跑過一次沒事」排除）。rev4 全代在 WSL2 bash 5 從未暴露＝跨平台移植必掃。防法：①`$VAR` 後緊接非 ASCII 一律 `${VAR}` 包裹；②機器枚舉全 repo bash 面（regex `(?<!\\)\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])`、排除註解與 `\$` 轉義）逐處處置、絕不只修被咬那行（本次 6 檔 21 處一鍋改）；③新寫告警／訊息分支先空跑一次。
