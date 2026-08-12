# Contract — 本刀新增訊息鍵

> 後端 `msg` 載**穩定 i18n key**、不在地化（憲法 §I.3）；前端以 `$t` 轉譯、未命中 graceful
> fallback。★新增鍵一律進兩語 runtime locale 的 `backend:` 樹＋治理錨點檔，**三處鍵集必須相等**
> （跨端契約閘 Lint24：少鍵＝缺譯紅、多鍵＝孤兒紅）。

## 新增六鍵（全數綁 `2222` 業務碼）

| # | key | 情境 | 譯文語意（zh-TW） |
|---|---|---|---|
| 1 | `biz.ipRule.invalidRuleType` | 規則類型非二值 | 規則類型不正確 |
| 2 | `biz.ipRule.invalidCidr` | 網段字面不可解析 | 網段格式不正確 |
| 3 | `biz.ipRule.conflict` | 有效列唯一性衝突 | 相同網段與類型的規則已存在 |
| 4 | `biz.ipRule.notFound` | 標的不存在／狀態不符 | 找不到指定的規則，或其狀態不允許此操作 |
| 5 | `biz.ipRule.selfLock` | 寫端自鎖 | 此規則會使你目前的連線被阻擋，已拒絕寫入 |
| 6 | `biz.throttle.invalidUnlockTarget` | 解鎖參數畸形 | 解鎖對象不正確 |

★譯文為**語意規範**，實際字串於實作期定稿；三語一致性由型別與鍵集斷言守。

## 零新增的既有鍵（本刀復用）

| key | 碼 | 本刀用途 |
|---|---|---|
| `system.forbidden` | `5003` | **IP 閘阻擋**（★零新碼、零新鍵） |
| `system.internal` | `5000` | 內部異常 |
| `common.success` | `0000` | 成功 |

## 鍵集算術（Lint24 自證）

- 後端實發鍵：現行 N 鍵 **＋6** ＝ N+6
- 前端白名單鍵：不變（本刀不新增保留碼、不動 13 碼矩陣）
- ⇒ 三處鍵集（`en-us` 的 `backend:` 樹／`zh-cn` 的 `backend:` 樹／治理錨點檔）
  各 **+6**、彼此相等。

## 軌道歸屬（★兩類鍵落點不同，勿混）

| 鍵類 | 落點 | 授權 |
|---|---|---|
| 上表六個 `biz.*` | 兩語 locale 檔的 **`backend:` 樹** | ★**既有 I18N-WIRING 用途 (ii) 授權內**——資料級鍵、不觸 Amendment（ADR 0021「零新 key」釋義） |
| `route.manage_ip-rule`、`page.manage.ipRule.*` | 兩語 locale 檔的 **`route:` / `page:` 樹**（同檔、不同區塊） | ★**不在 (ii) 射程**（該用途的插入錨是 `backend:`）⇒ 屬本刀新開軌道 |
| 上表六個 `biz.*` | 治理錨點檔（`zh-tw.ts`） | 純新增檔、不觸 ★ 軌道 |
| 路由／頁面鍵 | ★**不進**治理錨點檔 | 該檔只承載後端訊息鍵、非 runtime locale |
