# Implementation Plan: 005 role＋menu 管理 CRUD 寫端（含序列化域與判定面同步基建）

**Branch**: `005-role-menu-crud` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-role-menu-crud/spec.md`

## Summary

把 role／menu 兩張管理頁自 upstream demo 殼接成真：16 支端點（ROUTES 22→38、seed 政策列
100% 預埋＝零 migration 零 seed 變更）、前後端同刀、CDP 三方對照驗收。同刀落地三件授權治理刀
（authz-governance）也要消費的底座：選單域 advisory 序列化域（含 deleteRole 入域）、casbin
rebuild-swap 判定面同步（menu 移除面 MUST reload、keep-last-good、絕不裸呼 load_policy）、
授權歸檔寫入面＋reason gate。憲法一次 MINOR（v1.6.2→v1.7.0）：島 H 五條入憲＋`MANAGE-PAGE-WIRING`
用途 (ii)＋B-087 殘餘②補註。技術路徑＝高度參照 rev4:009／rev4:010 as-built 重打字消化
（ADR 0019；差異點見 research R2）。

## Technical Context

**Language/Version**: Rust（workspace 既有 toolchain、容器內 build/test、全程 serial）＋
TypeScript／Vue 3（base-web、pnpm）

**Primary Dependencies**: 零新依賴——axum／sea-orm／casbin 2.20.0（Cargo.toml:46 釘版、與
rev4 同版）／既有 sea-orm-adapter；前端零新套件（naive-ui／useNaivePaginatedTable 既有）

**Storage**: PostgreSQL（dev 容器）——`sys_role`／`sys_menu`／`casbin_rule`／
`sys_casbin_policy_archive`／`sys_operation_log` 全為 001 基線既有表；redis 不涉本刀新面

**Testing**: cargo test（容器內 serial；現 512 支）＋既有 lint 型測家族＋schema-gate 三閘＋
wire-schema 快照＋fork-delta-lint＋view-render-guard；CDP 實機三方對照（22080 vs 42080）

**Target Platform**: Linux 容器（dev compose stack；單副本＝ADR 0014）

**Project Type**: web-service（rust-api）＋web-app（base-web fork）雙腿同刀

**Performance Goals**: 管理面 QPS≈0（治理寫端全序列化之代價經 rev4 論證＝零實質影響）；
無新效能預算節（RUNBOOK §12 既有基線不受擾動）

**Constraints**: 零 migration／零 seed 變更（硬預期）；域鎖必為 txn 首動作；判定面同步失敗
keep-last-good 服務不中斷；憲法 Amendment 先行硬閘（accepted 前不得動 base-web 既有檔）

**Scale/Scope**: 16 端點／島 H 五條入憲／三支 ADR／修改型 5~6 檔＋新增型 wrapper/typings／
~17 執行單元（tasks 期定稿）；seed 選單 78 列、政策 163 列不動

## Constitution Check

*GATE: Phase 0 前初評（對憲法 v1.6.2）→ Phase 1 後複評（對 Amendment 後 v1.7.0）。*

1. **§I.1 base-web 為權威**：**PASS（帶一筆拍板記載）**——role／menu 頁為 upstream 既有
   demo 面、其 fetch 打的端點正是本刀補齊對象（「fork 有而後端缺」的正向補齊）。wire 型別
   依 brainstorm 拍板照 004 慣例開獨立命名空間（`createdBy` 帳號名 enrich、`deleted` 導出
   布林），demo 頁欄定義同批改（修改型標記）⇒ 權威鏈＝本刀 contracts 凍結、typings 新命名
   空間同批落地、upstream 舊型別檔零標記保持。驗收錨＝`contracts/wire-role-admin.md`＋
   `wire-menu-admin.md`＋wire-schema 快照。
2. **§III.2 base-web inline**：**涉及——授權以 Amendment 先行取得**。本刀動 base-web 既有檔
   ＝role 3 檔（index.vue／role-operate-drawer.vue／role-search.vue）＋menu 2~3 檔（index.vue
   ／menu-operate-modal.vue／shared.ts 視需要），逐行 `原行:` 修改型標記；★兩顆授權 modal
   一行不動（授權治理刀射程、檔級硬邊界）。授權鏈＝ADR draft → user 親決 → accepted ＋
   §III.2 `MANAGE-PAGE-WIRING` 加用途 (ii)（檔逐支列出）＋ §I.7 島 H 條文 ＋ bump
   1.6.2→1.7.0 ＋ `docs-sync generate`。★硬序約束：Amendment accepted 之前不得動任何
   base-web 既有檔（research R10 之 U1 硬閘；純後端單元不受阻）。i18n 新鍵（showDeleted／
   confirmRestore＋CRUD 拒因鍵）進 `backend:`／`page:` 樹屬既有授權用途內或隨 (ii) 併列。
3. **§I.2 menu 走 Casbin enforce**：PASS——本刀對選單域只做 CRUD 資料面；可見性授權
   （menu 維 grant）屬授權治理刀；零 seed 改動、動態選單模式既有機制不變。已知態③
   （新建選單側欄不現）＝本項的誠實結果、非違反。
4. **§I.3 wire 不變式**：PASS——信封三欄／業務錯誤 HTTP 200／id 逐欄忠實（i64→number＋2^53
   守衛沿 004）／`msg` 載穩定 i18n key／**13 碼矩陣零觸碰**（守門與唯一性拒因復用 `2222`、
   授權拒 `5003` 既有，零新錯誤變體）。`PageRes` 上移 envelope 層＝機械搬移、契約字面不變、
   既有消費者（ip_rule）同批改引。
5. **§I.5 前代 source**：PASS——rev4 樹唯讀直讀、重打字消化零拷貝、註解 rev5 語境重寫
   （rev4 出處帶 `rev4:` 前綴）；防回歸以 research R2 清單落地（含 `"rev4menu"` 域鎖字面
   →`"rev5menu"`）。
6. **§II 設計拍板**：PASS——既有三拍板零抵觸。★推翻一處碼內舊拍板：`enforce.rs:8`／
   `main.rs:56`「boot 載入即終態、不再重載」——理由子句（B12 零治理寫端）被本刀移除面推翻，
   以 ADR 翻案＋同批改寫兩處註解（沿 004 對狀態容器五欄封條的處置形）。
7. **§III ★ 軌道**：**涉及——授權以 Amendment 先行取得**（同第 2 題）。屬既有軌道
   `MANAGE-PAGE-WIRING` 加用途、非開新軌道；wrapper／typings 新檔走既有 WRAPPER／ADAPT
   軌道零修憲。
8. **§I.6 業務表審計欄**：PASS（零 migration）——`sys_role`／`sys_menu` 皆變體 A 六審計欄
   基線齊備＋軟刪 partial unique（`sys_role_code_active_uniq`／`sys_menu_route_name_active_uniq`
   機器核）；`casbin_rule` 11 欄（adapter 8 基底＋治理 3）；歸檔表 14 欄含 `role_id`。
   ★sequence 紀律：`sys_role_id_seq`／`sys_menu_id_seq` 有 gate2 setval 期望值、寫端推進
   與 gate 互動為 tasks 早期顯式查證項（data-model §7）。
9. **§I.7 行為島**：**涉及——授權以 Amendment 先行取得**。本刀落地第七座島（島 H 選單域
   生命週期）：H1 序列化域（含終態成員清單——授權治理刀寫端屆時加入＝vacuous 先成立）＋
   advisory key space 全域唯一句／H2 同鍵重建零繼承（DB＋判定面雙封）／H3 樹結構不變式＋
   常量父鏈句（rev5 專屬新條）／H4 不可變錨欄＋治理域顯示域分層／H5 復原不回灌。MAJOR 界定
   照 rev4:0052 字面；常數（advisory key、上溯上限、route_name 形制）留活書。★島 G 之
   G1/G3/G4/G5 行為本刀先兌現、條文由 A1 域行為 ADR 承載、隨授權治理刀入憲（判例＝rev4
   拒絕把樹結構塞進島 G——一台狀態機一島）。設計以 state-machine 鏡頭（data-model §3 矩陣）。

**Post-Phase-1 複評**（design 產物齊後）：九題判定不變——Q1／Q3～Q6／Q8 PASS；Q2／Q7／Q9
維持「涉及、授權以 Amendment 先行取得」，授權鏈定形為 research R10 之 U1 硬閘（Amendment
accepted 前：不得動 base-web 既有檔、不得落任何憲法接觸面碼；純後端 U2~U8 可先行——但慣例
沿 004＝U1 排最前）。design 階段新增憲法接觸面＝零。★GATE 狀態＝**條件通過**。

## Project Structure

### Documentation (this feature)

```text
specs/005-role-menu-crud/
├── spec.md              # /speckit-specify（已收、含 clarify 三題）
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R10）
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1（驗證指南）
├── contracts/           # Phase 1
│   ├── wire-role-admin.md
│   ├── wire-menu-admin.md
│   └── msg-keys.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks（未生成）
```

### Source Code (repository root)

```text
rust-api/server/src/
├── auth/enforce.rs          # 改：註解翻案＋rebuild_enforcer/reload_enforcer 新建
├── handler/
│   ├── role.rs              # 新：role CRUD 6＋roleHome 2 handler
│   ├── menu.rs              # 新：menu CRUD 7＋getMenuTree handler
│   └── ip_rule.rs           # 改：PageRes 上移後改引 envelope
├── envelope.rs              # 改：PageRes 落戶
├── router.rs                # 改：+16 條 ROUTES、ROUTES_COUNT 22→38
├── model/
│   ├── audit.rs             # 改：AuditOperation 詞彙定案釘子（T005：零新 variant、entity_table 區分）
│   └── facade/
│       ├── sys_role.rs      # 改：CRUD 寫端＋鎖讀 helper＋SEEDED_ROLE_IDS 常數
│       ├── sys_menu.rs      # 改：治理域讀端＋樹寫端＋狀態機守門
│       ├── sys_casbin_archive.rs  # 新：歸檔寫入面＋reason gate＋域鎖底座＋移除面掃描
│       │                          #   （獨立政策 facade 留授權治理刀；analyze I2 修正）
│       └── mod.rs           # 改：掛新模組
└── tests/（既有整合測樹）    # 擴：contract case＋守門矩陣＋併發機器證＋同步四測

base-web/src/
├── service/api/rev5-role-admin.ts   # 新（WRAPPER 軌道）
├── service/api/rev5-menu-admin.ts   # 新
├── typings/rev5-role-admin.d.ts     # 新（ADAPT 軌道）
├── typings/rev5-menu-admin.d.ts     # 新
├── views/manage/role/{index.vue,modules/role-operate-drawer.vue,modules/role-search.vue}   # 改（軌道 (ii)）
├── views/manage/menu/{index.vue,modules/menu-operate-modal.vue[,modules/shared.ts]}        # 改（軌道 (ii)）
└── locales/langs/{zh-cn,en-us}.ts＋typings/app.d.ts＋locales/langs/zh-tw.ts               # 改：i18n 三處
```

## Complexity Tracking

無憲法違規待豁免。三處刻意複雜度皆有拍板出處：①序列化域整域一把鎖（rev4:0051 論證：逐列
精緻鎖必漏；QPS≈0 零代價）②rebuild-swap 而非就地 reload（casbin 2.20.0 clear-then-load＝
全域鎖死風險，硬禁令）③deleteRole 入域（rev5 補 rev4 未論證併發窗，grilling 已拍）。
