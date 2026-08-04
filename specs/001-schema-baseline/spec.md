# Feature Specification: 波 0 schema 基線（rev4 終態壓平＋定稿制）

**Feature Branch**: `001-schema-baseline`

**Created**: 2026-08-05

**Status**: Draft

**Input**: User description: "docs/brainstorms/001-schema-baseline.md"（階段 0 brainstorm 定稿、2026-08-05；本 spec 之唯一輸入。該檔 §5 為欄序定稿權威，SDD 轉錄 `specs/001-schema-baseline/data-model.md` 凍結後以 data-model 為權威、brainstorm 轉史料）

> 摘要：rev5 資料庫基線＝rev4 終態（15 表）壓平為兩支基線遷移——結構（m001）＋seed 定稿（m002）；
> 方法沿定稿制（欄序親排＋更名開放＋seed 全量過目、「定稿即基線」）。同刀就位三閘驗證與
> Day-1 受管演進帳契約、entity 對應層與漂移防線、參考真表首算。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 基線結構定稿落地 (Priority: P1)

作為 workspace 維護者，我要 rev5 資料庫結構基線＝rev4 終態 15 表壓平、且欄序／欄名／型別依親排
定稿（brainstorm §5，含 rename map 4 組與定稿差異 2 項），使後續一切功能刀都建立在單一權威
schema 起點上；rev4 的後續 delta（m003～m015）不搬（淨效果已含於終態），rev5 第一支 delta 自
m003 起編。

**Why this priority**: 沒有結構基線，rust-api 首批程式工件與一切後續刀都無地基；定稿制（而非
盲目壓平）是 rev4 已驗證的方法且 user 已三題拍板。

**Independent Test**: 對一次性 pristine 資料庫重放結構遷移，機器比對實庫結構與定稿是否全等——
不需 seed、不需任何後續刀即可獨立驗證並交付價值。

**Acceptance Scenarios**:

1. **Given** 一次性 pristine 資料庫，**When** 重放 rev5 結構基線遷移，**Then** 實庫 15 表結構
   （型別／nullable／default／約束／索引）與定稿全等；14 親排表欄序逐欄一致（158 欄＋
   casbin_rule 11 欄＝169 欄）。
2. **Given** data-model 已轉錄凍結，**When** 與 brainstorm §5 定稿逐表對照，**Then** 欄序、
   rename map 4 組（sys_operation_log 去 operator_ 前綴）、定稿差異 2 項（region 新增 text 可空；
   trace_id 改 text）逐筆記明、零漏轉。
3. **Given** 重放後實庫，**When** archetype 歸屬逐表驗證，**Then** 15 表歸屬與 archetype-map
   定稿一致（15/15 綠）。
4. **Given** casbin_rule 沿委派建表（基底 8 欄＋同檔 ALTER 補 3 治理欄），**When** 建表完成，
   **Then** 結構語意符合定稿；其欄序由建表機制決定、不入親排比對。

---

### User Story 2 - seed 全量過目定稿 (Priority: P2)

作為 workspace 維護者，我要親自過目 rev4 終態 seed 的全量淨效果（機器萃取成逐表清單），逐筆
調整（id 重編／刪列／改值、連動同步）後定稿，使 seed 基線（m002）的每一列都經我簽核——
「定稿即基線」，零未過目內容進基線。casbin 授權政策 seed 併入同批定稿。

**Why this priority**: seed 是基線的另一半（帳號／選單／政策皆繫於此）；拍板甲明定過目時點＝
SDD clarify 步、user 親自定稿不可代勞。依賴 US1 的素材產製鏈但可獨立驗收。

**Independent Test**: 素材鏈可獨立驗證——重放 rev4 遷移萃取 seed 淨效果清單、與結構快照雙源
互證；定稿後 m002 重放與定稿 fixtures 逐列比對即獨立閉環。

**Acceptance Scenarios**:

1. **Given** rev4 十五支 migration 素材（抄至 scratchpad、拷貝例外射程內），**When** 容器內對
   一次性 pristine 資料庫重放並機器萃取，**Then** 產出 (a) 結構快照 (b) seed 淨效果逐表清單
   （＝clarify 過目素材），且 rev4 側零寫入（不起其 Exited 容器、不動其 volume）。
2. **Given** 萃取結構快照與 rev4 已入版 schema-snapshot，**When** 雙源互證，**Then** 兩源一致；
   不一致即停手升級 user 裁決、不得單源逕行定稿。
3. **Given** seed 淨效果清單，**When** user 於 clarify 工作坊逐表過目調整，**Then** 調整連動
   同步（如 id 重編後外鍵引用同步）、定稿全文紀錄在案。
4. **Given** seed 定稿，**When** rev5 基線遷移對 pristine 重放後與定稿 fixtures 做未排序逐列
   diff（含 id 欄；COPY 段整列排序 normalize），**Then** 零差異；sequence 落值與物理列序兩類
   病灶皆可現形（禁止排序後雜湊比對）。

---

### User Story 3 - 驗證閘＝Day-1 受管演進帳 (Priority: P3)

作為 workspace 維護者，我要 schema 驗證閘自 Day-1 起採「凍結面＋演進登記」合成期望值、與實庫
**全等**比對的契約——未登記漂移一律紅，避免 rev4 凍結模型被三段鑿洞（0032→0039→0064）的教訓
重演；每支帶 migration 的刀必跑照相＋登記，成為常設程序。

**Why this priority**: 閘是基線的保鮮機制；沒有它基線落地即開始腐化。依賴 US1／US2 的定稿
產物存在。

**Independent Test**: 對就位後的閘做往返驗證——注入未登記漂移必紅、補登記後轉綠、登記檔格式
破損時啟動斷言 fail-loud——不需任何後續刀即可獨立驗證。

**Acceptance Scenarios**:

1. **Given** 凍結 fixtures＋空演進登記檔，**When** 閘對基線實庫比對，**Then** 全等、綠。
2. **Given** 實庫注入一筆未登記漂移（新欄／改型別／seed 改值任一），**When** 閘執行，**Then**
   紅且指明漂移位置（negative test、比對器先自證）。
3. **Given** 該漂移補入演進登記檔（帶來源刀編號），**When** 閘再執行，**Then** 合成期望值後
   全等、綠。
4. **Given** 登記檔缺欄位或來源刀編號格式錯誤，**When** 閘啟動，**Then** 啟動斷言 fail-loud、
   不得靜默通過。
5. **Given** 三閘（gate1 結構全等／gate2 欄序＋seed 對 data-model 定稿、rename 走映射比對／
   audit archetype 15 表歸屬），**When** 對基線實庫全跑，**Then** 全綠；閘工具內殘留的 3 行
   rev4 字面座標已同刀清償為 rev5 座標。

---

### User Story 4 - 參考真表與漂移防線就位（DoD 鏈） (Priority: P4)

作為 workspace 維護者，我要「查現況」的 schema／accounts 參考真表自實庫照相首算就位、快照豁免
拔項、entity 對應層（15 表）與 entity-drift 雙向比對自 Day-1 跳過解除起實跑，使帳面與實庫的
漂移在 commit 時即被攔下。

**Why this priority**: 收尾防線與查表可信度；價值真實但依賴前三個 story 的產物齊備。

**Independent Test**: 照相→真表→豁免拔項→drift 實跑可逐環驗證：每環有明確的綠／紅可觀察
產物（真表內容、lint 結果、commit 被擋）。

**Acceptance Scenarios**:

1. **Given** 基線實庫就位，**When** 照相（refresh）首跑＋真表重算（generate），**Then**
   schema／accounts 兩快照與兩張參考真表就位、內容與定稿一致。
2. **Given** 快照豁免（gen.snapshots）拔項，**When** 全量 lint／pre-commit 執行，**Then** 綠；
   快照缺席時紅（「到期即紅」第四例成立）。
3. **Given** entity-drift Day-1 跳過解除，**When** entity 對應層在場且與快照一致，**Then**
   pre-commit 綠；**When** entity 目錄缺席，**Then** 擋死一切 commit（fail-loud）。

---

### Edge Cases

- **雙源互證分歧**：重放環境差異使萃取快照與 rev4 已入版快照不一致 → 停手升級 user，禁止
  單源逕行定稿（US2 場景 2）。
- **假紅與真漂移的分辨**：物理列序差異＝假紅（COPY 段整列排序 normalize 消除）；sequence
  落值漂移＝真漂移（必須現形）。兩需求同時成立 → 絕不排序後雜湊比對整檔。
- **rename 映射比對**：閘對 rev4 欄名 ↔ rev5 定稿欄名走 rename map 映射，防 4 組改名被誤報
  漂移、亦防映射錯位漏報真漂移。
- **casbin_rule 欄序**：由委派建表機制決定、不入親排；欄序比對（gate2）射程＝14 親排表，
  casbin_rule 僅驗結構語意與 archetype 歸屬。
- **演進登記檔破損**：缺欄、格式錯、來源刀編號不合規 → 閘啟動斷言 fail-loud，不得以「登記檔
  壞了」為由靜默放行。
- **entity 對應層半缺**：目錄缺席或表數不足 → 擋死一切 commit；不得降級為警告。
- **rev4 側唯讀紀律**：素材產製全程對一次性 pristine 實例操作；誤起 rev4 既有容器（一起即寫
  WAL、volume 變動）＝違唯讀精神，程序上禁止。

## Requirements *(mandatory)*

### Functional Requirements

**基線定稿**

- **FR-001**: rev5 資料庫基線 MUST 為 rev4 終態 15 表之壓平：結構基線（m001）＋seed 基線
  （m002）兩支；rev4 的 m003～m015 delta 不搬；rev5 第一支後續 delta 自 m003 起編
  （migration 短編號紀律）。
- **FR-002**: 14 親排表之欄序／欄名／型別 MUST 逐欄轉錄 brainstorm §5 定稿至 data-model 凍結，
  含 rename map 節（4 組、全在 sys_operation_log）與定稿差異節（region 新增 text 可空、
  trace_id 改 text）；轉錄完成後 data-model 為唯一權威。結構語意除定稿差異載明者外 MUST 忠實
  rev4 終態快照。
- **FR-003**: casbin_rule MUST 沿 rev4 委派建表模式（基底 8 欄＋同檔 ALTER 補 3 治理欄），
  欄序不入親排；其授權政策 seed MUST 併入基線同批定稿。
- **FR-004**: memo 欄家族語意（user_memo／role_memo／menu_memo／wbip_memo：R_SUPER 備註、
  顯示於管理列表、不顯示於下拉／引用／對外 API）MUST 於 data-model 凍結；role_desc 與
  role_memo 並存不合併。活書資料慣例節 MUST 同刀加入此一行（UI 兌現不在本刀，由 BACKLOG
  B-003 承載）。

**seed 定稿制**

- **FR-005**: seed 內容 MUST 採定稿制：機器萃取 rev4 終態 seed 淨效果成逐表清單檔，於 SDD
  clarify 步由 user 親自全量過目調整（id 重編／刪列／改值、連動同步）後定稿；定稿前本 spec
  以「seed＝定稿制、內容於 clarify 工作坊定稿」占位，MUST NOT 以未定稿內容施工 seed 基線。

**對賬鏈**

- **FR-006**: 素材產製 MUST 於容器內將 rev4 十五支 migration 對一次性 pristine 資料庫重放，
  機器萃取 (a) 結構快照 (b) seed 淨效果逐表清單；rev4 側 MUST 零寫入（原始碼僅抄至
  scratchpad——拷貝例外射程內；不起其既有容器、不動其 volume）。
- **FR-007**: 結構面 MUST 雙源互證：重放萃取快照 vs rev4 已入版 schema-snapshot；不一致 MUST
  停手升級 user 裁決。
- **FR-008**: 定稿後 MUST 驗證：rev5 基線兩支對 pristine 重放，與定稿 fixtures 做未排序逐列
  diff（含 id 欄；COPY 段整列排序 normalize 消物理列序假紅；MUST NOT 排序後雜湊比對）；
  MUST 附 negative test（注入假漂移必紅、比對器先自證）。

**驗證閘＋演進帳**

- **FR-009**: schema 閘契約 MUST 為 Day-1 受管演進帳：凍結面（`specs/001-schema-baseline/fixtures/*`，定稿產物、永不改寫、provenance 保存）＋演進面（`docs/ops/reference-src/schema-evolution.json` 單一登記檔，每筆新表／新欄／新索引／新 seed 列／seed 內容變更帶來源刀編號）合成期望值後與實庫**全等**比對——非容差剝除；未登記漂移一律紅；登記檔自身
  MUST 有啟動斷言防呆（欄位齊全性＋來源刀編號格式）。
- **FR-010**: 三閘 MUST 就位：gate1 結構（凍結＋演進帳合成後全等）／gate2 欄序＋seed（vs
  data-model 定稿；rename 走映射比對）／audit archetype（15 表歸屬逐表驗）；schema 閘工具
  MUST 整組重建為 rev5 座標（fixtures 與 data-model 路徑指向本刀、15 表），其殘留的 3 行
  rev4 字面 MUST 同刀清償。
- **FR-011**: 「每支帶 migration 的刀必跑照相（refresh）＋演進帳登記」MUST 入 RUNBOOK 成為
  常設程序。

**entity 與 DoD 鏈**

- **FR-012**: entity 對應層 MUST 覆蓋 15 表並隨本刀首批程式工件就位；entity-drift MUST 為
  快照 vs entity 對應層之雙向比對；Day-1 跳過解除後 pre-commit MUST 實跑，entity 目錄缺席
  MUST 擋死一切 commit。
- **FR-013**: DoD 鏈 MUST 依序完成：照相首跑 → schema／accounts 兩快照就位 → 真表重算 →
  schema／accounts 參考真表首算 → 快照豁免（gen.snapshots）拔項（到期即紅第四例）→
  entity-drift Day-1 跳過解除且 pre-commit 綠。
- **FR-014**: archetype 歸屬登記（archetype-map）初版 MUST 就位：15 表變體歸屬、自 data-model
  定稿轉錄。
- **FR-015**: 兩支 ADR MUST 於刀內落地 draft→accepted：①「schema 基線＝rev4 終態壓平＋user
  定稿制」（provenance `rev4:0014`＋`rev4:0021`）②「schema 閘契約＝Day-1 受管演進帳」
  （承 K1-32／K1-39 重審）。

### Key Entities

- **基線 schema（15 表、169 欄）**: 14 親排表（sys_user 17、sys_role 13、sys_menu 29、
  sys_ip_rule 11、system_settings 10、sys_access_log 12、sys_login_attempt 11、sys_token 9、
  sys_user_role 2、session_event 8、sys_operation_log 14、sys_pwd_custody 3、
  sys_user_email_verify 5、sys_casbin_policy_archive 14＝158 欄）＋casbin_rule（11 欄、委派
  建表）；逐欄定稿＝brainstorm §5 → data-model 凍結。
- **data-model 定稿文件**: 欄序權威（轉錄後）；含 rename map、定稿差異、memo 欄家族語意、
  archetype 歸屬轉錄來源。
- **定稿 fixtures（凍結面）**: 結構＋seed 定稿產物；永不改寫、provenance 保存。
- **演進登記檔（演進面）**: 跨刀單一登記檔；每筆變更帶來源刀編號；與快照同家（specs 下屬
  凍結史料、放彼處違語意）。
- **archetype 歸屬登記**: 15 表 × 憲法 §I.6 四變體（A 業務全 6 欄／B append-only 日誌／
  C join·狀態機／D 治理變體）之歸屬帳。
- **entity 對應層**: 15 表之程式側對應；entity-drift 比對之一側。
- **參考真表與快照**: schema／accounts 兩快照（照相產物）與兩張參考真表（重算產物）；
  「查現況」正典入口。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 對 pristine 重放 rev5 基線後，結構與 seed 與定稿 fixtures 未排序逐列 diff＝
  **零差異**（含 id 欄與 sequence 落值）。
- **SC-002**: 比對器自證通過：注入假漂移（結構、欄序、seed 值、sequence 落值各至少 1 例）
  全數必紅、零漏報。
- **SC-003**: 14 親排表欄序與定稿逐欄一致（158＋11＝169 欄）、rename map 4 組映射比對通過、
  archetype 歸屬 15/15 綠。
- **SC-004**: seed 全量清單 100% 經 user 過目簽核（clarify 工作坊紀錄在案）、零未過目列進
  基線。
- **SC-005**: 演進帳往返驗證通過：未登記漂移注入→閘紅；補登記→閘綠；登記檔破損→啟動斷言
  fail-loud。
- **SC-006**: DoD 鏈全綠：快照豁免拔項與 entity-drift 跳過解除後，全量 pre-commit 零紅；
  entity 目錄缺席演練＝commit 被擋。

## Assumptions

- rev4 repo 為本機可達之唯讀參考庫；migration 原始碼抄至 scratchpad 屬拷貝例外射程
  （ADR 0001 決定 3）；rev5 正式程式工件不拷貝前代 code（工具性 crate 整檔拷貝例外承憲法
  §I.5）。
- 容器化資料庫可起一次性 pristine 實例；rust 建置／測試一律容器內、全程 serial（host 無
  toolchain）。
- 欄序定稿權威現為 brainstorm §5；SDD 轉錄 data-model 凍結後權威移轉、brainstorm 轉史料。
- seed 內容於 clarify 工作坊定稿（拍板甲）；本 spec 對 seed 內容不預斷、僅凍結「定稿制」
  程序本身。
- rev5 新結構差異＝零支（純壓平；§5 定稿差異屬定稿制射程、非新能力面）。
- 本刀非一次性遷移（pristine 建庫、無既有資料搬移），Risk／Guard／Rollback 三欄表免附
  （CLAUDE.md §2 該條射程＝改名／搬移／基線前進／拓樸調整）。

### Out of Scope

- server crate／router／一切業務邏輯（後續刀）。
- wire-schema 實跑（server 在場才有意義；維持 fail-open 警告態）。
- memo 欄家族之 UI 兌現（BACKLOG B-003 承載、四張管理列表）。
- 任何新能力面 schema 設計（本刀＝壓平＋定稿，零新設計夾帶）。
