# fork260509-rev5 — rev5-admin 傘狀整合 workspace

admin 後台系統第五代重跑版：前端 fork 自 soybean-admin（Vue3＋naive-ui）、後端 Rust 從零重寫。
本 repo 是**傘狀整合層**——管文件、決策、spec 與編排；程式碼住兩個 submodule
（`base-web/`、`rust-api/`，本機以 git worktree 掛載）。

## 文件系統地圖（哪些檔案在哪裡）

```text
fork260509-rev5/
├── README.md                        本檔：人類入口導覽
├── CLAUDE.md                        操作規則書：工作流／git 手冊／文件紀律／硬禁令
├── .specify/memory/constitution.md  凍結權威：原則、wire 不變式、軌道授權、自查題組
├── specs/<NNN>-<feature-name>/      spec-kit per-feature 文件（收刀即凍結；首刀時出現）
├── docs/
│   ├── arc42/ARCHITECTURE.md        活書：系統現在長怎樣、只寫現在式（arc42 12 節）
│   ├── arc42/FORK-DELTA-WIRING.md   活書附屬文件：base-web ★ 軌道接線 as-built（§8 下放、ADR 0062；同受活書三閘）
│   ├── arc42/decisions/             ADR 一決策一檔：為什麼這樣做＋出處（accepted 後不可變）
│   ├── ops/NOTES.md                 當前意圖（唯一手寫進度敘事、幾行）
│   ├── ops/BACKLOG.md               待辦 B-NNN（完成即刪列、git 即史）
│   ├── ops/BACKLOG-DEFERRED.md      滯後卷：user 拍板暫不排程者（滯後≠完成、STATE 分計）
│   ├── ops/LESSONS.md               坑與防法索引（一行一坑＋防法 hook；動手前掃一遍）
│   ├── ops/LESSONS/                 L-NNN 一坑一檔（append-only；晉升必答欄 promoted_to）
│   ├── ops/RUNBOOK.md               dev stack 操作手冊：起停／輪替／備份／維運端點
│   ├── ops/events.jsonl             事件源：收刀／review／里程碑（機器讀；人讀 MILESTONES）
│   ├── brainstorms/                 各刀階段 0 產出（NNN- 前綴）與創世期史料（000＝啟動書、b2-～b7-＝創世證據）
│   ├── reviews/                     review 報告史料
│   └── generated/                   機器生成、嚴禁手改：STATE（現況帳）／MILESTONES（全事件表）
│                                      ／DECISIONS-INDEX（ADR 索引）／reference/（全量正典表）
├── tools/                           repo 治理面工具鏈（pre-commit／bootstrap 掛勾；管「版控品質」）
│   ├── bootstrap.sh                 新機重建／體檢（刻意 bash＝驗證器不與被驗證者共用底座）
│   ├── docs-sync.py                 文件系統中樞：lint 條款群／generate／errata／真表掃源
│   ├── schema-gate.py               schema 閘
│   ├── wire-schema.py               wire 契約閘
│   ├── entity-drift-gate.py         entity↔schema 快照漂移閘
│   ├── fork-delta-lint.py           base-web 原行紀律閘（fork-delta）
│   ├── secret-value-guard.py        機密值比對 pre-commit 防線（機密管線的治理端消費者）
│   ├── view-render-guard.py         管理頁零原始 HTML 插值守門（FR-038；pre-commit 條件觸發）
│   ├── route-artifact-gate.py       路由外掛產物四檔重算冪等閘（憲法 §III.2 第五列唯一機器守；
│   │                                需 dev stack、刻意不掛 pre-commit，單元邊界／CI 手動跑）
│   ├── seed-view-gate.py            seed sys_menu.component 之 view.* ⊆ 前端 view 集對賬閘（B-088／FR-049；pre-commit 條件觸發）
│   ├── rust-fmt-gate.py             rust 格式守門：容器內 cargo fmt --all --check 唯讀比對（B-112／ADR 0057；
│   │                                pre-commit 條件觸發、stack 未起＝具名跳過）
│   └── wf-watchdog.py               workflow 編排看門狗（stall／runaway 保險絲、可鎖定目標 run）
├── deploy/                          營運面：dev stack 部署資產＋機密管線（管「跑起來的系統」）
│   ├── secrets_common.py            落點解析共用庫（消費者五支＝下列四支 CLI＋secret-value-guard）
│   ├── preflight-secrets.py         機密上機前把關（缺檔／CR·LF／composite drift）
│   ├── decrypt-secrets.py           密文→落點明文（passphrase 自動應答＝ADR 0013）
│   ├── generate-secrets.py          十三機密缺則補（亂數走 docker openssl）
│   ├── setup-reaper-role.py         reaper role 設密（docker compose exec psql）
│   ├── sops.sh                      sops 官方容器 wrapper（digest 釘版、exec 薄殼）
│   ├── generate-age-key.sh          age 產鑰（容器化＝ADR 0011 ③類 latest）
│   ├── generate-dev-cert.sh         dev TLS 憑證（容器化 openssl）
│   ├── backup-db.py                 DB 備份／還原（pg_dump 走容器；不吃 secrets_common、落點 $HOME 防跨代撞名、RUNBOOK §6）
│   ├── Dockerfile.age、Dockerfile.rust-api    建置檔
│   ├── secrets.dev.enc.yaml         機密密文（sops age、tracked）
│   ├── secrets/                     明文落點說明（README＋.example；實值 gitignored）
│   ├── alloy/、grafana-provisioning/、nginx/、prometheus/、loki-config.yml
│   │                                  compose 掛載的服務／觀測層設定（動它＝動 runtime）
│   └── dev-certs/                   dev TLS 憑證落點（gitignored）
├── docker-compose*.yml              dev stack 三檔：base 層／dev override／example 參照實例
│                                      （dev stack 就位時出現；敘事見活書 §7）
├── fork260509-*/                    fork 源倉本機 clone（gitignored、必留、勿直接編輯）
└── base-web/、rust-api/             程式體 worktree（本機 worktree／外層 gitlink 雙身分）
```

**工具擺放原則**（承 B-035 落點拍板）：`tools/`＝repo 治理面、`deploy/`＝營運面——分界是
**服務對象、不是語言**（兩邊各有刻意保留的 bash，逐支理由＝ADR 0010 不做集）。命名慣例：
連字檔名＝CLI（不可 import）、底線檔名＝庫（可 import）。

## 這裡的文件系統怎麼運作（30 秒版）

- **三種材質**：人寫（規則與敘事）／事件源（`docs/ops/events.jsonl` 半自動 append）／機器生成（`docs/generated/`、嚴禁手改）。
- **時態分離**：活書只寫「現在」；未來住 ops/（NOTES、BACKLOG）；過去住 git 史＋events。
- **每個事實只有一個家**：找不到的東西不是沒記、是住在權威的那一份裡——鏡像要嘛機器生成、要嘛不存在。
- 以上規則由 pre-commit lint 強制（`tools/docs-sync.py`）；違規在 commit 當下被擋。

## 第一次來，照這個順序讀（約 30 分鐘）

1. [CLAUDE.md](CLAUDE.md) — 操作規則書：工作流、git/submodule 手冊、硬禁令
2. [docs/arc42/ARCHITECTURE.md 活書](docs/arc42/ARCHITECTURE.md) — 系統現在長怎樣（現在式 as-built、隨刀成長；空節＝對應子系統尚未建置）
3. [.specify/memory/constitution.md SpecKit-憲法](.specify/memory/constitution.md) — 凍結權威：不可違反的原則、wire 不變式、前端改動授權軌道

## 操作快速入口

首次啟動五步（每步陷阱與全部維運程序→[docs/ops/RUNBOOK.md](docs/ops/RUNBOOK.md)）：

1. `bash tools/bootstrap.sh`
2. `python3 deploy/generate-secrets.py`
3. `python3 deploy/preflight-secrets.py`
4. `bash deploy/generate-dev-cert.sh`（★非可選——缺憑證 up 即 front-nginx 死循環；自簽 ca.pem 記得 trust 進 OS）
5. `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait`

## 想知道 X，看 Y

| 想知道 | 去哪看 |
|---|---|
| 系統架構 | [docs/arc42/ARCHITECTURE.md 活書](docs/arc42/ARCHITECTURE.md)（目錄樹全景＝本檔上方地圖） |
| 什麼不能做（紅線） | [.specify/memory/constitution.md SpecKit-憲法](.specify/memory/constitution.md)＋CLAUDE.md「不要做的事」節 |
| 之前踩過什麼坑 | [docs/ops/LESSONS.md](docs/ops/LESSONS.md)（L-NNN 教訓索引，條目全文＝docs/ops/LESSONS/ 一坑一檔；前代候選＝啟動書 §5 K3） |
| 怎麼起環境／日常操作／輪替機密／備份 | [docs/ops/RUNBOOK.md](docs/ops/RUNBOOK.md)（dev stack 操作手冊） |
| 還有什麼沒做／候選 | [docs/ops/BACKLOG.md](docs/ops/BACKLOG.md)（B-NNN 待辦）＋[滯後卷](docs/ops/BACKLOG-DEFERRED.md)（拍板暫不排程；★滯後≠完成、查全帳須兩卷併看） |
| 現在進度到哪、submodule pins | [docs/generated/STATE.md](docs/generated/STATE.md)＋[docs/ops/NOTES.md](docs/ops/NOTES.md) |
| 歷史上發生過什麼 | [docs/generated/MILESTONES.md](docs/generated/MILESTONES.md)＋git log |
| 為什麼當初這樣決定 | [docs/generated/DECISIONS-INDEX.md](docs/generated/DECISIONS-INDEX.md) 找編號 → `docs/arc42/decisions/` 讀全文 |
| rev4 當初的設計結論與教訓 | [docs/brainstorms/000-doc-architecture.md](docs/brainstorms/000-doc-architecture.md) §5 知識匯出包（K1 設計結論／K2 設計域／K3 教訓候選） |
| 這套文件架構為什麼長這樣 | [docs/brainstorms/000-doc-architecture.md](docs/brainstorms/000-doc-architecture.md)（創世啟動書、史料） |
| 查埠／帳號／schema／畫面現況 | `docs/generated/reference/` 五張正典表（機器生成、嚴禁手改）：[ports](docs/generated/reference/ports.md)／[accounts](docs/generated/reference/accounts.md)／[schema](docs/generated/reference/schema.md)／[screens](docs/generated/reference/screens.md)／[tools-cli](docs/generated/reference/tools-cli.md) |

## 常見疑惑

- **不是用 arc42 嗎？為什麼待辦／教訓／風險不在 `docs/arc42/` 裡**：arc42 只取骨架概念、
  不照單全收——它只承載活書一檔（12 節對映）＋decisions/；活書的 §9（決策）與 §11
  （風險與技術債）是刻意的指路節，決策全文住 decisions/、風險與坑外掛 ops/
  （BACKLOG／LESSONS）、快變事實外掛 generated/reference/——防書內時態混寫腐爛。
- **`git submodule status` 行首有「-」**：worktree 模式的正常現象、不是壞掉；
  **絕不要跑 `git submodule update`**（會 reset worktree）。
- **想改 `docs/generated/` 裡的東西**：不要手改——改它的來源（events／ADR／BACKLOG…）
  再跑 `python3 tools/docs-sync.py generate`。
- **新機器初始化**：clone 本 repo 後跑 `bash tools/bootstrap.sh`（自動補齊 gitignored 源倉
  `fork260509-*`＋worktree＋hooks、斷言最原始源基線；詳 CLAUDE.md §3）。
  ★掃描防線就位前（＝bootstrap 驗證通過前）不落任何 commit——CLAUDE.md §6 硬禁令。
