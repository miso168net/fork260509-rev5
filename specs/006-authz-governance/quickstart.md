# Quickstart — 006 三維授權治理＋結構性封死＋授權回收桶（驗證指南）

> Phase 1 產物：可跑的端到端驗證情境；不含實作碼。前置＝CLAUDE.md §7（rev5 22080／rev4 42080 對照、dev 帳號
> Super／Admin／User＋123456、一律 127.0.0.1）；容器內 build/test 全程 serial。契約細節見 contracts/、
> 狀態機見 data-model.md §3。

## 0. 前置

```bash
cd /mnt/d/AnewSpaces/x_Project/fork260509-rev5
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait            # rev5 五容器＋front-nginx
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace -- --test-threads=1   # 基線 682 綠
python3 tools/schema-gate.py check                                                      # 三閘綠
TOKEN=$(curl -s -X POST http://127.0.0.1:22080/api/auth/login -H 'content-type: application/json' \
  -d '{"userName":"Super","password":"123456"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["token"])')
```

## 1. 後端契約面（curl；Super token）

```bash
H=(-H "authorization: Bearer $TOKEN" -H "content-type: application/json")
# 支撐讀三支（getAllPages 為 menu 頁既有 404 破口、交付即修復）
curl -s "${H[@]}" http://127.0.0.1:22080/api/systemManage/getAllPages      # data: string[]（顯示域、(order,id) 序）
curl -s "${H[@]}" http://127.0.0.1:22080/api/systemManage/getAllButtons    # data: string[]（治理域聯集）
curl -s "${H[@]}" http://127.0.0.1:22080/api/systemManage/getAllEndpoints  # data: Endpoint[]（Policy 全集、35）
# 三維讀端（角色鍵 id；每項帶 protected）
curl -s "${H[@]}" 'http://127.0.0.1:22080/api/systemManage/getRoleMenu?id=2'
curl -s "${H[@]}" 'http://127.0.0.1:22080/api/systemManage/getRoleButton?id=2'
curl -s "${H[@]}" 'http://127.0.0.1:22080/api/systemManage/getRoleEndpoints?id=2'
# 三維寫端（全量替換；回應 {revoked, granted, effective}）
curl -s "${H[@]}" -X POST http://127.0.0.1:22080/api/systemManage/updateRoleMenu -d '{"id":2,"menuIds":[1,2,3]}'
# 撤銷 R_SUPER（id 1）任一 protected 項 ⇒ 2222 biz.role.protectedRevoke、零變更
curl -s "${H[@]}" -X POST http://127.0.0.1:22080/api/systemManage/updateRoleEndpoints -d '{"id":1,"endpoints":[]}'
# 結構性封死：把受保護端點授給 R_ADMIN ⇒ 2222 biz.role.protectedGrant、零變更
curl -s "${H[@]}" -X POST http://127.0.0.1:22080/api/systemManage/updateRoleEndpoints \
  -d '{"id":2,"endpoints":[{"path":"/systemManage/updateRoleEndpoints","method":"POST"}]}'
# 回收桶
curl -s "${H[@]}" 'http://127.0.0.1:22080/api/systemManage/getArchivedPolicies?current=1&size=10&dimension=endpoint'
curl -s "${H[@]}" -X POST http://127.0.0.1:22080/api/systemManage/restorePolicy -d '{"id":<archiveId>}'
# 授權態：以 Admin token 打上述任一支 ⇒ 5003／HTTP 403
```

預期：Super 11 支全通；空 body 三維寫端→`biz.role.notFound`；menu／button 維撤銷列在回收桶 `restorable=false`、
端點維手動撤銷列 `restorable=true`（同實例∧在冊∧封死不擋）。

## 2. 判定面同步（US1／grant 面刻意例外）

- 對 R_ADMIN 新授一支非受保護端點→以 Admin token 立即打該端點由 5003 變通（API 判定即時）；再撤銷→立即回 5003。
- 空 diff 提交（期望集＝現況）仍觸發同步：`curl -s http://127.0.0.1:22080/api/metrics | grep casbin_reload_total`
  之 `outcome="ok"` 計數 +1；整批拒與 NotRestorable 不 +1。

## 3. 序列化域機器證＋封死變異自證（容器內 serial）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace -- --test-threads=1 menu_domain_serialization
# 兩支入域寫端各一支 NOT-granted 等待測（pg_locks classid/objid 拆讀）；restore-during-delete 以 pg_blocking_pids 形
# 封死變異自證：拆掉鎖內謂詞守門→對應測紅→還原→綠（實作單元 report 附三次結果）
```

## 4. 前端與 CDP 三方對照（22080 vs 42080、必要時 42089）

1. Super 登入→角色管理→編輯抽屜：三顆授權鈕（rev5 現況兩顆為錨點）。
2. 選單權限 modal：樹＝真樹、勾選非 1..21 連號、notFound toast 消失、受保護項鎖定、首頁下拉可選／可清（誠實 null）；提交後重開回讀一致。
3. 按鈕權限 modal：無 button1..button10 假資料；候選＝治理域聯集；切換角色後開啟讀到新角色 checks。
4. 端點權限 modal：依路徑群組、群組級勾選真連動葉鍵（`cascade`）；提交回讀一致。
5. policy-archive 頁：側欄有項（seed 列 10、icon `mdi:recycle`）、roleCode×dimension 可濾、`restorable=false` 列鈕停用、復原後列消失且留當頁。
6. menu 管理頁新增 modal：page／activeMenu 下拉非空（getAllPages 修復）。
7. ip-rule 頁以無寫端按鈕碼帳號開啟：不冒出新增／批刪鈕（B-099）。
8. 已知態排除：B-008 餘兩張死項；menu 維 protected 四列可授可見性（端點仍 5003）；授予指向不存在 view 的自建選單＝側欄可見點擊零反應。
★走查排 schema-gate 之後；走查後 psql 清殘列＋`setval('casbin_rule_id_seq',163,true)`＋`setval('sys_casbin_policy_archive_id_seq',1,false)`；真登入 smoke 後全量照 L-050。

## 5. 收刀閘（全量）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace -- --test-threads=1   # 全綠、淨增
python3 tools/schema-gate.py check && python3 tools/docs-sync.py lint && python3 tools/fork-delta-lint.py && python3 tools/route-artifact-gate.py check
python3 tools/wire-schema.py check        # 快照重抽後零漂移（跨子庫兩段式 commit）
python3 tools/seed-view-gate.py check     # B-088 對賬閘（具名豁免 seed 9／77）
python3 tools/docs-sync.py errata 六座    # 唯一現在式＝活書 §6「六座」→「八座」
```
ROUTES 49／contract 49／wire-schema definitions 自 57 淨增且新命名空間有裁判；憲法 v1.8.0＋ADR 三支 accepted；fork-delta 修改型僅 FR-047 檔集。
