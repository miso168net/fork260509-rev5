---
id: "0028"
title: 憲法 Amendment 1.2.0→1.3.0——§III.2 首批四條 ★ 軌道八用途授權＋§I.7 首批五座行為島入憲
date: 2026-08-09
status: accepted
supersedes: []
superseded_by: []
provenance: "003-auth-session 之 FR-028／FR-029；形制輸入＝research R8；★軌道範圍欄素材＝spec「★ 軌道逐處登記」15 列表（量測日 2026-08-09、基線 fork260509-soybean-admin-base@example）；fail-* 方向素材＝research R5 降級矩陣；憲法 §V.2 Amendment 流程、§V.3 MINOR 判準"
tags: [constitution, amendment, fork-delta, behavior-island, auth]
---

## 背景

憲法 §III.2 自 v1.0.0 起是空的凍結位，明文「尚未授權任何 ★ 軌道——第一刀撞到 base-web inline
需求時，以 §V.2 Amendment 開立第一個軌道與其用途」。§I.7 同樣是空的凍結位，只有進場規則與
承襲指針。003-auth-session 是第一把同時撞到兩者的刀：

- **§III.2 面**：後端補齊六支端點後，base-web 必須接線才看得到成果。逐處勘查得 15 個落點，
  其中 3 個屬 §III.1 既有的 `BASE-WEB-ADAPT` 軌道（`.env*`），其餘 **12 處分屬四條尚未存在的
  ★ 軌道、八個用途**。在 §III.2 開立這四條軌道之前，動任何一處都是無授權 inline。
- **§I.7 面**：本刀落地五台狀態機（token rotation／single-session／denylist 撤銷／idle 逾時／
  登入失敗節流）。§IV 第 9 題問「屬該入憲而未入憲的新行為島、是否隨本刀排入 Amendment」——
  不排即當場擋。更實質的理由是：這五台機器各有刻意選定的 fail-* 方向（且彼此方向不一致，
  例如 idle 是 fail-open 而 denylist 是 fail-closed、節流設定缺失是 fail-open 而 idle timeout
  設定缺失是 fail-loud），不入憲則日後任何一次方向反轉都只是普通改碼、沒有 MAJOR 閘擋著。

兩者同屬 §V.3 的 MINOR（「新增 ★ 軌道」與「行為島隨刀進場（§I.7 填充）」各自列名），故合計
一次 bump：**1.2.0 → 1.3.0**。

**順序相依**：本 Amendment 必須先於 `tools/fork-delta-lint.py` 的「軌道名 ∈ 授權名冊」斷言
（FR-030）落地——名冊的來源就是本次新建的 §III.2 表格，表格不存在則斷言無所依附。

## 決定

### 一、§III.2 新增機器可解表格（四軌道、八用途）

沿 §III.1 的 markdown 表格慣例，**逐軌道逐用途一列**，欄位＝`| 軌道 | 用途 | 範圍（檔案） | 紀律 |`；
軌道名以 `**★NAME**` 包覆（掃描端剝 `**` 與 `★`）。掃描錨＝本表標題列之後、以 `^|` 起的資料列，
跳分隔列。**授權名冊＝§III.2 ★ 軌道 ∪ §III.1 三軌道。**

| 軌道 | 用途 | 範圍（檔案） | 紀律 |
|---|---|---|---|
| **★BASE-WEB-AUTH-WIRING** | (a) constant routes 合併 | `src/store/modules/route/index.ts`（1 處，修改型） | 僅限 `initConstantRoute` 之 else 分支；MUST 為**併入** static 常量集而非取代（seed `constant=TRUE` 為 0 列，取代會清空 login／403／404／500／iframe-page 五條 builtin）；不得擴及 route store 其他分支 |
| **★BASE-WEB-AUTH-WIRING** | (b) 三表單 stub 化 | `src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue`（各 2 處，修改型） | 僅改 import 指向 stub wrapper＋消滅假成功 toast；不動表單欄位、驗證規則與版面 |
| **★BASE-WEB-AUTH-WIRING** | (c) captcha hook 改打 stub | `src/hooks/business/captcha.ts`（4 處，修改型） | 僅改請求目標為 `/auth/sendCaptcha`＋移除 500ms 假延遲與假成功 toast；hook 對外簽名不變 |
| **★BASE-WEB-LOGIN-CAPTCHA-WIRING** | (i) 登入頁 captcha 軟區 | `src/store/modules/auth/index.ts`（修改型）／`src/views/_builtin/login/modules/pwd-login.vue`（修改型＋新增型） | login 簽名加 captcha 參並串通失敗 msg 回傳鏈；軟區為條件渲染，**非軟區時零行為變更**。★用途 (ii)（`formRules` 放寬）**不在本次授權**，延改密端點刀 |
| **★BASE-WEB-I18N-WIRING** | (i) 後端 msg 轉譯 | `src/service/request/index.ts`（2 處修改型＋1 塊新增型） | `translateBackendMsg`／`translateDetailValue` 走 `$t` 並以原文 fallback；未命中 MUST graceful fallback，不得吞錯亦不得顯裸 key |
| **★BASE-WEB-I18N-WIRING** | (ii) locale backend 樹 | `src/locales/langs/{en-us,zh-cn}.ts`（各 1 塊，新增型） | 插入錨為**獨佔一行**的 `  backend: {`；兩語鍵集 MUST 相等；譯文以 `contracts/msg-keys.md` 為權威 |
| **★BASE-WEB-I18N-WIRING** | (iii) Schema backend 型節 | `src/typings/app.d.ts`（1 處，修改型） | 僅補 `App.I18n.Schema` 之 `backend` **必填**型節。★LangType 擴充／locale 註冊／`zh-tw.ts` 標型重構**不在本次授權**，仍延前端 UI 刀 |
| **★BASE-WEB-LOGOUT-UX-WIRING** | (i) 登出前撤銷接線 | `src/layouts/modules/global-header/components/user-avatar.vue`（3 處，修改型） | `onPositiveClick` 改 async、登出前 best-effort `await fetchLogout(...)`，**失敗不得阻斷** `resetStore()`。★用途 (ii)（reLogin toast）**不在本次授權** |

**表外三項紀律**（不入表、屬本節既有骨架之適用宣告）：

1. **範圍欄的處數為現階段估值**，實作期以 `rev5-inline` 標記實數為準；檔級名單則是硬邊界——
   名單外的 base-web 既有檔一律無授權，需要動即回本節走 Amendment。
2. **本刀不開的兩條**：承襲指針散文提及的 `MODAL-WIRING` 與 `BASE-WEB-DEVPROXY-WIRING`
   **不在名冊**（rev5 無 modal 治理需求；devproxy 由 §III.1 ADAPT 軌道的 `.env*` 涵蓋）。
3. **新增型 `NAME+` 標記不入名冊**（承 ADR 0021 款 1）——名冊斷言的射程僅修改型（帶 `原行:`）。

### 二、§I.7 新增五座行為島不變式

**A. token rotation**
- 同一鏈（family）至多一條 `active`；DB partial UNIQUE 為護欄而非唯一防線。
- rotate 次序 MUST 為「舊列轉 `rotated` 並寫 `used_at` → 插新 `active`」，**次序不可反**。
- grace 窗內同票二度換發 MUST 冪等回**既發的同一對**；grace 窗 MUST 大於前端最壞重試間隔。
- reuse 偵測的**唯一觸發形**＝列為 `rotated` 且 grace miss；命中即撤整條家族。
- fail-* 方向：grace 不可用＝**fail-secure**（並發換發觸發 reuse、撤家族；重登復原）。

**B. single-session**
- 政策解析為**兩層**：`effective_single = session_policy=='single' || (session_policy=='inherit'
  && single_session_default=='on')`。
- 踢除 MUST 落 `session_event(kicked)` 並寫 denylist；被踢者在 `(access, refresh)` 窗內換發仍
  得 `7777`。
- fail-* 方向：`single_session_default` 讀不到＝**off 語意**（刻意與 D、E 的方向不同）。

**C. denylist 撤銷**
- `sys_token.status` 為**權威**、denylist 為加速層；兩者不一致時以 status 定案。
- 鍵缺席（nil）＝「未撤」語意 ⇒ 放行；`revoked` 列缺 denylist MUST 靜默 `8888`、**不得落假 reuse**。
- denylist TTL MUST ＝ refresh 全壽命，`kicked` 與 `revoked` 兩 reason 皆同。
- fail-* 方向：讀不到（連線 Err）＝**fail-closed**——退 PG `has_active_in_chain`，無 active→`8888`；
  **PG 亦故障 MUST 視為無 active、絕不盲放**。

**D. idle 逾時**
- 門檻＝`refresh_secs − access_secs`；`session_event(idle)` MUST 僅首次落（SET NX 守門）。
- 不等式 `access_TTL ≤ N×30 < N×60` ⇒ idle 命中 **MUST NOT** 寫 denylist。
- fail-* 方向：`last_activity` 不可讀＝**fail-open**（不 idle-reject，以 token exp 為界）。

**E. 登入失敗節流**
- 三區（自由／需驗證碼／鎖定）；滑動窗（PG）為**權威**、redis L1 為負快取。
- 軟區與鎖定 MUST 在 argon2 **之前**擋下，且**零稽核列、零計數桶**（拒絕不得消耗受害者的額度）。
- fail-* 方向：redis 整體不可用＝**fail-open**（軟區 captcha 要求整層停用、續驗密碼，密碼錯仍
  計數）；L2（PG）查詢失敗＝**fail-open ＋ 補償**（`count:=0` 並置 `captcha_forced = !redis_down`）；
  captcha 標記 SET NX 瞬斷（redis 健康）＝**fail-closed 不罰**（拒該次、零計數桶）。

**跨島註（方向刻意不一致，記於此以免日後被「統一」）**：登入第⑥步的 `session_idle_timeout`
設定鍵缺失＝**fail-loud**（`5000`、不猜 TTL 值），與 E 的節流設定鍵缺失走 fail-open 退常數方向
相反——前者猜錯會靜默縮短或延長所有人的會話壽命，後者猜錯只影響阻力強度。

**方向性反轉自此為 MAJOR**（§I.7 進場規則既有條款，此處確認其射程已涵蓋上列五島）。

### 三、版本與程序

- bump **1.2.0 → 1.3.0**（MINOR：§V.3 之「新增 ★ 軌道」與「行為島隨刀進場」兩款）。
- 本 ADR 轉 accepted 與憲法改動 MUST 同一顆 commit（§V.2 步驟 4），並同批跑 `docs-sync generate`。
- 該 commit 落地即解除「base-web fork 既有檔硬閘」；在此之前，純新增檔（`rev5-` 前綴 wrapper／
  `rev5-auth.d.ts`／`zh-tw.ts`）依 ADR 0021 款 1 不受此閘。

## 後果

- **§III.2 自此不再是空節**，`tools/fork-delta-lint.py` 的名冊斷言取得可掃描的來源。名冊 ≥ 7 名
  （§III.2 四名 ∪ §III.1 三名），故 FR-031 要求的兩條非空斷言（名冊整體非空 ＋ §III.2 ★ 段貢獻
  列數 ≥ 4）皆為真且可落。
- ★**掃描錨必須按節定位、不得全檔掃 `^|`**：憲法 §II 亦有表格（`| # | 主題 | 拍板凍結 |`），
  全檔掃會把 `#1`／`#2`／`#3` 當成軌道名吃進名冊。§III.1 為三欄表、§III.2 為四欄表，載入器須容
  兩種欄數。
- **i18n 三檔是本次授權裡風險最高的面**：`app.d.ts`／`en-us.ts`／`zh-cn.ts` 是基線近 12 月最熱的
  三個檔（各 15／16／17 個 commit）。這反向印證 ADR 0021 當初「`app.d.ts` 等 upstream 熱檔零
  fork-delta」的顧慮；本刀提前吃下該面，代價已知並入帳（rev4 走過同路、I18N-WIRING 曾達 127
  處，故有先例，但風險等級誠實標高）。rebase 處置：先比對 upstream 是否已自行新增 `backend`
  節或改動 `Schema` 結構，若是則本刀 inline 改為**對齊而非疊加**。
- **授權是收窄的**：四條軌道在 rev4 曾有更寬的用途集（LOGIN-CAPTCHA 二用途、LOGOUT-UX 二用途、
  I18N 四範圍、AUTH 三接線），本次僅開其中八個用途；`(ii)` 類三項（captcha `formRules` 放寬／
  reLogin toast／LangType 與 locale 註冊）明文不授權。日後要開走 §V.2，不得以「同軌道內」為由默開。
- **§I.7 一旦填入，fail-* 方向即受 MAJOR 閘保護**：後續刀若因故要把 idle 改成 fail-closed 或把
  denylist 改成 fail-open，必須走 MAJOR Amendment 而非改碼了事。代價是這些方向的調整成本上升，
  這正是入憲的目的。
- 本 Amendment **不新增任何 migration、不動 wire 契約、不動 §II 拍板**；§I.1～§I.6 一字不動。
