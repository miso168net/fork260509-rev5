# Quickstart — 004-ip-trust-anchor 驗證指南

端到端證明「真實來源還原 → IP 存取閘 → 規則管理頁 → 來源維節流 → 管理員解鎖」的可跑場景；
細節指涉 `contracts/*.md` 與 `data-model.md`、不重複。全程 dev stack；rust build／test 一律
容器內、serial。★入口一律 `http://127.0.0.1:22080`（`localhost` 與 `127.0.0.1` 是不同 origin、
token 不共享；且兩入口共用同一個基建層限流桶——換入口不會重置額度）。

★★**本刀的核心驗收前提：構造轉發標頭**。dev 掛的最小信任模型只把容器網段列為受信轉發層
（`contracts/trust-model-config.md`），因此：

- **不帶**構造標頭的瀏覽器流量 → 鏈上兩跳皆受信 → 整鏈受信回退 → `real_ip` ＝反向代理位址、
  信心 `fallback`、**全站共用同一個來源計數桶**（極易誤觸鎖定）。
- **帶** `X-Forwarded-For: 203.0.113.x` → 解出該公網位址、信心 `proxy_clean` ⇒ 阻擋、
  計數隔離、防自鎖三者才**打得出來**。
- ★模擬位址必須落在**結構性豁免六段之外**（勿用 10/8、172.16/12、192.168/16、127/8）——
  豁免段恆放行、deny 規則對其永遠無效（判定序③先於⑤）。
- dev 經反向代理**可達二態**＝`fallback`／`proxy_clean`；其餘五態屬整合測試射程
  （逐態對照表＝`research.md` R7）。

## 0. 前置

```bash
cd /mnt/d/AnewSpaces/x_Project/fork260509-rev5
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait

BASE=http://127.0.0.1:22080/api
SIM_A='203.0.113.11'      # 模擬公網來源 A（TEST-NET-3、非豁免段）
SIM_B='203.0.113.22'      # 模擬公網來源 B

# 信任模型設定檔已隨 compose 掛載——先確認它真的生效（否則以下全部走不到）
docker compose logs rust-api 2>&1 | grep -i "trust" | tail -3
```

**預期**：見到信任模型載入成功的記錄，且**沒有**「設定缺席／解析失敗」類告警。
★若見告警＝設定沒掛上，後續 §2～§5 會全部得到 `fallback`、驗不出東西。

```bash
TOKEN=$(curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -d '{"userName":"Super","password":"123456"}' | jq -r .data.token)
AUTH="authorization: Bearer $TOKEN"
```

## 1. 真實來源還原（US1／SC-013 ④）

```bash
# 不帶構造標頭：預期 fallback、real_ip＝反向代理位址
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -d '{"userName":"Super","password":"wrong"}' > /dev/null

# 帶構造標頭：預期 proxy_clean、real_ip＝SIM_A
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_A" \
  -d '{"userName":"Super","password":"wrong"}' > /dev/null
```

查稽核列（psql 進 rev5 庫；★絕不指向對照環境的庫）：

```bash
# ★psql 一律走**容器內環境變數**形，且**本行是本檔 psql 形的單一定義點**——§1 收尾／
#   §1b／§5／§7 皆沿用 `$PG`（新開 shell 需重跑這一行）。
#   裸 `psql -c` 在 host 上必失敗：rev5 的庫在 compose 的 postgres 容器內，host 沒有 PG
#   server（實得 `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432"
#   failed`）；即使連得上，寫死 `-U postgres -d rev5_admin` 也會
#   `FATAL: role "root" does not exist`（LESSONS L-015 實暴）。真值＝compose 的
#   POSTGRES_USER／POSTGRES_DB，故一律由容器內的環境變數展開。
PG='docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres'

$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT real_ip, peer_ip, ip_confidence, attempted_user_name
  FROM sys_login_attempt ORDER BY created_at DESC LIMIT 2"'
```

**預期**：兩列的 `ip_confidence` 分別為 `proxy_clean`（帶標頭那筆、`real_ip`＝`203.0.113.11`）
與 `fallback`（不帶那筆）；**兩列的 `peer_ip` 皆有值**（此前恆 NULL）。

### ★§1 收尾（必做，**不可留到 §7**）

```bash
# 走查留下的登入嘗試列會毒化**下一次** `cargo test --workspace`（`$PG` 定義見上一塊）：
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "DELETE FROM sys_login_attempt WHERE attempted_user_name IN ('"'"'Super'"'"','"'"'Admin'"'"','"'"'User'"'"')" \
  -c "SELECT setval('"'"'sys_login_attempt_id_seq'"'"', 1, false)" \
  -c "SELECT count(*) AS remaining FROM sys_login_attempt"'
```

**預期**：`remaining` 為 0。

★**為什麼這一步不能省、也不能延到 §7**（2026-08-15 U-F 走查實暴，見 `docs/ops/LESSONS.md`
的 L-031）：`sys_login_attempt` 確實在 schema 閘的 runtime-append 收窄集內，所以留列**不會**
讓 `schema-gate check` 轉紅——但那只豁免了 **seed 內容比對**這一個面。真正被毒到的是**測試
套件**：測試起手掛的 `test_db::SequenceResetGuard` 在 Drop 時執行
`setval('sys_login_attempt_id_seq', 1, false)`（★這是 gate2 逐列 diff 凍結 seed 第 446 行
`setval('public.sys_login_attempt_id_seq', 1, false)` 所**要求**的，不能改成 `max(id)`），
於是走查留下的 committed 列一旦佔住 `id=1`，下一支 insert 就撞
`duplicate key value violates unique constraint "sys_login_attempt_pkey"`——
`handler::auth::login::integration_tests` **五支當場紅**。

★**最惡劣的是證據自毀**：同一次測試執行裡的 `handler::auth::user_info` 掛了
`LoginAttemptCleanup::new(&["Super","Admin","User"])`，而 `user_info` 在字典序上排在 `login`
之後 ⇒ 它會把走查列清掉。所以**重跑第二次就全綠**，看起來像 flaky test。若把「跑全量」排在
走查之前，更是連紅都看不到。

## 1b. 轉發鏈超長即拒絕（ADR 0043／憲法 F7／F8；★2026-08-15 追加、屬 U-M）

★編號取 `1b` **刻意不重排 §2～§7**：那些節號被碼註逐處引用（`handler/route.rs`、
`captcha/mod.rs`、`refresh.rs` …），重排即讓那批引用整批失準。

```bash
# ★`$PG` 與 §1 同一顆（此處重列一份讓本節可獨立起跑、不假設任何 shell alias；理由與
#   L-015 逐字記載見 §1）。以下命令皆為**實跑過**的形。
PG='docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres'

# 造一條 36 跳的鏈：35 跳洪泛（198.18.0.1~35）＋真實來源 SIM_A。
# ★nginx 以 $proxy_add_x_forwarded_for 在**最右**再附加它觀察到的對端 ⇒ 後端收到 37 跳
#   ＞ MAX_XFF_TOKENS（32），判定窗＝最右 32 跳（自 198.18.0.6 起）。
CHAIN=$(python3 -c "print(', '.join([f'198.18.0.{i}' for i in range(1,36)]+['$SIM_A']))")

curl -s -o /dev/null -w 'HTTP=%{http_code}\n' "$BASE/auth/login" \
  -H 'content-type: application/json' -H "X-Forwarded-For: $CHAIN" \
  -d '{"userName":"Super","password":"wrong"}'
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $CHAIN" \
  -d '{"userName":"Super","password":"wrong"}' | jq -c '{code, msg, data}'
```

**預期**：`{"code":"5003","msg":"system.forbidden","data":null}` ＋ **HTTP 403**
（★復用既有 `PermissionDenied`：零新碼、零新 msg key）。

```bash
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -x -c "
  SELECT ip_confidence, real_ip::text AS real_ip, peer_ip::text AS peer_ip,
         left(x_forwarded_for, 40) AS xff_head, right(x_forwarded_for, 40) AS xff_tail,
         (x_forwarded_for LIKE '"'"'%203.0.113.11%'"'"')  AS contains_real_ip,
         (x_forwarded_for LIKE '"'"'%198.18.0.1,%'"'"')   AS contains_overflowed_hop
  FROM sys_login_attempt ORDER BY id DESC LIMIT 1"'
```

**預期**（2026-08-15 實跑值）：

| 欄 | 值 | 這一格在守什麼 |
|---|---|---|
| `ip_confidence` | `chain_rejected` | 第八態落欄（FR-007）；帳號維計數即以此字面逐字排除該列 |
| `real_ip` | `203.0.113.11/32` | ★拒絕態下**恆有位址**——來源維計數要數這些列（FR-050），無位址即無從歸戶。★**出處視判定腿而定**：本例走層③故取自判定窗，層①直連腿／④回退腿／通道覆蓋層則取自傳輸層對端或訪客標頭（逐腿列舉見 `trust::Confidence::ChainRejected` doc） |
| `peer_ip` | 反向代理容器位址（如 `172.23.0.7/32`） | 鑑識三欄齊活 |
| `xff_head` | 自 `198.18.0.6` 起 | ★溢出窗外的左端 5 跳**不在欄裡**＝轉錄真的取了判定窗 |
| `contains_real_ip` | `t` | ★**F8 的走查面**：兩軌取同一組欄，故本例 `real_ip` 可由該欄複驗。★**本例成立不等於恆成立**——F8 v1.5.1 明列兩個條件：(a) `real_ip` 由鏈推導 (b) 窗未逾字元上限；本例兩者皆滿足（最右 32 跳皆短 v4 字面、窗長遠低於上限）。一般化條件見 FR-046 |
| `contains_overflowed_hop` | `f` | 同上的反面：轉錄若走原文，`198.18.0.1,` 會出現 |

★**本節的 `LIKE` 判別只在 v4 短字面下可靠**：鏈欄**逐字保留**原文，而 `real_ip` 是正規化後的壓縮小寫形 ⇒ 鏈裡若寫 `2001:0DB8:0000:…:0009`，`real_ip` 落 `2001:db8::9`，字串包含式比對得 `f`（**假陰性**）。走查造 v4 鏈故不受影響；★但**不得**把這個 `LIKE` 形搬進正式稽核報表或機器閘（已落 BACKLOG）——F8 講的「複驗」是**以同一份取窗＋正規化重推**，不是字串包含。

★**拒絕不是降級**（FR-049）：`ip_domain_degraded_total` **不得**因本節而動——該序列是掛
告警規則的，把「防護正常生效」計進去等於讓它在被攻擊時噴假警報。

```bash
curl -s http://127.0.0.1:22079/metrics | grep ip_domain_degraded_total
```

**預期**：本節前後該序列的值**不變**（僅 boot 期既有值）。

### ★§1b 收尾（必做，**不可留到 §7**）

```bash
# 本節與上面的 curl 都會落 committed 的 sys_login_attempt 列 ⇒ 毒化**下一次** cargo test
# （SequenceResetGuard 會 setval 回 1，留列佔住 id=1 即讓 login integration 撞主鍵）。
# 成因與「證據自毀」性質見 §1 收尾與 LESSONS L-031。
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "DELETE FROM sys_login_attempt WHERE attempted_user_name IN ('"'"'Super'"'"','"'"'Admin'"'"','"'"'User'"'"')" \
  -c "SELECT setval('"'"'sys_login_attempt_id_seq'"'"', 1, false)" \
  -c "SELECT count(*) AS remaining FROM sys_login_attempt"'
```

**預期**：`remaining` 為 0。★清完**才**跑全量（`cargo test --workspace -- --test-threads=1`）
——次序反了拿到的綠是走查**前**的快照（L-031 第③點）。

## 2. IP 存取閘（US2／SC-013 ②）

```bash
# 對 SIM_B 建阻擋規則
curl -s "$BASE/systemManage/addIpRule" -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"wbipCidr\":\"$SIM_B/32\",\"wbipType\":\"deny\",\"wbipMemo\":\"quickstart 驗收\"}" | jq .code

# 以 SIM_B 身分請求 → 預期被擋
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/auth/loginCaptcha?userName=Super" \
  -H "X-Forwarded-For: $SIM_B"

# 以 SIM_A 身分請求 → 預期不受影響
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/auth/loginCaptcha?userName=Super" \
  -H "X-Forwarded-For: $SIM_A"
```

**預期**：新增回 `"0000"`；SIM_B 得 **403**（信封碼 `5003`）；SIM_A 得 200。
★**未重啟服務**即生效＝門鈴熱重載成立（SC-004）。

```bash
# 白優先於黑：對同一位址再加放行規則
curl -s "$BASE/systemManage/addIpRule" -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"wbipCidr\":\"$SIM_B/32\",\"wbipType\":\"allow\"}" | jq .code
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/auth/loginCaptcha?userName=Super" \
  -H "X-Forwarded-For: $SIM_B"
```

**預期**：`"0000"` 後該位址改得 **200**（放行優先、與建立先後無關）。

```bash
# 結構豁免段不可被擋：對私網段建 deny，自身請求仍通
curl -s "$BASE/systemManage/addIpRule" -H "$AUTH" -H 'content-type: application/json' \
  -d '{"wbipCidr":"192.168.0.0/16","wbipType":"deny"}' | jq .code
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/auth/loginCaptcha?userName=Super" \
  -H "X-Forwarded-For: 192.168.1.5"
```

**預期**：`"0000"`（寫得進去）但請求仍得 **200**——豁免段恆放行。

## 3. 防自鎖（US3 場景 5／SC-005／SC-013 ③）

```bash
# ★關鍵：操作者本身帶 SIM_A 身分，再對含 SIM_A 的範圍建 deny
curl -s "$BASE/systemManage/addIpRule" -H "$AUTH" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_A" \
  -d '{"wbipCidr":"203.0.113.0/24","wbipType":"deny"}' | jq '.code, .msg'
```

**預期**：`"2222"` ＋ `"biz.ipRule.selfLock"`，且**零寫入**（下條查詢列數不變）：

```sql
SELECT count(*) FROM sys_ip_rule WHERE wbip_cidr = '203.0.113.0/24';   -- 預期 0
```

★不帶構造標頭做同一操作**不會**觸發自鎖（操作者來源落豁免段、判定回放行）——這是設計語意
而非缺陷（data-model §3 同源約束）。

## 4. 來源維節流（US4／SC-013 ①）

```bash
# 先清掉 §2 建立的規則，避免 allow 短路干擾計數
# （規則 id 由列表取；deleted/restore 語意見 contracts/wire-ip-rule.md）
curl -s "$BASE/systemManage/getIpRuleList?deleted=active" -H "$AUTH" | jq '.data.records[] | {id, wbipCidr, wbipType}'

# ★門檻取自 seed（data-model §1.4）——先讀出來，下面的發數才對得上；seed 若被調過就照
#   讀到的值換算（軟門檻＝N ⇒ 第 ① 步發 N−1 次、第 ③ 步的第二發即轉 2222）。
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT setting_key, setting_value FROM system_settings
  WHERE setting_key IN ('"'"'ip_captcha_after'"'"','"'"'ip_max_fails'"'"','"'"'ip_window_minutes'"'"')
  ORDER BY 1"'
```

**預期**：`ip_captcha_after=10`／`ip_max_fails=50`／`ip_window_minutes=15`（以下發數按此換算）。

```bash
# ① SIM_A 連續失敗 9 發（＝軟門檻 10 減一，仍在自由區）
#    ★帳號名每發都不同 ⇒ 帳號維構造上不可能觸發，之後看到的 2222 只能出自來源維
for i in $(seq 1 9); do
  curl -s "$BASE/auth/login" -H 'content-type: application/json' \
    -H "X-Forwarded-For: $SIM_A" \
    -d "{\"userName\":\"ghost$i\",\"password\":\"x\"}" | jq -r .msg
done
```

**預期**（2026-08-16 U-J 實跑值）：9 發全數 `auth.login.failed`。

```bash
# ② ★負向自證前半：此刻仍在自由區 ⇒ 成功登入免題
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_A" \
  -d '{"userName":"Super","password":"123456"}' | jq -r .code
```

**預期**：`"0000"`。

★★**這一發的位置不可調換到軟門檻之後**（2026-08-16 U-J 走查實暴、本節據此改寫）：軟區是
對**該來源的每一發**都要求驗證碼，帳密再正確也一樣（實跑得 `2222`／`biz.auth.captchaRequired`），
而 shell 走查解不了圖形題 ⇒ 原本「先打滿 12 發、再期望成功登入回 `0000`」的寫法**做不到**。
負向自證的成功登入因此必須落在自由區內，鑑別力改由第 ③ 步承載。

```bash
# ③ ★負向自證後半：成功登入 MUST NOT 重置來源計數
#    ——②之後若計數歸零，這三發會全部停在 auth.login.failed
for i in 10 11 12; do
  curl -s "$BASE/auth/login" -H 'content-type: application/json' \
    -H "X-Forwarded-For: $SIM_A" \
    -d "{\"userName\":\"ghost$i\",\"password\":\"x\"}" | jq -r .msg
done
```

**預期**（2026-08-16 U-J 實跑值）：`ghost10` 仍 `auth.login.failed`（它是第 10 次失敗——
★成功登入沒有把前 9 次抹掉），`ghost11`／`ghost12` 轉 **`biz.auth.captchaRequired`**。
——三發全數 `auth.login.failed`＝「成功即重置」被誤加進來源維（該形是可繞過整套來源維防護的
破口：攻擊者只需在同一來源穿插一次自有帳號的成功登入即可清零計數；計數下界必須恰兩源）。
★msg 鍵是 **`biz.auth.captchaRequired`**（rev5 的 Biz 構造點鍵走 `biz.<domain>.<case>`）
——本節原記 rev4 的 `auth.login.captchaRequired`，2026-08-16 實跑更正。

```bash
# ④ SIM_B 同時測 → 預期完全不受 SIM_A 的計數影響（計數隔離）
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_B" \
  -d '{"userName":"ghost99","password":"x"}' | jq -r .msg
```

**預期**：`auth.login.failed`（不是 captchaRequired）。

```bash
# 順帶自證位址還原真的走了 §1 那條路（否則本節擋的可能是別的桶）：
# ★`success` MUST 進 GROUP BY（2026-08-16 U-J 走查覆核追加）：本節要守的判別面是「**失敗列**
#   不增加」，而第 ② 步的成功登入自己也落一列稽核（login 第⑩步的寫入點 (c) 無條件落列）
#   ——混算成功列會讓總數被一個與本節無關的維度推移，鑑別力當場鈍化。
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT host(real_ip) AS real_ip, ip_confidence, success, count(*)
  FROM sys_login_attempt GROUP BY 1,2,3 ORDER BY 1,3"'
```

**預期**（2026-08-16 U-J 走查覆核實跑值）：三列——
`203.0.113.11｜proxy_clean｜f｜10`、`203.0.113.11｜proxy_clean｜t｜1`、
`203.0.113.22｜proxy_clean｜f｜1`。

★判別面＝**SIM_A 的失敗列恰 10**（＝軟區那兩發拒絕**零稽核列零計數桶**）；失敗列變 12
＝拒絕分支開始落列，攻擊者對著軟區反覆敲門即可把來源推進硬鎖。
★SIM_A 的**總**列數是 **11**＝9（①九發失敗）＋1（②成功登入自己那一列）＋1（③ghost10 失敗）
——2026-08-16 覆核前本節誤記為 10（漏算 ② 的成功列），依那個數字走查會把正常結果（11）
讀成「多出 1 列＝拒絕分支落列」的**假警報**、而真回歸值其實是 13。這正是本查詢要拆
`success` 的理由：拆開之後兩邊各自對得上、不必再靠總數心算。

### ★§4 收尾（必做，**不可留到 §7**）

```bash
# ★謂詞是 TRUNCATE、**不是** §1 收尾那條 `IN ('Super','Admin','User')`（2026-08-16 U-I
#   品質審查實查、U-J 走查覆核）：本節用的是 **ghost 帳號**，而 `login::record_attempt`
#   逐字寫入送入的帳號名 ⇒ 那批列完全不在該謂詞射程內，留列同樣佔住 id=1 並毒化下一次
#   `cargo test`（成因＝L-031）。
# ★第二句 `sys_token` 亦不可省：第 ② 步是**成功**登入，login 第⑧步無條件落一列 committed
#   憑證，而 `SequenceResetGuard` 的名冊含 `sys_token_id_seq` ⇒ 留列即撞 `sys_token_pkey`。
# ★判別面＝兩個 `remaining` 皆為 0，**不是**「三閘綠」——兩表都在 schema 閘的
#   runtime-append 收窄集內，留列時 `schema-gate check` 恆四項全綠。
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "TRUNCATE sys_login_attempt RESTART IDENTITY" \
  -c "SELECT count(*) AS login_attempt_remaining FROM sys_login_attempt" \
  -c "TRUNCATE sys_token RESTART IDENTITY" \
  -c "SELECT count(*) AS token_remaining FROM sys_token"'
```

**預期**：兩個 `remaining` 皆為 0。★清完**才**跑全量（次序反了拿到的綠是走查**前**的快照）。

## 5. 管理員解鎖（US5）

```bash
# 把 SIM_A 推到硬門檻後解鎖
curl -s "$BASE/systemManage/unlockLogin" -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"dimension\":\"ip\",\"target\":\"$SIM_A\"}" | jq .code

curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_A" \
  -d '{"userName":"ghost200","password":"x"}' | jq -r .msg
```

**預期**：解鎖回 `"0000"`；隨後該來源回到自由區（`auth.login.failed`）。

```bash
# 畸形參數 → 零稽核零狀態（`$PG` 定義見 §1；新開 shell 需重跑那一行）
COUNT_SQL='psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT count(*) FROM sys_operation_log"'
BEFORE=$($PG sh -lc "$COUNT_SQL")
curl -s "$BASE/systemManage/unlockLogin" -H "$AUTH" -H 'content-type: application/json' \
  -d '{"dimension":"nonsense"}' | jq '.code, .msg'
$PG sh -lc "$COUNT_SQL"   # 預期與 $BEFORE 相同
```

**預期**：`"2222"` ＋ `biz.throttle.invalidUnlockTarget`，稽核列數**不變**。

★**本節同樣會寫 `sys_login_attempt`，收尾請比照 §4 收尾那一塊**（★**不是** §1 收尾那條
`IN ('Super','Admin','User')`：本節用的是 ghost 帳號〔`ghost200`〕、不在該謂詞射程內；
成因與 §4 收尾同一條，2026-08-16 U-J 走查一併更正）。

## 6. 管理頁走查（US3／SC-009）

以 CDP 接 `127.0.0.1:9229`，開分頁對照 **22080（rev5）** vs **42080（rev4 同頁）**：

1. 以 Super 登入 → 側邊欄出現「IP 規則管理」→ 點擊**正常載入**（此前為「找不到資源」）
2. 列表顯示規則（含備註欄）→ 以網段片段搜尋、切類型與刪除狀態篩選
3. 新增：填 `203.0.113.7/24` → 送出後列表顯示 **`203.0.113.0/24`**（主機位元已正規化）
4. 重複新增同組合 → 顯示衝突提示（非伺服器錯誤）
5. 編輯 → 軟刪 → 切到回收桶 → 復原
6. 備註欄填 `<b>x</b>` → 列表顯示**字面** `<b>x</b>`（未被當標記執行）

★三方比對可再開 42089（原版基線）；驗收帳號 Super／Admin／User。

★**本節步驟 1 的成功登入會落一列 committed `sys_token`**——收尾見 §7 第 3b 步。★別指望三閘
會提醒你：該表在收窄集內、留列恆綠，漏清是毒化**下一次** `cargo test`（成因與實測鏈見 §7
末「為什麼第 3b 步不能省」）。

### ★§6 機器守：路由產物四檔重算冪等閘（T042②／憲法 §III.2 第五列）

管理頁進場會讓路由外掛重算 `src/router/elegant/{imports,routes,transform}.ts` 與
`src/typings/elegant-router.d.ts`。這四支**同時被 fork-delta 檢查全域豁免**（檔頭帶
`Generated by …` 者豁免手標）⇒ 本閘是它們**唯一**的機器守，不跑就等於這四支一行守門都沒有。

```bash
# ★這是本閘的**排程落點**：單元邊界（與 CI）手動跑，**刻意不掛 pre-commit**——本閘要在容器內
#   實跑 vite 外掛三趟、實測十餘秒，而 pre-commit 的全鏈預算是秒級（20s 警戒／45s 硬擋）；
#   且本閘依賴 dev stack 在跑，pre-commit 則 MUST 在 stack 沒起時照樣可用。完整論證見
#   tools/route-artifact-gate.py 檔頭「落點：為何**不**掛 pre-commit」一節。
# 何時必跑（三個觸發事實，皆屬單元邊界事件、不是每次 commit 都發生）：
#   ①新增／搬移／刪除 base-web/src/views 底下的 view 檔
#   ②動路由外掛設定（base-web/build/plugins/router.ts）
#   ③產物四檔本身出現在 diff 裡
python3 tools/route-artifact-gate.py check
```

**預期**：`[route-artifact-gate] ✓ 產出檔集 4 支對賬憲法第五列與產物檔頭；重算冪等（種＝版控）
與零手改（種＝基線）兩道皆 byte 相等（self-test 過）`。

★報紅的三種讀法：①產出檔集對不上＝憲法第五列漏列一支（該支從此完全無守）或版控多／少掛了
產物檔頭；②重算不冪等＝新增 view 後忘了讓外掛重算、或重算結果沒 commit（症狀會是「側邊欄
少一項」「頁面 404」，而第一嫌疑犯永遠是別的東西）；③零手改斷言紅＝有人直接編輯產物檔。
★rc=2＝環境前提不成立（dev stack 沒起／基線源倉缺席），與 rc=1 的「檢查判定為紅」分流。

## 7. 收尾（★必做）

```bash
# 0) `$PG` 定義見 §1（新開 shell 需重跑那一行；★裸 `psql -c` 在 host 上必失敗）
# 1) 清掉走查建立的 IP 規則列——sys_ip_rule 是變體 A 業務表、
#    ★刻意不納入 schema 閘的 runtime-append 收窄集，留列會使 gate2 逐列比對紅
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "TRUNCATE sys_ip_rule RESTART IDENTITY"'

# 1b) ★★**不可省的下一步：TRUNCATE 不會按門鈴**（下方「為什麼」有實測鏈）。
#     門鈴 payload 不帶語意、收訊端只認頻道 ⇒ 手動 PUBLISH 一次即可讓判定面重讀空表。
#     ★頻道名的單一權威＝`rust-api/server/src/ipgate/mod.rs` 的 IPGATE_INVALIDATE_CHANNEL；
#       密碼一律以容器內 `/run/secrets/redis_password` 展開（同 compose healthcheck 既有形，
#       絕不把值打進命令列），理由同 §1 的 psql 環境變數形（L-015）。
RD='docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T redis'
$RD sh -lc 'redis-cli -a "$(cat /run/secrets/redis_password)" --no-auth-warning \
  PUBLISH ipgate:invalidate 1'

# 1c) 驗判定面真的跟上了（兩個模擬來源皆須回 200）——這一步是 1b 的收據，不是裝飾：
#     PUBLISH 回 `1`（訂閱者數）只證明「有人在聽」，不證明重讀成功。
#     ★`$BASE`／`$SIM_A`／`$SIM_B` 定義見 §0（新開 shell 需重跑那一塊）。
#     ★這兩發走 loginCaptcha、不落 sys_login_attempt；即使落了也會被下方第 3 步清掉
#       （故本步刻意排在第 3 步之前）。
curl -s -o /dev/null -w 'SIM_A=%{http_code}\n' "$BASE/auth/loginCaptcha?userName=Super" \
  -H "X-Forwarded-For: $SIM_A"
curl -s -o /dev/null -w 'SIM_B=%{http_code}\n' "$BASE/auth/loginCaptcha?userName=Super" \
  -H "X-Forwarded-For: $SIM_B"

# 2) 操作稽核表已納入收窄集（本刀常數加一行）⇒ schema 閘面免清理
#    ★但「在收窄集內」只豁免 seed 內容比對，**不等於留列無害**——見下一步
# 3) ★登入嘗試列：收窄集豁免不了測試套件（SequenceResetGuard 會 setval 回 1，
#    留列佔住 id=1 即讓 login integration 五支撞主鍵）。各節走查後就該清，
#    此處為兜底；理由見 §1 收尾與 LESSONS L-031
#    ★**兜底這一句用 TRUNCATE、不用 §1 收尾那條 `IN (...)`**（2026-08-16 U-J 走查更正）：
#      §4／§5 用的是 ghost 帳號，`login::record_attempt` 逐字寫入送入的帳號名 ⇒ 那批列
#      不在 `IN ('Super','Admin','User')` 的射程內，兜底若沿用該謂詞就兜不到。
#      凍結 seed 對本表期望 0 列，TRUNCATE 嚴格涵蓋且免去「下次又多一種帳號名」的維護面。
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "TRUNCATE sys_login_attempt RESTART IDENTITY" \
  -c "SELECT count(*) AS remaining FROM sys_login_attempt"'

# 3b) ★★會話憑證列：**成功登入必落一列 committed `sys_token`**（login 第⑧步無條件 insert）
#     ——與第 3 步同一形、不同載體，下方「為什麼」有實測鏈。
#     ★**三閘抓不到這一列**：`sys_token` 在 schema 閘的 runtime-append 收窄集**內**
#       （gate2 剝其 COPY 資料列、不逐列 diff）⇒ 留列不會讓 `schema-gate check` 轉紅。
#       但 `SequenceResetGuard` 的名冊 `AUTH_SEQUENCES`（`rust-api/server/src/model/mod.rs`）
#       **含** `sys_token_id_seq` ⇒ 留列佔住 id=1 即讓下一次 cargo test 撞 `sys_token_pkey`。
#       ★「在收窄集內」只豁免 seed 內容比對，**不等於留列無害**——與第 3 步同一個誤讀點。
#     ★一律 TRUNCATE、不做針對性 DELETE：來源不只 §6 步驟 1——§0 取 `$TOKEN` 那發、§4 負向
#       自證那發成功登入各再落一列，且凍結 seed 對本表期望 0 列。
$PG sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "TRUNCATE sys_token RESTART IDENTITY" \
  -c "SELECT count(*) AS remaining FROM sys_token"'

# 3c) ★成功登入的其餘兩處寫入**不需要**清（實測：兩發成功登入後 `session_event` 恆 0 列、
#     `sys_user.session_id` 恆全 NULL）——兩者都掛在 login 第⑨步的 single-session 踢除腿上，
#     而凍結 seed 是 `session_policy=inherit`＋`single_session_default=off` ⇒ 該腿不觸發。
#     ★這是**設定相依**的豁免、不是恆真：若走查前置把 `single_session_default` 翻 `on`
#       （003 quickstart 正是那樣做），本步就要補回這兩句——`sys_user` **不在**收窄集內，
#       殘值會讓 gate2 逐列 diff 直接紅：
#       `UPDATE sys_user SET session_id = NULL WHERE session_id IS NOT NULL`

# 4) 三閘
python3 tools/docs-sync.py check && python3 tools/schema-gate.py check
```

**預期**：`SIM_A=200`／`SIM_B=200`（第 1c 步）；第 3 步與第 3b 步的 `remaining` **皆為 0**；
三閘全綠。★若 gate2 對 `sys_ip_rule` 報紅＝第 1 步沒做；若對 `sys_operation_log` 報紅＝
收窄集那一行常數沒加（spec FR-042）。★**三閘全綠 ≠ 清乾淨了**：第 3 步與第 3b 步的兩表都在
收窄集內、閘對它們的殘留恆綠，唯一的判別面是那兩個 `remaining`。

### ★為什麼第 1b 步不能省（2026-08-16 U-I 走查覆核實暴）

`TRUNCATE` 走的是 **SQL 直寫**，繞過了 IP 規則的四個寫端端點——而「重載判定面＋按門鈴」
（`contracts/wire-ip-rule.md` §2 第 5 步）**只掛在那些端點上**（`handler::ip_rule::reload_after_write`
→ `ipgate::reload_and_publish`）。所以第 1 步跑完是這個狀態：**資料庫歸零、記憶體判定面
原封不動**。實測鏈：

| 步驟 | 觀測 |
|---|---|
| 以 API 建 `203.0.113.0/24` deny（＝§6 步驟 3 填 `203.0.113.7/24` 正規化後的同一條） | `SIM_A` 得 **403** |
| `TRUNCATE sys_ip_rule RESTART IDENTITY` → `SELECT count(*)` | **0 列** |
| 同一刻再打一次 | `SIM_A` **仍得 403**（表已空、閘照擋） |
| `PUBLISH ipgate:invalidate` | 記錄出現 `IP 規則集已重讀換版…allow_rules=0, deny_rules=0` → `SIM_A` 回 **200** |

★**漏掉 1b 的實害不在本節、在下一節**：§6 步驟 3 所建的規則正好涵蓋 `SIM_A`，於是 §4／§5
會在 `SIM_A` 上恆得**假 403**，而下一次 §7 的清列又會把現場抹掉 ⇒ 外觀像 flaky（L-031 講的
正是這個形；差別只在那次的載體是 `sys_login_attempt`、這次是記憶體判定面）。

★替代形（等價、擇一即可）：`docker compose … restart rust-api`——重啟後的啟動初載會讀空表。
慢且會中斷其他驗證，故預設用門鈴；只有在通知層本身壞掉（第 1c 步仍 403）時才用它。

### ★為什麼第 3b 步不能省（2026-08-16 U-I 走查覆核實暴）

`sys_token` 是走查全程唯一「**有寫入、卻零處置**」的表（本檔在本刀之前對它零次提及）：
§6 步驟 1 逐字要求「以 Super 登入」，而 login 第⑧步**無條件** `sys_token::insert`
（`handler/auth/login.rs`）⇒ 照著跑一定留列。寫入點恰三處：§0 取 `$TOKEN`、§4 負向自證那發、
§6 步驟 1（§1／§1b 走密碼錯誤路徑、§2／§3 復用既有 token，皆不落列）。
實測鏈（皆於容器內、`--test-threads=1`）：

| 步驟 | 觀測 |
|---|---|
| 以 Super 登入（＝§6 步驟 1） | `sys_token` 恰 **1 列**、`id=1`、`status=active`、`created_by=1` |
| 只跑既有的第 3 步（清 `sys_login_attempt`）→ `cargo test --lib` | **rc=101、399 passed／2 failed**：`t019_login_success_returns_pair_token_row_and_one_audit_row` 與 `t019_login_starts_last_activity_clock_best_effort` 皆得 `{"code":"5000","msg":"system.internal"}` |
| 改跑本步（`TRUNCATE sys_token RESTART IDENTITY`）→ 同一指令 | **rc=0、401 passed／0 failed** |

★**成因**：`SequenceResetGuard` 在**每支測試** Drop 時對 `sys_token_id_seq` 執行
`setval(seq, 1, false)` ⇒ 一次執行裡**第二支以後**寫 `sys_token` 的測試取到 `id=1`，與走查
留下的 committed 列撞 `sys_token_pkey`。insert 的 Err 被第⑧步的 `internal("login 寫 sys_token")`
收成信封 `5000` ⇒ **斷言訊息只看得到 `5000`／`system.internal`，完全不指向主鍵、更不指向走查**。

★**證據自毀（與 L-031、L-036 同形）**：同一次執行裡的
`t069_chain_rejection_precedes_password_hashing_with_no_success_side_effect` 掛了
`purge_success_side_effects_of_user(&db, 1)`＝**無條件** `DELETE FROM sys_token WHERE
created_by = 1`，而走查以 Super（uid=1）登入的列正好落在該範圍、`t069` 又排在 `t019` 之後
⇒ 紅跑結束時 `sys_token` 已回 0 列（實測），**重跑第二次必全綠**。若把「跑全量」排在走查
之前更是連紅都看不到——外觀完全就是 flaky test。

★**為何第 3 步的既有條文接不住它**：那一步的載體是 `sys_login_attempt`、謂詞是
`attempted_user_name IN ('Super','Admin','User')`，與 `sys_token` 零交集；而 §1 收尾／§1b 收尾
兩處的「清乾淨才跑全量」也同樣只點名 `sys_login_attempt` ⇒ 本表在本檔原先**零處置**。
