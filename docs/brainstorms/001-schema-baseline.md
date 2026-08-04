# 001 波 0 schema 基線刀・階段 0 brainstorm 定稿

> 落點＝`docs/brainstorms/`（NNN- 空間首用：b 系前綴＝創世史料、NNN-＝刀流程編號，同名即當前
> feature branch 名）。日期＝2026-08-05。
> 依據＝啟動書 `docs/brainstorms/000-doc-architecture.md` §4.5.8（藍本座標＋拷貝例外射程）＋
> ADR 0001 決定 3（schema 拷貝例外承載）＋`b5b-gate-decisions.md` Q2 甲（降為波 0 正式刀）＋
> K1 承襲條目（K1-13／14／15／21／23／24／32／39）。
> 下一步＝**手動** `/speckit-specify`（input＝本檔；不自動觸發、feature branch pre-hook 首實戰）。
> **本檔 §5 即欄序定稿權威**；SDD 時轉錄 `specs/001-schema-baseline/data-model.md` 凍結，此後以
> data-model 為權威、本檔轉史料。

## 0. 拍板紀錄（本 brainstorm 三題＋工作坊，user 逐題裁定 2026-08-04～05）

| 題 | 裁定 | 要點 |
|---|---|---|
| seed 全量過目的執行時點 | 甲・SDD clarify 步 | 容器內把 rev4 十五支 migration 重放到 pristine 庫、機器萃取終態 seed 淨效果成逐表清單檔，user 對準確清單過目調整（id 重編／刪列／改值、連動同步）；spec 先以「seed＝定稿制、內容於 clarify 工作坊定稿」占位 |
| 欄序工作坊是否開放更名 | 甲・開放 | 重排＋改名同坊受理；定稿進 data-model 的 rename map 節、驗證閘走映射比對；實績＝4 組改名（見 §5） |
| schema 驗證閘契約 | 甲・Day-1 受管演進帳 | 凍結面＋演進登記檔合成期望值後與實庫**全等**比對；承 K1-32／K1-39 重審結論（rev4 凍結模型三段鑿洞 0032→0039→0064 的教訓），細節見 §3 |
| 欄序親排工作坊 | 14 表逐表親排定稿 | user 指定於本 brainstorm 最後一問執行（原 Q1 嵌 clarify 之欄序半題提前兌現；seed 半題仍在 clarify）；定稿見 §5 |

**ADR 待立**（刀內隨 spec 落 draft→accepted，不在 default branch 先落）：
①「schema 基線＝rev4 終態壓平＋user 定稿制」（provenance `rev4:0014`＋`rev4:0021`）
②「schema 閘契約＝Day-1 受管演進帳」（承 K1-32／39 重審）。

## 1. 目標與範圍

**目標**：rev5 資料庫基線＝rev4 終態（15 表）壓平為 `m001_baseline_schema`（結構）＋
`m002_baseline_seeds`（seed 定稿）；方法沿 rev4:0021 定稿制——欄序親排＋更名開放＋seed
全量過目、「定稿即基線」。rev4 的 m003～m015 是其後續刀 delta、不搬（淨效果已含於終態）；
rev5 第一支 delta 從 m003 起編（migration 短編號紀律承 K1-13）。

**入刀**：
- rust-api worktree 首批程式工件：Cargo workspace＋migration crate（m001／m002）＋
  entity crate（15 表對應——★DoD 的 entity-drift Day-1 跳過解除結構性要求它在場：快照就位後
  pre-commit 實跑、entity 目錄缺席＝rc 2 擋死一切 commit）。
- `tools/schema-gate.py` 整組重建：rev5 座標（fixtures→`specs/001-schema-baseline/fixtures/`、
  data-model→001、15 表）＋§3 演進帳契約；B3 刻意殘留的 3 行 rev4 字面同刀清償。
- `docs/ops/reference-src/archetype-map.json` 初版（15 表變體歸屬、data-model 定稿轉錄）。
- refresh 首跑（實庫照相）＋schema／accounts 真表首算＋`gen.snapshots` 豁免拔項＋
  entity-drift Day-1 跳過解除。

**不入刀**：server crate／router／一切業務邏輯（後續刀）；wire-schema 實跑（server 在場才有
意義，維持 fail-open 警告態）。

**範圍聲明（工作坊後修訂版）**：
1. 結構語意（型別／nullable／default／約束／索引）忠實 rev4 終態；**定稿制射程含欄序重排、
   表欄更名、欄增刪與型別調整**（rev4 先例：其基線工作坊即新增 role_memo）——凡動者逐筆載於
   §5 定稿差異、data-model 記明，非「忠實壓平」之破例。本次實績＝新增 1 欄＋改型別 1 欄。
2. casbin_rule 沿 rev4:0015（K1-15）委派建表：adapter 建基底 8 欄＋同檔 ALTER 補 3 治理欄，
   欄序由建表機制決定、不入親排。其授權政策 seed 併入基線同批定稿（K1-23）。
3. rev5 新結構差異＝零支（純壓平、無夾帶新設計；§5 定稿差異不屬新能力面）。

## 2. 驗證鏈

- **對 rev4 終態對賬（SDD 素材產製）**：抄 rev4 migration 原始碼至 scratchpad（§I.5 拷貝例外
  射程內、ADR 0001 決定 3）→ 容器內 build、對一次性 pristine postgres 重放 15 支 → 機器萃取
  (a) information_schema 快照 (b) seed 淨效果逐表清單（＝clarify 過目素材）。結構面與 rev4 已
  commit 的 `schema-snapshot.json` **雙源互證**（防重放環境差異）。
  紀律：**不起 rev4 的 Exited 容器**（postgres 一起即寫 WAL、volume 會變，違唯讀精神）；
  rev4 repo 零寫入（`CARGO_TARGET_DIR` 外指、cargo 全程 serial 容器內）。
- **定稿後**：rev5 m001＋m002 對 pristine 重放 → **未排序逐列 diff**（含 id 欄；COPY 段整列
  排序 normalize 消物理列序假紅；★絕不排序後 md5——會同時掩蓋 sequence 落值漂移與物理序
  假紅）vs 定稿 fixtures；＋negative test（注入假漂移必紅、比對器先自證）。
- **三閘就位**：gate1 結構（凍結 fixtures＋演進帳合成後全等）／gate2 欄序＋seed（vs data-model
  定稿）／audit archetype（15 表歸屬逐表驗）。entity-drift：快照 vs entity crate 雙向比對。
- **DoD 鏈**：refresh 首跑 → 兩快照就位 → generate → schema／accounts 真表 →
  `gen.snapshots` 拔項（到期即紅第四例）→ entity-drift Day-1 跳過解除（pre-commit 實跑綠）。

## 3. 演進帳契約（閘設計拍板細化）

- **凍結面**：`specs/001-schema-baseline/fixtures/*`（定稿產物、永不改寫、provenance 保存）。
- **演進面**：單一登記檔 `docs/ops/reference-src/schema-evolution.json`（跨刀更新、與快照同家
  ——specs 下屬凍結史料、放彼處違語意）；每筆新表／新欄／新索引／新 seed 列／seed 內容變更
  帶來源刀編號登記。
- **閘語意**：「凍結＋登記」合成期望值後與實庫**全等**比對——非容差剝除；未登記漂移一律紅；
  登記檔自身 schema 有啟動斷言防呆（欄位齊全性＋來源刀編號格式）。
- **Day-1 紀律**：每支帶 migration 的刀必跑 refresh＋登記（入 RUNBOOK；rev4 是紅燈裸奔兩刀
  後才補此紀律——K1-39）。

## 4. 流程與 user 關卡

1. 本檔審定 → **手動** `/speckit-specify`（input＝本檔）。
2. SDD 5 步：specify → clarify【★seed 全量過目工作坊、user 親自定稿不可代勞】→ plan
   【Constitution Check 九題首實戰】→ tasks → analyze；每步後 commit。
3. TDD：Workflow 編排（防呆六件套＋watchdog 原子成對）；rust 容器內全程 serial。
4. 收刀：final holistic review → finishing（push／merge 需 user 當回合同意）→ 簿記三步
   （首筆 feature_close 事件）。
5. 非一次性遷移（pristine 建庫、無既有資料搬移），Risk／Guard／Rollback 三欄表免附
   （CLAUDE.md §2 該條射程＝改名／搬移／基線前進／拓樸調整）。

## 5. 欄序定稿一覽（權威；user 逐表親排、2026-08-05 總確認）

差異總覽：照舊 9 表｜調序 4 表｜綜合調整 1 表（sys_operation_log）。欄數 168→**169**
（region 新增）。型別／可空／預設除「定稿差異」載明者外，一律忠實 rev4 終態快照
（`rev4:docs/ops/reference-src/schema-snapshot.json`）。

### 照舊 9 表（欄序＝rev4 終態原樣）

| 表 | 定稿欄序 |
|---|---|
| sys_user（17） | id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, status, user_gender, user_name, password, nick_name, session_policy, session_id, user_phone, user_email, user_memo |
| sys_role（13） | id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, status, role_code, role_name, role_memo, role_home, role_desc |
| sys_menu（29） | id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, status, order, hide_in_menu, keep_alive, constant, multi_tab, protected, parent_id, menu_type, menu_name, menu_memo, route_name, route_path, component, icon, icon_type, i18n_key, href, active_menu, fixed_index_in_tab, query, buttons |
| sys_ip_rule（11） | id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, order, wbip_type, wbip_cidr, wbip_memo |
| system_settings（10） | setting_key, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, setting_type, setting_value, description |
| sys_access_log（12） | id, created_at, created_by, http_status, http_method, http_path, real_ip, peer_ip, x_forwarded_for, ip_confidence, region, trace_id |
| sys_login_attempt（11） | id, created_at, created_by, success, attempted_user_name, real_ip, peer_ip, x_forwarded_for, ip_confidence, region, trace_id |
| sys_token（9） | id, created_at, created_by, status, token_hash, rotation_chain, issued_at, expires_at, used_at |
| sys_user_role（2） | user_id, role_id |

### 調整 5 表

| 表 | 定稿欄序 | 差異 vs rev4 終態 |
|---|---|---|
| session_event（8） | id, created_at, created_by, user_id, sid, event_type, reason, source_ip | created_by 由第 7 位上移第 3 位（對齊審計欄群慣例） |
| sys_operation_log（14） | id, created_at, created_by, operation, entity_table, entity_id, payload_before, payload_after, real_ip, peer_ip, x_forwarded_for, ip_confidence, region, trace_id | 改名×4（去 operator_ 前綴）；region 新增；trace_id 改 text（見下） |
| sys_pwd_custody（3） | user_id, created_at, created_by | 後兩欄交換（複合 PK＝(user_id, created_by) 內部序屬語意、原樣不動） |
| sys_user_email_verify（5） | user_id, created_at, created_by, verified_at, verified_email | 審計欄群上移、verified 對殿後 |
| sys_casbin_policy_archive（14） | id, role_id, created_at, created_by, archived_at, archived_by, archive_reason, ptype, v0, v1, v2, v3, v4, v5 | role_id 由末位上移第 2 位 |

### casbin_rule（11 欄；不入親排、僅供參考——rev4:0015 委派建表）

id｜ptype｜v0～v5｜protected（ALTER 治理欄）｜created_at（ALTER）｜created_by（ALTER）

### rename map（4 組、全在 sys_operation_log；data-model §rename-map 轉錄、閘比對走映射）

| rev4 終態欄名 | rev5 定稿欄名 |
|---|---|
| operator_real_ip | real_ip |
| operator_peer_ip | peer_ip |
| operator_x_forwarded_for | x_forwarded_for |
| operator_ip_confidence | ip_confidence |

### 定稿差異（非純重排、data-model 記明）

| 項 | 內容 | 理由 |
|---|---|---|
| sys_operation_log.region 新增 | text、可空 | 對齊 B 型日誌家族（sys_access_log／sys_login_attempt 皆有、GeoIP 填值） |
| sys_operation_log.trace_id 型別 | varchar(64) → text | 對齊 sys_access_log 家族形 |

### memo 欄家族語意（data-model 凍結；活書一行＝刀內施工項）

user_memo／role_memo／menu_memo／wbip_memo（text 可多行）：R_SUPER 備註用途；顯示於
**管理列表**；不顯示於其它被取用處（下拉、引用、對外 API 一律不帶）。rev4 設計入 schema 但
各 UI 刀 brainstorm 均未兌現——rev5 以 BACKLOG B-003 承載提醒（brainstorm 直接輸入機制）。
另 role_desc（upstream UI「角色描述」、使用者可見）與 role_memo 職責不同、兩欄並存不合併。

## 6. 隨做隨記

- BACKLOG B-003 已 append（memo 欄家族 UI 兌現、四張管理列表）；後隨 ports-2xxxx 維護批衍生
  B-004（前代 ADR 指涉清償）、B-005（watchdog 目標參數），next-id 現為 B-006。
- 活書 ARCHITECTURE.md 資料慣例節加 memo 家族一行＝刀內施工項（活書改動走 feature branch）。
- 兩支 ADR draft＝刀內首批施工項（見 §0）。
