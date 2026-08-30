# Specification Quality Checklist: 007 使用者＋密碼管理（島 I 入憲、授權下放＋no-escalation）

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-26
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- **判定原則承 001～006 前例**：本刀 stakeholder＝admin 後台的超級管理員／多層管理員／一般登入者與 workspace
  維護者（技術身分即業主身分）。spec 中的端點路徑、seed 政策列、拒因鍵與 i18n 鍵、憲法島／★軌道名、檔級名單
  （FR-042／FR-048）、事件 reason 與稽核詞彙字面係**交付物座標（WHAT）**與治理設施引用，非實作選型（HOW）；
  包含規則三元（A／T／N）、鎖序、五步序、滑動窗常數係 brainstorm §3 四十一題＋§3b 十八題 **user 親決拍板之逐字
  轉錄**，spec 記載拍板結果、非新增選型。
- **零 [NEEDS CLARIFICATION]**（機器驗證 grep＝0）：階段 0 已於 2026-08-25 以五路偵查 workflow 對賬後定稿、41 題
  逐輪親決；2026-08-26 grilling 十八題把 frontier 走空、共識已確認。兩處由 spec 期定字（回報備查）：①違規碼
  字面＝Lint24 白名單既有八鍵尾段（FR-027）②session_event 五 reason 與 denylist `admin_kick` 字面（FR-022／
  FR-023）。「plan 期釘死」項＝rev4 as-built 碼清單、wire 型欄集、拒因鍵全表（contracts msg-keys）、CDP 起手腳本
  ——皆為落點指派、非語意待定。
- **「零 migration、零 seed 變更」係硬預期**（FR-001／SC-004）：十支端點政策列逐支對賬 001 凍結 seed（brainstorm
  §0 列號機器複核）；自助二支採 Authed 免政策列；custody／memo／session_policy／活性唯一索引／八鍵皆在基線。
  plan／clarify 若冒出 DDL 或 seed 需求 → 走 RUNBOOK §10 三步並回頭修正本 spec。
- **user 親決之非建議項二處**（Q09 下放寫端＋G8 前端不預判）已如實入 FR-016～FR-021 與 Edge Cases；其代價
  （測試面倍增、seed 之 R_ADMIN 預設只能管同級、5003 toast 學規則）於 brainstorm §8 逐字列出。
- **已知態**（Edge Cases 末段）＝拍板的刻意結果：詳情頁佔位、個人中心三卡留白、兩語、B-064 三顆鈕必留、B-008
  餘兩張死項——煙測與 CDP 對照之判準須照 Edge Cases 所述驗「現狀形」。
