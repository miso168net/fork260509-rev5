# Data Model — 003-auth-session

Phase 1 產物。**零 migration**：本刀所有表結構與 seed 皆在 001 基線；本檔只描述既有結構的
**行為語意**（狀態機、值域、寫入點、不變式）與 redis 承載態。wire 形制見 `contracts/`、
不重複。

## §1 sys_token 狀態機（B-017 核心；隨 §I.7 入憲）

**欄**（001 基線 9 欄、archetype C）：`id`／`created_at`／`created_by`（＝擁有者 uid）／
`status`／`token_hash`（SHA-256 hex 64、UNIQUE）／`rotation_chain`（＝`sid`＝會話身分）／
`issued_at`／`expires_at`／`used_at`。★**無 `last_activity` 欄**——idle 時鐘只住 redis（§6）。

**DB 層護欄**：partial UNIQUE `uq_sys_token_chain_active ON (rotation_chain) WHERE
status='active'` ⇒ 同鏈至多一條 active（並發 rotate 的失敗模式＝唯一鍵衝突 DbErr，MUST 辨識
並轉 grace 冪等分支、不得籠統 5000）。

**現態 × 事件 → 次態＋副作用**（rev5 首個狀態機矩陣；★列＝呈遞 refresh 票所對應的列狀態）：

| 現態 | 事件 | 次態 | 副作用 | 回應 |
|---|---|---|---|---|
| （無列） | refresh | — | — | `8888`（票不在狀態機內＝作廢／偽造） |
| `active` | refresh＋idle 未逾時 | 舊列→`rotated`（`used_at`＝now）；新列→`active`（同鏈） | 寫 grace（30s、★commit 前仍持鎖時）；★次序不可反 | `0000`＋新對 |
| `active` | refresh＋idle 逾時 | 不變 | SET NX `idle-emitted:{sid}` 冪等守門；僅首次落 `session_event(idle)`；★不寫 denylist | `8888` |
| `rotated` | refresh＋grace 命中 | 不變 | — | `0000`＋**既發的同一對**（冪等） |
| `rotated` | refresh＋grace miss | 全鏈→`revoked` | `revoke_family`＋落 `session_event(reuse)`＋denylist(revoked, TTL=refresh 全壽命) | `8888`（★唯一觸發 reuse 的形） |
| `revoked` | refresh＋denylist reason==`kicked` | 不變 | — | `7777`（modal） |
| `revoked` | refresh＋reason==`revoked` **或鍵缺席** | 不變 | ★不落事件、不重複撤（status 即權威） | `8888`（靜默） |
| `active` | logout（驗章成功） | 該列→`revoked` | denylist(revoked, TTL=refresh 全壽命)＋落 `session_event(logout)`（created_by＝本人） | `0000` |
| （任意／無） | logout（驗章失敗／垃圾票） | 不變 | ★不落事件 | `0000`（冪等 no-op；回異碼＝token 有效性 oracle） |
| `active` | 他處登入且 single-session 生效 | 其他 sid 之列→`revoked` | 逐 sid 落 `session_event(kicked, reason=single_session)`＋denylist(kicked, TTL=refresh 全壽命)＋寫 `sys_user.session_id` | 被踢者下個請求得 `7777` |

**不變式**：①同鏈至多一 active（DB partial UNIQUE）②rotate 次序：先舊列轉 `rotated` 再插新
`active` ③denylist TTL＝refresh 全壽命（兩 reason 皆然）④`access_TTL ≤ N×30 < N×60 ＝ idle 門檻`
（⇒ idle 觸發時 access 必已過期，故 idle 不需寫 denylist）。

## §2 session_event（append-only 稽核；001 基線 8 欄、archetype B）

`id`／`created_at`／`created_by`（操作者 uid、nullable）／`user_id`／`sid`／`event_type`／
`reason`／`source_ip`（★`varchar(45)`、**非 INET**——與 §3 的 `real_ip` 型別不同，寫入不共 helper）。

| `event_type` | `reason` | `created_by` | 落列時機 |
|---|---|---|---|
| `kicked` | `single_session` | 被踢對象 uid | login 第⑨步逐 sid |
| `reuse` | — | NULL | refresh 之 `rotated`＋grace miss（唯一形） |
| `idle` | `idle_timeout` | NULL | refresh 之 idle 命中首次（SET NX 守門） |
| `logout` | — | 本人 uid | logout 驗章成功 |

★無 update／delete（archetype B 不可竄改）。★redis 狀態永不影響本表內容（R3-7：缺 denylist
不落假 `reuse`）。

## §3 sys_login_attempt（節流權威源；001 基線 11 欄、archetype B）

`real_ip`（**INET NOT NULL**）／`peer_ip`／`x_forwarded_for`／`ip_confidence`／`success`／
`attempted_user_name`／`region`／`trace_id`／`created_at`／`created_by`／`id`。

**本刀寫入值**：`real_ip`＝nginx 注入的 `X-Real-IP`（client 自帶被 `proxy_set_header` 覆寫）／
`ip_confidence`＝`nginx_peer`（單一字面）／`x_forwarded_for`＝原文**截斷 1024＋剝 CR/LF**
（★不可信原文、任何渲染端必須轉義）／`peer_ip`／`region`／`trace_id`＝本刀不填。
★integration 測直打 8080 無 nginx ⇒ 標頭缺席，測試 MUST 顯式注入 `X-Real-IP`、不為缺席開
回填值。

**落列點恰三處**（皆在 login 內）：①`authenticate` Denied（外層 conn；uid 可為 None＝帳號查無）
②鎖內重驗失敗（★先 `txn.rollback()` 再落列於**外層 conn**，否則隨 txn 回滾）③成功（落 **txn
內**、與建會話原子）。**不落列四類**：形制閘超限（1000）／節流三個拒絕分支（`?` 早退、構造上
零寫入）／captcha 缺錯過期重放（同上）／5000 配置與內部異常。寫入為 best-effort：失敗只發
`degraded=db_write` 告警、不改登入回應——★但等於計數斷供（該帳號永不鎖亦永不 captcha），故
必須可見（§8）。

**滑動窗計數**（唯一權威）：窗內 `success=false` 列數，下界＝`GREATEST(窗起點, 窗內最近成功的
MAX(created_at), unlock_marker)`。★本刀 **完全不讀** unlock marker：rev4 存於 redis 鍵
`throttle:unlock:user:{name}`，而本刀無解鎖端點＝無寫入者，故 `unlock_marker_ts` 恆傳 `None`、
`cache` 六支 key builder 不含該鍵、降級 source 集不含 `redis_unlock_marker`（見 research R3-17）。★三源之「reset-on-success」由查詢形免費兌現、MUST 逐字帶入
不得簡化；★子查詢必帶窗下界（防全歷史回掃）；★`unlock_marker` 在本刀**無寫入者**（管理員解鎖
端點屬後續刀）——無 marker 綁 SQL NULL、`GREATEST` 非 strict 自然退化為兩源，故保留參數位
（未來解鎖刀零改動）、MUST NOT 用 sentinel 值；「該源恆 NULL」列為已知態、不得宣稱三源皆已驗。

## §4 sys_user 的會話欄（001 基線）

| 欄 | 型 | seed 現值 | 本刀語意 |
|---|---|---|---|
| `session_policy` | `varchar(20) NOT NULL DEFAULT 'inherit'` | 三帳號皆 `inherit` | 值域＝`single`｜`multi`｜`inherit`（★零 CHECK、碼層收斂＋值域測試守，加 CHECK 即破零 migration） |
| `session_id` | `varchar(36)` nullable | 三帳號皆 NULL | login 第⑨步寫入當前 sid（single-session 生效時） |

**兩層政策解析**：`effective_single = session_policy=='single' || (session_policy=='inherit'
&& single_session_default=='on')`；`single_session_default` 讀不到→**off 語意**（與 idle TTL
讀不到的 fail-loud 方向相反、刻意）。★seed 現值 `off`＋全帳號 `inherit` ⇒ 預設不啟用，
single-session 驗收須前置翻 `on`（並於驗收後翻回 `off`，見 §9 與 quickstart §0）。

## §5 sys_menu → MenuRoute 映射（dynamic 選單）

seed 78 列；★`constant` 欄值域 TRUE=0／FALSE=14／NULL=64 ⇒ `getConstantRoutes` 過濾謂詞
MUST 寫 `constant = TRUE`（**勿寫 `IS NOT FALSE`**），現回 `[]`。

| MenuRoute 欄 | 來源 | 規則 |
|---|---|---|
| `id` | `sys_menu.id`（i64） | ★序列化為**字串**（typings 宣告 string） |
| `name` | `route_name` | 直傳 |
| `path` | `route_path` | 缺值兜底空字串 |
| `component` | `component` | 直傳 |
| `children` | 子樹 | 非空才插 |
| `meta.title` | `i18n_key` fallback `menu_name` | ★恆存（唯一必填 meta 欄） |
| `meta.i18nKey` | `i18n_key` | ★須為前端生成鍵字面聯集之一，否則畫面出現點分字串 |
| `meta.icon`／`localIcon` | `icon`＋`icon_type` | `icon_type==2` → `(None, icon)`；否則 `(icon, None)`；★`icon_type` 本身不外洩 |
| `meta.{order,hideInMenu,keepAlive,constant,multiTab,href,activeMenu,fixedIndexInTab,query}` | 同名欄 | 全 optional、None 不序列化 |
| — | `roles` 類欄 | ★dynamic 模式下前端忽略 `meta.roles`（授權全靠後端 Casbin 過濾）⇒ **不下發** |

**樹組裝**：DB-fresh roles → Casbin `menu` 維度 `get_filtered_policy` 過濾 → 祖先包含 →
同層 `order` → `id` 升冪。**`home`**＝啟用角色（`status=1`）依 role id 升冪取首個非空
`role_home`，全空→`home`；再經兜底（驗屬可見樹之可導航葉；不屬→先序第一可導航頁）。★三 seed
角色 `role_home` 同值 ⇒ 機器測不出分歧，收斂律 MUST 由碼註釘住＋一支合成多角色測試守。

## §6 非 DB 承載態

**JWT Claims**（8 欄）：`uid`／`sid`（＝rotation_chain＝會話身分）／`jti`（per-token uuid）／
`roles`（★僅 hint，授權恆 DB-fresh）／`iss`／`aud`／`exp`／`iat`。驗章：HS256、`leeway=0`、
`validate_exp`、`set_issuer`／`set_audience`；access 與 refresh **各自秘鑰**。
**TTL**（N＝`session_idle_timeout` 分鐘）：`access = min(300, N×60/2)`／
`refresh = N×60 + access`；N 缺失→5000 不猜值。seed N=60 ⇒ access 300s／refresh 3900s／
idle 門檻 3600s。

**CaptchaClaims**（4 欄、無狀態簽題）：`nonce`（16 bytes OsRng→hex 32）／`user_name`（綁帳號）／
`exp`（＝簽發＋300s）／`ans_mac`＝`hex(SHA256(captcha_secret ‖ nonce ‖ lower(answer)))`
（★秘鑰參與雜湊 ⇒ 答案不可離線還原）。HS256、第三把秘鑰。字元集 34 字（小寫 a-z 去 `o`＋
數字去 `0`）、題長 4（34⁴≥10⁶）——★字集含 `0`/`o` 會因內嵌字型無 glyph 而**靜默跳過**、產約
20% 廢題。

**redis 鍵空間**：

| 鍵 | 值 | TTL | 語意 |
|---|---|---|---|
| `session:denylist:{sid}` | `kicked`｜`revoked` | refresh 全壽命 | 撤銷加速層（權威為 `sys_token.status`） |
| `session:{sid}:last_activity` | unix 秒 | refresh 全壽命 | idle 時鐘（唯一載體） |
| `session:rotate-grace:{token_hash}` | 新對 JSON | **30 秒** | rotate 冪等窗（結構上無 PG 退路） |
| `session:idle-emitted:{sid}` | `1` | refresh 全壽命 | idle 事件冪等守門（SET NX） |
| `throttle:lock:user:{name}` | 寫入時戳 | `min(window_secs, 900)` | L1 負快取；★唯一寫入點＝同一次新鮮 L2 讀之後；命中**不續期** |
| `throttle:captcha:used:{nonce}` | `1` | 300 秒 | 提交即消耗（SET NX、寫入**先於**答案比對） |

★nil 與 Err 嚴格分流：所有 GET 一律 `Option<T>`——nil→`Ok(None)`＝權威「未撤／未寫」；
連線故障→`Err`＝caller 退權威源（§8）。★測試鍵 MUST 加 uniq 前綴（時戳＋pid），dev 與測試
共用 DB 0。

## §7 設定鍵消費表（16 鍵中本刀只活 5 個）

| 鍵 | seed | 本刀消費點 | 讀不到時 |
|---|---|---|---|
| `session_idle_timeout` | 60 | login 第⑥步套 TTL；idle 門檻 | **5000 fail-loud**（不猜值） |
| `single_session_default` | off | login 第⑨步兩層政策 | **off 語意**（保守多會話） |
| `login_throttle_max_fails` | 5 | 硬鎖門檻 | 退常數 5＋一筆告警 |
| `login_throttle_window_minutes` | 15 | 滑動窗長（亦決定 L1 lock TTL 上界） | 退常數 15＋同一筆告警 |
| `login_throttle_captcha_after` | 2 | 軟區門檻 | 退常數 2＋同一筆告警 |
| `ip_*` 三鍵 | 10／50／15 | **本刀零消費者**（延 B-019） | — |
| `password_*` **八**鍵 | — | **本刀零消費者**（無改密／建帳號端點） | — |

★三個節流鍵缺失時告警**每次載入至多一筆**（不放大成三筆）。

## §8 降級不變式（隨 §I.7 Amendment 入憲；完整矩陣見 research R5）

- denylist 讀不到（Err）→ **fail-closed**：退 PG `has_active_in_chain`；PG 亦故障→視為無
  active、絕不盲放。
- last_activity 不可讀 → **fail-open**：不 idle-reject（token exp 為界）。
- grace 不可用 → **fail-secure**：並發 refresh 觸發 reuse→撤家族（多分頁全域登出、重登復原）。
- captcha 標記 SET NX 瞬斷（redis 健康）→ **拒但零計數不罰**；redis **整體不可用** →
  軟區要求**整層停用**、續驗密碼（密碼錯仍計數）。
- 節流 L2（PG）失敗 → **fail-open ＋ `captcha_forced = !redis_down`** 補償（否則 DB 抖動同時
  關閉節流與 captcha）；★`captcha_forced` 不入軟區計數。
- 失敗列寫入失敗 → best-effort、不改回應；★計數斷供必須可見（`degraded=db_write`）。

## §9 gate2 seed 與 runtime 寫入的相容紀律（本刀首撞）

凍結 seed 對 `sys_token`／`session_event`／`sys_login_attempt` 各有 0 列 COPY 段＋
`setval(seq, 1, false)`，schema-gate gate2 **原位保留 setval 逐列 diff**。本刀寫入這三張表會
**不可逆推進三支 sequence**——刪列救不回 setval（002 的還原守衛只 `UPDATE system_settings`、
無 sequence，故未撞到）。

**紀律**：真 DB 測試守衛除還原列外，MUST 顯式 `setval(<seq>, 1, false)` 重設三支 sequence；
`single_session_default` 前置翻 `on` 者驗收後 MUST 翻回 `off`（連帶 `updated_at`／
`updated_by`）。否則 gate2 seed 自本刀起永久紅、須 pristine 重放才綠。
候選 BACKLOG：對 append-only 稽核表的 seed 比對面收窄。
