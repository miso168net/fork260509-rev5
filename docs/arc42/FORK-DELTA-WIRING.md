# FORK-DELTA-WIRING — base-web fork-delta 接線現況（活書附屬文件）

本檔＝活書 `docs/arc42/ARCHITECTURE.md` §8「fork-delta 接線現況」子節下放之 as-built（ADR 0062）、
永遠現在式；同受 Lint07（行數預算）／Lint10（時態禁詞）／Lint11（禁入詞典）三閘。授權面＝
constitution §III.2 名冊（★ 軌道條數以名冊為準、本檔不複述）；機器守＝`tools/fork-delta-lint.py`／
`tools/view-render-guard.py`／`tools/route-artifact-gate.py` 三支（前二支掛 pre-commit；第三支需 dev
stack、刻意不掛 pre-commit、單元邊界手動跑）。

### fork-delta 接線現況（base-web）

授權面＝constitution §III.2 名冊（授權歸憲法、本節只記 as-built 接線形；**條數以該名冊
為準、本節刻意不複述**——複述即第二份會漂的手抄計數）。003 起實接之 ★ 軌道逐條如下：

- **★BASE-WEB-AUTH-WIRING**：(a) `store/modules/route/index.ts` constant routes **併入**
  static 常量集（seed `constant=TRUE` 現 0 列、取代形會清空五條 builtin）；(b) 三張替代
  登入表單改打 `rev5-auth.ts` 誠實 stub（恆 2222 notSupported）並消滅假成功 toast；
  (c) `hooks/business/captcha.ts` 改打 `/auth/sendCaptcha` stub、假延遲與假成功 toast 移除。
- **★BASE-WEB-LOGIN-CAPTCHA-WIRING**：(i) login 簽名加 captcha 參＋失敗 msg 回傳鏈
  （`store/modules/auth/index.ts`）；`pwd-login.vue` 軟區條件渲染 220×120 驗證碼欄，
  非軟區零行為變更。
- **★BASE-WEB-I18N-WIRING**：(i) `service/request/index.ts` 之 `translateBackendMsg`／
  `translateDetailValue`——後端 msg（穩定 i18n key）經 ``$t(`backend.${msg}`, msg)`` 顯人話、
  未命中以原文 graceful fallback；(ii) `en-us.ts`／`zh-cn.ts` 各插 backend 樹（★鍵數與鍵清單
  之機器真源＝`deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json`（generate 自
  兩語 locale 重算、Lint24 雙向守相等）——本節不手抄計數；各刀增鍵記各自 spec）；
  (iii) `app.d.ts` 補 backend 必填型節。
- **★BASE-WEB-LOGOUT-UX-WIRING**：(i) `user-avatar.vue` 登出前 best-effort
  `fetchLogout`（失敗不阻斷 `resetStore()`）。
- **★BASE-WEB-MANAGE-PAGE-WIRING**：(i) IP 規則管理頁進場——兩語 locale 之 `route:` 樹加
  `manage_ip-rule`、`page:` 樹加 `manage.ipRule.*`；`app.d.ts` 補 `Schema.page` 型節；
  路由外掛產物**四檔**（`router/elegant/{imports,routes,transform}.ts`＋
  `typings/elegant-router.d.ts`）**由外掛重算產出**、採**產物檔紀律**（禁手改、不逐行標記
  ——標記於下次重算即被抹除、物理上不可維持）；(ii)（005、憲法 v1.7.0 開）role／menu
  既有管理頁 CRUD 接真——檔級定數名單恰 8 檔＝role 3 view＋menu 2 view＋兩語 locale＋
  `app.d.ts`（兩顆授權 modal 與 `shared.ts` 明文不入、零 diff 機器斷言），`page:` 樹加
  memo／回收桶欄位鍵；upstream 誤植之 `fetchGetAllRoles` 殘留於 menu modal 移除；
  (iii)（006、憲法 v1.8.0 開）三顆授權 modal 接真——menu／button modal 修改型（原行 13／23＋
  就緒守：確定鈕於現況讀成功前 disabled、user 拍板 2026-08-24）＋endpoint modal 新增型新檔
  （cascade＋check-strategy=child）＋drawer 同檔雙用途第三鈕＋roleHome（誠實 null＋clearable）
  ＋`page:` 樹 endpointAuth 鍵；(iv)（006）policy-archive 頁進場——兩新檔＋`route:`／`page:`
  樹＋產物四檔重算；role/index.vue 零 diff、三鈕零 hasAuth gating（門在頁級）。

機器守（`tools/fork-delta-lint.py`、`tools/view-render-guard.py`、
`tools/route-artifact-gate.py`、pre-commit）：修改型標記逐處帶 `原行:`＋軌道名 ∈
授權名冊斷言（名冊掃自 constitution §III.1/§III.2 表格、掃空即 die）；新增型圈界；
「假成功 toast 不得回歸」四檔靜態斷言與「`$t` fallback 不得退化」斷言（B-061／B-062 收單）；
管理頁 `views/manage/**` 零原始 HTML 插值（FR-038）。
★**射程界線**：`fork-delta-lint` 的 `scan()` 對「基線沒有的檔」結構性豁免 ⇒ **rev5 新檔的
檔頭標記不受機器守**（004 U-I 變異實測：拿掉新檔標記，lint 仍全綠），該面屬紀律；受機器
守的是**基線既有檔**的修改型與圈界。★路由外掛產物四檔受 fork-delta **全域豁免**，其唯一
機器守＝`route-artifact-gate` 的產出檔集對賬／重算冪等／零手改三道（★第三道以**上游基線**
為種：以版控為種重算時，外掛的 magicast 增量合併會讓手改過的行原封不動活下來、第二道全綠）。

