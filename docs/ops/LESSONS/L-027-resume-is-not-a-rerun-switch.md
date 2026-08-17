---
promoted_to: CLAUDE.md §2（看門狗段：resume 只用於故障續跑、重跑＝新開 workflow）
---
- **L-027**｜**Workflow 的 `resumeFromRunId` 不是「讓某一支 agent 重跑」的手段**——它是
  故障續跑用的，拿來當重跑開關會踩兩個坑：①快取判定不是逐字比 prompt。本批 U5 為了讓卡住的
  spec-fix-3 重跑而改 script 的註記內容（且用 `round === MAX_FIX_ROUNDS` 條件確保只有那一支
  的 prompt 變），檔案確認改到、`node --check` 也過，resume 卻回 `subagent_tokens: 0`／
  `tool_uses: 0`／`duration_ms: 10`——**七支全數快取回放**、吐出逐字相同的舊結果，連續三次
  皆然。②就算改對了也可能反噬：若圖省事直接改共用的 `fixPrompt`，前幾輪已完成的 fix agent
  會一併失去快取而重跑，而它們重跑時看到的是**自己已修好**的檔案 ⇒ 回報零改動 ⇒ 恰好觸發
  「fix 連兩輪零改動＝不收斂」把整支 workflow 提早中止。★正解：需要某階段重跑就**新開一支
  只跑該階段的 workflow**（新 runId、零快取糾纏），CONTEXT 內把已完成階段的結論與「勿重報」
  清單寫清楚。本批 U5b 即此形——只跑碼品質、7 支 agent、當場抓出一發存活變異。
