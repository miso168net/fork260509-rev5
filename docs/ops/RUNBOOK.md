# RUNBOOK — dev stack 操作手冊

本檔＝「怎麼操作」唯一的家。分工（防鏡像）：系統長怎樣→活書 §7；十三機密明細表→
`deploy/secrets/README.md`；埠／帳號全表→`docs/generated/reference/`；坑全文→`docs/ops/LESSONS.md`。
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

（本章隨觀測層刀補實文；創世期無內容。）

## 12. 工具鏈速查（★python 工具一律直跑或 `python3` 前綴、bash 前綴＝假失敗 rev4:L-129/rev4:L-143）

| 命令 | 作用 | 需運行中 stack |
|---|---|---|
| `python3 tools/docs-sync.py generate` | 重算 docs/generated/ 全部（跑完必 git add） | 否 |
| `python3 tools/docs-sync.py check` / `lint` | pre-commit 兩道（staged 過期／Lint03~Lint25） | 否 |
| `python3 tools/docs-sync.py refresh` | 自實庫撈 schema/accounts 快照 | **是** |
| `python3 tools/docs-sync.py errata <詞>` / `test` | 全 repo 同語意枚舉／自測 | 否 |
| `python3 tools/schema-gate.py check` | 三閘全跑（gate1 結構／gate2 欄序＋seed／audit archetype；fixtures⊕演進帳合成、入口自證 self-test；不進 pre-commit、手動跑） | **是** |
| `python3 tools/schema-gate.py test` | 自測 | 否 |
| `python3 tools/schema-gate.py doccheck` | data-model §2/§6 文件面 vs 凍結 fixtures 對賬（B-010；離線、不入 pre-commit 常跑鏈——手動／review 輪跑） | 否 |
| `python3 tools/wire-schema.py extract` / `check` / `test` | 容器內抽 typings→wire-schema.json 快照／快照 drift 比對（`--staged-gate`＝pre-commit 收窄形）／自測 | extract **是**、check 未起→警告放行 |
| `python3 tools/fork-delta-lint.py` | base-web 原行紀律（前置：fork 源倉在 example 分支） | 否 |
| `python3 tools/secret-value-guard.py check --full-tree` | 機密現值 × 全 tracked 檔一次性盤點：staged 增量對既存明文結構性失明（rev4:L-190）、本旗標補盤點面——導入既有 repo 與定期體檢用；命中只印「檔:行｜機密名」絕不印值、有命中 exit 1。★不進 pre-commit（全樹非增量；增量面＝pre-commit 自動跑裸 check） | 否 |
| `python3 tools/view-render-guard.py check` / `test` | 管理頁 `base-web/src/views/manage/**` 零原始 HTML 插值斷言（FR-038；六條禁用字面逐行掃原文、**不解析註解與語法**——能藏在註解裡就能藏在字串常值裡再拼接）／自測。★pre-commit **條件觸發**：base-web pin bump 或本檔 staged 時自動跑（`base-web/src` 缺席＝具名跳過）；掃到零檔＝fail-loud rc=2 | 否 |
| `python3 tools/route-artifact-gate.py check` / `test` | 路由外掛產物四檔（`src/router/elegant/{imports,routes,transform}.ts`＋`src/typings/elegant-router.d.ts`）之**產出檔集對賬＋重算冪等＋零手改**三道——★憲法 §III.2 第五列「產物檔紀律」的**唯一**機器守（該四檔受 fork-delta 檢查全域豁免）。★**刻意不掛 pre-commit**：實跑外掛三趟、實測 15.2s，且依賴 dev stack 在跑，而 pre-commit MUST 在 stack 沒起時可用；落點＝**單元邊界／CI 手動跑** | check **是**、test 否 |
| `python3 tools/entity-drift-gate.py check` / `test` | entity（rust-api/entity/src）vs schema 快照漂移比對（欄序歸 gate2、index/constraint 歸 gate1、default 不驗）／自測 | 否 |
| `bash tools/bootstrap.sh` | 新機重建／舊機體檢 | 否 |
| `./deploy/sops.sh <sops 參數>` | sops 官方容器 wrapper（digest 釘版、自 repo 根跑；自動選鑰＝見 §15.2 步驟 1 註記，`RV5_AGE_KEY_FILE` 可覆寫；營運程序＝§15） | 否（需 docker） |
| `python3 deploy/decrypt-secrets.py` | 加密檔 → `$SECRETS_DIR` 寫出明文機密檔；passphrase **只輸入一次**（腳本對每個 recipient 提示自動代餵；`RV5_DECRYPT_MANUAL=1`＝逐次手打退路） | 否（需 docker＋互動 tty） |
| `bash deploy/generate-age-key.sh [檔名]` | 產 age 金鑰（覆蓋閘＋先寫 `.new` 再 `mv`＋產物自檢；age 走容器＝`deploy/Dockerfile.age`，每次產鑰 `docker build --pull --no-cache` 取真最新）。省略檔名＝預設 `keys.txt`；同機第二把給非預設長檔名（跨代並存機的正解＝§15.2 步驟 1 註記） | 否（需 docker＋真 tty；build 需網路，離線退回本機既有映像＋警示） |

退出碼注意：view-render-guard＝命中 1、射程異常（掃到零檔）2、用法錯 64；route-artifact-gate＝判定紅 1、環境前提不成立（stack 未起／基線缺席）2、用法錯 64；
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
  具名跳過，同 fork-delta／entity-drift 的 Day-1 模式）；rust-api pin bump 或 schema 快照
  （docs/ops/reference-src/schema-snapshot.json）staged 時另跑
  `python3 tools/entity-drift-gate.py check`；`bash tools/bootstrap.sh` 體檢則無條件
  全跑工具名冊全部 test。全鏈計時兩級門檻與效能預算＝§12.1（數字只住那一處）。
- **lint 條款**：全 24 條（範圍 Lint03~Lint25；23 號已拆除、編號不重用）。severity 三分：
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

- **兩級門檻語意**：pre-commit 全鏈牆鐘超 **20s**＝警戒（列示放行、劣化趨勢訊號）、超
  **45s**＝硬擋（狀態型：`--no-verify` 只延後、下次 commit 仍提醒）。★數字權威＝
  `.githooks/pre-commit` 常數 `PRECOMMIT_WARN_SEC`／`PRECOMMIT_FAIL_SEC`（本節僅引用；
  調整走 ADR、不得就地改數字）。機器閘只有這一道**全鏈 45s**；本節其餘數字全屬觀測基準
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

- **本批終態實測**（2026-08-08、WSL2 drvfs/9p、每命令 3 次取中位數；量測面＝python 工具
  ——betterleaks 樣式掃描為原生二進位、不在本表量測面；另**四**支 **gitlink 觸發段**——
  fork-delta-lint〔pre-commit 自註 drvfs 約 9s〕／wire-schema check --staged-gate／
  entity-drift-gate check／**view-render-guard check**〔004 U-I 加掛，WSL2 drvfs 3 次
  中位數 **0.18s**、單跑上限 **1s**（純檔案掃描、受掃 15 檔，落下限檔位）〕——屬另一
  觸發維度亦不在本表，收刀簿記型 commit（pin bump＋
  多工具 staged）之真實最壞須在情境 B 上再加約 9s+）。**單跑上限推導＝該列中位數 ×3
  進位整秒、下限 1s**：×3 沿 pre-commit 既有餘裕先例（45s 對 rev4 WSL2 健康值 15.7s
  ≈3 倍）；下限 1s 吸收 drvfs 抖動的次秒級絕對尖峰；一律以 WSL2（慢端）實測定值——
  APFS 同工具快一個量級（pre-commit 註解既載事實），故上限對兩平台皆有餘裕。

  情境 A＝基礎鏈（無 gitlink、無 tools staged）：

  | 段 | 中位數 | 單跑上限 |
  |---|---|---|
  | `python3 tools/secret-value-guard.py check` | 0.179s | 1s |
  | `python3 tools/docs-sync.py check` | 1.004s | 4s |
  | `python3 tools/docs-sync.py lint` | 5.858s | 18s |
  | **基礎鏈合計** | **7.041s** | **22s**（＝合計中位數 ×3；非逐列上限加總 23s、以本值為權威） |

  情境 B＝理論最壞 staged（pre-commit 名冊 11 支工具本體全 staged、條件自測全中）＝
  基礎鏈＋11 支 test：

  | 支 | 自測案數 | 中位數 | 單跑上限 |
  |---|---|---|---|
  | `python3 tools/docs-sync.py test` | 469 | 11.893s | 36s |
  | `python3 tools/schema-gate.py test` | 88 | 0.362s | 2s |
  | `python3 tools/wire-schema.py test` | 27 | 0.191s | 1s |
  | `python3 tools/secret-value-guard.py test` | 56 | 0.420s | 2s |
  | `python3 tools/entity-drift-gate.py test` | 45 | 0.153s | 1s |
  | `python3 deploy/preflight-secrets.py test` | 30 | 0.120s | 1s |
  | `python3 deploy/decrypt-secrets.py test` | 71 | 2.367s | 8s |
  | `python3 deploy/generate-secrets.py test` | 35 | 1.769s | 6s |
  | `python3 deploy/setup-reaper-role.py test` | 32 | 0.604s | 2s |
  | `python3 deploy/backup-db.py test` | 17 | 1.645s | 5s |
  | `python3 tools/wf-watchdog.py test` | 23 | 0.211s | 1s |
  | **11 支 test 合計** | **893** | **19.735s** | — |

  **情境 B 合計＝26.776s**（7.041＋19.735；越 20s 警戒、未破 45s 硬擋——合計面守門
  仍＝全鏈 45s、不另定上限）。
- **★2026-08-16 實測資料點（004 U-I 收刀 commit，收刀簿記型：兩個 gitlink 同時 bump ＋
  `tools/docs-sync.py` staged）＝hook 自報 38s**，對照上方推估（情境 B 26.776s ＋「再加約
  9s+」≈36s）已偏高約 2s，**距 45s 硬擋餘裕僅 7s**。逐段中位數（同日、WSL2 drvfs、
  各跑 3 次）：`docs-sync test` **14.99s**（僅工具本體 staged 時）／`wire-schema check`
  **8.02s**（僅 base-web pin bump 時）／`docs-sync lint` **7.38s**（恆跑）／`fork-delta-lint`
  **5.98s**／`docs-sync check` **1.00s**（恆跑）／`view-render-guard check` 0.18s／
  `entity-drift-gate check` 0.17s／`secret-value-guard check` 0.13s。
  ⇒ **恆跑段僅 8.5s**，38s 全部來自條件觸發段的疊加。★成長面在 `docs-sync test`（隨案數）
  與 `lint`／`fork-delta-lint`（隨 repo／base-web 規模），非本刀新增的 0.18s。
  ★本表上方兩張逐支表為 2026-08-08 值、**已過期**，重量測掛在 004 之 T062（全量閘）。
- **歷史對照**（皆全鏈牆鐘粗判值、與上表逐支中位數非同一量測面）：001 收刀＝無 gitlink
  無 tools staged **1.016s**／staged `tools/docs-sync.py`（428 案自測）**27s**（出處＝
  docs/brainstorms/b8b-acceptance-evidence.md）；本維護批中途量測點（單元② commit
  1779d17 後／單元③ commit 6a6378e 後，基礎鏈＋docs-sync／schema-gate／backup-db 三支
  test 合計粗判）＝**20.9s**／**17.6s**。可比面趨勢（本節立意所在）：基礎鏈同情境自
  001 收刀約 1s 成長至約 7s（主因＝lint 條款成長至全 24 條）、距 20s 警戒餘約 3 倍
  ——下一批續比此值。
- **一致性核**：最大單支上限（docs-sync test 36s）＋基礎鏈實測 7.041s ≈43s、仍在全鏈
  45s 內——常見情境（單支工具 staged）下觀測上限先於機器硬擋喊人。逐支上限**加總**
  （基礎鏈 22s＋11 支 65s＝87s）遠超 45s——單跑上限是逐支劣化偵測基準、非「全數同時
  到頂仍過鏈閘」的保證；理論最壞情境的守門仍＝全鏈 45s。
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
- 本節為觀測基準、**無機器閘**（與 §12.1 的全鏈 45s 硬擋不同）。dev profile 的 debuginfo
  裁剪與否屬後續評估，數據前提即本表。

## 13. 故障排除速查（全文→LESSONS；此表只指路）

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
