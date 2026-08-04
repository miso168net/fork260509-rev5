# B5b 機密管線落地施工紀錄

> 落點＝`docs/brainstorms/`（HISTORICAL_EXEMPT 前綴、創世期史料）。日期＝2026-08-04。
> 依據＝啟動書 §4.5.11 v3（步驟 1 按 Q4 乙縮減）、`b5b-gate-decisions.md`。計畫＝`tmp/B5B-PLAN.md`。
> user 參與兩點（passphrase 不經手 Claude）：步 3 產鑰、步 6 round-trip——皆於 user 自己的終端完成。

## 一、八步逐步實得

| # | 步 | 實得 |
|---|---|---|
| 1 | 最小集搬運 | 21 檔＝六支腳本（§4.5.1 名冊 sha256 **逐支相符**）＋secrets 範本 **14 檔**（rev4 HEAD blob 逐位元覆核、枚舉自 ls-tree 防漏防多）＋dev-certs/.gitkeep；六支 index mode 100755；**Lint21 五紅全轉綠（紅軌跡 7→2）** |
| 2 | 平台移植 | (a) `AGE_ASSET` 改 `uname` 雙平台 case（Linux-x86_64／Darwin-arm64、其餘 fail-loud；darwin-arm64 資產名經 release API 實查存在）；(b) `stat` 12 處兩型——檔案資訊形 9 處改 `stat -c … \|\| stat -f` 雙平台回退（BSD token 實測定案：mode=%A／uid=%u／user=%Su／size=%z）、檔案系統形 3 處 `uname` 閘限 Linux（BSD `stat -f` 語意不同、不可直譯）；(c) CACHE／TMP_ROOT 落點 `fork260509-rev4`→`rev5`（兩代快取錯開）。macOS 側微測五值全對；`bash -n` 六支全過 |
| 3 | age 產鑰（user） | 首跑 `!` 形式取不到 `/dev/tty` → **FAIL 分支乾淨收場（殘檔已清、既有檔零動）**；user 於真終端重跑成功：darwin-arm64 下載＋digest 現查相符、passphrase 加殼＝True、明文私鑰形＝False、600/700（★該權限行即本次移植的雙平台 stat 實彈輸出）。公鑰＝`age1h86rpwqkfcqptwldqulg6wekvldzek0h44fvm5u6msexmdc3q5ts7mp46f`；**私鑰不在 repo**（porcelain 覆核） |
| 4 | .sops.yaml | recipient 一行換 rev5 新公鑰＋語境註解更新（P2.x 契約註解原樣）；★刻意不沿用 rev4 recipient——沿用＝rev4 私鑰能解 rev5 密文 |
| 5 | secrets＋preflight | `.env`（gitignored）寫 `SECRETS_DIR=/Users/testc1aw/.cache/fork260509-rev5/secrets`（展開後絕對路徑——§4.5.9 甲缺口處置）；generate-secrets 13 檔 GENERATED；**preflight rc=0**（alert_webhook_url 佔位 WARN＝設計、真值 B10 前人工填） |
| 6 | 密文產出＋round-trip | 10 leaf 組明文（tmp/、600、值形斷言、用畢即毀）→ wrapper `-e --filename-override` 加密 → `deploy/secrets.dev.enc.yaml` tracked（10 ENC 鍵集正確、recipient＝新公鑰、零 rev4 殘留）；**staged betterleaks rc=0**（sops 密文與掃描器相容實證）；user round-trip：10 支全 WRITTEN、**零 `.new`**（冪等路徑＝值形零漂移）、preflight 復驗 rc=0 |
| 7 | pre-push 可執行 | `bash -n` 過＋零 ref 乾跑 rc=0（B9 前無 remote、不實際 push） |
| 8 | 收工驗收 | 見三 |

## 二、★施工中親歷真 bug：macOS bash 3.2 全形字黏變數名（已入帳 L-001）

preflight 末行 `"$SECRETS_DIR；…"` 於 macOS bash 3.2 炸 `SECRETS_DIR�: unbound variable`——全形字首位元組被黏進變數名。**選擇性觸發**（同檔 L76 同形卻沒炸、繫於後接字元位元組值）；rev4 全代 WSL2 bash 5 從未暴露。照勘誤紀律（F03）機器枚舉全 repo bash 面：regex `(?<!\\)\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])`、排除註解與 `\$` 轉義——**6 檔 21 處一鍋 `${}` 包裹**（deploy 四支＋.githooks 兩處＋bootstrap 四處＋wf-watchdog 兩處；hooks 與 bootstrap 是 B6/B7 於 macOS 必跑的同族潛雷）。複掃殘餘僅 3 行註解（其一＝wf-watchdog 記載此坑的文件行、刻意不動）。修後 preflight rc=0。

## 三、收工判準（全數通過）

| 判準 | 實得 |
|---|---|
| DoD：私鑰不入 repo | ✓（git status 零機密新蹤） |
| DoD：recipient＝rev5 新公鑰 | ✓（密文 metadata 斷言＋零 `age1d9gu…` 殘留） |
| DoD：密文 tracked＋round-trip | ✓（100644 入 index；10 支 WRITTEN、零 .new） |
| DoD：preflight 全綠 | rc=0（含權限 700/644、CR 零命中、composite 一致） |
| DoD：範本 14 檔在 index | ✓ |
| Lint21 | 零紅；實 repo lint **7→2**（殘＝Lint20×2：ADR 空／events 空→B7 解） |
| 五支 self-test | 全 OK；docs-sync skipped **6→4**（AGE 釘版案＋EXEC_BIT_ROSTER 755 案隨 deploy 落地解除並轉綠——優於計畫預測的 5）、schema-gate=3 |
| `generate` | rc=0 |
| staged 掃描 | rc=0（1.77MB） |
| rev4 紀律 | porcelain 0、HEAD 仍 2b8a101 |
| index | 108→**130 檔**（deploy 22＋LESSONS 等） |

## 四、裁製雙雜湊留證（rev4 名冊值 → rev5 終態實算）

| 檔 | rev4（§4.5.1 名冊） | rev5 終態 | 裁製內容 |
|---|---|---|---|
| deploy/sops.sh | 590686b6…79add3 | **同值**（未裁製） | — |
| deploy/generate-age-key.sh | e0ea7558…05c025e | 29fc80c4…63c5bdc | 平台 case＋CACHE rev5＋註解＋stat×2 |
| deploy/decrypt-secrets.sh | 29c8b965…713062 | 7a68d72c…8977c2 | stat×4＋TMP_ROOT rev5＋fs 閘×2＋`${}`×7 |
| deploy/preflight-secrets.sh | c855c8d2…006c98 | f9c8ff35…8cfeea4 | stat×6＋fs 閘＋訊息 rev5/provenance＋`${}`×4 |
| deploy/generate-secrets.sh | d5659c6a…6caa815 | ca85b333…dc32651 | 檔頭 rev5＋provenance 形 |
| deploy/generate-dev-cert.sh | 920506b6…515856 | 1412d923…49d1a24 | CA CN rev5＋Linux 信任路徑 rev5 |
| .githooks/pre-commit | （B2 裁製版） | 1f5be0c6…268106 | `${}`×1 |
| .githooks/lib/scan-range.sh | （B2 原樣版） | 850666e1…45ad66 | `${}`×3 |
| tools/bootstrap.sh | （B3 裁製版） | 543424f1…aa700b | `${}`×4 |
| tools/wf-watchdog.sh | （B3 裁製版） | 2bb61531…4c5887 | `${}`×2 |

## 五、刻意不搬／留給後續

| 項 | 處置 |
|---|---|
| `setup-reaper-role.sh` | 隨 B10（非 roster、消費者＝reaper 維運） |
| `dev-webhook-sink.sh` | 永不搬（rev4 dev 收器已撤、rev5 另議）——啟動書明文 |
| nginx 三檔／observability／grafana 12 檔／Dockerfile.rust-api | 隨 B10 與 compose 同步（Q4 乙） |
| alert_webhook_url 真值 | B10 起 stack 前人工填＋§15 回寫密文 |
| bootstrap 完整體檢 | B6 只做三件、全體檢＝B8b |
