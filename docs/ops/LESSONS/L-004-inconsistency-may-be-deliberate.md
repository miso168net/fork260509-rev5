---
promoted_to: deploy/secrets_common.py 檔頭「動它之前先查由來」註＋deploy/setup-reaper-role.py 之「①由來（先查再動）」註（移植品怪寫法動手前先查由來）
---
- **L-004**｜移植品的「不一致」可能是前代刻意的防禦性慣例——動叫用形／預設值／樣式前，先查
  前代教訓帳與該處的 rev4 對應寫法，**repo 內部一致性不足以構成修改理由**。
  親歷：RUNBOOK／README 對五支 deploy 腳本混用 `bash deploy/x.sh` 與 `./deploy/x.sh`，我僅憑
  `tools/docs-sync.py` 之 EXEC_BIT_ROSTER 註解稱該五支為「直跑形」，就把 8 處 `bash` 前綴一律
  改成直跑形。user 指出前綴有前代來由後回查：①rev4 是**刻意混用**——其 RUNBOOK 同一張工具表
  內 `./deploy/sops.sh` 與 `bash deploy/decrypt-secrets.sh` 並存；真正的慣例是「docs 面用 `bash`
  前綴／腳本自身用法行與 `deploy/secrets/README.md` 用 `./` 形」②`bash` 前綴的防禦價值有二：
  可在前面掛環境變數（rev4:L-142 的定案指令＝`LC_ALL=C PYTHONUTF8=1 bash tools/bootstrap`，
  macOS bash 3.2 全形字邊界問題所需）、以及 index exec bit 若為 100644 時 `./x.sh` 會
  Permission denied 而 `bash x.sh` 恆可跑（rev4:B-116；drvfs 上 `ls` 恆顯 0777 看不出 index 真值）。
  ★即使 rev5 有 Lint21／EXEC_BIT_ROSTER 保證 100755 使直跑形安全，該慣例仍不該由 agent 以
  一致性為由單方抹平。
  防法：改**移植品**的既有寫法前，先跑「rev4 對應檔怎麼寫」與「教訓帳有無此主題」兩查；
  兩查皆無來由才動，有來由則升級為拍板題問 user。已回退 21 處。

