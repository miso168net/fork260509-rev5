# Implementation Plan: 003 auth 域整批——真登入、會話生命週期、節流＋驗證碼、dynamic 選單

**Branch**: `003-auth-session` | **Date**: 2026-08-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-auth-session/spec.md`（34 FR／11 SC；階段 0
brainstorm＋覆核輪＋Clarify 五題已收斂）

## Summary

把 base-web fork 原版 service 已在呼叫的認證／路由端點補齊到終態：真帳密登入（argon2＋
advisory lock＋鎖內重驗）、DB-stateful token rotation（partial UNIQUE 護欄＋30 秒 grace 冪等
窗）、帳號維三區節流（滑動窗為權威＋redis L1 負快取）、無狀態簽題圖形驗證碼、dynamic 側邊欄
（Casbin `menu` 維度過濾）、後端 msg 前端 `$t` 轉譯。ROUTES 4→16 條；`AppState` 兩欄→五欄；
`AppError` 6→9 變體；`dev_identity.rs` 整檔汰換使 release profile 首次可跑。

技術路線（research 定稿）：全面以 rev4 對應碼為藍本重打字消化（R2 三十九列清單），並以 R3
十六筆差異點清單防回歸；B-047 的 `method_not_allowed_fallback` 已在容器內以最小樣本實證，並
取得比 spec 預期更嚴格的組裝次序契約（R1）。預期**零 migration**（結構與 16 鍵 seed 全在 001
基線、零新 casbin 政策列），但本刀是 rev5 第一支會推進 append-only 表 sequence 的刀，須自帶
sequence 重設紀律（data-model §9）。

## Technical Context

**Language/Version**: Rust 1.96.1（容器內）／TypeScript 5.x＋Vue 3（base-web fork）

**Primary Dependencies**: axum 0.8.9／sea-orm／casbin（既有）＋本刀新進六支：argon2 0.5.3、
captcha 1.0.0、hex 0.4.3、jsonwebtoken 10.4.0（★`rust_crypto` feature 為硬需求）、redis 1.3.0
（`connection-manager`＋`tokio-comp`）、sha2 0.10.9（釘版雙源核對＝research R4）

**Storage**: PostgreSQL（001 基線結構、**零 migration**）＋Redis（denylist／last_activity／
rotate-grace／captcha nonce／節流 L1；★無 AOF＝已知態）

**Testing**: `cargo test --workspace -- --test-threads=1`（容器內、全程 serial）＋contract 16
case＋`pnpm typecheck`＋`fork-delta-lint`＋`docs-sync check`＋`schema-gate check`；base-web 側
**零測試框架**（前端執行單元的 TDD 迴圈退化為純 review 迴圈）

**Target Platform**: Linux 容器（dev stack 六業務件）；入口 `https://localhost:22443`
（front-nginx；★22081 直連 `/api` 必 404）

**Project Type**: web（rust-api 後端＋base-web 前端 fork，兩 submodule worktree）

**Performance Goals**: 無量化 SLA（dev workspace）；紀律面＝argon2 只在必要路徑跑一次（節流
與 captcha 拒絕一律在 argon2 **之前**擋下）、鎖內重驗不重跑 argon2、滑動窗子查詢必帶窗下界
（防全歷史回掃）

**Constraints**: 零 migration／零新 casbin 政策列／13 碼矩陣不動／★軌道未經 Amendment 授權前
不得動任何 base-web 既有檔／upstream rebase 友善（fork 差異全程 `rev5-inline` 標記）

**Scale/Scope**: 16 route（＋12）／9 AppError 變體（＋3）／6 facade（＋4 新增 2 擴充）／
22 i18n backend 鍵（＋6）／四條 ★ 軌道八個用途／五座 §I.7 行為島；估 45~60 個 T、14 個執行單元

## Constitution Check

*GATE: Phase 0 前初評（對憲法 v1.2.0）→ Phase 1 後複評（對 Amendment 後 v1.3.0）。*
*★本刀為 rev5 首刀踩到「須 Amendment」路徑（001／002 皆九題全過），Q2／Q7／Q9 之判定值
「涉及——授權以 Amendment 先行取得」係本刀自訂形制、無前例可抄。*

1. **§I.1 base-web 為權威**：**PASS with disclosure**——本刀為 base-web fork 原版 service 已在
   呼叫的 12 條端點補後端實作；回傳型逐欄忠實 typings（§I.3 權威序 1）。★揭露一處**排程延後**：
   fork 的 `service/api/auth.ts` 另呼叫 `/auth/error`（兩張 demo 頁消費），本刀不提供——依 §I.1
   「『v1 從簡』只能是交付排程」走排程錨（B-053＋spec Out of Scope 已具體化已知態），**非**設計
   範圍縮減；其兌現另有 §I.3 級前置衝突（保留碼 `9999` 三錨＋`msg` echo 通道），故不併本刀。
   驗收錨＝contracts/ 三檔＋wire-schema 快照消費（SC-001／SC-006）。
2. **§III.2 base-web inline**：**涉及——授權以 Amendment 先行取得**。本刀動 base-web 既有檔
   共 8 檔（`store/modules/route/index.ts`／`store/modules/auth/index.ts`／`pwd-login.vue`／
   三張替代登入表單／`hooks/business/captcha.ts`／`user-avatar.vue`／`service/request/index.ts`
   ／`typings/app.d.ts`／兩支 locale）＋`.env*` 四行。授權鏈＝**ADR draft → user 親決 →
   accepted ＋ §III.2 新增機器可解表格（四軌道八用途）＋ §I.7 五座島條文 ＋ bump 1.2.0→1.3.0
   ＋ `docs-sync generate`**（憲法 §V.2 四步）。★硬序約束：Amendment accepted **之前不得動任何
   base-web fork 既有檔**（FR-028）；`.env*` 四行走 §III.1 ADAPT 預設軌道（§II #2 明寫「ADAPT
   軌道」）＝零修憲，但仍須 `原行:` 標記（★該檔類在 fork-delta-lint 射程外＝人工紀律，FR-027
   已記已知態＋BACKLOG 新條目）。fork-delta 紀律：修改型帶原行註解、新增型圈界、全數含
   `rev5-inline` token。驗收錨＝`fork-delta-lint`（含本刀新增的名冊斷言、FR-030／031）。
3. **§I.2 menu 走 Casbin enforce**：PASS——`getUserRoutes` 以 DB-fresh roles 經 Casbin `menu`
   維度 `get_filtered_policy` 過濾 sys_menu 樹；demo menu 仍全集在 seed、不啟用 hideInMenu
   治理；constantRoutes 走 §I.2 末句「可經 §III.2 授權新增」＝**合併**而非取代（builtin 三頁
   不動、Casbin 豁免語意不變）。驗收錨＝SC-006。
4. **§I.3 wire 不變式**：PASS——信封三欄／`code` string／業務錯誤 HTTP 200（★新三變體落
   `http()` 的 `_ => OK` 萬用臂、零改動即成立）／`userId`＋`MenuRoute.id` 於序列化邊界轉字串
   （既有 `serialize_i64_as_string`）／13 碼矩陣不動（9 可發＋4 保留）／`msg` 載穩定 i18n key
   ／envelope 例外仍恰 2（B-047 是**消掉**未入文的第三種、非新增）。驗收錨＝contract 16 case
   ＋`error.rs` 六處斷言（research R7-3）。
5. **§I.5 前代 source**：PASS——零拷貝、重打字消化、註解一律 rev5 語境重寫（rev4 出處帶
   `rev4:` 前綴）；防回歸條款以 research R3 十六筆清單落地（每筆列出 rev4 行為與 rev5 拍板）。
   例外清單不適用（本刀無工具性 crate 整檔拷貝）。
6. **§II 設計拍板**：PASS——本刀**兌現** #2（`.env` `VITE_AUTH_ROUTE_MODE=dynamic`）與 #1
   （忽略 apifoxToken，contract case 釘住）、#3 `/api` 前綴拓樸不動，零抵觸。★但推翻三處**碼內
   舊拍板**（非 §II 條目）：`state.rs`「恰兩欄」封條、root `Cargo.toml`「不引 argon2」、
   `server/Cargo.toml` 不進清單——各須立 ADR 並同批改寫註解（research R4）。
7. **§III ★ 軌道**：**涉及——授權以 Amendment 先行取得**。四條軌道八個用途：
   `★BASE-WEB-LOGIN-CAPTCHA-WIRING`(i)／`★BASE-WEB-AUTH-WIRING`(a)(b)(c)／
   `★BASE-WEB-I18N-WIRING`(i)(ii)(iii)／`★BASE-WEB-LOGOUT-UX-WIRING`(i)。屬「**新能力**」而非
   §III.2 的「用途補完」（跨多頁、新 i18n 面級節、新元件行為）⇒ 須 Amendment，非 bump 豁免。
   ★連帶 ADR 0021 §3 收窄（`app.d.ts` backend 型節本刀提前；LangType／locale 註冊／zh-tw 標型
   重構仍延前端 UI 刀）。★順序相依：Amendment 須先定 §III.2 表格的機器可解形，FR-030 的名冊
   lint 斷言才寫得出來（research R8）。★憲法 §III.2 三必需欄位（位置＋改動內容＋upstream 衝突
   風險評估）齊備於 spec 之「★ 軌道逐處登記」表（15 列、附可覆算風險判準與 rebase 處置通則），
   該表同時是 Amendment ADR 的 §III.2「範圍（檔案）」欄輸入；★該表已揭露本刀最高風險面＝i18n
   三檔為基線最熱檔（近 12 月各 15–17 commit）。
8. **§I.6 業務表審計欄**：PASS（不觸發）——**零 create migration**；三張消費表（sys_token 變體
   C／session_event 與 sys_login_attempt 變體 B）皆 001 基線既有，本刀只寫入不改結構；append-only
   兩表零 update／delete。★連帶紀律：runtime 寫入會推進三支 sequence，須自帶重設守衛
   （data-model §9、非審計欄問題）。
9. **§I.7 行為島**：**涉及——授權以 Amendment 先行取得**。本刀落地五座島（token rotation／
   single-session／denylist 撤銷／idle 逾時／登入失敗節流），依 §I.7 進場規則須**同筆 MINOR
   Amendment** 將不變式與 fail-* 方向入憲（條文骨架＝research R8；完整矩陣＝research R5／
   data-model §8）。設計以 state-machine 鏡頭而非 CRUD 格子（data-model §1 為「現態×事件→次態
   ＋副作用」矩陣）。方向性反轉自此為 MAJOR。

**Post-Phase-1 複評**（design 產物齊後）：九題判定不變——Q1／Q3～Q6／Q8 全 PASS；Q2／Q7／Q9 維持
「涉及、授權以 Amendment 先行取得」且授權鏈已在 research R8 定形（§III.2 表格欄位＋§I.7 條文
骨架＋六筆 ADR 面）。design 新增之憲法接觸面＝零（Phase 1 三類產物皆為既有拍板的具象化；
R1 的組裝次序契約屬實作紀律、不觸憲法條文）。★**GATE 狀態＝條件通過**：Amendment（ADR
accepted＋bump 1.3.0）為 tasks 第一個 ★ 主線任務且為硬閘，未完成前 Q2／Q7／Q9 不得視為 PASS、
且不得動任何 base-web 既有檔。

## Project Structure

### Documentation (this feature)

```text
specs/003-auth-session/
├── plan.md              # 本檔
├── research.md          # Phase 0：R1~R9（含 R2 rev4 對應碼清單、R3 差異點清單）
├── data-model.md        # Phase 1：§1~§9（含 sys_token 狀態機矩陣）
├── quickstart.md        # Phase 1：§0~§7 驗證指南
├── contracts/
│   ├── wire-auth.md     # auth 面 9 條
│   ├── wire-route.md    # route 面 3 條＋動詞不符處置
│   └── msg-keys.md      # 22 鍵全集＋Lint24 算術自證
├── checklists/
│   └── requirements.md  # spec 品質檢核（16/16）
└── tasks.md             # Phase 2（/speckit-tasks 產出，非本命令）
```

### Source Code (repository root)

```text
rust-api/server/src/
├── auth/{jwt.rs(新), enforce.rs(改), mod.rs(改)}          # dev_identity.rs 整檔刪
├── cache/mod.rs(新)                                       # rev4 redis/mod.rs 縮編＋改名
├── throttle/mod.rs(新)                                    # 帳號維三區（IP 維全拔）
├── captcha/mod.rs(新)
├── handler/
│   ├── auth/{login,refresh,logout,user_info,alt_stub}.rs(新)
│   ├── route.rs(新)
│   └── captcha.rs(新)
├── model/
│   ├── password.rs(新)
│   └── facade/{sys_token,session_event,sys_login_attempt,sys_menu,sys_user,sys_role}.rs(新)
├── {state.rs, error.rs, router.rs, config.rs, request_context.rs, obs.rs}(改)
rust-api/server/tests/
├── contract.rs(改：4→16 case＋stub 連線改 sea-orm mock)
├── {authz_entrypoint_lint.rs, entity_access_lint.rs}(改：must-list 換檔)
└── common/mod.rs(改：stub_state 五欄)

base-web/
├── .env, .env.test, .env.prod                             # ADAPT 四行（原行標記）
└── src/
    ├── store/modules/{auth,route}/index.ts                # ★AUTH-WIRING(a)＋LOGIN-CAPTCHA(i)
    ├── views/_builtin/login/modules/{pwd-login,code-login,register,reset-pwd}.vue
    ├── hooks/business/captcha.ts                          # ★AUTH-WIRING(c)
    ├── layouts/modules/global-header/components/user-avatar.vue  # ★LOGOUT-UX(i)
    ├── service/request/index.ts                           # ★I18N-WIRING(i)
    ├── service/api/rev5-auth.ts(新)                       # WRAPPER 軌道
    ├── typings/{app.d.ts, api/rev5-auth.d.ts(新)}         # ★I18N-WIRING(iii)＋ADAPT
    └── locales/langs/{zh-tw,en-us,zh-cn}.ts               # ★I18N-WIRING(ii)＋22 鍵

tools/fork-delta-lint.py(改)                               # 軌道名 ∈ 名冊斷言
.specify/memory/constitution.md(改)                        # §III.2 表格＋§I.7 五島、1.3.0
```

**Structure Decision**: 沿 002 的兩子庫 worktree 結構，不新增頂層目錄。後端按**功能域分模組**
（`auth`／`cache`／`throttle`／`captcha`）＋handler 依端點群拆檔；`handler/auth/` 刻意拆目錄
而非單檔（rev4 為單檔約 860 生產行 ⇒ 防呆六件套⑥的「允許檔案清單」失去圈界力）。base-web 側
一律新檔優先（`rev5-` 前綴 wrapper／ADAPT typings），既有檔改動嚴限四條 ★ 軌道八用途之射程。

## Complexity Tracking

無 Constitution Check violation；本節空。

★判斷理由（本刀為首例，記於此以免 review 質疑該填表）：Q2／Q7／Q9 的「涉及」不是**違規**——
四條 ★ 軌道與五座 §I.7 行為島是循憲法 §V.2／§I.7 進場規則**正式取得授權**的路徑，憲法對此有
明文機制（§III.2「新用途一律走 §V.2 Amendment」、§I.7「隨其刀 brainstorm 拍板後以 MINOR
Amendment 入本節」）。Complexity Tracking 的用途是「必須被辯護的違規」，而走授權路徑者不屬此
類；真正需要記錄的是**授權鏈與硬序約束**，已寫在 Constitution Check Q2／Q7／Q9 與 research R8。
