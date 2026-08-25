# Implementation Plan: 007 使用者＋密碼管理（島 I 入憲、授權下放＋no-escalation）

**Branch**: `007-user-password-admin` | **Date**: 2026-08-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-user-password-admin/spec.md`

## Summary

把 rev5 第一個 user 域寫端家族從「seed 有政策列、碼與 UI 全無」做成真功能：管理面十支＋自助改密二支＝12 支端點
（ROUTES 49→61；seed 政策列 100% 預埋＝零 migration 零 seed 變更）、前後端同刀、CDP 三方對照驗收。本刀新拍板七件：
寫端授權可下放給多層管理員並以角色集包含規則守門（`T ⊆ A ∧ N ⊆ A`；持 R_SUPER 者 A＝全集；handler 鎖內具名純函式、
middleware 掛點續留）、斷權三腿（停用／刪除／重設同交易撤全部 active＋refresh 鎖內重驗＋踢除分鍵 7777
`admin_kick`）、密碼政策單一驗證點＋攜參明細通道（八鍵生效、`AppError::BizData` 唯二鍵、登入路徑不驗）、設密冷卻
（custody 只時戳）＋改密舊密節流（redis 5 次／15 分、fail-open 進觀測 source）、自助路由白名單帶回、軟刪硬刪指派＋
復原零回灌、登入表單降 required-only（B-089 結案）。憲法一次 MINOR v1.8.0→v1.9.0：§I.7 島 I 六條（含 rev5 新增 I7）＋
§III.2 三用途 (v)(vi)(vii)；ADR 五支。技術路徑＝高度參照 rev4:011-user-admin／rev4:014-user-center as-built 重打字消化
（ADR 0019；rev4 碼清單 research R1、差異點 R2 二十八點）；改密節流零藍本自建。同分支順路關帳 BACKLOG 十三條。

## Technical Context

**Language/Version**: Rust（workspace 既有 toolchain、容器內 build/test、全程 serial）＋TypeScript／Vue 3（base-web、pnpm）

**Primary Dependencies**: 零新依賴——argon2 0.5.3（`hash` 與既有 `verify` 同 crate、PHC 形）／redis 1.3.0（改密節流桶
沿既有連線管理）／sea-orm 1.1.20／axum 0.8.9／casbin 2.20.0（判定面同步純消費）；前端零新套件（naive-ui NDrawer／
NDropdown／NModal、useNaivePaginatedTable 既有；產密用 `crypto.getRandomValues`）

**Storage**: PostgreSQL（dev 容器）——`sys_user`／`sys_user_role`／`sys_pwd_custody`／`sys_token`／`session_event`／
`sys_operation_log`／`system_settings` 全為 001 基線既有表；兩支活性唯一索引基線現成；redis＝denylist（既有）＋改密節流
桶（新鍵前綴 `cpwd:`）

**Testing**: cargo test（容器內 serial；現 829 支）＋lint 型測家族（entity_access／authz_entrypoint 名冊閘／wire_i64_guard）
＋contract registry（50→62）＋wire-schema 裁判（75 definitions、本刀重抽）＋schema-gate 三閘＋fork-delta-lint＋
view-render-guard＋seed-view-gate＋docs-sync lint；`no_escalation.rs` 表驅動單元測；CDP 三角色實機對照（22080 vs 42080）

**Target Platform**: Linux 容器（dev compose stack 六容器；單副本＝ADR 0014）

**Project Type**: web-service（rust-api）＋web-app（base-web fork）雙腿同刀

**Performance Goals**: 管理面 QPS≈0；寫端每次多一次 advisory 鎖＋兩次角色集讀（A／T）與一次 `sys_role` code 查表，皆單列
級；changePassword 多一次 redis GET（precheck）；refresh 多一次 `sys_user` 單列讀（鎖內）；無新效能預算節，收刀依
RUNBOOK §12.1 實測 pre-commit 一筆

**Constraints**: 零 migration／零 seed 變更（硬預期）；Amendment 先行硬閘（accepted 前不得動 base-web 既有檔、不得落憲法
接觸面碼）；密碼政策 MUST NOT 掛登入路徑（seed 123456）；13 碼矩陣零觸碰（BizData 仍 2222）；denylist best-effort、
PG 權威；`kicked`／`admin_kick`／`revoked` 三 reason 不互換；前端不預判包含規則（G8）

**Scale/Scope**: 12 端點／島 I 六條入憲＋三用途／ADR 五支／後端新檔 5（handler/user.rs、handler/user_center.rs、
throttle/change_pwd.rs、auth/no_escalation.rs、facade/sys_pwd_custody.rs）＋擴 12 檔／前端修改型 inline 4（index.vue、
user-operate-drawer.vue、user-center/index.vue、pwd-login.vue）＋新檔 7（unlock modal、pwd-gen、password-card、typings×2、
service×2）＋順路 3 頁／i18n backend +21 鍵、page 樹 +~35 鍵／~10 執行單元（tasks 期定稿）

## Constitution Check

*GATE: Phase 0 前初評（對憲法 v1.8.0）→ Phase 1 後複評（對 Amendment 後 v1.9.0）。*

1. **§I.1 base-web 為權威**：**PASS（帶拍板記載）**——user 管理頁三檔與 user-center 為 upstream 既有 demo 面，其 fetch
   打的端點正是本刀補齊對象；wire 型依拍板落 rev5 獨立命名空間 `Api.UserAdmin`／`Api.UserCenter`（新檔）、使用者鍵
   `id`、status `'1'|'2'`、roles 為 code 集；權威鏈＝contracts 三檔凍結＋typings 同批＋wire-schema 重抽＋裁判。
2. **§III.2 base-web inline**：**涉及——授權以 Amendment 先行取得**。修改型＝`views/manage/user/index.vue`＋
   `modules/user-operate-drawer.vue`（(v)）、`views/user-center/index.vue`（(vi)）、`views/_builtin/login/modules/pwd-login.vue`
   （(vii)、既明文凍結位 LOGIN-CAPTCHA-WIRING (ii)）＋兩語 locale＋`app.d.ts`（圈界）；新增型新檔（unlock modal／
   pwd-gen／password-card／typings／service）不入名冊（ADR 0021）；B-129 走 (iii) 補完、B-132 走 (ii) 補完；
   `user-search.vue` 零改動不入名單。紀律＝修改型逐行 `原行:`（模板側多行註解形）、新檔檔頭 `[rev5-inline <軌道>+ 007]`。
   ★硬序：Amendment accepted 前不得動任何 base-web 既有檔（U0 硬閘；純後端 U1～U4 可先行）。
3. **§I.2 menu 走 Casbin enforce**：PASS——`manage_user`／`user-center` 選單列既在 seed；user-center 對非超管之可達走碼內
   自助白名單（承 rev4:ADR 0065、Q22 拍板、hide_in_menu 故側欄不現）——屬「受眾＝本人」的自助頁豁免、非 RBAC 資源頁；
   七枚按鈕碼 gating＝可見性由角色勾選層治理的正向消費；零 seed 改動。
4. **§I.3 wire 不變式**：PASS（帶新變體）——信封三欄／業務錯誤 HTTP 200／id 逐欄 i64 守衛／`msg` 載純 key；**13 碼矩陣
   零觸碰**：新增 `AppError::BizData(key, Value)` 仍映 `2222`、`msg`＝key、只多 `data` 載明細（唯二鍵、由新 ADR 承載；
   `Res::from_err` 仍 data null、`compile_fail` doctest 改寫為「帶資料只經 `from_err_with_data`」）；Lint24 白名單八鍵
   不得作 msg 發出（機器守既在）。
5. **§I.5 前代 source**：PASS——rev4 樹唯讀直讀、重打字消化零拷貝、註解 rev5 語境重寫（rev4 出處帶 `rev4:`）；防回歸以
   research R2 二十八點落地（含 clarify 三點：超管 A＝全集、roleIds 全量替換、觀測 source）。
6. **§II 設計拍板**：PASS——#1～#3 零抵觸；本刀推翻之碼內舊敘述＝`handler/route.rs` 檔頭「SELF_SERVICE_ROUTES 不帶回」句
   （改寫為「自本刀帶回」）、`model/password.rs` 檔頭「三支不搬」句、`sys_token.rs` 檔頭「revoke_all_of_user 不搬」句、
   `user_info.rs`／`enforce_mw` 不判 status 句不動（沿 003）。
7. **§III ★ 軌道**：**涉及——授權以 Amendment 先行取得**（同第 2 題）。三用途中 (v)(vi) 為既有軌道 `MANAGE-PAGE-WIRING`
   加用途、(vii) 為既有軌道 `LOGIN-CAPTCHA-WIRING` 之明文凍結位 (ii) 開立——皆非開新軌道；wrapper／typings 新檔走既有
   WRAPPER／ADAPT 軌道零修憲；zh-tw.ts 只補 backend 鍵。
8. **§I.6 業務表審計欄**：PASS（零 migration）——`sys_user` 六審計欄基線既有、寫端成對寫軟刪欄；`sys_user_role` join 變體
   無審計欄（硬刪／新增同交易、稽核由 `sys_operation_log` 承載）；`sys_pwd_custody` archetype C（`created_at／created_by`
   即業務語意欄、非審計欄）；★sequence：`sys_user_id_seq` 由 `UserCleanup` 還原 (3,true)、gate2 逐列全等（data-model §6）。
9. **§I.7 行為島**：**涉及——授權以 Amendment 先行取得**。本刀落地第九座島 I（六條；I7 為 rev5 新拍板），設計以
   state-machine 鏡頭（data-model §3 矩陣）；既有島保持：A（撤 active 不動 rotated、reuse 偵測不受擾）、B（kick 仍落
   事件＋denylist；新 reason `admin_kick` 與 `kicked` 並陳不互換）、C（`sys_token.status` 權威；refresh 鎖內重驗＝新增
   判定腿、fail 方向不變——ADR 明列非方向反轉）、E（改密節流獨立桶、fail-open 同向）、G4／G5（in-use 守門經 `count_by_role`
   不濾之語意由硬刪指派保真；跨刀鉤子句「刀 B 指派寫端落地時 MUST 同納鎖序」兌現）、H1（advisory key space 沿 uid 鍵、
   核過）。

**Post-Phase-1 複評**（research R1～R12／data-model／contracts 三檔／quickstart 齊後、2026-08-26）：九題判定不變——
Q1／Q3～Q6／Q8 PASS；Q2／Q7／Q9 維持「涉及、授權以 Amendment 先行取得」，授權鏈定形為 research R10 之 U0 硬閘。
design 階段新增憲法接觸面＝零（島 I I7 條文方向面之「超管 A＝全集」由 clarify Q1 定字、入 Amendment 草案）。
★GATE 狀態＝**條件通過**。

## Project Structure

### Documentation (this feature)

```text
specs/007-user-password-admin/
├── plan.md              # 本檔
├── research.md          # Phase 0：R1 rev4 對應碼清單／R2 差異點 28 點／R3～R12
├── data-model.md        # Phase 1：既有表消費面／記憶體實體／狀態機矩陣／島 I 骨架／錯誤碼／sequence
├── quickstart.md        # Phase 1：curl 契約面＋下放情境＋斷權＋密碼面＋容器內閘＋CDP
├── contracts/
│   ├── wire-user-admin.md    # 十支管理端點＋unlockLogin UI 接線
│   ├── wire-user-center.md   # changePassword／getPasswordPolicy
│   └── msg-keys.md           # backend.biz.user.* 21 鍵＋auth.session.kickedByAdmin＋page 樹候選
├── checklists/requirements.md
└── tasks.md             # Phase 2（/speckit-tasks）
```

### Source Code (repository root)

```text
rust-api/server/src/
├── router.rs                     # +12 RouteDef、ROUTES_COUNT 49→61
├── error.rs／envelope.rs         # +AppError::BizData、Res::from_err_with_data
├── obs.rs                        # THROTTLE_DEGRADED_SOURCES +redis_change_pwd（12→13）
├── auth/
│   ├── no_escalation.rs          # 新：ActorScope＋assert_no_escalation＋actor_scope_of（表驅動測）
│   └── enforce.rs                # enforce_mw reason→碼／鍵分派（admin_kick 新鍵）；no_escalation_check 不動
├── cache/mod.rs                  # +REASON_ADMIN_KICK；cpwd: 桶鍵
├── throttle/change_pwd.rs        # 新：改密舊密節流（precheck／record_failure／clear；fail-open＋降級 source）
├── handler/
│   ├── user.rs                   # 新：十支 handler＋begin_and_lock_user／finish_user_write／map_*_err
│   ├── user_center.rs            # 新：change_password／get_password_policy
│   ├── throttle.rs               # unlock_login 帳號維加 assert_no_escalation
│   ├── route.rs                  # +SELF_SERVICE_ROUTES 聯集
│   ├── common.rs                 # +wire_two_value_to_db（B-127 收攏；role.rs／menu.rs 改 import）
│   └── auth/refresh.rs           # 鎖內使用者活性重驗
├── model/
│   ├── password.rs               # +hash／PasswordPolicy／load_policy／validate_against_policy／VIOLATION_*
│   ├── audit.rs                  # vocabulary +kick／reset_password／change_password（釘值測改）
│   ├── mod.rs（test_db）          # UserCleanup 三腿、PwdCustodyCleanup、SessionRevokeCleanup
│   └── facade/
│       ├── sys_user.rs           # +寫端家族（insert／update／soft_delete／batch／kick／reset_password／set_session_policy／
│       │                         #   list／list_deleted／restore／change_own_password）＋advisory_lock_user 上提
│       ├── sys_user_role.rs      # +role_codes_all_of_user／replace_roles_of_user／delete_all_of_user／codes_of_role_ids
│       ├── sys_token.rs          # +revoke_all_of_user
│       ├── session_event.rs      # +EVENT_REVOKED＋五 reason（macro 單一宣告源）
│       └── sys_pwd_custody.rs    # 新：touch／last_set_at
rust-api/server/tests/
├── contract.rs                   # +12 ContractCase
├── authz_entrypoint_lint.rs      # RELOAD_CALL_FILES +handler/user.rs
├── wire_schema.rs                # +Api.UserAdmin.*／Api.UserCenter.* 裁判；fixtures/wire-schema.json 重抽
└── wire_i64_guard_lint.rs        # 新 wire 型 i64 欄守衛

base-web/src/
├── views/manage/user/index.vue                    # 修改型 (v)：接真＋回收桶 toggle＋NDropdown＋七碼 gating＋memo＋scroll-x
├── views/manage/user/modules/user-operate-drawer.vue   # 修改型 (v)
├── views/manage/user/modules/user-unlock-modal.vue     # 新增型（雙維）
├── views/user-center/index.vue                    # 修改型 (vi)：父層骨架＋只掛 password-card
├── views/user-center/modules/password-card.vue    # 新增型
├── views/_builtin/login/modules/pwd-login.vue     # 修改型 (vii)：pwd／userName → createRequiredRule
├── components/custom/pwd-gen-modal.vue            # 新增型
├── hooks/business/pwd-policy.ts                   # 新增型（buildPolicyRules）
├── typings/api/rev5-user-admin.d.ts／rev5-user-center.d.ts   # 新（ADAPT 軌道）
├── service/api/rev5-user-admin.ts／rev5-user-center.ts       # 新（WRAPPER 軌道）
├── locales/langs/{zh-cn,en-us}.ts（page.manage.user／page.userCenter／backend.biz.user／auth.session）＋zh-tw.ts（backend）
├── typings/app.d.ts                               # page／backend 型節（圈界）
├── views/manage/role/modules/*-auth-modal.vue     # 順路 B-129（(iii) 補完）
└── views/manage/menu/index.vue                    # 順路 B-132（(ii) 補完）

.specify/memory/constitution.md                    # U0：島 I 六條＋§III.2 (v)(vi)(vii)＋修訂日誌（v1.9.0）
docs/arc42/decisions/0063～0067                     # ADR 五支（實作期落檔）
docs/arc42/ARCHITECTURE.md＋FORK-DELTA-WIRING.md   # as-built（§5／§6／§8／§12＋附屬文件接線段）
```

**Structure Decision**: 雙腿同刀，沿 003～006 既有拓樸：後端新 handler 兩檔＋facade 擴＋兩個純函式新模組（no-escalation／
改密節流）；前端修改型限四檔（三用途檔級名單）、其餘一律新增型新檔；治理面 U0 先行。

## Complexity Tracking

無需填寫——Constitution Check 無未經授權之違反；三題「涉及」皆走 Amendment 授權鏈（非違反）。
