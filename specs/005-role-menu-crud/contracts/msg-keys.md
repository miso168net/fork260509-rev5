# Contract — 本刀新增 i18n 拒因鍵（候選權威；逐字面於 i18n 單元定稿、Lint24 對賬）

> 全部 2222 家族（純 key、零攜參——島 G2 不綁載體形）。三處同補：兩語 locale `backend:` 樹
> ＋`app.d.ts` 型節＋zh-tw.ts 治理字典。rev4 鍵集為藍本（rev4:zh-cn.ts `biz.role.*`），
> 本刀只取 CRUD 面子集；三維／回收桶（policy）鍵隨授權治理刀。

## `backend.biz.role.*`（CRUD 面）

| 鍵 | 觸發 |
|---|---|
| `codeInvalid` | roleCode 形制不合 |
| `codeExists` | 活性代碼重複 |
| `codeImmutable` | updateRole 試改 roleCode |
| `notFound` | 標的不存在／已刪 |
| `seededProtected` | deleteRole 撞 seed 三角色 |
| `inUse` | 有掛載使用者（others>0） |
| `cannotDeleteSelfRole` | 刪自己所屬角色 |
| `cannotDisableSelfRole` | 停用自己所屬角色 |
| `superCannotDisable` | 停用 R_SUPER |
| `nameRequired` | updateRole 對 NOT NULL 欄 roleName 送顯式 null（ADR 0023 補充條款 1 拒收；★user 拍板 2026-08-19 開第十鍵——原九鍵集無對應、as-built 曾暫收斂 no-op；施工＝role 側 handler 拒收＋四處 i18n 隨 next-go 後首件） |

## `backend.biz.menu.*`（CRUD 面）

| 鍵 | 觸發 |
|---|---|
| `notFound` | 標的不存在／已刪（含 restore 標的非已刪） |
| `routeNameExists` | 活性同鍵（addMenu 先驗＋23505 兜底同鍵） |
| `routeNameImmutable`／`menuTypeImmutable` | 不可變欄試改 |
| `parentNotFound` | 父不存在或已刪（新增／改父／復原三處同鍵——rev4 restore 併鍵先例、本刀沿用） |
| `cycleDetected` | 改父成環（含上溯逾限） |
| `hasChildren` | deleteMenu 存在未刪子項 |
| `protectedMenu` | deleteMenu 撞受保護列 |
| `constantParent` | 常量父鏈守門拒 |
| `restoreConflict` | 復原撞活性同鍵 |
| `nameRequired` | updateMenu 對 NOT NULL 欄 menuName 送顯式 null（同 role 側第十鍵拍板、兩域同式；隨 US2 handler 單元施工） |
| `routeNameInvalid` | routeName 形制不合（rev4 同名鍵；facade `MenuCreateError::RouteNameInvalid` 已立面〔T023〕、原表漏列——2026-08-19 補、隨 US2 handler 單元接鍵並走 Lint24 四處同步） |

## 前端 `page.manage.menu.*` 補鍵

`showDeleted`（顯示已刪除 toggle）／`confirmRestore`（復原確認）——本刀自有鍵；與授權治理刀
之 policyArchive 鍵收斂屆時議。role／menu 之 memo 欄位標籤鍵隨欄補。
