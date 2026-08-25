# 007-user-password-admin — 使用者＋密碼管理（刀 B）

> 階段 0 brainstorm **定稿（2026-08-25）**。基準＝rev5-admin-root @ 6a748ef（B-126 收單）；pins
> rust-api=5d2d536／base-web=854a72e；憲法 v1.8.0；ROUTES 49／POLICY_ENDPOINT_COUNT 35；rust 測試 829；
> 零 migration（`schema-evolution.json` 空）。
> 偵查＝五路並行 workflow（rev5 後端／rev5 前端／rev4 後端／rev4 前端／治理與拍板面）＋二階彙總，
> 矛盾處回 repo 與 `../fork260509-rev4/`（唯讀）核對裁決；主線再逐項 grep 復核承載拍板的事實。
> ★41 題拍板已於 2026-08-25 以 AskUserQuestion 逐輪親決：★拍板級 18 題逐題（17 題取建議、
> **Q09 取「下放」非建議項**，其連動子題 Q09-1／Q09-2／Q28 同輪補決）、◇快答 23 題整批照建議。
> 決議總表見 §3；★2026-08-26 grilling 輪（grill-with-docs＋domain-modeling、AskUserQuestion 逐題）再親決 18 題
> （G1～G25、見 §3b；唯一非建議項＝G8 前端不預判包含規則），frontier 已空、共識已確認。
> 本檔自此為 speckit-specify 的直接輸入（specify 手動起手、不入自動流程）。
> 血緣：scope 預拍「全納入含 changePassword」承 [005-role-menu-crud.md](005-role-menu-crud.md) §3 #4
> 與 [006-authz-governance.md](006-authz-governance.md) §3 #4；seed 68 歸刀 B 承 006 §10-19。

## §0 地基：rev5 現況事實（只留與本刀決策相關者）

**資料面（001 基線、全在、零 migration）**：`sys_user` 十七欄——`status smallint` 可空零 CHECK
（碼層三處判準收斂為二值「1 啟用、其餘停用」）、`session_policy varchar(20) NOT NULL DEFAULT 'inherit'`
（值域僅碼層收斂、`login.rs::effective_single` 值域外 warn＋off）、`session_id`、`user_memo text`
（零消費者、B-003 餘項）、成對 `deleted_at`／`deleted_by`；兩支活性 partial-unique index
`sys_user_user_name_active_uniq (user_name) WHERE deleted_at IS NULL`、
`sys_user_user_email_active_uniq (lower(user_email)) WHERE deleted_at IS NULL AND user_email IS NOT NULL`
（`user_email` 全樹零消費者 ⇒ 本刀首個寫入者必撞 23505）；`sys_user_role` join 表；`sys_pwd_custody`
（PK `(user_id, created_by)`、零 FK、零寫入者、schema-gate「暫不入集」）；八把 `password_*` 設定鍵
seed 值 min 8／max 64／四支 require off／forbid_username off／change_min_interval 60
（`validation.rs::NUMBER_RANGES` 界 min [1,128]／max [1,256]／interval [0,86400]、0＝停用）。
★seed 三帳號密碼 `123456`＝6 字元＜min 8 ⇒ **密碼政策絕不可掛登入路徑**。

**seed 政策（`m002_baseline_seeds.rs` casbin 列、本刀零新列）**：端點十支全 R_SUPER——`getUserList GET`
（另 R_ADMIN 一列）、`addUser`、`updateUser`、`deleteUser DELETE`、`batchDeleteUser DELETE`、
`resetUserPassword`、`restoreUser`、`kickUser`、`getDeletedUsers GET`、`updateUserSessionPolicy`
（**唯一 protected=TRUE**、seed 68）；按鈕碼 R_SUPER 七枚 `user:add／edit／delete／reset-pwd／kick／
restore／unlock`、**R_ADMIN 僅 `user:edit`**；menu 維 `manage_user` R_SUPER＋R_ADMIN（＝seed 中唯一非超管
可達的管理頁）、`manage_user-detail` 同、`user-center` 僅 R_SUPER；`ptype='g'` 零列；
`changePassword／getProfile／updateProfile／getPasswordPolicy` 零列。

**後端底座（可複用）**：login 鏈 ④ `advisory_lock_user`＝`pg_advisory_xact_lock(uid)`（私有 fn）＋⑤ 鎖內
重驗 `status==Some(1) && deleted_at.is_none()`；`facade/sys_token.rs` 七支（`revoke_family`／
`revoke_others_of_user`／`revoke_row`…，★無「某 uid 全撤」原語、檔頭逐字「revoke_all_of_user 前提本刀
未成立、不搬」）；`facade/session_event.rs` 事件型恰四 `reuse／kicked／idle／logout`；denylist 分碼
`reason=="kicked"`→7777 modal／`revoked`→8888 靜默（`auth/enforce.rs::enforce_mw`）；`unlockLogin`
已上線且**雙維**（`handler/throttle.rs` `DIM_USER`／`DIM_IP`、`dimension` 必給、API-only）；
`handler/common.rs` 七件（`audit_operator` real_ip 不可得→5000 拒寫、`tristate`、`blank_to_none`、
`db_status_to_wire`…）；`reload_enforcer` rebuild-swap（ADR 0049）；`no_escalation_check` 恆 `Ok(())`、
middleware 掛點無 body 通道；`Res::from_err` data 恆 null（compile_fail 釘住）、`error.rs` 九變體
**無 `BizData`**（ADR 0022 §2② 自陳「已有」實為誤）；Lint24 白名單已預留 `biz.user.passwordViolation.*`
八鍵、註明「經 BizData 明細通道下發」（整鍵下發＝白名單腐化 ERROR）。

**寫端全無**：`facade/sys_user.rs` 恰四支（三讀＋`write_session_id`）、`facade/sys_user_role.rs` 三支全讀
（`roles_of_user` 濾 role 未軟刪＋status=1；`count_by_role` ★不濾 user／role status）、`model/password.rs`
只有 `verify`／`dummy_verify`（零 production 雜湊入口、零格式規則）；`refresh.rs` 生產碼只查
`roles_of_user`、零 sys_user 活性查詢；`getUserInfo`／`enforce_mw` 刻意不判 status（003 拍板）。

**前端基線**：`views/manage/user/{index.vue, modules/user-operate-drawer.vue, modules/user-search.vue}`、
`views/manage/user-detail/[id].vue`（LookForward 佔位）、`views/user-center/index.vue`（佔位）五支皆
upstream 逐位原樣（`rev5-inline` 標記 0）、**不在憲法 §III.2 任何用途的檔級名單內**；index.vue 刪除為
console.log 假實作、drawer 零請求假成功＋`getRoleOptions()` mock 段、email 欄 `path="email"` 基線瑕疵；
`constants/reg.ts` `REG_PWD=/^\w{6,18}$/` 綁 pwd-login／register／reset-pwd；`pwd-login.vue` 碼註
「(ii) formRules 放寬不帶回——延改密端點刀」；三顆快速登入鈕字面 `Super／Admin／User`＋`123456`（B-064）；
`page.manage.user` 葉鍵 rev5 19／rev4 45；`backend.biz.user.passwordViolation.*` 八鍵三語已在；
`user-avatar.vue` 下拉 `DropdownKey='user-center'|'logout'`、seed 選單列 16 `user-center`（hide_in_menu）已在；
gating 現況：menu 頁碼註「hasAuth gating 為 rev5 已推翻行為〔前提＝頁級 R_SUPER 即門〕」、ip-rule 頁仍 gating
（B-099 形 6 處）。

**治理約束**：憲法 §V.3 島隨刀進場＋用途擴展＝MINOR；既有島 C（sys_token.status 權威）／E（節流
fail-open）／F3①（real_ip 拒寫）／G4（in-use 守門）／G5「刀 B 之 `sys_user_role` 指派寫端落地時 MUST 同納
本鎖序」／H1「advisory key space 新增用途 MUST 先核」；ADR 0019（rev4 藍本紀律）、0021（純新增檔免軌道）、
0022（純 key／掛點零簽章）、0023（三態更新）、0038（register／reset-pwd 恆 stub）、0041（mailer 域外）、
0049 §3 失效條件②「刀 B user 寫端進場」、0050 §2（deleteRole 免 reload）、0054（seed 68 上線即入 P）、
0059（logout no-op；翻案觸發器「single-session 語意調整時」）、0058／0062（活書 §5 70/90、§6 120/160、
§8 53/130，撞頂＝輕量軌下放）。

## §1 背景與觸發

- 刀 B＝rev5 第一個 user 域寫端家族：seed 已錨定的能力面（十支端點＋七枚按鈕碼）＋自助改密，
  從「seed 有列、碼與 UI 全無」做成真功能；同分支順路收 BACKLOG 17 條（甲類內建 8：B-003／B-021／
  B-020／B-024／B-025①／B-089／B-093／B-113；丙類順路 6：B-127／B-129／B-128／B-098／B-029／B-132；
  demo 3：B-018／B-053／B-064）。乙類硬前置 B-126 已於本日關帳（ADR 0062）。
- 觸發器兌現：B-021「改密端點建立時」、B-020「第二消費者」、B-089「使用者域寫端那一刀」、B-093
  「刀 B 起手必復核」、B-025①「刀 B 落地時同窗重評」、B-003「餘 sys_user 一張」皆在本刀成立。

## §2 射程

### 2.1 端點（ROUTES 49→61；POLICY_ENDPOINT_COUNT 35→45；零 migration、零新 casbin seed 列）

| # | 路徑 | 動詞 | Protection | seed 列 | 按鈕碼 | rev4 對應 |
|---|---|---|---|---|---|---|
| 1 | `/systemManage/getUserList` | GET | Policy | 1／2 | — | 同 |
| 2 | `/systemManage/getDeletedUsers` | GET | Policy | 155 | — | 同 |
| 3 | `/systemManage/addUser` | POST | Policy | 17 | `user:add` | 同 |
| 4 | `/systemManage/updateUser` | POST | Policy | 18 | `user:edit` | 同（userName 出現即拒＝rev5 差異） |
| 5 | `/systemManage/deleteUser` | DELETE | Policy | 19 | `user:delete` | 同（動詞不符→4040＝ADR 0031） |
| 6 | `/systemManage/batchDeleteUser` | DELETE | Policy | 20 | `user:delete` | 同 |
| 7 | `/systemManage/restoreUser` | POST | Policy | 152 | `user:restore` | 同（零回灌） |
| 8 | `/systemManage/kickUser` | POST | Policy | 154 | `user:kick` | 同 |
| 9 | `/systemManage/resetUserPassword` | POST | Policy | 151 | `user:reset-pwd` | 同（＋設密冷卻） |
| 10 | `/systemManage/updateUserSessionPolicy` | POST | Policy（protected） | 68 | （drawer edit 模式） | 同 |
| 11 | `/userCenter/changePassword` | POST | Authed | 零 | — | 同（五步序） |
| 12 | `/userCenter/getPasswordPolicy` | GET | Authed | 零 | — | 同（7 鍵 allowlist） |

既有 `unlockLogin`（004、雙維、seed 148）由本刀接 UI（`user:unlock`）。

### 2.2 UI 射程（Q03＝rev4 全套形）

`views/manage/user/` 全套：抽屜新增／編輯（NDrawer 360、password 僅 add、sessionPolicy 僅 edit、
userName edit 模式 disabled、memo textarea）＋回收桶 toggle（切兩資料源、已刪模式隱搜尋卡、operate 整欄
換復原）＋列上 NDropdown 收納踢除／重設密碼／隨機密碼＋頁首「解鎖登入」modal（新檔
`modules/user-unlock-modal.vue`、雙維）＋產密浮層（新檔、i18n 掛 `page.manage.user.pwdGen.*`）＋七碼
逐鈕 `hasAuth` gating（B-099 形）；`views/user-center/index.vue` 改寫為真頁、只掛改密卡（新檔
`modules/password-card.vue`、只舊密碼一路、動態 rules）；`pwd-login.vue` pwd／userName 降 required-only。

### 2.3 非射程（spec 明列）

`manage_user-detail` 詳情頁（續留佔位、seed-view-gate 對賬故不可刪檔）；首登強制改密（→B-134）；
getProfile／updateProfile／email 驗證四支（撞 ADR 0041）；改密卡信箱／手機驗證 radio；zh-TW 接 runtime；
`Api.IpRule.*` 七支補裁判（B-098 留帳）；B-029；`/auth/error`（B-053 移滯後卷）；快速登入鈕拆除（B-064）。

## §3 拍板全紀錄（2026-08-25、AskUserQuestion 逐輪親決）

★＝拍板級逐題；◇＝快答整批照建議。「歸屬」＝本檔承接節。

| # | 題 | 決議 | 歸屬 |
|---|---|---|---|
| Q01★ | 射程主幹 | 管理面十支＋changePassword（＋getPasswordPolicy 依 Q26）；profile／email 不進 | §2 |
| Q02★ | 首登強制改密 | 本刀不做；custody 表除冷卻時戳外零寫入；立 B-134 | §2.3／§6 |
| Q03★ | UI 射程 | 照 rev4 全套形 | §2.2／§5 |
| Q04◇ | 詳情頁 | 不兌現、續留佔位、spec 明列非射程 | §2.3 |
| Q05◇ | migration | 零 migration | §2 |
| Q06★ | 憲法進場 | §I.7 新島 I（沿 rev4 I1～I5；I6 不入）＋§III.2 新用途；MINOR 1.8.0→1.9.0 | §6.1 |
| Q07★ | Amendment 用途 | (v)(vi)(vii) 三用途一次開齊、名單當場定數 | §6.1 |
| Q08◇ | i18n 語系 | page 樹補 zh-cn＋en-us；zh-tw.ts 只補 backend 樹 | §5.5 |
| Q09★ | 寫端授權面 | **下放寫端給 R_ADMIN＋實作 no-escalation**（非建議項、user 親決） | §4.1 |
| Q09-1★ | 下放載體 | seed 不動；運行期由超管以 006 端點＋按鈕授權 modal 勾給角色 | §4.1 |
| Q09-2★ | 下放射程與規則 | 七動作全可下放；守門＝角色集包含規則（標的角色集 ⊆ 操作者角色集 ∧ 指派後角色集 ⊆ 操作者角色集） | §4.1 |
| Q28★ | no-escalation 掛點 | handler 鎖內具名守門；middleware 四參掛點續留恆 Ok；新 ADR 寫射程分工、不翻 0022 | §4.1 |
| Q10★ | 按鈕 gating | 七碼逐鈕 `hasAuth`（B-099 形）；spec 寫判準「該頁 menu 維政策是否僅 R_SUPER」；ADR 記為既有拍板之例外釋義 | §5.1 |
| Q11◇ | seed 帳號保護 | 全套：三帳號不可刪；Super 恆禁停用／恆禁解超管指派；self 不得刪／停用／踢／改自身指派；碼內常數 | §4.3 |
| Q12◇ | kick 射程 | self 禁踢；Super 可踢（受包含規則）；停用可踢；已刪不可 | §4.3 |
| Q13◇ | kick 撤銷範圍 | 撤該 uid 全部 active、不動 rotated（新 `revoke_all_of_user` 薄殼） | §4.2 |
| Q14★ | 失效碼分派 | kick→`kicked`(7777)；停用／刪除／重設→`revoked`(8888)；7777 文案改中性或另立鍵 | §4.2 |
| Q15★ | 斷權即時性 | 同交易撤全部 active＋best-effort denylist＋refresh 鎖內重驗 status／deleted_at；顯式復核 ADR 0059 | §4.2 |
| Q16★ | 軟刪指派／restore | 同交易硬刪全部指派；復原零回灌、status 保留；UI 明示須重新指派（B-025① 結案） | §4.3 |
| Q17◇ | updateUser no-op | 先全 None 早退、再值 diff | §4.7 |
| Q18★ | 密碼政策 | 整套承襲 rev4:ADR 0054（單一驗證點、八鍵生效、chars＋bytes 雙約束、三重不洩；登入路徑不驗） | §4.4 |
| Q19★ | 明細通道 | 新增 `AppError::BizData`＋`Res::from_err_with_data`，射程嚴限密碼（＋冷卻剩餘秒）；5003 純 key；新 ADR 澄清 0022 §2②、結 B-024③ | §4.4 |
| Q20★ | 設密冷卻 | 實作；維度＝(標的 user_id, 操作者 uid)；借 custody 時戳；一體適用零豁免；未滿→2222 攜 remainingSeconds | §4.4 |
| Q21◇ | changePassword | Authed 零 seed；標的恆 `claims.uid`；序＝兩次一致→舊密→新≠舊→政策；成功撤他 session 保留當前 | §4.4 |
| Q22★ | 自助頁可達 | 帶回 `SELF_SERVICE_ROUTES` 碼內白名單（承 rev4:ADR 0065） | §4.5 |
| Q23◇ | seed 68 | 交付端點＋drawer 三選一 inherit／single／multi；改 single 不即時踢 | §4.7 |
| Q24◇ | unlock 入口 | user 頁頁首 modal、雙維；ADR 0042 第 2 項措辭訂正 | §5.1／§6.2 |
| Q25★ | B-089 修法 | `pwd-login.vue` pwd／userName 降 required-only、不動 `reg.ts`；用途 (vii) | §5.3 |
| Q26★ | 前端規則來源 | `getPasswordPolicy` Authed 端點＋`pwd-policy` hook 動態 rules；drawer 只掛 hint | §4.4／§5.2 |
| Q27◇ | B-093 閉合 | ①指派寫端 commit 後 `reload_enforcer`；`handler/user.rs` 進 `RELOAD_CALL_FILES`；ADR 矩陣補列 | §4.6 |
| Q29◇ | 稽核詞彙 | 新增小寫 `kick`／`reset_password` | §4.7 |
| Q30★ | 改密節流（B-021） | 做：argon2 前掛點、per-user 桶、成功清計數、fail-open、碼內常數門檻；B-020 通用化＝工程自決 | §4.4 |
| Q31◇ | 回收桶 UI | toggle 切兩資料源 | §5.1 |
| Q32◇ | 已刪模式欄 | 不加「刪除時間」欄 | §5.1 |
| Q33◇ | 產密浮層 | 承襲元件、i18n 掛 `page.manage.user.pwdGen.*` | §5.1 |
| Q34◇ | 改密 UI 落點 | 改寫 `user-center/index.vue` 真頁、只掛改密卡、三卡位留白 | §5.2 |
| Q35◇ | 改密卡驗證方式 | 只舊密碼一路、不放信箱／手機 radio | §5.2 |
| Q36◇ | B-129 | 納入、先修再照抄 | §5.4 |
| Q37◇ | B-132 | 納入修法①（只動 `menu/index.vue`） | §5.4 |
| Q38◇ | B-029 | 不納 | §2.3 |
| Q39◇ | B-018 | 只更新條文、觸發器改狀態式「轉 prod 時」 | §6.3 |
| Q40◇ | B-053 | 不兌現、改觸發器、移 BACKLOG-DEFERRED | §6.3 |
| Q41◇ | B-064 | 不拆；BACKLOG 補「刀 B 期間必須保留」硬約束 | §6.3 |

## §3b grilling 輪（2026-08-26、18 題；★＝與 §3 既有結論的延伸或細化）

| # | 題 | 決議 | 延伸／歸屬 |
|---|---|---|---|
| G1 | 標的角色集 T 的定義 | T＝全部指派列（`role_ids_of_user`、不濾角色 status）；A＝操作者現役角色（`roles_of_user`） | ★Q09-2 細化；§4.1 |
| G2 | 同級互管 | 允許（單一規則零特例；seed 保護擋 id 1） | §4.1 |
| G3 | self 可改範圍 | 非角色欄可改；`status`／`roleIds` 出現即拒；sessionPolicy 可改 | ★Q11 細化；§4.1 |
| G4 | 批刪原子性 | 照 rev5 既有形：任一違規整批 rollback、純 key 不指筆、空陣列 no-op | §4.3 |
| G5 | 已軟刪標的拒因 | 一律 `biz.user.notFound`；只有 restoreUser 認得已刪列 | §4.3 |
| G6 | unlockLogin 套規則 | 帳號維套 T ⊆ A；IP 維不套 | §4.1（原「spec 期決」收束） |
| G7 | 非超管的會話政策欄 | 顯示但 disabled＋提示「僅超級管理員可改」（protected 端點結構上不可授非超管） | ★Q23 細化；§5.1 |
| G8 | 前端預判包含規則 | **都不預判、全靠後端 5003**（非建議項、user 親決） | ★Q10 細化；§5.1 |
| G9 | 管理員踢除分鍵 | 新 denylist reason `admin_kick`→7777＋新鍵 `auth.session.kickedByAdmin`；`kicked` 原文案不動 | ★Q14 細化；§4.2 |
| G10 | 自助改密事件與稽核 | session_event reason `password_changed`；op-log 第三個新值 `change_password` | ★Q29 延伸；§4.2／§4.7 |
| G12 | 改密舊密節流常數 | redis 滑動窗 5 次／15 分鐘、超限 `biz.user.changePasswordThrottled` 純 key、成功即清、窗自癒、桶獨立 | ★Q30 細化；§4.4 |
| G13 | custody 寫入語意 | 只 upsert `(user_id, created_by, created_at=now())`；不做「自改→全刪」 | ★Q20 細化；§4.4 |
| G14 | addUser 計入冷卻 | 計入（addUser 也寫 custody 列） | §4.4 |
| G16 | 信箱／手機 | 皆選填（空→NULL）；信箱簡式格式＋活性唯一預檢；手機只驗 ≤32 | §4.7 |
| G17 | addUser 初始態 | 預設啟用（抽屜可改）；允許零角色 | §4.7 |
| G23 | 詞彙六條 | 停用／軟刪／踢除／撤銷／鎖定／重設 vs 修改密碼——入活書 §12 | §6.4 |
| G24 | 復原前超管 | 可以：零回灌下無升權、規則不加例外（spec 列驗收案） | §4.3 |
| G25 | self 重設自己密碼 | 禁止：`biz.user.cannotResetSelfPassword`、導向個人中心（self 四不擴為五不） | ★Q11 延伸；§4.1 |

## §4 核心設計（後端）

### 4.1 授權下放與 no-escalation（Q09／Q09-1／Q09-2／Q28）

- **預設 seed 不動**：dev stack 起手仍是「寫端 super-only、R_ADMIN 只有 getUserList＋`user:edit` 鈕」；
  「多層管理員」是超管可在運行期用 006 的端點授權 modal＋按鈕授權 modal 開關的能力，不是預設態。
- **守門規則（對所有角色一體適用、住 handler 寫端鎖內；G1／G2）**：`A`＝操作者**現役**角色 code 集
  （`roles_of_user(claims.uid)`、DB-fresh、濾角色軟刪與停用）、`T`＝標的**全部指派列**（`role_ids_of_user`、
  ★不濾角色 status——停用中的角色仍算標的潛在持有的權力）、`N`＝本次寫入後的標的角色集；寫端 MUST 同時
  滿足 `T ⊆ A` 且 `N ⊆ A`；違者 5003（純 key、★不洩漏差集）。同級互管允許（{R_ADMIN} 可管 {R_ADMIN}、
  {R_SUPER} 可管 {R_SUPER}）；★持 R_SUPER 者之 `A` 視為全集（specify clarify 2026-08-26 訂正：seed Super 只持
  R_SUPER、原句「超管因 A 最大自然不受限」的字面集合前提不成立）；seed 帳號結構保護與 self 五不（§4.3）先於本規則判定。★純包含規則的已知後果（user 已知悉）：seed 中
  R_ADMIN 只持一枚角色 ⇒ 預設只能管「只持 R_ADMIN 的帳號」，實用面須由超管多授 R_ADMIN 一枚 R_USER。
- **掛點形**：新增具名純函式（例 `assert_no_escalation(actor, target, next)`、`auth/` 或 `model/` 域內），
  於 addUser／updateUser／deleteUser／batchDeleteUser／restoreUser／kickUser／resetUserPassword／
  updateUserSessionPolicy 的鎖內、寫入前呼叫；`enforce.rs::no_escalation_check` 四參掛點續留恆 `Ok`
  （一般上限位）。ADR 0022 不翻：新 ADR 寫明兩個實作位的射程分工（middleware＝路徑級上限、handler＝
  body 級指派集）。
- **`unlockLogin`（004 handler）帳號維同套 `T ⊆ A`**（G6；解鎖＝替該帳號移除一道安全門）；IP 維無標的角色、不套；
  帳號不存在照既有形不洩漏。
- **可測性**：每支寫端至少一案「R_ADMIN 運行期被授予端點後、對持 R_SUPER 標的仍 5003」與一案
  「指派超出自身角色集 5003」；測試在測內 grant（casbin 資料列、`CasbinCleanup` 兜底）。

### 4.2 斷權語意（Q13／Q14／Q15）

- `sys_token` 新增 `revoke_all_of_user(uid)` 薄殼（或 `revoke_others_of_user(keep_sid: Option)`）：撤該 uid
  全部 active、不動 rotated（rotated 重放仍走 reuse 偵測、不混流盜用訊號）；回 distinct sid 集餵
  session_event＋denylist。
- `session_event` 新增事件型 `revoked`＋reason `user_disabled／user_deleted／password_reset／password_changed／
  admin_kick`（varchar、零 migration；順手收成 macro 單一宣告源）。
- 停用（status 1→2）／刪除／重設密碼：**同交易**撤全部 active＋寫事件；commit 後 best-effort denylist
  （`revoked`、TTL＝refresh 全壽命）；kick 同形但 reason `admin_kick`、denylist `kicked`（7777）。
- `refresh.rs` 鎖內重驗使用者活性（`status==Some(1) && deleted_at IS NULL`）——動到 003 島 C 的 token
  狀態機但非方向反轉（仍 PG-first、fail 方向不變），ADR 明列；ADR 0059（logout no-op）顯式復核不受影響。
- 失效碼與事件終態（G9／G10；`kicked`／`revoked` 不互換的島 C 語意不變）：

  | 動作 | session_event（事件／reason） | denylist reason | 被撤者所見 |
  |---|---|---|---|
  | 管理員踢除 | `revoked`／`admin_kick` | `admin_kick`（新） | 7777、`auth.session.kickedByAdmin`（新鍵：「此工作階段已被管理員結束，請重新登入」） |
  | 單一會話頂替（既有） | `kicked`／`single_session` | `kicked` | 7777、`auth.session.kicked`（不動） |
  | 停用 | `revoked`／`user_disabled` | `revoked` | 8888 靜默、再登入得 1000 |
  | 刪除 | `revoked`／`user_deleted` | `revoked` | 8888 |
  | 管理員重設密碼 | `revoked`／`password_reset` | `revoked` | 8888 |
  | 本人改密（撤他 session） | `revoked`／`password_changed` | `revoked` | 8888 |

  `cache::REASON_*` 多一值 `admin_kick`、`enforce_mw` 依 reason 分鍵；新鍵兩語＋backend-msg-dict 同批。

### 4.3 軟刪／restore／seed 保護／kick 射程（Q16／Q11／Q12）

- deleteUser／batchDeleteUser：鎖內 ①seed 保護 ②self 保護 ③no-escalation → 軟刪（成對 `deleted_*`）→
  同交易硬刪全部 `sys_user_role` → `revoke_all_of_user` → 事件 `revoked／user_deleted`。批刪照 rev5 既有形：
  任一違規整批 rollback（no-partial）、拒因純 key 不指筆、空陣列提前 no-op（G4）。
- 已軟刪標的：updateUser／kickUser／resetUserPassword／updateUserSessionPolicy／deleteUser 一律
  `biz.user.notFound`（活性判準 `deleted_at IS NULL`、同 role 域形）；只有 restoreUser 認得已刪列（G5）。
- restoreUser：鎖已刪列 → 鎖內重驗同名活性、同信箱活性（兩腿、撞則 2222 專屬拒因）→ 成對清 `deleted_*`；
  **零回灌**（復原後零角色、status 保留刪除前原值）；UI 確認框明示「復原後需重新指派角色」。
  藍本＝`facade/sys_menu.rs::restore` 形（不借 `sys_casbin_archive::restore`）。★被下放者可復原「前超管」
  （T＝∅ ⊆ A、復原後零角色、要回超管須持 R_SUPER 者指派）——規則不加例外、spec 列為驗收案（G24）。
- seed 帳號結構保護（碼內常數 `USER_SEED_MAX_ID=3` 家族）：三帳號不可刪；Super（id 1）恆禁停用、恆禁
  解其超管指派——拒因純 key。**self 五不**（G3／G25）：不得刪／停用／踢／改自身指派（updateUser 對 self 之
  `status`、`roleIds` 出現即拒）／用 resetUserPassword 重設自己（`biz.user.cannotResetSelfPassword`、導向個人
  中心）；self 可改非角色欄與 sessionPolicy。
- kick：self 禁踢；Super 可踢（但受 §4.1 包含規則＝只有持 R_SUPER 者能踢 Super）；停用可踢；已軟刪不可
  （鎖列「未刪即可」）。

### 4.4 密碼面（Q18／Q19／Q20／Q21／Q26／Q30）

- `model/password.rs` 補三支 `hash`／`load_policy`／`validate_against_policy`（rev4:ADR 0054 整套：7 鍵
  單快照、缺鍵 fail-default、收集全部違規、chars 計長＋bytes ≤ `LOGIN_PASSWORD_MAX_BYTES`、
  `forbid_username` case-insensitive 相等、密碼三重不洩）；addUser 初始密碼／resetUserPassword／
  changePassword 三入口共用、hash 鎖前算；★登入路徑絕不驗政策。
- 明細通道：`AppError::BizData(key, Value)`＋`Res::from_err_with_data`，射程恰二鍵
  `biz.user.passwordPolicy{violations[]}`（違規碼＝Lint24 白名單八鍵尾段）與 `biz.user.pwdSetTooFrequent
  {remainingSeconds}`；其餘一律純 key。
- 設密冷卻：讀 `password_change_min_interval`（0＝停用）；維度＝(標的 user_id, 操作者 uid)；借
  `sys_pwd_custody (user_id, created_by, created_at)` 時戳（首寫者；測試補 RAII 清理腿、入不入
  `RUNTIME_APPEND_TABLES` 實作期判）；一體適用零豁免；★寫入語意只 upsert 該對的 `created_at=now()`、不做
  rev4 的「本人自改→全刪經手列」（G13）；addUser 初始密碼也寫 custody 列、計入冷卻（G14）；ADR 明示只用時戳、
  不做 EXISTS 判定（那是 B-134）。
- changePassword：`Protection::Authed`、零 seed；標的恆 `claims.uid`；五步序＝帳號存在→兩次一致→舊密
  正確→新≠舊→政策；成功 `revoke_others_of_user(keep=claims.sid)`＋事件；路徑 `/userCenter/changePassword`
  （`/auth/*` 現清一色 Public、工程自決）。
- 改密舊密節流（B-021）：argon2 前掛點、per-user 桶（redis、鍵前綴與登入節流桶分離）、★redis 滑動窗
  5 次／15 分鐘、第 6 次起 `biz.user.changePasswordThrottled`（純 key、不攜秒數）、成功即清、無解鎖端點
  （窗自癒）（G12）；redis 故障 fail-open（島 E 同向、擴射程仍 MINOR）；門檻碼內常數（不動 002 之 16 鍵
  凍結）；是否做成 B-020 通用 seam＝工程自決（做通用即關 B-020）。
- `getPasswordPolicy`：Authed、7 鍵 allowlist 投影（不含 interval）；前端 `hooks/business/pwd-policy.ts`
  動態 rules（取不到靜默降 required）；`forbid_username` 前端略、交後端。

### 4.5 自助頁可達性（Q22）

`handler/route.rs::get_user_routes` 於 casbin 過濾後恆併入碼內常數 `SELF_SERVICE_ROUTES=["user-center"]`
（承 rev4:ADR 0065；紀律嚴限「受眾＝本人」的自助頁家族、RBAC 資源頁禁入）；hide_in_menu 故側欄不現、
只從頭像下拉進；seed `p|R_SUPER|user-center|menu` 保留（聯集下冗餘無害）。單測兩向：零 menu policy 角色
仍得自助路由；白名單外路由不受影響。route.rs 檔頭「不帶回」註解改寫為「自本刀帶回」。

### 4.6 B-093 閉合與鎖序（Q27）

- 指派寫端（updateUser 改角色、restore 不回灌故不觸）commit 後呼 `reload_enforcer`（Applied 即觸發、
  不問 diff，同 006 grant 面口徑）；`tests/authz_entrypoint_lint.rs::RELOAD_CALL_FILES` 擴一檔
  `handler/user.rs`（恰等斷言、漏擴即紅）；ADR 0053 款四觸發矩陣補一列。
- 鎖序（島 G5／H1／ADR 0049 §3 條件②）：user 域寫端全數進 per-user advisory 鎖（`advisory_lock_user(uid)`
  自 login.rs 上提 facade、DbErr 形；addUser 豁免）；固定序＝advisory(uid) → sys_user 列 → sys_role 列升序
  → sys_user_role；H1 key space 沿用 login 之 uid 鍵＝同一用途擴消費者，ADR 明寫核過；lock-then-redecide。

### 4.7 其他後端（工程自決、回報備查）

updateUser 三態（ADR 0023）、no-op＝先全 None 早退再值 diff、`blank_to_none` 僅 addUser、userName 出現即拒
（沿 sys_role 差異①）；email／phone 皆選填（空字串→`blank_to_none`＝NULL、不參與唯一）；email 簡式格式守門（恰一個 `@`、無空白、
≤254）→`biz.user.userEmailInvalid`＋鎖內活性唯一預檢→`biz.user.userEmailExists`＋23505 兜底、`lower()`
語意入契約；phone 只驗 ≤32（G16）；addUser 預設啟用（抽屜可改）、允許零角色（G17）；user_name 形制 `^[A-Za-z0-9_-]{1,64}$` 自建；seed 68 端點＋寫端 `inherit／single／multi` 三值
收斂、改 single 不即時踢；稽核詞彙新增小寫三值 `kick`／`reset_password`／`change_password`（G10；payload 只 `{id,user_name}`、
負向斷言不含 `$argon2`）；B-127 兩份映射收攏 `handler/common.rs::wire_two_value_to_db`；B-113 種合成候選外
protected 探針列、`outside_protected≥1` 升真 assert；每個新 wire 型 i64 欄掛 `serialize_*_guarded`；
`ROUTES` 六欄＋`ROUTES_COUNT` 61＋`POLICY_ENDPOINT_COUNT` 45＋`tests/contract.rs` ContractCase；
`UserCleanup` 補業務鍵腿＋op-log 腿＋`setval('sys_user_id_seq', 3, true)`；seed 三帳號測試掛
`SeedOpLogCleanup::arm`；endpoint 測試帶真 connect-info（real_ip NOT NULL）。

## §5 前端面

### 5.1 user 管理頁（(v)；Q03／Q10／Q24／Q31～Q33）

- 修改型（帶 `原行:`、多行註解形）：`index.vue`（接真 fetch、刪 console.log 假實作、回收桶 toggle、
  NDropdown 收納、七碼 gating B-099 形、memo 純文字欄、`scroll-x` 962→Σ 欄寬）、`user-operate-drawer.vue`
  （接真 submit、刪 mock 段、修 `path="email"`→`userEmail`、password 僅 add＋隨機鈕＋hint、sessionPolicy 僅
  edit、userName edit disabled、memo textarea）；`user-search.vue` 兩向 diff 零改動則不入名單。
- 新增型（免名冊、檔頭 `[rev5-inline <軌道>+ 007]`）：`modules/user-unlock-modal.vue`（雙維、顯式帶
  `dimension`）、產密元件（front CSPRNG）、`typings/api/rev5-user-admin.d.ts`＋`service/api/rev5-user-admin.ts`
  （`Api.UserAdmin.*`、每 definition 配 `wire_schema.rs` 裁判正向≥1 反例≥1、`system-manage.ts` 不動）。
- 接真形照三頁：status `'1'|'2'`、`createdAt／createdBy`、拒因 `translateBackendMsg`、鍵 `id`；
  已刪模式不加 deletedAt 欄；toast／確認框自備 `page.manage.user.*`（不借 menu／policyArchive 鍵）。
- ★前端**不預判**包含規則（G8、user 親決）：抽屜角色下拉全列、列級操作鈕只依按鈕碼 gating、送出後端 5003
  誠實 toast；抽屜 sessionPolicy 欄對非超管（`authStore.userInfo.roles` 不含 `R_SUPER`）顯示但 disabled＋提示
  「僅超級管理員可改」、不發出必敗的第二支呼叫（G7）；自己那列的抽屜 `status`／`roleIds` 控制項 disabled、
  操作下拉不列「重設密碼」（self 五不）。

### 5.2 個人中心改密（(vi)；Q34／Q35／Q26）

`views/user-center/index.vue` 修改型：採 rev4 父層骨架、只掛 `modules/password-card.vue`（新檔）；三卡位
留白；只舊密碼一路、無 radio；rules 來自 `pwd-policy` hook；`:user-name` 不用 `authStore.userInfo.userName`
（nick_name 別名）；新 top-level `page.userCenter.*` 命名空間（Amendment 具名）。

### 5.3 登入頁（(vii)；Q25）

`pwd-login.vue` 就地把 pwd／userName 規則改 `createRequiredRule`、不動 `reg.ts`；register／reset-pwd stub
不動。前後對照：改前 `P@ssw0rd!2026` 紅字零請求；改後直送、後端判定。

### 5.4 順路丙類（Q36／Q37／B-128／B-098）

B-129：三顆授權 modal `getChecks()` 起手清 `rawChecks／protectedIds`＋`homeReq` 世代（(iii) 補完免 bump）、
排在 user drawer 照抄範式之前；B-132：`menu/index.vue` 切模式時重置 `pagination.pageSize`（(ii) 名單內、
帶 `原行:`）——★user 頁治理清單帶參、結構性不重現；B-128：編排 script 前端驗證段 .ts 改指
`pnpm exec oxlint <file>`＋RUNBOOK 一段（不開 `eslint.config.js` 用途）；B-098：只補 `Api.UserAdmin.*`／
`Api.UserCenter.*` 裁判、IpRule 七支留帳。

### 5.5 i18n 與驗收

`page.manage.user` +26 鍵×zh-cn／en-us（鍵集相等）＋`page.userCenter.*`＋`app.d.ts` 型節；
`backend.biz.user.*` 新鍵三檔同批（Lint24）；`zh-tw.ts` 只補 backend 樹。CDP 對照 42080（rev4）：
user 頁列表／抽屜／回收桶／踢除（對方 7777）／重設密碼／解鎖 modal／gating（Super／Admin／User 三角色反覆
切換，★B-064 三顆鈕刀 B 期間必留）；user-center 改密卡；登入頁特殊字元密碼可登入；rev5 側預期差異＝
三卡留白、兩語、無首登強制頁。

## §6 治理面

### 6.1 憲法 Amendment（MINOR 1.8.0→1.9.0；brainstorm 收尾即成稿、specify 前 user 親審）

- §I.7 新島 I「使用者域治理」：I1 寫端鎖序（per-user advisory、lock-then-redecide、addUser 豁免）；I2
  停用‧刪除‧重設同交易撤全部 session＋refresh 鎖內重驗、`kicked`／`revoked` 不互換、MUST NOT 每請求
  活性判定；I3 seed 三帳號與自身結構保護；I4 軟刪同交易硬刪指派＋復原零回灌；I5 密碼政策單一驗證點＋
  三重不洩＋登入路徑不驗；★I7 no-escalation 包含規則（rev5 新增、rev4 無）；條文只凍結方向面。
- §III.2 新用途：(v) `BASE-WEB-MANAGE-PAGE-WIRING` user 管理頁 CRUD 接真（`index.vue`＋
  `user-operate-drawer.vue` 修改型＋兩語 locale＋`app.d.ts`）；(vi) 個人中心改密（`user-center/index.vue`
  修改型＋`page.userCenter` 命名空間＋`password-card.vue`／產密元件具名）；(vii)
  `BASE-WEB-LOGIN-CAPTCHA-WIRING (ii)` `pwd-login.vue` formRules 放寬。B-129 走 (iii) 補完、B-132 走 (ii)
  補完、皆免 bump。

### 6.2 ADR 配置草案（tasks 期定稿、實作期落檔）

1. 島 I 行為承載＋no-escalation 掛點射程分工（補 ADR 0022 決定 3、不翻）＋按鈕 gating 例外釋義
   （ADR 0019 差異點：判準＝該頁 menu 維政策是否僅 R_SUPER）。
2. BizData 明細通道（射程二鍵；澄清 ADR 0022 §2② 之誤；結 B-024③ 受眾邊界）。
3. `SELF_SERVICE_ROUTES` 碼內白名單（承 rev4:ADR 0065）。
4. 設密冷卻＋改密節流（custody 只用時戳；fail-open；常數門檻）。
5. ADR 0042 第 2 項措辭訂正（解鎖入口＝使用者管理頁；走 v1.6.1 對 0043 之範式）＋ADR 0053 矩陣補列。

### 6.3 BACKLOG 處置（本檔 commit 同批落帳者標 ✓）

| 條目 | 處置 |
|---|---|
| B-003 | 刀 B 兌現 user memo 兩面 → 收刀關帳 |
| B-021 | Q30 做 → 收刀關帳 |
| B-020 | 第二消費者成立；做通用 seam 即關帳（工程自決） |
| B-024 | ①隨 Q09/Q28 落地、③隨 Q19 ADR 結掉 → 收刀關帳 |
| B-025 | ①隨 Q16 結案；②事後對賬掃描續留（觸發器不變） |
| B-089 | Q25／Q26 → 收刀關帳 |
| B-093 | Q27 → 收刀關帳 |
| B-113 | ✓條文更正（續綠非轉紅）；探針列處置 → 收刀關帳 |
| B-127 | 收攏 → 收刀關帳 |
| B-129 | Q36 → 收刀關帳 |
| B-128 | ①②做、③不做 → 收刀關帳 |
| B-098 | 新型配裁判；IpRule 留帳（觸發器不變） |
| B-029 | 不納（觸發器不成立） |
| B-132 | Q37 → 收刀關帳 |
| B-018 | ✓條文更新（fetchGetUserList 失消費者、觸發器改狀態式） |
| B-053 | ✓移 BACKLOG-DEFERRED、觸發器改「下一把觸及 §I.3 wire 例外集的刀」 |
| B-064 | ✓補硬約束「刀 B 期間必須保留」、觸發器改狀態式 |
| B-134 | ✓新立：首登強制改密（Q02） |

勘誤（收刀期）：NOTES「seed 68（manage_user view）」→「seed 68（updateUserSessionPolicy 端點）」；
`handler/common.rs` 檔頭與 NOTES「六件」→七件；ADR 0022 §2② 由新 ADR 一句澄清。活書 as-built 落點：
§5（模組拓樸、預估 +8）、§6（斷權與密碼序，預估 +20）、§8（授權慣例＋接線指針，預估 +6）、附屬文件
FORK-DELTA-WIRING.md（(v)(vi)(vii) 接線 as-built）；撞頂即依 ADR 0062 輕量軌下放。

### 6.4 詞彙（活書 §12 名詞表候選、U0 落檔；G23）

- **停用**：`sys_user.status=2`、管理員設定、持久；登入得 1000、既有 session 同交易撤銷（8888）。
- **軟刪**：`deleted_at` 非空、可復原；指派列已硬刪、復原零回灌。
- **踢除**：撤銷標的全部 active session、帳號狀態不變、可立即重登；被踢者見 7777。
- **撤銷**：系統因停用／刪除／重設密碼／自助改密而撤 session；被撤者見 8888。
- **鎖定**：登入失敗節流鎖（帳號維／IP 維）、時窗自癒或管理員解鎖；與停用無關。
- **重設密碼 vs 修改密碼**：管理員對他人 vs 本人自助；同一驗證點、皆撤 session（後者保留當前）。

## §7 執行單元草案（tasks 期定稿）

U0 憲法 Amendment＋ADR 首批（島 I／三用途；user 親審）→ U1 後端底座（password 三支＋BizData 通道＋
`revoke_all_of_user`＋session_event 擴＋facade sys_user／sys_user_role 寫端＋advisory 上提＋no-escalation
純函式）→ U2 user 寫端十支（含 seed 保護、軟刪／restore、kick、冷卻、reload、B-127／B-113）→ U3
changePassword＋getPasswordPolicy＋改密節流＋SELF_SERVICE_ROUTES → U4 refresh 鎖內重驗＋失效碼文案 →
U5 前端 user 頁全套（(v)、順路 B-129／B-132 先修）→ U6 user-center 改密卡＋登入頁 required-only
（(vi)(vii)）→ U7 i18n＋wire-schema 裁判＋CDP 三角色走查 → U8 收尾（活書 as-built、RUNBOOK §12.1 量測、
BACKLOG 關帳、B-128 ①②）。rust 全程 serial 容器內；每單元 pin bump。

## §8 風險與誠實界線

1. **Amendment 面＝rev5 史上最大**：三用途＋新島 I＋rev5 新增條 I7；Amendment 未落前前端一行不能動；
   §V.2 提案在 brainstorm 收尾成稿、specify 前 user 親審。
2. **Q09 下放的連動代價**（user 已知悉）：no-escalation 在八支寫端＋unlockLogin 帳號維各一掛點、測試面每端點
   至少兩案；純包含規則下 seed 之 R_ADMIN 只能管「只持 R_ADMIN 的帳號」；運行期下放後 dev stack 每次 refresh
   seed 須重勾（寫成 CDP 起手腳本）；前端不預判（G8）⇒ R_ADMIN 會在抽屜看到可勾但必敗的 R_SUPER 選項、
   靠 5003 toast 學規則。
3. **密碼面三題連動**：政策真源（Q18）× 明細通道（Q19）× 登入頁規則（Q25）任一走偏即「設得進、登不進」；
   seed `123456` 令登入路徑永不驗政策。
4. **斷權動到 003 島 C**：refresh 補活性重驗＝token 狀態機新增判定腿（非方向反轉）；ADR 明列；ADR 0059
   復核結論一併入 ADR。
5. **B-113 條文原述有誤**（續綠非轉紅）——探針列處置不變、但驗收判準改為「探針列 assert 真紅證」。
6. **`sys_pwd_custody` 首寫**：schema-gate 集外表、測試需清理腿；入集與否實作期判。
7. 「五前置三項本就要建、增量僅四樣」（005 §3 #4 原句）細目全 repo 查無——本檔 §2 以端點表重建 scope
   論證，不再引該句。
8. rev4 as-built 四處瑕疵不可照抄：`password-card.vue` 之 `verify.*` 假功能、`deletedAt` 孤兒鍵、
   `scroll-x` 未隨欄寬改、跨頁借鍵。
9. 活書配額：§6 預估 +20 仍在 160 內；撞頂＝ADR 0062 輕量軌。

## §9 rev4 參照清單（plan research 前置素材；ADR 0019：高度參照、重打字消化、註解重寫）

**rev4 碼與文件（`../fork260509-rev4/`、唯讀）**：`specs/011-user-admin`（spec Clarifications 五題、FR-004／
FR-007／FR-036／FR-043）、`specs/014-user-center`、`specs/015-pwd-custody`（Clarifications「強制態不豁免冷卻」）、
`specs/007-login-throttle`（unlock）、`specs/009-role-admin`（no-escalation 零實作）；`rust-api/server/src/
handler/user.rs`、`handler/user_center.rs`、`handler/route.rs`（`SELF_SERVICE_ROUTES`）、`model/facade/sys_user.rs`
（`insert`／`update`／`delete_one_locked`／`kick`／`reset_password`／`restore`／`change_own_password`）、
`model/facade/sys_token.rs::revoke_all_of_user`、`model/password.rs`、`middleware/mod.rs`（`pwd_gate_mw`、
本刀不搬）；ADR rev4:0006（軟刪慣例）、rev4:0053（島 I 總綱）、rev4:0054（密碼政策）、rev4:0055（初始密碼
分期）、rev4:0065（自助白名單）、rev4:0067（首登換密、本刀不搬）；LESSONS rev4:L-121（`\w{6,18}` 擋含連字號
密碼零請求）、rev4:L-145（熱套 casbin 後重登）、rev4:L-149（constant route 登出競態）；`base-web/src/views/
manage/user/{index.vue, modules/user-operate-drawer.vue, modules/user-unlock-modal.vue}`、
`views/user-center/{index.vue, modules/password-card.vue}`、`components/custom/pwd-gen-modal.vue`、
`hooks/business/pwd-policy.ts`、`service/api/rev4-user-admin.ts`、`views/_builtin/login/modules/pwd-login.vue`。

**rev5 拍板差異點（rev4 做法 ｜ rev5 現行 ｜ 本刀處置；不得帶回者標 ✗）**

| # | rev4 | rev5 現行 | 本刀 |
|---|---|---|---|
| 1 | 清空語意 `Some("")` | ADR 0023 三態 `tristate` | updateUser 三態；`blank_to_none` 僅 addUser |
| 2 | userName 等值放行 | sys_role「出現即拒」 | 出現即拒；前端 wrapper 剝 userName |
| 3 | 拒因 BizData 攜參（多鍵） | ADR 0022 純 key | 只開密碼二鍵（Q19） |
| 4 | no-escalation 零實作 | 空掛點 | 本刀實作於 handler（Q09／Q28） |
| 5 | 稽核詞彙大寫 8 值 | 小寫 5 值 macro | 新增小寫 `kick`／`reset_password` |
| 6 | op-log real_ip fail-open | `real_ip NOT NULL` F3① | 每寫端 fail-closed |
| 7 | denylist TTL＝access 窗 | TTL＝refresh 全壽命 | 沿 rev5 |
| 8 | logout 撤整鏈 | 只撤呈遞列（ADR 0059） | kick／停用撤全 active、不動 rotated |
| 9 | `needChangePwd` 欄 ✗ | 不帶回 | B-134 |
| 10 | `SELF_SERVICE_ROUTES` | 「不帶回——前提未成立」 | 本刀帶回（Q22） |
| 11 | 每鈕 hasAuth gating | role／menu 不 gating | user 頁 gating＝例外釋義（Q10） |
| 12 | 角色鍵 `roleId` | 統一 `id` | 沿 rev5 |
| 13 | 併 `Api.SystemManage` | 獨立 `Api.<Domain>` 新檔 | `Api.UserAdmin.*`／`Api.UserCenter.*` |
| 14 | `createTime／createBy` | `createdAt／createdBy` | 沿 rev5 |
| 15 | 借跨頁 i18n 鍵 ✗ | 各頁自備 | `page.manage.user.*` 自備 |
| 16 | 未知 setting_type→2222 | →5000 | 沿 rev5 |
| 17 | unlock dimension 預設帳號維 | 必給、缺席 2222 | modal 顯式帶 |
| 18 | 動詞不符→5003 | →4040（ADR 0031） | delete 用 DELETE |
| 19 | `scroll-x` 962 未改 ✗ | Σ 欄寬不變式 | 同批改 |
| 20 | 授權 modal 殘影 ✗ | B-129 列缺陷 | 先修再照抄 |
| 21 | 新檔標記 `MODAL-WIRING(h)` | `[rev5-inline <軌道>+ <NNN>]` | 照範本 |
| 22 | 首登強制換密整包 ✗ | — | B-134 |
| 23 | 寫端 super-only 不對稱留置 | — | 本刀下放＋no-escalation（Q09） |
