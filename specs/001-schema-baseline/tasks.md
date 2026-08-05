# Tasks: 波 0 schema 基線（rev4 終態壓平＋定稿制）

**Input**: Design documents from `/specs/001-schema-baseline/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md、
seed-decision.json（clarify 簽核定稿）

**Tests**: 本 repo TDD＝憲法級（§I.4）——「驗證先行」紀律**非可選**：US1／US2 設專節
（T006／T008 先紅）；US3 之先紅面由 T011 內建 self-test＋negative 注入承載、US4 由
T017／T018 之缺席／負向演練承載。

**Organization**: 依 user story 分期；本刀為地基刀、story 間存在天然順序相依
（US1→US2→US3→US4，見 Dependencies）——各 story 仍各有獨立驗收面。

**紀律烤入**（一切任務隱含）：rust build/test 一律容器內、全程 serial；rev4 唯讀參照、
code 不拷貝（adapter 例外）；兩段式 commit（worktree 內 commit → 外層即時 bump pin）；
★絕不 push／merge（finishing 前硬禁令、本清單不含此類任務）；書面產物一律 zh-TW。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup（共享基礎）

- [ ] T001 建 rust-api workspace 骨架：`rust-api/Cargo.toml`（members＝migration／entity／
      sea-orm-adapter；workspace.package edition=2024；workspace.dependencies 依 research
      R1 pins 全組）＋`rust-api/rust-toolchain.toml`（channel "1.96.1"）
- [ ] T002 [P] vendored 拷貝 `rust-api/sea-orm-adapter/`（整檔自 rev4 @ 2b8a101、工作區
      同層 `../fork260509-rev4`、§I.5 例外）：僅 Cargo.toml 檔頭 provenance 註解行前移一代（拷貝自 rev4…原鏈 rev2@1fa2ebd
      →rev1@0b64a57）、其餘位元零改寫——驗收＝`diff -r` 對 rev4 源僅 provenance 行差異
- [ ] T003 [P] 立兩支 ADR draft：`docs/arc42/decisions/0006-schema-baseline-flatten-finalize.md`
      （基線＝rev4 終態壓平＋user 定稿制；provenance rev4:0014＋rev4:0021）＋
      `docs/arc42/decisions/0007-schema-gate-managed-evolution.md`（閘契約＝Day-1 受管
      演進帳；承 K1-32／K1-39）——status: draft（0005 已由 §I.2 Amendment 取號）
- [ ] T004 [P] 建 dev 映像並斷言 toolchain：`docker compose -f docker-compose.yml -f
      docker-compose.dev.yml build rust-api`；容器內 `cargo --version`＝1.96.1

---

## Phase 2: Foundational（阻斷性前置）

**⚠️ 完成前不得開任何 user story**

- [ ] T005 migration crate 骨架：`rust-api/migration/Cargo.toml`（deps＝sea-orm-migration／
      sea-orm-adapter／tokio、★不含 argon2）＋`src/main.rs`（`_FILE` 優先語意＋空值／
      CHANGE-ME fail-loud，全新打字）＋`src/lib.rs`（空 Migrator）——驗收＝容器內
      `cargo build -p migration` 綠＋`Cargo.lock` pins 對照 R1 清單（sea-orm 1.1.20／
      casbin 2.20.0／tokio 1.52.3）

**Checkpoint**: workspace 可建置——US1 可開工

---

## Phase 3: User Story 1 - 基線結構定稿落地 (Priority: P1) 🎯 MVP

**Goal**: m001 落地——15 表結構（169 欄、欄序＝data-model §2）＋索引 38／約束 101＋
pg_trgm＋casbin 委派建表，pristine 重放與定稿全等。

**Independent Test**: pristine 重放 m001 → 照相 → (a) vs data-model §2 欄序逐表全等
(b) 經 rename map 映射 vs rev4 快照三節全等（血緣核對）——不需 seed 即閉環。

### 驗證先行（US1）

- [ ] T006 [US1] 結構驗證腳本（scratchpad `check-m001.py`）：照相三查詢（refresh 同構
      SQL）＋vs data-model §2 欄序比對＋血緣核對（data-model §4 授權偏離集 normalize
      〔rename／region／trace_id／real_ip NN／預設 now()〕後 vs rev4 快照
      `../fork260509-rev4` 已入版件全等）；對空庫跑＝紅（15 表缺席逐項指名）——先紅為證

### 實作（US1）

- [ ] T007 [US1] 實作 `rust-api/migration/src/m001_baseline_schema.rs`＋掛載 `src/lib.rs`：
      `CREATE EXTENSION IF NOT EXISTS pg_trgm` → casbin_rule 委派 adapter 建基底＋同檔
      ALTER 3 治理欄 → 14 表 CREATE（欄序／型別／nullable／default 逐欄照 data-model §2）
      → 索引／約束全量（data-model §6、含 partial-uniq 與 GIN trigram）；`down`＝全量
      反向——驗收＝T006 綠＋up→down 後我方建物淨空（15 表＋索引＋sequences；
      seaql_migrations 與 pg_trgm extension 保留——down 不 DROP EXTENSION、跨刀共享物）
      →再 up 綠（IF NOT EXISTS 冪等）

**Checkpoint**: 結構基線可獨立交付（MVP）

---

## Phase 4: User Story 2 - seed 全量過目定稿 (Priority: P2)

**Goal**: m002 落地——266 列 seed 完全決定性（明示 id／created_at 定稿時戳／PHC 常數／
protected 明示／setval×4），重放與 seed-decision.json 逐列全等。

**Independent Test**: pristine 重放 m001＋m002 → 逐表 SELECT 萃取 → vs seed-decision.json
逐列比對零差異（含 password／created_at／sequence 落值——Q1 零豁免驗證）。

### 驗證先行（US2）

- [ ] T008 [US2] seed 驗證＋轉錄雙腳本（scratchpad）：①`check-m002.py`——萃取實庫 vs
      seed-decision.json 逐列比對（含 sequences）、對僅 m001 之庫跑＝紅（266 列缺席）；
      ②`transcribe-m002.py`——自 seed-decision.json 機器轉錄 m002 用 SQL 字面（斷言：
      總列數 266、具 id 欄 247 列、具 created_at 欄 263 列、PHC、時戳、protected 總數
      自該檔現算〔現值 casbin true×19、menu true×8〕；★禁手抄、data-model §8）

### 實作（US2）

- [ ] T009 [US2] 實作 `rust-api/migration/src/m002_baseline_seeds.rs`＋掛載 `src/lib.rs`：
      T008② 轉錄產物入碼（明示 id＋明示 created_at＝2026-08-05T00:00:00+00:00＋PHC 常數
      ＋casbin protected 明示）＋收尾 setval（casbin_rule=163／sys_menu=78／sys_role=3／
      sys_user=3）；`down`＝seed 反向刪除——驗收＝T008① 綠；若 pre-commit 機密掃描誤報
      PHC 字面→依 ADR 0003 佔位字面白名單處置（.gitleaks.toml allowlist、絕不 --no-verify）

**Checkpoint**: 基線兩支齊備、重放完全決定性

---

## Phase 5: User Story 3 - 驗證閘＝Day-1 受管演進帳 (Priority: P3)

**Goal**: 三閘重建（contracts/gates.md 契約）＋演進帳＋fixtures 凍結；未登記漂移一律紅。

**Independent Test**: quickstart B／C——`schema-gate.py check` 三閘綠；四類假漂移注入
必紅（SC-002）；演進帳往返（注入紅→登記綠→壞形 rc2）。

### 實作（US3）

- [ ] T010 [P] [US3] reference-src 兩檔初版：`docs/ops/reference-src/schema-evolution.json`
      （`{"next_id":1,"entries":[]}`）＋`docs/ops/reference-src/archetype-map.json`
      （data-model §1 十五表逐筆轉錄、含 lineage／usage 檔頭欄）
- [ ] T011 [US3] 整組重建 `tools/schema-gate.py`（契約＝contracts/gates.md 逐條）：
      gate1 凍結＋演進帳合成全等／gate2 欄序（parse data-model §2；casbin_rule 豁免）＋
      seed（pg_dump normalize：COPY 段整列排序、★禁全檔排序後雜湊）／audit archetype
      （15 表×四變體規則）；rev4 白名單模型（ADR 0032/0039/0064 殘留＋specs/002 字面）
      整組移除；check 入口無條件合成 self-test；`test` 子命令含四類 negative 注入
      （結構／欄序／seed 值／sequence 落值各≥1、全紅）＋登記檔壞形自測（knife 格式錯／
      kind 非枚舉／id 非遞增各≥1 例、斷言 rc 2 指名）——驗收＝`test` 全綠＋fixtures
      缺席時 check rc 2 附補救
- [ ] T012 [US3] fixtures 凍結（contracts/fixtures.md §2 先驗後凍）：pristine 重放→三驗
      三綠（vs seed-decision 逐列／vs data-model 欄序／rename 映射 vs rev4 快照）→落
      `specs/001-schema-baseline/fixtures/`（columns/indexes/constraints.json＋seed.sql
      normalize＋provenance.md 六欄目）——驗收＝落檔後 `schema-gate.py check` 對基線庫
      rc 0
- [ ] T013 [US3] 演進帳往返驗證（quickstart C 四步實跑）：注入未登記欄→check rc 1 指名；
      補登記（E-001 試登）→rc 0；登記檔壞形（刪 date 欄；另 knife 格式錯一例）→rc 2
      啟動斷言；全還原（撤登記＋DROP、
      登記檔復原空 entries）→rc 0——驗收＝四步輸出留存 review 憑證
- [ ] T014 [P] [US3] RUNBOOK 增補 Day-1 登記紀律：`docs/ops/RUNBOOK.md` §10 migration
      操作節加「每支帶 migration 的刀收刀前必跑 refresh＋schema-evolution 登記＋三閘綠」
      （contracts/gates.md §5 條文）；並移除該節現存之創世佔位句（「本章隨 schema 刀
      補實文」類）——補實與佔位不並存

**Checkpoint**: 閘常態運轉、基線保鮮機制就位

---

## Phase 6: User Story 4 - 參考真表與漂移防線就位（DoD 鏈） (Priority: P4)

**Goal**: entity 對應層＋refresh 首跑＋gen.snapshots 拔項＋真表首算＋pre-commit 全鏈綠。

**Independent Test**: quickstart E——DoD 鏈順序全綠；entity 目錄缺席演練＝commit 被
entity-drift-gate rc 2 擋。

### 實作（US4）

- [ ] T015 [P] [US4] entity crate（15 表 entity 檔＋Cargo.toml＋lib.rs）：`rust-api/entity/Cargo.toml`（sea-orm features
      恰四項）＋`src/lib.rs`＋15 表 entity（含 casbin_rule.rs；欄名＝rename 後定稿名、
      型別對照 TYPE_MAP：bigint→i64／timestamptz→DateTimeWithTimeZone／inet→IpNetwork／
      jsonb→Json；全新打字、參照 rev4 對照不拷貝）——驗收＝容器內
      `cargo build -p entity` 綠
- [ ] T016 [P] [US4] dev stack 基線落庫＋refresh 首跑：`docker compose … up -d --wait
      postgres` → `run --rm migrate`（m001+m002 applied）→ `python3 tools/docs-sync.py
      refresh` 產 `docs/ops/reference-src/schema-snapshot.json`＋`accounts-snapshot.json`
      ——驗收＝兩快照落檔且 schema 快照欄名＝rename 後定稿名
- [ ] T017 [US4] entity-drift 恢復實跑驗證（依賴 T015＋T016＋T018——拔項未落前 lint 因
      gen.snapshots 到期即紅而全紅、演練不可歸因）：`python3
      tools/entity-drift-gate.py check` 直跑 rc 0（casbin_rule SKIP 註記一行）；
      防線演練＝暫移 `rust-api/entity/src` → 對 rust-api pin bump 之 commit 被 pre-commit
      rc 2 擋 → 還原綠——驗收＝兩態輸出留存
- [ ] T018 [US4] `tools/docs-sync.py` 拔項＋真表首算（依賴 T010＋T016）：DAY1_EXEMPTIONS
      ＋DAY1_EXEMPT_SCOPE 雙表拔 `gen.snapshots`（謂詞已成立、循 gen.compose 前例留日期
      註解）→ `generate`（`docs/generated/reference/schema.md`＋`accounts.md` 首算）→
      `lint` 全綠且跳過明細零 gen.snapshots；負向演練＝暫移 schema-snapshot.json→lint 紅
      指名（到期即紅第四例之負向半）→還原綠——驗收＝pre-commit 全鏈綠（工具本體 staged
      觸發 docs-sync 自測）

**Checkpoint**: 查表可信、漂移防線常態化

---

## Phase 7: Polish & 收刀前置

- [ ] T019 [P] 活書隨刀：`docs/arc42/ARCHITECTURE.md` 增設「資料慣例」節（現無此節、隨刀
      新設）並載 memo 欄家族一行
      （data-model §5 語意；UI 兌現＝B-003）＋schema 基線現況一段（15 表／archetype／
      閘與演進帳、現在式）
- [ ] T020 [P] ADR 0006／0007 draft→accepted（body 不變、status 翻轉；DECISIONS-INDEX
      由 generate 重算）
- [ ] T021 quickstart A～E 全場景端到端重跑（驗收證據彙整：SC-001～SC-006 逐項對照輸出
      留存 → 供 final holistic review；含 pre-commit 全鏈耗時 <20s 警戒線確認）

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup（P1 期）→ Foundational（T005 需 T001）→ US1 → US2 → US3 → US4 → Polish。
- **本刀 story 順序相依**（地基刀天然鏈）：US2 需 m001（US1）；US3 fixtures 需 m001+m002
  （US1+US2）；US4 refresh／drift 需基線落庫＋archetype-map（US1～US3）。
  各 story 驗收面獨立（見各 Independent Test）。

### 任務級相依

- T005←T001；T007←T005+T006；T009←T007+T008；T011←T010（audit 左源）；T012←T009+T011；
  T013←T012；T015←T005（workspace）；T016←T009；T017←T015+T016+T018（拔項先行——T016
  落快照後 gen.snapshots 謂詞成立、lint 到期即紅，未拔項前任何 commit 全紅、演練不可
  歸因）；T018←T010+T016；T021←全部。

### Parallel Opportunities

- Setup：T002／T003／T004 三支並行（T001 後）。
- US3：T014 與 T011 可並行；T010 先行（T011 audit 左源）。
- US4：T015（rust-api）與 T016（stack＋快照）不同面可並行。
- Polish：T019／T020 並行。
- ★rust 面任務（T005/T007/T009/T015）縱使標 [P] 仍不得同時起 cargo（全程 serial 紀律）
  ——[P] 僅表無邏輯相依。

## Implementation Strategy

- **執行單元切分（Workflow 編排、CLAUDE.md §2 範本）**：
  單元①＝T001～T007（Setup+Foundational+US1）｜單元②＝T008～T009（US2）｜
  單元③＝T010～T014（US3）｜單元④＝T015～T018（US4）｜單元⑤＝T019～T021（Polish）。
  每單元內 serial：implementer(TDD)→spec-compliance review→fix 迴圈→code-quality
  review→fix 迴圈；單元邊界＝復核＋load-bearing 自驗＋bump submodule pin。
- **MVP**＝US1（結構基線單獨可交付、可獨立驗證）。
- 增量交付：每 story 一個 checkpoint、驗收綠才進下一 story。
- 收刀（不在本清單）：final holistic review → finishing-a-development-branch（push／merge
  需 user 當回合同意）→ 簿記三步。
