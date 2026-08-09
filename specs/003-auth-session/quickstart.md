# Quickstart — 003-auth-session 驗證指南

端到端證明「真登入 → 角色化側邊欄 → 會話續期／撤銷 → 節流＋驗證碼 → 錯誤訊息顯人話」的可跑
場景；細節指涉 `contracts/*.md` 與 `data-model.md`、不重複。全程 dev stack；rust build/test
一律容器內、serial。★入口一律 `http://127.0.0.1:22080`（翻 `VITE_HTTP_PROXY=N` 後
22081 直連的 `/api` 必 404——vite dev server 已無 proxy）。

★**curl 與瀏覽器鎖同一 origin `http://127.0.0.1:22080`**——`localhost` 與 `127.0.0.1` 是不同
origin、localStorage token 不共享，混用時注入的 session 白做（rev4:L-100；2026-08-09 於 rev4
活體實證重現）。等價性已查證：front-nginx 的 `listen 80` 與 `listen 443 ssl` 兩個 server block
include 同一份 `_locations.inc`、無 301／HSTS，rust-api 零 `X-Forwarded-Proto` 讀取、零 cookie
⇒ 22080 與 22443 路由與行為等價；走 http 另免 CDP 驗收撞 dev 自簽憑證攔截頁。★但 `limit_req` 的
`auth_limit` 桶定義在 `nginx.conf` 的 `http{}` 層、鍵＝`$binary_remote_addr` ⇒ 兩入口**共用同一
桶**（5r/s、burst 40），換入口不會重置節流額度——§5 節流驗收連跑時尤須留意。

## 0. 前置

```bash
cd /mnt/d/AnewSpaces/x_Project/fork260509-rev5
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait

BASE=http://127.0.0.1:22080/api         # 經 front-nginx；http 入口＝無自簽憑證、免 -k
# ★.env 已翻：VITE_AUTH_ROUTE_MODE=dynamic／VITE_HTTP_PROXY=N；.env.test 與 .env.prod 的
#   VITE_SERVICE_BASE_URL 已由 apifox mock 改 /api（四行 ADAPT 標記見 research R2）
# ★三帳號密碼皆 123456（＝upstream demo 值、seed 三帳共用同一 argon2 PHC）

# single-session 驗收前置：把全站預設翻 on（seed 現值 off ⇒ 不翻則 login 第⑨步永不執行）
TOKEN_SUPER=$(curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -d '{"userName":"Super","password":"123456"}' | jq -r .data.token)
curl -s "$BASE/systemManage/updateSystemSetting" -H "authorization: Bearer $TOKEN_SUPER" \
  -H 'content-type: application/json' \
  -d '{"settingKey":"single_session_default","settingValue":"on"}' | jq .code
```

預期：`"0000"`。★**驗收全部做完後必須翻回 `off`**（見 §7）——否則 schema-gate gate2 seed 逐列
紅（`data-model.md` §9）。

## 1. 真登入與角色化側邊欄（US1）

```bash
for U in Super Admin User; do
  T=$(curl -s "$BASE/auth/login" -H 'content-type: application/json' \
      -d "{\"userName\":\"$U\",\"password\":\"123456\"}" | jq -r .data.token)
  echo "== $U"
  curl -s "$BASE/auth/getUserInfo" -H "authorization: Bearer $T" | jq '.data | {userId, userName, roles, buttonsN: (.buttons|length)}'
  curl -s "$BASE/route/getUserRoutes" -H "authorization: Bearer $T" | jq '{home: .data.home, topN: (.data.routes|length)}'
done
curl -s "$BASE/route/getConstantRoutes" | jq '{code, n: (.data|length)}'   # 未認證可取
```

預期：三帳號 `userId` 皆為**字串**、`userName` 為 nick_name（User → `User01`）、`roles` 各異、
`routes` 條數遞減（Super > Admin > User）、`home` 非空且為可導航葉頁；getConstantRoutes 回
`{"code":"0000", n:0}`（★seed `constant=TRUE` 為 0 列，前端須**合併**而非取代，否則登入頁與
403/404/500/iframe-page 五條 builtin 常量路由被清空）。

瀏覽器：`http://127.0.0.1:22080` 以三帳號分別登入（可用登入頁三顆快速登入鈕），側邊欄呈現
三種不同選單。★已知態：快速登入鈕暴露 dev seed 帳密，轉 prod 前必須拆除。

## 2. 會話續期與並發 rotation（US2）

```bash
R=$(curl -s "$BASE/auth/login" -H 'content-type: application/json' \
    -d '{"userName":"Super","password":"123456"}' | jq -r .data.refreshToken)
curl -s "$BASE/auth/refreshToken" -H 'content-type: application/json' \
  -d "{\"refreshToken\":\"$R\"}" | jq '{code, newPair: (.data.token != null)}'
# 同票二度換發（grace 30 秒窗內）→ 冪等回既發的同一對
curl -s "$BASE/auth/refreshToken" -H 'content-type: application/json' \
  -d "{\"refreshToken\":\"$R\"}" | jq '{code, token: .data.token}'
# 驗章失敗一律 8888（★絕不 3333——否則前端自動 refresh 死迴圈）
curl -s "$BASE/auth/refreshToken" -H 'content-type: application/json' \
  -d '{"refreshToken":"garbage"}' | jq '{code, msg}'
```

預期：第一發 `0000`＋新對；第二發 `0000` 且 `token` 與第一發**相同**（grace 冪等）；垃圾票
`{"code":"8888","msg":"auth.session.reLogin"}`。★grace 窗外（>30s）再送同一舊票 → `8888` 且
落一筆 `session_event(reuse)`、整條家族被撤（唯一觸發 reuse 的形）。

瀏覽器：登入後靜置至 access 過期（seed N=60 ⇒ access 300 秒），操作應無感續期、不被登出。

## 3. 撤銷矩陣（US3）

```bash
# 登出即撤：舊 access 立刻失效
L=$(curl -s "$BASE/auth/login" -H 'content-type: application/json' \
    -d '{"userName":"Admin","password":"123456"}')
A=$(jq -r .data.token <<<"$L"); RF=$(jq -r .data.refreshToken <<<"$L")
curl -s "$BASE/auth/logout" -H 'content-type: application/json' -d "{\"refreshToken\":\"$RF\"}" | jq .code
curl -s "$BASE/auth/getUserInfo" -H "authorization: Bearer $A" | jq '{code, msg}'
# logout 冪等：垃圾／已撤票一律 0000（回異碼＝提供 token 有效性 oracle）
curl -s "$BASE/auth/logout" -H 'content-type: application/json' -d '{"refreshToken":"garbage"}' | jq .code

# single-session 踢除（前置已翻 on）：同帳號二次登入 → 前一條下個請求得 7777
A1=$(curl -s "$BASE/auth/login" -H 'content-type: application/json' \
     -d '{"userName":"User","password":"123456"}' | jq -r .data.token)
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -d '{"userName":"User","password":"123456"}' >/dev/null
curl -s "$BASE/auth/getUserInfo" -H "authorization: Bearer $A1" | jq '{code, msg}'
```

預期：logout `0000`、舊 access 得 `8888`、垃圾票 logout 仍 `0000`；被踢者得
`{"code":"7777","msg":"auth.session.kicked"}`（瀏覽器顯示 modal、且內容為人話非裸鍵）。

## 4. 節流三區與圖形驗證碼（US4）

```bash
# 三區的序數語意（★precheck 讀「當下」窗計數、record_attempt 在 authenticate 之後才推進）：
#   第 1 次請求 count=0 → 1000（結束後 count=1）／第 2 次 count=1 → 1000（結束後 count=2）
#   第 3 次起 count=2 ≥ captcha_after(2) → 2222 captchaRequired，且★該路徑零稽核列零計數桶
#   ⇒ count 永久卡在 2、**locked 在這條路上構造性不可達**（rev4 有專測釘住此性質）
for i in 1 2 3 4; do
  curl -s "$BASE/auth/login" -H 'content-type: application/json' \
    -d '{"userName":"Admin","password":"wrong"}' | jq -c "{n:$i, code, msg}"
done
# 發題：對任意 userName 一律發（含不存在帳號＝零存在性洩漏）
curl -s "$BASE/auth/loginCaptcha?userName=Admin" | jq '{code, hasImg: (.data.captchaImg|startswith("data:image/png;base64,"))}'
curl -s "$BASE/auth/loginCaptcha?userName=ghost-no-such-user" | jq .code
# userName 超限 → 與登入端點同形的 1000 閘
curl -s "$BASE/auth/loginCaptcha?userName=$(printf 'x%.0s' {1..200})" | jq .code
# 鎖定區：直接造窗（★最短路徑；in-band 路徑須人工解題 3 次推進 count 2→5，見下方瀏覽器段）
#   ★三個必填欄：success／attempted_user_name／real_ip(INET)；可用不存在帳號名（節流判定鍵＝
#   送出原文、鎖定判定在 authenticate 之前）。★此 INSERT 推進 sys_login_attempt_id_seq，§7 收尾涵蓋
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres \
  psql -U postgres -d rev5_admin -c "
    INSERT INTO sys_login_attempt (success, attempted_user_name, real_ip, created_at)
    SELECT false, 'lockprobe', '127.0.0.1', now() - interval '30 seconds'
    FROM generate_series(1,5);"
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -d '{"userName":"lockprobe","password":"wrong"}' | jq -c '{code, msg}'
```

預期：第 1、2 次 `1000`（`auth.login.failed`）；第 3、4 次 `2222 biz.auth.captchaRequired`；
發題兩次皆 `0000` 且 `captchaImg` 為 data URI；超限 `1000`；造窗後單發 → `2222 biz.auth.locked`。
瀏覽器：軟區出現 220×120 驗證碼欄；答對但密碼錯 → 該次落列使 count 推進（2→3→4→5）並自動換新題
（★同一張題提交即消耗、答錯即失效）；解題三次後第六發即 `locked`。答錯驗證碼**不**推進鎖定計數。

## 5. 替代登入 stub 與 i18n 人話（US5）

```bash
for P in sendCaptcha codeLogin register resetPwd; do
  printf '%-12s ' "$P"
  curl -s "$BASE/auth/$P" -H 'content-type: application/json' -d '{}' | jq -c '{code, msg}'
done
# 動詞不符（B-047）：已註冊路徑遇未註冊動詞 → 4040＋HTTP 404
curl -s -o /dev/null -w '%{http_code} ' "$BASE/auth/getUserInfo" -X POST
curl -s "$BASE/auth/getUserInfo" -X POST | jq -c '{code, msg}'
```

預期：四支皆 `{"code":"2222","msg":"biz.auth.notSupported"}`；動詞不符回 `404` ＋
`{"code":"4040","msg":"system.notFound"}`（★未認證亦同碼同 status＝零路徑存在性洩漏）。
瀏覽器：三張表單送出顯示「該功能尚未開放」人話（非假成功 toast）；切換語系（zh-CN／en-US）
同一後端 key 顯示對應語言譯文。

## 6. 測試與機器閘（US 全；DoD）

```bash
# ★rust build/test 一律容器內、全程 serial；--test-threads=1 為必帶（否則 integration 搶同列 DB）
# ★redis：dev 與測試共用 DB 0 ⇒ 測試鍵一律 uniq 前綴（時戳＋pid），否則會踢掉開發者自己的 session
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api \
  cargo test --workspace -- --test-threads=1
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api \
  cargo build --release            # dev_identity 汰換後 release 首次可跑

docker compose -f docker-compose.yml -f docker-compose.dev.yml exec base-web pnpm typecheck
python3 tools/fork-delta-lint.py           # ★含新增的「軌道名 ∈ 授權名冊」斷言
python3 tools/docs-sync.py generate && python3 tools/docs-sync.py check
python3 tools/schema-gate.py check         # ★三閘；gate2 seed 對 runtime 寫入敏感（見 §7）
grep -c '^| ' docs/generated/reference/backend-msg-dict.md    # 預期 23（表頭 1＋22 鍵）
grep -c '^| ' docs/generated/reference/routes.md              # 預期 17（表頭 1＋16 條）
```

預期：cargo test 全綠（含 contract 16 case 雙向覆蓋閘、動詞探測閘、denylist TTL 兩 reason 皆
refresh_secs、reuse 僅 rotated+grace miss、3333／7777→HTTP 200、refresh 驗章失敗→8888、觀測面
三序列顯式 0）；`pnpm typecheck` 綠；fork-delta-lint 綠且名冊斷言非 vacuous（抽掉任一合法軌道
名即紅指名）；docs-sync check 一致（`gen.msg_dict` 豁免已拔、空表安全）；schema-gate 三閘綠。

## 7. 收尾（★必做，否則 gate2 永久紅）

```bash
# ★一次 psql 批次做完三件事（★步驟①**不可走 API**——updateSystemSetting 必寫 updated_by＝操作者
#   uid 與 updated_at＝now，而凍結 seed 該列兩欄皆為 NULL ⇒ 走 API 還原值仍留痕跡、gate2 逐列紅）
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres \
  psql -U postgres -d rev5_admin -c "
    -- ① single_session_default 還原為 seed 值，並把審計兩欄歸 NULL
    UPDATE system_settings SET setting_value='off', updated_at=NULL, updated_by=NULL
      WHERE setting_key='single_session_default';
    -- ② 清 runtime 寫入並重設三支 sequence（★刪列救不回 setval——gate2 原位比對 setval）
    TRUNCATE sys_token, session_event, sys_login_attempt;
    SELECT setval('sys_token_id_seq', 1, false),
           setval('session_event_id_seq', 1, false),
           setval('sys_login_attempt_id_seq', 1, false);
    -- ③ 還原 sys_user 的 session 欄（session_id 由 login 第⑨步寫入）
    UPDATE sys_user SET session_id = NULL WHERE session_id IS NOT NULL;"
# ④ 清 §4 造窗殘留的 L1 lock 鍵（redis；鍵名 throttle:lock:user:{name}）
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec redis \
  sh -c 'redis-cli -a "$(cat /run/secrets/redis_password)" --no-auth-warning DEL throttle:lock:user:lockprobe throttle:lock:user:Admin'
python3 tools/schema-gate.py check
```

預期：schema-gate gate2 seed 逐列綠（★含 `system_settings` 該列的 `updated_at`／`updated_by`
兩欄為 NULL）。★此節即 `data-model.md` §9 的操作面；本刀是 rev5 第一支會推進 sequence 的刀
（002 的還原守衛只 `UPDATE system_settings`、無 sequence 面）。★次序：本節須在 §6 的
`schema-gate.py check` **之前**執行，或 §6 的該項改為「於本節收尾後補跑」。
