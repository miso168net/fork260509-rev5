# Implementation Plan: B12 系統設定讀寫——後端首刀縱切管線

**Branch**: `002-system-settings` | **Date**: 2026-08-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-system-settings/spec.md`（Clarify Q1~Q3
已定案）＋docs/brainstorms/002-system-settings.md（設計九節）＋ADR 0018/0019/0020

## Summary

立 `rust-api/server` crate 打通「router→授權→handler→registry→DB→wire→前端接線層」
縱切管線，功能面＝系統設定 16 鍵讀＋寫。技術路徑＝**高度參照 rev4:004-system-settings
終態碼**（axum 0.8.9 全棧、RouteDef 註冊表、enforce 骨架、validation registry、facade
分層、oneshot 測試形——research R2 逐檔清單），依 R3 十二筆拍板差異點改判（三態
description、未知型 5000、未認證 8888、dev-only 查表 identity、無 op-log、六碼變體集
等）。前端腿＝typings＋service 兩新檔（ADR 0018 零修憲）；治理起手＝zh-tw.ts＋豁免
三筆處置（gen.msg_dict 走 ADR 0020 甲案修謂詞）；契約機器化＝wire-schema 三件
（K1-25）。零 migration。

## Technical Context

**Language/Version**: Rust（edition 2024、rust-toolchain.toml 既有釘定；容器內 build/test、全程 serial）＋TypeScript（base-web typings/service 新檔、不動既有碼）

**Primary Dependencies**: axum 0.8.9／serde 1.0.228／sea-orm 1.1.20（既有）／casbin 2.20.0＋vendored sea-orm-adapter（既有）／metrics 三件（R6）；dev-dep tower 0.5.3＋jsonschema 0.46.9——版本＝rev4 已驗證組合，進場時逐筆雙源對照（CLAUDE.md §6、R1）

**Storage**: PostgreSQL（既有 001 基線；system_settings 16 鍵 seed 在庫；零 migration）

**Testing**: cargo test 三層（純函式紅綠／oneshot 契約＋覆蓋閘／真 DB integration——R7）；容器內 `--test-threads=1`

**Target Platform**: Linux 容器（compose dev stack；六業務件）

**Project Type**: web-service（rust-api server crate）＋前端接線層（base-web 兩新檔）

**Performance Goals**: 無量化目標（16 鍵低頻治理面）；B-028 兩輪 build 時間量測隨刀交付（FR-027）

**Constraints**: 憲法 §I.3 wire 凍結面（信封／13 碼 reuse／msg=key）；§I.5 rev4 參照紀律（重打字消化＋註解重寫＋R3 防回歸清單）；§I.6 審計欄 facade 顯式成對寫；rust 全程 serial 容器內；review agent 只讀不寫

**Scale/Scope**: 4 routes／16 keys／2 DTO／6 AppError 變體；server crate 首落地＋傘狀 wire-schema.py＋base-web 3 新檔（typings/service/zh-tw.ts）

## Constitution Check

*GATE: Phase 0 前初評→Phase 1 後複評，兩評皆過。（憲法 v1.2.0 九題）*

1. **§I.1 base-web 為權威**：PASS——rust-api 提供 manage_system-settings 頁所需兩端點全套（讀＋寫、範圍不縮減）；wire 形對齊 typings 新檔權威；view 延後＝交付排程非設計縮減（ADR 0018 已拍）。
2. **base-web inline？**：PASS——恰三新檔（rev5-settings.d.ts／rev5-settings.ts／zh-tw.ts）、零既有檔改動。前二在 §III.1 ADAPT／WRAPPER 軌道；zh-tw.ts 屬治理契約既定錨點（啟動書 Day-1⑦跨端契約閘＋MSG_DICT_LOCALES 常量自創世錨定該路徑），純新增檔不觸 §III.2「base-web inline」授權射程，依 §III fork-delta 新增型紀律檔頭一行 `[rev5-inline …+]` 標記；en-us.ts 零改動（ADR 0020 甲案、user 拍板 2026-08-08）。
3. **menu Casbin enforce？**：PASS——不動 sys_menu／casbin seed；manage_system-settings 選單既 seed 且僅 R_SUPER；404 已知態持續（ADR 0018）。
4. **wire 對齊 §I.3？**：PASS——信封三欄宣告序／code string／business error HTTP 200（例外僅 4040/5003）／13 碼全 reuse 零新碼／4 保留碼＋3 未進場碼構造層不可發出（R3-9）／msg=穩定 i18n key＋Lint24 閉環／2^53 守衛通用件承襲；id 欄無（PK=string）；PageRes 不適用（R3-10）。
5. **前代拷貝？**：PASS——rust 應用碼全程重打字消化＋註解 rev5 語境重寫（rev4 出處帶 `rev4:` 前綴）；sea-orm-adapter 已 vendored（001、§I.5 例外）；wire-schema.py＝傘狀治理工具（§I.5 射程外）仍 rev5 座標重寫；防回歸＝R3 十二筆差異清單烤進實作單元 prompt。
6. **§II 拍板抵觸？**：PASS——#1 unknown header 忽略（contract case 附斷言）；#2 dynamic route mode 不觸；#3 route path 不帶 `/api` 前綴（front-nginx strip）。
7. **§III ★軌道？**：PASS——零 inline＝不觸 ★軌道；首個 ★軌道（view／i18n runtime 接線）依 ADR 0018/0020 延前端刀。
8. **新建業務表？**：PASS——零 migration（表＋seed 001 已在）；DDL 冒出＝FR-023 走 RUNBOOK §10 三步。
9. **§I.7 行為島？**：PASS——本刀無狀態機（registry 純驗證、enforce 消費 seed 政策皆非島）；K1-27 授權治理島（rev4 島 G）屬治理寫端刀、本刀僅 enforce 消費不入憲；零 §I.7 Amendment。

**Post-Phase-1 複評**（design 產物齊後）：九題判定不變、全 PASS；design 無新增憲法接觸面（data-model §7 兩拍板為 brainstorm 既拍轉錄、非新決策）。

## Project Structure

### Documentation (this feature)

```text
specs/002-system-settings/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R10＋K1 對照表回填）
├── data-model.md        # Phase 1（DTO／registry 16 鍵／ROUTES／錯誤映射／三態條文）
├── quickstart.md        # Phase 1（端到端驗證指南）
├── contracts/
│   └── wire-settings.md # Phase 1（兩端點契約／碼面斷言／快照與覆蓋閘）
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本命令）
```

### Source Code (repository root)

```text
rust-api/                          # worktree（rev5-admin-rust-api）
├── Cargo.toml                     # workspace members += "server"
└── server/
    ├── Cargo.toml                 # R1 依賴子集
    ├── src/
    │   ├── main.rs                # boot：config→db→enforcer→router→serve
    │   ├── lib.rs
    │   ├── config.rs              # APP_DATABASE_URL[_FILE]
    │   ├── router.rs              # ROUTES const（4 條）＋build（data-model §4）
    │   ├── state.rs               # AppState{db, enforcer}
    │   ├── envelope.rs            # Res＋2^53 守衛＋serialize_i64_as_string
    │   ├── error.rs               # 13 碼常量＋AppError 六變體（data-model §6）
    │   ├── obs.rs                 # recorder＋render＋axum-prometheus（R6）
    │   ├── validation.rs          # registry：validate＋NUMBER_RANGES（data-model §3）
    │   ├── auth/
    │   │   ├── mod.rs
    │   │   ├── enforce.rs         # MODEL_CONF／init_enforcer／enforce_mw／require_policy
    │   │   └── dev_identity.rs    # cfg(debug_assertions) 查表驗證器（R8）
    │   ├── request_context.rs     # B-019 seam 介面位（空殼、信任判定不進 handler）
    │   ├── handler/
    │   │   ├── mod.rs
    │   │   └── system_settings.rs # SettingItem／UpdateReq 三態／兩 handler＋mod tests
    │   └── model/
    │       ├── mod.rs
    │       └── facade/
    │           ├── mod.rs
    │           ├── system_settings.rs  # find_all／find_by_key／update_by_key
    │           └── sys_user_role.rs    # roles_of_user
    └── tests/
        ├── health.rs              # oneshot 基礎形
        ├── contract.rs            # case registry＋覆蓋閘（4 case）
        ├── wire_schema.rs         # 快照裁判（SettingItem／UpdateReq）
        ├── entity_access_lint.rs  # handler 零 entity:: 機器強制
        └── fixtures/wire-schema.json   # extract 產物（快照）

rust-api/entity/src/sys_user_role.rs   # B-014：Relation＋Related impl（既有檔補強）

base-web/                          # worktree（rev5-admin-base-web）
└── src/
    ├── typings/api/rev5-settings.d.ts # ADAPT 軌道新檔（wire 權威）
    ├── service/api/rev5-settings.ts   # WRAPPER 軌道新檔
    └── locales/langs/zh-tw.ts         # 治理契約錨點新檔（backend.* 起手鍵集＝R3-12）

tools/wire-schema.py               # 傘狀治理工具（extract／check／test；R5）
tools/docs-sync.py                 # gen.msg_dict 謂詞修改＋lint24.day1／gen.router 下架（FR-026）
```

**Structure Decision**: server crate 目錄形逐一對應 rev4 終態（R2 清單）以最小化參照
摩擦；rev5 縮編面（不建 redis/／throttle/／ipgate/ 等）＝R3 差異點的目錄級呈現。
dev_identity.rs 獨立檔（rev4 無對應——auth 刀汰換時整檔刪除、爆炸半徑最小）。

## Complexity Tracking

無 Constitution Check violation；本節空。
