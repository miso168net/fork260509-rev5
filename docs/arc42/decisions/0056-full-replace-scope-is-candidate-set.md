---
id: "0056"
title: 三維授權全量替換之射程＝候選集——候選外現役列不撤不授不入 effective（rev5 路由註冊表遞增 vs seed 完整之實況拍板）
date: 2026-08-23
status: accepted
supersedes: []
superseded_by: []
provenance: "006-authz-governance 實作期（U5 implementer 升級①、2026-08-23）；user 親決 2026-08-23 取選項 A（射程＝候選集）；spec FR-009／FR-017 同日補射程句、tasks T037 新增；落地＝U5c（facade sys_casbin_policy.rs 三維同式＋測＋handler R_SUPER 自授 wire 案）；背景事實＝rust-api/migration/src/m002_baseline_seeds.rs 政策列（R_SUPER 端點維含未註冊端點列、2026-08-23 量測候選外 protected 5 列／非 protected 15 列〔seed R_SUPER 端點維 50 列＝候選內 30＋候選外 20〕）與 router.rs ROUTES 逐刀遞增（005 終態 38、本刀終態 49）"
tags: [authz, casbin, governance, state-machine, constitution-island-g]
---

## 背景

spec FR-009 寫「三維寫入以期望全集為輸入、由系統與現況比對導出撤銷集與新授集（全量替換）」，
rev4 藍本亦為 `to_revoke＝live∖desired`。該形隱含前提＝**現役列皆在候選集內**——rev4 路由
全部註冊完畢、seed 政策列無一不在候選集。rev5 實況不同：seed 於創世即寫入**全部世代終態**
的政策列（含刀 B 之 user 家族端點、`updateUserSessionPolicy` 等），而 `router::ROUTES`
逐刀遞增（005 終態 38、本刀終態 49）⇒ R_SUPER 的端點維現役列中恆有「尚未註冊進 ROUTES」
的列；端點 modal 的候選集＝`policy_endpoints()`（與判定面同源、FR-039），UI 勾不到候選外列
⇒ 全量替換把候選外現役列全算進撤銷集：其中 protected 列（2026-08-23 量測 5 列；本刀收刀後
仍剩 1 列直到刀 B）觸島 G2 整批拒 ⇒ **R_SUPER 在端點 modal 按 Save 恆回
`biz.role.protectedRevoke`**；即使無 protected，首次 Save 亦會把 15 列未註冊 seed 端點撤進
歸檔（`endpoint_revoke`、可復原）——非預期副作用。U5 implementer 於 handler 端到端測首次
實跑即撞此事、升級主線。

## 決定

**全量替換之射程＝候選集，三維同式**：撤銷集 MUST 自「現況 ∩ 候選集」導出
（`to_revoke＝(live ∩ candidates)∖desired`）；候選外之現役列（端點維＝未註冊進路由註冊表
之 (path,method)；選單維＝不在治理域之 route_name；按鈕維＝不在治理域 buttons 聯集之碼）
**不撤、不授、不入 effective**——UI 看不見的不動。讀端維持現狀（端點維讀端以方法白名單
回全部現役列、選單維孤兒 route_name 不反射）；orphan skip（期望集含候選外項靜默略過）不變。
落地＝facade `sys_casbin_policy.rs` 於鎖內 live 讀後、diff 前以候選集濾 live（三路同一處）；
spec FR-009 補射程句、FR-017 同步；tasks T037。

## 考慮過的替代案與棄用理由

- **B. 維持 live 全集（照 spec 字面）**——棄。R_SUPER 端點 modal 於刀 B 前恆被拒＝本刀「三顆授權 modal 接真」user story
  之主要可見功能對唯一有權者不可用；quickstart「R_SUPER 自授→通」不成立；刀 B 後首次 Save 仍會
  把未註冊 seed 端點撤入歸檔。
- **C. 只豁免 protected 之候選外列**——棄。R_SUPER Save 可用但非 protected 候選外列仍被撤入
  歸檔；語意不對稱、靠特例、日後難解釋。

## 後果

- R_SUPER 端點 modal Save 立即可用（前：勾全部候選按 Save→`2222 biz.role.protectedRevoke`；
  後：`0000`、revoked 0／granted n）；seed 未來端點列原封、刀 B 註冊後自動成為候選；歷史孤兒列
  不被全量替換清掉（選單／按鈕維孤兒之清理路徑＝選單刪除連動歸檔；端點維候選外列無 UI 撤銷路徑、
  待路由註冊後自動入候選——seed 未來端點列正是此形、刻意保留）。
- 島 G2 整批拒語意不變（仍以撤銷集觸及 protected 判）；封死（G6）不變；FR-039 候選同源因此
  成為射程的唯一定義（候選集＝可操作集）。
- 既有測若以「候選外現役列被撤銷」為期望者須改（U5c 逐案核）；新增三維各一支「候選外現役列
  不動」測＋handler「R_SUPER 自授 P 中端點→0000」wire 案。
- 日後任何新增維度或候選集定義變更，MUST 同步本射程語意（候選集即射程）。
