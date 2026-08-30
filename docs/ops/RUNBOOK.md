# RUNBOOK — dev stack 操作手冊

本檔＝「怎麼操作」唯一的家。分工（防鏡像）：系統長怎樣→活書 §7；十三機密明細表→
`deploy/secrets/README.md`；埠／帳號全表→`docs/generated/reference/`；坑索引→`docs/ops/LESSONS.md`（條目全文＝`docs/ops/LESSONS/` 一坑一檔）。
本檔命令一律完整可複製——整行逐字貼進 shell 即可跑、一律於 repo 根執行。
創世期章節現況：§1／§12／§14／§15 為最小必備四章；其餘各章隨對應刀補實文、章內不放未經實跑的命令。

## 1. 快速啟動（新機五步）

1. `bash tools/bootstrap.sh` —— 源倉＋worktree＋hooks＋secrets 體檢（幂等、可重跑）
2. `python3 deploy/generate-secrets.py` —— 十三機密缺則補
3. `python3 deploy/preflight-secrets.py` —— up 前預檢（全齊印 OK）
4. `bash deploy/generate-dev-cert.sh` —— dev TLS 憑證。★非可選：front-nginx 恆 bind-mount
   兩支 pem、缺檔直接 up＝Docker 代建空目錄佔位→nginx PEM emerg 死循環（rev4:L-141；修復＝
   `rmdir` 假目錄→生成→`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate front-nginx`）。
   自簽路線再把 `deploy/dev-certs/ca.pem` trust 進 OS（Windows shell：
   `certutil -addstore -user Root deploy/dev-certs/ca.pem`；macOS 信任程序隨 dev stack 刀實測後補記）
5. `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait` —— 起六業務件（migrate 是啟動閘：migration 失敗→rust-api 不啟→非零退出）

★缺 secret 直接 up：compose 對缺 bind source 不報錯、自動建**空目錄**佔位——容器拿到空
secret、錯誤訊息誤導（DB 連線失敗／boot panic 不指真因）。所以第 3 步不可跳。

## 2. 日常起停

（本章隨 dev stack 就位後補實文；創世期無內容。）

## 3. 觀測層 profiles（obs／metrics／jobs）

（本章隨觀測層刀補實文；創世期無內容。）

## 4. ★人工必填清單（腳本不代辦）

（本章隨 dev stack 就位後補實文；創世期無內容。）

## 5. named volume（卷名帶 project 前綴 `rev5-admin_`）

（本章隨 dev stack 就位後補實文；創世期無內容。）

## 6. 備份與還原

★**命令驗證狀態**：§6.1／§6.2 全序列**已於 2026-08-07 真還原演練實跑**（紀錄＝§6.3）；
§6.4 原地還原命令形**未實跑**——破壞性操作、須 operator 明確同意後另行執行。

### 6.1 備份（pg_dump 走容器、host 除 docker 外零依賴）

```bash
python3 deploy/backup-db.py dump
```

自 dev stack 的 postgres 容器 `pg_dump` 整庫（plain SQL）、落
`$HOME/backups-fork260509-rev5/`（檔名帶 UTC 時戳、絕不覆寫既有檔）。**落點紀律**＝
$HOME 下以 repo 目錄名為根（`SECRETS_DIR` 同款命名、rev4:0084 防跨代撞名）、絕不落 repo 內。
★本工具**零機密處理**：不碰 age 私鑰、不碰 `$SECRETS_DIR` 明文——機密檔與資料卷的**配對
備份＝第二段**（排程化亦同，BACKLOG B-023）、明確不在本章。★界線另一條：plain `pg_dump`
只含單一 database、**不含 cluster 級 globals（role 定義與其密碼）**——現況零 role GRANT
故全新 cluster 可直灌；日後 reaper role 建立後 dump 會帶 `GRANT … TO reaper`，還原目標
須先建該 role（否則 `ON_ERROR_STOP` 停在首個 GRANT）。

### 6.2 還原演練（scratch 容器、★非破壞——既有容器與卷零觸碰）

```bash
docker run -d --name rev5-admin-drill-pg -v rev5-admin-drill-pg-data:/var/lib/postgresql \
  -e POSTGRES_USER=soybean -e POSTGRES_PASSWORD=drill-scratch \
  -e POSTGRES_DB=soybean_admin_rust postgres:18.4-alpine
until docker exec rev5-admin-drill-pg pg_isready -U soybean -d soybean_admin_rust >/dev/null 2>&1; do sleep 1; done
python3 deploy/backup-db.py restore "$HOME/backups-fork260509-rev5/<dump 檔名>" --container rev5-admin-drill-pg
python3 deploy/backup-db.py dump --container rev5-admin-drill-pg
```

驗證＝normalize 後逐位元比對（剝 pg_dump 隨機 token 行、與 schema-gate normalize 同則）＋
唯讀抽驗（對 scratch 庫 `psql -Atc` 數列數對照現庫）：

```bash
grep -v -e '^\\restrict ' -e '^\\unrestrict ' "$HOME/backups-fork260509-rev5/<原 dump>" > tmp/a.norm
grep -v -e '^\\restrict ' -e '^\\unrestrict ' "$HOME/backups-fork260509-rev5/<re-dump>" > tmp/b.norm
cmp tmp/a.norm tmp/b.norm && echo 逐位元相等
```

收尾清理**只准刪演練自建、名稱帶 drill 者**（既有 stack 的容器與卷絕不動）：

```bash
docker rm -f rev5-admin-drill-pg && docker volume rm rev5-admin-drill-pg-data
rm tmp/a.norm tmp/b.norm
```

### 6.3 演練紀錄

- **2026-08-07**（B-023 第一段收單演練）：現庫 dump（60791 bytes）→ 全新 scratch 容器＋卷
  （`rev5-admin-drill-pg`／`rev5-admin-drill-pg-data`）restore rc=0 → re-dump normalize 後
  `cmp` **逐位元相等**（sha256 同值）＋唯讀抽驗（sys_user 3／sys_menu 78／sys_role 3／
  public 表 16、兩庫同值）→ scratch 清理；docker 容器與卷名冊演練前後 diff 零增減。

### 6.4 原地還原（★破壞性——覆寫 dev stack 既有庫；未實跑、須 operator 明確同意後執行）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres dropdb -U soybean --force soybean_admin_rust
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres createdb -U soybean soybean_admin_rust
python3 deploy/backup-db.py restore "$HOME/backups-fork260509-rev5/<dump 檔名>" --container rev5-admin-postgres-1
```

`dropdb` 起即無回頭路——執行前先照 §6.1 再留一份新 dump；還原後跑
`python3 tools/schema-gate.py check` 三閘綠＝驗收。

## 7. 機密輪替表（生成明細→`deploy/secrets/README.md`；密文面連帶＝§15）

（本章隨機密管線就位後補實文；創世期無內容。）

## 8. reaper 操作

（本章隨對應刀補實文；創世期無內容。）

## 9. 維運端點與 DB 直連

（本章隨對應刀補實文；創世期無內容。）

## 9a. 授權治理面速查（006；僅指針）

- 回收桶復原（getArchivedPolicies／restorePolicy 動線、restorable 五腿判準）→
  `specs/006-authz-governance/contracts/wire-policy-archive.md`＋ADR 0055；復原 UI＝manage/policy-archive 頁。
- 授權拒因三鍵查法：`biz.role.protectedRevoke`（撤 protected 整批拒）／`biz.role.protectedGrant`
  （封死：protected 端點授非 R_SUPER）／`biz.policy.notRestorable`（復原任一腿拒）→ 語意與掛點＝
  ADR 0054；封死謂詞＝`sys_casbin_policy.rs::protected_endpoint_set`；全量替換射程＝候選集（ADR 0056）。

## 9b. 前端驗證指令分工（★誤用即假紅／假綠；B-128）

在 `base-web/` 下跑。**四件各有其職，缺一不可互相替代**：

| 面 | 指令 | 判準 |
|---|---|---|
| 型別 | `pnpm typecheck` | rc=0（`vue-tsc --noEmit --skipLibCheck`） |
| `.vue` | `pnpm lint` | **0 errors**（既有 warning 見下方注意事項） |
| `.ts` | `pnpm exec oxlint <file>` | 0 errors／0 warnings |
| 標記與渲染 | 倉庫根跑 `python3 tools/fork-delta-lint.py`／`tools/view-render-guard.py` | 綠 |

★★**`eslint` 對 `src/**/*.ts` 零覆蓋——拿它判 `.ts` 是假紅**：`pnpm exec eslint --print-config src/service/request/index.ts`
回 `undefined`＝flat config 無匹配設定；實跑則以「File ignored because no matching configuration was supplied」
計一個 warning ⇒ `--max-warnings=0` 下 **rc=1**。該現象對**未改動**的既有檔同樣重現（＝既存現象、非某次改動所致）。
`.ts` 面的實際檢查由 `oxlint` 承接（`package.json` 之 `lint` 已是 `oxlint` 打頭）。

★★**`pnpm lint` 內含 `--fix`，會就地改寫「本來就不 lint-clean 的既有檔」**（B-144）：本刀 U6～U8 三度撞到
`src/views/manage/ip-rule/index.vue` 被重排一段 HTML 註解。危害在**執行單元的空間邊界靠「工作樹只出現允許清單內的檔」
判定**——這筆改寫會讓清單外的檔平白出現在 `git status`，很容易被誤當成自己的交付。
處置：跑完 `pnpm lint` 後檢查 `git status`，清單外的檔一律**存原文→寫回**還原（★不用 `git checkout`，L-060），
並在交付報告裡註明。根治面＝讓那些檔一次性回到 lint-clean（B-144 候選處置①）。

★**編排 script 的前端驗證段照此表寫**：把「`.ts` 走 oxlint、`.vue` 走 `pnpm lint`、MUST NOT 用 eslint 判 `.ts`」
與上述 `--fix` 還原紀律逐條烤進 agent prompt（本刀 U6／U7／U8 三支已照辦）。

## 10. migration 操作

★**Day-1 登記紀律（隨刀常設）**：每支帶 migration 的刀**收刀前必跑**下列三步（契約＝
`specs/001-schema-baseline/contracts/gates.md` §5；rev4 紅燈裸奔兩刀教訓 K1-39）：

1. `python3 tools/docs-sync.py refresh` —— 照相（schema／accounts 兩快照前進；需運行中 stack）
2. 登記 `docs/ops/reference-src/schema-evolution.json` —— 該刀**全部**結構／seed 變更逐筆入帳
   （kind 枚舉恰八值、每筆帶來源刀編號；刪除性演進〔drop_*〕不入登記檔——屬拍板級、
   走新 ADR 基線翻案；seed 面合成現況：add_table 與帶 default／NOT NULL 之 add_column
   落 rc 2 fail-loud 指引擴充；壞形登記由啟動斷言七條攔下——含 kind×detail 必備鍵表，
   契約＝`specs/001-schema-baseline/contracts/schema-evolution.md` §2、每跑必驗 rc 2）
3. `python3 tools/schema-gate.py check` —— 三閘綠（gate1 結構／gate2 欄序＋seed／audit
   archetype）；未登記漂移一律紅、「migration 已跑、登記缺席」＝gate1 紅之常態語意；
   一次性 pristine 場景加 `--container <容器名>`（預設＝compose dev stack）；判讀提示：
   同庫反覆 DROP→ADD COLUMN（含 down→up）後 gate1 會因 PG attnum 空洞報 ordinal 差
   ——補救＝pristine 重放、勿誤判真漂移

新業務表另備兩件：先補 `specs/001-schema-baseline/data-model.md` §1 archetype 歸屬、再登記
`docs/ops/reference-src/archetype-map.json`——否則 audit 表清單守門攔。

## 11. 觀測層維運

- 選單域 advisory 鎖觀測：pg_locks 之 classid/objid 拆讀 64-bit key——helper 與坑
  （bigint 直比恆假）＝rust-api `facade/sys_casbin_archive.rs` 觀測 helper 的 doc。
- casbin 判定面熱重載：metrics `casbin_reload_total{ok|retry|exhausted}`；exhausted＝
  keep-last-good 續舊面（服務不中斷）、查 log 結構化告警；落點測與手動 smoke 動線＝
  specs/005-role-menu-crud/quickstart.md §2。

## 12. 工具鏈速查（★python 工具一律直跑或 `python3` 前綴、bash 前綴＝假失敗 rev4:L-129/rev4:L-143）

★rc 判讀先辨層次：`rc=1` 常是工具**拒絕執行**（參數錯、零測試跑）而非受測物真失敗——
雙證＝rc＋輸出行為（跑了幾支、誰報的錯）；詳 L-021。

| 命令 | 作用 | 需運行中 stack |
|---|---|---|
| `python3 tools/docs-sync.py generate` | 重算 docs/generated/ 全部（跑完必 git add） | 否 |
| `python3 tools/docs-sync.py check` / `lint` | pre-commit 兩道（staged 過期／Lint03~Lint27） | 否 |
| `python3 tools/docs-sync.py refresh` | 自實庫撈 schema/accounts 快照 | **是** |
| `python3 tools/docs-sync.py errata <詞>` / `test` | 全 repo 同語意枚舉／自測 | 否 |
| `python3 tools/schema-gate.py check` | 三閘全跑（gate1 結構／gate2 欄序＋seed／audit archetype；fixtures⊕演進帳合成、入口自證 self-test；不進 pre-commit、手動跑） | **是** |
| `python3 tools/schema-gate.py test` | 自測 | 否 |
| `python3 tools/schema-gate.py doccheck` | data-model §2/§6 文件面 vs 凍結 fixtures 對賬（B-010；離線、不入 pre-commit 常跑鏈——手動／review 輪跑） | 否 |
| `python3 tools/wire-schema.py extract` / `check` / `test` | 容器內抽 typings→wire-schema.json 快照／快照 drift 比對（`--staged-gate`＝pre-commit 收窄形）／自測 | extract **是**、check 未起→警告放行 |
| `python3 tools/fork-delta-lint.py` | base-web 原行紀律（前置：fork 源倉在 example 分支） | 否 |
| `python3 tools/secret-value-guard.py check --full-tree` | 機密現值 × 全 tracked 檔一次性盤點：staged 增量對既存明文結構性失明（rev4:L-190）、本旗標補盤點面——導入既有 repo 與定期體檢用；命中只印「檔:行｜機密名」絕不印值、有命中 exit 1。★不進 pre-commit（全樹非增量；增量面＝pre-commit 自動跑裸 check） | 否 |
| `python3 tools/view-render-guard.py check` / `test` | 管理頁 `base-web/src/views/manage/**` 零原始 HTML 插值斷言（FR-038；禁用字面表逐行掃原文，條數以 `FORBIDDEN` 為準、成功訊息會印、**不解析註解與語法**——能藏在註解裡就能藏在字串常值裡再拼接）／自測。★pre-commit **條件觸發**：base-web pin bump 或本檔 staged 時自動跑（`base-web/src` 缺席＝具名跳過）；掃到零檔＝fail-loud rc=2 | 否 |
| `python3 tools/seed-view-gate.py check` / `test` | seed `sys_menu.component` 之 `view.*` 集 ⊆ `base-web/src/views/**` 依 elegant-router 規則導出集對賬（B-088／FR-049；另斷言導出集恰等 `router/elegant/imports.ts` 產物鍵集＝結構自證；具名豁免兩列住工具常數、到期／幽靈皆紅；self-test 每次 check 連帶跑）／自測。pre-commit **條件觸發**：base-web 或 rust-api pin bump 或本檔 staged 時自動跑（`base-web/src` 或 `rust-api/migration` 缺席＝具名跳過）；三面任一空集＝fail-loud rc=2 | 否 |
| `python3 tools/route-artifact-gate.py check` / `test` | 路由外掛產物四檔（`src/router/elegant/{imports,routes,transform}.ts`＋`src/typings/elegant-router.d.ts`）之**產出檔集對賬＋重算冪等＋零手改**三道——★憲法 §III.2 第五列「產物檔紀律」的**唯一**機器守（該四檔受 fork-delta 檢查全域豁免）。★**刻意不掛 pre-commit**：實跑外掛三趟、實測 15.2s，且依賴 dev stack 在跑，而 pre-commit MUST 在 stack 沒起時可用；落點＝**單元邊界／CI 手動跑** | check **是**、test 否 |
| `python3 tools/entity-drift-gate.py check` / `test` | entity（rust-api/entity/src）vs schema 快照漂移比對（欄序歸 gate2、index/constraint 歸 gate1、default 不驗）／自測 | 否 |
| `python3 tools/rust-fmt-gate.py check` / `test` | rust-api 容器內 `cargo fmt --all --check`（**唯讀**、設定＝`rust-api/rustfmt.toml`；B-112／ADR 0057）四態分流：docker 不可用或 compose 檔缺席＝具名跳過 rc 0／rust-api 容器未在跑＝具名跳過 rc 0／全綠 rc 0（印耗時）／未格式化 rc 1（印 `Diff in` 段數＋前 12 行摘要＋補救命令）／容器在跑但映像未含 rustfmt component＝**rc 2 fail-loud**（附重建映像命令、刻意不設豁免）。★檢查的是 rust-api **工作樹**、非 pin 指向的 commit（worktree 髒時多印一行警示、不影響 rc）。pre-commit **條件觸發**：rust-api pin bump 或本檔 staged 時自動跑（★跳過邏輯住工具內、hook 段零條件判斷）／自測（離線、subprocess 全樁） | check **條件**（容器在跑才實跑，否則具名跳過）、test 否 |
| `bash tools/bootstrap.sh` | 新機重建／舊機體檢 | 否 |
| `./deploy/sops.sh <sops 參數>` | sops 官方容器 wrapper（digest 釘版、自 repo 根跑；自動選鑰＝見 §15.2 步驟 1 註記，`RV5_AGE_KEY_FILE` 可覆寫；營運程序＝§15） | 否（需 docker） |
| `python3 deploy/decrypt-secrets.py` | 加密檔 → `$SECRETS_DIR` 寫出明文機密檔；passphrase **只輸入一次**（腳本對每個 recipient 提示自動代餵；`RV5_DECRYPT_MANUAL=1`＝逐次手打退路） | 否（需 docker＋互動 tty） |
| `bash deploy/generate-age-key.sh [檔名]` | 產 age 金鑰（覆蓋閘＋先寫 `.new` 再 `mv`＋產物自檢；age 走容器＝`deploy/Dockerfile.age`，每次產鑰 `docker build --pull --no-cache` 取真最新）。省略檔名＝預設 `keys.txt`；同機第二把給非預設長檔名（跨代並存機的正解＝§15.2 步驟 1 註記） | 否（需 docker＋真 tty；build 需網路，離線退回本機既有映像＋警示） |

退出碼注意：view-render-guard＝命中 1、射程異常（掃到零檔）2、用法錯 64；seed-view-gate＝判定紅（缺 view／豁免到期／幽靈豁免／導出集≠imports 鍵集）1、射程異常（seed 檔／views／imports.ts 缺席或空集）2、用法錯 64；route-artifact-gate＝判定紅 1、環境前提不成立（stack 未起／基線缺席）2、用法錯 64；
rust-fmt-gate＝未格式化 1、環境不可用（容器在跑但 cargo-fmt 缺席）2、用法錯 64（docker 不可用／
容器未在跑＝**具名跳過 0**，訊息與「全綠 0」不同字樣）；
schema-gate＝差異 1、環境不可用 2、用法錯 64；wire-schema＝抽取失敗／check
不一致 2、用法錯 64（check 於 stack 未起＝警告＋0 放行）；entity-drift-gate＝漂移 1、
異常 2、用法錯 64；docs-sync refresh
的 stack 不在走 exit 1——判讀看是哪支工具的哪個碼、勿一概當失敗。

- **子命令真表**：`docs/generated/reference/tools-cli.md`（機器生成、
  `python3 tools/docs-sync.py generate` 重算、嚴禁手改）——納冊工具子命令的查詢入口；
  lint 命令形判定基準＝工具源碼分派表、真表為同一掃源的生成物（手改真表不影響判定）。
- **pre-commit 條件觸發**（工具自測、平時零額外開銷）：staged 含某 python 工具本體才跑
  該支 test 子命令；fork-delta-lint 兩觸發條件（base-web pin bump／工具本體 staged）取聯集
  只跑一次；base-web pin bump 時另跑 `python3 tools/wire-schema.py check --staged-gate`
  （staged 區間零 typings 變動即跳過）；base-web pin bump 或 `tools/view-render-guard.py`
  自身 staged 時另跑 `python3 tools/view-render-guard.py check`（`base-web/src` 未就位時
  具名跳過，同 fork-delta／entity-drift 的 Day-1 模式；★該檔在 TOOLS_PY 名冊內但**不入**
  `for t in` 自測迴圈＝具名豁免 `HOOK_TEST_LOOP_EXEMPT`——其 self-test 隨本 check 連帶跑、
  入迴圈即重複跑；bootstrap 體檢不受此豁免、照跑其 test）；base-web／rust-api 任一 pin bump 或
  `tools/seed-view-gate.py` 自身 staged 時另跑 `python3 tools/seed-view-gate.py check`（`base-web/src`
  或 `rust-api/migration` 未就位時具名跳過；同屬 `HOOK_TEST_LOOP_EXEMPT` 第二位成員、理由同上）；rust-api pin bump 或 schema 快照
  （docs/ops/reference-src/schema-snapshot.json）staged 時另跑
  `python3 tools/entity-drift-gate.py check`；rust-api pin bump 或 `tools/rust-fmt-gate.py`
  自身 staged 時另跑 `python3 tools/rust-fmt-gate.py check`（★該段**無** Day-1 條件判斷：
  跳過邏輯住工具內＝ADR 0057 決定 3，docker 不可用／容器未在跑皆由工具具名跳過 rc 0 承擔；
  該檔**不在** `HOOK_TEST_LOOP_EXEMPT`、照入 `for t in` 自測迴圈）；`bash tools/bootstrap.sh` 體檢則無條件
  全跑工具名冊全部 test。全鏈計時兩級門檻與效能預算＝§12.1（數字只住那一處）。
- **lint 條款**：全 26 條（範圍 Lint03~Lint27；23 號已拆除、編號不重用）。severity 三分：
  ERROR＝exit 1 擋 commit、WARN＝放行列示、跳過＝條款不適用而未執行、落跳過明細
  （**跳過≠通過**）。摘要末行形＝`lint：X 錯誤／Y 警告／Z 條款跳過／共 N 條款`。
  逐條機制→工具源碼與 `python3 tools/docs-sync.py test` 自測敘述；創世期具名豁免
  （DAY1_EXEMPTIONS）逐筆帶解除謂詞、到期即紅。
- **機密工具鏈釘版**（＝ADR 0011 ② 類「機密管線常駐件」全員）：Betterleaks **1.7.3**（原生
  二進位、bootstrap 存在性斷言同值）／sops 容器 **v3.13.3-alpine**（index digest＝
  `sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`、寫死於容器
  wrapper 常數）。★age **不在本表**：它是 ADR 0011 ③ 類一次性輔助工具（低頻單發、產物格式
  穩定），沿 **latest**、版本不落任何字面——每次產鑰以 `docker build --pull --no-cache`
  重建 `deploy/Dockerfile.age` 取真最新（防浮動 tag 被 docker 層快取凍成「假 latest」），
  離線／限流時退回本機既有映像並印警示、不靜默；完整性面走 go module sumdb 校驗。

### 12.1 效能預算（B-007：觀測基準與預算分攤、非機器閘）

★本節僅涵蓋 **pre-commit 全鏈**的 python 工具預算；容器內 cargo build 的時間基線另見 §12.2。

- **兩級門檻語意**（★**2026-08-17 改為雙錨**，ADR 0044、user 親決）：pre-commit 全鏈牆鐘
  超 **45s**＝警戒（列示放行、劣化趨勢訊號）、超 **90s**＝硬擋（狀態型：`--no-verify` 只延後、
  下次 commit 仍提醒）。★**兩條線各自對準不同的東西**：警戒錨在「最壞**合法**情形」
  （收刀簿記型實測 41.2s 進位）⇒ 它一亮就代表**出現了比已量測過的更慢的形**；硬擋錨在
  「病態」（掛住的工具／無窮迴圈／環境壞掉），取最壞合法值的約 **2.2 倍**（90/41.2）。
  ★**舊制 WARN=20s 已成假警報**：004 期間**每一顆** pin bump commit 都越線而放行＝警戒線
  恆亮，只訓練人忽略它（同 `obs.rs` 對「假警報養成無人看告警」的立場）。
  ★**配套引信（缺此則本次調整退化成單純放寬）**：「收刀簿記型 commit 的實測值」列為
  **每刀收尾的例行量測**、記入本節資料點序列；**連續兩刀 ≥60s**（新警戒與新硬擋的中點）
  即強制觸發①優化慢路徑 ②再立 ADR 調門檻 ③縮減 pre-commit 名冊之一，**不得**以
  「還沒破硬擋」續推。★數字權威＝
  `.githooks/pre-commit` 常數 `PRECOMMIT_WARN_SEC`／`PRECOMMIT_FAIL_SEC`（本節僅引用；
  調整走 ADR、不得就地改數字）。機器閘只有這一道**全鏈 90s**；本節其餘數字全屬觀測基準
  與預算分攤、無機器強制。
- **量測法**（K3-162 紅線、rev4 實證；出處＝docs/brainstorms/000-doc-architecture.md）：
  `time.perf_counter` 直接包被測**整命令**（subprocess）、每命令連跑 ≥3 次取**中位數**；
  合計＝逐支中位數加總。★**禁整鏈前後差量歸因單閘**——WSL2 全鏈牆鐘變異可達 ±1.5s、
  rev4 曾量出負值；整鏈計時只用於「有無數量級劣化」粗判。可複製命令形（輸出＝runs 三值
  ＋median；argv 換成被測整命令即可逐支複測）：

```bash
python3 - <<'EOF'
import statistics, subprocess, time
argv = ["python3", "tools/docs-sync.py", "lint"]   # ←換成被測整命令
ts = []
for _ in range(3):
    t0 = time.perf_counter()
    r = subprocess.run(argv, capture_output=True)   # 不 check：紅燈現場也要量得到值
    ts.append(time.perf_counter() - t0)
print(f"runs={[f'{t:.3f}' for t in ts]} median={statistics.median(ts):.3f}s rc={r.returncode}")
EOF
```

- **本批終態實測**（★**2026-08-18 重量測**（治理批 B-080 納冊後 pre-commit 迴圈名冊 12 支；
  **2026-08-25 起 13 支**——見情境 B 表 † 註）、WSL2 drvfs/9p、每命令 3 次取中位數；量測面＝
  python 工具——betterleaks 樣式掃描為原生二進位、不在本表量測面；**條件觸發段**另列於
  兩表之後）。**單跑上限推導＝該列中位數 ×3
  進位整秒、下限 1s**：×3 沿 pre-commit 既有餘裕先例（45s 對 rev4 WSL2 健康值 15.7s
  ≈3 倍）；下限 1s 吸收 drvfs 抖動的次秒級絕對尖峰；一律以 WSL2（慢端）實測定值——
  APFS 同工具快一個量級（pre-commit 註解既載事實），故上限對兩平台皆有餘裕。

  情境 A＝基礎鏈（無 gitlink、無 tools staged）：

  | 段 | 中位數 | 單跑上限 |
  |---|---|---|
  | `python3 tools/secret-value-guard.py check` | 0.127s | 1s |
  | `python3 tools/docs-sync.py check` | 1.317s | 4s |
  | `python3 tools/docs-sync.py lint` | 12.251s | 37s |
  | **基礎鏈合計** | **13.695s** | **42s**（＝合計中位數 ×3；逐列上限加總同為 42s、以本值為權威） |

  情境 B＝理論最壞 staged（pre-commit 名冊 13 支工具本體全 staged、條件自測全中）＝
  基礎鏈＋13 支 test（★名冊＝test 名冊（TOOLS_PY 16 支中帶 test 介面的 15 支；
  fork-delta-lint 無 test 介面、天然不入迴圈而走條件觸發段）減 `HOOK_TEST_LOOP_EXEMPT`
  具名豁免 2 支（view-render-guard／seed-view-gate——其 self-test 隨 check 連帶跑））：

  | 支 | 自測案數 | 中位數 | 單跑上限 |
  |---|---|---|---|
  | `python3 tools/docs-sync.py test` | 524 | 15.415s | 47s |
  | `python3 tools/schema-gate.py test` | 99 | 0.464s | 2s |
  | `python3 tools/wire-schema.py test` | 27 | 0.188s | 1s |
  | `python3 tools/secret-value-guard.py test` | 56 | 0.377s | 2s |
  | `python3 tools/entity-drift-gate.py test` | 45 | 0.175s | 1s |
  | `python3 tools/route-artifact-gate.py test` | —* | 0.070s | 1s |
  | `python3 deploy/preflight-secrets.py test` | 30 | 0.130s | 1s |
  | `python3 deploy/decrypt-secrets.py test` | 71 | 2.366s | 8s |
  | `python3 deploy/generate-secrets.py test` | 35 | 1.710s | 6s |
  | `python3 deploy/setup-reaper-role.py test` | 32 | 0.585s | 2s |
  | `python3 deploy/backup-db.py test` | 17 | 1.649s | 5s |
  | `python3 tools/wf-watchdog.py test` | 30 | 0.158s | 1s |
  | `python3 tools/rust-fmt-gate.py test` † | 11 | 0.125s | 1s |
  | **13 支 test 合計** | **977＋具名段** | **23.412s** | — |

  （*route-artifact-gate 自測為具名段形、非 unittest 計數，案數不入合計。）
  （†rust-fmt-gate＝**2026-08-25** 維護批 A（B-112／ADR 0057）新入名冊、該列為當日單獨量測，
  其餘各列沿 08-18 值。★同日 `docs-sync test` 案數已 524→**527**（本批 U1~U5 新案）但中位數
  未重測，故該列與合計之案數仍記 08-18 值——讀本表時注意其時點混成。）

  **情境 B 合計＝37.107s**（13.695＋23.412）。★門檻對照以 **2026-08-17 新制**（ADR 0044）
  為準：37.107s **未越警戒 45s**、遠未破硬擋 90s——合計面守門仍＝全鏈門檻、不另定上限。

  **條件觸發段**（gitlink／特定檔 staged 才跑，**不入上兩表**；★**前四列**沿 2026-08-16
  量測值（同法）、其後各批未重測；seed-view-gate 一列為 006-authz-governance 刀入冊當日量測、rust-fmt-gate
  一列為 **2026-08-25** 入冊當日量測（維護批 A／B-112）——讀值注意時點混成）：

  | 段 | 觸發條件 | 中位數 | 單跑上限 |
  |---|---|---|---|
  | `python3 tools/fork-delta-lint.py` | base-web gitlink／該工具／憲法 staged | 6.163s | 19s |
  | `python3 tools/wire-schema.py check --staged-gate` | base-web gitlink staged | 8.431s | 26s |
  | `python3 tools/entity-drift-gate.py check` | rust-api gitlink staged | 0.179s | 1s |
  | `python3 tools/view-render-guard.py check` | base-web gitlink／該工具 staged | 0.224s | 1s |
  | `python3 tools/seed-view-gate.py check` | base-web／rust-api gitlink／該工具 staged | 0.49s | 2s |
  | `python3 tools/rust-fmt-gate.py check` | rust-api gitlink／該工具 staged | 2.783s | 9s |

  ★`tools/route-artifact-gate.py check` **不在 pre-commit**（其 check 需 dev stack 在跑），
  故不列本表；其本身耗時亦屬量級可觀（同日單跑約 15s，且**連續背靠背跑第三趟時實得
  rc=2「外掛產出未在 90s 內靜止」**——沙盒內跑 vite 外掛、drvfs 爭用下會逾時，單跑重驗即綠）。
- **★2026-08-16 收刀簿記型 commit 的合成推估＝41.2s**（★該值即 **2026-08-17 新警戒線 45s 的錨**——ADR 0044 取它進位；舊制下它距 45s 硬擋僅 3.8s，正是本次調門檻的觸發事實）（同日
  中位數逐段相加：基礎鏈 9.907＋`docs-sync test` 16.272＋`fork-delta-lint` 6.163＋
  `wire-schema check` 8.431＋`entity-drift-gate check` 0.179＋`view-render-guard check` 0.224）。
  對照同日 004 U-I 收刀 commit 的 **hook 自報 38s**（實測值、單次牆鐘），兩者同量級。
  ⇒ 恆跑段（基礎鏈）**當時**約 9.9s（2026-08-18 已 13.695s、見上表），其餘全部來自
  條件觸發段與 `docs-sync test` 的疊加。
  ★**當批（～08-16）**成長面在 `docs-sync test`（隨案數：469→**496**）與 `lint`／
  `fork-delta-lint`（隨 repo／base-web 規模），非任何單一新工具；★2026-08-18 批歸因**相反**
  ——主力＝`docs-sync lint` 單項、`docs-sync test` 中位反降（16.272→15.415），詳上一批對照段。
  ★**該處置已於 2026-08-17 執行完畢**：走 ADR 0044（user 親決），兩門檻改為
  WARN=45／FAIL=90（推導見「兩級門檻語意」）。連帶配套＝**本值自此列為每刀收尾的例行量測**，
  資料點續記本節；**連續兩刀 ≥60s** 即強制觸發「優化慢路徑／再立 ADR/縮減名冊」三者之一。

- **★2026-08-25 例行量測（刀 B 前置維護批收尾；同法、WSL2 drvfs、dev stack 六容器在跑）**
  ——★前一筆（維護批 A）為**合成推估 47.4s、未實測**，本次依本節量測法重量、勿再沿用推估值。
  三個主導項各連跑 **5 次**（變異緊、非負載抖動）：

  | 段 | 2026-08-25 中位數 | 對照（時點） | 變化 |
  |---|---|---|---|
  | `docs-sync lint` | **17.337s** | 12.251s（08-18） | +41% |
  | `docs-sync test` | **19.824s**（案數 528） | 15.415s（08-18、524 案） | +29% |
  | `fork-delta-lint` | **10.152s** | 6.163s（08-16） | +65% |
  | `docs-sync check` | 2.063s | 1.317s（08-18） | +57% |
  | `rust-fmt-gate check` | 2.836s | 2.783s（08-25 入冊當日） | 持平 |
  | `secret-value-guard check`／`view-render-guard check`／`seed-view-gate check`／`entity-drift-gate check` | 0.188／0.210／0.595／0.173s | 同量級 | 持平 |
  | 其餘 12 支 test（docs-sync 以外） | 合計 9.688s | — | 持平 |

  **合成推估（沿 2026-08-16 之同一公式）＝59.8s**：基礎鏈 19.588（0.188＋2.063＋17.337）
  ＋`docs-sync test` 19.824＋`fork-delta-lint` 10.152＋`wire-schema check` 8.431（★**沿 08-16
  值未重測**——本次工作樹乾淨、該命令走跳過分支只得 0.186s，非真路徑值）＋
  `entity-drift-gate check` 0.173＋`view-render-guard check` 0.210＋`seed-view-gate check` 0.595
  ＋`rust-fmt-gate check` 2.836。⇒ 47.4→59.8s，**貼著 ADR 0044 引信線（60s）但未達**。
  ★**歸因**：`docs-sync.py` 單一工具佔 37.2s／59.8s＝**62%**（lint＋test）；三個主導項的成長
  合計約 +13.5s，其餘全部持平 ⇒ 成長面是 lint 條款數×repo 規模與自測案數，非任何新工具。
  ★**同批的實測反證（重要，勿只讀合成值）**：本批四顆 commit（含三顆 pin bump 收單型）
  **無一顆觸發 hook 的 >45s 警告** ⇒ 真實牆鐘皆 <45s。原因＝自測迴圈只對**已 staged 的工具**
  跑 `test`，而 pin bump 型 commit 通常零工具 staged ⇒ `docs-sync test`（19.8s）根本不進鏈。
  合成公式把它算進去，故**合成值系統性高於真實值**——兩者都留、但引信判讀應以 hook 自報的
  實測牆鐘為準（本節「整鏈計時只用於數量級粗判」之同一取態）。
  ★**同日補：兩顆 commit 的 hook 自報牆鐘實測**（`time.perf_counter` 直接包 `git commit`
  整命令、單次；★這才是 ADR 0044 引信所指的「收刀簿記型 commit 的實測值」）：
  **收刀簿記型（events＋NOTES＋docs/generated，零 gitlink、零工具 staged）＝16.68s**；
  **文件型（RUNBOOK＋BACKLOG＋generated）＝26.10s**。兩者皆遠低於警戒 45s，也遠低於同日
  合成值 59.8s ⇒ **合成公式對真實情形高估約 3.6 倍**（差額幾乎全來自 `docs-sync test` 19.8s
  與 `fork-delta-lint` 10.2s——前者只在該工具 staged 時進鏈、後者只在 base-web gitlink／憲法
  staged 時進鏈，收刀簿記型兩者皆不觸發）。★**引信判讀結論**：以實測為準則本刀 16.68s、
  距 60s 引信線甚遠；合成值僅作「若最壞情形全中」的上界參考，**不得**單獨用來判引信。
  ★**下一刀必做**：①`wire-schema check --staged-gate` 於 base-web gitlink 真 staged 時重測
  （現值已是 08-16 的、且它是合成值裡第二大項）②pin bump 型 commit（gitlink staged、條件段
  全中但無自測迴圈）亦補一次牆鐘實測——本批三顆皆未越警戒但未逐顆計時 ③若 `docs-sync lint`
  續增，處置面＝該工具的慢路徑（見 BACKLOG）。
- **★2026-08-18 治理批收尾合成推估＝44.107s**（資料點軌：41.2〔08-16〕→**44.107**；同法
  逐段相加＝基礎鏈 13.695＋`docs-sync test` 15.415＋條件觸發四列**沿用 2026-08-16 中位**
  6.163＋8.431＋0.179＋0.224——★半新半舊推估：本批未動 base-web／schema 面、四列條件段無
  重測理由，讀值時注意其時點混成）。距警戒 45s 餘 **0.893s**——下一刀動 base-web 面時宜
  連四列條件段一併重測後再讀本值；引信（連續兩刀 ≥60s）本刀未觸發。
- **★2026-08-25 維護批 A（B-112）名冊變動後之增量重估＝47.380s**（資料點軌：41.2〔08-16〕→
  44.107〔08-18〕→**47.380**〔08-25〕；★本值為**重估、非收刀實測**——本刀非收刀）。算式＝
  08-18 之 44.107 ＋本批新入的 `rust-fmt-gate check` **2.783s** ＋該軌一直漏記的
  `seed-view-gate check` **0.49s**（該列於 006-authz-governance 刀入冊、晚於 08-18 資料點，從未併入本序列）。
  `rust-fmt-gate test` 0.125s 屬情境 B 面、不入本推估（收刀簿記型 commit 不 stage 工具本體）。
  ⇒ **已越警戒 45s**（越線＝列示放行、不擋；距硬擋 90s 仍遠）——即 ADR 0044 所謂「出現了比
  已量測過的更慢的形」，成因明確＝新增一道容器內守門，非慢路徑劣化。引信（連續兩刀 ≥60s）
  **未觸發**：47.380 < 60，且本刀非收刀。★半新半舊推估（僅新列於 08-25 實測、其餘沿舊），
  **下一刀收尾必須依本節量測法實測全鏈**再讀。★`rust-fmt-gate check` 現值量於**存量尚未格式化**
  之時（687 段 diff、rc 1）；存量一次格式化 commit（§12.3）落地後段數歸零，但成本**不等比下降**
  （rustfmt 仍須全樹解析）——屆時重測改值。
- **★2026-08-25 B-097 維護批：hook 自報 55s ＝ 首筆「真實越線」實測**（前此越線皆為合成推估）。
  該顆＝pin bump 型外層 commit（staged `base-web` gitlink ＋ ADR ＋ BACKLOG ＋ `docs/generated`）
  ⇒ `fork-delta-lint`（10.2s）與 `view-render-guard`／`seed-view-gate` 皆進鏈，而 `docs-sync test`
  （19.8s、僅工具本體 staged 時跑）未進鏈——此即與同日簿記型 **16.68s** 的主要差額來源。
  ⇒ **B-130 觸發器「hook 開始自報 >45s 警告時」自此達成**；ADR 0044 引信（連續兩刀 ≥60s）
  **仍未觸發**（55 < 60）。★本值取自 hook 自報行、非依本節逐支中位數法量測，兩者不可混用作成長率。
- **★2026-08-25 B-130 提速批：全鏈 43.46s → 13.09s（3.3×）**（ADR 0061；同一支 bench、同條件三跑取最佳，
  ★非本節逐支中位數法——該法需乾淨環境，本值供**前後對比**用、不可與上方序列混算成長率）。
  分項：`docs-sync lint` 25.34→**15.92**／`docs-sync check` 4.79→**3.44**／`fork-delta-lint` 17.04→**3.93**（4.3×）。
  真 hook 最重情境（staged 三支工具＝觸發 529 案自測）實跑 **24.1s rc=0**，瓶頸已是自測本身。
  ★**歸因紀律（本節新增、L-062）**：動手前先 cProfile 分「I/O 稅 vs 邏輯」——本批三個憑直覺列的
  處置面全數證偽（lint 的檔案系統原語佔 64%、邏輯僅 7%；fork-delta 的 select.poll 佔 99%）。
  ★**合成公式的第二處誤導已結清**：`wire-schema check --staged-gate` 真路徑僅 **0.43s**（走 `no-typings`
  短路），而合成值沿用 08-16 的 8.431s（未短路路徑）——B-130 所列「先決事實」自此不再是待辦。
- **★2026-08-30 007-user-password-admin 之 U10 收尾：兩個量測面各一筆**（★兩值**不可混算**——
  hook 自報牆鐘與逐支中位數是不同量測面，本節既有紀律）。
  - **牆鐘實測（真 commit、`time.perf_counter` 直接包 `git commit` 整命令、單次）＝13.89s rc=0**
    （U10 治理收尾 commit `b5b6912`；staged＝4 支新 ADR＋活書＋附屬文件＋BACKLOG／LESSONS／NOTES／
    tasks＋`docs/generated`，**零 gitlink、零工具本體** ⇒ `fork-delta-lint`／`view-render-guard`／
    `seed-view-gate`／`docs-sync test` 皆未進鏈）。對照同型的 2026-08-18 之**文件型 26.10s** ⇒
    **B-130 的提速在真實 commit 面兌現**（−47%）。距警戒 45s 餘 3.2 倍。
  - **逐支中位數（情境 A 基礎鏈、乾淨環境、每支 3 跑取中位）**：`secret-value-guard check` **0.138s**／
    `docs-sync check` **1.153s**／`docs-sync lint` **13.326s** ⇒ **基礎鏈合計 14.617s**。
    對照 2026-08-18 同法同情境的 13.695s ⇒ **+6.7%**（主項＝`lint` 12.251→13.326、+8.8%）。
    ★**這個 +8.8% 要正著讀**：其間 repo 掃描面增加了 005／006／007 **三刀**的全部產出
    （ADR 0053～0068、LESSONS 分檔 47→70 條、三份 spec 目錄、活書四節擴充），而基礎鏈只漲不到一成
    ——B-130 的 I/O 稅處置正是在吸收這段成長。★**勿與 B-130 那筆的 25.34→15.92 混算**：該筆是
    「同一支 bench、同條件三跑取最佳」，量測面與本序列不同（該筆自己也載明不可混算）。
  - ★**誠實界線**：本刀這兩筆**都不是收刀簿記型**（那顆＝events append＋NOTES＋generate，尚未發生）
    ⇒ **ADR 0044 引信所指的本刀資料點，須於收刀簿記那顆 commit 補記**；引信（連續兩刀 ≥60s）
    以現有值判**未觸發**。
  - **★同日第三筆：pin bump 型＝19.41s rc=0**（`33ee6b7`；staged `rust-api` gitlink＋憲法＋活書＋specs＋
    generated ⇒ `fork-delta-lint`〔憲法 staged 即觸發〕／`wire-schema --staged-gate`／`view-render-guard`／
    `seed-view-gate` 進鏈，`docs-sync test` 未進）。對照同日文件型 13.89s ⇒ 條件段淨增 **5.5s**（與 B-130 後
    `fork-delta-lint` 3.93s＋其餘次秒級之和吻合）；距警戒餘 2.3 倍。★結清「下一刀必做」②，惟本顆 staged 者為
    rust-api 而非 base-web gitlink、`fork-delta-lint` 係經憲法觸發。★**本節撞頂＝B-149**。
  - **★★同日第四筆：merge commit ＝4.55s rc=0**（`5e8b32f`；staged **兩個** gitlink）——**推翻本序列
    先前的期待**：舊記載說「收刀 merge 那顆是尚未量過的最重情境」，實測卻比 pin bump 型（19.41s）短 4 倍。
    根因＝**merge commit 不跑 `pre-commit`**（git 對 merge 走 `pre-merge-commit`，而本 repo `.githooks/`
    只裝 `pre-commit`／`pre-push`，實地確認）。⇒ 最重情境不在 merge 那顆，真實上界仍是情境 B。
    ★**副作用**：收刀 merge 不受任何 lint 把關，分支最後一顆的綠燈即收刀全部憑據（merge 前每顆都過閘，
    但別誤以為 merge 又驗了一次）。
  - ★**既有「下一刀必做」三項結算**：①`wire-schema check --staged-gate` 重測＝**已由 B-130 那筆結清**
    （真路徑 0.43s、走 `no-typings` 短路）②pin bump 型牆鐘＝**已補**（同日第三筆 19.41s）。★收刀 `merge --no-ff` 那顆宜再測——staged **兩個** gitlink、本序列未量過
    ③`docs-sync lint` 慢路徑處置＝B-130 已處置、本刀無新增條款。
- **史料批次**（同法量測，供成長率比較；★**2026-08-30 依 B-149 候選②壓縮**——逐項分析全文查 git）：
  2026-08-16＝基礎鏈 **9.907s**／11 支 test 24.593s（938 案）／情境 B 34.499s；
  2026-08-08＝基礎鏈 7.041／test 19.735（893 案）／情境 B 26.776。⇒ 08-16→08-18 基礎鏈 **+38%**、
  成長主力是 `docs-sync lint` 單項（8.388→12.251，B-090 分檔制掃描面＋Lint26/27 兩新條款）。
- **歷史對照**（皆全鏈牆鐘粗判值、與上表逐支中位數非同一量測面）：001 收刀＝無 gitlink
  無 tools staged **1.016s**／staged `tools/docs-sync.py`（428 案自測）**27s**（出處＝
  docs/brainstorms/b8b-acceptance-evidence.md）；本維護批中途量測點（單元② commit
  1779d17 後／單元③ commit 6a6378e 後，基礎鏈＋docs-sync／schema-gate／backup-db 三支
  test 合計粗判）＝**20.9s**／**17.6s**。可比面趨勢（本節立意所在）：基礎鏈同情境自
  001 收刀約 1s→2026-08-08 約 7s→2026-08-16 約 9.9s（主因＝lint 條款成長至全 24 條
  ＋ repo 規模）→**2026-08-18 約 13.7s**（主因＝lint 8.388→12.251：B-090 分檔制掃描面
  ＋Lint26/27）。★**比較對象自 2026-08-17 起改為新警戒 45s**（ADR 0044）：基礎鏈 13.695s
  距其**餘約 3.3 倍**；舊制記法「距 20s 警戒餘約 2 倍」已隨門檻改值作廢、勿再據以比較。
- **一致性核**（★兩次翻面、逐字留痕以免下一位覆核者重推一遍）：最大單支上限
  （`docs-sync test` **47s**）＋基礎鏈實測 **13.695s** ≈**60.7s**。
  - 2026-08-08 舊句：「36s＋7.041s ≈43s、仍在全鏈 45s 內 ⇒ 常見情境（單支工具 staged）下
    **觀測上限先於機器硬擋喊人**」。
  - 2026-08-16 一度**反轉**：59s 已越當時的全鏈 45s 硬擋 ⇒ 常見情境下改為「機器硬擋先喊」。
  - **2026-08-17 起還原成立**（ADR 0044 把硬擋提到 **90s**）：59s < 90s ⇒ 「觀測上限先於
    機器硬擋喊人」這條性質**恢復**，且餘裕比 2026-08-08 當時更寬（59/90 vs 43/45）。
  - 2026-08-18 本批複核（B-080 納冊後現值）**仍成立**：60.7s < 90s（餘裕 60.7/90）。
  ★真實值（`docs-sync test` 15.415s）距其單跑上限（47s）仍約 3 倍餘裕。逐支上限**加總**
  （基礎鏈 42s＋13 支 78s＝120s）仍超 90s——單跑上限是逐支劣化偵測基準、非「全數同時到頂
  仍過鏈閘」的保證；理論最壞情境的守門仍＝**全鏈硬擋那一道**。
- **超上限處置**（對齊 pre-commit 硬擋訊息措辭）：先量哪一段吃掉時間、勿憑猜——rev4 的
  rev4:B-113 三個病因候選經實測全數證偽；兩條出路＝①優化慢路徑②立 ADR 調門檻並記錄
  劣化理由。
- **維護紀律**：新工具入 pre-commit 名冊時，本表**須同步加列**（量測＋定上限）；名冊
  變動而本表未動＝表已過期。

### 12.2 容器內 cargo build 基線（B-028）

- **量測法**沿 §12.1 形制（`time.perf_counter` 直接包被測整命令），惟**冷編性質上一次性**
  ——重測須先清 `rev5-admin_rust_api_target` 卷、單次成本 >40s，故冷編記單次值並註明；
  單檔增量（`touch` 一支 entity 檔後重 build）連跑 3 次取中位數。
- **被測整命令**（兩輪同形；`--no-deps` 只是不重啟依賴服務，secrets 與網路照掛）：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml \
  run --rm --no-deps --entrypoint cargo rust-api build --workspace
```

- **兩輪實測**（2026-08-08、WSL2 drvfs/9p、容器內；`rust_api_cargo_cache` 卷兩輪皆保留
  ＝量的是編譯而非取件）：

  | 輪次 | workspace members | 冷編（單次） | 單檔增量（3 次中位數） |
  |---|---|---|---|
  | 第一輪（動工前） | migration／entity／sea-orm-adapter | 43.9s | 2.26s |
  | 第二輪（server 進場後） | ＋server | 46.6s | 3.35s |

- **判讀**：server crate 及其依賴（axum 0.8／tower／metrics 三件／casbin 消費面）進場後，
  冷編僅 +2.7s——因第一輪的 43.9s 已含 sea-orm／sqlx／tokio 這批重量級（migration crate
  即需要），新增件相對輕且多核並行編譯。增量 +1.09s＝多一個 crate 要重編的固定成本。
- ★**離群值註記**：第二輪增量三次為 13.17／3.35／3.35s——首次含冷編後的首輪 link，
  屬結構性離群，中位數取法自然排除之。★量測面用中位數而非平均，理由即此。
- **wall clock vs cargo 自報**：上表為 wall clock（含 compose run 建容器開銷約 1.7s）；
  同一次冷編 cargo 自報 `Finished dev profile … in 44.90s`。★兩者不可混用比較。
- 本節為觀測基準、**無機器閘**（與 §12.1 的全鏈硬擋不同——該值以
  `.githooks/pre-commit` 的 `PRECOMMIT_FAIL_SEC` 為權威）。dev profile 的 debuginfo
  裁剪與否屬後續評估，數據前提即本表。

### 12.3 rust 格式守門（B-112／ADR 0057）

- **設定三值**（`rust-api/rustfmt.toml`、皆 stable 選項）：`max_width = 100`／
  `use_small_heuristics = "Max"`／`style_edition = "2024"`。取值推導＝2026-08-24 存量 diff
  實測（本組 675 段最小；全預設 1,649 段、max_width=120＋Max 1,293 段——全表見 ADR 0057
  背景節）。★**調值走新 ADR**、不得就地改數字；rustfmt.toml 檔頭註解即該來源的指針。
- **工具鏈版本**：容器映像 `deploy/Dockerfile.rust-api` 以 `rustup component add rustfmt`
  附掛，版本隨 toolchain（`rust-api/rust-toolchain.toml` channel 1.96.1）＝rustfmt
  1.9.0-stable，**無獨立釘版面**（rustfmt 與 rustc 同版發行）。
- **舊映像＝rc 2 擋 commit**（刻意 fail-loud、不設豁免）。重建映像：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml build rust-api \
  && docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d rust-api
```

- **實作完工前的自律動作**（rust 碼改動的完工自驗必含＝ADR 0057 決定 5；閘紅時的補救亦同此命令）：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo fmt --all
```

- **存量一次格式化 commit**（rust-api、零語意變更、與功能改動隔離＝ADR 0057 決定 4）＝
  `d940d03`（本批 U5 收尾落地、53 檔 +3670/−1753）。該 commit 使 `git blame` 對被動行指向它；兩個繞法旗標各自可單用、亦可
  併用——`-w` 忽略純空白差異、`--ignore-rev` 整顆跳過指定 commit；本次格式化含單行呼叫
  的拆／併（非純空白），故單用 `-w` 不足以全繞，下列命令兩者同時帶：

```bash
git -C rust-api blame -w --ignore-rev d940d03 -- <檔案>
```

## 13. 故障排除速查（索引→LESSONS.md、全文→LESSONS/；此表只指路）

（本章隨教訓累積補實文；創世期 LESSONS 自空白起家、尚無條目可指。）

## 14. 埠與帳號

- 真相源：埠全表→`docs/generated/reference/ports.md`（機器生成）；帳號／角色→
  `docs/generated/reference/accounts.md`。本檔命令帶字面埠（22080/22443/22079/23000/23100/
  25432/26379/29090/29091）純為可複製執行；動埠的刀照 errata 紀律
  （`python3 tools/docs-sync.py errata <埠>`）機器枚舉全 repo 同步、含本檔。

## 15. SOPS 機密營運（密文入版控 × age 私鑰）

★**命令驗證狀態**（本檔開頭「章內不放未經實跑的命令」之誠實揭露）：§15.4 路徑 (a) 與 §15.7
步驟 3 的加密序列**已非破壞性實跑驗證**（產物落 `tmp/` 後即刪、真密文零改動）；§15.2 步驟 3 的
`updatekeys` **已於首次真實加人實跑**（2026-08-06 第二位成員入列；diff 性質經機器複核、與本節
所述預期逐項相符——10 支 `ENC[…]` 本體零改動、`mac` 不變、密文內 recipient 1→2 且與
`.sops.yaml` 逐把相符）；§15.7 步驟 1 的解密需 passphrase
（僅存持鑰者腦中）故**未實跑**，其正規化片段與 `deploy/decrypt-secrets.py` 的
`normalize_stream` **同形**（CR→行界＋剝 ANSI CSI、同序；語意等價、非逐字複本）——該函式
每次 decrypt 都在實跑。2026-08-08（B-041 第三把離線復原鑰）：`updatekeys` **第二次真實
實跑**（recipient 2→3、diff 性質同上逐項相符）；`deploy/decrypt-secrets.py` 以
`RV5_AGE_KEY_FILE` 指向復原鑰**端到端實跑**（3 recipient 自動代餵、10 支 WRITTEN）
＝復原鑰可解實證。

### 15.1 資產、工具與不可省紀律

資產三件：`deploy/secrets.dev.enc.yaml`（密文、**tracked**、承載 10 支＝9 leaf＋
`alert_webhook_url`）／`.sops.yaml`（recipient 公鑰清單、tracked）／
`~/.config/sops/age/keys.txt`（**私鑰＝passphrase 加殼**、目錄 700 檔 600、**永不進版控**；
跨代並存機改用 `keys-fork260509-rev5.txt`＝§15.2 步驟 1 註記）。另有第三把**離線復原鑰**
（B-041、ADR 0015 子題三）：私鑰檔＋passphrase **離線保管、不駐任何開發機**——封「雙持鑰人
同失 passphrase＝密文永久不可解」死路；災難動用＝`RV5_AGE_KEY_FILE` 給其檔案的 host 絕對
路徑後照常跑 `python3 deploy/decrypt-secrets.py`。
工具＝`./deploy/sops.sh`（官方容器 wrapper、digest 釘版、自動選鑰）、`python3 deploy/decrypt-secrets.py`
（密文→`$SECRETS_DIR/*.txt`）、`python3 deploy/generate-secrets.py`（產亂數）、
`python3 deploy/preflight-secrets.py`（上機前體檢）、`bash deploy/generate-age-key.sh`（產 identity）。
★所有命令一律**自 repo 根**執行——wrapper 只掛載 `$PWD`，換目錄跑就找不到 `.sops.yaml`。

三條不可省紀律：
1. **私鑰與其 passphrase 永不進版控、永不離開持鑰機**；私鑰檔遺失或 passphrase 遺失＝該
   identity 永久失效（§15.5）。交付只交公鑰（`age1…` 開頭、非機密、無需保密通道）。
2. **改值後回寫加密檔**（§15.4）：密文檔是唯一真相，明文 `$SECRETS_DIR` 只是投影；不回寫＝
   下次 decrypt 判 DIFF 另存 `<name>.txt.new` 不覆寫，值就分叉。
3. **加密不需私鑰、解密才需**：age 加密只用公鑰——§15.4 的回寫與 §15.7 步驟 3 全程無 passphrase；
   只有 `-d`／`updatekeys` 需要。

★**輸入 passphrase：只有一次**（預設姿態＝自動應答，安全姿態拍板見 ADR 0013）。
`python3 deploy/decrypt-secrets.py` 把 sops 提示行與解密輸出收進同一條容器 pty 流，畫面上常
看不到提示，故改由腳本代勞：它先向你要一次 passphrase（不回顯），其後**每偵測到一個提示就
餵一次**、次數邊讀邊數不預測（L-005）；identity 無 passphrase 殼＝零提示直通，此時直接按
Enter 即可。★時機仍看腳本自己印的**預告行**：預告行出現後再輸入；搶在它之前打字＝該串字被
host shell 回顯成明文留在畫面與 scrollback（rev4:L-179）。本管線零 gpg 前置（passphrase 由
sops 內嵌 age 直讀容器內 `/dev/tty`）——提示異常不要往 gpg-agent／pinentry 方向查。
★**互動探查／解回驗收也走 `decrypt-secrets.py`、勿裸 `./deploy/sops.sh -d`**：裸 -d 對每個
recipient 各索一次 passphrase，且 stdout 重導向＋`-t` 並存時提示與資料**同流**（wrapper 檔頭
既載）——重導向到 /dev/null 連提示一起隱形、盲打必敗（2026-08-08 B-041 驗收實撞）。

★**逐次手打退路＝`RV5_DECRYPT_MANUAL=1`**（嚴格判 `1`；災難復原路徑不鎖死）。走這條時下列
四條全數適用，也正是 ADR 0013 記在退路帳上的風險面：★**次數＝recipient 數**（每個 recipient
各索一次、皆同一個 passphrase；`decrypt-secrets.py` 會自密文現算後印在預告行）。實測
（2026-08-06、單檔掛載×2 recipient、逐次手打姿態）：恰 2 次，且**單次提示內無重試迴圈**
——passphrase 打錯即該 masterkey 失敗、不會再問一次。★**打太早會外洩**：本路徑無代餵、字得
直接進容器，故預告行印出後仍須**等容器接管 tty 再輸入**；搶在容器接管之前打字＝該串字被
host shell 回顯成明文留在畫面與 scrollback（rev4:L-179）。★**打太晚同樣會外洩**：sops 已結束才
輸入的那一次落到 host shell，畫面會留下 `<你打的字>: command not found` 並進
`~/.bash_history`——徵狀就是「我輸的次數比預告多」；處置＝`history -d <行號>`＋清 scrollback。
★**絕不空答**：任一次空答即以 `passphrase can't be empty` 整體失敗（判讀＝§15.2）。

### 15.2 加人四步（新成員／新機器）

**步驟 1【新成員做】產 identity**：`bash deploy/generate-age-key.sh`（產到預設
`~/.config/sops/age/keys.txt`、passphrase 加殼；覆蓋前有閘——**覆蓋＝永久銷毀既有私鑰、
其密文即刻不可解**）。host 端不需要 age 二進位：腳本每次都重建 `deploy/Dockerfile.age`
（ADR 0011 ③ 類、沿 latest）；離線時退回本機既有映像並印警示，首次產鑰則必須能連外一次。
　★**passphrase 提示文字看不見**：age 跑在容器裡，提示與產物併成同一個 pty 流被腳本捕捉
　（同 §15.1 的併流限制）。腳本會先印預告，之後**畫面停住就是在等你打字**，打完 Enter、
　共兩次（設定＋確認），輸入不回顯屬正常。★**絕不空答**：空答會讓 age 自動生成一組只印在
　那條看不見的流裡的 passphrase＝這把鑰匙沒有人能解開——腳本偵測到即擋下、不落檔。
　★**註記：該機已有前代 identity 時（跨代並存機）＝保留舊鑰、另產第二把**。腳本有覆蓋閘會擋下
　（`FAIL：… 已存在——覆蓋＝永久銷毀該私鑰`），**絕不可繞過**：覆蓋掉前代私鑰＝該代密文從此
　不可解、不可逆。正解：
```bash
bash deploy/generate-age-key.sh keys-fork260509-rev5.txt
# 之後解密照常跑、★毋須帶任何環境變數——wrapper 認得這個檔名、會自動選它
python3 deploy/decrypt-secrets.py
```
　檔名取 **repo 目錄名**（`keys-fork260509-rev5.txt`）而非 `keys-rev5.txt` 這類短代號——跨代並存
　的機器上短代號家族必撞名，此即 `rev4:0084` 付過代價換來的命名紀律（同源＝`SECRETS_DIR`
　亦以 repo 目錄名為根）。放別處不行：wrapper 只認 `~/.config/sops/age` 這一個目錄。
　★**這個檔名是機器口徑、不只是慣例**：wrapper 見到它就**只掛這一支**到容器內預設尋鑰路徑，
　令容器內**恰有一把** identity。掛整個目錄（＝本機另有前代 `keys.txt` 時的舊行為）會讓 sops
　把他代的鑰一併載入、並對「每個 recipient × 每把鑰」各索一次 passphrase——提示與資料同流
　不可見，任一次空答即整體失敗（L-005）。用別的檔名（如 §15.3 演練鑰）＝以 `RV5_AGE_KEY_FILE`
　給 **host 端絕對路徑**覆寫。
　★rev5 **刻意不沿用前代 recipient**（`.sops.yaml` 註解明載：沿用＝前代私鑰能解 rev5 密文、違
　世代錯開紀律），故前代那把鑰在 rev5 永遠無效，這是設計不是漏配。

**步驟 2【新成員做】交付公鑰**：把腳本印出的 `age1…` 公鑰給管理者。公鑰非機密，任何管道皆可。

**步驟 3【管理者做，必須在尚能解密的機器】加 recipient 並重加密**：
```bash
# ① 把公鑰加進 .sops.yaml 的 age: 清單（YAML 清單形、一行一把）
# ② 重新包資料金鑰給新的收件人集合（需 passphrase；-y 免互動確認但仍需 passphrase）
./deploy/sops.sh updatekeys deploy/secrets.dev.enc.yaml
```
　驗 diff：應只動 `sops:` metadata 段（age recipients 清單與 lastmodified）；**10 支機密的
　`ENC[…]` 本體不變**——updatekeys 換的是「包資料金鑰的收件人」、不是資料本身。若 `ENC[…]`
　也變，表示有人同時改了值，停下來查清楚再 commit。

**步驟 4【管理者做】同批 commit**：`.sops.yaml` ＋ `deploy/secrets.dev.enc.yaml` 兩檔一起
commit＋push（分開推會出現「清單有你、密文還沒給你」的中間態）。

**★末條**：少了步驟 3，新私鑰不在 recipient 清單裡＝拉到的密文一律解不開——這是最常見的
「我照做了怎麼還是解不開」原因。

**★失敗訊息判讀（此訊息會誤導）**：新成員側解不開時 sops 會印
`identity did not match any of the recipients` 並附一長串「找不到金鑰於 SOPS_AGE_KEY_FILE…」，
讀起來像「你的鑰匙有問題」，但**真正的判準是 `Group 0` 底下列出的 recipient 清單**：

- `Group 0` 只列**管理者那一把** → 步驟 3／4 尚未做或尚未 push；**新成員這端無事可做**，
  重產鑰也不會好（新鑰同樣不在清單裡）。等管理者完成加人再 `git pull` 重跑。
- `Group 0` **已含新成員的公鑰**卻仍失敗 → 才輪到查這端：passphrase 打錯、或用到別把
  identity（見步驟 1 註記的檔名口徑）。
- `Group 0` 已含新成員公鑰、且錯誤是 **`passphrase can't be empty`** → **不是鑰匙問題，是有
  一次提示收到了空字串**。判讀不變，成因隨互動路徑分流：
  - **自動路徑（預設）**：你在腳本那一問直接按了 Enter，空字串隨後被餵給每個提示、sops 遂
    整體失敗。重跑並確實輸入即可（真的零提示的鑰不會走到這個錯誤）。
  - **`RV5_DECRYPT_MANUAL=1` 逐次手打**：提示不只一次而有一次被空答。sops 對**每個 recipient**
    各索一次 passphrase（容器內若還有他代的鑰，還要再乘上鑰匙數），而提示被暫存檔捕捉、
    畫面上看不見。處置＝把 rev5 那把改名為 `keys-fork260509-rev5.txt`（wrapper 即改走單檔
    掛載、次數收斂為 recipient 數），並依 `decrypt-secrets.py` 預告行印出的次數**每一次都
    輸入**、絕不空答。

前兩種的頭一種是流程未完成、不是故障；`WARN … encrypted identity … didn't match file's
recipients` 一行同樣只是這件事的複述——它在多 recipient 下屬**正常過程訊息**（試到不是你那把
的 recipient 時必然出現），不可據以判定失敗。
**驗收（新成員側）**：`python3 deploy/decrypt-secrets.py` 寫出 10 支且零 `.new`，
`python3 deploy/preflight-secrets.py` rc=0。

### 15.3 撤銷與 recipient 輪替（五準則）

程序＝從 `.sops.yaml` 移除該公鑰 → `./deploy/sops.sh updatekeys deploy/secrets.dev.enc.yaml`
→ 兩檔同批 commit。五條準則：

1. **只 re-key 不換值＝形式撤銷**：移除只讓**新**密文不可解；舊密文永遠在 git 史，對方若曾
   解過就已握有明文。**撤銷必連帶輪替機密值本身**（§15.6）——這條是實質、其餘是形式。
2. 撤銷後 recipient 清單**不得為空**，也不得只剩不在手邊的 identity。
3. **絕不移除自己手上唯一那把**：`updatekeys` 需先解密，移除後就再也解不開＝把自己鎖在門外。
4. 撤銷連動：該成員機器上的 `$SECRETS_DIR` 明文與其私鑰不受本程序影響（在他機器上），故
   準則 1 的值輪替是唯一有效手段。
5. **撤銷演練需第二把**：先 `bash deploy/generate-age-key.sh keys-fork260509-rev5-drill.txt` 產第二把、加入 recipient
   並確認它真的能解，再演練移除第一把——否則演練失敗就是永久失效。★演練鑰的檔名**不等於**
   wrapper 自動選用的那個名，故用它解密時要覆寫：
   `RV5_AGE_KEY_FILE=$HOME/.config/sops/age/keys-fork260509-rev5-drill.txt python3 deploy/decrypt-secrets.py`
   （★給 **host 端絕對路徑**、非容器內路徑；wrapper 自行對位掛載）。

### 15.4 值變更後回寫加密檔

**何時**：跑過 `python3 deploy/generate-secrets.py --force`、單支重生（刪檔重跑）、或人工編輯
`$SECRETS_DIR/<name>.txt`（例：填 `alert_webhook_url` 真值、把 `smtp_password` 換成 Gmail
app password）之後。**不需 passphrase**（見 §15.1 紀律 3）。

**路徑 (a)｜全套重建**（`$SECRETS_DIR` 已有全部 10 支明文時，最常見）：
```bash
cd <repo 根> && umask 077
SD="$(sed -n 's/^SECRETS_DIR=//p' .env)"
: > tmp/plain.yaml
for k in postgres_password redis_password jwt_secret refresh_token_secret captcha_secret \
         reaper_password grafana_admin_password smtp_password email_verify_secret \
         alert_webhook_url; do
  printf '%s: %s\n' "$k" "$(cat "$SD/$k.txt")" >> tmp/plain.yaml
done
./deploy/sops.sh -e --filename-override deploy/secrets.dev.enc.yaml tmp/plain.yaml \
  < /dev/null > tmp/enc.new
mv tmp/enc.new deploy/secrets.dev.enc.yaml && chmod 644 deploy/secrets.dev.enc.yaml
rm -f tmp/plain.yaml
```
　★上面那行 `printf` 是**裸量 YAML 產生器**：值原樣接在 `key: ` 之後，故值若含「冒號空白」、
　井號或前後空白，產出的 YAML 會被 sops 解析成別的東西——這類值須在 `sops -e` 之前**自行按
　YAML 規則加引號**。引號形是安全的：decrypt 走 `--output-type json` ＋ JSON 解析，逐位元組
　還原原值、不會把引號寫進 `.txt`（ADR 0010；舊 bash 版逐行拆 key 還原不回來，才要求一律裸量）。
　★**含換行的值一律不可用**：decrypt 的 CR／LF 護欄會指名該 key、零寫入退出（落點檔形＝
　一值一檔零換行）。★`< /dev/null` 讓 stdin 非 tty、wrapper 不掛 `-i -t`，從根上不生 CRLF 與
　提示併流。★輸入檔落 `tmp/`（gitignored）是**必要**的：wrapper 只掛載 `$PWD`，repo 外的檔
　容器讀不到。

**路徑 (b)｜只改一兩支且 `$SECRETS_DIR` 不全**：走 §15.7 三步往返。

**驗收**：`python3 deploy/decrypt-secrets.py` 後零 `.new` ＋ `python3 deploy/preflight-secrets.py` rc=0。

### 15.5 金鑰／passphrase 遺失與災難復原

私鑰檔與 passphrase **缺一即不可解**，故離線備份義務**含 passphrase 本身**。四種情境：

| 情境 | 處置 |
|---|---|
| 自己這把失效、**他人尚可解** | 走 §15.2 產新鑰重新加入；舊 identity 依 §15.3 撤銷 |
| 自己這把失效、**唯一 identity** | 密文永久不可解（無後門、設計如此）→ 下一列 |
| **全部 identity 皆失去** | `python3 deploy/generate-secrets.py --force` 重產全部亂數機密（dev 值本就是亂數、無歷史價值）→ 依 §15.4 回寫新密文 → `.sops.yaml` 換成新 recipient。★**人工真值必須在原始來源重新取得**（SMTP app password 回 Gmail 重簽、`alert_webhook_url` 回告警平台重取）——這些不是亂數，重產不回來 |
| **成員離開／持鑰人失聯**、其 identity 仍有效 | 走 §15.3 撤銷該公鑰；★準則 1＝**只 re-key 不換值＝形式撤銷**——對方曾解過就已握有明文，撤銷**必連帶輪替機密值本身**（依 §15.6 輪替表換 9 支 leaf＋`--compose-only` 重組；★人工真值——SMTP app password 與 `alert_webhook_url`——`--force` 不重置，須回原始來源重取，同 §15.6 第三列警語） |

舊密文留在 git 史不必也無法移除——沒有任何 identity 能解它。

### 15.6 輪替表

| 對象 | 產法 | 觸發 |
|---|---|---|
| 9 支 leaf（postgres／redis／jwt／refresh／captcha／reaper／grafana／smtp／email_verify） | `python3 deploy/generate-secrets.py --force`（全部重產）或刪單支檔後重跑（單支重生） | 疑似外洩、成員撤銷（§15.3 準則 1）、prod 上線前 |
| 3 支 composite（`database_url`／`redis_url`／`reaper_database_url`） | `python3 deploy/generate-secrets.py --compose-only`（自 leaf 重組） | 對應 leaf 換過即須重組 |
| `alert_webhook_url` | 人工填真值（`--force` **不**重置；重置法＝刪檔重跑） | 起 obs 軌前（BACKLOG 滯後卷） |
| age identity | `bash deploy/generate-age-key.sh` | 成員異動、私鑰疑洩 |

★composite 三支**不在密文檔內**（密文＝9 leaf＋`alert_webhook_url`），故換 leaf 後除了 §15.4
回寫，還要跑 `--compose-only` 重組落點。
★**定期輪替節奏未拍板**，現行實務＝觸發式；prod 是否入 roadmap 定案時一併拍（BACKLOG 拍板待答項）。

### 15.7 手動呼叫 wrapper 的正規化三步

僅用於 §15.4 路徑 (b) 或需直接編輯密文時。**日常解密一律用 `python3 deploy/decrypt-secrets.py`**
（已內建全部正規化、名冊斷言與權限自證）。

**步驟 1｜解密（需 passphrase、走 tty）**——wrapper 在 stdin 有 tty 時掛 `-i -t`，容器 pty 會把
換行改 CRLF、且 passphrase 提示行與資料同流，**必須自行正規化**（與 decrypt-secrets.py 的
`normalize_stream` 同形）：
```bash
cd <repo 根> && umask 077
WORK="$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/fork260509-rev5/edit.XXXXXX")"
./deploy/sops.sh -d deploy/secrets.dev.enc.yaml > "$WORK/raw.out"
tr '\r' '\n' < "$WORK/raw.out" | sed -E "s/$(printf '\033')\[[0-9;]*[A-Za-z]//g" > "$WORK/plain.yaml"
```

**步驟 2｜編輯**：改 `$WORK/plain.yaml`；值依 YAML 規則書寫（需引號者就加引號——decrypt
逐位元組還原原值），★但不可用含換行的值（decrypt 的 CR／LF 護欄零寫入退出）。同 §15.4。

**步驟 3｜重加密（不需 passphrase）**——輸入檔**必須搬進 repo 內**（wrapper 只掛載 `$PWD`）：
```bash
cp "$WORK/plain.yaml" tmp/plain.yaml
./deploy/sops.sh -e --filename-override deploy/secrets.dev.enc.yaml tmp/plain.yaml \
  < /dev/null > tmp/enc.new
mv tmp/enc.new deploy/secrets.dev.enc.yaml && chmod 644 deploy/secrets.dev.enc.yaml
rm -f tmp/plain.yaml && rm -rf "$WORK"
```
★收尾**必刪兩處明文**（repo 內 `tmp/` 與快取 `$WORK`）——步驟 3 的 `< /dev/null` 是讓 `-e`
不走 tty 分支、從根上不生 CRLF 與併流的關鍵。

## 16. 部署 checklist（信任錨與 IP 存取閘）

★本章＝004-ip-trust-anchor 交付的**文件**（spec FR-043），不是 prod 設定檔——rev5 的 prod
資產不入 roadmap（**ADR 0014**；本章的來歷即該檔「後果」節逐字寫的「部署 checklist 改明文
併入 ingress 刀交付物」）。本章寫的是「prod 部署時要逐項確認什麼」，而每一項的樣例都取自
dev **已實跑過**的那一份。

### 16.1 信任模型設定檔

- 路徑由環境變數 `APP_TRUST_MODEL_PATH` 指向，**啟動時一次載入、唯讀共享**；缺檔或解析失敗
  一律**只縮小信任**（三層降級語意＝`specs/004-ip-trust-anchor/contracts/trust-model-config.md`
  的「載入失敗語意」節）。dev 現況＝compose 把 `deploy/trust-model.dev.toml` 唯讀掛進容器內的
  `/etc/rev5/trust-model.toml`。
- ★**樣例一律以 dev 實際掛載的那一份為基底**＝`deploy/trust-model.dev.toml`（**跑過的形**）。
  刻意不另寫示意稿：rev4 的部署樣例**從未被任何環境實跑過**，而那正是本刀 research R7 抓到的
  缺陷——rev4 的驗收手冊寫了「構造轉發標頭模擬公網來源」的走查步驟，但其 compose／`.env`／
  部署腳本從未設過信任模型 ⇒ 全空集合下對端閘恆先觸發、構造標頭一律被忽略，那些步驟跑不出
  它宣稱的結果。**驗收程序存在、使其成立的設定不存在**，兩邊各自看起來都沒問題。
- **prod 由 dev 那份擴充**（逐集合語意與 prod 樣例＝上述 contracts 檔的「prod 樣例」節）：
  最少要填 `internal_default`（我方內網／容器網段——★缺它則對端閘恆先觸發，第二／三層與兩個
  覆蓋層在**任何環境**都是死碼）；前置 CDN 者另填 `cf_gate_egress`（掛驗證閘的我方 ingress
  出口——邊緣驗證升等的四個前置之一，缺它則驗證標記不被採信）與 `[[cdn]]`。
- **驗收指令**（dev 實跑過的形；★過濾面刻意**不**用 `grep -i trust`，理由見本節末）：

```bash
# ①終態總結行——確認「設定有掛上、掛的是預期那一份、逐集合真的有值」
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs rust-api 2>&1 \
  | grep -E '信任模型|connecting_ip_header' | tail -1
# ②降級告警計數——**「沒有告警」的判準即此數**，期望輸出 0
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs rust-api 2>&1 \
  | grep -E '信任模型|connecting_ip_header' | grep -c '"level":"WARN"'
```

  **預期**：①最後一行＝「信任模型載入完成（trust model）」的 `"level":"INFO"` 行——載入面的
  告警一律在此總結行**之前**發射，故它是該次 boot 這一段的收尾標記；②輸出 **0**。
  ★**②才是判準、①判不出這件事**：三層降級皆**不 panic**、boot 照常繼續，總結行在任何降級下
  都照印（只是欄位變 0），「①看起來正常」與「零告警」是兩件事。
  ★②橫跨 log 內全部 boot 累計，方向保守（舊 boot 的告警也計入、寧可多叫）；剛部署完當場跑
  即精準，log 已累積多次重啟時加 `--since <時間>` 收窄。
  ★②**看印出的數、不要看 rc**：`grep -c` 零命中時印 `0` 而 **rc=1**（grep 的既定行為）
  ——即「通過」這一格的 rc 恰是 1。包進 `set -e` 腳本時須自行接 `|| true`。
  ①的總結行另帶 `trust_model_path`（據此可一眼看出「設定有掛上、且掛的是預期那一份」）與逐集合
  載入筆數。★**計數欄數與集合數刻意不相等**：三個陣列型集合（`[[cdn]]`／`[[my_public]]`／
  `[[bindings]]`）各報**條目數與網段數兩欄**（理由＝`main.rs` 該發射點的就地註記：條目非零而
  網段為零的模型一條都不受信，只報條目數等於把它寫成「有值」）⇒ 共 **9 個計數欄**。
  dev 現況逐字實得（`internal_default` 為 1、**其餘 8 欄皆 0**，對應 `tunnel`／`cf_gate_egress`
  ／`[[cdn]]`／`[[my_public]]`／`[[bindings]]` 這 **5 個 dev 刻意不宣告的集合**）：

```text
"internal_default":1,"tunnel":0,"cf_gate_egress":0,"cdn_entries":0,"cdn_networks":0,
"my_public_entries":0,"my_public_networks":0,"bindings_entries":0,"bindings_internal_networks":0
```

  ★上段為**同一行**輸出、僅為版面折成兩行；照本節逐項核對時請數 **8 個 0**（把「5 個集合」
  直接當成「5 個 0」或「6 個 0」都會與實跑對不上——本節的硬要求正是樣例 MUST 是跑過的形）。
- ★**為何過濾面不用 `grep -i trust`**（本節自身曾踩過的同型復發，見 L-044）：載入面共**九類**
  告警，逐類以代表性 JSON 行過 `grep -i trust` 實測，**四類漏網**——TOML 整體解析失敗、
  未知鍵（FR-033，★正是 rev4 實暴形「設定存在卻完全沒生效」）、單一集合清空（FR-010 第三層）、
  訪客位址標頭名不可用。這四類的整行 JSON（含 `message`／`scope`／`reason`／`target` 各欄）
  皆無 ASCII `trust`。命中的五類裡另有兩類（讀檔失敗／內容非 UTF-8）只因 dev 路徑字串恰為
  `trust-model.toml` 才命中，而本節開頭已寫明路徑由 `APP_TRUST_MODEL_PATH` 指向 ⇒ prod 換檔名
  即一併漏網。**過濾不到 ⇒「且沒有 X 類告警」這種預期在結構上驗不出來**。
  改用 `信任模型|connecting_ip_header` 聯集則九類全覆蓋：前八類的 `message` 一律含「信任模型」，
  第九類（標頭名）的 `message` 含 `connecting_ip_header`。
- ★連帶棄掉的是 `tail -3`：`boot 就緒（config→db→enforcer→cache→trust→ipgate→router）` 這行含
  ASCII `trust`，本機實跑 `grep -i trust | tail -3` 的 3 行中有 **2** 行是它；多重啟幾次即可把
  總結行整個擠掉。聯集式不含 `trust` 字面，結構上不會被 boot 行污染，故 `tail -1` 即足。

### 16.2 ★CDN 網段的一致性義務（兩處各存一份、必須同步更新）

| 落點 | 用途 |
|---|---|
| `deploy/nginx/nginx.conf` 的 `geo $cf_edge` 區塊 | 判**傳輸層對端**是否為 CDN 邊緣 → 決定 `X-CF-Verified`／`CF-Connecting-IP` 兩標頭注入或移除 |
| 信任模型檔的 `[[cdn]]` 之 `networks` | 判**轉發鏈中的位置錨**（Tier-1） |

- 兩者用途不同、**內容必須一致**；供應商的網段表是部署參數、會變（Cloudflare 的公開表
  ＝`https://www.cloudflare.com/ips/`），**更新節奏＝跟著供應商公告走，且兩處一起改**。
- ★**只改一邊的表徵＝信心大量落 `cdn_mismatch`**：邊緣驗證標記為真（nginx 那半認得這個邊緣）
  但位置錨推導與之不一致（信任模型那半不認得），判定面即降級留痕。反過來只改信任模型檔而
  漏改 nginx，則標頭根本不會被注入、升等的四前置永遠湊不齊。
- ★dev 兩處皆為**空集**，故 `cdn_verified`／`cdn_mismatch` 兩態在 dev 經反向代理**結構性
  不可達**（research R7 有逐態對照表）——這是誠實分界、不是漏填。

### 16.3 鎖定來源站僅接受 CDN 邊緣連線（★縱深防禦建議、**非**承重前提）

- 前置 CDN 時，建議在來源站的網路層（安全群組／防火牆／CDN 專屬通道）只接受 CDN 邊緣位址
  的連線。
- ★**它在 rev5 是縱深防禦、不是承重前提**：spec FR-005 的**錨硬化**（憲法島 F 之 F6）已
  **入碼**——Tier-1 位置錨成立的必要條件是「錨的右鄰起、直到傳輸層對端，全屬受信基建」，
  否則**錨棄用、退下一層**。故有人繞過 CDN 直連來源站並在轉發鏈裡填公開可查的 CDN 邊緣
  位址當錨時，還原結果是**攻擊者的真實位址**，不是他偽造的那個。
- ★這與前代**相反**、是本刀刻意翻案的點：前代把安全保證整個壓在「部署方 MUST 鎖 origin
  僅接受 CDN 邊緣連線」這條**文件約束**上，本刀把它入碼後降為建議（翻案的耐久家＝憲法
  `.specify/memory/constitution.md` §I.7 島 F 之 **F6** 條文本體與其 v1.4.0 amendment 條目；
  拍板脈絡＝ADR 0040）。**文件約束沒有任何機器面，部署方漏做時零訊號**——那正是降它為
  縱深防禦、而非續當承重前提的理由。

### 16.4 其餘 prod 遞延項（留指針、不展開）

| 項 | 去處 |
|---|---|
| 登入頁三顆快速登入鈕把 dev seed 帳密帶進前端 bundle ★轉 prod 前必須拆除 | ops/BACKLOG **B-064** |
| 前端 demo 資產去留（alova 第二請求棧等） | ops/BACKLOG **B-018** |
| 備份自動化第二段（排程化／機密與資料卷配對備份／還原演練自動化） | ops/BACKLOG **B-023**；第一段已收單＝§6 |
| 快取持久化模式（redis AOF） | 004 重評結論＝**維持現狀不開**（暴險受「狀態即權威」封頂：判定面不依賴快取、解鎖標記遺失可再解鎖自癒） |
| IP 閘阻擋告警無量的上界（加了 deny 規則後 log 量由被擋方決定） | ops/BACKLOG **B-077** |
| 機密輪替與 prod 值 | §7、§15 |
