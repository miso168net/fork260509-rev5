---
promoted_to: CLAUDE.md §3（session 健檢判讀：pin 分歧先判方向、兩向處置＋is-ancestor 三態機判）
---
- **L-008**｜單向書寫的判讀規則在反向情境會導向破壞性操作。親歷：外層 pull 進他機 37 筆後
  rust-api pin 分歧，四處文件（CLAUDE.md §3／SessionStart hook／bootstrap 註解與 warn）皆只寫
  「一律回外層更新 pin」——該句為「worktree 在前」而寫；反向（pin 在前、worktree 落後）照做即把
  pin 倒回舊值、抹掉他人 commit。防法：凡寫「一律 X」的處置規則，先問「反向情境存在嗎」，
  存在就必須雙向寫並給機器判準（此處＝merge-base --is-ancestor 三態）。

