---
promoted_to: deploy/decrypt-secrets.py（檔頭註明「勿假設恰跳 1 次」＋自動應答令提示次數與基數脫鉤）
---
- **L-005**｜以**當時基數**寫死的互動預期（「恰跳 1 次 passphrase 提示」），會在基數變動的
  當天失效——而該工具的失敗訊息指向錯方向，operator 只能誤判成「我的鑰匙壞了」。
  親歷：RUNBOOK §15.2 首次真實加人（recipient 1→2）當日，跨代並存機（本機另存前代 age 私鑰
  於 sops **預設**尋鑰路徑 `keys.txt`）跑 `decrypt-secrets.sh`：wrapper 唯讀掛載**整個**
  `~/.config/sops/age` 目錄 → 容器內兩把 identity → sops 對「每個 recipient × 每把鑰」各索
  一次 passphrase（本例 3 次），而提示與資料同流被暫存檔捕捉、畫面上**一次都看不到**
  （rev4:P1.2／rev4:L-168 之連帶）。operator 只答了第一次、其餘空答，sops 回
  `passphrase can't be empty` 並附一長串「找不到金鑰於 SOPS_AGE_*」——讀起來像鑰匙或加人
  有問題，真因只是「提示不只一次」。腳本檔頭那句「恰跳 1 次（單 recipient 基線）」正是
  誤導的來源：它把一個**隨資料變動的量**寫成了常數，且沒有任何機器會在基數變動時喊它過期。
  防法：①凡「次數／數量」類的互動預期，一律由腳本**自資料現算**後印在預告行，不落字面
  （本次＝自密文數 `recipient:` 行）；②把不可見互動的**面積收斂到最小**——容器內 identity
  收斂成恰一把（單檔掛到預設尋鑰路徑），而非把整個金鑰目錄攤進去，面積即提示次數的乘數；
  ③失敗訊息的**判準**寫進手冊（`Group 0` 的 recipient 清單看加人完沒完、`passphrase can't
  be empty` 看提示有沒有漏答），別讓 operator 從工具的「找不到金鑰」清單反推。
  ★連帶承認：`WARN … didn't match file's recipients` 在多 recipient 下是**正常過程訊息**
  （試到不是你那把的 recipient 時必然出現），單看它會把人帶往錯的方向。

