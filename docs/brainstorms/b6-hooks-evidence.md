# B6 hooks 接線＋bootstrap 裁製施工紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-04。依據＝§4.2 B6（「只做三件」縮限版）。

## 三件實得

| # | 件 | 實得 |
|---|---|---|
| 1 | 外層 hooksPath 指派 | `git config core.hooksPath .githooks`＋**讀值回驗**＝`.githooks`（rev4 兩子庫「設而未驗＝防線未就位」的教訓處置；本設定 per-machine、新機由 bootstrap 重佈）。★自此 B7 創世 commit 起 pre-commit 真閘實彈 |
| 2 | docs-sync test 手動跑 | OK（skipped=4、Day1 謂詞跳過如預期） |
| 3 | bootstrap 裁製＋掃描器斷言 | `BETTERLEAKS_VER` 1.7.1→**1.7.3**；安裝指引改**雙平台 case**（linux_x64＋sha256sum／darwin_arm64＋shasum -a 256、未支援平台 die——同 B5b AGE_ASSET 處方）；斷言單跑（bootstrap 同形裸值比對）＝**1.7.3 過**；平台 case 本機實選 darwin_arm64 |

## 刻意不做（§4.2 B6 明文）

- 體檢**不可全跑**：第 2/3 節 clone 源倉＋掛 worktree（B9 的事）、第 5 節 fork-delta-lint（需基線源倉）與 entity-drift check（需 schema 快照）——B9/B10 前必 die。完整體檢＝B8b。
- hooks 指紋斷言不跑（以 `git hash-object` 對 HEAD 冒號路徑，B7 前 HEAD 不存在必 die）。★降級版（工作樹對 B2 manifest）已無意義——pre-commit／scan-range／bootstrap／wf-watchdog 歷經 B2 裁製＋B5b `${}` 一鍋修共多輪合法變更，B2 manifest 值已非預期值；工作樹↔index 一致性由 porcelain 覆核承接，正式指紋驗證隨 B8b 以 HEAD 為基準。

## 既已就位（免做）

- origin 斷言＝rev5（B3 已重指，本步驗讀 L31-33 確認）；兩子庫 hooksPath 體檢＋讀值斷言已預埋（bootstrap L107-116、B9 接線後轉綠）。

## 收工

lint 基線 2 錯誤／0 警告／10 跳過（殘紅全繫 B7）；五支 self-test 綠；rev4 porcelain 0、HEAD 2b8a101 凍結。
