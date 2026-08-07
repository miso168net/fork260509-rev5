# Quickstart — 002-system-settings 驗證指南

端到端證明「管線七環全通」的可跑場景；細節指涉 contracts/wire-settings.md 與
data-model.md、不重複。全程 dev stack；rust build/test 一律容器內、serial。

## 0. 前置

```bash
bash tools/bootstrap.sh                 # 防線體檢（新機必跑；舊機＝純體檢）
python3 deploy/preflight-secrets.py     # 機密預檢（缺則先 generate-secrets.py）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait
```

預期：六業務件全 healthy、`up --wait` 零非零退出（B12 前「跑不完」已知態自此撤除——
RUNBOOK §1 註記同步刪）；`migrate` 完成後 server 常駐。

## 1. 讀端（US1）

```bash
BASE=https://127.0.0.1:22443/api        # 經 front-nginx；-k 收 dev 自簽
curl -ks $BASE/systemManage/getSystemSettings \
  -H "Authorization: Bearer dev-super" | python3 -m json.tool
```

預期：`code:"0000"`、data 為 16 元素陣列（settingKey 升冪）、四欄形＝data-model §1；
與 seed 定稿逐鍵全等。

## 2. 授權矩陣（US4）

```bash
# 越權：dev-admin（R_ADMIN 有 user:edit 鈕、無設定域政策）
curl -ks -o /dev/null -w "%{http_code}\n" $BASE/systemManage/getSystemSettings \
  -H "Authorization: Bearer dev-admin"          # 預期 403（信封 code 5003）
# 未認證：無標頭
curl -ks $BASE/systemManage/getSystemSettings | python3 -m json.tool
#   預期 HTTP 200、code:"8888"、msg:"auth.session.reLogin"、data:null
```

## 3. 寫端往返（US2/US3/US5）

```bash
AUTH='-H "Authorization: Bearer dev-super" -H "Content-Type: application/json"'
U=$BASE/systemManage/updateSystemSetting
# 合法＋正規化：正號字面棄除、落庫為 "10"
curl -ks $U -H "Authorization: Bearer dev-super" -H "Content-Type: application/json" \
  -d '{"settingKey":"password_min_length","settingValue":"+10"}'      # 0000
# 非法值：超範圍（上界 128）
curl -ks $U -H "Authorization: Bearer dev-super" -H "Content-Type: application/json" \
  -d '{"settingKey":"password_min_length","settingValue":"999"}'      # 2222 invalidValue
# 未知鍵
curl -ks $U -H "Authorization: Bearer dev-super" -H "Content-Type: application/json" \
  -d '{"settingKey":"no_such_key","settingValue":"1"}'                # 2222 notFound
# 三態：description 顯式清空（null）
curl -ks $U -H "Authorization: Bearer dev-super" -H "Content-Type: application/json" \
  -d '{"settingKey":"password_min_length","settingValue":"8","description":null}'  # 0000、description 落 NULL
```

每步後以讀端回讀驗證落庫效果（非法案＝原值保留）。

## 4. 測試與閘（US 全；DoD）

```bash
# 契約快照（typings 變動後重抽；本刀首抽）
python3 tools/wire-schema.py extract && python3 tools/wire-schema.py check
# 容器內全測（serial）：純函式紅綠＋oneshot 契約＋真 DB integration
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec rust-api \
  cargo test --workspace -- --test-threads=1
# 治理面
python3 tools/docs-sync.py check        # lint 全綠（三筆 Day-1 豁免已處置）
python3 tools/schema-gate.py check      # 三閘綠（零 migration＝現況即基線）
```

預期：coverage gate 綠（4/4 case）；抽掉任一 case 重跑即紅指名（負向自證抽查）；
`/metrics` 有 exposition 輸出、grafana `rustapi-down` 恢復非觸發態。

## 5. 量測（FR-027）

B-028 第一輪（動工前起手態）與第二輪（server 依賴進場後）：容器內冷編＋單檔增量
計時，數據落帳 RUNBOOK §12.1 形制。
