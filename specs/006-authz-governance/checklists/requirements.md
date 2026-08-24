# Specification Quality Checklist: 006 三維授權治理＋結構性封死＋授權回收桶（島 G 入憲）

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-23
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

- **判定原則承 001～005 前例**：本刀 stakeholder＝admin 後台的超級管理員與 workspace 維護者（技術身分即業主
  身分）。spec 中的端點路徑、seed 政策列座標、拒因碼與 i18n 鍵、憲法島／★軌道名、檔級名單（FR-047）、
  reason 字面（FR-011／FR-030）係**交付物座標（WHAT）**與治理設施引用，非實作選型（HOW）；鎖序、謂詞式標的
  集、五腿固定序、判定面同步觸發矩陣係 brainstorm §10 二十二題 **user 親決拍板之逐字轉錄**（拍板本身即以這些
  字面為對象），spec 記載拍板結果、非新增選型。
- **零 [NEEDS CLARIFICATION]**（機器驗證 grep＝0）：本刀階段 0 為 2026-08-22 五 lens 偵查後全面重寫之定稿、
  §10 二十二題逐題 user 親決、§11 連動後果已承接進 FR-013／FR-030／FR-031／FR-051。兩處由 spec 期拍板（回報
  備查）：①revoke reason 字面沿用 reason gate 負向測已預留之 `menu_revoke`／`button_revoke`／`endpoint_revoke`
  （brainstorm Q6 拍板「字面 spec 期定」）②restorePolicy 鎖序＝歸檔表列→sys_role 列（不入域後之自然收斂）。
  「plan 期釘死」項＝封死拒因鍵命名（contracts msg-keys）、rev4 as-built 碼清單、wire 型欄集——皆為落點指派、
  非語意待定。
- **「零 migration、零 seed 變更」係硬預期**（FR-001／FR-056）：11 支端點政策列已逐支對賬 001 凍結 seed
  （brainstorm §2、seed 列號機器複核）；唯一已知威脅（ADR 0050 §4 翻案觸發條款）已由 Q6 取 B 化解。plan／
  clarify 若冒出 DDL 或 seed 需求 → 走 RUNBOOK §10 三步並回頭修正本 spec。
- **已知態**（Edge Cases 首三條）＝拆刀與拍板的刻意結果：本刀新造「授予指向不存在 view 的自建選單」、
  menu 維四列 protected 不納封死、回收桶對選單／按鈕維只剩稽核閱覽——煙測與 CDP 對照之判準須照 Edge Cases
  所述驗「現狀形」。
