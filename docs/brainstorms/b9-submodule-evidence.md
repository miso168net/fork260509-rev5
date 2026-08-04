# B9 子庫建置施工紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-04。依據＝§4.2 B9（內部順序 v2：hook 保護先於首 commit）＋`b9-gate-decisions.md`。
> 外層收工 commit＝`b0e356b`；子庫首 commit＝base-web `0fee6c02`／rust-api `69561c4`（皆已 push、user 當回合同意）。

## 一、八步實得

| 步 | 實得 |
|---|---|
| ①clone | GitHub 直 clone 兩源倉（甲案）；起點驗收＝example `8be6f9ba…dae5`／main tip `32c5254…9787`＝Initial commit；兩倉 gitignored ✓。★前端 clone 預設分支＝rev1-admin-base-web（GitHub default）——照「源倉恆切 example tip」紀律先 `switch example` |
| ②③分支＋worktree | `rev5-admin-base-web`@8be6f9ba→`base-web/`；`rev5-admin-rust-api`@32c5254→`rust-api/`（`worktree add`、絕不 submodule add） |
| ④hooksPath | 兩子庫指向外層 `.githooks-submodule`＋讀值回驗雙 OK（rev4「設而未驗＝防線未就位」教訓處置點） |
| ⑤x_fork 首 commit | 兩份 `x_fork.branch-origin.md`（rev4 同形改字；前端首行 `[rev5-inline meta+]` 新增型圈界）——**受 hook 保護後才落**、過子庫 pre-commit 實彈 |
| ⑥upstream 鎖 | 前端 `remote add upstream soybeanjs/soybean-admin`＋push URL `no_push`（與 rev4 逐字同形；後端無 upstream、不加）——丙缺口的工程自拍步 |
| ⑦push（user 同意） | 兩新分支上 remote、ls-remote 驗證 SHA 相符；只推新分支、零觸既有分支 |
| ⑧.gitmodules＋pins | 手寫兩組（path/url/branch 長名）；外層首記兩 gitlink＋commit `b0e356b`、porcelain 0、`submodule status` 行首「-」正常態 |

## 二、機器閘實彈三則（B9 段）

1. **gen.screens 到期即紅第二例**：worktree 掛載使 routes.ts 存在、豁免解除謂詞成立→lint 立紅要求下架→依紀律拔項（兩表同刀）→ **screens 真表首算 71 行**（generate 重算 5 檔）；self-test skipped 4→**3**（該 skipUnless 案同步解除轉綠）。
2. **Lint01 攔 pins commit 第一次嘗試**：gitlink 入 index 後 STATE 的 pins 欄由「未定」變實 SHA——add 前跑的 generate 已過期。照紅訊息去處補算後放行（generate 的輸出依賴 index 狀態＝本次學到的時序細節）。
3. **entity-drift-gate 攔第二次嘗試（rc=2）**：rust-api gitlink staged 觸發 check、schema 快照（schema 刀產物）Day-1 缺席→環境不可用硬擋。處置＝pre-commit 觸發段加**快照缺席具名跳過**（ADR 0001 決定 4「pre-commit Day-1 具名跳過」模式第二例、與 fork-delta 同族）＋成對契約測試（快照在必跑／缺席必跳，427+ tests OK）。快照就位（schema 刀）自動恢復實跑；快照在而 drift＝照擋。

## 三、連動實得（B9 收工全景）

- **skip 明細 9→5 案**：Lint16×2／Lint17×2 隨 gitlink 入 index **轉實跑**——Lint17 pin 互證綠；Lint16 首記 pin 走「舊 pin 不可解→退化為新 pin 全樹掃」WARN 放行路（B4 修的 python re 單一引擎實跑、兩子庫全樹掃過）。
- **fork-delta-lint 首次實跑**（源倉就位、B7 Day-1 跳過自動解除）：base-web 對 example 基線比對綠（唯一差異＝x_fork 新檔、新增型標記合規）。
- wire-schema staged-gate：容器未起→警告放行（fail-open 設計語意實證）。
- 殘餘豁免 5 案全繫後續步：gen.compose（B10）、gen.snapshots（schema 刀）、gen.router／gen.msg_dict／lint24.day1（B12±）。

## 四、刻意留給後續

| 項 | 落點 |
|---|---|
| entity-drift Day-1 跳過解除＋gen.snapshots 拔項 | 波 0 schema 基線刀（refresh 產快照） |
| gen.router／msg_dict／lint24.day1 的 lint 端拔項實證 | B8b（裁決員硬性待辦已入 task #25） |
| example compose 掛載的源倉路徑改指 rev5 自己那份 | B10（§4.5.9 錯開第 8 條） |
| bootstrap 完整體檢（含 hooks 指紋、兩源倉／worktree 斷言） | B8b |
