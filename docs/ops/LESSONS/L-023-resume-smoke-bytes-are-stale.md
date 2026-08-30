---
promoted_to: CLAUDE.md §2 看門狗段（「已完成 agent 走快取不重跑」＋L-027 之快取判定句＝防法③已載）；防法①（續跑冒煙改看最新 agent 檔 mtime＋本輪新字串）候選位＝tools/wf-watchdog.py 檔頭 docstring resume 場景段（現載「沿用原 runId」、未載「ARMED 冒煙位元組屬前一輪」）、不在本單元允許面、待下一把動該檔的刀（2026-08-30 B-091 盤點）
---
- **L-023**｜**`resumeFromRunId` 續跑時，看門狗 ARMED 行的冒煙位元組數是**前一輪**的殘留、
  不可據以判斷「新 prompt 有沒有送達」**：U-M 因允許清單缺口回 blocked，補列後以
  `resumeFromRunId` 續跑；看門狗 ARMED 行印出的「impl首行 10740bytes」與前一輪**完全相同**，
  讀起來像「implementer 走了快取、根本沒重新派」。成因＝resume 沿用同一個 wf 目錄與 runId，
  而看門狗的冒煙欄讀的是 journal 既有的第一筆記錄——那筆是前一輪寫的。同一行的
  `token 命中=1` 仍然有效（它證明鎖對了 run 目錄，不證明本輪 prompt 內容）。
  防法：①續跑時的冒煙查核**改看 agent 檔**——`ls -t <wf目錄>/agent-*.jsonl | head -1` 取最新一支，
  比 mtime 是否為剛剛、並 `grep` 本輪新加的字串（本例＝「本輪為續跑」）確認新 prompt 已送達；
  ②這是**一次性查核不是輪詢**，做完就等完成通知；③★續跑前先想清楚「我改的東西會不會讓
  (prompt, opts) 真的改變」——沒改到 prompt 的 agent 會走快取，那有時正是你要的、有時是災難。
