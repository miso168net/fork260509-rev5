# Quickstart — 007 使用者＋密碼管理（驗證指南）

> Phase 1 產物：可跑的端到端驗證情境；不含實作碼。前置＝CLAUDE.md §7（rev5 22080／rev4 42080 對照、dev 帳號 Super／
> Admin／User、一律 127.0.0.1）；容器內 build/test 全程 serial。契約見 contracts/、狀態機見 data-model.md §3。

## 0. 前置

```bash
cd /mnt/d/AnewSpaces/x_Project/fork260509-rev5
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace -- --test-threads=1   # 基線 829 綠
python3 tools/schema-gate.py check                                                      # 三閘綠
login() { curl -s -X POST http://127.0.0.1:22080/api/auth/login -H 'content-type: application/json' \
  -d "{\"userName\":\"$1\",\"password\":\"$2\"}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["token"])'; }
SUPER=$(login Super 123456); ADMIN=$(login Admin 123456)
H() { echo -H "authorization: Bearer $1" -H "content-type: application/json"; }
```

## 1. 管理面契約（Super token）

```bash
B=http://127.0.0.1:22080/api/systemManage
curl -s $(H $SUPER) "$B/getAllEndpoints" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["data"]))'   # 受政策管制端點＝45（SC-001 驗收錨）
curl -s $(H $SUPER) "$B/getUserList?current=1&size=10"                                  # data.records[].roles 為 code 集
curl -s $(H $SUPER) -X POST $B/addUser -d '{"userName":"alice","password":"Alice#2026x","nickName":"Alice","roleIds":[3]}'   # {id}
curl -s $(H $SUPER) -X POST $B/addUser -d '{"userName":"alice","password":"Alice#2026x"}'   # 2222 biz.user.userNameExists
curl -s $(H $SUPER) -X POST $B/updateUser -d '{"id":<alice>,"nickName":"A2","userName":"x"}'   # 2222 biz.user.userNameImmutable
curl -s $(H $SUPER) -X POST $B/updateUser -d '{"id":<alice>,"roleIds":[2]}'               # 0000；reload 一次
curl -s $(H $SUPER) -X POST $B/updateUser -d '{"id":1,"status":"2"}'                      # 2222 biz.user.superCannotDisable
curl -s $(H $SUPER) -X DELETE $B/batchDeleteUser -d '{"ids":[<alice>,2]}'                 # 2222 biz.user.seededProtected、零變更
curl -s $(H $SUPER) -X DELETE $B/deleteUser -d '{"id":<alice>}'                           # 0000；指派硬刪、session 全撤
curl -s $(H $SUPER) "$B/getDeletedUsers?current=1&size=10"                                # alice 在列
curl -s $(H $SUPER) -X POST $B/restoreUser -d '{"id":<alice>}'                            # 0000；roles=[]
curl -s $(H $SUPER) -X POST $B/updateUserSessionPolicy -d '{"id":<alice>,"sessionPolicy":"single"}'   # 0000
curl -s $(H $SUPER) -X POST $B/unlockLogin -d '{"dimension":"user","userName":"alice"}'   # 既有端點
```

## 2. 斷權（兩個 alice token）

```bash
A1=$(login alice 'Alice#2026x'); A2=$(login alice 'Alice#2026x')          # sessionPolicy 需 multi 才能雙開
curl -s $(H $SUPER) -X POST $B/kickUser -d '{"id":<alice>}'               # {revoked:2}
curl -s $(H $A1) http://127.0.0.1:22080/api/auth/getUserInfo              # 7777 auth.session.kickedByAdmin
A1=$(login alice 'Alice#2026x')                                           # 可立即重登
curl -s $(H $SUPER) -X POST $B/updateUser -d '{"id":<alice>,"status":"2"}'   # 停用
curl -s $(H $A1) http://127.0.0.1:22080/api/auth/getUserInfo              # 8888
curl -s -X POST http://127.0.0.1:22080/api/auth/refreshToken -d '{"refreshToken":"<alice refresh>"}'   # 8888（鎖內活性重驗）
login alice 'Alice#2026x'                                                 # 1000（三態收斂）
curl -s $(H $SUPER) -X POST $B/resetUserPassword -d '{"id":<alice>,"password":"Alice#2026y"}'   # 0000；再次 30s 內 → 2222 pwdSetTooFrequent{remainingSeconds}
```

## 3. 密碼面（政策生效於三入口、登入不驗）

```bash
curl -s $(H $SUPER) -X POST $B/updateSystemSetting -d '{"key":"password_min_length","value":"12"}'
curl -s $(H $SUPER) -X POST $B/addUser -d '{"userName":"bob","password":"Short#1"}'      # 2222 biz.user.passwordPolicy data.violations=["minLength"]
curl -s $(H $ADMIN) http://127.0.0.1:22080/api/userCenter/getPasswordPolicy               # 七鍵投影、minLength=12
curl -s $(H $ADMIN) -X POST http://127.0.0.1:22080/api/userCenter/changePassword \
  -d '{"oldPassword":"wrong","newPassword":"Admin#2026longer","confirmPassword":"Admin#2026longer"}'   # 2222 oldPasswordMismatch（×5 後第 6 次 → changePasswordThrottled）
curl -s $(H $ADMIN) -X POST http://127.0.0.1:22080/api/userCenter/changePassword \
  -d '{"oldPassword":"123456","newPassword":"Admin#2026longer","confirmPassword":"Admin#2026longer"}'   # 0000；另一 Admin token → 8888
login Super 123456                                                                          # 仍成功（登入路徑不驗政策）
```

## 4. 授權下放＋no-escalation（Admin token）

```bash
# 預設態：Admin 對寫端一律 5003
curl -s $(H $ADMIN) -X POST $B/updateUser -d '{"id":<alice>,"nickName":"x"}'              # 5003
# 超管運行期下放（006 端點授權 modal 的 API 形）：授 R_ADMIN updateUser＋deleteUser（＋按鈕碼 user:delete）
curl -s $(H $SUPER) -X POST $B/updateRoleEndpoints -d '{"id":2,"endpoints":[<既有集>,{"path":"/systemManage/updateUser","method":"POST"},{"path":"/systemManage/deleteUser","method":"DELETE"}]}'
curl -s $(H $SUPER) -X POST $B/updateRoleButton -d '{"id":2,"buttons":["user:edit","user:delete"]}'
curl -s $(H $ADMIN) -X POST $B/updateUser -d '{"id":<alice>,"nickName":"x"}'              # alice 持 {R_ADMIN}：0000（同級互管）
curl -s $(H $ADMIN) -X POST $B/updateUser -d '{"id":1,"nickName":"x"}'                    # Super 持 {R_SUPER}：5003
curl -s $(H $ADMIN) -X POST $B/updateUser -d '{"id":<alice>,"roleIds":[1]}'               # 指派 R_SUPER：5003
curl -s $(H $ADMIN) -X POST $B/updateUser -d '{"id":<alice>,"roleIds":[3]}'               # Admin 不持 R_USER：5003
curl -s $(H $SUPER) -X POST $B/updateUser -d '{"id":2,"roleIds":[2,3]}'                   # 超管授 Admin 一枚 R_USER（A＝全集）
curl -s $(H $ADMIN) -X POST $B/updateUser -d '{"id":<alice>,"roleIds":[3]}'               # 0000
curl -s $(H $SUPER) -X POST $B/updateRoleEndpoints -d '{"id":2,"endpoints":[...,{"path":"/systemManage/updateUserSessionPolicy","method":"POST"}]}'   # 2222 biz.role.protectedGrant（結構性封死）
```

## 5. 容器內測試與閘（每單元收尾）

```bash
X="docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api"
$X cargo fmt --all && $X cargo test --workspace -- --test-threads=1        # 全綠、案數自 829 淨增
python3 tools/schema-gate.py check && python3 tools/entity-drift-gate.py check
python3 tools/wire-schema.py check --staged-gate                             # 重抽後 definitions 75→＋N、裁判全綠
python3 tools/fork-delta-lint.py && python3 tools/view-render-guard.py && python3 tools/seed-view-gate.py
python3 tools/docs-sync.py lint                                              # 0 錯誤
```

## 6. 前端與 CDP 三方對照（22080 vs 42080）

1. Edge `--remote-debugging-port=9229`；起手清 localStorage；Super 登入 → `/manage/user`：列表欄（角色／狀態／會話政策／
   記事／審計）、抽屜新增（隨機密碼鈕、hint）、編輯（userName disabled、sessionPolicy 三值）、操作下拉（踢除／重設密碼／
   隨機密碼）、回收桶 toggle→復原（確認框「復原後需重新指派角色」）、頁首解鎖 modal（雙維）。
2. Admin 登入（預設態）：只見「編輯」鈕、其餘六鈕不見；按編輯 Super → 5003 toast；sessionPolicy 欄 disabled＋提示。
3. 授 R_ADMIN 六碼與端點後（§4）：鈕出現、操作同級成功、操作 Super 5003。
4. alice 雙開：Super 踢除 → alice 7777 modal 新文案；停用 → 8888。
5. User 登入 → 頭像下拉「個人中心」→ 改密卡（動態規則跟政策）；登入頁輸入含特殊字元密碼直送（無前端格式紅字）。
6. rev4 42080 同路徑逐項對照；預期差異＝三卡留白、兩語、無首登強制頁、7777 新文案（rev4 為舊文案）。
7. 走查排 schema-gate 之後（會留列與序列推進）。★**走查後清理契約**（2026-08-30 as-built 補入——
   本刀原文缺此段，L-055 的防法未被沿抄下來而原樣復發，詳 L-071）：
   - **清理面＝走查期間被寫過的全部表，與任何閘的射程無關**。`schema-gate` 對
     `session_event`／`sys_login_attempt`／`sys_token`／`sys_operation_log` 四張 runtime-append 表
     結構性無感（收窄集剝列＋setval 正規化）⇒ **三閘複驗綠不等於環境已還原**。
   - 種子面：`DELETE FROM sys_user_role/sys_pwd_custody/sys_user WHERE …` 走查建立的 id ＋
     `DELETE FROM casbin_rule WHERE id>163` ＋ `setval('sys_user_id_seq',3,true)`／
     `setval('casbin_rule_id_seq',163,true)`；歸檔面 `sys_casbin_policy_archive` 逐列核對。
   - 運行期面：`TRUNCATE sys_token, session_event, sys_operation_log, sys_login_attempt`；
     ★**表清空後 seq 刻意不復位**（復位到 1 會讓下一輪 nextval 落在殘列 id 上＝L-055 第一形）。
   - 快取面：`session:*`／`cpwd:*`／`throttle:*` 三前綴 DEL（redis 需 `-a $(cat /run/secrets/redis_password)`；
     ★**無認證時 `--scan` 回空是 NOAUTH 而非「無殘留」**，先自證再下結論）。
   - 判準：**走查前取全表基準列數與 seq，走查後逐值比對**——不是「照清單刪」（清單會隨情境失效：
     006 撞的是 auth seq × `sys_token`，本刀撞的是 user seq × `sys_operation_log`）。
   - 收尾必跑：三閘 ＋ **容器內全量測試**（★三閘綠而全量紅是本坑的典型徵狀：本刀實暴兩支——
     `uid 3 不得有憑證列` 撞 `sys_token` 殘列、`稽核恰一列` 撞 `sys_operation_log` 中 user_id 與
     復位後 seq 重號的殘列）。

## 7. 收刀閘

活書 §5／§6／§8 as-built＋附屬文件接線段＋§12 六詞；憲法 v1.9.0；ADR 五支 accepted；BACKLOG 十三條 backlog_done；
`docs-sync.py generate`；RUNBOOK §12.1 量測一筆；pre-commit 全鏈綠。
