# Implementation Plan: 008 稽核中心與系統設定頁（B-008 收官、audit 五端點）

**Branch**: `008-audit-settings-pages` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-audit-settings-pages/spec.md`

## Summary

把 B-008 餘兩張管理頁做成真功能：settings 頁純前端接線（後端 002 已備、既備 `rev5-settings`
接線層直接消費）；audit 頁四源四分頁＋水平線清理，後端新開 5 支端點（path×method 由 001 凍結
seed 預埋、零 migration 零 seed 變更）。技術路徑＝rev4 對應碼為預設藍本（重打字消化、六差異點
不帶回）：後端照 rev4 `audit.rs` 形（分頁 clamp、固定排序、寬鬆 query、enrich 批查、purge
固定守門序＋單交易自記）落 rev5 `handler/audit.rs`＋`Api.Audit.*` wire 三層測試；前端照 rev4
7 檔形落兩頁＋XFF 欄（ADR 0076 例外）；連帶 Lint24 佔位符擴腿（B-139）、`_with_db` 測試薄殼
＋purge/logout fault-injection（B-125）；U0 憲法 MINOR 先行（§III.2 用途 (vii)(viii)＋稽核域
行為島候選 user 親決）。

## Technical Context

**Language/Version**: Rust（rust-api；host 無 toolchain、build/test 一律容器內全程 serial）＋
TypeScript／Vue 3（base-web、soybean-admin fork）＋ Python 3（tools 治理面）

**Primary Dependencies**: axum＋sea-orm＋jsonschema（wire 裁判）；naive-ui＋@elegant-router/vue
（產物四檔重算）；tools/docs-sync.py（Lint24 擴腿掛點）

**Storage**: PostgreSQL——四稽核源表與索引（含兩支 pg_trgm GIN）001 既在；**零 migration**；
redis 不涉

**Testing**: 後端三層（handler 同檔真 DB 測〔容器內、分角色授權矩陣〕＋tests/contract.rs case
＋tests/wire_schema.rs 快照裁判）＋fault-injection（TableLock＋單連線 lock_timeout 池、經
`_with_db` 薄殼）；前端 `pnpm typecheck`；治理閘（fork-delta-lint／view-render-guard／
route-artifact-gate／seed-view-gate／docs-sync lint 29 條款）；驗收 CDP 三方對照＋
walkthrough-baseline 前後對賬

**Target Platform**: Linux 容器（compose dev stack；rev5 UI 22080／API 22079；rev4 對照 42080）

**Project Type**: web——前後端兩 submodule worktree（base-web／rust-api）＋傘狀層 tools/docs

**Performance Goals**: 管理頁無延遲 SLO（house style）；讀端 size clamp [1,100]＋固定排序走
001 既備索引（`created_at` 系＋pg_trgm）；效能引信照 ADR 0044 收刀例行量測

**Constraints**: 零 migration／零 seed 變更／零新 casbin 政策列；UI 對照 rev4 逐欄一致
（XFF 欄＝唯一例外、ADR 0076）；base-web inline 僅限 U0 開立之用途 (vii)(viii)＋既有
I18N-WIRING (ii)(iii) 射程；rev4 樹絕對唯讀

**Scale/Scope**: 後端 5 端點（ROUTES 61→66）＋前端 2 頁（audit 7 檔形＋settings 單檔）＋
`rev5-audit` 接線層新檔 2 支＋Lint24 一腿＋`_with_db` 薄殼＋3 支 fault-injection／同形測＋
憲法 MINOR 一次＋關帳六條

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*（對照 constitution
v1.9.1 §IV 九題）

1. **§I.1 base-web 為權威**：通過——本刀正是補齊 base-web 兩頁所需的全部後端（audit 5 支；
   settings 2 支既在）；seed `component` 指向之 view 兌現、seed-view-gate 豁免出列。
2. **base-web inline**：觸及。①§III.2 `BASE-WEB-MANAGE-PAGE-WIRING` **新用途 (vii)(viii)**
   （兩頁進場：兩語 locale route:/page: 兩樹＋app.d.ts page 型節＝新增型圈界；view 新檔檔頭
   標記不入名冊；產物四檔沿 (i) 產物檔紀律＋重算冪等檢查）——新 route 鍵＋新 page 節＋新
   view 檔＝「面」級新增、**不適用補完判準、須 §V.2 Amendment**（U0 先行、開立前零 base-web
   inline commit）。②`biz.audit.*` 拒因鍵入兩語 backend 樹＋app.d.ts backend 型節＝既有
   **I18N-WIRING (ii)(iii)** 射程（譯文權威＝本刀 contracts/msg-keys.md）；zh-tw.ts 治理錨同
   批補鍵（Lint24 射程、非 WIRING 名冊）。fork-delta 紀律全程：新增型圈界、`rev5-inline`
   token、重算冪等。
3. **§I.2 menu Casbin**：通過——兩頁 menu 維 seed 既在（僅 R_SUPER）、dynamic 模式、零
   hideInMenu 手段、零 seed 變更。
4. **§I.3 wire**：通過——分頁形 `PageRes<T>`（憲法字面）；碼復用 2222／5003／8888、零新碼；
   `msg`＝穩定 i18n key（`biz.audit.invalidTable`／`purgeBelowFloor`）；id 逐欄忠實 typings
   （i64→number、2^53 守衛）；`Api.Audit` typings＝wire 權威＋wire_schema 裁判＋contract
   coverage gate（每條新 route 必有 case）。
5. **§I.5 前代拷貝**：不拷貝——rev4 藍本重打字消化、註解重寫帶 `rev4:` 前綴；防回歸條款
   兌現＝spec §3 六差異點（XFF 渲染／DTO 欄名／access 空表／i18n 兩語／Api.Audit 獨立／PII
   打碼等價物）逐條不帶回 rev4 形；rev4 對應碼清單於 research.md §R1 凍結（ADR 0019）。
6. **§II 拍板**：不抵觸（#2 dynamic route mode 沿用；#1/#3 不涉）。
7. **§III ★ 軌道**：觸及＝第 2 題所列；判準明確落「新能力＝Amendment」側；§III.1 三軌道
   （ADAPT typings 新檔／WRAPPER service 新檔）照預設授權走。
8. **新業務表**：無（零 migration）。變體 B 紀律不受影響：purge 水平線刪除依 §I.6 變體 B
   括號句「retention 水平線刪除不屬竄改」——該句自載「權威釋義隨稽核域行為島入憲時載明」，
   U0 若拍入島、釋義隨島條文兌現。
9. **§I.7 行為島**：觸及候選——稽核域（rev4 十島承襲指針之「稽核域 reporting 與 retention」；
   K1-11／K1-57＝四源終態起手、本刀已兌現於 spec）。本刀 purge 域不變式候選（30 天下限／
   單交易自記／自記豁免／四值白名單／§I.6 變體 B 釋義）＝**U0 依 §IV 第 9 題判、user 親決**
   （spec FR-G02）。既入憲九島 A～I 不受影響：本刀零授權寫端、零 token／session／menu／user
   域寫入（purge 刪 session_event 稽核軌跡列＝retention 語意、非會話狀態機操作）。

**GATE 判定**：通過——條件＝U0 憲法 Amendment 先行（用途 (vii)(viii)＋行為島候選親決），
先於一切 base-web inline 與後端主體單元。無需 Complexity Tracking（零違規、零豁免申請）。

**Post-design 複核（Phase 0/1 後）**：新事實一件——`BizData` 通道射程現由 ADR 0064 嚴限
密碼二鍵，本刀 `purgeBelowFloor{minDays}` 走該通道＝射程擴一鍵；實質已由 grilling 拍板③
user 親決（第三攜參鍵）、形式承載＝**U0 立補充 ADR**（補充 ADR 0064 射程清單、error.rs
doc 同批改對；research D4）。九題判定不變、GATE 維持通過。

## Project Structure

### Documentation (this feature)

```text
specs/008-audit-settings-pages/
├── plan.md              # 本檔
├── research.md          # Phase 0（rev4 對應碼清單凍結＋差異點＋未知項收斂）
├── data-model.md        # Phase 1（四源讀模型＋DTO 對映；零 migration）
├── quickstart.md        # Phase 1（驗收動線：容器測試＋治理閘＋CDP 對照）
├── contracts/
│   ├── wire-audit.md    # Phase 1（Api.Audit 五端點契約）
│   └── msg-keys.md      # Phase 1（biz.audit 拒因鍵＋兩語譯文權威）
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks 產（非本命令）
```

### Source Code (repository root)

```text
rust-api/（worktree；容器內 serial）
├── server/src/handler/audit.rs        # 新檔：四讀端＋purge（rev4 藍本形）
├── server/src/router.rs               # 5 條 RouteDef＋ROUTES_COUNT 61→66
├── server/src/model/facade/…          # 四源讀 fn（現況與缺口見 research §R2）
├── server/tests/contract.rs           # 5 case 登記
├── server/tests/wire_schema.rs        # Api.Audit.* definition 裁判
└── server/…（test_db `_with_db` 薄殼＋refresh/logout fault-injection 同族）

base-web/（worktree）
├── src/views/manage/audit/            # 新目錄 7 檔（index＋4 搜尋卡＋purge modal＋daterange）
├── src/views/manage/system-settings/index.vue
├── src/service/api/rev5-audit.ts      # 新檔（WRAPPER 軌）
├── src/typings/api/rev5-audit.d.ts    # 新檔（ADAPT 軌、Api.Audit）
├── src/locales/langs/{zh-cn,en-us}.ts # route:/page:/backend 樹（WIRING 圈界）
├── src/locales/langs/zh-tw.ts         # backend 樹治理錨補鍵
├── src/typings/app.d.ts               # Schema.page 兩型節＋backend 型節
└── src/router/elegant/*＋typings/elegant-router.d.ts  # 產物四檔（外掛重算）

傘狀層
├── tools/docs-sync.py                 # Lint24 佔位符擴腿（B-139）
├── tools/seed-view-gate.py            # EXEMPT 摘兩列
├── .specify/memory/constitution.md    # U0 Amendment（用途 (vii)(viii)＋island 候選）
└── docs/arc42/decisions/              # U0 之 Amendment ADR（editorial：ADR 0076 已先行 accepted）
```

**Structure Decision**: 沿工作區既定拓樸（前後端兩 worktree＋傘狀治理層）；本刀零新
crate、零新頂層目錄；audit view 目錄結構照 rev4 7 檔形、settings 單檔形。

## Complexity Tracking

無——Constitution Check 零違規、零豁免申請。
