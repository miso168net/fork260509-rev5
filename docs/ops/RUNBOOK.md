# RUNBOOK — dev stack 操作手冊

本檔＝「怎麼操作」唯一的家。分工（防鏡像）：系統長怎樣→活書 §7；十三機密明細表→
`deploy/secrets/README.md`；埠／帳號全表→`docs/generated/reference/`；坑全文→`docs/ops/LESSONS.md`。
本檔命令一律完整可複製——整行逐字貼進 shell 即可跑、一律於 repo 根執行。
創世期章節現況：§1／§12／§14／§15 為最小必備四章；其餘各章隨對應刀補實文、章內不放未經實跑的命令。

## 1. 快速啟動（新機五步）

1. `bash tools/bootstrap.sh` —— 源倉＋worktree＋hooks＋secrets 體檢（幂等、可重跑）
2. `bash deploy/generate-secrets.sh` —— 十三機密缺則補
3. `bash deploy/preflight-secrets.sh` —— up 前預檢（全齊印 OK）
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

（本章隨對應刀補實文；創世期無內容。）

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
   落 rc 2 fail-loud 指引擴充——斷言完備化由 BACKLOG B-006 承載、首筆真登記前完備）
3. `python3 tools/schema-gate.py check` —— 三閘綠（gate1 結構／gate2 欄序＋seed／audit
   archetype）；未登記漂移一律紅、「migration 已跑、登記缺席」＝gate1 紅之常態語意；
   一次性 pristine 場景加 `--container <容器名>`（預設＝compose dev stack）；判讀提示：
   同庫反覆 DROP→ADD COLUMN（含 down→up）後 gate1 會因 PG attnum 空洞報 ordinal 差
   ——補救＝pristine 重放、勿誤判真漂移

新業務表另備兩件：先補 `specs/001-schema-baseline/data-model.md` §1 archetype 歸屬、再登記
`docs/ops/reference-src/archetype-map.json`——否則 audit 表清單守門攔。

## 11. 觀測層維運

（本章隨觀測層刀補實文；創世期無內容。）

## 12. 工具鏈速查（★python 工具一律直跑或 `python3` 前綴、bash 前綴＝假失敗 rev4:L-129/L-143）

| 命令 | 作用 | 需運行中 stack |
|---|---|---|
| `python3 tools/docs-sync.py generate` | 重算 docs/generated/ 全部（跑完必 git add） | 否 |
| `python3 tools/docs-sync.py check` / `lint` | pre-commit 兩道（staged 過期／Lint03~Lint24） | 否 |
| `python3 tools/docs-sync.py refresh` | 自實庫撈 schema/accounts 快照 | **是** |
| `python3 tools/docs-sync.py errata <詞>` / `test` | 全 repo 同語意枚舉／自測 | 否 |
| `python3 tools/schema-gate.py check` | 三閘全跑（gate1 結構／gate2 欄序＋seed／audit archetype；fixtures⊕演進帳合成、入口自證 self-test；不進 pre-commit、手動跑） | **是** |
| `python3 tools/schema-gate.py test` | 自測 | 否 |
| `python3 tools/wire-schema.py extract` / `check` / `test` | 容器內抽 typings→wire-schema.json 快照／快照 drift 比對（`--staged-gate`＝pre-commit 收窄形）／自測 | extract **是**、check 未起→警告放行 |
| `python3 tools/fork-delta-lint.py` | base-web 原行紀律（前置：fork 源倉在 example 分支） | 否 |
| `python3 tools/secret-value-guard.py check --full-tree` | 機密現值 × 全 tracked 檔一次性盤點：staged 增量對既存明文結構性失明（rev4:L-190）、本旗標補盤點面——導入既有 repo 與定期體檢用；命中只印「檔:行｜機密名」絕不印值、有命中 exit 1。★不進 pre-commit（全樹非增量；增量面＝pre-commit 自動跑裸 check） | 否 |
| `python3 tools/entity-drift-gate.py check` / `test` | entity（rust-api/entity/src）vs schema 快照漂移比對（欄序歸 gate2、index/constraint 歸 gate1、default 不驗）／自測 | 否 |
| `bash tools/bootstrap.sh` | 新機重建／舊機體檢 | 否 |
| `./deploy/sops.sh <sops 參數>` | sops 官方容器 wrapper（digest 釘版、自 repo 根跑；營運程序＝§15） | 否（需 docker） |
| `bash deploy/decrypt-secrets.sh` | 加密檔 → `$SECRETS_DIR` 寫出明文機密檔 | 否（需 docker＋互動 tty） |
| `bash deploy/generate-age-key.sh [檔名]` | 產 age 金鑰（覆蓋閘＋先寫 `.new` 再 `mv`＋產物自檢＋自動取 age 並驗 digest）。省略檔名＝預設 `keys.txt`；同機第二把給非預設長檔名（跨代並存機的正解＝§15.2 步驟 1 註記） | 否（需真 tty；age 缺席時需網路） |

退出碼注意：schema-gate＝差異 1、環境不可用 2、用法錯 64；wire-schema＝抽取失敗／check
不一致 2、用法錯 64（check 於 stack 未起＝警告＋0 放行）；entity-drift-gate＝漂移 1、
異常 2、用法錯 64；docs-sync refresh
的 stack 不在走 exit 1——判讀看是哪支工具的哪個碼、勿一概當失敗。

- **子命令真表**：`docs/generated/reference/tools-cli.md`（機器生成、
  `python3 tools/docs-sync.py generate` 重算、嚴禁手改）——納冊工具子命令的查詢入口；
  lint 命令形判定基準＝工具源碼分派表、真表為同一掃源的生成物（手改真表不影響判定）。
- **pre-commit 條件觸發**（工具自測、平時零額外開銷）：staged 含某 python 工具本體才跑
  該支 test 子命令；fork-delta-lint 兩觸發條件（base-web pin bump／工具本體 staged）取聯集
  只跑一次；base-web pin bump 時另跑 `python3 tools/wire-schema.py check --staged-gate`
  （staged 區間零 typings 變動即跳過）；rust-api pin bump 或 schema 快照
  （docs/ops/reference-src/schema-snapshot.json）staged 時另跑
  `python3 tools/entity-drift-gate.py check`；`bash tools/bootstrap.sh` 體檢則無條件
  全跑工具名冊全部 test。全鏈計時兩級：超 20 秒 WARN、超 45 秒 ERROR（調整走 ADR）。
- **lint 條款**：全 23 條（範圍 Lint03~Lint24；23 號已拆除、編號不重用）。severity 三分：
  ERROR＝exit 1 擋 commit、WARN＝放行列示、跳過＝條款不適用而未執行、落跳過明細
  （**跳過≠通過**）。摘要末行形＝`lint：X 錯誤／Y 警告／Z 條款跳過／共 N 條款`。
  逐條機制→工具源碼與 `python3 tools/docs-sync.py test` 自測敘述；創世期具名豁免
  （DAY1_EXEMPTIONS）逐筆帶解除謂詞、到期即紅。
- **機密工具鏈釘版**：Betterleaks **1.7.3**（原生二進位、bootstrap 存在性斷言同值）／sops
  容器 **v3.13.3-alpine**（index digest＝
  `sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`、寫死於容器
  wrapper 常數）／age **v1.3.1**（一次性產鑰工具、不常駐：官方 release 二進位以 release API
  digest 欄位驗 sha256、取用完畢即清理）。

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
（僅存持鑰者腦中）故**未實跑**，其正規化片段係逐字鏡像 `deploy/decrypt-secrets.sh` 的
`normalize_raw`——該函式每次 decrypt 都在實跑。

### 15.1 資產、工具與不可省紀律

資產三件：`deploy/secrets.dev.enc.yaml`（密文、**tracked**、承載 10 支＝9 leaf＋
`alert_webhook_url`）／`.sops.yaml`（recipient 公鑰清單、tracked）／
`~/.config/sops/age/keys.txt`（**私鑰＝passphrase 加殼**、目錄 700 檔 600、**永不進版控**）。
工具＝`./deploy/sops.sh`（官方容器 wrapper、digest 釘版）、`bash deploy/decrypt-secrets.sh`
（密文→`$SECRETS_DIR/*.txt`）、`bash deploy/generate-secrets.sh`（產亂數）、
`bash deploy/preflight-secrets.sh`（上機前體檢）、`bash deploy/generate-age-key.sh`（產 identity）。
★所有命令一律**自 repo 根**執行——wrapper 只掛載 `$PWD`，換目錄跑就找不到 `.sops.yaml`。

三條不可省紀律：
1. **私鑰與其 passphrase 永不進版控、永不離開持鑰機**；私鑰檔遺失或 passphrase 遺失＝該
   identity 永久失效（§15.5）。交付只交公鑰（`age1…` 開頭、非機密、無需保密通道）。
2. **改值後回寫加密檔**（§15.4）：密文檔是唯一真相，明文 `$SECRETS_DIR` 只是投影；不回寫＝
   下次 decrypt 判 DIFF 另存 `<name>.txt.new` 不覆寫，值就分叉。
3. **加密不需私鑰、解密才需**：age 加密只用公鑰——§15.4 的回寫與 §15.7 步驟 3 全程無 passphrase；
   只有 `-d`／`updatekeys` 需要。

★**輸入 passphrase 的時機**：`bash deploy/decrypt-secrets.sh` 把 sops 提示行與解密輸出收進
同一條容器 pty 流，畫面上常看不到提示——看到腳本自己印的預告行後、**等容器起來再輸入**；
搶在容器接管 tty 之前打字＝該串字被 host shell 回顯成明文留在畫面與 scrollback（rev4:L-179）。
本管線零 gpg 前置（passphrase 由 sops 內嵌 age 直讀容器內 `/dev/tty`）——提示異常不要往
gpg-agent／pinentry 方向查。

### 15.2 加人四步（新成員／新機器）

**步驟 1【新成員做】產 identity**：`bash deploy/generate-age-key.sh`（產到預設
`~/.config/sops/age/keys.txt`、passphrase 加殼；覆蓋前有閘——**覆蓋＝永久銷毀既有私鑰、
其密文即刻不可解**）。
　★**註記：該機已有前代 identity 時（跨代並存機）＝保留舊鑰、另產第二把**。腳本有覆蓋閘會擋下
　（`FAIL：… 已存在——覆蓋＝永久銷毀該私鑰`），**絕不可繞過**：覆蓋掉前代私鑰＝該代密文從此
　不可解、不可逆。正解：
```bash
bash deploy/generate-age-key.sh keys-fork260509-rev5.txt
# 之後每次解密都要指定它——★給的是「容器內路徑」，不是你本機的路徑
SOPS_AGE_KEY_FILE=/root/.config/sops/age/keys-fork260509-rev5.txt bash deploy/decrypt-secrets.sh
```
　檔名取 **repo 目錄名**（`keys-fork260509-rev5.txt`）而非 `keys-rev5.txt` 這類短代號——跨代並存
　的機器上短代號家族必撞名，此即 `rev4:0084` 付過代價換來的命名紀律（同源＝`SECRETS_DIR`
　亦以 repo 目錄名為根）。放別處不行：wrapper 只唯讀掛載 `~/.config/sops/age` 這一個目錄。
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
  identity（同機多把時漏掛 `SOPS_AGE_KEY_FILE`，見步驟 1 註記）。

前一種是流程未完成、不是故障；`WARN … encrypted identity … didn't match file's recipients`
一行同樣只是這件事的複述。
**驗收（新成員側）**：`bash deploy/decrypt-secrets.sh` 寫出 10 支且零 `.new`，
`bash deploy/preflight-secrets.sh` rc=0。

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
   並確認它真的能解，再演練移除第一把——否則演練失敗就是永久失效。

### 15.4 值變更後回寫加密檔

**何時**：跑過 `bash deploy/generate-secrets.sh --force`、單支重生（刪檔重跑）、或人工編輯
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
　★值一律**裸量、不加引號**——decrypt 側 parser 取 `": "` 之後的字面全量，引號會被當成值的
　一部分寫進 `.txt`。★`< /dev/null` 讓 stdin 非 tty、wrapper 不掛 `-i -t`，從根上不生 CRLF 與
　提示併流。★輸入檔落 `tmp/`（gitignored）是**必要**的：wrapper 只掛載 `$PWD`，repo 外的檔
　容器讀不到。

**路徑 (b)｜只改一兩支且 `$SECRETS_DIR` 不全**：走 §15.7 三步往返。

**驗收**：`bash deploy/decrypt-secrets.sh` 後零 `.new` ＋ `bash deploy/preflight-secrets.sh` rc=0。

### 15.5 金鑰／passphrase 遺失與災難復原

私鑰檔與 passphrase **缺一即不可解**，故離線備份義務**含 passphrase 本身**。三種情境：

| 情境 | 處置 |
|---|---|
| 自己這把失效、**他人尚可解** | 走 §15.2 產新鑰重新加入；舊 identity 依 §15.3 撤銷 |
| 自己這把失效、**唯一 identity** | 密文永久不可解（無後門、設計如此）→ 下一列 |
| **全部 identity 皆失去** | `bash deploy/generate-secrets.sh --force` 重產全部亂數機密（dev 值本就是亂數、無歷史價值）→ 依 §15.4 回寫新密文 → `.sops.yaml` 換成新 recipient。★**人工真值必須在原始來源重新取得**（SMTP app password 回 Gmail 重簽、`alert_webhook_url` 回告警平台重取）——這些不是亂數，重產不回來 |

舊密文留在 git 史不必也無法移除——沒有任何 identity 能解它。

### 15.6 輪替表

| 對象 | 產法 | 觸發 |
|---|---|---|
| 9 支 leaf（postgres／redis／jwt／refresh／captcha／reaper／grafana／smtp／email_verify） | `bash deploy/generate-secrets.sh --force`（全部重產）或刪單支檔後重跑（單支重生） | 疑似外洩、成員撤銷（§15.3 準則 1）、prod 上線前 |
| 3 支 composite（`database_url`／`redis_url`／`reaper_database_url`） | `bash deploy/generate-secrets.sh --compose-only`（自 leaf 重組） | 對應 leaf 換過即須重組 |
| `alert_webhook_url` | 人工填真值（`--force` **不**重置；重置法＝刪檔重跑） | 起 obs 軌前（BACKLOG 滯後卷） |
| age identity | `bash deploy/generate-age-key.sh` | 成員異動、私鑰疑洩 |

★composite 三支**不在密文檔內**（密文＝9 leaf＋`alert_webhook_url`），故換 leaf 後除了 §15.4
回寫，還要跑 `--compose-only` 重組落點。
★**定期輪替節奏未拍板**，現行實務＝觸發式；prod 是否入 roadmap 定案時一併拍（BACKLOG 拍板待答項）。

### 15.7 手動呼叫 wrapper 的正規化三步

僅用於 §15.4 路徑 (b) 或需直接編輯密文時。**日常解密一律用 `bash deploy/decrypt-secrets.sh`**
（已內建全部正規化、名冊斷言與權限自證）。

**步驟 1｜解密（需 passphrase、走 tty）**——wrapper 在 stdin 有 tty 時掛 `-i -t`，容器 pty 會把
換行改 CRLF、且 passphrase 提示行與資料同流，**必須自行正規化**（與 decrypt-secrets.sh 的
`normalize_raw` 同形）：
```bash
cd <repo 根> && umask 077
WORK="$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/fork260509-rev5/edit.XXXXXX")"
./deploy/sops.sh -d deploy/secrets.dev.enc.yaml > "$WORK/raw.out"
tr '\r' '\n' < "$WORK/raw.out" | sed -E "s/$(printf '\033')\[[0-9;]*[A-Za-z]//g" > "$WORK/plain.yaml"
```

**步驟 2｜編輯**：改 `$WORK/plain.yaml`；值裸量、不加引號（同 §15.4）。

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
