---
promoted_to: 無：候選位＝bash 面機器閘（docs-sync.py 新條款：`$VAR` 後緊接非 ASCII 即紅、regex 見本條防法②）不在本單元允許面、待下一把動 docs-sync 的刀；★2026-08-30 B-091 盤點以本條 regex 重掃 bash 面得 4 行 7 處復發命中（.githooks/pre-commit 1 行、.githooks-submodule/pre-commit 1 行、deploy/generate-age-key.sh 2 行）＝防法未被任何面守住、已升級主線；★2026-08-31 主線直修該 4 行 7 處（改 `${VAR}` 括號形：.githooks/pre-commit、.githooks-submodule/pre-commit、deploy/generate-age-key.sh）；機器閘仍待、由 BACKLOG B-152 承載
---
L-001｜macOS bash 3.2 全形字黏變數名：`"$VAR全形字"` 在 UTF-8 locale 下會把全形字首位元組黏進變數名，`set -u` 直接炸 unbound variable（首暴＝preflight-secrets.sh 末行、B5b 移植期；且**選擇性觸發**——同檔他處同形卻沒炸，繫於後接字元的位元組值，不能靠「跑過一次沒事」排除）。rev4 全代在 WSL2 bash 5 從未暴露＝跨平台移植必掃。防法：①`$VAR` 後緊接非 ASCII 一律 `${VAR}` 包裹；②機器枚舉全 repo bash 面（regex `(?<!\\)\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])`、排除註解與 `\$` 轉義）逐處處置、絕不只修被咬那行（本次 6 檔 21 處一鍋改）；③新寫告警／訊息分支先空跑一次。

