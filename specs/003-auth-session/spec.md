# Feature Specification: 003 auth 域整批——真登入、會話生命週期、節流＋驗證碼、dynamic 選單

**Feature Branch**: `003-auth-session`

**Created**: 2026-08-09

**Status**: Draft

**Input**: User description: "docs/brainstorms/003-auth-session.md"（階段 0 brainstorm＋同日覆核輪
——六路唯讀搜證 144 findings＋grilling 一問一答十三題逐題拍板 §1.2；本 spec 之唯一輸入。直接
輸入含 BACKLOG B-017／B-020／B-022／B-029／B-047／B-050／B-051＋K1 十四條與 K2 六條（該檔
§2 表）；rev4 對應碼＝實作預設藍本、清單於 plan research 凍結（ADR 0019））

> 摘要：把 base-web fork 原版 service 已在呼叫的認證／路由端點補齊到終態——真帳密登入、
> DB-stateful token rotation、帳號維登入節流、圖形驗證碼、dynamic 側邊欄、後端 msg 前端轉譯；
> ROUTES 4→16 條；開憲法 §III.2 首批四條 ★ 軌道＋§I.7 首批五座行為島入憲（1.2.0→1.3.0）。
> 交付價值＝rev5 第一次端到端可見（瀏覽器真登入 → 側邊欄由後端 Casbin 過濾生成、錯誤訊息顯
> 人話）＋rust-api release profile 第一次可跑（`dev_identity` 整檔汰換）。預期**零 migration**
> （sys_token 9 欄＋rotation partial UNIQUE＋session_event＋sys_user.session_policy／session_id
> ＋16 設定鍵 seed 全在 001 基線；零新 casbin 政策列）。

## Clarifications

### Session 2026-08-09（brainstorm 覆核輪代答；spec 沿用、/speckit-clarify 複核）

- Q: 未認證／會話失效回哪個碼？→ A: **三分**（比 rev4 更精確）：access exp 過期→`3333`
  （前端自動 refresh 無感續期）／標頭缺席・非 Bearer・簽章不符・已撤銷・refresh 鏈失效→
  `8888`／被踢下線→`7777`（modal）。rev4 把「缺席」也判 3333，未登入者每次白跑一輪注定失敗
  的 refresh。
- Q: refresh 遇 `revoked` 列但 denylist 鍵缺席時判哪個碼？→ A: **`sys_token.status=='revoked'`
  即權威**（rev5 對 rev4 差異點）：缺 denylist（nil）回靜默 `8888`、不落事件、不重複撤；reuse
  偵測**只保留給 `rotated` 且 grace miss**。denylist 純加速層，其狀態（TTL 短／連線故障／資料
  遺失）永不污染稽核帳。代價＝redis 丟失時被踢者拿 `8888` 而非 `7777`（解釋性降級、非安全）。
- Q: token rotation grace 冪等窗載於何處、redis 故障時方向？→ A: **grace 住 redis**（sys_token
  只存 hash＝結構上無 PG 退路）、fail-secure（redis 故障期間並發 refresh 觸發 revoke_family、
  多分頁使用者被全域登出、重登即復原＝已知態）。
- Q: captcha nonce used 標記寫不進 redis 時？→ A: **拒絕不罰**（沿 rev4）：該次登入拒絕（重放窗
  不存在）、但不消耗計數桶（不推進 ≥5 硬鎖）。★射程限「redis 連得上、單次寫入瞬斷」——redis
  整體不可用另有相反方向，見下一 session 之兩層拍板。
- Q: logout 對已失效／垃圾 refresh token 回哪個碼？→ A: **一律 `0000` 冪等 no-op、不落事件**
  （回異碼＝提供 token 有效性 oracle）。
- Q: 圖形驗證碼字面／crate？→ A: 字元集 34 字（小寫 a-z 去 `o`＋數字去 `0`）、產圖 crate＝
  `captcha 1.0.0`（rev4 釘版）。
- Q: 未認證回 `8888` 還是沿 002 待複核？→ A: 三分拍板已定 `8888`（002 FR-015 的「plan 期複核」
  於本刀收斂）。

### Session 2026-08-09（/speckit-clarify）

- Q: refresh token 輪替的 grace 冪等窗要設多長？→ A: **30 秒**（rev5 對 rev4 差異點——rev4 用
  10 秒，但 rev5 前端最壞換發間隔約 11 秒〔1 秒 promise 快取＋10 秒單請求 timeout〕，10 秒等於
  預留「慢請求即誤撤」踩雷點；30 秒給約 3 倍餘裕，延後盜用偵測的暴險比例＜1%〔refresh 全壽命
  約 65 分〕）。
- Q: 使用者同時具多個角色時，登入後要落到哪一個角色的首頁？→ A: **沿 rev4 已驗證規則**——
  啟用角色（`status=1`）依 role id 升冪掃描、取首個**非空** `role_home`；全空→預設 `home`
  （自動跳過「停用角色」與「空 role_home」兩個陷阱）。選出後仍過既定兜底（驗屬可見樹可導航葉）。
- Q: 本刀的降級與安全事件要不要進 Prometheus 計數器（不只寫 log）？→ A: **雙軌——結構化
  tracing warn（帶 target＋欄位）＋計數器**；序列面取本刀真有發射點的三支
  （`throttle_degraded_total`／`denylist_hit_total`／`throttle_soft_zone_total`）＋啟動即顯式
  註冊 0，rev4 的 HLL 廣度估計兩支不做；守門走計數器 render 文本比對、不新建 log 捕捉層設施
  （詳見 FR-034）。
- Q: 登入頁三顆快速登入鈕（Super／Admin／User＋寫死 123456）保留還是拿掉？→ A: **保留＋記帳**
  ——本刀零 inline、不占軌道用途（rev4 亦保留），手動驗收一鍵切三帳號；連帶把「快速登入鈕暴露
  dev seed 帳密＝已知態、轉 prod 前必須拆除」寫入 ADR＋BACKLOG 新條目（綁 prod 硬化刀），
  避免此事無帳面家。
- Q: redis 不可用時，軟區帳號到底還能不能登入？→ A: **沿 rev4 完整兩層、方向相反**——①redis
  整體不可用（連不上／無 cache）→整個軟區 captcha 要求**停用**、直接續驗密碼（驗不了題就不該
  要求，否則把合法使用者鎖在門外；密碼錯仍照常計數）②redis 連得上但單次 SET NX 標記瞬斷→
  **拒但零計數不罰**（若放行，攻擊者附偽造 captchaId 即可在瞬斷窗通關＝降級恰好只放行對抗性
  流量）。★本條補正覆核輪 R10 的射程（當時只查到第②層）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 真帳密登入取得會話、側邊欄由後端生成 (Priority: P1)

作為 admin 後台使用者，我以帳號密碼登入，系統驗章成功後發給我一對可續期的憑證；登入後我看到
的側邊欄選單，是後端依我的角色經 Casbin 過濾後動態生成的（非前端寫死），且登入頁等內建常量
路由不受影響。

**Why this priority**: 這是 rev5 第一次端到端可見——沒有真登入與 dynamic 側邊欄，一切後續
功能刀（管理頁、B-008 view 腿）都無入口。它獨立成 MVP：只實作 login＋getUserInfo＋
getUserRoutes＋getConstantRoutes 與前端 dynamic 接線，即交付「瀏覽器真登入看見角色化側邊欄」
的完整價值。

**Independent Test**: 起容器 stack，瀏覽器以三個 seed 帳號（Super／Admin／User，密碼皆
`123456`）分別登入，觀察三者側邊欄差異；比對 getUserInfo 回包（userId 字串型／userName 為
nick_name／roles／buttons）與 getUserRoutes 樹（角色可見選單）。

**Acceptance Scenarios**:

1. **Given** seed 三帳號在庫、`.env` 已翻 `VITE_AUTH_ROUTE_MODE=dynamic`＋baseURL＝`/api`，
   **When** 使用者以正確帳密經 `/api/auth/login` 登入，**Then** 回 `{data:{token,refreshToken},
   code:"0000"}`、前端存憑證並轉呼 getUserInfo／getUserRoutes、側邊欄呈現該角色可見選單。
2. **Given** 已登入的 access token，**When** 呼叫 `/auth/getUserInfo`，**Then** 回
   `{userId(字串), userName(＝nick_name fallback user_name), roles[], buttons[]}` 四欄皆備。
3. **Given** dynamic 模式，**When** 呼叫 `/route/getUserRoutes`，**Then** 回 `{routes[], home}`
   ——routes 為該使用者角色經 Casbin `menu` 維度過濾後的 sys_menu 樹（含祖先包含、同層
   order→id 升冪）、home 為經兜底解析的可導航葉頁。
4. **Given** 登入前尚無 access token，**When** 呼叫 `/route/getConstantRoutes`，**Then** 回
   常量路由集（Public 可取得）；前端與寫死的 5 條 builtin 常量路由（403/404/500/iframe-page／
   login）**合併**而非取代（seed constant=TRUE 為 0 列、取代語意會清空登入頁）。
5. **Given** 錯誤帳密，**When** 登入，**Then** 回 `1000`（`auth.login.failed`）、不洩漏帳號
   是否存在（三態 collapse 同一碼）。

---

### User Story 2 - access 過期無感續期（token rotation） (Priority: P2)

作為已登入使用者，當我的短命 access token 過期時，系統以我的 refresh token 自動換發新的一對
憑證、我的操作不中斷、也不會被要求重新登入；並發請求同時觸發換發時不會誤判我盜用而登出。

**Why this priority**: 續期是「可續期會話」的核心；沒有它，使用者每隔數分鐘就被登出。依賴
US1 的登入但可獨立驗收（登入後等 access 過期、觀察自動 refresh）。

**Independent Test**: 登入後直接以舊 last_activity 值寫入（免注入時鐘）觸發各分支；或以同票
兩並發驗證 rotation 冪等——斷言一支 rotate、一支走 grace 回同一對、不觸 reuse。

**Acceptance Scenarios**:

1. **Given** access 過期（回 `3333`），**When** 前端自動以 refresh token 呼叫
   `/auth/refreshToken`，**Then** 回新的一對憑證（舊 refresh 列轉 `rotated`、插新 `active`
   同鏈）、原請求以新 token 重放成功。
2. **Given** 同一 refresh token 的兩個並發換發（多分頁），**When** 兩請求先後到達，**Then**
   一支完成 rotation、另一支在 grace 窗內冪等回既發後繼的同一對、**不**觸發 reuse 偵測、
   **不**落 `session_event(reuse)`。
3. **Given** 已 rotate 過的舊 refresh token 且 grace 窗已過，**When** 再次持它換發，**Then**
   判為 reuse→撤銷整條 session 家族＋落 `session_event(reuse)`→`8888`（唯一觸發 reuse 的形）。
4. **Given** refresh token 簽章失敗／過期／垃圾值，**When** 換發，**Then** 一律回 `8888`
   （★絕不 `3333`——否則前端自動 refresh 死迴圈）。

---

### User Story 3 - 會話撤銷與單一會話治理（logout／被踢／閒置） (Priority: P2)

作為使用者，我登出後舊憑證立即在伺服器端失效；當單一會話政策開啟時，我在他處登入會使前一
會話被踢下線（顯示 modal）；長時間閒置的會話會逾時失效。

**Why this priority**: 撤銷語意是安全面的底線（登出即撤、他處登入即踢）。依賴 US1／US2 的
會話狀態機但可獨立驗收各撤銷路徑。

**Independent Test**: logout 後以舊 token 打受保護端點得 `8888`；single-session 前置翻 on 後
同帳號二次登入、斷言前一條下個請求得 `7777`；idle 直接寫舊 last_activity 值觸發逾時。

**Acceptance Scenarios**:

1. **Given** 已登入使用者，**When** 於 UI 按登出（前端 best-effort 呼 `/auth/logout` 後清本地
   儲存），**Then** 該 refresh token 對應 session 於伺服器端撤銷、舊憑證再打受保護端點得
   `8888`；logout 對任何 refresh token（含垃圾／已撤）一律 `0000` 冪等 no-op、不落事件。
2. **Given** `single_session_default=on`（前置以 `updateSystemSetting` 翻），**When** 同帳號
   在他處二次登入，**Then** 前一會話被踢、其下個請求得 `7777`（modal「你已在他處登入」）、
   落 `session_event(kicked, reason=single_session)`。
3. **Given** 會話閒置超過 `session_idle_timeout`，**When** 持既有憑證換發或請求，**Then** 判
   idle 逾時→`8888`、僅首次落 `session_event(idle)`（SET NX 冪等守門、背景 refresh-loop 不
   刷重複列）。
4. **Given** 被踢者在 access 過期後於 (access, refresh) 窗內換發，**When** refresh，**Then**
   仍得 `7777`（denylist TTL＝refresh 全壽命保證，不降級為 8888、不落假 reuse）。

---

### User Story 4 - 登入失敗節流三區＋圖形驗證碼 (Priority: P3)

作為系統，我對同一帳號的連續登入失敗施以三區節流：少量失敗自由重試、達門檻後要求圖形驗證
碼、再失敗則短暫鎖定；驗證碼答對但登入仍失敗時自動換發新題。

**Why this priority**: 節流是 001 已 seed 的三區狀態機（captcha_after=2／max_fails=5），不做
captcha 軟區即塌。依賴 US1 的登入路徑但可獨立驗收三區轉換。

**Independent Test**: 對同一帳號連續送錯密碼，斷言失敗 <2 自由／2–4 回 `2222
biz.auth.captchaRequired`／≥5 回 `2222 biz.auth.locked`；軟區送正確驗證碼但錯密碼→登入失敗
且自動換題。

**Acceptance Scenarios**:

1. **Given** 某帳號失敗次數在滑動窗內 <2，**When** 再次登入失敗，**Then** 直接回 `1000`
   （不要求驗證碼）。
2. **Given** 失敗次數達 2–4（軟區），**When** 未帶或帶錯驗證碼登入，**Then** 回 `2222
   biz.auth.captchaRequired`——在 argon2 之前擋下、不落稽核列、不消耗計數桶。
3. **Given** 失敗次數 ≥5，**When** 登入，**Then** 回 `2222 biz.auth.locked`（同樣 argon2 前
   擋、零列零桶）；成功登入或解鎖 marker 使滑動窗計數重置。
4. **Given** 軟區帳號，**When** 呼叫 `/auth/loginCaptcha?userName=X`（含不存在帳號），**Then**
   一律發題（`{captchaId, captchaImg(data URI)}`、零存在性洩漏）；userName 超限走與登入端點
   同形的 `1000` 閘；產圖／簽章內部失敗→`5000`。

---

### User Story 5 - 替代登入四流程誠實 stub＋錯誤訊息顯人話 (Priority: P3)

作為使用者，當我嘗試手機驗證碼登入／註冊／重設密碼等尚未開放的流程時，得到明確的「該功能
尚未開放」提示（而非假成功）；且所有錯誤／狀態提示以我的介面語言顯示人話，而非後端識別字。

**Why this priority**: 誠實 stub 消滅 upstream 三張表單的假成功（安全誤導）；i18n 前端轉譯
兌現「錯誤訊息顯人話」的交付價值。依賴 US1～US4 產生的 msg key 但可獨立驗收提示文案。

**Independent Test**: 送出替代登入四流程任一，斷言回 `2222 biz.auth.notSupported`、UI 顯示
對應語言人話；切換語系觀察同一後端 key 顯示不同語言譯文。

**Acceptance Scenarios**:

1. **Given** upstream 三張表單（code-login／register／reset-pwd），**When** 送出，**Then** 打
   後端 stub 回 `2222 biz.auth.notSupported`、UI 顯示「該功能尚未開放」人話（非假成功 toast）
   ——★繁中字面以 `contracts/msg-keys.md` 為權威（該欄逐字落進 `zh-tw.ts` 與生成字典）。
2. **Given** 後端回任一業務碼（如 `biz.auth.captchaRequired`／`auth.login.failed`），**When**
   前端顯示，**Then** 經 `$t` 轉譯為當前語系人話（zh-CN 顯簡中／en-US 顯英文）、未命中鍵才
   graceful fallback 回原文。
3. **Given** 7777 被踢 modal，**When** 顯示，**Then** modal 內容為轉譯後人話（非
   `auth.session.kicked` 裸鍵）。

---

### Edge Cases

- **並發同鏈 rotation**：同鏈至多一條 active 由 partial UNIQUE 硬保證；並發失敗模式＝唯一鍵
  衝突 DbErr，MUST 辨識並轉 grace 冪等分支、不得籠統回 `5000`。
- **redis 全故障**：denylist 查 fail-closed（退 PG `has_active_in_chain`、PG 亦故障→視為無
  active 拒絕、絕不盲放）；idle fail-open（無 last_activity 即不 idle-reject、退 token exp 為
  界）；grace fail-secure（並發 refresh 觸發 revoke_family、多分頁全域登出、重登復原＝已知態）；
  captcha 分兩層——整體不可用→軟區要求停用（fail-open、免把合法使用者鎖死）／單次標記寫入瞬斷
  →拒但不罰（FR-016）。
- **redis RDB 回捲**（不開 AOF＝已知態）：denylist 鍵可在回捲窗內丟失；暴險受「status 即權威」
  封頂（換發被 PG 擋）、復活面＝被踢者既有 access 直打 API 至自然過期（≤access TTL）。
- **設定鍵讀不到**：節流門檻／idle TTL 退活書常數＋一筆 `degraded=settings_default` 告警（每次
  載入至多一筆）；idle TTL 缺失於 login 第⑥步反而 fail-loud `5000`（不猜 TTL 值）。
- **X-Real-IP 缺席**（integration 直打 8080 無 nginx）：`sys_login_attempt.real_ip` 為 INET
  NOT NULL，測試 MUST 顯式注入 X-Real-IP、不為缺席開回填值。
- **x_forwarded_for 惡意值**：入庫前截斷至 1024 字元＋剝 CR/LF；該欄為不可信原文、任何渲染端
  必須轉義（帳面隨稽核 UI 刀）。
- **非 2xx HTTP 吞信封**：前端 validateStatus 只放 2xx＋304，非 2xx 使錯誤信封整個丟失、
  onBackendFail 不跑——故 `3333`／`7777`／`8888`／`1000`／`2222` MUST 皆映射 HTTP 200；僅
  `4040`→404、`5003`→403（既有已知態）。
- **method_not_allowed（B-047）**：已註冊路徑遇未註冊動詞 → 回 `4040` 信封＋HTTP 404（消除
  框架預設 405 裸 body）；動詞探測閘 MUST 永遠裸掛 router（改走 build() 共用即恆綠）。
- **loginCaptcha 廢題**：字元集含 `0`/`o` 時產圖 crate 靜默跳過無 glyph 字元→約 20% 不可解
  題；故字集 MUST 為 34 字（去 `o`／`0`）。

## Requirements *(mandatory)*

### Functional Requirements

**端點與路由（ROUTES 4→16）**

- **FR-001**: ROUTES MUST 由 4 條擴為 16 條，逐條對齊 rev4 實表（路徑與 Protection 已逐字
  核實）。新增 12 條：`/auth/login`（POST/Public）、`/auth/refreshToken`（POST/Public）、
  `/auth/logout`（POST/Public）、`/auth/getUserInfo`（GET/Authed）、`/auth/loginCaptcha`
  （GET/Public）、`/auth/{sendCaptcha,codeLogin,register,resetPwd}`（POST/Public）、
  `/route/getConstantRoutes`（GET/Public）、`/route/getUserRoutes`（GET/Authed）、
  `/route/isRouteExist`（GET/Authed）。三個 Public（refreshToken／logout／getConstantRoutes）
  各有非做不可理由（過期不能換／壞了不能撤／登入前需取常量路由）。
- **FR-002**: 零新 casbin 政策列——16 條 route 無一為 `Protection::Policy`；163 條 seed 政策
  一列不動、維持零 migration。seed 已含 kickUser／getSessionEvent／user:kick 等後續刀政策列，
  本刀 MUST NOT 消費（spec 明寫防 review 質疑「政策設得進、端點不存在」）。
- **FR-003**: `/auth/loginCaptcha` MUST 帶 `?userName=` query（challenge 綁帳號的前提；對任意
  userName 一律發題＝零存在性洩漏）；userName 超限走與登入端點**同形**的 `1000` 閘（零新碼
  零新 key）；產圖／簽章內部失敗→`5000`。

**認證與登入（B-017 login）**

- **FR-004**: login MUST 依序執行十一步：①輸入形制閘（超限 `1000`、零稽核零 argon2 不消耗桶）
  ②節流狀態機（FR-014）③`authenticate`（帳號不存在／密碼錯／已停用三態 collapse 同一 `1000`）
  ④開 txn＋`pg_advisory_xact_lock(uid)`⑤**鎖內重驗**（status／deleted_at／password 字面比對；
  ★不重跑 argon2）⑥讀 `session_idle_timeout` 套 TTL（缺失→`5000` 不猜值）⑦生新 sid＋簽對
  ⑧sys_token insert ⑨single-session 判定＋逐 sid `session_event(kicked)`＋寫 session_id
  ⑩稽核成功列同 txn ⑪commit 後 best-effort 進 denylist＋last_activity 起點。
  ★第⑥步之 TTL 公式（規範，非假設）：`access = min(300, N×60/2)`／`refresh = N×60 + access`
  （N＝`session_idle_timeout` 分鐘）；seed N=60 ⇒ access 300s／refresh 3900s／idle 門檻 3600s。
  ★**稽核列寫入點恰三處**（本條為 FR-014「滑動窗為權威」的資料來源，缺此則三區節流永不觸發）：
  ①`authenticate` Denied（外層 conn；uid 可為 None＝帳號查無）②鎖內重驗失敗（★先
  `txn.rollback()` 再落列於**外層 conn**，否則隨 txn 回滾）③成功（落 txn 內、與建會話原子）。
  **不落列四類**：形制閘超限（第①步）／節流三個拒絕分支（第②步以 `?` 早退、構造上零寫入）／
  captcha 缺錯過期重放／`5000` 配置與內部異常。寫入為 best-effort：失敗只發
  `degraded=db_write` 告警、不改登入回應——★但等於計數斷供（該帳號永不鎖亦永不 captcha），
  故 MUST 可觀測（FR-034）。
- **FR-005**: single-session 判定（第⑨步）MUST 為**兩層政策解析**：`effective_single =
  session_policy=='single' || (session_policy=='inherit' && single_session_default==on)`；
  `sys_user.session_policy` 值域＝{single, multi, inherit}（碼層收斂＋值域測試守、不加 CHECK
  以保零 migration）；`single_session_default` 缺鍵→off 語意（與第⑥步 fail-loud 方向相反、
  刻意）。
- **FR-006**: getUserInfo MUST 回 `UserInfo{userId, userName, roles[], buttons[]}` 四欄皆備：
  `userId` typings 宣告字串、DB i64 於序列化邊界轉字串（憲法 §I.3）；`userName`＝`nick_name`
  fallback `user_name`（碼中零帳號字面——「User→User01 alias」以 seed 資料兌現、rev4 亦然）；
  `roles` DB-fresh；`buttons`＝Casbin `button` 維度政策枚舉（`get_filtered_policy`、非
  `enforce*`＝不觸單一判定進入點守恆）。

**會話生命週期（B-017 refresh／logout／enforce）**

- **FR-007**: refresh MUST：驗章失敗一律 `8888`（★絕不 `3333`——jwt 底層恆吐 3333、handler
  漏 map_err 即死迴圈）；`FOR UPDATE` 鎖呈遞列後分流——`active`→idle 檢查→rotate（舊列轉
  `rotated`+`used_at`、插新 `active`，次序不可反、partial UNIQUE 護欄）→寫 grace（TTL＝**30
  秒**＞前端最壞換發間隔 11 秒；★commit 前、仍持鎖時）；`rotated` 且 grace 窗內→冪等回既發後繼；`rotated` 且 grace miss→reuse 偵測
  （唯一觸發形）→`revoke_family`+`session_event(reuse)`→`8888`；`revoked`→denylist
  reason==kicked→`7777`／其餘（reason==revoked **或鍵缺席**）→靜默 `8888`、不落事件、不重複
  撤；查無列→`8888`。
- **FR-008**: denylist TTL MUST 為 **refresh 全壽命**（非 access），且 **kicked／revoked 兩
  reason 一律 refresh_secs**（rev5 對 rev4 差異點：rev4 僅 kicked 用 refresh_secs、logout／
  reuse 路徑仍 access_secs＝同缺陷換 reason 版）——否則被踢／被撤者於 (access, refresh) 窗內
  換發時 denylist 已過期、掉進 reuse 分支回 `8888` 並落假 `session_event(reuse)`。
- **FR-009**: idle 逾時 MUST：門檻＝`refresh_secs − access_secs`（＝N×60，N＝idle_timeout 分
  鐘）、僅 last_activity 可讀時判；命中→SET NX `idle-emitted:{sid}` 冪等守門、僅首次落
  `session_event(idle)`→`8888`；idle 命中 MUST NOT 寫 denylist（不變式 `access_TTL ≤ N×30 <
  N×60`⇒idle 觸發時 access 必已過期）。
- **FR-010**: logout MUST 冪等：驗 refresh 成功→撤該 session（列轉 revoked＋denylist）＋落
  `session_event(logout, created_by=本人)`→`0000`；驗章失敗（垃圾／過期）→仍 `0000` no-op、
  不落事件、★絕不 `8888`（回異碼＝token 有效性 oracle）。
- **FR-011**: enforce middleware MUST：驗 access→denylist 查→放行後推進 last_activity；redis
  故障退 PG `has_active_in_chain`（無 active→`8888` fail-closed）；PG 亦故障→視為無 active、
  絕不盲放。Public 路由不掛本 middleware（「Public 不查 denylist／refresh 不推進 idle-clock」
  天然成立）。
- **FR-012**: 五座行為島的降級方向 MUST 落實並隨 §I.7 入憲：denylist fail-closed／idle
  fail-open／grace fail-secure／captcha 兩層（整體不可用→要求停用 fail-open；單次標記瞬斷→拒但
  不罰）；redis 不開 AOF＝已知態（暴險受
  FR-007「status 即權威」封頂）。session_event.source_ip 為 varchar(45)（與 sys_login_attempt
  .real_ip 的 INET 型別不同、寫入不共 helper）；event_type／reason 字面沿 rev4（kicked／reuse／
  idle／logout；reason=single_session／idle_timeout 等）。

**登入節流（B-020 帳號維）**

- **FR-013**: 節流三區 MUST：失敗 <2 自由／2–4 回 `2222 biz.auth.captchaRequired`／≥5 回
  `2222 biz.auth.locked`；後兩者 MUST 在 argon2 之前擋下、不落稽核列、不消耗計數桶（構造上
  零 record_attempt——落列則鎖可被週期性探測無限延長）。
- **FR-014**: 節流權威源 MUST 為 `sys_login_attempt` 滑動窗（GREATEST 三源下界：窗起點／窗內
  最近成功／unlock marker——reset-on-success 由查詢形免費兌現、MUST 逐字帶入不得簡化）；redis
  為 L1 負快取（命中不續期；lock key 唯一寫入點＝同一次新鮮 L2 讀）；設定鍵讀不到→退活書常數
  ＋一筆 `degraded=settings_default` 告警（每次載入至多一筆；告警形式見 FR-034）。★三源下界的
  unlock marker 在本刀**無寫入者**（管理員解鎖端點屬後續刀）——無 marker 綁 SQL NULL、`GREATEST`
  非 strict 自然退化為兩源，故查詢形沿 rev4 保留該參數位（未來解鎖刀零改動）、MUST NOT 用
  sentinel 值；「該源恆 NULL」列為已知態、不得據此宣稱三源皆已驗。
- **FR-015**: 節流實作 MUST 老實記為 **login 專用**（本刀唯一消費者＝login）、不宣稱通用 seam
  （閘存在≠生效——通用化與第二消費者隨 B-021）；per-IP 維本刀不做（`request_context.rs` 留
  介面位、信任判定屬 B-019）。IP 維不做的理由＝per-IP **鎖定**（不自癒）在 prod CF 拓樸下會把
  整個邊緣後方的人塞進少數桶一併鎖掉；nginx `limit_req`（自癒速率限制）與懲罰性鎖定是兩回事、
  可先行。

**圖形驗證碼（B-029）**

- **FR-016**: captcha MUST 為無狀態簽題 `CaptchaClaims{nonce, user_name, exp, ans_mac}`（HS256、
  第三把秘鑰 `APP_CAPTCHA_SECRET`）；`ans_mac = hex(SHA256(secret ‖ nonce ‖ lower(answer)))`
  ——秘鑰參與雜湊故答案不可離線還原；challenge 綁 user_name；驗題在 redis 標記 nonce used
  （SET NX、寫入**先於**答案比對＝提交即消耗：一張題只能作答一次、答錯即失效須重取；若「答對
  才消耗」則同一張題可在有效期內被反覆猜）。**redis 降級分兩層、方向相反**（沿 rev4）：①redis
  整體不可用（連不上／無 cache）→整個軟區 captcha 要求**停用**、直接續驗密碼（驗不了題就不該
  要求，否則把合法使用者鎖在門外；密碼錯仍照常計數、摩擦力不歸零）②redis 連得上但單次 SET NX
  瞬斷→**拒但零計數不罰**（若放行，攻擊者附偽造 captchaId 即可在瞬斷窗通關＝降級恰好只放行
  對抗性流量）。★captcha 缺／錯／過期／重放一律 `2222 biz.auth.captchaRequired` 且**零稽核列
  零計數桶**——答錯不推進鎖定，但該題已耗須重取。★題目有效期＝**300 秒**（規範，非假設；
  `CaptchaClaims.exp` 與 redis nonce-used 標記 TTL 同值，確保「題失效前重放必被擋」）。
- **FR-017**: captcha 字元集 MUST 為 34 字（小寫 a-z 去 `o`＋數字去 `0`）、題長 4（34⁴≥10⁶）
  ——產圖 crate 內嵌字型排除混淆字且對無 glyph 字元靜默跳過，字集含 `0`/`o` 產約 20% 廢題。
  答對但登入失敗時前端自動換題。
- **FR-018**: request_context MUST 加 `real_ip`／`x_forwarded_for`／`ip_confidence` **原樣轉錄**
  欄（零信任判定——handler 一律經此型取請求事實、絕不自讀轉發標頭；B-019 接手只換 real_ip
  推導、欄與寫入點不動）；`real_ip`＝nginx 注入的 X-Real-IP（INET NOT NULL）、`ip_confidence`
  ＝`nginx_peer`（snake_case；B-019 接手時與 rev4 七態合併治理）、`x_forwarded_for` 截斷 1024
  ＋剝 CR/LF 後存。

**dynamic 選單與路由（B-018 前端腿）**

- **FR-019**: getUserRoutes MUST 回 `UserRoute{routes[], home}`：routes＝DB-fresh roles→Casbin
  `menu` 維度過濾→sys_menu 樹（祖先包含、同層 order→id 升冪）；`MenuRoute.id` 為字串（i64→
  字串）；欄位映射沿 rev4 `to_menu_route`（icon_type 拆 icon／localIcon、title 恆存、其餘欄
  optional）；`home` 之多角色收斂律＝**啟用角色（status=1）依 role id 升冪、取首個非空
  `role_home`；全空→預設 `home`**（沿 rev4 已驗證規則），選出後再經兜底解析（驗 home 屬可見樹
  可導航葉、不屬→先序第一可導航頁——否則「登入落 404」復活）；★三 seed 角色 role_home 同值＝
  機器測不出分歧，收斂律 MUST 由碼註釘住＋一支合成多角色測試守。
- **FR-020**: getConstantRoutes MUST 濾 `sys_menu.constant = TRUE`（★勿寫 IS NOT FALSE——
  constant 允許 NULL 64 列）組樹；seed constant=TRUE 為 0 列故現回 `[]`；前端 constant routes
  接線 MUST **合併**（`[...staticRoute.constantRoutes, ...data]`、Map 按 name 收斂後端同名可
  覆寫）而非取代——取代會清空 5 條 builtin 常量路由（403/404/500/iframe-page／login）。
- **FR-021**: isRouteExist（GET/Authed）MUST 依 rev4 形回傳路由存在性判定。dynamic 模式下前端
  三處硬閘（initConstantRoute／initAuthRoute／getIsAuthRouteExist）方會呼叫本組 route 端點；
  故 `.env` MUST 翻 `VITE_AUTH_ROUTE_MODE=dynamic`（見 FR-027）。

**替代登入誠實 stub（B-022）**

- **FR-022**: 四替代登入端點（sendCaptcha／codeLogin／register／resetPwd）MUST 共用一支
  `not_supported_stub()`、恆回 `2222 biz.auth.notSupported`；前端三張表單（code-login／register／
  reset-pwd）各改 2 行改打 stub（消滅假成功 toast）、表單與入口原樣保留。第四流程（自助頁手機
  驗證從零建頁）不在本刀（B-022 半消化、條目續留）。

**錯誤處理與碼表（B-047＋§I.3）**

- **FR-023**: `AppError` MUST 由 6→9 變體（加 `LoginFailed` 1000／`TokenExpired` 3333／
  `ModalLogout` 7777；`Biz(Cow)` 已存在故三新 Biz 構造點不需新變體）。碼表終形＝9 可發＋4
  保留（7778/8889/9998/9999）＝13；`issuable_six_and_no_variant_seven` 測試 MUST 改斷言此對應
  （★**六處**同批〔原稿誤記四處、實碼核實為六〕：①函式名改九可發語意 ②計數斷言 6→9
  ③期望陣列收成四保留碼 ④`matrix()` 補三列 sample ⑤`issuable_witness` 窮舉臂補三臂（不補＝
  編譯紅）⑥`witness_aligns_matrix_and_excludes_no_variant_codes` 內**第二份** `no_variant`
  陣列同步——漏一即編譯紅或恆綠）。
- **FR-024**: 新變體 HTTP 映射 MUST 落 `_ => StatusCode::OK` 臂（1000／2222／3333／7777／8888
  皆 HTTP 200）；僅 `4040`→404、`5003`→403（非 2xx 會吞信封、3333 配 401 則自動 refresh 靜默
  失效）。B-047：build() MUST 新增第二道 `method_not_allowed_fallback` 回 `AppError::NotFound`
  （現有 path fallback 不動、兩道並存＋與 metric layer 掛載次序須明寫）；★該 API 於 axum
  0.8.9 之存在性離線未證——plan 第一步 MUST 容器內最小樣本驗（含「只對已註冊路由生效」次序
  約束），證偽則回 BACKLOG B-047 候選②（憲法例外集加註）重拍。動詞探測閘 MUST 永遠裸掛
  router（碼註同時釘 contract.rs 與 router.rs）。

**wire 契約與 i18n（K1-25＋§I.3＋B-030）**

- **FR-025**: msg key MUST：固定變體鍵沿 rev4（`auth.login.failed`／`auth.token.expired`／
  `auth.session.kicked`；既有 `auth.session.reLogin`＝8888 現行鍵不動、★勿漏）；Biz 構造點鍵
  走 `biz.auth.{notSupported,captchaRequired,locked}`（後兩者為 rev5 對 rev4 `auth.login.*` 的
  命名正規化——前端 captcha 軟區判斷式拿 msg 字面比對區分兩態、須用新名）。Biz 三新鍵不在
  Lint24 抽取面**之內**（★原稿誤記為「不在抽取面」——實碼核實該閘抽三面：①`Biz`／`BizData`
  構造點字面 ②名冊常數間接形 ③`error.rs` 之 `fn key()` match 臂），故三個 Biz 鍵 MUST 以
  `Cow::Borrowed("字面")` 構造——**非字面即 fail-loud**（防恆綠洞）；msg-dict 兩語鍵集閘與
  contract case 逐鍵斷言為補強、非唯一守。
- **FR-026**: i18n 前端轉譯（★BASE-WEB-I18N-WIRING 三用途、甲案 rev4 全形）MUST：(i) request
  層 modal content＋showErrorMsg 鏈改走 `translateBackendMsg`（`$t(\`backend.${msg}\`, msg)`
  原文 fallback、detail 值連帶轉譯）／(ii) en-us.ts＋zh-cn.ts 插 backend 樹（22 鍵＝既有 16＋
  本刀 6；簡中照 rev4 鏡像重打字消化）＋zh-tw.ts 補 6 鍵（rev5 新檔免軌道）／(iii) app.d.ts
  backend **必填**型節（zh-cn 結構同步由必填型節＋pnpm typecheck 免費守）。`MSG_DICT_LOCALES`
  維持兩支不擴；en-us backend 樹一插即解除 `DAY1_EXEMPTIONS["gen.msg_dict"]`（同 commit 拔項
  ＋跑 generate；插入行形 MUST 為整行 `backend: {`——謂詞 fullmatch；拔項後空表安全先驗）。

**前端接線（.env ADAPT 軌道）**

- **FR-027**: `.env` 三處 ADAPT 改動 MUST（§III.1 射程含 `.env*`、§II #2 明寫「ADAPT 軌道」＝
  零修憲）：①`.env` `VITE_HTTP_PROXY=Y→N`／②`.env.test`（dev 實載此檔）`VITE_SERVICE_BASE_URL`
  apifox mock→`/api`＋`.env.prod` 同步拆 mock（dev/prod 同形）／③`.env`
  `VITE_AUTH_ROUTE_MODE=static→dynamic`（不翻則 /route/* 三端點前端永不呼叫、交付價值空轉）。
  .env 在 fork-delta-lint 射程外＝機器不守，MUST 手寫 `# [rev5-inline BASE-WEB-ADAPT] 原行:…`
  標記＋review 把關、ADR 記已知態；BACKLOG 立「lint 射程擴 .env*＋build/」條目。翻 N 後 22081
  直連 `/api` 必 404、唯一入口 http://127.0.0.1:22080（curl 與瀏覽器鎖同一 origin；記 quickstart）。

**憲法 Amendment（★ 軌道首開＋§I.7 首批行為島，1.2.0→1.3.0）**

- **FR-028**: 本刀第一件事 MUST 為憲法 Amendment（走 §V.2：ADR draft→user 親決→accepted＋憲法
  段＋bump 1.3.0＋docs-sync generate），★軌道未開之前不得動任何 base-web fork 既有檔。四條
  ★ 軌道：`★BASE-WEB-LOGIN-CAPTCHA-WIRING`（本刀僅 (i) captcha 軟區、(ii) 延改密刀）／
  `★BASE-WEB-AUTH-WIRING` 三用途（(a) constant routes 合併 1 行／(b) 三表單 stub／(c) captcha
  hook）／`★BASE-WEB-I18N-WIRING` 三用途（見 FR-026）／`★BASE-WEB-LOGOUT-UX-WIRING` 僅 (i)
  （user-avatar.vue 3 行＋fetchLogout wrapper 免軌道新檔）。用途 (a) 為必需非選配（seed
  constant=TRUE 為 0 列、取代清空登入頁）。
- **FR-029**: §I.7 五座行為島（token rotation／single-session／denylist 撤銷／idle 逾時／登入
  失敗節流）之不變式與 fail-* 方向 MUST 同筆 MINOR 入 §I.7（否則 §IV 第 9 題當場擋、日後 fail
  方向反轉無 MAJOR 閘）；不牽動版號（軌道與行為島同屬 MINOR、仍 1.3.0）。同批 ADR 面：★軌道
  ＋§I.7 Amendment、AppState 五欄翻案、ADR 0021 §3 收窄（app.d.ts backend 型節本刀提前）、
  B-047 4040 解讀、R7～R11 已知態集。

**★ 軌道逐處登記（憲法 §III.2 必需三欄：位置＋改動內容＋upstream 衝突風險評估）**

風險判準（可覆算，以基線 `fork260509-soybean-admin-base@example` 為量測面）：**高**＝該檔近 12 月
commit ≥5；**中**＝近 12 月 1–4 或近 24 月 ≥5；**低**＝近 12 月 0 且近 24 月 ≤4。**修改型再 +1 級**
（衝突塊必然與 upstream 行交錯）、純新增型不加級。量測日＝2026-08-09。

| 位置（檔案） | 軌道·用途 | 型別 | 改動內容 | 12m／24m | 風險 |
|---|---|---|---|---|---|
| `.env`（2 處） | ADAPT（非 ★） | 修改型 | `VITE_AUTH_ROUTE_MODE` static→dynamic；`VITE_HTTP_PROXY` Y→N | 0／5 | 高 |
| `.env.test`（1 處） | ADAPT（非 ★） | 修改型 | `VITE_SERVICE_BASE_URL` apifox mock→`/api` | 0／0 | 中 |
| `.env.prod`（1 處） | ADAPT（非 ★） | 修改型 | 同上（dev/prod 同形） | 0／0 | 中 |
| `src/store/modules/route/index.ts`（1 處） | `★BASE-WEB-AUTH-WIRING(a)` | 修改型 | `addConstantRoutes(data)`→併入 static 常量集 | 0／7 | 高 |
| `src/store/modules/auth/index.ts` | `★BASE-WEB-LOGIN-CAPTCHA-WIRING(i)` | 修改型 | login 簽名加 captcha 參＋失敗 msg 回傳鏈 | 1／7 | 高 |
| `src/views/_builtin/login/modules/pwd-login.vue` | `★BASE-WEB-LOGIN-CAPTCHA-WIRING(i)` | 修改型＋新增型 | 軟區條件渲染塊（新增型圈界）＋提交鏈接線（修改型） | 0／4 | 中 |
| `.../login/modules/code-login.vue`（2 處） | `★BASE-WEB-AUTH-WIRING(b)` | 修改型 | import stub wrapper＋消滅假成功 toast | 0／2 | 中 |
| `.../login/modules/register.vue`（2 處） | `★BASE-WEB-AUTH-WIRING(b)` | 修改型 | 同上 | 0／2 | 中 |
| `.../login/modules/reset-pwd.vue`（2 處） | `★BASE-WEB-AUTH-WIRING(b)` | 修改型 | 同上 | 0／2 | 中 |
| `src/hooks/business/captcha.ts`（4 處） | `★BASE-WEB-AUTH-WIRING(c)` | 修改型 | 改打 `/auth/sendCaptcha` stub、移除假延遲與假成功 | 0／1 | 中 |
| `.../global-header/components/user-avatar.vue`（3 處） | `★BASE-WEB-LOGOUT-UX-WIRING(i)` | 修改型 | `onPositiveClick` 改 async＋登出前 best-effort `fetchLogout` | 0／0 | 中 |
| `src/service/request/index.ts`（2 處＋1 塊） | `★BASE-WEB-I18N-WIRING(i)` | 修改型＋新增型 | modal `content` 與 `showErrorMsg` 鏈改走轉譯（修改型）＋`translateBackendMsg`／`translateDetailValue`（新增型圈界） | 0／4 | 中 |
| `src/typings/app.d.ts`（1 處） | `★BASE-WEB-I18N-WIRING(iii)` | 修改型 | `App.I18n.Schema` 補 `backend` 必填型節 | **15／32** | **高** |
| `src/locales/langs/en-us.ts`（1 塊） | `★BASE-WEB-I18N-WIRING(ii)` | 新增型 | 插 backend 樹 22 鍵 | **16／38** | **高** |
| `src/locales/langs/zh-cn.ts`（1 塊） | `★BASE-WEB-I18N-WIRING(ii)` | 新增型 | 插 backend 樹 22 鍵（簡中） | **17／39** | **高** |

**★ 本表最重要的一件事**：i18n 三檔（`app.d.ts`／`en-us.ts`／`zh-cn.ts`）是**基線最熱的三個檔**
（近 12 月各 15–17 個 commit），而 R2 甲案正是要動它們——這反向印證 ADR 0021 當初「`app.d.ts` 等
upstream 熱檔零 fork-delta（rebase 衝突面不擴）」的顧慮；本刀提前吃下該面，代價已知並入帳
（rev4 走過同路：I18N-WIRING 127 處，故有先例但風險等級誠實標高）。

**rebase 處置**（全表通則，承 §III「rebase 同步紀律」）：修改型一律以 `原行:` 註解為基準重放語意，
並**同步更新 `原行:` 為 upstream 現行版**（防對照基準過時）；純新增型整塊搬移、不與 upstream 行
交錯。i18n 三檔的高風險處置另加：rebase 時先比對 upstream 是否已自行新增 `backend` 節或改動
`Schema` 型別結構，若是則本刀 inline 改為對齊而非疊加。

★逐處明細（每處的精確行號與 `原行:` 逐字）由實作期各任務的 fork-delta 標記逐處落地並受
`fork-delta-lint` 機器強制（憲法 §III「全 repo grep `rev5-inline` 即得完整 patch set」）；本表為
**檔級**風險評估與 rebase 處置索引，處數為現階段估值、實作期以標記實數為準。

**機器強制（fork-delta-lint 軌道名名冊）**

- **FR-030**: fork-delta-lint MUST 加「軌道名 ∈ 授權名冊」斷言：名冊源＝Amendment 於 §III.2
  新建的**機器可解表格**（掃描錨＝表格列 `^\|` 起、跳標題／分隔列、剝 `**`；名冊＝§III.2 ★軌道
  ∪ §III.1 三軌道；★順序相依：Amendment 先定表格形、lint 斷言後落）。射程僅修改型（帶 `原行:`）
  標記、並順手強制修改型同行必含 `[rev5-inline` token；新增型 `NAME+` 不入冊（ADR 0021 款 1、
  既有 `BACKEND-MSG-DICT+` 天然豁免）。正規化規則：★ 必帶、全名不縮寫、用途後綴 `(x)` 必帶且
  ∈ 該軌道授權用途集。
- **FR-031**: 名冊斷言 MUST fail-loud＋非 vacuous：首次跨界讀 `.specify/memory/constitution.md`
  ——檔缺席／名冊掃空＝die（絕不退空名冊全放行）；self-test 加成對樣本（名冊內過／名冊外攔）
  ＋**兩條**非空斷言（名冊整體非空 ＋ §III.2 ★段貢獻列數 ≥4——單一條不足：§III.2 表若被刪或掃描
  錨打錯，§III.1 三名仍在、名冊仍非空而整段失守）＋「承襲指針散文中**本刀不開的兩名**
  （`MODAL-WIRING`／`BASE-WEB-DEVPROXY-WIRING`）不在名冊」反例（★原稿誤記「六名」——Amendment
  後六名中四名正式在冊，該反例必然不成立）；
  既有 self-test 名冊外合成名（UI／DEP）須同批改造；結構性 vacuous 護欄＝自證含「真 repo 至少
  一修改型對象被檢查」（現況 base-web vs 基線僅三新增檔＝今日實掃修改型對象為零）。

**依賴與汰換**

- **FR-032**: AppState MUST 由兩欄→五欄（加 `cache: Option<SessionCache>`／`jwt: JwtConfig`／
  `captcha_secret: String`；測試 None、production 恆 Some、boot 建連失敗即 fail-loud panic）；
  state.rs「恰兩欄」拍板須立 ADR、檔頭拍板註同批改寫。六新 crate 全需釘版（argon2 0.5.3／
  captcha 1.0.0／hex 0.4.3／jsonwebtoken 10.4.0 ★必帶 rust_crypto feature／redis 1.3.0／
  sha2 0.10.9、沿 rev4 釘版 spec 期雙源核對）；root Cargo.toml「不引 argon2」舊拍板翻案記 ADR。
  config.rs 新讀六鍵（APP_JWT_JWT_SECRET／REFRESH_TOKEN_SECRET／ISS／AUD／REDIS_URL／
  CAPTCHA_SECRET，compose 皆已接）。
- **FR-033**: `auth/dev_identity.rs` MUST 整檔汰換（K1-27 解除、release profile 首次可跑）；
  enforce.rs 接點僅一處 cfg verify 收斂成真驗章、連帶清 `Bearer dev-super` 測試面。順手收
  B-050（`roles_of_user` 次段查詢 DbErr 機器守）＋B-051（test_kit 遷 facade/mod.rs——門檻「第
  三消費者」須至少一支新 facade 測試真用 `test_kit::FailingConn` 驗 DbErr、寫成任務非順手
  重構）。

**觀測面（obs.rs pre-register 接續契約）**

- **FR-034**: 本刀的靜默降級與安全事件 MUST 雙軌可觀測——①**結構化** tracing warn（帶 target
  ＋欄位，非純訊息字串：無欄位即無從機器守門）②Prometheus 計數器。序列面＝本刀真有發射點者
  三支：`throttle_degraded_total`（label＝降級來源，本刀實有源集含設定鍵退預設與 captcha 標記
  失敗等）／`denylist_hit_total`（label＝redis｜pg，redis 降級退 PG 的唯一可觀測訊號）／
  `throttle_soft_zone_total`（無 label、軟區命中）。三支 MUST 依 `obs.rs` 既有紀律做**啟動即
  顯式註冊 0**（防「事件未發生」與「序列缺席」混淆致 rate() 失去基線），且 label 值集與發射點
  同步（發射點新增字面即補註冊表）。rev4 的 HLL 廣度估計兩支（`throttle_hll_*`）不在本刀。
  守門走計數器 render 文本比對（沿 obs.rs 現有測試形）；不新建 log 捕捉層測試設施。

### Key Entities *(include if feature involves data)*

- **sys_token**（會話憑證狀態機、001 baseline 9 欄）：id／created_at／created_by（擁有者 uid）／
  status（active｜rotated｜revoked）／token_hash（SHA-256、UNIQUE）／rotation_chain（＝sid＝
  會話身分）／issued_at／expires_at／used_at；partial UNIQUE `WHERE status='active'` 保證同鏈
  至多一 active；**無 last_activity 欄**（idle 依賴 redis）。
- **session_event**（append-only 稽核、001 baseline 8 欄變體 B）：記 kicked／reuse／idle／logout
  事件；source_ip 為 varchar(45)；created_by 為操作者 uid（kicked=被踢對象／logout=本人）。
- **sys_login_attempt**（節流權威、001 baseline 11 欄）：real_ip（INET NOT NULL）／peer_ip／
  x_forwarded_for／ip_confidence／success／attempted_user_name／…；帳號維滑動窗計數源。
- **sys_user**（001 baseline）：session_policy（varchar20 default 'inherit'、值域 single｜multi｜
  inherit）／session_id（varchar36 nullable）；三 seed 帳號密碼皆 argon2id PHC（明文 `123456`、
  共用同一 hash）。
- **sys_menu → MenuRoute**（dynamic 選單來源）：78 列 seed、constant=TRUE 為 0 列；經
  `to_menu_route` 映射為前端 `MenuRoute`（id 字串／meta 17 欄）。
- **CaptchaClaims**（無狀態簽題，非 DB）：nonce／user_name／exp／ans_mac；HS256 簽於
  `APP_CAPTCHA_SECRET`；nonce used 標記住 redis。
- **redis 承載態**（非 DB、fail-* 各異）：denylist（reason=kicked｜revoked、TTL=refresh 全壽命）／
  last_activity（idle 時鐘）／rotate-grace（`session:rotate-grace:{token_hash}`＝新對 JSON、
  TTL＝30 秒）／captcha nonce used（SET NX、TTL=captcha exp）。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 端到端可見——三 seed 帳號（密碼 `123456`）分別登入，側邊欄呈現三種不同的角色化
  選單；getUserInfo 四欄型別逐欄對齊 typings（userId 字串／userName＝nick_name）。
- **SC-002**: token rotation 往返——access 過期回 `3333`→自動 refresh 得新對→原請求重放成功；
  同票兩並發斷言一 rotate 一走 grace 回同一對且不觸 reuse；rotated+grace miss 才判 reuse。
- **SC-003**: 撤銷矩陣全數正確——logout 後舊 token 得 `8888`（且對垃圾 token 冪等 `0000`）；
  single-session on 時二次登入使前一條得 `7777`；被踢者 (access,refresh) 窗內換發仍 `7777`
  （denylist TTL＝refresh 全壽命）；redis 缺 denylist 的 revoked 列靜默 `8888` 不落假 reuse。
- **SC-004**: 節流三區全數正確——<2 自由／2–4 `captchaRequired`／≥5 `locked`；軟區與鎖定皆
  argon2 前擋、零稽核列零計數桶（以「拒絕後成功登入仍可」證明不消耗桶）；成功／unlock 重置窗。
  ★正向可測斷言（FR-004 第⑩步之資料來源）：連續失敗 N 次（N＜captcha_after）後，該帳號窗內
  `success=false` 列數恰為 N；★軟區拒絕後再數一次，列數**不變**（證明零計數桶）。
- **SC-005**: captcha 全數正確——任意 userName（含不存在）發題、userName 超限 `1000`、產圖失敗
  `5000`、答對密碼錯自動換題、答錯不推進鎖定但該題作廢、nonce 重放第二次拒；**兩層降級各一案**
  ：redis 整體不可用→軟區要求停用且密碼錯仍計數／單次標記寫入瞬斷→拒但計數桶不進。
- **SC-006**: dynamic 選單全數正確——getUserRoutes 樹依角色 Casbin 過濾、home 兜底非 404；
  getConstantRoutes 濾 constant=TRUE（現 `[]`）、前端合併保留 5 條 builtin 常量路由。
- **SC-007**: 替代登入四流程恆 `2222 biz.auth.notSupported`、三表單無假成功 toast；i18n 三語
  backend 樹鍵集相等（22 鍵）、UI 顯人話（zh-CN 簡中／en-US 英文）、7777 modal 顯人話非裸鍵。
- **SC-008**: 碼表與契約自證——碼表 9 可發＋4 保留＝13、`issuable_*` 斷言**六處**一致；method 不符
  回 `4040`＋HTTP 404、動詞探測閘裸掛自證在案；3333／7777 映射 HTTP 200 自證；refresh 驗章失
  敗→8888 紅綠測；contract case 4→16、雙向覆蓋閘無缺 case／殭屍 case（四支同形 stub 有區別
  手法）；denylist TTL 兩 reason 皆 refresh_secs 自證。
- **SC-009**: 憲法與機器守——Amendment bump 1.3.0（四 ★ 軌道＋§I.7 五座島）；fork-delta-lint
  名冊斷言非 vacuous（名冊空集 die、§III.2 ★段列數 ≥4、承襲指針**不開兩名**反例、真 repo 至少
  一修改型對象被檢查、既有
  BACKEND-MSG-DICT+ 不誤攔）；gen.msg_dict 豁免拔項＋backend-msg-dict.md 首次生成。
- **SC-010**: 靜默降級變得看得見——三類降級（設定鍵缺失退預設／redis 不可用退資料庫／節流軟區
  命中）各有獨立可量測訊號，且服務啟動後即帶基線值（不因「事件尚未發生」而整條訊號缺席，
  否則趨勢與告警都算不出來）；三類各至少一案觸發後訊號遞增可被斷言，降級記錄帶可機器判讀的
  欄位（非純文字訊息）。
- **SC-011**: DoD 鏈全綠——`cargo test --workspace --test-threads=1` 全綠（redis 測試鍵 uniq
  前綴隔離、X-Real-IP 顯式注入）；`pnpm typecheck` 綠（app.d.ts 必填型節後 zh-cn 結構受守）；
  fork-delta-lint 綠；release profile 起得動；手動端到端七項通過（入口 http://127.0.0.1:22080）。

## Assumptions

- **grace 窗長度＝30 秒**（Clarify 定案、rev5 對 rev4 差異點）：rev4=10s 小於 rev5 前端最壞換發
  間隔約 11s（1s promise 快取＋10s 單請求 timeout）故不沿用。不變式＝**grace 窗 MUST > 前端最壞
  換發間隔**（前端 timeout 設定若變更須重算此值）。
- **home 多角色收斂律＝沿 rev4 已驗證規則**（Clarify 定案）：啟用角色（status=1）依 role id
  升冪、取首個非空 `role_home`，全空→預設 `home`；規則由碼註釘住＋一支合成多角色測試守
  （seed 三角色 role_home 同值＝'home'、機器測不出分歧）。
- **TTL 公式**已升為規範（FR-004 第⑥步逐字載明），本節不再重述——沿 rev4 且 plan 期複核完成。
- **ip_confidence 字面**＝`nginx_peer`（snake_case、rev5 新字面）；B-019 接手時與 rev4 七態合併
  治理。
- **captcha 產圖 crate**＝`captcha 1.0.0`（rev4 釘版）；rev5 CaptchaClaims 單語境不設 ctx 欄
  （rev4 有 ctx 欄做跨語境隔離——未來開第二語境需 additive 加欄並同步簽驗兩端）。題目有效期
  ＝300 秒（沿 rev4；nonce used 標記 TTL 同值，確保「題失效前重放必被擋」）。
- **wire fixture**：LoginToken／UserInfo／MenuRoute／UserRoute／ElegantConstRoute 已在 002 快照
  內（TYPINGS_GLOB 全 api 目錄）；真正新增＝captcha 形，靠新檔 `rev5-auth.d.ts` 入快照。
- **seed 密碼明文＝`123456`**（已離線 argon2 verify MATCH、＝upstream demo 值、三帳共用同一
  PHC）；single-session 驗收前置＝先以 `updateSystemSetting` 翻 `single_session_default=on`
  （001 凍結 seed 是 schema-gate gate2 比對左源、不可動）。
- **登入頁三顆快速登入鈕保留**（Clarify 定案；rev4 亦保留）：帳密字面（Super／Admin／User＋
  123456）正好對上 seed，本刀零 inline、不占軌道用途，手動驗收一鍵切三帳號。★已知態＝該鈕
  暴露 dev seed 帳密，轉 prod 前必須拆除——ADR 記已知態＋BACKLOG 新條目綁 prod 硬化刀。
- **實作紀律引用**（非本 spec 新拍板）：rev4 對應碼先讀後寫、重打字消化、註解一律重寫（憲法
  §I.5＋ADR 0019）；rust build／test 容器內全程 serial、`--test-threads=1`（載
  specs/002-system-settings/quickstart.md）；redis dev 與測試共用 DB 0＝測試鍵 uniq 前綴隔離。
- **stakeholder 判定承 001／002 前例**：本刀 stakeholder＝admin 後台使用者與 workspace 維護者；
  spec 中的端點路徑／碼／casbin 政策座標／軌道名／閘名稱係交付物座標（WHAT），非實作技術選型
  （HOW）；「容器內 serial」「cargo test 形」等屬憲法與 CLAUDE.md 既定紀律引用。

### Out of Scope

- **per-IP 節流／信任錨**（B-019）：request_context 僅留原樣轉錄欄；ip_* 三鍵無消費者；nginx
  其餘 8 條端點無 limit_req＝已知態。
- **改密／建帳號端點**（B-021）：password_* 八鍵無消費者、`biz.user.passwordViolation.*` 八白
  名單鍵維持後端不發；LOGIN-CAPTCHA 用途 (ii)（formRules 放寬）延此刀。
- **自助頁手機驗證從零建頁**（B-022 第四流程）：條目續留、本刀僅三表單 stub 化。
- **管理頁 view UI**（B-008）：本刀不建 view；四張管理頁的後端寫端不在本刀。
- **`/auth/error` demo 端點**（B-053）：base-web fork 原版兩張 demo 頁
  （`views/function/request/index.vue`／`views/alova/request/index.vue`）經
  `fetchCustomBackendError(code, msg)` 打 `GET /auth/error`——本刀 ROUTES 16 條**不含**此端點。
  依憲法 §I.1「『v1 從簡』只能是交付排程、不能簡化設計範圍」，此為**排程延後**（B-053 承載）、
  非設計範圍縮減；★延後理由非工期而是**拍板級衝突**：該端點契約＝回吐 client 任意 `code`／`msg`，
  而 demo 字面含保留碼 `9999`（「後端從不發出」由 `error.rs` 兩處 `no_variant` 陣列＋
  `envelope.rs` 之 `compile_fail` doctest 三錨釘死）、`msg` 又是已在地化人話（違 §I.3「msg 載
  穩定 i18n key」且破 `contracts/msg-keys.md` 的 13＋9＝22 算術）⇒ 兌現須先走 §I.3 Amendment。
  已知態：`.env` 翻 `/api`＋`dynamic` 後 R_SUPER 側邊欄可見該兩頁、其按鈕點擊得 `4040`＋
  `system.notFound` 信封（前端顯「找不到請求的資源」）＝user 可見已知態。
- **★MODAL-WIRING／★DEVPROXY-WIRING**：本刀不開（DEVPROXY 由 nginx 前置拓樸取代、
  `VITE_HTTP_PROXY=N` 後 vite proxy 無消費者）。
- **redis AOF 持久化**：不開＝已知態（暴險受 status 即權威封頂）；prod 化由 B-019／部署刀重評。
- **稽核管理頁 x_forwarded_for 渲染轉義**：入庫已截斷剝控制字元、渲染端轉義隨稽核 UI 刀。
- **prod 資產／base-web prod build**：release「可跑」僅指 rust-api profile；base-web 無 prod
  build target。
