---
id: "0027"
title: dev 驗收入口統一為 http://127.0.0.1:22080——curl 與瀏覽器全程鎖同一 origin
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "user 拍板 2026-08-09（003-auth-session 開工前、CDP 驅動能力接通當日）；承襲 rev4:L-100（啟動書 §5 K3-100「CDP token 注入鎖同 origin」）；落地面＝errata 枚舉紀律（CLAUDE.md §4 勘誤）"
tags: [acceptance, cdp, nginx, origin, dev-stack]
---

## 背景

驗收入口的寫法自 brainstorm 逐層下傳至 spec／plan／quickstart，字面一路是「唯一入口
`https://localhost:22443`」。但同一份 quickstart 的 curl 用的是
`BASE=https://127.0.0.1:22443/api`。

**兩者不是同一個 origin。** `localhost` 與 `127.0.0.1` 在瀏覽器眼中是不同 origin、
localStorage 不共享。這正是 rev4:L-100（啟動書 §5 承襲條目 K3-100）記下的坑：CDP 走
login-form 自動化很 flaky，且 origin 混用時「curl 取 token → 注入 localStorage」這條標準
路徑會靜默白做。rev4 給的防法是「全程鎖同一 origin」——而 rev5 文件在逐層下傳的過程中把
「鎖同一 origin」這半句丟了，只留下兩個不同 origin 的字面共存於同一份驗收程序。

003-auth-session 正是 auth 刀，驗收全程繞著 token 與 session 打轉，是最會被這個坑咬的一刀；
在此之前沒有任何一刀的驗收面同時涉及 curl 憑證與瀏覽器 session，故潛伏至今未現形。

2026-08-09 CDP 驅動能力接通（Edge 151 @ `127.0.0.1:9229`）後於 rev4 活體實證重現：同一
app、同一埠 42080，`http://localhost:42080` 的 `SOY_*` 只有主題鍵且停在 `/login`；
`http://127.0.0.1:42080` 有 `SOY_token`／`SOY_refreshToken` 且已在 `/home`。

## 決定

1. **dev 驗收入口統一為 `http://127.0.0.1:22080`**——curl 的 BASE 與瀏覽器網址列共用同一
   字面，不再一邊 `127.0.0.1`、一邊 `localhost`。
2. **origin 鎖定升為紀律、非偏好**：同一輪驗收內，curl 取得的憑證與瀏覽器注入或觀察的
   session 必須同 origin（scheme＋host＋port 三者全等）；混用即判該輪結果無效、重跑。
3. **走 http 而非 https**：dev 自簽憑證在 CDP 自動化下會產生攔截頁，屬純粹的驗收摩擦，
   而非被驗證的性質。
4. **22443 不廢除、埠拓樸零變更**：front-nginx 仍同時 listen 80／443，ADR 0004 的埠配號
   不受影響。本 ADR 規範的是「驗收該走哪個入口」，不是埠的存廢。
5. **理由的家＝驗收程序檔本身**：origin 規則、等價性證據與節流桶共用三項寫入
   `specs/003-auth-session/quickstart.md` 檔頭；本 ADR 只承載決策。理由不得只存在於
   per-machine memory——別台機器與別的 session 讀不到，該改動下一輪即被當成無謂變更還原。

## 後果

- **等價性已逐條查證，非便宜行事**：`deploy/nginx/conf.d/dev.conf` 的 `listen 80` 與
  `listen 443 ssl` 兩個 server block **include 同一份 `_locations.inc`**、無 301 亦無
  HSTS ⇒ `/`→base-web、`/api/`→rust-api（剝前綴）、四個 auth 專用限流塊、`X-Real-IP`
  與 `X-Forwarded-For` 注入全部等價；rust-api 零 `X-Forwarded-Proto` 讀取、零 cookie
  （Bearer 走 localStorage）⇒ scheme 差異對後端行為中性。
- **★節流桶跨入口共用**：`limit_req_zone` 定義在 `nginx.conf` 的 `http{}` 層、鍵＝
  `$binary_remote_addr` ⇒ 22080 與 22443 共用同一個 `auth_limit` 桶（5r/s、burst 40）。
  換入口不會重置節流額度——003 的節流驗收段連跑時尤須留意，否則會得到難以歸因的結果。
- **落地面**：errata 全 repo 枚舉 14 處、逐處處置——改 9 處（003 的 quickstart 三處／
  plan／spec 兩處／brainstorm 兩處，002-system-settings 的 quickstart 一處）；不改 5 處
  （compose 埠映射與其註解、ADR 0004 埠配號史料、機器生成的 ports 真表、RUNBOOK 真相源
  政策句）。連帶 32 個 `curl -sk`／`-ks` 改回 `curl -s`——http 下 `-k` 無意義，且 BASE 行
  原註解「-k 收 dev 自簽」會反過來誤導讀者以為仍在 https。
- **射程僅限 dev stack 驗收**：prod 拓樸有真憑證與 CF 前置，https 仍是唯一對外形，本 ADR
  不觸及。
- 日後若確有 https 專屬行為要驗（HSTS、Secure cookie 屬性、混合內容），22443 仍在，
  屆時整輪鎖 `https://127.0.0.1:22443`（dev 憑證 SAN 含 `IP:127.0.0.1`，此形有效）
  ——仍受決定 2 約束，不得與 http 入口混用。
- 本 ADR 未新增任何機器閘：origin 混用目前無機器可判（curl 與瀏覽器分屬不同工具面）。
  若日後驗收腳本化，該斷言應寫進腳本而非依賴人工紀律。
