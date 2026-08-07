---
id: "0013"
title: decrypt passphrase 自動應答（只打一次）之安全姿態
date: 2026-08-07
status: accepted
supersedes: []
superseded_by: []
provenance: "BACKLOG B-036（ADR 0010 轉換批②、grilling 拍板 2026-08-06）；動機＝L-005（寫死互動次數失效）＋2026-08-07 真密文首輪實跑之盲打體感（user 多打一次落 host shell、rev4:L-179 事故面重演邊緣）；實證素材＝maint-b036 首單元端到端與退路對照實測"
tags: [security, tooling, ux]
---

## 背景

`deploy/decrypt-secrets.py` 沿 rev4 姿態逐次手打 passphrase：sops 對每個 recipient 各索
一次，提示行被容器 pty 單流捕進暫存檔、**從不出現在終端**——operator 盲打、次數靠猜。
實測兩条外洩路：打太早／太晚的那次落 host shell（回顯進畫面與 history、rev4:L-179）；
手打的字在 docker 切 raw 前明文回顯 host 終端（U1 ⑦-b 實測可見假 passphrase 全文）。
2026-08-07 真密文首輪（2 recipient）user 實際輸入三次即此事故面的現場樣本。

## 決定

預設改**自動應答**：`getpass` 自 /dev/tty 收 passphrase 恰一次（不回顯）→ `pty.fork` 起
wrapper → 累積流正規化後**偵測到 `Enter passphrase` 才餵**、`fed<hits` 補餵——不預測次數
（L-005）；零提示（無殼 identity）自然直通。`RV5_DECRYPT_MANUAL=1`（嚴格判 `1`）保留
現行逐次手打退路——災難復原路徑不鎖死。

### 兩代價（誠實記帳）

1. **暴露面**：passphrase 從「鍵盤→容器直達」變「經腳本記憶體→寫進 pty」。緩解＝
   bytearray 持有、finally 零填、不進 argv／環境變數／磁碟／log；CPython `getpass` 回傳
   str 的那一份緩衝清不掉＝盡力而為極限、程式註解如實記載。
2. **跨代餵錯**：wrapper 走目錄掛載回退分支時，會把 rev5 passphrase 餵給前代鑰的提示。
   單檔掛載修正（ac00328、L-005）後此情境已不存在；回退分支仍在（目錄掛載＋提示行），
   故記為殘餘理論代價。

### 對向收益（實測）

自動路徑反而**關掉**手打的兩條既有外洩路：pty master 關 ECHO＋回顯守衛（passphrase 現身
任何將倒流內容→整段抑制＋fail-loud），代餵零回顯；「多打一次落 host shell」的操作面
自此消滅（只打一次、無時機判斷）。

## 後果

- 已知誤擋：某支機密值恰等於 passphrase 時回顯守衛會攔下正常解密——實作 docstring
  記載、指路 MANUAL 退路。
- MANUAL 退路保留原有全部風險（盲打、回顯、時機外洩）——手冊在該語境保留警語。
- 逾時／SIGINT 邊界常數寫死於腳本；行為變更之等價驗收＝pty 樁＋加殼測試鑰端到端＋
  真密文人工一輪（記於收刀事件）。
