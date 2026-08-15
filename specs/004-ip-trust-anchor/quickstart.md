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

```sql
SELECT real_ip, peer_ip, ip_confidence, attempted_user_name
FROM sys_login_attempt ORDER BY created_at DESC LIMIT 2;
```

**預期**：兩列的 `ip_confidence` 分別為 `proxy_clean`（帶標頭那筆、`real_ip`＝`203.0.113.11`）
與 `fallback`（不帶那筆）；**兩列的 `peer_ip` 皆有值**（此前恆 NULL）。

### ★§1 收尾（必做，**不可留到 §7**）

```bash
# 走查留下的登入嘗試列會毒化**下一次** `cargo test --workspace`：
psql -c "DELETE FROM sys_login_attempt WHERE attempted_user_name IN ('Super','Admin','User')"
psql -c "SELECT setval('sys_login_attempt_id_seq', 1, false)"
```

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

# SIM_A 連續失敗至軟門檻 → 預期要求驗證碼（帳號名每次不同，證明是「來源維」在擋）
for i in $(seq 1 12); do
  curl -s "$BASE/auth/login" -H 'content-type: application/json' \
    -H "X-Forwarded-For: $SIM_A" \
    -d "{\"userName\":\"ghost$i\",\"password\":\"x\"}" | jq -r .msg
done
```

**預期**：前段回 `auth.login.failed`，達軟門檻後轉 `auth.login.captchaRequired`
——★**帳號名每次都不同**，帳號維不可能觸發，只能是來源維。

```bash
# SIM_B 同時測 → 預期完全不受 SIM_A 的計數影響（計數隔離）
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_B" \
  -d '{"userName":"ghost99","password":"x"}' | jq -r .msg
```

**預期**：`auth.login.failed`（不是 captchaRequired）。

```bash
# ★負向自證（SC-006）：穿插一次成功登入，來源計數 MUST NOT 重置
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_A" \
  -d '{"userName":"Super","password":"123456"}' | jq -r .code
curl -s "$BASE/auth/login" -H 'content-type: application/json' \
  -H "X-Forwarded-For: $SIM_A" \
  -d '{"userName":"ghost100","password":"x"}' | jq -r .msg
```

**預期**：成功登入回 `"0000"`，但下一發**仍是** `auth.login.captchaRequired`
——若變回 `auth.login.failed`＝「成功即重置」被誤加進來源維（該形是可繞過整套來源維防護的
破口，計數下界必須恰兩源）。

★**本節同樣會寫 `sys_login_attempt`，收尾請比照 §1 收尾那兩行清理**（理由同 §1）。

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
# 畸形參數 → 零稽核零狀態
BEFORE=$(psql -tAc "SELECT count(*) FROM sys_operation_log")
curl -s "$BASE/systemManage/unlockLogin" -H "$AUTH" -H 'content-type: application/json' \
  -d '{"dimension":"nonsense"}' | jq '.code, .msg'
psql -tAc "SELECT count(*) FROM sys_operation_log"   # 預期與 $BEFORE 相同
```

**預期**：`"2222"` ＋ `biz.throttle.invalidUnlockTarget`，稽核列數**不變**。

★**本節同樣會寫 `sys_login_attempt`，收尾請比照 §1 收尾那兩行清理**（理由同 §1）。

## 6. 管理頁走查（US3／SC-009）

以 CDP 接 `127.0.0.1:9229`，開分頁對照 **22080（rev5）** vs **42080（rev4 同頁）**：

1. 以 Super 登入 → 側邊欄出現「IP 規則管理」→ 點擊**正常載入**（此前為「找不到資源」）
2. 列表顯示規則（含備註欄）→ 以網段片段搜尋、切類型與刪除狀態篩選
3. 新增：填 `203.0.113.7/24` → 送出後列表顯示 **`203.0.113.0/24`**（主機位元已正規化）
4. 重複新增同組合 → 顯示衝突提示（非伺服器錯誤）
5. 編輯 → 軟刪 → 切到回收桶 → 復原
6. 備註欄填 `<b>x</b>` → 列表顯示**字面** `<b>x</b>`（未被當標記執行）

★三方比對可再開 42089（原版基線）；驗收帳號 Super／Admin／User。

## 7. 收尾（★必做）

```bash
# 1) 清掉走查建立的 IP 規則列——sys_ip_rule 是變體 A 業務表、
#    ★刻意不納入 schema 閘的 runtime-append 收窄集，留列會使 gate2 逐列比對紅
psql -c "TRUNCATE sys_ip_rule RESTART IDENTITY"

# 2) 操作稽核表已納入收窄集（本刀常數加一行）⇒ schema 閘面免清理
#    ★但「在收窄集內」只豁免 seed 內容比對，**不等於留列無害**——見下一步
# 3) ★登入嘗試列：收窄集豁免不了測試套件（SequenceResetGuard 會 setval 回 1，
#    留列佔住 id=1 即讓 login integration 五支撞主鍵）。各節走查後就該清，
#    此處為兜底；理由見 §1 收尾與 LESSONS L-031
psql -c "DELETE FROM sys_login_attempt WHERE attempted_user_name IN ('Super','Admin','User')"
psql -c "SELECT setval('sys_login_attempt_id_seq', 1, false)"

# 4) 三閘
python3 tools/docs-sync.py check && python3 tools/schema-gate.py check
```

**預期**：三閘全綠。★若 gate2 對 `sys_ip_rule` 報紅＝第 1 步沒做；若對 `sys_operation_log`
報紅＝收窄集那一行常數沒加（spec FR-042）。
