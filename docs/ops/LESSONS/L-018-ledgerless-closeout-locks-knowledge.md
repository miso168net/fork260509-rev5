---
promoted_to: CLAUDE.md §2（單元收尾六步序之③落帳、③必早於⑤ generate）
---
- **L-018**｜**單元收尾只寫 commit message、不落帳本也不勾 tasks.md，等於把知識鎖進 git 史**：
  003-auth-session 連跑九個單元（U-A~U-J）後盤點才發現——(a)每單元發現的衍生工作與踩坑全寫進
  了 commit message，但 `BACKLOG.md`／`LESSONS.md` **零 append**；(b)`tasks.md` 77 條 checkbox
  **全部沒勾**、已完成 38 條卻通篇 `[ ]`，該檔完全不反映實況。兩者都不會被任何機器閘擋下（lint
  不比對 tasks 勾選、帳本形制亦無機器守——後者即 U-N 待斟酌項），所以能一路靜默到收刀。
  ★危害不對稱：commit message 是**寫給讀那顆 commit 的人**看的，帳本才是**查得到**的那一份
  ——下一個接手的人不會去翻九顆 commit 找待辦；tasks.md 不勾則進度只能靠人腦或 session 外的
  task list 維持，換 session／換人即失真。防法：①單元收尾六步序**第③步固定是落帳**——衍生
  工作→BACKLOG append、踩坑→LESSONS append、tasks.md 把該單元涵蓋的 T 全勾；★主動做、不等
  user 問（user 2026-08-10 明令）；②★落帳必須排在 `docs-sync.py generate` **之前**：STATE.md
  的帳面統計現讀 BACKLOG／LESSONS，反序會產出仍帶舊計數的 STATE.md，**而且因為沒有 diff 所以
  不會被察覺**（與 pin／generate 次序陷阱同一形）；③判準——「這件事下一個人要查得到嗎？」要，
  就進帳本；「這條 task 做完了嗎？」做完了，就勾。commit message 照寫，但它是補充、不是替代。
