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

（本章隨 schema 刀補實文；創世期無內容。）

## 11. 觀測層維運

（本章隨觀測層刀補實文；創世期無內容。）

## 12. 工具鏈速查（★python 工具一律直跑或 `python3` 前綴、bash 前綴＝假失敗 rev4:L-129/L-143）

| 命令 | 作用 | 需運行中 stack |
|---|---|---|
| `python3 tools/docs-sync.py generate` | 重算 docs/generated/ 全部（跑完必 git add） | 否 |
| `python3 tools/docs-sync.py check` / `lint` | pre-commit 兩道（staged 過期／Lint03~Lint24） | 否 |
| `python3 tools/docs-sync.py refresh` | 自實庫撈 schema/accounts 快照 | **是** |
| `python3 tools/docs-sync.py errata <詞>` / `test` | 全 repo 同語意枚舉／自測 | 否 |
| `python3 tools/schema-gate.py gate1|gate2|audit` | 零漂移／定稿落實／審計欄矩陣（不進 pre-commit、手動跑） | **是** |
| `python3 tools/schema-gate.py test` | 自測 | 否 |
| `python3 tools/wire-schema.py extract` / `check` / `test` | 容器內抽 typings→wire-schema.json 快照／快照 drift 比對（`--staged-gate`＝pre-commit 收窄形）／自測 | extract **是**、check 未起→警告放行 |
| `python3 tools/fork-delta-lint.py` | base-web 原行紀律（前置：fork 源倉在 example 分支） | 否 |
| `python3 tools/secret-value-guard.py check --full-tree` | 機密現值 × 全 tracked 檔一次性盤點：staged 增量對既存明文結構性失明（rev4:L-190）、本旗標補盤點面——導入既有 repo 與定期體檢用；命中只印「檔:行｜機密名」絕不印值、有命中 exit 1。★不進 pre-commit（全樹非增量；增量面＝pre-commit 自動跑裸 check） | 否 |
| `python3 tools/entity-drift-gate.py check` / `test` | entity（rust-api/entity/src）vs schema 快照漂移比對（欄序歸 gate2、index/constraint 歸 gate1、default 不驗）／自測 | 否 |
| `bash tools/bootstrap.sh` | 新機重建／舊機體檢 | 否 |
| `./deploy/sops.sh <sops 參數>` | sops 官方容器 wrapper（digest 釘版、自 repo 根跑；營運程序＝§15） | 否（需 docker） |
| `bash deploy/decrypt-secrets.sh` | 加密檔 → `$SECRETS_DIR` 寫出明文機密檔 | 否（需 docker＋互動 tty） |
| `bash deploy/generate-age-key.sh [檔名]` | 產 age 金鑰（覆蓋閘＋先寫 `.new` 再 `mv`＋產物自檢＋自動取 age 並驗 digest）。省略檔名＝預設 `keys.txt`；同機第二把給非預設名 | 否（需真 tty；age 缺席時需網路） |

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
  `docs/generated/reference/accounts.md`。本檔命令帶字面埠（52080/52443/52079/53000/53100/
  55432/56379/59090/59091）純為可複製執行；動埠的刀照 errata 紀律
  （`python3 tools/docs-sync.py errata <埠>`）機器枚舉全 repo 同步、含本檔。

## 15. SOPS 機密營運（密文入版控 × age 私鑰）

資產三件：`deploy/secrets.dev.enc.yaml`（密文、**tracked**）／`.sops.yaml`（recipient
公鑰清單、tracked）／`~/.config/sops/age/keys.txt`（**私鑰＝passphrase 加殼**、目錄 700
檔 600、**永不進版控**）。工具兩支＝`./deploy/sops.sh`（官方容器 wrapper、digest 釘版）與
`bash deploy/decrypt-secrets.sh`（把密文寫成 `$SECRETS_DIR` 的明文檔）。★所有命令一律
**自 repo 根**執行——wrapper 只掛載 `$PWD`，換目錄跑就找不到 `.sops.yaml`。

兩條不可省紀律：
1. **私鑰與其 passphrase 永不進版控、永不離開持鑰機**；私鑰檔遺失或 passphrase 遺失＝該
   identity 永久失效，處置＝以尚可解密的機器走加人流程重新加密。交付只交公鑰（`age1…` 開頭、非機密）。
2. **改值後回寫加密檔**：機密輪替先改密文面（`./deploy/sops.sh` 編輯 enc 檔）再解密落地，
   或落地後立即回寫 enc——密文檔是唯一真相，明文 `$SECRETS_DIR` 只是投影。

★**輸入 passphrase 的時機**：`bash deploy/decrypt-secrets.sh` 把 sops 提示行與解密輸出收進
同一條容器 pty 流，畫面上常看不到提示——看到腳本自己印的預告行後、**等容器起來再輸入**；
搶在容器接管 tty 之前打字＝該串字被 host shell 回顯成明文留在畫面與 scrollback（rev4:L-179）。
本管線零 gpg 前置（passphrase 由 sops 內嵌 age 直讀容器內 `/dev/tty`）——提示異常不要往
gpg-agent／pinentry 方向查。

加人四步、輪替表、災難復原全文：隨機密管線（啟動書 B5b）落地後補全本章。
