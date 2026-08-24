---
id: "0057"
title: rust 格式守門——rustfmt 設定釘 max_width=100＋use_small_heuristics=Max（存量 diff 實測最小）、閘以納冊工具承載並於 pre-commit 條件式呼叫容器（stack 在跑才實跑、不在跑具名跳過）
date: 2026-08-24
status: accepted
supersedes: []
superseded_by: []
provenance: "B-112（006-authz-governance Foundational 單元 implementer 查定：容器 toolchain 未裝 rustfmt component、repo 無 rustfmt.toml、零機器 fmt check）；維護批 A（批分支名＝maint- 前綴串接七條 B 編號、字面不入本檔——子串會被 Lint25 誤讀為跨代刀名形，同 ADR 0046 註）主線於 dev 容器實測存量 diff 後提兩題、user 親決 2026-08-24；落地＝該批 U5（tools/rust-fmt-gate.py＋deploy/Dockerfile.rust-api＋rust-api/rustfmt.toml＋hook 段）＋主線存量格式化單獨一顆 rust-api commit"
tags: [tooling, rust, pre-commit, governance]
---

## 背景

rust-api 自 002 起全部由 agent 手寫、從未跑過 rustfmt：`deploy/Dockerfile.rust-api` 以
`rust:1.96.1-slim` 起建、`rustup` 只裝 minimal profile（無 `rustfmt` component），repo 亦無
`rustfmt.toml`。新碼只能「手動對齊既有風格」，而既有風格本身是有機長成的——一致與否
無任何機器判準（B-112）。rev5 零 CI（ADR 0014 之既知缺口同族），唯一的機器守門面是
pre-commit；但 host 無 rust toolchain、`cargo fmt` 只能在容器內跑，而 pre-commit 現行紀律
是「stack 沒起時 MUST 可用」（route-artifact-gate 刻意不掛 pre-commit 即為此）且各段守門
皆「純檔案掃描、零 docker」。

主線於 2026-08-24 在 dev 容器臨時裝上 rustfmt（1.9.0-stable、隨 1.96.1 附帶）量測
「存量一次格式化」的 diff 規模（`cargo fmt --all --check`、84 檔／60,539 行）：

| 設定 | diff 段數 | +行 | −行 |
|---|---|---|---|
| max_width=100（預設）＋`use_small_heuristics="Max"` | **675** | 3,457 | 1,696 |
| 全預設（max_width=100、heuristics Default） | 1,649 | 12,320 | 3,097 |
| max_width=120＋Max | 1,293 | 2,373 | 6,272 |
| max_width=120（無 Max） | 1,273 | 6,546 | 3,065 |
| max_width=130／140（無 Max） | 1,118／1,124 | 4,531／3,180 | 3,237／3,928 |

行寬分佈：>100 字元者僅 689 行（1.1%）——差異主體不是行寬，而是「單行呼叫是否被拆多行」
的 heuristics；`Max` 形與碼庫慣用形最接近。

## 決定

1. **設定檔** `rust-api/rustfmt.toml`：`max_width = 100`（＝預設、顯式釘住）＋
   `use_small_heuristics = "Max"`＋`style_edition = "2024"`（與 Cargo.toml `edition = "2024"`
   同源、顯式釘住）。三值皆 stable 選項；不用 nightly-only 選項。
2. **工具鏈**：`deploy/Dockerfile.rust-api` 於 watchexec 安裝行之後加
   `RUN rustup component add rustfmt`——版本＝toolchain 1.96.1 隨附之 rustfmt（1.9.0-stable），
   **無獨立釘版面**（rustfmt 與 rustc 同版發行、由 `rust-toolchain.toml` 的 channel 決定）。
3. **閘的承載**＝納冊 python 工具 `tools/rust-fmt-gate.py`（`check`／`test` 兩子命令、入
   TOOLS_PY／hook 自測迴圈／bootstrap `run_tool_test`／README 樹四處名冊）：
   - `check`：docker 不可用或 compose 檔缺席＝具名跳過 rc=0；rust-api 容器**未在跑**＝具名
     跳過 rc=0（印出「起 stack 後自動恢復實跑」）；容器在跑＝`docker compose … exec -T
     rust-api cargo fmt --all --check`，未格式化＝印 diff 摘要與補救命令、rc=1 擋 commit；
     容器在跑但 `cargo-fmt` 缺席（舊映像）＝環境不可用 **fail-loud rc=2**、附重建映像命令
     （不得靜默跳過——那正是「守門動作恆不跑」的失效類）。
   - `test`：離線自測（subprocess 樁）涵蓋上述四態＋rc 語意。
   - pre-commit：`rust-api` gitlink 或本工具本體 staged 時呼叫 `check`（與 entity-drift／
     seed-view-gate 同觸發鍵）；跳過邏輯住工具內、hook 段只做接線，故 docs-sync
     `TestGateWiring` 乾跑案可以樁工具釘住接線（整段被拆即紅）。
4. **存量格式化**＝主線單獨一顆 rust-api commit（訊息標明 B-112、零語意變更），排在本批
   全部 rust 改動之後、pin bump 之前；與任何功能／測試改動隔離。
5. **單元紀律**：CLAUDE.md §2 編排提示詞範本之 rust 行加「完工前容器內 `cargo fmt --all`」
   ——implementer／fix agent 完工自驗必含；主線親改 rust 碼亦同。

## 考慮過的替代案

- **hook 段直接內嵌 docker 呼叫**（不立工具）：不採。docs-sync 乾跑 harness 只能樁
  TOOLS_PY 名冊工具，內嵌 docker 呼叫在沙盒裡要嘛真的去打 docker、要嘛靠「compose 檔
  缺席即跳過」而使接線案永遠走跳過分支——接線不可證。
- **不進 pre-commit、只靠 agent 紀律＋收刀閘**：不採。B-112 的缺口正是「無機器 check」；
  主線親改時零機器擋、忘跑即漏。
- **pre-commit 無條件要求容器在線**：不採。違反「stack 沒起時 MUST 可用」既有紀律，
  離線／停 stack 時 pin bump 全擋。
- **max_width=120 或全預設**：不採，量測見背景表——前者 diff 反而更大且行寬超出多數編輯
  器分隔線，後者把大量單行呼叫拆成多行、一次性 commit 難以人審。

## 後果

- pre-commit **首次**在 stack 在跑時呼叫容器（實測 1～2 秒、落在 45s 警戒線內）；「stack
  沒起時 MUST 可用」紀律**不變**（具名跳過）。跳過分支的存在意味著離線 commit 仍可能帶入
  未格式化碼——下一次 stack 在跑的 pin bump 會擋下、屬延遲一站而非漏網。
- `check` 檢查的是 rust-api **工作樹**內容而非 pin 指向的 commit：worktree 髒時工具印警示
  （兩者可能不同）；正常流程（子庫先 commit、再回外層 bump pin）下兩者一致。
- 舊映像的機器（未重建 `rust-api` 映像）在 stack 在跑時會 rc=2 擋 commit、附重建命令；
  這是刻意的 fail-loud，不設豁免。
- 存量格式化 commit 使 `git blame` 對被動行指向該 commit；以 `git blame -w`／
  `--ignore-rev` 該 SHA 可繞過（RUNBOOK 記該 SHA）。
- 治理工具名冊由 15 支 python 增為 16 支；docs-sync 名冊釘測、README 樹（Lint27）、
  bootstrap 體檢、RUNBOOK 命令表同步。
