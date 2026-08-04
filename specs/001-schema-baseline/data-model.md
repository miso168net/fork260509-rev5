# data-model — 001-schema-baseline（凍結定稿）

> **權威聲明**：本檔轉錄 brainstorm 001 §5 欄序定稿（user 逐表親排、2026-08-05 總確認）＋
> clarify seed 定稿（user 總簽核 2026-08-05）。**自本檔入版起：欄序／欄名／型別之權威＝
> 本檔，brainstorm 轉史料**（brainstorm 001 檔頭預告條款兌現）。
> 結構語意除 §4「定稿差異」載明者外，一律忠實 rev4 終態快照（provenance＝rev4 repo @
> `2b8a101` 之 `docs/ops/reference-src/schema-snapshot.json`；本刀 clarify 已容器內重放
> 十五支 migration 雙源互證、columns／indexes／constraints 三節全等）。
> **機器轉錄**：§2／§6／§7 表體由工具自 rev4 快照＋定稿欄序生成（斷言：逐表欄集合全等、
> 總欄數 169、`operator_` 字樣零殘留）——非手工抄錄；生成器＝scratchpad
> `gen-data-model.py`（一次性、隨 session 消滅，重生成可自本檔規則重建）。

## 1. archetype 歸屬（15 表；憲法 §I.6 四變體）

> 承 rev4 archetype-map（已驗證歸屬帳）；`docs/ops/reference-src/archetype-map.json` 初版
> 由本節轉錄（audit 閘與 reference/schema 同源消費）。後續刀新表：先補本節歸屬、再登記
> archetype-map，否則 audit 攔。

| 表 | 變體 | 活性唯一（索引名） | 註 |
|---|---|---|---|
| sys_user | A 業務全六欄 | sys_user_user_name_active_uniq＋sys_user_user_email_active_uniq | 六欄全；兩支 partial-uniq `WHERE deleted_at IS NULL`（email 支另含 `user_email IS NOT NULL`、lower() 表達式） |
| sys_role | A 業務全六欄 | sys_role_code_active_uniq | 六欄全；活性唯一 |
| sys_menu | A 業務全六欄 | sys_menu_route_name_active_uniq | 六欄全；活性唯一 |
| system_settings | A 業務全六欄 | ——（null） | 六欄全（PK＝setting_key 總體唯一、免 partial-uniq） |
| sys_ip_rule | A 業務全六欄 | sys_ip_rule_cidr_type_active_uniq | 六欄全；複合 (wbip_cidr, wbip_type) 活性唯一 |
| sys_operation_log | B append-only | —— | 僅 created_at NN＋created_by（operator 域欄）；禁 updated_*／deleted_*；鑑識欄群＝rename 後定稿名（§3） |
| sys_access_log | B append-only | —— | 僅 created_at NN＋created_by（NN）；禁 updated_*／deleted_* |
| sys_login_attempt | B append-only | —— | 僅 created_at NN＋created_by（可空）；禁 updated_*／deleted_* |
| session_event | B append-only | —— | 僅 created_at NN＋created_by（可空）；禁 updated_*／deleted_* |
| sys_user_role | C join | —— | 零審計欄、硬刪；複合 PK＋2 FK |
| sys_token | C 狀態機 | —— | created_at NN＋created_by NN＋status；created_by＝domain 擁有者欄（非 archetype 審計欄、NN 不受「*_by nullable」通則約束） |
| sys_pwd_custody | C 極簡 | —— | 複合 PK (user_id, created_by)；created_at＝最後設定時間（upsert 刷新）；零 FK；不存密碼 |
| sys_user_email_verify | C 衛星 | —— | 單一 PK user_id；verified_at＝最後驗證時刻（upsert 刷新）；零 FK；不存驗證碼 |
| sys_casbin_policy_archive | D 治理 | —— | created_at/by（原 grant 快照、可空）＋archived_at NN def now()＋archived_by＋archive_reason NN |
| casbin_rule | D 治理 | —— | adapter 基底 8 欄＋ALTER 治理欄（protected NN def false／created_at NN def now()／created_by 可空）；欄序不入親排（§7） |

**`*_by` 欄性質判準**（audit 閘可空性期望之左源）：語意為**變更操作者**之 `*_by`＝archetype
審計欄、受 §I.6「*_by nullable」通則；語意為**資料擁有者／請求主體／複合 PK 成分／首建者**
者＝domain 欄、可 NN。本刀 created_by NN 恰四表、逐表釋義：sys_access_log（B、請求主體
紀錄、NN）／sys_token（C、擁有者欄）／sys_pwd_custody（C、複合 PK 成分）／
sys_user_email_verify（C、首建者、NN）；其餘表之 created_by 一律可空。

## 2. 逐表欄序定稿（14 親排表 158 欄＋casbin_rule 11 欄＝169 欄）

### sys_user（17 欄；變體 A）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_user_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | updated_at | timestamp with time zone | 可空 | —— |  |
| 5 | updated_by | bigint | 可空 | —— |  |
| 6 | deleted_at | timestamp with time zone | 可空 | —— |  |
| 7 | deleted_by | bigint | 可空 | —— |  |
| 8 | status | smallint | 可空 | —— |  |
| 9 | user_gender | smallint | 可空 | —— |  |
| 10 | user_name | character varying | NN | —— |  |
| 11 | password | character varying | NN | —— |  |
| 12 | nick_name | character varying | 可空 | —— |  |
| 13 | session_policy | character varying(20) | NN | 'inherit'::character varying |  |
| 14 | session_id | character varying(36) | 可空 | —— |  |
| 15 | user_phone | character varying | 可空 | —— |  |
| 16 | user_email | character varying | 可空 | —— |  |
| 17 | user_memo | text | 可空 | —— |  |

### sys_role（13 欄；變體 A）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_role_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | updated_at | timestamp with time zone | 可空 | —— |  |
| 5 | updated_by | bigint | 可空 | —— |  |
| 6 | deleted_at | timestamp with time zone | 可空 | —— |  |
| 7 | deleted_by | bigint | 可空 | —— |  |
| 8 | status | smallint | 可空 | —— |  |
| 9 | role_code | character varying | NN | —— |  |
| 10 | role_name | character varying | NN | —— |  |
| 11 | role_memo | text | 可空 | —— |  |
| 12 | role_home | character varying | 可空 | —— |  |
| 13 | role_desc | character varying | 可空 | —— |  |

### sys_menu（29 欄；變體 A）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_menu_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | updated_at | timestamp with time zone | 可空 | —— |  |
| 5 | updated_by | bigint | 可空 | —— |  |
| 6 | deleted_at | timestamp with time zone | 可空 | —— |  |
| 7 | deleted_by | bigint | 可空 | —— |  |
| 8 | status | smallint | 可空 | —— |  |
| 9 | order | integer | 可空 | —— |  |
| 10 | hide_in_menu | boolean | 可空 | —— |  |
| 11 | keep_alive | boolean | 可空 | —— |  |
| 12 | constant | boolean | 可空 | —— |  |
| 13 | multi_tab | boolean | 可空 | —— |  |
| 14 | protected | boolean | NN | false |  |
| 15 | parent_id | bigint | 可空 | —— |  |
| 16 | menu_type | smallint | 可空 | —— |  |
| 17 | menu_name | character varying | NN | —— |  |
| 18 | menu_memo | text | 可空 | —— |  |
| 19 | route_name | character varying | NN | —— |  |
| 20 | route_path | character varying | 可空 | —— |  |
| 21 | component | character varying | 可空 | —— |  |
| 22 | icon | character varying | 可空 | —— |  |
| 23 | icon_type | smallint | 可空 | —— |  |
| 24 | i18n_key | character varying | 可空 | —— |  |
| 25 | href | character varying | 可空 | —— |  |
| 26 | active_menu | character varying | 可空 | —— |  |
| 27 | fixed_index_in_tab | integer | 可空 | —— |  |
| 28 | query | jsonb | 可空 | —— |  |
| 29 | buttons | jsonb | 可空 | —— |  |

### sys_ip_rule（11 欄；變體 A）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_ip_rule_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | updated_at | timestamp with time zone | 可空 | —— |  |
| 5 | updated_by | bigint | 可空 | —— |  |
| 6 | deleted_at | timestamp with time zone | 可空 | —— |  |
| 7 | deleted_by | bigint | 可空 | —— |  |
| 8 | order | integer | 可空 | —— |  |
| 9 | wbip_type | character varying | NN | —— |  |
| 10 | wbip_cidr | inet | NN | —— |  |
| 11 | wbip_memo | text | 可空 | —— |  |

### system_settings（10 欄；變體 A）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | setting_key | character varying(64) | NN | —— |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | updated_at | timestamp with time zone | 可空 | —— |  |
| 5 | updated_by | bigint | 可空 | —— |  |
| 6 | deleted_at | timestamp with time zone | 可空 | —— |  |
| 7 | deleted_by | bigint | 可空 | —— |  |
| 8 | setting_type | character varying | NN | —— |  |
| 9 | setting_value | character varying | NN | —— |  |
| 10 | description | character varying | 可空 | —— |  |

### sys_access_log（12 欄；變體 B）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_access_log_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | NN | —— |  |
| 4 | http_status | integer | NN | —— |  |
| 5 | http_method | text | NN | —— |  |
| 6 | http_path | text | NN | —— |  |
| 7 | real_ip | inet | NN | —— |  |
| 8 | peer_ip | inet | 可空 | —— |  |
| 9 | x_forwarded_for | text | 可空 | —— |  |
| 10 | ip_confidence | text | 可空 | —— |  |
| 11 | region | text | 可空 | —— |  |
| 12 | trace_id | text | 可空 | —— |  |

### sys_login_attempt（11 欄；變體 B）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_login_attempt_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | success | boolean | NN | —— |  |
| 5 | attempted_user_name | text | NN | —— |  |
| 6 | real_ip | inet | NN | —— |  |
| 7 | peer_ip | inet | 可空 | —— |  |
| 8 | x_forwarded_for | text | 可空 | —— |  |
| 9 | ip_confidence | text | 可空 | —— |  |
| 10 | region | text | 可空 | —— |  |
| 11 | trace_id | text | 可空 | —— |  |

### sys_token（9 欄；變體 C）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_token_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | NN | —— |  |
| 4 | status | character varying(20) | NN | —— |  |
| 5 | token_hash | character varying(64) | NN | —— |  |
| 6 | rotation_chain | character varying(36) | NN | —— |  |
| 7 | issued_at | timestamp with time zone | NN | —— |  |
| 8 | expires_at | timestamp with time zone | NN | —— |  |
| 9 | used_at | timestamp with time zone | 可空 | —— |  |

### sys_user_role（2 欄；變體 C）

欄序 vs rev4 終態：照舊

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | user_id | bigint | NN | —— |  |
| 2 | role_id | bigint | NN | —— |  |

### session_event（8 欄；變體 B）

欄序 vs rev4 終態：調序：created_by 由第 7 位上移第 3 位（對齊審計欄群慣例）

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('session_event_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | user_id | bigint | NN | —— |  |
| 5 | sid | character varying(36) | NN | —— |  |
| 6 | event_type | character varying(20) | NN | —— |  |
| 7 | reason | character varying(64) | 可空 | —— |  |
| 8 | source_ip | character varying(45) | 可空 | —— |  |

### sys_operation_log（14 欄；變體 B）

欄序 vs rev4 終態：綜合調整：改名×4（§3）；region ★新增；trace_id ★改 text

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_operation_log_id_seq'::regclass) |  |
| 2 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 3 | created_by | bigint | 可空 | —— |  |
| 4 | operation | character varying(20) | NN | —— |  |
| 5 | entity_table | character varying(64) | NN | —— |  |
| 6 | entity_id | bigint | 可空 | —— |  |
| 7 | payload_before | jsonb | 可空 | —— |  |
| 8 | payload_after | jsonb | 可空 | —— |  |
| 9 | real_ip | inet | 可空 | —— | 改名（原 operator_real_ip） |
| 10 | peer_ip | inet | 可空 | —— | 改名（原 operator_peer_ip） |
| 11 | x_forwarded_for | text | 可空 | —— | 改名（原 operator_x_forwarded_for） |
| 12 | ip_confidence | text | 可空 | —— | 改名（原 operator_ip_confidence） |
| 13 | region | text | 可空 | —— | ★新增（定稿差異） |
| 14 | trace_id | text | 可空 | —— | ★型別改 text（rev4＝varchar(64)） |

### sys_pwd_custody（3 欄；變體 C）

欄序 vs rev4 終態：調序：後兩欄交換（複合 PK＝(user_id, created_by) 內部序屬語意、原樣不動）

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | user_id | bigint | NN | —— |  |
| 2 | created_at | timestamp with time zone | NN | now() |  |
| 3 | created_by | bigint | NN | —— |  |

### sys_user_email_verify（5 欄；變體 C）

欄序 vs rev4 終態：調序：審計欄群上移、verified 對殿後

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | user_id | bigint | NN | —— |  |
| 2 | created_at | timestamp with time zone | NN | now() |  |
| 3 | created_by | bigint | NN | —— |  |
| 4 | verified_at | timestamp with time zone | NN | —— |  |
| 5 | verified_email | character varying | NN | —— |  |

### sys_casbin_policy_archive（14 欄；變體 D）

欄序 vs rev4 終態：調序：role_id 由末位上移第 2 位

| # | 欄 | 型別 | NULL | default | 註 |
|---|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('sys_casbin_policy_archive_id_seq'::regclass) |  |
| 2 | role_id | bigint | 可空 | —— |  |
| 3 | created_at | timestamp with time zone | 可空 | —— |  |
| 4 | created_by | bigint | 可空 | —— |  |
| 5 | archived_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |  |
| 6 | archived_by | bigint | 可空 | —— |  |
| 7 | archive_reason | character varying(32) | NN | —— |  |
| 8 | ptype | character varying(18) | NN | —— |  |
| 9 | v0 | character varying(125) | NN | —— |  |
| 10 | v1 | character varying(125) | NN | —— |  |
| 11 | v2 | character varying(125) | NN | —— |  |
| 12 | v3 | character varying(125) | NN | ''::character varying |  |
| 13 | v4 | character varying(125) | NN | ''::character varying |  |
| 14 | v5 | character varying(125) | NN | ''::character varying |  |


## 3. rename map（4 組、全在 sys_operation_log；閘對 rev4 血緣對賬走此映射）

| rev4 終態欄名 | rev5 定稿欄名 |
|---|---|
| operator_real_ip | real_ip |
| operator_peer_ip | peer_ip |
| operator_x_forwarded_for | x_forwarded_for |
| operator_ip_confidence | ip_confidence |

> 射程註記：映射僅用於「vs rev4 快照」的血緣核對場景；rev5 自家管線（fixtures／refresh
> 快照／entity／seed）一律新欄名。rev4 快照中 `operator_` 僅出現於此 4 欄欄名與兩個索引
> **名稱**（`idx_access_log_operator_time`／`idx_operation_log_operator_time`，皆索引
> `(created_by, created_at)`、名稱語意＝operator=created_by）——**改名對一切索引／約束
> 定義零影響**（機器斷言在案）；兩索引名照 rev4 原樣保留。

## 4. 定稿差異（非純重排、對 rev4 終態的全部偏離）

| 項 | 內容 | 理由 |
|---|---|---|
| sys_operation_log.region 新增 | text、可空、無 default | 對齊 B 型日誌家族（sys_access_log／sys_login_attempt 皆有、GeoIP 填值） |
| sys_operation_log.trace_id 型別 | varchar(64) → text | 對齊 sys_access_log 家族形 |
| 欄序重排 5 表 | session_event／sys_operation_log／sys_pwd_custody／sys_user_email_verify／sys_casbin_policy_archive | user 親排定稿（§2 各表註記差異；語意不變） |
| 表欄更名 4 組 | §3 rename map | 去 operator_ 前綴（B 型家族欄名對齊） |

以上即全部偏離；此外 rev5 新結構差異＝零支（純壓平、無新能力面）。

## 5. memo 欄家族語意（凍結）

user_memo／role_memo／menu_memo／wbip_memo（text 可空、可多行）：R_SUPER 備註用途；
顯示於**管理列表**；不顯示於其它被取用處（下拉、引用、對外 API 一律不帶）。
role_desc（upstream UI「角色描述」、使用者可見）與 role_memo 職責不同、兩欄並存不合併。
UI 兌現不在本刀（BACKLOG B-003 承載；活書資料慣例節同刀加一行）。

## 6. 索引與約束（忠實 rev4 終態、機器轉錄；gate1 比對面）

> 前置：`CREATE EXTENSION IF NOT EXISTS pg_trgm`（GIN trigram 索引相依、承 rev4:m009
> 淨效果、隨 m001）。NOT NULL 逐欄約束為 pg_constraint 實報形（PG18）、隨建表自動生成。

總計：索引 38 支、約束 100 條（含 NOT NULL 逐欄形）。

### casbin_rule

索引（2）：

- `casbin_rule_pkey`：`CREATE UNIQUE INDEX casbin_rule_pkey ON public.casbin_rule USING btree (id)`
- `unique_key_sea_orm_adapter`：`CREATE UNIQUE INDEX unique_key_sea_orm_adapter ON public.casbin_rule USING btree (ptype, v0, v1, v2, v3, v4, v5)`

約束（12）：

- `casbin_rule_created_at_not_null`：`NOT NULL created_at`
- `casbin_rule_id_not_null`：`NOT NULL id`
- `casbin_rule_pkey`：`PRIMARY KEY (id)`
- `casbin_rule_protected_not_null`：`NOT NULL protected`
- `casbin_rule_ptype_not_null`：`NOT NULL ptype`
- `casbin_rule_v0_not_null`：`NOT NULL v0`
- `casbin_rule_v1_not_null`：`NOT NULL v1`
- `casbin_rule_v2_not_null`：`NOT NULL v2`
- `casbin_rule_v3_not_null`：`NOT NULL v3`
- `casbin_rule_v4_not_null`：`NOT NULL v4`
- `casbin_rule_v5_not_null`：`NOT NULL v5`
- `unique_key_sea_orm_adapter`：`UNIQUE (ptype, v0, v1, v2, v3, v4, v5)`

### session_event

索引（2）：

- `idx_session_event_user_time`：`CREATE INDEX idx_session_event_user_time ON public.session_event USING btree (user_id, created_at)`
- `session_event_pkey`：`CREATE UNIQUE INDEX session_event_pkey ON public.session_event USING btree (id)`

約束（6）：

- `session_event_created_at_not_null`：`NOT NULL created_at`
- `session_event_event_type_not_null`：`NOT NULL event_type`
- `session_event_id_not_null`：`NOT NULL id`
- `session_event_pkey`：`PRIMARY KEY (id)`
- `session_event_sid_not_null`：`NOT NULL sid`
- `session_event_user_id_not_null`：`NOT NULL user_id`

### sys_access_log

索引（4）：

- `idx_access_log_created_at`：`CREATE INDEX idx_access_log_created_at ON public.sys_access_log USING btree (created_at)`
- `idx_access_log_operator_time`：`CREATE INDEX idx_access_log_operator_time ON public.sys_access_log USING btree (created_by, created_at)`
- `idx_access_log_path_trgm`：`CREATE INDEX idx_access_log_path_trgm ON public.sys_access_log USING gin (http_path gin_trgm_ops)`
- `sys_access_log_pkey`：`CREATE UNIQUE INDEX sys_access_log_pkey ON public.sys_access_log USING btree (id)`

約束（8）：

- `sys_access_log_created_at_not_null`：`NOT NULL created_at`
- `sys_access_log_created_by_not_null`：`NOT NULL created_by`
- `sys_access_log_http_method_not_null`：`NOT NULL http_method`
- `sys_access_log_http_path_not_null`：`NOT NULL http_path`
- `sys_access_log_http_status_not_null`：`NOT NULL http_status`
- `sys_access_log_id_not_null`：`NOT NULL id`
- `sys_access_log_pkey`：`PRIMARY KEY (id)`
- `sys_access_log_real_ip_not_null`：`NOT NULL real_ip`

### sys_casbin_policy_archive

索引（3）：

- `idx_casbin_archive_archived_at`：`CREATE INDEX idx_casbin_archive_archived_at ON public.sys_casbin_policy_archive USING btree (archived_at)`
- `idx_casbin_archive_role_dim`：`CREATE INDEX idx_casbin_archive_role_dim ON public.sys_casbin_policy_archive USING btree (v0, v2)`
- `sys_casbin_policy_archive_pkey`：`CREATE UNIQUE INDEX sys_casbin_policy_archive_pkey ON public.sys_casbin_policy_archive USING btree (id)`

約束（11）：

- `sys_casbin_policy_archive_archive_reason_not_null`：`NOT NULL archive_reason`
- `sys_casbin_policy_archive_archived_at_not_null`：`NOT NULL archived_at`
- `sys_casbin_policy_archive_id_not_null`：`NOT NULL id`
- `sys_casbin_policy_archive_pkey`：`PRIMARY KEY (id)`
- `sys_casbin_policy_archive_ptype_not_null`：`NOT NULL ptype`
- `sys_casbin_policy_archive_v0_not_null`：`NOT NULL v0`
- `sys_casbin_policy_archive_v1_not_null`：`NOT NULL v1`
- `sys_casbin_policy_archive_v2_not_null`：`NOT NULL v2`
- `sys_casbin_policy_archive_v3_not_null`：`NOT NULL v3`
- `sys_casbin_policy_archive_v4_not_null`：`NOT NULL v4`
- `sys_casbin_policy_archive_v5_not_null`：`NOT NULL v5`

### sys_ip_rule

索引（2）：

- `sys_ip_rule_cidr_type_active_uniq`：`CREATE UNIQUE INDEX sys_ip_rule_cidr_type_active_uniq ON public.sys_ip_rule USING btree (wbip_cidr, wbip_type) WHERE (deleted_at IS NULL)`
- `sys_ip_rule_pkey`：`CREATE UNIQUE INDEX sys_ip_rule_pkey ON public.sys_ip_rule USING btree (id)`

約束（5）：

- `sys_ip_rule_created_at_not_null`：`NOT NULL created_at`
- `sys_ip_rule_id_not_null`：`NOT NULL id`
- `sys_ip_rule_pkey`：`PRIMARY KEY (id)`
- `sys_ip_rule_wbip_cidr_not_null`：`NOT NULL wbip_cidr`
- `sys_ip_rule_wbip_type_not_null`：`NOT NULL wbip_type`

### sys_login_attempt

索引（5）：

- `idx_login_attempt_created_at`：`CREATE INDEX idx_login_attempt_created_at ON public.sys_login_attempt USING btree (created_at)`
- `idx_login_attempt_ip_time`：`CREATE INDEX idx_login_attempt_ip_time ON public.sys_login_attempt USING btree (real_ip, created_at)`
- `idx_login_attempt_user_name_trgm`：`CREATE INDEX idx_login_attempt_user_name_trgm ON public.sys_login_attempt USING gin (attempted_user_name gin_trgm_ops)`
- `idx_login_attempt_user_time`：`CREATE INDEX idx_login_attempt_user_time ON public.sys_login_attempt USING btree (attempted_user_name, created_at)`
- `sys_login_attempt_pkey`：`CREATE UNIQUE INDEX sys_login_attempt_pkey ON public.sys_login_attempt USING btree (id)`

約束（6）：

- `sys_login_attempt_attempted_user_name_not_null`：`NOT NULL attempted_user_name`
- `sys_login_attempt_created_at_not_null`：`NOT NULL created_at`
- `sys_login_attempt_id_not_null`：`NOT NULL id`
- `sys_login_attempt_pkey`：`PRIMARY KEY (id)`
- `sys_login_attempt_real_ip_not_null`：`NOT NULL real_ip`
- `sys_login_attempt_success_not_null`：`NOT NULL success`

### sys_menu

索引（2）：

- `sys_menu_pkey`：`CREATE UNIQUE INDEX sys_menu_pkey ON public.sys_menu USING btree (id)`
- `sys_menu_route_name_active_uniq`：`CREATE UNIQUE INDEX sys_menu_route_name_active_uniq ON public.sys_menu USING btree (route_name) WHERE (deleted_at IS NULL)`

約束（6）：

- `sys_menu_created_at_not_null`：`NOT NULL created_at`
- `sys_menu_id_not_null`：`NOT NULL id`
- `sys_menu_menu_name_not_null`：`NOT NULL menu_name`
- `sys_menu_pkey`：`PRIMARY KEY (id)`
- `sys_menu_protected_not_null`：`NOT NULL protected`
- `sys_menu_route_name_not_null`：`NOT NULL route_name`

### sys_operation_log

索引（3）：

- `idx_operation_log_created_at`：`CREATE INDEX idx_operation_log_created_at ON public.sys_operation_log USING btree (created_at)`
- `idx_operation_log_operator_time`：`CREATE INDEX idx_operation_log_operator_time ON public.sys_operation_log USING btree (created_by, created_at)`
- `sys_operation_log_pkey`：`CREATE UNIQUE INDEX sys_operation_log_pkey ON public.sys_operation_log USING btree (id)`

約束（5）：

- `sys_operation_log_created_at_not_null`：`NOT NULL created_at`
- `sys_operation_log_entity_table_not_null`：`NOT NULL entity_table`
- `sys_operation_log_id_not_null`：`NOT NULL id`
- `sys_operation_log_operation_not_null`：`NOT NULL operation`
- `sys_operation_log_pkey`：`PRIMARY KEY (id)`

### sys_pwd_custody

索引（1）：

- `sys_pwd_custody_pkey`：`CREATE UNIQUE INDEX sys_pwd_custody_pkey ON public.sys_pwd_custody USING btree (user_id, created_by)`

約束（4）：

- `sys_pwd_custody_created_at_not_null`：`NOT NULL created_at`
- `sys_pwd_custody_created_by_not_null`：`NOT NULL created_by`
- `sys_pwd_custody_pkey`：`PRIMARY KEY (user_id, created_by)`
- `sys_pwd_custody_user_id_not_null`：`NOT NULL user_id`

### sys_role

索引（2）：

- `sys_role_code_active_uniq`：`CREATE UNIQUE INDEX sys_role_code_active_uniq ON public.sys_role USING btree (role_code) WHERE (deleted_at IS NULL)`
- `sys_role_pkey`：`CREATE UNIQUE INDEX sys_role_pkey ON public.sys_role USING btree (id)`

約束（5）：

- `sys_role_created_at_not_null`：`NOT NULL created_at`
- `sys_role_id_not_null`：`NOT NULL id`
- `sys_role_pkey`：`PRIMARY KEY (id)`
- `sys_role_role_code_not_null`：`NOT NULL role_code`
- `sys_role_role_name_not_null`：`NOT NULL role_name`

### sys_token

索引（6）：

- `idx_sys_token_chain`：`CREATE INDEX idx_sys_token_chain ON public.sys_token USING btree (rotation_chain)`
- `idx_sys_token_expires_at`：`CREATE INDEX idx_sys_token_expires_at ON public.sys_token USING btree (expires_at)`
- `idx_sys_token_user_active`：`CREATE INDEX idx_sys_token_user_active ON public.sys_token USING btree (created_by) WHERE ((status)::text = 'active'::text)`
- `sys_token_pkey`：`CREATE UNIQUE INDEX sys_token_pkey ON public.sys_token USING btree (id)`
- `sys_token_token_hash_key`：`CREATE UNIQUE INDEX sys_token_token_hash_key ON public.sys_token USING btree (token_hash)`
- `uq_sys_token_chain_active`：`CREATE UNIQUE INDEX uq_sys_token_chain_active ON public.sys_token USING btree (rotation_chain) WHERE ((status)::text = 'active'::text)`

約束（10）：

- `sys_token_created_at_not_null`：`NOT NULL created_at`
- `sys_token_created_by_not_null`：`NOT NULL created_by`
- `sys_token_expires_at_not_null`：`NOT NULL expires_at`
- `sys_token_id_not_null`：`NOT NULL id`
- `sys_token_issued_at_not_null`：`NOT NULL issued_at`
- `sys_token_pkey`：`PRIMARY KEY (id)`
- `sys_token_rotation_chain_not_null`：`NOT NULL rotation_chain`
- `sys_token_status_not_null`：`NOT NULL status`
- `sys_token_token_hash_key`：`UNIQUE (token_hash)`
- `sys_token_token_hash_not_null`：`NOT NULL token_hash`

### sys_user

索引（3）：

- `sys_user_pkey`：`CREATE UNIQUE INDEX sys_user_pkey ON public.sys_user USING btree (id)`
- `sys_user_user_email_active_uniq`：`CREATE UNIQUE INDEX sys_user_user_email_active_uniq ON public.sys_user USING btree (lower((user_email)::text)) WHERE ((deleted_at IS NULL) AND (user_email IS NOT NULL))`
- `sys_user_user_name_active_uniq`：`CREATE UNIQUE INDEX sys_user_user_name_active_uniq ON public.sys_user USING btree (user_name) WHERE (deleted_at IS NULL)`

約束（6）：

- `sys_user_created_at_not_null`：`NOT NULL created_at`
- `sys_user_id_not_null`：`NOT NULL id`
- `sys_user_password_not_null`：`NOT NULL password`
- `sys_user_pkey`：`PRIMARY KEY (id)`
- `sys_user_session_policy_not_null`：`NOT NULL session_policy`
- `sys_user_user_name_not_null`：`NOT NULL user_name`

### sys_user_email_verify

索引（1）：

- `pk_sys_user_email_verify`：`CREATE UNIQUE INDEX pk_sys_user_email_verify ON public.sys_user_email_verify USING btree (user_id)`

約束（6）：

- `pk_sys_user_email_verify`：`PRIMARY KEY (user_id)`
- `sys_user_email_verify_created_at_not_null`：`NOT NULL created_at`
- `sys_user_email_verify_created_by_not_null`：`NOT NULL created_by`
- `sys_user_email_verify_user_id_not_null`：`NOT NULL user_id`
- `sys_user_email_verify_verified_at_not_null`：`NOT NULL verified_at`
- `sys_user_email_verify_verified_email_not_null`：`NOT NULL verified_email`

### sys_user_role

索引（1）：

- `sys_user_role_pkey`：`CREATE UNIQUE INDEX sys_user_role_pkey ON public.sys_user_role USING btree (user_id, role_id)`

約束（5）：

- `fk_sys_user_role_role`：`FOREIGN KEY (role_id) REFERENCES sys_role(id) ON DELETE RESTRICT`
- `fk_sys_user_role_user`：`FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE RESTRICT`
- `sys_user_role_pkey`：`PRIMARY KEY (user_id, role_id)`
- `sys_user_role_role_id_not_null`：`NOT NULL role_id`
- `sys_user_role_user_id_not_null`：`NOT NULL user_id`

### system_settings

索引（1）：

- `system_settings_pkey`：`CREATE UNIQUE INDEX system_settings_pkey ON public.system_settings USING btree (setting_key)`

約束（5）：

- `system_settings_created_at_not_null`：`NOT NULL created_at`
- `system_settings_pkey`：`PRIMARY KEY (setting_key)`
- `system_settings_setting_key_not_null`：`NOT NULL setting_key`
- `system_settings_setting_type_not_null`：`NOT NULL setting_type`
- `system_settings_setting_value_not_null`：`NOT NULL setting_value`


## 7. casbin_rule（委派建表；欄序參考、不入親排比對）

沿 rev4 形（provenance rev4:ADR 0015／K1-15）：m001 委派 vendored `sea-orm-adapter` 建
基底 8 欄，同檔 ALTER 補 3 治理欄。欄序由建表機制決定——下表僅為參考快照形；gate2 欄序
比對豁免本表（僅驗結構語意與 archetype 歸屬）。entity 面完整（casbin_rule.rs 在場）、
entity-drift 比對豁免本表。

| # | 欄 | 型別 | NULL | default |
|---|---|---|---|---|
| 1 | id | bigint | NN | nextval('casbin_rule_id_seq'::regclass) |
| 2 | ptype | character varying(18) | NN | —— |
| 3 | v0 | character varying(125) | NN | —— |
| 4 | v1 | character varying(125) | NN | —— |
| 5 | v2 | character varying(125) | NN | —— |
| 6 | v3 | character varying(125) | NN | —— |
| 7 | v4 | character varying(125) | NN | —— |
| 8 | v5 | character varying(125) | NN | —— |
| 9 | protected | boolean | NN | false |
| 10 | created_at | timestamp with time zone | NN | CURRENT_TIMESTAMP |
| 11 | created_by | bigint | 可空 | —— |

## 8. seed 定稿（m002 唯一來源）

- **內容權威**＝`specs/001-schema-baseline/seed-decision.json`（clarify 定稿機器檔：
  rev4 淨效果素材 sha256 血緣＋Q1／Q2 裁定；過目紀錄＝seed-review.md）。**m002 施工時
  機器轉錄、禁止手抄**。
- 規模：266 列——casbin_rule 163＋sys_menu 78＋system_settings 16＋sys_user 3＋sys_role 3
  ＋sys_user_role 3；其餘 9 表零列。
- **決定性施工形**（clarify Q1＝甲・全面定稿字面）：
  - 凡具 id 欄之表**明示 id**（247 列、不吃 nextval；system_settings PK＝setting_key、
    sys_user_role 零審計 join 表——兩表無 id 欄、不在此射程）；凡具 `created_at` 欄者
    **明示定稿時戳 `2026-08-05T00:00:00+00:00`**（263 列、不吃欄 default）；凡具
    `created_by` 欄者一律 NULL。
  - `sys_user.password`＝定稿 PHC 常數（三帳共用、plaintext `123456`、全文載
    seed-review.md 定稿節）；m002 **無 runtime 雜湊**（不引 argon2）。
  - casbin_rule 163 列與 sys_menu 78 列之 `protected` 值逐列明示（casbin true×19、
    menu true×8；總數以 seed-decision.json 現算為準、施工斷言禁寫死字面）。
  - 收尾 `setval` 對齊 sequence 落值（§9）。
- 簡繁定稿：22 筆改值（Q2；含 `登录→登入`、`菜单→選單` 修正）已固化於 seed-decision.json
  ——m002 不做任何 runtime 轉換。
- `hide_in_menu` 6 列 true（id 6 manage_user-detail／16 user-center／22 function_multi-tab／
  58·59·60 function_hide-child_*）＝upstream route meta 原樣、非 §I.2 隱藏治理——釋義與
  白名單＝ADR 0005。
- 4 列選單之 `component` 指向 view 於 rev5 base-web 尚缺（manage_system-settings／
  manage_policy-archive／manage_audit／manage_ip-rule）——選單與政策隨基線先行、view 由
  對應 UI 刀補齊（BACKLOG B-008）。

## 9. sequences 落值（m002 收尾 setval；gate2／SC-001 比對面含此）

| sequence | 落值 |
|---|---|
| casbin_rule_id_seq | 163 |
| sys_menu_id_seq | 78 |
| sys_role_id_seq | 3 |
| sys_user_id_seq | 3 |
| 其餘 7 支（session_event／sys_access_log／sys_casbin_policy_archive／sys_ip_rule／sys_login_attempt／sys_operation_log／sys_token） | 未動用（不 setval） |

## 10. 防回歸條款（§I.5 防回歸 ＋ 本刀射程界定）

1. `operator_` 前綴欄名與 `trace_id varchar(64)` 為 rev5 拍板已推翻之形——參照 rev4 source
   施工時**不得帶回**。
2. seed 簡體原值（role_name／buttons desc）與 password runtime 隨機雜湊為已推翻之形——
   **不得帶回** m002。
3. rev4 m003～m015 為其後續刀 delta、淨效果已含於終態——**不搬**；rev5 第一支 delta 自
   m003 起編（短編號紀律承 K1-13）。
4. reaper DB role＋GRANTs（rev4:m012／m013）**不入基線**——非三節快照射程、屬
   observability 域運維工件、隨該域刀重進場（research R4、provenance rev4:ADR 0072）。
5. fixtures 凍結後永不改寫；基線翻案＝新刀新 ADR（supersedes），不回改本檔。
