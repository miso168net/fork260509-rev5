# Feature Specification: 007 使用者＋密碼管理（島 I 入憲、授權下放＋no-escalation）

**Feature Branch**: `007-user-password-admin`

**Created**: 2026-08-26

**Status**: Draft

**Input**: User description: "docs/brainstorms/007-user-password-admin.md"（階段 0 brainstorm 定稿〔2026-08-25
五路偵查 workflow＋二階彙總後撰寫〕＋§3 四十一題 AskUserQuestion 逐輪親決＋§3b grilling 十八題親決〔2026-08-26、
frontier 已空〕；本 spec 之唯一輸入。射程權威＝brainstorm §2；rev4 對應碼＝實作預設藍本、清單於 plan research
凍結（ADR 0019）；乙類硬前置 B-126 已先於本刀關帳（ADR 0062）、本刀自乾淨基線 9bd26bc 長出）

> 摘要：把 rev5 第一個 user 域寫端家族從「seed 有政策列、碼與 UI 全無」做成真功能——**管理面十支端點＋自助改密
> 二支＝12 支**（ROUTES 49→61；seed 政策列 100% 預埋、**零 migration、零 seed 變更**），前後端同刀、CDP 三方
> 對照驗收。本刀新拍板七件：**寫端授權可下放給多層管理員並以角色集包含規則守門（no-escalation、rev5 新增
> 島 I7）**、**斷權三腿**（停用／刪除／重設同交易撤全部 session＋refresh 鎖內重驗＋踢除分鍵 7777）、**密碼政策
> 單一驗證點＋明細通道**（八鍵生效、違規逐條下發、登入路徑不驗）、**設密冷卻與改密舊密節流**、**自助路由白名單**
> 帶回、**軟刪硬刪指派＋復原零回灌**、**登入表單規則降 required-only**（B-089 結案）。憲法一次 MINOR
> v1.8.0→v1.9.0：§I.7 第九座行為島（島 I 使用者域治理、六條）＋§III.2 三用途 (v)(vi)(vii)；ADR 五支草案。
> 同分支順路關帳 BACKLOG 十三條（甲類 8＋丙類 5）、三條 demo 條文更新。

## Clarifications

### Session 2026-08-25（brainstorm 四十一題親決；全紀錄見 brainstorm §3）

- Q01 射程主幹？→ A: **管理面十支＋changePassword＋getPasswordPolicy**；profile／email 驗證不進（撞 ADR 0041）。
- Q02 首登強制改密？→ A: **本刀不做**；custody 表只借時戳；立 B-134。
- Q03 UI 射程？→ A: **照 rev4 as-built 全套形**（抽屜、回收桶 toggle、操作下拉、解鎖 modal、產密浮層、gating）。
- Q05 migration？→ A: **零 migration**（全射程在 001 基線內）。
- Q06／Q07 憲法？→ A: **§I.7 新島 I＋§III.2 (v)(vi)(vii) 三用途一次 MINOR 1.8.0→1.9.0**；名單當場定數。
- Q09／Q09-1／Q09-2／Q28 授權面？→ A: **下放寫端給 R_ADMIN＋實作 no-escalation**（user 親決、非建議項）；
  載體＝seed 不動、運行期由超管以 006 授權 UI 勾給角色；七動作全可下放、守門＝角色集包含規則；掛點＝handler
  鎖內具名守門、middleware 四參掛點續留恆 Ok、ADR 0022 不翻。
- Q10 按鈕 gating？→ A: **七碼逐鈕 gating**（B-099 形）；判準「該頁 menu 維政策是否僅 R_SUPER」、記為既有拍板之例外釋義。
- Q11／Q12／Q13 seed 保護／kick 射程／撤銷範圍？→ A: 三帳號不可刪、Super 恆禁停用與解超管指派、self 不得
  刪／停用／踢／改自身指派；self 禁踢、Super 可踢、停用可踢、已刪不可；撤該 uid 全部 active、不動 rotated。
- Q14／Q15 失效碼與即時性？→ A: kick→7777、停用／刪除／重設→8888；**同交易撤全部 active＋refresh 鎖內重驗**；
  顯式復核 ADR 0059。
- Q16 軟刪指派／restore？→ A: **同交易硬刪指派、復原零回灌、status 保留**（B-025① 結案）。
- Q18／Q19／Q20／Q21 密碼面？→ A: 整套承襲 rev4:ADR 0054；**開 BizData 明細通道、射程嚴限密碼二鍵**；設密冷卻
  (標的,操作者) 對、借 custody 時戳、一體適用；changePassword Authed 零 seed、五步序、成功撤他 session 保留當前。
- Q22 自助頁可達？→ A: **帶回 SELF_SERVICE_ROUTES 碼內白名單**（承 rev4:ADR 0065）。
- Q23／Q24 seed 68 與 unlock？→ A: updateUserSessionPolicy 端點＋抽屜三值；unlock 入口＝user 頁頁首 modal 雙維、
  ADR 0042 措辭訂正。
- Q25／Q26 B-089 與前端規則？→ A: **登入表單 pwd／userName 降 required-only、不動 reg.ts**（用途 (vii)）；
  getPasswordPolicy＋動態 rules、抽屜只掛 hint。
- Q27 B-093？→ A: ①指派寫端 commit 後 reload；RELOAD_CALL_FILES 擴一檔。
- Q30 改密舊密節流？→ A: 做：argon2 前掛點、per-user 桶、fail-open、碼內常數門檻。
- Q31～Q35 UI 形？→ A: 回收桶 toggle、不加刪除時間欄、產密浮層承襲、user-center 只掛改密卡、只舊密碼一路。
- Q36～Q41 順路與 demo？→ A: B-129／B-132／B-128①②／B-098 新型裁判納入；B-029 不納；B-018／B-053／B-064
  只動條文（已落帳）。

### Session 2026-08-26（grilling 十八題親決；全紀錄見 brainstorm §3b）

- G1 標的角色集 T？→ A: **T＝全部指派列（不濾角色 status）、A＝操作者現役角色**。
- G2 同級互管？→ A: **允許**（零特例）。
- G3／G25 self？→ A: 非角色欄可改、`status`／`roleIds` 出現即拒、sessionPolicy 可改；**self 不得用 resetUserPassword
  重設自己**（五不）。
- G4／G5 批刪與軟刪標的？→ A: 任一違規整批 rollback、純 key 不指筆；已軟刪一律 `biz.user.notFound`。
- G6 unlockLogin？→ A: 帳號維套 T ⊆ A、IP 維不套。
- G7／G8 前端？→ A: 非超管 sessionPolicy 欄 disabled＋提示；**前端不預判包含規則、全靠後端 5003**（user 親決）。
- G9／G10 事件與稽核？→ A: 新 denylist reason `admin_kick`→7777＋新鍵 `auth.session.kickedByAdmin`；
  自助改密 reason `password_changed`＋稽核第三新值 `change_password`。
- G12／G13／G14 密碼面常數？→ A: 節流滑動窗 5 次／15 分鐘、純 key、窗自癒；custody 只 upsert；addUser 計入冷卻。
- G16／G17 欄位？→ A: 信箱／手機皆選填、信箱簡式格式＋活性唯一預檢、手機只驗長度；預設啟用、允許零角色。
- G23 詞彙六條入活書 §12；G24 被下放者可復原前超管（零回灌下無升權）。

### Session 2026-08-26（/speckit-clarify）

- Q: 持有 R_SUPER 的操作者，包含規則 T ⊆ A ∧ N ⊆ A 要怎麼對他成立？（seed 之 Super 只持 {R_SUPER}，字面規則下連編輯
  Admin 都 5003；brainstorm「超管因角色集最大自然不受限」前提不成立）→ A: **持 R_SUPER 者之 A 定義為全集**——規則本體
  不變、零特例分支；超管對任何標的、任何指派恆過；seed 保護與 self 五不仍先判。
- Q: 改密舊密節流因 redis 不可用而 fail-open、以及包含規則拒絕（5003），要不要進既有觀測面？→ A: **節流降級進既有
  `throttle_degraded_total` 新增一個 source（改密節流專用）、值集 12→13 同批改預註冊清單與活書複驗清單；5003 拒絕只記
  warn 日誌（操作者與標的 id、不含角色差集）、不另立序列**。
- Q: 編輯使用者時送出的角色集（roleIds）是「期望全集、全量替換」還是「增量 add／remove」？→ A: **期望全集、全量替換**——缺席＝不動
  （三態）、帶陣列＝寫後角色集 N 恰等於該陣列（去重；含不存在或已軟刪之角色 id → 拒、非靜默跳過）、空陣列＝全撤；差集導出
  硬刪＋新增同交易、稽核一列 `update`；與現值相同＝no-op。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 超管使用者管理全套（列表／新增／編輯／刪除／回收桶） (Priority: P1)

超級管理員在使用者管理頁看到現役使用者列表（含角色、狀態、會話政策、記事、審計欄），可新增帳號（帳號名、
初始密碼〔手輸或隨機產生〕、暱稱、性別、手機、信箱、狀態、角色、記事）、編輯既有帳號（帳號名不可改；會話政策僅
編輯模式）、單筆或批次軟刪、切到回收桶看已刪帳號並復原——復原後帳號零角色、須重新指派。所有寫入同交易落
操作稽核，拒因以人話 toast 顯示。

**Why this priority**: 本刀的本體；rev5 至今使用者只能靠 seed 三帳號，沒有任何運行期帳號治理能力；甲類八條
BACKLOG 中五條的觸發器就是「user 寫端存在」。

**Independent Test**: 以 Super 登入→新增帳號 alice（指派 R_USER）→以 alice 登入成功→編輯 alice 改暱稱與角色
→軟刪 alice→alice 既有 session 下一次請求即失效→回收桶復原 alice→alice 角色欄空白、以原密碼可登入但無任何
管理頁。

**Acceptance Scenarios**:

1. **Given** Super 已登入、seed 三帳號存在，**When** 新增帳號（帳號名唯一、密碼合規），**Then** 回應 0000、列表
   出現新列（status 預設啟用、角色可為空）、稽核一列 `add`；重複帳號名→`biz.user.userNameExists`；重複信箱
   （不分大小寫、僅現役列）→`biz.user.userEmailExists`。
2. **Given** 編輯抽屜開啟，**When** 提交含 `userName` 的請求，**Then** 出現即拒（純 key）；**When** 沒改任何值
   按確定，**Then** 零寫入零稽核（值 diff 判定）；**When** 只改暱稱，**Then** 同交易寫入＋稽核 `update`。
3. **Given** 使用者 X 持 R_USER 且有 2 個 active session，**When** Super 軟刪 X，**Then** 同交易：X 標記軟刪、
   X 的全部角色指派列硬刪、X 的全部 active 票撤銷、事件 `revoked／user_deleted`、稽核 `delete`；X 下一次請求
   得 8888。
4. **Given** 批刪集合含一筆 seed 帳號或 self，**When** 提交，**Then** 整批拒（純 key）、零變更；空陣列＝提前
   no-op 成功。
5. **Given** 回收桶含已刪 X，**When** 復原，**Then** 鎖內重驗「同帳號名／同信箱無現役列」後清除軟刪標記；復原
   後 X 角色為空、status 為刪除前原值；UI 確認框明示「復原後需重新指派角色」；稽核 `restore`。
6. **Given** 已刪 X，**When** 對 X 呼叫編輯／踢除／重設密碼／會話政策／刪除，**Then** 一律 `biz.user.notFound`。

---

### User Story 2 - 斷權：踢除／停用／刪除／重設密碼即刻失效 (Priority: P1)

管理員對某帳號按「踢除下線」，該帳號所有裝置的既有登入立即失效、對方看到「此工作階段已被管理員結束，請重新
登入」的提示（可立即重登）；停用、刪除、重設密碼三種動作同樣即刻撤銷對方全部登入，但對方只看到「請重新登入」、
再登入時得到與帳密錯誤無差別的回應（不洩漏帳號被動過）。

**Why this priority**: 沒有斷權的使用者管理是假的——現況下被停用者可持續刷新票、Authed 端點照放行。

**Independent Test**: 以 alice 在兩個瀏覽器登入→Super 踢除 alice→兩邊下一次請求皆 7777 modal→alice 重登成功；
Super 停用 alice→alice 兩邊皆 8888、重登得 1000、refresh 票亦失效；Super 重設 alice 密碼→同 8888、以新密碼
可登入。

**Acceptance Scenarios**:

1. **Given** alice 有 N 個 active 票（含 rotated 歷史列），**When** 踢除，**Then** N 個 active 全撤、rotated 列
   不動（重放仍走 reuse 偵測）；事件 `revoked／admin_kick`；denylist reason `admin_kick`；alice 下一次請求
   7777＋`auth.session.kickedByAdmin`；單一會話頂替的既有 7777 文案 `auth.session.kicked` 不變。
2. **Given** alice 啟用，**When** 停用（status→2），**Then** 同交易撤全部 active＋事件 `user_disabled`；commit 後
   best-effort 寫 denylist（`revoked`、TTL＝refresh 全壽命）；alice 的 refresh 請求在鎖內重驗活性後拒；再登入
   得 1000。
3. **Given** alice 啟用，**When** 重設密碼，**Then** 同上但 reason `password_reset`；以新密碼登入成功。
4. **Given** self，**When** 踢除自己，**Then** 拒（純 key）；**Given** 已刪帳號，**When** 踢除，**Then** `notFound`；
   **Given** 停用帳號，**When** 踢除，**Then** 允許（殘留 session 清乾淨）。
5. **Given** ADR 0059（logout 呈遞 rotated 票靜默 no-op），**Then** 本刀不改其行為、ADR 明列復核結論。

---

### User Story 3 - 密碼政策與自助改密 (Priority: P1)

系統設定頁的八把密碼政策鍵（最小／最大長度、四類字元要求、禁含帳號名、設密冷卻秒數）自本刀起生效：管理員
設初始密碼／重設密碼、使用者在個人中心自助改密，三條路徑走同一個驗證點；不合規時逐條告知「少了哪幾條」。
自助改密須驗舊密碼、新舊不得相同，成功後本人其他裝置登入失效、當前裝置保留；猜舊密碼超過 5 次／15 分鐘
被暫時拒絕。登入路徑永不驗政策（seed 帳號 123456 仍可登入）。

**Why this priority**: 密碼面是「設得進、登不進」缺陷的根；八鍵上架已久卻零消費者；B-021／B-020／B-089 觸發器
皆在此成立。

**Independent Test**: 設定頁把最小長度調 12→新增帳號給 11 字密碼→2222＋明細列出「至少 12 字元」；alice 進
個人中心改密（舊密正確、新密合規）→成功、另一瀏覽器的 alice 8888、當前保留；alice 連猜錯舊密 6 次→第 6 次
起 `biz.user.changePasswordThrottled`、15 分鐘後或改密成功後解除。

**Acceptance Scenarios**:

1. **Given** 政策 min 8／require_digit on，**When** 設密 `abcdefgh`，**Then** 2222＋`biz.user.passwordPolicy`
   攜 `violations:["requireDigit"]`（違規碼＝前端內部詞彙表八鍵尾段、全部違規一次收集）；密碼明文與雜湊
   不出現於回應、稽核、日誌。
2. **Given** 政策 forbid_username on，**When** 密碼與帳號名大小寫不敏感相等，**Then** 拒；**Given** 密碼 >512
   bytes，**Then** 拒（字元數＋位元組數雙約束）。
3. **Given** alice 登入中，**When** 自助改密（兩次一致→舊密正確→新≠舊→政策），**Then** 成功、`revoke_others_of_user`
   保留當前 sid、事件 `revoked／password_changed`、稽核 `change_password`；任一步失敗即該步拒因、零寫入。
4. **Given** Super 於 T0 重設 alice 密碼，**When** T0＋30s 再重設（interval=60），**Then** 2222＋
   `biz.user.pwdSetTooFrequent{remainingSeconds:30}`；另一管理員同時重設不受限（維度＝(標的,操作者) 對）；
   interval=0 即停用冷卻；addUser 初始密碼同計入。
5. **Given** 任何角色登入者，**When** GET getPasswordPolicy，**Then** 回七鍵投影（不含 interval）；個人中心改密卡
   依之產生即時規則；取不到時靜默降 required、後端仍是唯一裁判。
6. **Given** seed 三帳號密碼 6 字元＜min 8，**When** 登入，**Then** 成功（登入路徑不驗政策）。

---

### User Story 4 - 授權下放給多層管理員＋no-escalation (Priority: P2)

超級管理員用 006 的端點授權與按鈕授權 modal，把使用者管理的部分寫端（例如編輯、重設密碼）與對應按鈕碼授給
R_ADMIN。被授權的 R_ADMIN 進使用者管理頁只看到被授的按鈕；對任何「持有自己沒有的角色」的帳號（例如超管）
操作，或試圖指派自己沒有的角色，一律被拒——規則對所有角色一體適用，持 R_SUPER 者之角色集視為全集故恆過。預設 seed
不動（寫端仍 super-only），多層管理員是可開關的能力、不是預設態。

**Why this priority**: user 親決的 scope 擴張（B-024① 自此落地）；沒有它，manage_user 這張唯一非超管可達的
管理頁對 R_ADMIN 只是「有鈕無權」。

**Independent Test**: Super 以 006 UI 把 updateUser 端點＋`user:edit` 授給 R_ADMIN（seed 已有）、再授 deleteUser
＋`user:delete`→Admin 登入：可編輯持 {R_ADMIN} 的帳號、刪除持 {R_ADMIN} 的同級；對 Super（持 R_SUPER）編輯
→5003；把某帳號指派 R_SUPER→5003；把 R_USER 指派給誰→5003（Admin 自己不持 R_USER）；Super 再授 Admin 一枚
R_USER→前述指派成功。

**Acceptance Scenarios**:

1. **Given** 操作者現役角色集 A、標的全部指派列 T、寫後角色集 N，**When** 任一使用者寫端（新增／編輯／刪除／
   批刪／復原／踢除／重設密碼／會話政策）與 unlockLogin 帳號維執行，**Then** 鎖內、寫入前判 `T ⊆ A ∧ N ⊆ A`，
   違者 5003（純 key、不洩漏差集）、零變更零稽核；持 R_SUPER 之操作者 A＝全集、恆過。
1b. **Given** Super（僅持 R_SUPER）與持 {R_ADMIN} 的帳號 Y，**When** Super 編輯 Y 並指派 R_USER，**Then** 成功（A＝全集；
   若照字面 A＝{R_SUPER} 則會誤拒——本案為包含規則的正向守門）。
2. **Given** 標的 X 持有的 R_SUPER 角色被暫時停用，**When** 持 {R_ADMIN} 者編輯 X，**Then** 仍 5003（T 不濾
   角色狀態）；**Given** 操作者持有的某角色被停用，**Then** 該角色不計入 A。
3. **Given** 持 {R_ADMIN} 的甲與乙，**When** 甲停用／刪除／踢除乙，**Then** 允許（同級互管）、稽核記甲。
4. **Given** 回收桶中曾持 R_SUPER 的 X（指派列已硬刪、T＝∅），**When** 持 {R_ADMIN} 且被授 restoreUser 者復原
   X，**Then** 允許，X 復原後零角色。
5. **Given** updateUserSessionPolicy 為受保護端點，**When** 超管試圖授予 R_ADMIN，**Then** 006 既有封死整批拒
   （結構性）；非超管的編輯抽屜中會話政策欄顯示現值但 disabled＋提示「僅超級管理員可改」。
6. **Given** R_ADMIN 被授 `user:delete` 按鈕碼但未被授 deleteUser 端點，**Then** 鈕可見、按下 5003（誠實）；反之
   端點有、鈕無→鈕不見、API 可達（兩鍵各自獨立、由超管一併治理）。
7. **Given** 前端不預判規則，**When** R_ADMIN 開編輯抽屜，**Then** 角色下拉全列（含 R_SUPER）、勾選送出得 5003
   toast；列級操作鈕只依按鈕碼顯隱。

---

### User Story 5 - 解鎖登入、會話政策、記事欄 (Priority: P2)

使用者管理頁頁首的「解鎖登入」鈕開一個小視窗：選維度（帳號／來源 IP）、輸入帳號名或 IP，送出即解除登入失敗
節流鎖。編輯抽屜可把該帳號的會話政策設為 inherit／single／multi（僅超管；改為 single 不即時踢、下次登入才
生效）。記事欄（memo）在列表純文字顯示、抽屜多行編輯——B-003 最後一張表關帳。

**Why this priority**: 三者皆是 seed 已錨定的能力（`user:unlock`、seed 68、`user_memo` 欄）零消費者的收尾。

**Independent Test**: 以錯密登入 alice 至帳號維鎖定→Super 頁首解鎖（帳號維、alice）→alice 可登入；Super 設
alice 會話政策 single→alice 兩處登入、第二處頂掉第一處（7777、既有文案）；記事欄寫入→列表顯示、下拉／引用處不帶。

**Acceptance Scenarios**:

1. **Given** alice 帳號維鎖定，**When** 解鎖（dimension=user）→**Then** 0000、稽核 `unlock`（既有）；R_ADMIN 被授
   unlockLogin 而 alice 持 R_SUPER→5003（帳號維套包含規則）；IP 維不套。
2. **Given** 抽屜編輯模式，**When** 會話政策未變，**Then** 不發第二支呼叫；**When** 改為 single／multi／inherit，
   **Then** 寫端三值收斂、值域外→2222；稽核 `update`。
3. **Given** memo 含 HTML 字面，**Then** 列表以純文字插值顯示（零原始 HTML）。

---

### User Story 6 - 登入頁規則放寬與順路修復 (Priority: P3)

管理員替 bob 設了含特殊字元、超過 18 字元的合規密碼後，bob 在登入頁能直接送出並成功登入（現況會被前端正則
擋下、零請求、誤導為「格式不正確」）。同分支順手修好：三顆授權 modal 換角色殘影（B-129）、menu 頁回收桶每頁
殘留 100（B-132）、前端 .ts 驗證假綠（B-128 ①②）。

**Why this priority**: B-089 一旦寫端進場即成真缺陷（user 可見）；順路三條與本刀共用範式、邊際成本近零。

**Independent Test**: Super 設 bob 密碼 `P@ssw0rd!2026-long`→bob 登入頁輸入後直送、0000；role 頁連續開兩個角色
的授權 modal 無殘影；menu 頁切回收桶每頁顯示 10。

**Acceptance Scenarios**:

1. **Given** 登入表單，**When** 輸入任意非空密碼與帳號，**Then** 前端只驗必填、格式判定交後端；register／reset-pwd
   兩支 stub 不動。
2. **Given** B-129，**When** 換角色開授權 modal，**Then** 起手清空前一角色勾選與鎖定、首頁請求帶世代。
3. **Given** B-132，**When** menu 頁切到回收桶，**Then** 每頁大小重置為 10（只動 menu 頁；user 頁治理清單帶參、
   結構性不重現）。

---

### Edge Cases

- **seed 帳號結構保護**：id 1／2／3 不可刪（批刪含之整批拒）；Super（id 1）恆禁停用、恆禁解除其超管指派；
  拒因純 key（`seededProtected` 家族）。
- **self 五不**：self 不得刪／停用／踢／改自身指派／用管理頁重設自己密碼；self 可改自己的非角色欄與會話政策；
  前端自己那列 `status`／`roleIds` 控制項 disabled、操作下拉不列重設密碼。
- **超管的 A＝全集**：持 R_SUPER 者對任何標的／指派恆過包含規則（seed Super 只持 R_SUPER、字面集合不成立故明訂）；
  其餘角色照字面。
- **停用中的角色**：計入標的 T、不計入操作者 A；停用角色的指派列不硬刪（只有軟刪使用者才硬刪指派）。
- **零角色帳號**：可建立、可登入；只得常量路由＋個人中心（自助白名單）；N＝∅ 恆滿足包含規則。
- **前超管復原**：回收桶中 T＝∅ ⇒ 任何被授 restore 者可復原；復原後零角色；要回超管須持 R_SUPER 者指派。
- **併發**：同一標的兩個寫端於 per-user advisory 鎖序列化、lock-then-redecide；addUser 無 uid 豁免鎖；固定鎖序
  advisory(uid)→sys_user 列→sys_role 列升序→sys_user_role；advisory key 沿用 login 之 uid 鍵（同用途擴消費者、
  ADR 記核過）。
- **信箱唯一性**：不分大小寫、僅現役列；已刪列同信箱與現役並存合法；復原時鎖內重驗兩腿（帳號名／信箱）撞則
  專屬拒因。
- **空字串欄**：新增時空字串→NULL；編輯走三態（缺席＝不動、null＝清空、值＝設值）。
- **roleIds 含界外 id**：不存在或已軟刪之角色 id → 整筆拒（純 key、非 orphan skip——與 006 授權 modal 對選單維的 orphan
  skip 不同形：角色是指派的主體、不是候選集過濾）。
- **值域**：status 二值收斂（1 啟用、其餘停用；不加 CHECK）；session_policy 三值（inherit／single／multi、
  值域外 2222）；user_name 形制 `^[A-Za-z0-9_-]{1,64}$`；密碼 ≤512 bytes。
- **冷卻邊界**：interval=0 停用；剩餘秒數下取整；不同操作者互不影響；custody 只做 upsert、不做「自改→全刪」。
- **改密節流 fail-open**：redis 不可用時不計數、不拒（島 E 同向）；成功改密即清桶；無解鎖端點（窗自癒）。
- **denylist best-effort**：commit 後寫入失敗只記警告、PG 為權威（refresh 鎖內重驗兜底）。
- **7777 分鍵**：`admin_kick` 與 `kicked` 各自文案；`revoked` 8888 靜默；三者不互換（島 C）。
- **request context 缺席**：寫端稽核來源不可得 ⇒ 拒寫 5000（F3①）。
- **已知態（必明記）**：`manage_user-detail` 續為 LookForward 佔位（seed 對賬故不可刪檔）；個人中心三卡留白；
  語言兩語（zh-tw 只補 backend 樹）；B-064 三顆快速登入鈕本刀期間必留；B-008 餘兩張死項續留（CDP 排除清單）。
- **rev4 as-built 瑕疵不照抄**：改密卡 `verify.*` 假 radio、`deletedAt` 孤兒鍵、`scroll-x` 未隨欄寬改、跨頁借鍵。
- **測試殘列與序列**：sys_user／sys_user_role 不在 schema-gate runtime-append 收窄集 ⇒ gate2 逐列全等；addUser
  走 nextval 必配業務鍵腿＋seq 還原（setval 3）；custody 首寫配 RAII 清理腿；CDP 走查排 schema-gate 驗收之後。

## Requirements *(mandatory)*

### Functional Requirements

#### A. 端點與契約總則

- **FR-001**: 本刀 MUST 新增恰 12 支端點：管理面十支 path×method 逐字對齊 001 凍結 seed 政策列（getUserList／
  getDeletedUsers／addUser／updateUser／deleteUser／batchDeleteUser／restoreUser／kickUser／resetUserPassword／
  updateUserSessionPolicy；零新 seed、零 migration）＋自助二支 `/userCenter/changePassword`（POST）、
  `/userCenter/getPasswordPolicy`（GET）採 Authed 授權態（登入即可用、零 casbin 列）；路由註冊表條數常數同
  commit 對齊（49→61）、受政策管制端點計數 35→45。
- **FR-002**: 授權態照 seed：十支 Policy 全 R_SUPER（getUserList 另 R_ADMIN）、updateUserSessionPolicy protected=TRUE；
  deleteUser／batchDeleteUser 用 DELETE 動詞（動詞不符→4040）。既有 unlockLogin 由本刀接 UI、端點不改。
- **FR-003**: 使用者鍵 MUST 一律 `id`；標的與操作者皆以 id 識別；changePassword 標的恆＝登入者本人（不信任 body id）。
- **FR-004**: 業務拒因 MUST 為純 i18n key、一因一鍵；**唯二例外**＝`biz.user.passwordPolicy{violations[]}` 與
  `biz.user.pwdSetTooFrequent{remainingSeconds}` 走新增之攜參明細通道（2222）；5003 授權拒絕恆純 key；不得新增
  錯誤碼（13 碼矩陣不動）。
- **FR-005**: 寫端操作稽核 MUST 與業務寫入同一交易；稽核詞彙 MUST 新增小寫三值 `kick`／`reset_password`／
  `change_password`（其餘沿 `add`／`update`／`delete`／`restore`／`unlock`）；payload 只含 `{id,user_name}`、
  MUST NOT 含密碼明文或雜湊；請求上下文缺席 MUST 拒寫 5000。
  > ★**2026-08-30 勘誤（收刀前 final holistic；改文件不改碼）**：「payload 只含 `{id,user_name}`」的射程係
  > **本刀新增的三值** `kick`／`reset_password`／`change_password`（brainstorm G10 原句即掛在該三值之後，
  > spec 抄寫時脫落了限定、data-model §1.5 再複製一次）。as-built 這一側才對——`add`／`update`／`delete`／
  > `restore`／`updateUserSessionPolicy` 五支落的是 `audit_json` 十五欄白名單（部分再加 roles），沿 role／menu
  > 兩域既有慣例，且 `delete`／`update` 的 before/after 快照是 `sys_user_role` 硬刪後的**唯一留痕**，改成兩欄
  > 反而毀掉稽核價值。★安全面的 MUST NOT 未被違反：`audit_json` 型別上無 `password`／`session_id` 欄，
  > 機器釘＝`audit_json_is_a_whitelist_without_password_or_session_id`（含 `$argon2` 字面不出現的負向斷言）。
- **FR-006**: 分頁列表（getUserList／getDeletedUsers）MUST 採共用分頁信封；現役列表穩定排序 `id ASC`、回收桶
  `deleted_at DESC, id DESC`；治理清單 MUST 帶參（不依賴後端預設頁大小）。
- **FR-007**: 共用 handler 件（audit_operator／json_or_default／tristate／blank_to_none／db_status_to_wire／
  resolve_operator_names／MAX_CURRENT）MUST 引用共用模組零拷貝；wire→DB 二值映射 MUST 收攏為單一共用函式
  （B-127：role／menu 兩份改 import、user 為第三消費者）。

#### B. 使用者寫端語意

- **FR-008**: addUser MUST 收帳號名（形制守門、現役唯一）、初始密碼（走政策、走冷卻、寫 custody）、暱稱、性別、
  手機（選填、≤32）、信箱（選填、簡式格式、現役唯一不分大小寫）、狀態（預設啟用）、角色集（可空）、記事；
  空字串→NULL；密碼雜湊於鎖前計算。
- **FR-009**: updateUser MUST 採部分更新三態（缺席＝不動、null＝清空、值＝設值）；`userName` 出現即拒；no-op
  判準＝先全缺席早退、再值 diff（零變更＝零寫入零稽核）；`roleIds` 為**期望全集、全量替換**語意（缺席＝不動；陣列＝
  寫後角色集恰等於之、去重、含不存在或已軟刪角色 id 則拒非跳過；空陣列＝全撤；差集導出硬刪＋新增同交易）；角色集
  實際變更 commit 後 MUST 觸發判定面同步。
- **FR-010**: deleteUser／batchDeleteUser MUST 於鎖內依序判 seed 保護→self→no-escalation，通過後同交易：軟刪
  （成對 deleted_at／deleted_by）→硬刪該使用者全部角色指派列→撤銷全部 active 票→事件 `revoked／user_deleted`；
  批刪任一違規整批 rollback、拒因純 key 不指筆、空陣列提前 no-op。
- **FR-011**: restoreUser MUST 鎖已刪列→鎖內重驗同帳號名／同信箱無現役列（撞則專屬拒因）→成對清除軟刪標記；
  MUST NOT 回灌角色指派（復原後零角色）；status 保留刪除前原值。
- **FR-012**: 對已軟刪標的之 updateUser／kickUser／resetUserPassword／updateUserSessionPolicy／deleteUser MUST
  一律回 `biz.user.notFound`（活性判準＝未軟刪）；只有 restoreUser 認得已刪列。
- **FR-013**: seed 帳號結構保護 MUST 為碼內常數形：id 1／2／3 不可刪；id 1 恆禁停用、恆禁解除超管指派。self
  五不：不得刪／停用／踢／改自身指派／以 resetUserPassword 重設自己（各配純 key 拒因）；self 可改非角色欄與
  會話政策。
- **FR-014**: updateUserSessionPolicy MUST 三值收斂（inherit／single／multi、值域外 2222）；改為 single MUST NOT
  即時踢除（下次登入才生效）；對已刪標的 `notFound`。
- **FR-015**: 記事欄（user_memo）MUST 於列表純文字插值顯示、抽屜多行編輯；MUST NOT 出現在下拉／引用／對外 API。

#### C. 授權下放與 no-escalation（島 I7）

- **FR-016**: 寫端授權 MUST 可由超管在運行期以既有授權治理 UI 授予其他角色（端點維＋按鈕碼各自獨立）；seed 政策列
  MUST NOT 改動（預設仍 super-only）。
- **FR-017**: 八支使用者寫端（addUser／updateUser／deleteUser／batchDeleteUser／restoreUser／kickUser／
  resetUserPassword／updateUserSessionPolicy）與 unlockLogin 帳號維 MUST 於 per-user 鎖內、任何寫入前判包含規則：
  `A`＝操作者現役角色集（濾軟刪與停用角色、DB-fresh；**★持 R_SUPER 者之 A 視為全集**）、`T`＝標的全部指派列（不濾角色
  狀態）、`N`＝寫後標的角色集；
  MUST `T ⊆ A ∧ N ⊆ A`，違者 5003 純 key、零變更零稽核、MUST 記一筆 warn 日誌（操作者 id、標的 id、端點；不含角色
  差集）、不新增觀測序列；seed 保護與 self 五不先於本規則判定；同級互管允許；unlockLogin IP 維不套。
- **FR-018**: 判定 MUST 以具名純函式單點實作、八支寫端＋unlock 共用；middleware 既有四參掛點續留恆放行（一般
  上限位）；ADR MUST 寫明兩實作位射程分工（不翻 ADR 0022 決定 3）。
- **FR-019**: 受保護端點（updateUserSessionPolicy）MUST 維持 006 結構性封死（不可授非超管）；前端非超管編輯抽屜之
  會話政策欄 MUST 顯示現值但 disabled＋提示，MUST NOT 發出必敗呼叫。
- **FR-020**: 前端 MUST NOT 預判包含規則（角色下拉全列、列級鈕只依按鈕碼顯隱）；後端為唯一裁判。
- **FR-021**: 每支受規則約束的寫端 MUST 至少配兩案負向測：被授權之 R_ADMIN 對持 R_SUPER 標的仍 5003、指派超出
  自身角色集仍 5003（測內以資料列 grant、測後清理）；另配一案正向：Super（僅持 R_SUPER）對持其未持角色之標的成功
  （A＝全集非 vacuous）。

#### D. 斷權＝踢除與撤銷兩形之合稱（島 I2）

- **FR-022**: 停用（status→2）／刪除／重設密碼 MUST 同交易撤銷標的全部 active 票（rotated 列不動）＋寫事件
  `revoked`（reason `user_disabled`／`user_deleted`／`password_reset`）；commit 後 best-effort 寫 denylist
  （reason `revoked`、TTL＝refresh 全壽命）；被撤者下一次請求 8888、再登入得 1000 三態收斂。
- **FR-023**: kickUser MUST 同形但事件 reason `admin_kick`、denylist reason `admin_kick`（新值）→7777＋新鍵
  `auth.session.kickedByAdmin`；既有單一會話 `kicked`／`auth.session.kicked` 文案 MUST NOT 變；kick 射程＝self 禁、
  Super 可（受 FR-017）、停用可、已刪 `notFound`。
- **FR-024**: refresh MUST 於鎖內重驗使用者活性（啟用且未軟刪），不活即拒；MUST NOT 每請求查活性（Authed 端點與
  getUserInfo 沿 003 不判 status）；此為 003 token 狀態機新增判定腿、非 fail 方向反轉，ADR 明列；ADR 0059
  行為不變、復核結論入 ADR。
- **FR-025**: changePassword 成功 MUST 撤銷本人其他 active 票、保留當前；事件 reason `password_changed`；稽核
  `change_password`。

#### E. 密碼政策、冷卻、節流、自助改密（島 I5）

- **FR-026**: 密碼政策 MUST 以單一驗證點承載並消費八鍵（單快照讀、缺鍵 fail-default）：字元數 min／max、位元組
  ≤512、四類字元要求、禁含帳號名（大小寫不敏感相等）；MUST 收集全部違規一次回；密碼三重不洩（回應／稽核／
  日誌）；addUser 初始密碼／resetUserPassword／changePassword 三入口 MUST 共用；**登入路徑 MUST NOT 驗政策**。
  > ★**2026-08-30 勘誤（收刀前 final holistic；改文件不改碼）**：「消費**八**鍵」中的八係**違規碼**數而非
  > 設定鍵數——`password::PASSWORD_POLICY_KEYS` 恰 **7** 個（min_length／max_length／require_digit／
  > require_lowercase／require_uppercase／require_special／forbid_username），第八個違規碼 `maxBytes`（≤512）
  > 是**碼內常數、不是設定鍵**（見 FR-027 的違規碼八枚清單）。★`password_change_min_interval` 亦**不在**
  > 本清單（碼註逐字：它是端點固有規則、判定位不同，混進來會讓「政策違規」與「設得太頻繁」共用同一條
  > 驗證路徑）。活書兩處同源失準已同批訂正為「七個設定鍵」。
- **FR-027**: 違規明細 MUST 經攜參通道下發：`biz.user.passwordPolicy{violations:[code…]}`，違規碼逐字＝前端內部
  詞彙表八鍵尾段（minLength／maxLength／maxBytes／requireDigit／requireLowercase／requireUppercase／
  requireSpecial／forbidUsername）。
- **FR-028**: 設密冷卻 MUST 讀 `password_change_min_interval`（0＝停用）、維度＝(標的 id, 操作者 id)、以
  `sys_pwd_custody` 該對之 created_at 為上次設密時間（只 upsert、不刪他列）；未滿→2222＋
  `biz.user.pwdSetTooFrequent{remainingSeconds}`；一體適用零豁免；addUser 初始密碼同計入。
- **FR-029**: changePassword MUST 依序判：帳號存在→兩次一致→舊密正確→新≠舊→政策；任一步拒即零寫入；成功後
  FR-025。
- **FR-030**: 改密舊密節流 MUST 於舊密驗證（雜湊比對）之前判 per-user 滑動窗 5 次／15 分鐘、第 6 次起
  `biz.user.changePasswordThrottled`（純 key）；成功改密即清；redis 不可用 fail-open **且 MUST 計入既有節流降級序列
  之新 source（改密節流專用；值集 12→13、boot 預註冊、活書觀測面清單與複驗法同批更新）**；門檻為碼內常數；桶鍵與
  登入節流分離；無解鎖端點。
- **FR-031**: getPasswordPolicy MUST 回七鍵投影（不含 interval）、Authed；前端改密卡據以產生即時規則、取不到靜默
  降必填；抽屜設密欄只掛提示文字。

#### F. 自助頁可達性

- **FR-032**: getUserRoutes MUST 於授權過濾後恆併入碼內常數自助路由白名單（現含 user-center）；白名單 MUST 只收
  「受眾＝本人」的自助頁、RBAC 資源頁禁入；seed 之 R_SUPER user-center 政策列保留；單測 MUST 覆蓋「零 menu 政策
  角色仍得自助路由」與「白名單外路由不受影響」。

#### G. B-093 閉合與鎖序（島 I1）

- **FR-033**: 角色指派寫端 commit 後 MUST 觸發判定面同步（Applied 即觸發、不問 diff）——觸發源恰二：updateUser
  之角色集**實際變更**、deleteUser／batchDeleteUser 之硬刪指派（清判定面殘留）；其餘寫端零觸發（restore 零回灌）；
  reload 呼叫者名冊 MUST 擴一檔且漏擴即紅；ADR 0053 觸發矩陣補一列。
- **FR-034**: 使用者域寫端 MUST 進 per-user advisory 鎖（自 login 上提為共用、addUser 豁免）；固定鎖序＝
  advisory(uid)→sys_user 列→sys_role 列升序→sys_user_role；lock-then-redecide；advisory key space 沿用 login 之
  uid 鍵，ADR 明寫核過（H1）。

#### H. 前端

- **FR-035**: 使用者管理頁 MUST 接真：列表（角色、狀態、會話政策、記事、審計欄）、搜尋、抽屜新增／編輯（帳號名
  編輯模式 disabled；密碼僅新增＋隨機產密鈕＋提示；會話政策僅編輯）、單刪／批刪、回收桶 toggle（切兩資料源、
  已刪模式隱搜尋卡、操作欄換復原、不加刪除時間欄）、列上操作下拉收納踢除／重設密碼／隨機密碼、頁首解鎖 modal
  （帳號維／IP 維、顯式帶維度）；`scroll-x` 隨欄寬總和同批改。
- **FR-036**: 七枚按鈕碼 MUST 逐鈕 gating（外層保底＋顯隱兩層）；spec 判準＝「該頁 menu 維政策非僅 R_SUPER」；
  role／menu 頁不 gating 之既有拍板不變（ADR 記為例外釋義）。
- **FR-037**: 個人中心 MUST 改寫為真頁、只掛「修改密碼」卡（舊密碼一路、無信箱／手機 radio、規則來自 FR-031）；
  其餘卡位留白；入口沿既有頭像下拉。
- **FR-038**: 登入表單 pwd／userName MUST 降為必填、不動全域正則；register／reset-pwd stub 不動。
- **FR-039**: 前端接真形 MUST 照三頁既有慣例：status `'1'|'2'`、`createdAt／createdBy`、拒因經 `translateBackendMsg`、
  鍵 `id`；管理頁零原始 HTML 插值；新 wire 型 i64 欄掛守衛序列化；新命名空間 `Api.UserAdmin.*`／`Api.UserCenter.*`
  每 definition 配裁判（正向≥1、反例≥1）、快照重抽。
- **FR-040**: i18n MUST：`page.manage.user.*` 兩語鍵集相等、新 top-level `page.userCenter.*`、產密 `page.manage.user.
  pwdGen.*`、`backend.biz.user.*` 新鍵三檔同批、新 7777 鍵兩語；zh-tw 只補 backend 樹、語言下拉不變。
- **FR-041**: 順路 MUST：B-129（三顆授權 modal 起手清空＋首頁請求世代）先修再讓 user 抽屜照抄；B-132（menu 頁切
  回收桶重置每頁大小）；B-128 ①②（前端 .ts 驗證改指 oxlint＋RUNBOOK 一段）；`Api.IpRule.*` 七支不補（B-098 留帳）。

#### I. 治理與簿記

- **FR-042**: 憲法 MUST 一次 MINOR v1.8.0→v1.9.0：§I.7 新島 I 六條（I1 寫端鎖序／I2 斷權即時性與分碼不互換／I3
  seed 帳號與自身結構保護／I4 軟刪硬刪指派＋復原零回灌／I5 密碼政策單一驗證點＋登入不驗／I7 no-escalation
  包含規則；條文只凍結方向面、常數留活書）＋§III.2 三用途 (v) user 管理頁（index.vue＋user-operate-drawer.vue
  修改型＋兩語 locale＋app.d.ts）、(vi) 個人中心改密（user-center/index.vue 修改型＋page.userCenter 命名空間＋
  password-card.vue／產密元件具名）、(vii) 登入表單規則放寬（pwd-login.vue）；B-129 走 (iii) 補完、B-132 走 (ii)
  補完、皆免 bump；Amendment 提案 MUST 於 plan 前成稿、user 親審。
- **FR-043**: ADR MUST 五支（草案）：①島 I 行為承載＋no-escalation 掛點射程分工＋gating 例外釋義；②BizData 明細
  通道（澄清 ADR 0022 §2② 之誤、結 B-024③）；③自助路由白名單（承 rev4:ADR 0065）；④設密冷卻＋改密節流；
  ⑤ADR 0042 第 2 項措辭訂正＋ADR 0053 矩陣補列。accepted 後 body 不可變。
- **FR-044**: BACKLOG MUST 於收刀關帳：B-003／B-021／B-024／B-025①／B-089／B-093／B-113／B-127／B-129／B-128／
  B-132（B-020 視通用 seam 是否做；B-098 續留）；B-113 探針列處置＝種合成候選外 protected 列、升真 assert；
  勘誤 NOTES「seed 68（manage_user view）」與「六件→七件」。
- **FR-045**: 活書 as-built MUST 落 §5（模組拓樸）、§6（斷權與密碼序）、§8（授權慣例）＋附屬文件 FORK-DELTA-WIRING.md
  （三用途接線）；撞頂即依 ADR 0062 輕量軌下放；詞彙六條入 §12。

#### J. 測試與紀律

- **FR-046**: TDD、rust 全程容器內 serial；每單元 pin bump；rust 碼完工前容器內格式化；review agent 只讀；絕不 push／merge。
- **FR-047**: 測試設施 MUST：UserCleanup 補業務鍵腿＋op-log 腿＋seq 還原；custody 首寫配 RAII 清理腿（入不入
  runtime-append 收窄集實作期判）；seed 三帳號測試掛既有 seed op-log 守衛；endpoint 測試帶真 connect-info；
  fault-injection 用既有 seam。
- **FR-048**: fork-delta：修改型標記僅出現於「FR-042 三用途 (v)(vi)(vii) 檔集 ∪ 順路補完檔集」——後者＝FR-041 之
  B-129 三顆授權 modal（既有用途 (iii)）與 B-132 之 `menu/index.vue`（既有用途 (ii)），合計既有檔 8 支
  （`user-search.vue` 兩向 diff 零改動則不入）；
  新檔照 `[rev5-inline <軌道>+ 007]` 檔頭；模板側原行註解多行形；路由外掛產物零重算（不新增 view 目錄）。
- **FR-049**: CDP 三方對照（22080 vs 42080）MUST 逐項：列表／抽屜／回收桶／踢除（對方 7777 新文案）／重設密碼／
  解鎖 modal／gating（Super／Admin／User 三角色反覆切換）／個人中心改密卡／登入頁特殊字元密碼可登入；已知態列
  排除清單；起手先清 localStorage、走查排 schema-gate 之後；下放情境走查前先以 006 UI 授權 R_ADMIN（起手腳本）。
- **FR-050**: 收刀 MUST 依 RUNBOOK §12.1 實測 pre-commit 一筆；零 migration 兌現＝migration 目錄兩支不變、schema-gate
  三閘綠。

### Key Entities *(include if feature involves data)*

- **使用者（sys_user）**: 帳號名（現役唯一、不可改）、密碼雜湊、暱稱、性別、手機、信箱（現役唯一不分大小寫）、
  狀態（1 啟用／其餘停用）、會話政策（inherit／single／multi）、當前會話 id、記事、審計四欄、軟刪成對欄。
- **角色指派（sys_user_role）**: 使用者×角色 join；軟刪使用者時硬刪、復原零回灌；標的角色集 T 的來源。
- **密碼經手（sys_pwd_custody）**: (標的, 操作者) 對之上次設密時間；本刀只作冷卻時戳（upsert）、不做經手判定。
- **密碼政策（八鍵）**: 系統設定表中的 password_* 鍵；七鍵投影對外可讀、interval 只供冷卻。
- **會話與斷權面**: sys_token 票（active／rotated／revoked）、session_event（新事件 `revoked`＋五 reason）、
  denylist（reason `kicked`／`admin_kick`／`revoked`）。
- **角色集 A／T／N（概念）**: 操作者現役角色集／標的全部指派列／寫後角色集；包含規則之三元。
- **自助路由白名單（概念）**: 碼內常數、登入即可達、受眾＝本人。
- **改密節流桶（概念）**: per-user 滑動窗計數、成功即清、fail-open。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 路由註冊表恰 61 條（具名常數 `ROUTES_COUNT`）、受政策管制端點恰 45（★無具名常數——驗收錨＝以 Super
  呼叫既有 `getAllEndpoints` 之回應長度實測）、與 seed 政策列 path×method 逐字對齊（機器對賬零漂移）；
  12 支新端點以 dev 帳號實測：Super 全通、Admin 對十支 Policy 端點除 getUserList 外皆 5003（seed 預設態）。
- **SC-002**: rust 測試總數自 829 淨增且全綠（容器內 serial、rc=0）；含：每支寫端兩案 no-escalation 負向、seed
  保護與 self 五不各一負向、批刪整批 rollback、斷權三腿（撤銷／denylist／refresh 重驗）、政策八鍵各一違規案＋
  三重不洩、冷卻邊界、節流第 6 次拒與 fail-open（含降級 source 計數）、自助白名單兩向、reload 名冊恰等、降級 source
  值集 13 成員測——負向自證逐項可示範。
- **SC-003**: CDP 三方對照逐項一致（FR-049 清單）；已知態逐項驗證其現狀；踢除情境對方 7777 新文案、停用情境
  對方 8888。
- **SC-004**: 零 migration 兌現：migration 目錄維持兩支；schema-gate 三閘綠；seed 零變更。
- **SC-005**: 憲法 v1.9.0（島 I 六條＋§III.2 三用途）；ADR 五支 accepted；lint 全綠（0 錯誤）；fork-delta 修改型
  標記僅出現於三用途檔集；活書配額不超（撞頂即下放）。
- **SC-006**: 包含規則非 vacuous：被授權 R_ADMIN 以 UI 可達路徑操作超管帳號必 5003；拆掉守門函式呼叫必有測試紅；
  停用中角色仍擋（T 不濾）。
- **SC-007**: 密碼面端到端：設定頁調政策後即時生效於三入口；違規明細逐條顯示；seed 帳號 123456 登入不受影響；
  含特殊字元與 >18 字元的密碼可自登入頁登入（B-089 結案）。
- **SC-008**: wire-schema 快照重抽後新命名空間全數有裁判；前端 typecheck 綠；.ts 驗證改指 oxlint 後無假綠。
- **SC-009**: FR-044 所列 BACKLOG 條目於收刀事件 `backlog_done` 關帳（B-020 視通用 seam 是否做而條件性關帳、
  B-025 只結①、B-098 續留不關帳）；B-113 條文更正已落；B-134 新立；三條 demo 條文已更新。
- **SC-010**: pre-commit 全鏈實測一筆（RUNBOOK §12.1）低於 ADR 0044 之 45s 警戒。

## Assumptions

- rev4 樹（`../fork260509-rev4/`）為唯讀活體藍本：spec 對應＝rev4:011-user-admin（rev4:FR-004／FR-007／FR-036／
  FR-043）、rev4:014-user-center（changePassword／getPasswordPolicy）、rev4:015-pwd-custody（只借冷卻拍板）、
  rev4:007-login-throttle（unlock）；ADR rev4:0006／0053／0054／0065；as-built 碼清單於 plan research 凍結
  （ADR 0019）；rev5 已明文推翻之行為不得帶回（brainstorm §9 差異點 23 列：清空語意三態、userName 出現即拒、
  拒因純 key 除二鍵、稽核小寫、real_ip 拒寫、denylist TTL、logout 單列、needChangePwd 不帶回、角色鍵 id、
  獨立 Api 命名空間、審計欄名、各頁自備 i18n、未知型 5000、unlock 維度必給、動詞不符 4040、scroll-x 不變式、
  B-129 先修、新檔標記形、首登強制不做）。
- 003～006 底座已兌現且本刀純消費：login 鏈 per-user 鎖與鎖內重驗、sys_token 撤銷家族、denylist 雙通道、
  unlockLogin 雙維、handler 共用件、rebuild-swap 判定面同步、006 端點／按鈕授權 modal（下放載體）、結構性封死
  謂詞、test_db 名冊；B-126 已關帳（活書餘裕 §5 20／§6 40／§8 77）。
- `sys_pwd_custody`、`user_memo`、`session_policy`、兩支活性唯一索引、八鍵皆在 001 基線；`schema-evolution.json` 空。
- 單副本部署（ADR 0014）；判定面同步不需跨副本；denylist best-effort、PG 為權威。
- dev 環境：容器內 build/test、serial；CDP 對照照 CLAUDE.md §7（dev 三帳號密碼 123456 仍在、B-064 三顆鈕本刀必留）。
- 「五前置三項本就要建、增量僅四樣」（005 §3 #4 原句）細目查無，以 §2 端點表重建 scope 論證。

### Out of Scope

- 首登強制改密整包（needChangePwd／硬閘／強制頁／router guard）——B-134。
- getProfile／updateProfile／信箱驗證與通知（mailer 域外、ADR 0041）；個人中心其餘三卡；改密卡信箱／手機驗證路徑。
- `manage_user-detail` 詳情頁（續留佔位）；批次復原；使用者匯入／匯出；列表排序能力（B-027 續掛）。
- 角色分級（rank）模型；前端預判包含規則（列級 disabled／選項過濾）；no-escalation 之 middleware 帶 body 改造。
- 會話政策改 single 的即時踢除；每請求活性判定。
- zh-TW 接 runtime（語言下拉三語）；`Api.IpRule.*` 七支補裁判（B-098）；captcha 產圖對抗（B-029）；`/auth/error`
  demo 端點（B-053、滯後卷）；快速登入鈕拆除（B-064，轉 prod 時）；alova 棧拆除（B-018）。
- 密碼歷史（不得重用最近 N 次）、密碼過期、帳號鎖定旗標等需 migration 之能力。
