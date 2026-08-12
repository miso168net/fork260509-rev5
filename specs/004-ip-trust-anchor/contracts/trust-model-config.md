# Contract — 信任模型設定檔

> 格式＝**TOML**（Clarify 定案；決定性理由＝這份檔的內容是 CIDR 清單，而「哪一段是哪家 CDN、
> 何時更新、依據哪份官方網段表」屬維運必須寫在旁邊的資訊，JSON 無註解語法承載不了）。
> 以環境變數指向路徑、**啟動時一次載入**、之後唯讀共享。★dev **必掛**一份（spec FR-010 後段）。

## 集合語意（六項，皆可省略＝空集）

| 鍵 | 型 | 語意 |
|---|---|---|
| `internal_default` | CIDR 陣列 | 內網預設受信集 |
| `cf_gate_egress` | CIDR 陣列 | 掛邊緣驗證閘的我方出口集（★邊緣驗證升等的前置之一） |
| `[tunnel]` `networks` | CIDR 陣列 | 通道來源集 |
| `[tunnel]` `connecting_ip_header` | string | 通道注入的訪客位址標頭名；省略＝預設值 |
| `[[cdn]]` `networks` | CIDR 陣列 | 該 CDN 的出口網段（Tier-1 位置錨判定面） |
| `[[cdn]]` `connecting_ip_header` | string | 該 CDN 的訪客位址標頭名；省略＝預設值 |
| `[[my_public]]` `networks` | CIDR 陣列 | 我方公開出口 |
| `[[my_public]]` `dual_role` | bool | `true`＝該位址也可能是直連使用者 ⇒ walk 經過即降 `proxy_soft` |
| `[[bindings]]` `public` / `internal` | CIDR 陣列 | 公開出口×其專屬後置內網（右鄰不符即降 `proxy_soft`） |

★**六集合的聯集**同時導出「受信集」與「跳過集」——兩者**必須同源**（data-model §2.1）。

## 載入失敗語意（★三層、方向皆為「只縮小信任」）

| 情境 | 行為 |
|---|---|
| 路徑未設 / 檔案讀不到 | 沿用**扁平環境變數退路**（逗號分隔的 CIDR 清單，充 `internal_default`） |
| 檔案存在但整體解析失敗 | **全空＝全直連**；★**不**套用扁平退路——設定存在但壞掉時擴大信任是錯誤方向 |
| 單一集合含無效 CIDR | **只清空該集合**，其餘照常 |

三者皆**永不當機**、皆發結構化告警。

## dev 交付形（★本刀新增；同時是部署樣例的活體驗證）

```toml
# ── rev5 dev 信任模型 ──
# 本檔的存在理由：後端的傳輸層對端恆為反向代理容器；它若不在受信集，
# 對端閘會恆先觸發，第二／三層與兩個覆蓋層在任何環境都是死碼。
#
# ★dev 只填這一項，其餘集合刻意留空（Clarify 定案）：
#   ⇒ 經反向代理的端到端走查可達 fallback / proxy_clean 二態，
#     其餘五態由整合測試覆蓋（research R7 有逐態對照表）。
internal_default = [
  "172.16.0.0/12",   # docker 預設橋接網段
]
```

## prod 樣例（落部署 checklist、由上式擴充而來）

```toml
internal_default = ["10.0.0.0/8"]

# 掛 CF 驗證閘的我方 ingress 出口——沒有這一項，
# 邊緣驗證標記不會被採信（四前置之一）。
cf_gate_egress = ["10.0.0.0/8"]

# Cloudflare 邊緣網段（部署參數）
# 來源：https://www.cloudflare.com/ips/ ——★需定期更新，
# 且必須與 nginx 的 geo 區塊同步（兩處各一份、更新時一起改）。
[[cdn]]
networks = [
  "173.245.48.0/20",
  "2400:cb00::/32",
  # …其餘依官方表逐行列出
]
connecting_ip_header = "CF-Connecting-IP"
```

★**checklist 必列的一致性義務**：CDN 網段在 nginx 的 `geo` 區塊與本檔**各存一份**，
用途不同（前者判傳輸層對端、後者判轉發鏈位置錨）但**必須同步更新**；只改一邊會使
邊緣驗證升等與位置錨的判定互相矛盾（表徵＝信心大量落 `cdn_mismatch`）。

## 標頭契約（反向代理側，★rev5 既有、本刀零改動）

| 標頭 | 注入規則 |
|---|---|
| `X-Real-IP` | 恆為反向代理觀察到的傳輸層對端 |
| `X-Forwarded-For` | 既有鏈 ＋ 反向代理觀察到的對端（附加於**最右**） |
| `X-CF-Verified` | 對端∈CDN 邊緣網段→`"1"`；否則**空值＝移除**（client 自帶不倖存） |
| `CF-Connecting-IP` | 同上條件透傳 CDN 注入原值；否則移除 |

★dev 的 `geo` 網段清單為空 ⇒ 後兩個標頭恆被移除 ⇒ 邊緣驗證兩態在 dev 經反向代理不可達
（research R7）。
