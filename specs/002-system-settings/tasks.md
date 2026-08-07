# Tasks: B12 系統設定讀寫——後端首刀縱切管線

**Input**: Design documents from `/specs/002-system-settings/`

**Prerequisites**: plan.md、spec.md（US1~US5）、research.md（R1~R10）、data-model.md、contracts/wire-settings.md、quickstart.md

**Tests**: 含測試任務——spec 明定 TDD＋契約測試紅綠（憲法 §I.4；每實作 task 內先紅後綠）。

**Organization**: 依 user story 分 phase；每 phase 獨立可測、可增量交付。

## Format: `[ID] [P?] [Story] Description`

## 全程紀律（每 task 隱含、不逐條重複）

- ★實作前先讀 R2 清單對應之 rev4 碼（`git -C fork260509-rev2-anew-rust-api show origin/rev4-admin-rust-api:<path>` 唯讀）；高度參照、重打字消化、註解一律 rev5 語境重寫（rev4 出處帶 `rev4:` 前綴）；R3 十二筆差異點不得帶回 rev4 已推翻行為（ADR 0019）。
- rust build/test 一律容器內、`--test-threads=1` serial；★絕不 push/merge。
- 兩段式 commit：worktree 內 commit → 單元邊界回傘狀 `git add <子庫>` bump pin＋傘狀 commit。
- ★Lint24 同步律：zh-tw.ts `backend.*` 鍵集必須＝後端實發集（少鍵＝缺譯紅、多鍵＝孤兒紅）——新 msg key 與 zh-tw.ts 增鍵恆同單元落地。

---

## Phase 1: Setup

**Purpose**: 動工前量測基線＋工具與依賴地基（先於 server 首支 .rs）

- [ ] T001 B-028 第一輪量測（★動工前、server 依賴未進場態）：容器內冷編（清 rust_api_target 卷後 `cargo build --workspace`）＋單檔增量（touch entity 一檔重 build）各計時；數據暫存 scratchpad、落帳歸 T030
- [ ] T002 [P] 重寫傘狀 `tools/wire-schema.py`（承 rev4 傘狀同名工具形、rev5 座標化：分支名／worktree 路徑／容器名；extract／check（含 `--staged-gate`）／test 三子命令、python 標準庫單檔）＋`python3 tools/wire-schema.py test` 自帶測試綠（離線、不需 stack）
- [ ] T003 [P] rust-api workspace 加 server member：`rust-api/Cargo.toml` members＋`rust-api/server/Cargo.toml` 依賴子集（research R1 表；★逐筆雙源對照 rev4 lockfile vs crates.io latest stable，同值採用回報、分歧停手升 user）＋最小可編譯 `server/src/main.rs` 骨架；容器內 `cargo build` 綠；worktree commit（pin bump 延至 T011 組合拳）

---

## Phase 2: Foundational（阻塞全部 user story）

**Purpose**: server 基座全件＋治理組合拳＋六件起得齊——管線存在性

- [ ] T004 `rust-api/server/src/envelope.rs`（Res 三欄宣告序＋2^53 守衛＋serialize_i64_as_string；不含 PageRes——R3-10）＋`error.rs`（13 碼常量 mod 全列＋AppError 六變體＝data-model §6；1000/3333/7777＋4 保留碼無變體）＋in-crate 碼映射測試（先紅後綠）
- [ ] T005 [P] `rust-api/server/src/config.rs`（APP_DATABASE_URL[_FILE] 讀取）＋`state.rs`（AppState{db, enforcer: Arc<RwLock<Enforcer>>} 恰兩欄）
- [ ] T006 [P] `rust-api/server/src/auth/`：enforce.rs（MODEL_CONF／init_enforcer／enforce_role_path_method 單一純函式進入點＋空 no-escalation 掛點／require_policy DB-fresh；不搬 denylist/reload——R3-8）＋dev_identity.rs（`#[cfg(debug_assertions)]` 查表 dev-super→1／dev-admin→2／dev-user→3、缺席或未知 token→8888——R8；獨立檔、auth 刀整檔汰換）＋mod.rs；判定純函式單元測先紅後綠
- [ ] T007 [P] `rust-api/server/src/request_context.rs`（B-019 seam 介面位空殼、信任判定不進 handler）＋`model/facade/sys_user_role.rs`（roles_of_user）＋`model/facade/mod.rs`＋`model/mod.rs`
- [ ] T008 `rust-api/server/src/obs.rs`（recorder＋render＋axum-prometheus layer——R6）＋`router.rs`（RouteDef 六欄／Protection 三態／ROUTES 起手＝/health＋/metrics 兩條／build 迭代註冊）＋`handler/mod.rs`（依賴 T004~T006）
- [ ] T009 `rust-api/server/src/main.rs`＋`lib.rs` boot 鏈（config→db→init_enforcer→router build→serve；tracing-subscriber json）；容器內 build 綠、watchexec 起得來
- [ ] T010 `rust-api/server/tests/`：health.rs（oneshot 基礎形）＋contract.rs（case registry＋ROUTES 雙向覆蓋閘＋health/metrics 兩 case＋Policy 路由無標頭→8888 oneshot 免 DB 形）＋entity_access_lint.rs（handler 零 `entity::` 機器強制）；容器內 cargo test 綠（serial）
- [ ] T011 ★治理組合拳（單一傘狀 commit 收攏、防 Lint24/Lint20 中間態紅）：①base-web worktree 建 `base-web/src/locales/langs/zh-tw.ts`（`backend.*` 起手五鍵＝error.rs 實發集：common.success／system.notFound／system.forbidden／system.internal／auth.session.reLogin；fork-delta 新增型檔頭一行標記）＋worktree commit ②傘狀 `tools/docs-sync.py`：下架 lint24.day1＋gen.router 兩筆 Day-1 豁免、gen.msg_dict 解除謂詞改「兩語皆含 backend 樹」（ADR 0020 甲案）＋DAY1_EXEMPTIONS 註解改寫、docs-sync 自測綠 ③同一傘狀 commit：bump base-web＋rust-api 兩 pin＋`python3 tools/docs-sync.py generate`（routes 真表首算）→pre-commit lint 全綠
- [ ] T012 六業務件 `up -d --wait` 起得齊驗證（migrate 閘後 server 常駐、front-nginx healthy＝/health 經 proxy 回 ok、`/metrics` 有 exposition）＋撤除 `docs/ops/RUNBOOK.md` §1 步 5「B12 之前跑不完」已知態註記（傘狀 commit）

**Checkpoint**: 管線骨架可跑、治理閘全綠——user story 實作解鎖

---

## Phase 3: User Story 1 — 讀端管線全通（P1）🎯 MVP

**Goal**: R_SUPER 一次讀取 16 鍵全集，七環管線每環有真實流量

**Independent Test**: 起 stack、dev-super 呼叫讀端、回包與 seed 定稿逐鍵全等（quickstart §1）

- [ ] T013 [US1] base-web typings 新檔 `base-web/src/typings/api/rev5-settings.d.ts`（declaration merging 併入 Api.SystemManage：SystemSetting 四欄＋UpdateSystemSettingReq 三態形——contracts §5、data-model §1/§2；檔頭 fork-delta 標記）；worktree commit＋傘狀 pin bump
- [ ] T014 [US1] `python3 tools/wire-schema.py extract` 首抽（需 stack 在跑）→`rust-api/server/tests/fixtures/wire-schema.json` 落地＋`check` 綠；rust-api worktree commit
- [ ] T015 [US1] `rust-api/server/src/model/facade/system_settings.rs`：find_all（`deleted_at IS NULL` filter——R3-6、settingKey 升冪）；純函式／facade 測試先紅後綠
- [ ] T016 [US1] `rust-api/server/src/handler/system_settings.rs`：SettingItem（camelCase、審計欄不上 wire、description skip_if_none）＋get_system_settings＋router.rs 掛 `GET /systemManage/getSystemSettings`（Policy）＋contract.rs 補 get-system-settings case＋`tests/wire_schema.rs`（SettingItem vs 快照 `Api.SystemManage.SystemSetting` 裁判）
- [ ] T017 [US1] handler `mod tests` 真 DB integration（沿 rev4 real_app oneshot 形）：dev-super 讀回 16 鍵與 seed 定稿全等／dev-admin→5003／無標頭→8888（SC-001、US1 場景 1~3）；容器內 cargo test 綠
- [ ] T018 [US1] base-web service 新檔 `base-web/src/service/api/rev5-settings.ts`：fetchGetSystemSettings（直接路徑 import、不經 barrel；檔頭標記）；worktree commit＋傘狀 pin bump（單元邊界）

**Checkpoint**: US1 獨立可驗——MVP 達成

---

## Phase 4: User Story 2 — 寫端合法路徑（P2）

**Goal**: 單鍵更新經 registry 驗證＋正規化落庫、審計欄成對

**Independent Test**: 合法更新後回讀＝canonical 新值＋updated_at/by 非空（quickstart §3 首例）

- [ ] T019 [US2] `rust-api/server/src/validation.rs`：validate(setting_key, setting_type, value)→canonical＋NUMBER_RANGES 10 鍵 const（data-model §3 原值）＋enum 精確成員＋未知型→Internal 5000（★R3-2 差異、勿帶回 rev4 2222）＋未宣告 number 鍵 fail-loud 拒；TDD 紅綠矩陣（每型合法／非法／未知型）；★同單元 base-web zh-tw.ts 加 biz.systemSettings.invalidValue／biz.systemSettings.notFound 二鍵（Lint24 同步律）＋兩側 worktree commit
- [ ] T020 [US2] facade `system_settings.rs` 補：find_by_key（miss→Ok(None)）＋build_update_active_model（純測 seam、now 注入、§I.6 updated_at/by 成對）＋update_by_key（★無 op-log——R3-5；description 三態參數）；純函式測先紅後綠
- [ ] T021 [US2] handler 補：UpdateSystemSettingReq（三態承載型 `Option<Option<String>>`＋default——data-model §2）＋update_setting（解析→registry 驗證→facade→`Res::ok(())`；未知鍵→Biz notFound 2222）＋router 掛 `POST /systemManage/updateSystemSetting`（Policy）＋contract.rs 補 update-system-setting case＋wire_schema.rs 補 UpdateSystemSettingReq 裁判
- [ ] T022 [US2] integration（handler mod tests）：number `"+10"`→`"10"` 正規化落庫＋enum 更新＋審計欄成對＋回讀一致（SC-002、US2 場景 1~3）；容器內 cargo test 綠
- [ ] T023 [US2] service `rev5-settings.ts` 補 fetchUpdateSystemSetting（三態 req 型別完備）；worktree commit＋傘狀 pin bump（單元邊界）

---

## Phase 5: User Story 3 — 寫端驗證失敗路徑（P2）

**Goal**: 非法寫入一律拒收零寫入、碼與 msg key 正確

**Independent Test**: 逐形注入非法值、斷言碼＋原值保留（quickstart §3 後三例）

- [ ] T024 [US3] integration 失敗矩陣（handler mod tests）：型別不符／超範圍／enum 外→2222 invalidValue、未知鍵→2222 notFound、庫中手植未知 setting_type 列→5000（US3 場景 4；測試內 SQL 植入異型列後還原）——全案回讀斷言原值保留零寫入（SC-003）；容器內 cargo test 綠；rust-api worktree commit＋pin bump

---

## Phase 6: User Story 4 — 越權拒絕與授權骨架定形（P2）

**Goal**: 「有鈕無政策」組合正確拒絕、拒絕語意 ADR 定死（B-024 前置）

**Independent Test**: 兩身分×兩端點授權矩陣全數符合 ADR 定稿（quickstart §2）

- [ ] T025 [US4] 立 `docs/arc42/decisions/0021-write-authz-denial-semantics.md`（draft→user 過目→accepted）：R_ADMIN 有 user:edit 鈕無寫端政策組合之拒絕語意＝5003＋錯誤明細粒度＝Biz 純 i18n key 形起步（無結構化明細、BizData 形留擴充）＋no-escalation 空掛點語意（B-024 seam 邊界）；`python3 tools/docs-sync.py generate` 同 commit
- [ ] T026 [US4] integration 授權矩陣（handler mod tests）：dev-admin 讀→5003／寫→5003、dev-user 讀寫→5003、無標頭讀寫→8888（HTTP 200 信封）——斷言對照 T025 之拒絕語意 ADR 定稿（SC-004、US4 場景 1~3）＋enforce 判定單一進入點與空 no-escalation 掛點存在性斷言；容器內 cargo test 綠；worktree commit＋pin bump

---

## Phase 7: User Story 5 — 三態部分更新語意（P3）

**Goal**: B-026 envelope 級三態在真實寫端具象驗證

**Independent Test**: description 三態矩陣＋settingValue 顯式 null 拒收四案全綠（quickstart §3 末例）

- [ ] T027 [US5] 三態 deserialize 純函式測（缺席／null／值三形×兩欄）＋integration 四案：description 缺席不動／null 落 NULL／設值生效、settingValue null→2222（SC-005、US5 場景 1~3）；容器內 cargo test 綠；worktree commit＋pin bump

---

## Phase 8: Polish＋DoD 收攏

- [ ] T028 [P] B-014：`rust-api/entity/src/sys_user_role.rs` 補兩條 FK 之 Relation 枚舉＋Related impl（機械工）；entity-drift 閘綠；worktree commit＋pin bump
- [ ] T029 [P] 活書 `docs/arc42/ARCHITECTURE.md` 對應節 as-built 更新（server crate 管線形／三態約定定形／授權骨架與 seam；feature branch 內改——現在式、不含排程）
- [ ] T030 B-028 第二輪量測（server 依賴全進場後：容器內冷編＋單檔增量）＋兩輪數據落帳 `docs/ops/RUNBOOK.md` §12.1 形制＋`docs/ops/BACKLOG.md` B-028 條目改寫（收掉量測半條、留 sea-orm DDL 草稿半條、勿整列刪）
- [ ] T031 DoD 收攏與負向自證：quickstart 全場景走查（§0~§4）＋`python3 tools/docs-sync.py check` 全綠＋`python3 tools/schema-gate.py check` 三閘綠＋entity-drift 綠＋coverage gate 負向抽查（暫 comment 一 case→紅指名→還原）＋4 保留碼與 1000/3333/7777 零發出斷言在案＋SC-001~SC-008 逐條對照勾稽（結果記單元 report、供 final holistic review）

---

## Dependencies

- Phase 1：T001 最先（動工前基線）；T002／T003 平行（T001 後）。
- Phase 2：T004→{T005、T006、T007 平行}→T008→T009→T010→T011（組合拳）→T012。
- US1（Phase 3）依 Phase 2；內部 T013→T014→{T015}→T016→T017→T018。
- US2（Phase 4）依 US1（管線＋typings 快照既在）；內部 T019→T020→T021→T022→T023。
- US3（Phase 5）依 US2 寫端在場：T024。
- US4（Phase 6）依 US1（讀矩陣）＋US2（寫矩陣）；T025（ADR）可與 US2/US3 平行先行、T026 依 T025。
- US5（Phase 7）依 US2 三態型在場：T027。
- Phase 8：T028／T029 平行可提前；T030 依全依賴定案；T031 壓軸。

## Parallel Example

- Setup：`T002 wire-schema.py`（傘狀）∥`T003 server 骨架`（rust-api）——不同 repo 檔域。
- Foundational：T005（config/state）∥T006（auth/）∥T007（seam/facade 骨架）——同 crate 不同檔、皆依 T004。
- US2 期間：T025（US4 之 ADR、docs 檔域）可平行先行。
- Polish：T028（entity）∥T029（活書）。
- ★rust build/test 不平行（容器內 serial）——[P] 僅指檔域不相交可分派，cargo 執行一律序列。

## Implementation Strategy

- **MVP＝Phase 1＋2＋3（US1）**：讀端全通即為「rev5 第一條管線存在」的可交付增量。
- 之後按 US2→US3→US4→US5 增量交付；每 phase 尾 pin bump＝單元邊界、隨時可停可審。
- 編排（CLAUDE.md §2 範本）：每執行單元 implementer(TDD)→spec-compliance review→fix→code-quality review→fix；驗收對照 spec.md；review agent 只讀不寫。
- 收尾（不在本清單）：final holistic review→finishing-a-development-branch（push/merge 需 user 同意）→收刀簿記三步。
