# Wire 契約 — route 面（3 條）＋動詞不符處置

權威＝base-web typings（憲法 §I.3 權威序 1）。欄位映射見 `../data-model.md` §5、不重複。

## GET /route/getConstantRoutes（**Public**）

Public 理由：登入前就要拿得到（前端 `initConstantRoute` 於 dynamic 模式呼叫）。

| 面 | 內容 |
|---|---|
| 成功 | `data`＝`Api.Route.MenuRoute[]`；濾 `sys_menu.constant = TRUE`（★勿寫 `IS NOT FALSE`——NULL 佔 64 列） |
| 現值 | seed `constant=TRUE` 為 **0 列** ⇒ 現回 `[]` |
| 前端接線 | ★**合併**而非取代：`addConstantRoutes([...staticRoute.constantRoutes, ...data])`；取代會清空 5 條 builtin 常量路由（403／404／500／iframe-page／login） |

## GET /route/getUserRoutes（Authed）

| 面 | 內容 |
|---|---|
| 成功 | `data`＝`Api.Route.UserRoute`＝`{routes: MenuRoute[], home}` |
| `routes` | DB-fresh roles → Casbin `menu` 維度過濾 → 祖先包含 → 同層 `order`→`id` 升冪 |
| `home` | 啟用角色依 role id 升冪取首個非空 `role_home`，全空→`home`；再經兜底（驗屬可見樹可導航葉、不屬→先序第一可導航頁） |

★`home` 型別為 elegant-router 生成的字面聯集——回非法值時前端靜默不改 root redirect
（無錯誤訊息、極難查），故 tasks 須有合成多角色測試釘住收斂律。

## GET /route/isRouteExist（Authed）

請求 `?routeName=`；成功 `data`＝boolean。dynamic 模式下前端 `getIsAuthRouteExist` 走此端點
（static 模式走本地表 ⇒ 未翻 `.env` 則此端點零呼叫）。

## 動詞不符（B-047）

已註冊路徑遇未註冊動詞 → `4040`＋**HTTP 404**（消除框架預設 405 裸 body）。

**組裝次序契約**（實證，見 `../research.md` R1）：route 註冊 → 各子 router `enforce_mw` layer →
merge → `.fallback()` → `.method_not_allowed_fallback()` → 最外側 metric layer。

| 情境 | 結果 |
|---|---|
| Public 路由＋動詞不符 | `4040`＋404 |
| Authed 路由＋**未認證**＋動詞不符 | `4040`＋404（★mnaf 在 layer 之後掛 ⇒ 405 handler 不經 `enforce_mw`；與未註冊路徑同碼同 status＝零路徑存在性洩漏） |
| Authed 路由＋已認證＋動詞不符 | `4040`＋404 |
| 完全未註冊路徑 | `4040`＋404（既有 path fallback、語意分離） |

★兩條次序反例（tasks 須以測試釘住）：①mnaf 之後才 `merge` 進來的 route 不受保護（回框架
405）②mnaf 排在 `enforce_mw` layer 之前 ⇒ 未認證動詞不符被攔成 `8888`、4040 語意失效。
★動詞探測閘（`contract.rs`）以 `Router::new().route(...)` **裸掛**，不經 `build()` ⇒ 其 405
語意不受本改動影響；該前提 MUST 由碼註同時釘在 `contract.rs` 與 `router.rs`（改走 `build()`
共用即恆綠、L-010 形）。
