---
id: "0063"
title: 憲法 Amendment 1.9.0——§I.7 第九座行為島（島 I 使用者域治理、含 I7 no-escalation 包含規則）＋§III.2 MANAGE-PAGE-WIRING 用途 (v)(vi)（user 管理頁接真＋個人中心改密頁）＋LOGIN-CAPTCHA-WIRING 凍結位 (ii) 開立（登入表單規則放寬）＋no-escalation 掛點射程分工與按鈕 gating 例外釋義
date: 2026-08-27
status: accepted
supersedes: []
superseded_by: []
provenance: "007-user-password-admin 之 T001／T003（tasks.md Phase 1 主線任務）；授權鏈＝plan.md Constitution Check 第 2／7／9 題（條件通過、Amendment 先行）＋research R10 治理原料；拍板鏈＝docs/brainstorms/007-user-password-admin.md §3 四十一題（2026-08-25 user 逐題親決：Q06／Q07 一次 MINOR 兩處、Q09 寫端下放＋no-escalation、Q10 七碼逐鈕 gating 之例外釋義、Q22 自助白名單、Q25 登入表單降 required-only）＋§3b grilling 十八題（2026-08-26：G1 T 不濾角色狀態／G2 同級互管允許／G3 self 五不／G6 unlock 帳號維套規則／G8 前端不預判規則）＋spec.md Clarifications 2026-08-26（/speckit-clarify Q1 持 R_SUPER 者之 A 視為全集、Q3 roleIds 期望全集全量替換）＋U0 兩題 user 親決 2026-08-27（I7 條文逐字具名 R_SUPER；島 I header 取完整形、含 I6 位刻意空缺說明）；島 I 條文藍本＝rev4:ADR 0053 總綱／rev4:ADR 0054 密碼政策＋rev4 憲法 §I.7 島 I 段 I1～I5 原文（rev4:ADR 0067 之 I6 不帶回、留 B-134）"
tags: [constitution, governance, behavior-island, user-domain, authz, password, fork-delta]
---

## 背景

007-user-password-admin（刀 B、使用者＋密碼管理）撞到**兩個空凍結位＋一個明文凍結位**，
外加一筆須留痕的射程分工釋義——皆為憲法自身備有的授權路徑、非違規待辯護：

1. **§I.7 行為島**——本刀落地使用者域治理狀態機（per-user 鎖序與 lock-then-redecide、斷權
   四路同交易撤票、seed 帳號與自身結構保護、軟刪硬刪指派＋復原零回灌、密碼政策單一驗證點、
   寫端授權下放之 no-escalation 包含規則），依 §I.7 進場規則須以 MINOR Amendment 入憲。
   I1～I5 主體沿 rev4 已驗證形（rev4 憲法 §I.7 島 I 段原文；設計理據＝rev4:ADR 0053 總綱／
   rev4:ADR 0054 密碼政策）。**I7 no-escalation 包含規則為 rev5 專屬新條**（brainstorm §3 Q09
   user 親決「下放寫端＋實作 no-escalation」、非建議項；A 之全集定義由 spec Clarifications
   釘字）。★字母記法沿 rev4：本島記 **I**；rev5 §I.7 至此為 A～I 九座。
2. **§III.2 `BASE-WEB-MANAGE-PAGE-WIRING` 兩個新用途**——user 管理頁三檔與個人中心父層皆為
   upstream 既有 demo 面，其 fetch 打的端點正是本刀補齊對象。現有用途 (i)～(iv) 分別授權
   IP 規則頁進場／role·menu 頁 CRUD 接真／三顆授權 modal 接真／policy-archive 頁進場，
   **涵蓋不到** user 頁與個人中心 ⇒ 依「同軌道內的未列用途不自動授權」須 Amendment 加兩用途。
3. **§III.2 `BASE-WEB-LOGIN-CAPTCHA-WIRING` 之明文凍結位 (ii) 開立**——該軌道 (i) 列的紀律欄
   末句逐字寫著「用途 (ii)（`formRules` 放寬）不在授權內」，`pwd-login.vue`:42 之 rev5 inline
   註解亦逐字記「★(ii) formRules 放寬不帶回——延改密端點刀」。本刀即該「改密端點刀」：B-089
   （前端正則擋掉合規密碼、零請求零 toast）一旦寫端進場即成 user 可見真缺陷 ⇒ 開立該凍結位、
   同批刪去兩處「不在授權內／不帶回」的自陳。
4. **no-escalation 掛點射程分工＋按鈕 gating 例外釋義**（款三、ADR 級）——ADR 0022 決定 3 已
   凍結「middleware 四參掛點 `no_escalation_check` 恆放行」；本刀在 handler 鎖內新增具名純函式
   判定，兩實作位並存易被日後讀者誤判為「重複實作」或「該把 middleware 那支補起來」，須明文
   分工留痕（**補充** ADR 0022 決定 3、**不** supersede）。按鈕 gating 則相反：role／menu 頁
   拍板「不做 hasAuth gating」（ADR 0053 款二 (iii) 列逐字），本刀 user 頁卻要七碼逐鈕 gating
   ——判準須寫下來，否則下一把刀只能靠猜。

★**T001 前置查證結論**（2026-08-27 主線親跑、名單以定數落；憑證為 dev 庫實測與逐位 diff）：

- `manage_user` 之 menu 維政策列＝`{R_SUPER, R_ADMIN}`（**非僅 R_SUPER**）；`manage_role`／
  `manage_menu`／`user-center` 皆**僅** `R_SUPER`。此即款三 gating 判準的事實底座。
- 七枚 user 按鈕碼（`user:add`／`user:edit`／`user:delete`／`user:kick`／`user:reset-pwd`／
  `user:restore`／`user:unlock`）seed 全在，其中 `user:edit` 已勾 `R_ADMIN`。
- `src/views/manage/user/modules/user-search.vue` 對 rev4 同檔與最原始源 `example` 基線**兩向
  逐位 diff 零差異** ⇒ 判定零改動、**不入** (v) 檔級名單（日後出現任何 diff＝紅）。
- `getAllEndpoints` 現況回應長度實測 **35**（＝ROUTES 之 `Protection::Policy` 全集）；dev 庫
  `p` 政策列之 distinct path×method＝50（＝35 已實作＋本刀 10 支預埋＋audit 5 支未實作），
  兩數的差為預埋量、非漂移。
- `page.manage.user` 兩語各 19 葉鍵、`page.userCenter` **尚不存在**（(vi) 要開的正是新 top-level
  命名空間，落在 §III.2「零新 key」釋義所指之須 Amendment 面）。

若實作期發現名單外 base-web 既有檔非動不可（編排防呆⑥空間邊界會擋下）＝名單擴列＝回本節走
§V.2、非默改。

## 決定

以**一筆 MINOR Amendment**（1.8.0 → 1.9.0）處理款一、款二；款三為 ADR 級射程釋義、**不入
條文、不參與 bump**。依 §V.3，款一分級為「行為島隨刀進場（§I.7 填充）」、款二為「軌道授權
邊界擴展（新用途）」＝MINOR。

### 款一：§I.7 新增第九座行為島（島 I），條文逐字如下

> **I. 使用者域治理**（007-user-password-admin 進場；I1～I5 沿 rev4 已驗證形〔rev4:ADR 0053
> 總綱／rev4:ADR 0054 密碼政策〕、**I7 no-escalation 包含規則為本刀新拍板**〔編號 0063〕；
> 字母沿 rev4 記 I、★**I6 位刻意空缺**＝rev4 之密碼經手與首登強制換密〔rev4:ADR 0067〕本刀
> 不做、留 B-134，日後兌現時回填該位）
>
> - **I1 寫端鎖序與 lock-then-redecide**：一切以**既有**使用者為標的之使用者域寫端 MUST 於
>   交易起手取得與登入／換發同源的 per-user advisory 鎖；域內固定鎖序 MUST 為 advisory(uid)→
>   標的使用者列 `FOR UPDATE`（復原用已刪列版）→角色列（僅比對需要時讀、識別升序）→角色指派
>   列寫入，禁反向；一切守門判定 MUST 鎖內重驗（lock-then-redecide、永不信 pre-read）。新增
>   使用者豁免 per-user 鎖（新識別對並發不可見；並發同名保護＝帳號名活性唯一約束）；批次刪除
>   依識別去重升序逐一取鎖。帳號名與信箱之活性唯一索引為復原衝突守門之顯式前提。★advisory
>   key space 沿用登入之 uid 鍵（同用途擴消費者、與島 H1 域鎖之高位自描述常數不碰撞、核過）。
>   ★方向反轉（拆散序列化、改回無鎖 pre-read）＝MAJOR。
> - **I2 斷權即時性與分碼不互換**：停用／刪除／重設密碼 MUST 同交易撤銷標的全部 active 票
>   （rotated 列不動、重放仍走既有重用偵測）並落 session 事件；管理員踢除同形、但為**獨立
>   reason**。動作序 MUST 權威優先（業務寫＋票作廢＋稽核同一交易落定→commit→失效廣播
>   best-effort、存活時間覆蓋換發憑證壽命）；廣播失敗只結構化告警、**權威儲存為準**。換發流程
>   MUST 於鎖內重驗使用者活性（啟用且未軟刪），不活即拒——此為既有 token 狀態機**新增判定腿**、
>   非 fail 方向反轉。MUST NOT 為此新增每請求活性判定。撤銷類、單一會話頂替類與管理員踢除類之
>   體驗碼與文案鍵 MUST NOT 互換（三者各自對應、勿「統一」）。★方向反轉（拔鎖內重驗、改廣播
>   優先、改為每請求活性判定）＝MAJOR。
> - **I3 seed 帳號與自身結構保護**：前三個種子帳號 MUST 不可刪；第一個（Super）MUST 恆禁停用、
>   恆禁解除其超管角色指派（不因操作者身分而異）——系統恆有至少一個活躍且啟用的超級管理員
>   （結構保證、不需動態計數）；Super MAY 被踢除、被重設密碼。操作者 MUST NOT 刪除／停用／
>   踢除自己、MUST NOT 變更自己的角色指派、MUST NOT 以管理端重設自己的密碼（自助改密走自助
>   端點）；操作者 MAY 改自己的非角色欄與會話政策。守門為碼內常數形。
> - **I4 軟刪硬刪指派＋復原零回灌**：使用者軟刪 MUST 同交易硬刪其全部角色指派列（零幽靈掛載、
>   角色域掛載計數守門保持誠實）；復原 MUST NOT 回灌任何指派（復原後零角色、須重新指派）、
>   狀態保留刪除前原值；同帳號名重建之新使用者 MUST NOT 經任何路徑繼承舊實例角色。批次刪除
>   逐項驗證、任一違規（含已刪識別）**整批拒**（no-partial、單一交易）。
> - **I5 密碼政策單一驗證點＋登入不驗＋三重不洩**：密碼政策驗證 MUST 為單一驗證點（建帳／
>   管理端重設／自助改密三入口共用、零分叉）、政策鍵單一快照讀取、違規 MUST 一次收集全部；
>   長度單位＝字元、另加固定位元組上界 ≤登入端形制上限；「禁止密碼與帳號名相同」＝大小寫
>   不敏感相等。★**登入路徑 MUST NOT 驗政策**——政策是設密面的守門、不是登入面的守門；把它
>   掛上登入即令既存帳號的合法憑證因政策事後調整而失效。密碼明文與雜湊 MUST NOT 洩漏於任何
>   面：承載密碼之 DTO 除錯輸出 MUST 遮蔽（不得預設印出）；操作稽核 payload MUST NOT 含密碼
>   明文／雜湊；API 回應 MUST NOT 含密碼；密碼雜湊 MUST NOT 於持有列鎖期間計算。★方向反轉
>   （拆單一驗證點、拔遮蔽、把政策掛上登入路徑）＝MAJOR。
> - **I7 no-escalation 包含規則**（rev5 專屬新條）：使用者域寫端授權 MAY 由超管於運行期下放
>   給其他角色（seed 預設仍 super-only、下放為可開關能力、非預設態）；下放後**一切受規則約束
>   之寫端**（使用者域寫端全集＋帳號維解鎖）MUST 於鎖內、任何寫入前判 `T ⊆ A ∧ N ⊆ A`——
>   A＝操作者現役角色集（濾軟刪與停用角色、DB-fresh；★持 `R_SUPER` 者之 A 視為全集）、
>   T＝標的全部指派列（**不**濾角色狀態）、N＝寫後標的角色集；違者 MUST fail-closed 拒絕
>   （純 key、不洩漏角色差集、零變更零稽核）。seed 保護（I3）與 self 諸不 MUST **先於**本規則
>   判定；同級互管允許（零特例）；來源維解鎖不套。判定 MUST 以具名純函式單點實作、諸寫端共用；
>   前端 MUST NOT 預判本規則（後端為唯一裁判）。★方向反轉（拔守門、改 fail-open、改由前端
>   預判、把某支受約束寫端移出射程）＝MAJOR。
> - 常數（seed 帳號識別集、政策鍵名與門檻、設密冷卻與改密節流之窗與次數、事件 reason 字面集、
>   自助路由白名單成員、advisory key 值）＝活書／ADR 級、不入條文。

★**落字與 rev4 原文的差異六處**（防「照抄 rev4」回帶已翻案語意；research R2 為完整清單）：
①I1 不抄 rev4 之「與 login/refresh 共鎖」括號措辭中隱含的實作綁定，改寫為方向面＋key space
不碰撞句（島 H1 已凍結該紀律、此處只擴消費者）；②I2 刪 rev4 之「即時性契約＝廣播成功即時、
失敗殘留窗上界 access token 壽命」量測句（屬活書級）、補「換發鎖內重驗＝新增判定腿非方向
反轉」與「三 reason 不互換」——rev4 只寫兩類、rev5 為三類（新增管理員踢除之獨立 reason）；
③I3 由 rev4 之「self 四不」擴為「self 諸不」並明列「不得以管理端重設自己密碼」（G3 親決）；
④I4 刪 rev4「fail-fast」措辭（與 rev5 之 no-partial 同義、避免兩詞並存）；⑤I5 **新增「登入
路徑 MUST NOT 驗政策」整句**——rev4 未寫，而 rev5 seed 三帳號密碼為 6 字元＜政策 min 8，
不寫即結構性自鎖（本刀 T043 有機器守）；⑥I7 全新。rev4 之 I6（密碼經手與首登強制換密）**整條
不帶回**——custody 表本刀只借時戳、不做 EXISTS 經手判定，該條連同其「硬閘每請求 EXISTS 判定
與 I2 射程區隔」段留待 B-134 兌現時回填 I6 位。

### 款二：§III.2 加三列，表列逐字如下

★**用途索引對應**（防混淆）：spec／plan／tasks 以本刀序號稱三用途為 (v)(vi)(vii)；**憲法表內
用途索引是 per-軌道的**，故落字為 `BASE-WEB-MANAGE-PAGE-WIRING` 之 **(v)**／**(vi)** 與
`BASE-WEB-LOGIN-CAPTCHA-WIRING` 之 **(ii)**。此非文字美化：`fork-delta-lint` 驗的是
（軌道×用途×檔案）三元組硬邊界，用途後綴寫錯即紅；`pwd-login.vue` 既有標記亦為
`BASE-WEB-LOGIN-CAPTCHA-WIRING(i)`。本刀之 (vii) 一律讀作 `LOGIN-CAPTCHA-WIRING(ii)`。

> | **★BASE-WEB-MANAGE-PAGE-WIRING** | (v) user 管理頁接真（含回收桶、操作下拉、解鎖入口、七碼 gating） | `src/views/manage/user/index.vue`／`src/views/manage/user/modules/user-operate-drawer.vue`（兩支＝修改型，逐行 `原行:`）／`src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型圈界；僅限 `page:` 樹既有 `manage.user` 子命名空間之資料級補鍵）／`src/typings/app.d.ts`（1 塊，新增型圈界；僅限 `App.I18n.Schema.page` 之 `manage.user` 對應型節） | 嚴格限 demo 殼接真後端（列表／搜尋／新增編輯 drawer／單刪批刪／回收桶 toggle 切兩資料源／操作下拉之踢除·重設密碼·隨機密碼／頁首解鎖 modal 掛載／七枚按鈕碼逐鈕 gating／memo 欄純文字插值）；★同目錄 `user-search.vue` 經 rev4 與最原始源基線兩向逐位 diff 判定零改動、**明文不入名單**（本刀出現任何 diff＝紅）；`modules/user-unlock-modal.vue`／`src/components/custom/pwd-gen-modal.vue`／`src/typings/api/rev5-user-admin.d.ts`／`src/service/api/rev5-user-admin.ts` 為 rev5 新增型新檔（檔頭標記、不入名冊——承 ADR 0021 款 1）；兩語鍵集 MUST 相等；`route:` 樹零新增（`manage_user` route 鍵 upstream 既在）；路由外掛產物四檔零變動（不新增 view 頁）；表格 `scroll-x`＝Σ 欄寬不變式同批改 |
> | **★BASE-WEB-MANAGE-PAGE-WIRING** | (vi) 個人中心改密頁進場 | `src/views/user-center/index.vue`（修改型，逐行 `原行:`）／`src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型圈界；僅限 `page:` 樹新 top-level `userCenter` 命名空間）／`src/typings/app.d.ts`（1 塊，新增型圈界；僅限 `App.I18n.Schema.page` 之 `userCenter` 型節） | 嚴格限父層骨架改寫＋只掛「修改密碼」卡（其餘卡位留白、不補 rev4 之 basic-info／email／phone 三卡）；★`src/views/user-center/modules/password-card.vue`／`src/hooks/business/pwd-policy.ts`／`src/typings/api/rev5-user-center.d.ts`／`src/service/api/rev5-user-center.ts` 為 rev5 新增型新檔、不入名冊；入口沿既有頭像下拉（`user-avatar.vue` 零 diff）；兩語鍵集 MUST 相等；`route:` 樹零新增（`user-center` route 鍵 upstream 既在）；路由外掛產物四檔零變動 |
> | **★BASE-WEB-LOGIN-CAPTCHA-WIRING** | (ii) 登入表單規則放寬 | `src/views/_builtin/login/modules/pwd-login.vue`（修改型，逐行 `原行:`） | 嚴格限 `formRules` 之 `pwd`／`userName` 由格式正則改必填規則（前端只驗必填、格式判定交後端——設得進的密碼必須登得進）；★MUST NOT 動 `src/constants/reg.ts`（全域正則為其他表單共用）；`register`／`reset-pwd` 兩支 stub 不動；用途 (i) 之 captcha 軟區條件渲染行為零變更 |

★**同批刪句兩處**（凍結位開立的必然後果、不刪即自相矛盾）：①`BASE-WEB-LOGIN-CAPTCHA-WIRING`
(i) 列紀律欄末句「。用途 (ii)（`formRules` 放寬）不在授權內」整句刪去；②`pwd-login.vue`:42
之 rev5 inline 註解內「★(ii) formRules 放寬不帶回——R3-12、延改密端點刀」改寫為 as-built
（該檔改動屬本款授權範圍、隨 (ii) 之實作單元同批）。

檔級名單為硬邊界（§III.2 表外宣告 1）：(v) 修改型**恰 2 支**、(vi) 修改型**恰 1 支**、
(ii) 修改型**恰 1 支**；三用途之 base-web 既有 i18n 檔（兩語 locale＋`app.d.ts`）逐支以路徑
寫出。後端拒因鍵（`backend.biz.user.*` 二十鍵＋`backend.auth.session.kickedByAdmin`）落於兩語
locale 之 `backend:` 樹與 `app.d.ts` 之 backend 型節——其授權在**既有** ★BASE-WEB-I18N-WIRING
(ii)(iii) 射程內、不隨本款擴列（同 ADR 0040／0048／0053 判法：硬閘按「既有檔」判、與授權
來源無關）；`zh-tw.ts` 為 rev5 純新增治理孤立檔（ADR 0021 款 1）、不涉名冊。

### 款三：no-escalation 掛點射程分工＋按鈕 gating 例外釋義（ADR 級、不入條文）

**1. 兩實作位的射程分工**（補充 ADR 0022 決定 3、不 supersede）：

| 實作位 | 判定單位 | 現行行為 | 為何不合併 |
|---|---|---|---|
| middleware `auth::enforce::no_escalation_check`（四參） | 路徑級「上限位」 | 恆 `Ok`（ADR 0022 決定 3 凍結） | 中介層**取不到 body**（body 只能消費一次、extractor 順序在 handler）⇒ 拿不到 `N`；亦**取不到鎖內的 `T`**（標的指派列須於 per-user 鎖內現查，pre-read 會與 I1 之 lock-then-redecide 直接相牴） |
| handler 鎖內具名純函式 `auth::no_escalation::assert_no_escalation` | body 級指派集 | 依 I7 判 `T ⊆ A ∧ N ⊆ A` | 唯一能同時看見 A／T／N 三元且在鎖內的位置 |

★本刀**不動** middleware 那支（不翻 ADR 0022 決定 3、不改其簽名、不改其恆 `Ok`）。日後讀者
見兩位並存時的正解＝**分工**，不是「重複實作」、也不是「該把 middleware 那支補起來」——要把
判定上提中介層＝須先解掉 body 消費與鎖內現查兩個結構性前提，屬新拍板、走 §V.2。

**2. 按鈕碼 gating 例外釋義**（判準寫死、消滅「靠猜」）：

> **判準＝該頁之 menu 維政策是否僅 `R_SUPER`。** 僅 `R_SUPER` ⇒ 門在頁級、頁內不做逐鈕
> `hasAuth` gating（進得來的一定是超管、gating 是裝飾）；**非**僅 `R_SUPER` ⇒ 該頁對非超管
> 可達、頁內 MUST 逐鈕 gating（否則出現「看得到按不動」的假可用面）。

實測底座（2026-08-27）：`manage_role`／`manage_menu` 之 menu 維政策皆僅 `R_SUPER` ⇒ ADR 0053
款二 (iii) 列「role 頁三鈕不做 hasAuth gating（門在頁級）」之拍板**不變**；`manage_user` 之
menu 維政策為 `{R_SUPER, R_ADMIN}` ⇒ user 頁 MUST 七碼逐鈕 gating。兩者不是前後不一致，是
同一判準的兩側。★gating 治理**與端點授權各自獨立**：按鈕碼有、端點無 ⇒ 鈕可見、按下 5003
（誠實）；端點有、按鈕碼無 ⇒ 鈕不見、API 仍可達——由超管在 006 的兩顆 modal 一併治理，前端
MUST NOT 代為對齊。

## 考慮過的替代案與棄用理由

- **I7 條文不具名 `R_SUPER`、改寫「持系統最高權限角色者」**（U0 題①選項 b）——棄（user 親決
  取具名）。「常數留活書」的慣例射程是**量測值與可調門檻**（島 H1 之 advisory key 值、島 G6 之
  封死集列數），不是**結構性身分**；同節 G6 條文本身即逐字寫「MUST NOT 授予非 R_SUPER 角色」，
  具名在 §I.7 已有先例。不具名的代價是「系統最高權限角色」在 rev5 無第二個定義來源、讀者仍須
  跳活書。
- **I7 之超管全集完全不入條文、只落 ADR 與活書**（U0 題①選項 c）——棄。條文將對 seed Super
  成為**假述**：seed 之 Super 只持 `{R_SUPER}`，照字面 `T ⊆ A` 連編輯持 `{R_ADMIN}` 的 Admin
  都不成立；憲法是唯一權威，照條文重寫實作會做出「超管什麼都不能改」的系統。
- **改以「角色分級（rank）」模型取代包含規則**——棄（brainstorm §3 Q09-2）。rank 需要 schema
  欄與整套治理 UI（本刀硬預期零 migration），且對「同級互管」與「零角色帳號」兩個既定行為要
  另立特例；包含規則零 schema、零特例分支，且 A 之全集定義使超管路徑天然閉合。
- **把 no-escalation 判定上提 middleware（帶 body 改造）**——棄（款三表已列理由）；並列入
  spec Out of Scope。
- **島 I 沿 rev4 連 I6 一併帶回**——棄（brainstorm §3 Q02 user 親決「首登強制改密本刀不做」）。
  I6 整包需 `needChangePwd` 身分欄、每請求 EXISTS 硬閘、強制頁與 router guard；本刀只借 custody
  表的時戳做設密冷卻。條號**刻意留空**而非往前遞補，使 B-134 兌現時可直接回填、不動已凍結編號。
- **島 I header 走精簡形（只寫進場刀與條區間）**（U0 題②選項 b）——棄（user 親決取完整形）。
  島 G／H 的 header 都帶承襲 ADR 指針與字母沿革；且 I6 跳號若不在憲法本體留痕，讀者只能猜，
  而 ADR 與 BACKLOG 都不是憲法讀者的必經路徑。
- **(vii) 落在 `MANAGE-PAGE-WIRING` 之下作為第七用途**——棄。`pwd-login.vue` 不是 manage 頁，
  且該軌道之 (ii) 凍結位是**逐字為 `formRules` 放寬**保留的；落錯軌道會讓
  `fork-delta-lint` 的三元組硬邊界失去意義（借一個在冊軌道名即可在無授權檔上開標記＝B-068
  修掉的正是這個病）。
- **把款三之 gating 判準寫進憲法條文**——棄。判準的輸入是 seed 的 menu 維政策列（資料態、隨
  seed 演化），寫進條文即每次 seed 調整都可能要 Amendment；ADR 級承載＋活書 §8 條目即足。

## 後果

- **硬閘解除點**：本 ADR accepted 且憲法 bump 落地後，「T003 accepted 前不得動任何 base-web
  既有檔」之硬閘解除（`views/manage/user/index.vue`／`modules/user-operate-drawer.vue`／
  `views/user-center/index.vue`／`views/_builtin/login/modules/pwd-login.vue`／兩語 locale 之
  `page:` 樹／`app.d.ts` 之 page 型節自此有授權前提；純新增 wrapper／typings／新檔依 ADR 0021
  款 1 本就不受閘；純後端單元不受閘）。
- **島 I 方向性面凍結**（MAJOR 界定逐條列於條文）：後續刀拆散 per-user 序列化或改回無鎖
  pre-read、拔換發鎖內重驗或改廣播優先或改每請求活性判定、拆密碼政策單一驗證點或把政策掛上
  登入路徑、拔 no-escalation 守門或改 fail-open 或改由前端預判——皆 MAJOR。
- **§I.7 島數 8 → 9**（A～I）；§III.2 表列數 12 → 15。新列變異自證照 ADR 0040 後果之形
  （暫改 (v) 列範圍欄任一路徑為裸措辭 → `fork-delta-lint` 須當場紅 → 還原），於本 Amendment
  落地 commit 前主線親跑、關鍵行寫進 commit message。
- **`LOGIN-CAPTCHA-WIRING` 自此為二用途軌道**；其 (i) 列紀律欄之「用途 (ii) 不在授權內」句
  與 `pwd-login.vue`:42 之「不帶回」自陳自此為假述，同批刪改（款二 ★同批刪句兩處）。
- **ADR 0022 決定 3 續行有效**：middleware 四參掛點不動、不 supersede；本 ADR 款三為其射程
  補充。日後若要改動該掛點行為，仍以 ADR 0022 為翻案對象。
- **ADR 0053 款二 (iii) 列之 role 頁不 gating 拍板不變**：款三判準是其**上位釋義**、不是翻案
  ——兩頁走同一判準、結論不同僅因 menu 維政策不同。
- **後續四支 ADR 的射程邊界**（本刀同分支落檔、編號 0064～0067）：明細攜參通道／自助路由
  白名單／設密冷卻與改密節流／ADR 0042 措辭訂正與 ADR 0053 觸發矩陣補列——皆**不重複**本檔
  已凍結之島 I 條文，只承載常數、掛點與訂正。
- 本檔為 §V.2 之提案；user 已於 2026-08-27 親決兩題後轉 accepted，憲法改動與本檔同一 commit、
  緊接 `python3 tools/docs-sync.py generate`。
