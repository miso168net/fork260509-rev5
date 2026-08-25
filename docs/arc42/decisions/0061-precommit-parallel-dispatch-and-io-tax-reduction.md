---
id: "0061"
title: pre-commit 全鏈提速——閘並行派發（fail-fast 改 run-all）＋工具內 I/O 稅削減（作用域快取／EAFP／subprocess 並行）；根因是 drvfs 單次 I/O 延遲而非條款邏輯
date: 2026-08-25
status: accepted
supersedes: []
superseded_by: []
provenance: "B-130（2026-08-25 該批 pin bump commit 的 hook 自報 55s、首度真實越 ADR 0044 之 45s 警戒線，觸發器「hook 開始自報 >45s 警告時」達成）；主線同日剖析與微基準後提題、user 親決做 A+B；落地＝維護批 maint-b130"
tags: [tooling, performance, pre-commit, governance]
---

## 背景

B-130 原列三個處置面（剖析 `docs-sync lint` 慢條款／`docs-sync test` 案分層／`fork-delta-lint`
成長面）**皆假設成本在條款邏輯**。2026-08-25 剖析後三者全數證偽：

- `docs-sync lint`（cProfile、19.3s）：檔案系統原語佔 **64%**（`open` 1407 次／`stat` 1428 次／
  `__exit__`／`read`），唯一顯著的邏輯成本 `scan_id_namespace`（Lint25）僅 **7%**。
- `fork-delta-lint`（cProfile、14.3s）：`select.poll` 佔 **99%**（50 個 `git show` subprocess
  逐次序列等待），檔案 I/O 僅 0.167s。

**根因＝drvfs（9p）單次 I/O 延遲 × 存取次數**。受控微基準（同一批 269 檔 stat+read）：
drvfs **2845ms** vs 原生 ext4 **4.8ms** ＝ **587×**，每檔約 **10.56ms**；其中 `os.path.isfile`
一項就佔 40%（250 檔：isfile 732ms／open+read 1092ms）。

★另兩項實測推翻既有推估：①`wire-schema check --staged-gate` 真路徑僅 **0.43s**，而合成公式
沿用 08-16 的 **8.431s**（該值是未短路路徑；真實 pin bump 走 `no-typings` 短路）——B-130 所列
「先決事實」自此結清 ②9p 雖掛載成單一 transport，**支援並發 in-flight 請求**：同批檔案序列
2572ms／並行 4 為 526ms（4.89×）／並行 8 為 406ms（**6.33×**）。

## 決定

**A. hook 層：閘並行派發**（`.githooks/pre-commit`）。各閘皆唯讀、無共享可變狀態，以
`pc_run` 背景派發、`pc_join` 收斂。★**機密面兩道刻意留在序列前導**（betterleaks 樣式掃描與
`secret-value-guard` 值比對）：兩者屬 hook 檔頭逐字載明的**事件型**（機密進 git 歷史不可逆），
併入並行段會使擋阻被延後到最慢閘結束、且輸出淹沒於回放序。

**B. 工具層：削減 I/O 稅**
1. `docs-sync.py` 之 `_read` 加**作用域快取**——`run_lint` 一輪內 971 次呼叫只碰 380 個唯一
   檔案（重複率 2.56×）。★快取**限作用域、預設停用**：`generate` 寫檔後會再讀、自測 529 案
   各自建臨時 repo 並就地改檔，行程級常駐快取會讓兩者讀到過期內容＝把效能修成正確性缺陷。
2. 同函式改 **EAFP**（`try: open` 取代 `os.path.isfile` 前置判斷）——省掉的正是那 40%。
3. `fork-delta-lint.py` 之 `scan()` 以 `ThreadPoolExecutor` **並行預取基線原文**；判定邏輯與
   逐檔順序一字不動（下方迴圈照原序消費），故結果逐位元組相同。

## 語意變更（刻意，非退化）

**fail-fast → run-all**：並行後某閘失敗時其餘閘照樣跑完，退出碼於 `pc_join` 統一收斂
（任一非零即 exit 1）。取捨理由＝本 repo 紀律是「被擋的是 Claude、同回合修復」，一次看齊所有
失敗比逐輪擠牙膏省一個數量級的往返；各閘皆唯讀、多跑無副作用。
★**fail-closed 未變**，變的只是 fail-fast。

## 守門面的同步調整（三項，皆為等價轉換或補強）

1. `test_every_gate_action_line_is_guarded`：保護形式自逐行 `|| exit 1` 擴為「`|| exit 1` **或**
   `pc_run` 派發」二擇一，關切未變＝每個動作都必須有退出碼歸宿；**並補斷言 `pc_join` 收斂點
   存在**——少了它是全段 fail-open，比舊形的「末位優勢」更危險。
2. `_UnorderedLines`：樁工具完成序在並行下本質不確定，比較改為忽略順序、**保留重複次數**
   （「哪些閘被觸發」「各幾次」皆完整保留）。
3. **新增** `test_hook_runs_secret_gates_serially_before_parallel_dispatch`：釘住上述唯一仍屬
   契約的順序。沒有它，把 betterleaks 改成 `pc_run` 會全綠存活＝ADR 0024 所指「判準結構性
   無感即恆綠」。

## 後果

- 同條件量測（bench 三跑取最佳）：全鏈 **43.46s → 13.09s（3.3×）**；分項 `docs-sync lint`
  25.34→15.92、`docs-sync check` 4.79→3.44、`fork-delta-lint` 17.04→**3.93（4.3×）**。
  真 hook 最重情境（staged 三支工具＝觸發 529 案自測）實跑 **24.1s rc=0**，瓶頸已是自測本身。
- ADR 0044 的兩錨（WARN 45／FAIL 90）**不動**：門檻仍是合理警戒，本決定改的是被量的東西。
  該 ADR 所記的「雙峰」結構屬 as-built，隨本批更新於 RUNBOOK §12.1、不回灌 ADR。
- 非 vacuous 自證（ADR 0024）：三個變異皆落地紅證——拆一個 `pc_run` 派發→1 案紅；拿掉
  `pc_join`→2 案紅；把 `secret-value-guard` 移到並行段後→順序契約案精確命中；還原後 529 全綠、
  逐位元組相同。
- ★**根治面未做、留帳 B-133**：repo 位於 `/mnt/d`（v9fs），CLAUDE.md §11 自己就寫著
  performance-sensitive path 屬原生 WSL 檔案系統。遷移可再得約 587× 的 I/O 面，但屬拓樸調整
  （worktree 的 `.git` 絕對路徑、docker bind mount、Windows 側工具鏈），須走一次性遷移程序。
