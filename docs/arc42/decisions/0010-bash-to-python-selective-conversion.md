---
id: "0010"
title: bash→python 選擇性轉換範圍總帳（轉換集 5 支＋不做集 16 支＋兩硬約束）
date: 2026-08-06
status: accepted
supersedes: []
superseded_by: []
provenance: "評估＝5-agent workflow 逐檔實查（全 repo bash 面 24 支 4164 行、142 次工具調用）＋grilling 19 題逐題 user 拍板（2026-08-06）；動機源頭＝decrypt-secrets.sh 加人日互動失效（L-005）暴露之移植品三病：bash 解析力不足、rev4 考古註解、零測試治理"
tags: [tooling, governance, tech-debt]
---

## 背景

deploy／tools／hooks 面腳本多為 rev4 原樣移植，`deploy/decrypt-secrets.sh` 於首次真實
加人日（recipient 1→2）暴露互動失效後，user 提出「全部 bash 改寫 python」評估需求。
逐檔實查結果：全 repo bash 面 24 支 4164 行，其中 `.specify/` vendored 佔 2412 行（58%）；
選擇性轉換 10.3～12.0 人日 vs 全轉約 26.8 人日——多出的 16.5 人日買到零功能增益與數項
新風險（vendored drift、hooks 防線裸奔期、bootstrap 共模失效）。

## 決定

### 一、轉換集（5 支、依批次序執行；承載＝BACKLOG B-035～B-037＋B-005 併刀項）

| 批序 | 檔 | 核心收益 |
|---|---|---|
| ① B-035 | preflight-secrets＋decrypt-secrets＋落點共用庫 | 真 YAML 解析（`sops -d --output-type json`）整段刪非裸量純量斷言；共用庫自 secret-value-guard 既有已測實作提出、消費者限三支；test 子命令入自測治理 |
| ② B-036 | decrypt「passphrase 只打一次」互動改動 | UX 主訴求；與①分刀＝失效可歸因；刀內立安全姿態 ADR |
| ③ B-037 | generate-secrets＋setup-reaper-role | 共用庫攤提（邊際 1.25＋0.3 人日）；密碼傳遞由 API 形參保證 |
| 併 B-005 | wf-watchdog | 淨減行數、刪 L-142 補丁、消 GNU/BSD 雙分支；必與 B-005 同刀（CLAUDE.md §2 契約字面只改一次） |

軌別＝**輕量軌**（user 拍板、推翻評估建議之 SDD）；等價驗收 DoD 與 ADR 義務不隨軌別豁免。
治理落點（tools/ vs deploy/——四份自測名冊全綁 `tools/<name>.py` 字面）＝①開刀首題、屆時拍。

### 二、兩硬約束（全轉換集適用）

1. **stdlib-only**：零第三方套件（現有 tools/*.py 實證零第三方 import；YAML 走
   `sops --output-type json`＋json、v9fs 判定讀 /proc/self/mountinfo 或保留單次 stat -f
   subprocess；亂數維持 docker openssl、不換 python secrets 模組）。
2. **等價驗收硬規則**：無 machine-checkable 等價驗收（逐位元組比對／exit code 矩陣／輸出
   diff）之腳本不轉；永遠測不到的段（passphrase 互動、產鑰主路徑、ALTER ROLE 生效）以
   人工端到端一輪補、記於收刀事件。

### 三、不做集（16 支、逐支帶由）

| 對象 | 不做理由（一句話） |
|---|---|
| tools/bootstrap.sh | python3 故障時 bash 版仍能建環境、python 版連第 0 節都跑不到；§6 以「bootstrap 綠」為可 commit 前置；bash 驗 python／python 驗 bash 之異質互驗不可自毀 |
| .githooks/pre-commit | 邏輯已住 python（五工具只能 subprocess、零行程節省）；轉換須重建三支現存最強檔文守衛（名冊對賬／行尾 `\|\| exit 1`／betterleaks --config 斷言）、重建期即「守門動作恆不跑」失效類的裸奔期 |
| .githooks/pre-push＋.githooks-submodule/pre-push | 4 行純轉接頭、三檔 source 契約連坐、零可轉邏輯 |
| .githooks-submodule/pre-commit | 檔內明文設計契約「零 python 依賴、毫秒級」；子庫為 node／rust 生態，shebang 換 python3 遇 PATH 受限即 exit 127＝子庫 commit 零機密防線；翻案需新 ADR |
| .githooks/lib/scan-range.sh | 唯一有真演算法者，但零測試、零實戰史、守 --no-verify 災難路徑＝負期望值；覆蓋缺口以 B-039 測試矩陣補（與轉換脫鉤） |
| .claude/hooks/session-start.sh | 15 行 echo／cat／git、收益恰為零；`\|\| exit 0` fail-open 契約在 python 更易寫壞成 traceback 進注入內容 |
| deploy/sops.sh | 30 行實碼 exec 薄殼；且為 decrypt 等價驗收基準線、同期動它＝輸出差異無法歸因 |
| deploy/generate-dev-cert.sh | 工具面已容器化（alpine/openssl、rev4:0022 豁免沿 latest）、剩餘為檔案編排；user 確認不動 |
| deploy/generate-age-key.sh | python 轉換取消、改走容器化（ADR 0011、B-038）——真正的醜來自 host 缺 age 二進位，容器化使 66 行下載膠水＋27 行行內 python 蒸發 |
| .specify/ 九支（2412 行） | vendored、sha256 被兩張 manifest 釘死、零本地改動；git extension 四支上游已備 stdlib-only python port；rev4→rev5 已自然漂 583 行、若當年轉了今天須手工回填 |

hooks 六支「全組不轉」＝user 拍板（比評估建議之「scan-range 低優先」更嚴）。

## 後果

- 待辦承載：B-035～B-039＋B-005 併刀項＋B-004 補記（setup-reaper 註解失真）；
  執行時機一律 B12（後端首刀）之後。
- 落點解析口徑在①落地前維持六份現狀；bootstrap 那份**永不併庫**（驗證器不與被驗證者
  共用底座）。
- 不做集之任一支日後要翻案＝立新 ADR 引用本帳；hooks 子庫兩支另有檔內契約、雙重門檻。
- 總帳：待辦面合計約 10.8 人日（含 B-039 為 11.3），對照全轉 26.8。
