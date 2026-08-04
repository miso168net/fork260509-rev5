# B10 compose 移植＋九條錯開施工紀錄

> 落點＝`docs/brainstorms/`（創世期史料）。日期＝2026-08-04。依據＝§4.2 B10（Q3/Q4 裁定縮限＝純移植工程步）＋§4.5.9 錯開表。
> schema 壓平不在本步（→波 0 基線刀）；refresh 首跑隨刀（Q3 甲）。

## 一、搬運（23 檔、rev4 HEAD 唯讀、機器化）

compose 三檔＋Dockerfile.rust-api＋setup-reaper-role.sh（名冊 sha256 相符、755）＋nginx 三檔＋alloy／loki／prometheus 設定＋grafana-provisioning **12 檔**（★扣治外飛地 `backend-msg-dict.json`——機器生成物、gen.msg_dict 豁免解除後由 generate 重產）。無名冊 hash 者以 rev4 HEAD blob 為源直落（git show、零手抄）。

## 二、九條錯開（全機器化替換、逐檔計數）

| 條 | 實得 |
|---|---|
| project name | `rev4-admin`→`rev5-admin`×42（含 example project／container_name／映像 tag 三 service／alloy 標籤／grafana dashboards 六 json） |
| host port | 12 埠＋留號段全換 5xxxx（42079→52079…49091→59091；逐值精確替換、計數見證據） |
| DB 三處 | `soybean_admin_rust`→`…_rev5`×7、`soybean`→`soybean_rev5`×6（含 POSTGRES_DB／healthcheck pg_isready／postgres_exporter DATA_SOURCE_URI；★樣式 `\bsoybean\b(?!-)(?!js)` 防誤傷 soybean-admin／soybeanjs）；**schema-gate 雙記帳側 B3 已改 rev5 值、本步核對即可（免同刀）** |
| network | `rev4_net`→`rev5_net`×17 |
| grafana alerting 識別名 | 首輪殘留掃描抓 6 處 `rev4-webhook`／`rev4-obs`（三檔互引組）→補輪同刀齊改、複掃零殘留（唯三命中＝generate-secrets.sh 檔頭 provenance 註解、B5b 合法形） |
| SECRETS_DIR | 已就位（B5b `.env`）、compose 回退值原樣 |
| example 源倉路徑 | 相對路徑同名、rev5 根下同名源倉就位＝自然指對 |
| 不錯開 | 容器內側 port（官方預設值＝設計）、映像版本 pin |

## 三、驗收

| 判準 | 實得 |
|---|---|
| config 解析 | `docker compose -f …yml -f …dev.yml config` 過：七 services；published 全 5xxxx；POSTGRES_DB／USER＝rev5 值；卷全帶 `rev5-admin_` 前綴 |
| postgres/redis 實起 | `up -d --wait`→**雙 healthy**（healthcheck 用 rev5 帳號名＝DB 三處改對的實證）；55432／56379 loopback 實聽；`down` 乾淨（`rev5-admin_rev5_net` Removed） |
| gen.compose 豁免 | **到期即紅第三例**→兩表拔項→`generate` 重算 6 檔、**ports 真表首算 19 行**；豁免表餘 3 筆（gen.msg_dict／gen.router／gen.snapshots）＋lint24.day1 |
| 全鏈 | test OK（skipped=3）；lint 0 錯誤／0 警告／6 跳過（＝4 豁免類＋Lint16×2 未 staged 正常態）；rev4 零改動 |

## 四、刻意留給後續

alert_webhook_url 真值人工填＋§15 回寫密文（起 obs 軌前）；六業務件全起＝後端首刀後；observability 三軌 profiles 實測＝觀測刀；gen.snapshots＋entity-drift Day-1 跳過解除＝波 0 schema 基線刀。
