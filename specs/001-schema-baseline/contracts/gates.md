# contracts/gates.md — 三閘行為契約（tools/schema-gate.py 重建依據）

> 本檔＝閘的**行為契約**：實作必須滿足、測試自此推導。lineage：spec FR-008～FR-011、
> research R5／R6、data-model §2／§6／§9、ADR 待立②（閘契約＝Day-1 受管演進帳）。

## 0. 共通紀律

- **退出碼**（沿 repo 工具慣例）：`0` 全綠／`1` 漂移（逐項指名）／`2` 環境或結構異常
  （fixtures 缺、登記檔壞形、庫不可達、比對面為空——附補救提示）／`64` 用法錯誤。
- **self-test 無條件合成**（沿 tools/entity-drift-gate.py 模式）：check 入口先以合成
  fixtures×合成庫照相跑「健康對必綠＋注入假漂移必紅」；self-test 敗＝rc 2 指名比對邏輯壞、
  **不讀任何真檔**（防恆綠假閘）。
- **零容差語意**：一切比對＝全等；「容差」只有一種合法形＝演進帳登記（§2）。
- 實庫照相＝與 tools/docs-sync.py refresh 同構之三查詢（columns／indexes／constraints、
  排除 seaql_migrations、確定性排序）。
- python 標準庫單檔、秒級、自帶 `test` 子命令（pre-commit 條件觸發自測既有接線）。

## 1. gate1 結構閘（凍結＋演進帳合成 → 全等）

- **左源（期望）**：`specs/001-schema-baseline/fixtures/{columns,indexes,constraints}.json`
  （凍結面、永不改寫）⊕ `docs/ops/reference-src/schema-evolution.json`（演進面）合成：
  依 entries 逐筆把 add_table／add_column／alter_column／add_index／add_constraint 疊加到
  凍結基底，得「當下期望結構」。
- **右源（實際）**：實庫照相三節。
- **判準**：三節逐列全等。任何未登記差異＝紅（rc 1、指名 section＋table＋名稱＋左右值）；
  登記了但實庫沒有＝同樣紅（登記超前也是漂移）。
- **啟動斷言**：fixtures 三檔在場且形合（list[dict]、鍵集恰合）；演進帳過形檢
  （contracts/schema-evolution.md §2）——任一敗＝rc 2。

## 2. gate2 欄序＋seed 閘（vs data-model 定稿）

- **欄序面**：左源＝data-model.md §2 逐表欄序表（解析「| # | 欄 |」表體）；右源＝實庫
  information_schema ordinal。14 親排表逐表逐欄位置全等；**casbin_rule 豁免欄序**（僅
  gate1 結構語意＋audit 歸屬）。演進帳 add_column 之新欄＝接在該表末位（登記時帶
  position、預設殿後）。
- **seed 面**：左源＝`fixtures/seed.sql`；右源＝實庫 `pg_dump --data-only` 經同一
  normalize：**COPY 段內整列排序**（消物理列序假紅）、setval 行保留原位、★剝除 pg_dump
  框架噪音兩類——①`\restrict`／`\unrestrict` token 行（pg_dump 18.4 每次 dump 隨機）
  ②`seaql_migrations` COPY 段（框架帳表、applied_at 逐次重放異；gate1 照相同義排除
  前例）——2026-08-05 兩座 pristine 獨立重放位元 diff 實證：非決定性恰此兩處、266 列
  與 11 支 setval 行全等。normalize 後
  **未排序逐列 diff**（含 id 欄）；★**禁全檔排序後雜湊比對**（會同時掩蓋 sequence 落值
  漂移與真差異）。seed 演進（seed_add／seed_update／seed_delete 登記）同樣合成後才比對。
- **rename 血緣對照**：內建 data-model §3 rename map，僅用於「vs rev4 快照」對賬場景——
  該場景＝fixtures 產製之一次性三驗（T012、紀錄留 provenance.md），非三閘常態比對面；
  對照面＝data-model §4 授權偏離集全項 normalize（rename／region／trace_id／real_ip NN／
  預設 now()）、除此之外全等；rev5 自家比對一律新欄名、不走映射。

## 3. audit archetype 閘（15 表歸屬逐表驗）

- **左源**：`docs/ops/reference-src/archetype-map.json`（data-model §1 轉錄）。
- **左源形契約**：`{lineage, usage, tables:[{table, label, active_unique, note}]}`——
  tables Day-1 恰 15 筆（由 `test` 子命令釘死；後續刀隨 add_table 登記成長、常態守門
  ＝實庫表集 vs map 表集全等）；table／label 必填非空（label ∈ 四變體字串）；active_unique＝活性唯一
  **索引名**清單或 null；note＝人讀註記。load 斷言 fail-loud（缺鍵／表重複／label 值域外
  ＝rc 2）。
- **驗則**（對實庫照相逐表執行）：
  - 變體 A：六審計欄在場且型別／可空性合 §I.6（`*_at` timestamptz、created_at NN def
    now；`*_by` bigint 可空）；活性唯一驗則＝map `active_unique` 列出的**索引名**逐支
    在場且定義含 `WHERE (deleted_at IS NULL)`（sys_user 兩支：user_name＋lower(user_email)；
    sys_ip_rule 複合 (wbip_cidr, wbip_type)；PK 總體唯一者豁免、active_unique=null）。
  - 變體 B：禁欄＝**前綴判準**（ADR 0016）——欄名以 `updated_`／`deleted_` 起首即紅
    （防 updated_time／deleted_flag 之類變名欄繞過 append-only 保證）；合法 payload 欄
    走工具內具名豁免清單 `AUDIT_B_EXEMPT`（`{(表, 欄): 理由}`、Day-1 空集、每筆必附
    理由）正規出口；created_at NN。
  - 變體 C：子型規則**硬編碼於工具**（沿 rev4 已驗證先例；map 之 note＝人讀註記、非機器
    判準）——sys_user_role＝零審計欄 join；sys_token＝created_at NN＋created_by NN＋
    status；sys_pwd_custody＝複合 PK (user_id, created_by) 極簡三欄；
    sys_user_email_verify＝user_id PK 衛星五欄。
  - 變體 D：治理欄在場（casbin_rule：protected NN def false＋created_at NN＋created_by
    可空；archive：archived_at NN def now＋archive_reason NN）。
  - `created_by` 可空性顯式驗（不靜默）：期望值＝data-model「`*_by` 欄性質判準」逐表
    釋義——NN 恰四表（sys_access_log／sys_token／sys_pwd_custody／sys_user_email_verify）、
    其餘一律可空。
- **表清單守門**：實庫表集 ≠ map 表集＝紅（新表未登記歸屬即攔——先補 data-model §1、
  再登記 map）。

## 4. negative test 義務（SC-002；比對器先自證）

實作 MUST 附注入式負向測試，四類假漂移各至少 1 例、全數必紅：
①結構（加欄／改型別）②欄序（同表兩欄互換）③seed 值（改一格）④sequence 落值
（setval±1）。連同 self-test 進 `test` 子命令；pre-commit 於工具本體 staged 時自動跑。

## 5. Day-1 營運紀律（隨刀常設）

每支帶 migration 的刀收刀前 MUST：跑 refresh（快照前進）＋ schema-evolution.json 登記
（該刀全部結構／seed 變更）＋三閘綠。此條入 `docs/ops/RUNBOOK.md` migration 操作節
（rev4 紅燈裸奔兩刀教訓、K1-39）。

## 6. doccheck 文件面對賬（B-010；三閘之外的離線子命令）

- **對賬面**：data-model.md **§2 逐欄五元組**（ordinal／column／type／NN／default）vs
  `fixtures/columns.json`（casbin_rule 依 §7／欄序豁免名冊不在 §2、自 fixtures 面排除）；
  **§6 索引與約束定義** vs `fixtures/{indexes,constraints}.json`（全表）。文件單邊被改
  ＝紅、逐項指名——補「§2 型別/NULL/default 三欄與 §6 定義從未進機器比對面」缺口。
- **解析紀律**（兩個已實證陷阱、負向測試釘死）：§2 default 欄「——」＝無 default
  （None、非字面）；§6 條目行可帶尾註（條目正則不錨行尾）。宣告欄數／支數逐表自檢＋
  §6 總計行自檢，防靜默漏列。
- **運行面**：離線零 docker、只讀 repo 檔；退出碼同 §0（0 全等／1 差異／2 環境或結構
  異常）；★**不入 pre-commit 常跑鏈**（護效能預算 B-007）——手動／review 輪跑。精確界線：
  schema-gate.py 本體 staged 時，pre-commit 條件觸發的工具自測含「真 repo doccheck 綠」
  一案、仍會帶到（成本併入自測、實測毫秒級）；反面＝單改 data-model.md 不觸發本檢查，
  文件單邊漂移於下一次手動／review 輪才被抓（設計取捨、非缺陷）。
