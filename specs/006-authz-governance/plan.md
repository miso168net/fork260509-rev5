# Implementation Plan: 006 三維授權治理＋結構性封死＋授權回收桶（島 G 入憲）

**Branch**: `006-authz-governance` | **Date**: 2026-08-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-authz-governance/spec.md`

## Summary

把角色管理的三顆授權 modal（選單／按鈕／端點）與授權回收桶自 upstream demo 殼接成真：11 支端點
（ROUTES 38→49；seed 政策列 100% 預埋＝零 migration 零 seed 變更）、前後端同刀、CDP 三方對照驗收。
純消費 005 三底座（選單序列化域／rebuild-swap 判定面同步／授權歸檔寫入面＋reason gate），本刀新拍板
三件：結構性封死（謂詞式、掛 updateRoleEndpoints 與 restorePolicy 鎖內）、手動撤銷之選單／按鈕維歸檔列
入不可復原集（reason gate 三值→五值、回收桶可復原列只剩端點維）、restorePolicy 固定序五腿重驗（列表
restorable 旗標與①②③④逐腿同判準）。憲法一次 MINOR（v1.7.0→v1.8.0）：島 G 六條入憲＋§III.2
`MANAGE-PAGE-WIRING` 加 (iii)(iv)＋ADR 0052 生成檔條款入 §III 正文＋島 H 兩處括號回填；ADR 三支
（0053 島 G 入憲／0054 結構性封死／0055 五腿＋ADR 0050 §4 復核）。技術路徑＝高度參照 rev4:009-role-admin
as-built 重打字消化（ADR 0019；差異點見 research R2）；起手維護批已先行（handler/common.rs、
test_db::test_state、wire-schema 裁判）——本刀新 handler 引用 common、零拷貝。

## Technical Context

**Language/Version**: Rust（workspace 既有 toolchain、容器內 build/test、全程 serial）＋
TypeScript／Vue 3（base-web、pnpm）

**Primary Dependencies**: 零新依賴——axum／sea-orm／casbin 2.20.0（rust-api/Cargo.toml:46 釘版、
`default-features = false`；版本錨不升版＝判定面同步硬禁令技術根據）／既有 sea-orm-adapter；前端零新
套件（naive-ui NTree／useNaivePaginatedTable 既有）

**Storage**: PostgreSQL（dev 容器）——`casbin_rule`／`sys_casbin_policy_archive`／`sys_role`／`sys_menu`
／`sys_operation_log` 全為 001 基線既有表；歸檔表讀端索引（`idx_casbin_archive_role_dim`／`archived_at`）
基線現成＝讀端零 migration；redis 不涉本刀新面

**Testing**: cargo test（容器內 serial；現 682 支）＋lint 型測家族（entity_access／authz_entrypoint 三名冊
閘／entity_behavior）＋contract registry＋coverage gate＋wire-schema 裁判（57 definitions、本刀重抽）＋
schema-gate 三閘＋fork-delta-lint＋view-render-guard＋route-artifact-gate＋docs-sync lint；CDP 實機
三方對照（22080 vs 42080、必要時 42089）

**Target Platform**: Linux 容器（dev compose stack；單副本＝ADR 0014、判定面同步不跨副本）

**Project Type**: web-service（rust-api）＋web-app（base-web fork）雙腿同刀

**Performance Goals**: 治理面 QPS≈0（三維寫端 diff 為集合運算、reload 全量重建秒級以內；rev4 論證
成立）；無新效能預算節（RUNBOOK §12 既有基線不受擾動）；列表讀端之 restorable 旗標以批次讀端算
（避免逐列查、不另添 B-106 同族新形；`archivedBy` enrich 沿既有 `resolve_operator_names`）

**Constraints**: 零 migration／零 seed 變更（硬預期；唯一已知威脅 ADR 0050 §4 條款已由 Q6 取 B 化解）；
menu／button 維寫端域鎖必為交易首動作、endpoint 維與 restorePolicy 不入域；protected 整批拒於任何寫之前；
封死守門鎖內現查；判定面同步 commit 後讀鎖全釋後觸發、失敗 keep-last-good 服務不中斷；憲法 Amendment
先行硬閘（accepted 前不得動 base-web 既有檔、不得落憲法接觸面碼）

**Scale/Scope**: 11 端點／島 G 六條入憲／ADR 三支／前端修改型 inline 3＋新增型新檔 3＋圈界 3＋產物 4
／backend i18n 鍵 50→53＋page 樹 17 鍵／~12 執行單元（tasks 期定稿）；seed 選單 78 列、政策 163 列不動

## Constitution Check

*GATE: Phase 0 前初評（對憲法 v1.7.0）→ Phase 1 後複評（對 Amendment 後 v1.8.0）。*

1. **§I.1 base-web 為權威**：**PASS（帶拍板記載）**——三顆授權 modal 與 policy-archive 頁為 upstream 既有
   demo 面或 rev4 已驗證形，其 fetch 打的端點正是本刀補齊對象（「fork 有而後端缺」正向補齊；menu 頁之
   getAllPages 現況恆 4040 即同一形）。wire 型依拍板落 rev5 既有命名空間（`rev5-role-admin.ts`／`.d.ts`
   追加、policy-archive 新命名空間）、角色鍵 `id`、三支讀端帶 `protected`；權威鏈＝本刀 contracts 凍結＋
   typings 同批＋wire-schema 重抽。驗收錨＝`contracts/wire-authz-governance.md`＋`wire-policy-archive.md`
   ＋msg-keys＋wire-schema 快照＋新裁判。
2. **§III.2 base-web inline**：**涉及——授權以 Amendment 先行取得**。本刀動 base-web 既有檔＝
   `menu-auth-modal.vue`／`button-auth-modal.vue`（修改型、逐行 `原行:`）＋`role-operate-drawer.vue`
   （增量、同檔雙用途）＋兩語 locale＋`app.d.ts`（圈界）；新增型新檔＝`endpoint-auth-modal.vue`＋
   policy-archive 兩檔（不入名冊）；產物四檔沿 (i) 列紀律；`ip-rule/index.vue`（rev5 新增型新檔、零標記）。
   授權鏈＝ADR draft → user 親決 → accepted＋§III.2 加 (iii)(iv)＋§I.7 島 G＋bump 1.7.0→1.8.0＋
   `docs-sync generate`。★硬序：Amendment accepted 前不得動任何 base-web 既有檔（U1 硬閘；純後端單元可先行）。
3. **§I.2 menu 走 Casbin enforce**：PASS——本刀正是「可見性由角色勾選層治理」的第二步工具
   （updateRoleMenu）；零 seed 改動、動態選單模式不變。已知態（menu 維四列 protected 可授予 R_ADMIN
   可見性、端點仍 5003）＝誠實結果非違反。
4. **§I.3 wire 不變式**：PASS——信封三欄／業務錯誤 HTTP 200／id 逐欄忠實（i64→number 2^53 守衛沿用）／
   `msg` 載純 i18n key／**13 碼矩陣零觸碰**（封死與整批拒皆 `2222`＋新 key、`5003`／`5000` 既有）；
   `PageRes` 沿 envelope 既有；`protected` 旗標為新增布林欄、typings 先行。
5. **§I.5 前代 source**：PASS——rev4 樹唯讀直讀、重打字消化零拷貝、註解 rev5 語境重寫（rev4 出處帶
   `rev4:`）；防回歸以 research R2 十三點落地（BizData／BlockedTarget／roleId／無條件 reload／caller 傳
   role_id／刪除集重跑過濾／roleHome 形／hasAuth gating／具名歸檔 fn／restorePolicy 無條件入域／
   rev4 兩腿復原重驗／明細 DETAIL 對照表）。
6. **§II 設計拍板**：PASS——既有三拍板零抵觸；本刀推翻之碼內舊敘述＝`enforce.rs` 觸發矩陣 doc 之
   括號句（B-104、隨島 G 入憲 ADR〔編號 0053〕訂正）與 `sys_casbin_archive.rs:34-36` 模組 doc 失真句（同檔順修）。
7. **§III ★ 軌道**：**涉及——授權以 Amendment 先行取得**（同第 2 題）。屬既有軌道 `MANAGE-PAGE-WIRING`
   加用途、非開新軌道（Q13 拍板）；wrapper／typings 追加走既有 WRAPPER／ADAPT 軌道零修憲；zh-tw.ts 為
   rev5 純新增檔不觸 ★ 軌道。
8. **§I.6 業務表審計欄**：PASS（零 migration）——`casbin_rule`（變體 D、11 欄）與歸檔表（變體 D、14 欄
   含 `role_id`）皆基線既有；本刀 grant 寫入補齊治理欄、revoke 走 archive-move；★sequence 紀律：
   `casbin_rule_id_seq` (163,true)／archive seq (1,false) 由 CasbinCleanup 還原、gate2 逐列全等
   （data-model §6）。
9. **§I.7 行為島**：**涉及——授權以 Amendment 先行取得**。本刀落地第八座島（島 G casbin 授權治理、
   六條）：G1 DB-first＋判定面同步方向面與失敗契約／G2 protected 整批拒＋拒因可辨一因一鍵／G3 連動
   歸檔（deleteRole 已兌現半＋grant/revoke 半）／G4 選單維錨與候選同源／G5 固定鎖序＋復原同實例＋跨刀
   鉤子／G6 結構性封死（rev5 新拍板）；島 H H1 終態成員句與 header 括號 PATCH 回填。MAJOR 界定照
   rev4:ADR 0048 字面；觸發矩陣本體與常數留 ADR／活書。設計以 state-machine 鏡頭（data-model §3 矩陣）。
   ★既有島 H 各 invariant 保持（H1 成員擴列為條文預告之終態、H2 零破口由 Q6 拍板保證、H4 候選集含停用）。

**Post-Phase-1 複評**（research R1～R12／data-model／contracts 三檔／quickstart 齊後、2026-08-23）：九題判定不變——Q1／Q3～Q6／Q8
PASS；Q2／Q7／Q9 維持「涉及、授權以 Amendment 先行取得」，授權鏈定形為 research R10 之 U1 硬閘
（Amendment accepted 前：不得動 base-web 既有檔、不得落憲法接觸面碼；純後端 U2～U7 可先行——慣例沿
005＝U1 排最前）。design 階段新增憲法接觸面＝零（ADR 0052 條款入 §III 正文屬 Q13／FR-051 既列項）。
★GATE 狀態＝**條件通過**。

## Project Structure

### Documentation (this feature)

```text
specs/006-authz-governance/
├── spec.md              # /speckit-specify（已收、含 clarify 一題）
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R10）
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1（驗證指南）
├── contracts/           # Phase 1
│   ├── wire-authz-governance.md   # 三維六支＋支撐讀三支
│   ├── wire-policy-archive.md     # 回收桶兩支
│   └── msg-keys.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks（未生成）
```

### Source Code (repository root)

```text
rust-api/server/src/
├── auth/enforce.rs                 # 改：觸發矩陣 doc 訂正（B-104）＋grant 面刻意例外句；reload 呼叫者 3→7
├── handler/
│   ├── role.rs                     # 改：+9 支（三維六支＋支撐讀三支；8→17 支）、引用 common::*
│   ├── policy_archive.rs           # 新：回收桶兩支（獨立檔、ASCII 序插 menu 與 role 之間）
│   └── mod.rs                      # 改：註冊 policy_archive、doc 同步
├── router.rs                       # 改：+11 條 ROUTES、ROUTES_COUNT 38→49
├── envelope.rs                     # 改：+serialize_opt_i64_number_guarded（roleId number|null）
├── model/
│   ├── facade/
│   │   ├── sys_casbin_policy.rs    # 新：三維 grant/revoke 寫端＋讀端（全量替換 diff、protected 整批拒、orphan skip、封死守門）
│   │   ├── sys_casbin_archive.rs   # 改：list（雙濾＋旗標）／restore（五腿）／批次旗標料源／reason gate 五值／:34-36 doc 順修
│   │   ├── sys_menu.rs             # 改：+all_button_codes（治理域聯集、公開）
│   │   ├── sys_role.rs             # 改：+活性角色批次讀端（旗標同實例半料源）
│   │   └── mod.rs                  # 改：掛新模組
│   └── mod.rs                      # 改：test_db 視需要增守衛 helper（CasbinCleanup 既有）
└── tests/
    ├── contract.rs                 # 擴：11 支 contract case＋授權態矩陣
    ├── authz_entrypoint_lint.rs    # 改：RELOAD_CALL_FILES 擴列（menu.rs／policy_archive.rs／role.rs）
    ├── wire_schema.rs              # 擴：新命名空間裁判（三維型＋policy-archive）
    ├── menu_domain_serialization.rs# 擴：兩支入域寫端 NOT-granted 機器證
    └── fixtures/wire-schema.json   # 重抽（跨子庫兩段式 commit）

base-web/src/
├── views/manage/role/modules/
│   ├── menu-auth-modal.vue         # 改（修改型、原行:）：接 getRoleMenu／updateRoleMenu＋roleHome UI＋getAllPages 接真
│   ├── button-auth-modal.vue       # 改（修改型、21 條原行）：接 getRoleButton／updateRoleButton＋getAllButtons
│   ├── endpoint-auth-modal.vue     # 新（新增型新檔）
│   └── role-operate-drawer.vue     # 改（增量）：第三顆鈕＋掛載 endpoint modal
├── views/manage/policy-archive/{index.vue,modules/policy-archive-search.vue}   # 新（新增型新檔）
├── views/manage/ip-rule/index.vue  # 改（rev5 新增型檔、零標記）：B-099 default slot 保底
├── service/api/rev5-role-admin.ts  # 改：+三維六支＋支撐讀三支＋roleHome 兩支＋回收桶兩支 fetcher
├── typings/rev5-role-admin.d.ts    # 改：+對應型（含 protected 旗標、policy-archive 型）
├── locales/langs/{zh-cn,en-us}.ts＋typings/app.d.ts   # 改（圈界）：backend 3 鍵＋page.manage.policyArchive 15＋role.endpointAuth 1＋route 1
├── locales/langs/zh-tw.ts          # 改（純新增檔增量）：backend 3 鍵
└── router/elegant/{imports,routes,transform}.ts＋typings/elegant-router.d.ts   # 產物四檔重算（不手改）

.specify/memory/constitution.md    # Amendment v1.8.0（U1、主線親做）
docs/arc42/decisions/{0053,0054,0055}-*.md   # 新
docs/arc42/ARCHITECTURE.md         # §5／§8 as-built＋§6 errata「六座」→「八座」
tools/seed-view-gate.py            # 新：B-088 對賬閘（seed view.* ⊆ 前端 view 集；具名豁免 seed 9／77 附 B-008 指針；research R8-12）
.githooks/pre-commit／tools/bootstrap.sh／README.md／tools/docs-sync.py TOOLS_PY   # 改：seed-view-gate 接線與納冊（Lint27 樹對賬）
docs/ops/RUNBOOK.md                # 改：回收桶復原／封死拒因查法指針（T036）
```

**Structure Decision**: 沿 005 既有雙腿佈局；後端依 rev4 藍本落兩個新檔（facade/sys_casbin_policy.rs、
handler/policy_archive.rs）、其餘為既有檔增量；前端三 modal 同目錄、policy-archive 新目錄
（component 字面 `view.manage_policy-archive` 決定）。

## Complexity Tracking

無憲法違規待豁免。四處刻意複雜度皆有拍板出處：①全量替換 diff 而非增量介面（rev4:FR-017；UI 樹勾選即
期望全集、增量介面反而多一套語意）②protected 整批拒先於任何寫（島 G2；零變更保證與零 migration 承重前提）
③封死謂詞式 DB 態鎖內現查而非靜態守恆（Q22：避免與 runtime 第二套字面同源）④restorePolicy 五腿固定序
而非 rev4 兩腿（Q7：rev4 洞不帶進 rev5、ADR 0051 取態同構）。
