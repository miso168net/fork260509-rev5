# Contract — 本刀新增 i18n 鍵（候選權威；逐字面於 i18n 單元定稿、Lint24 對賬）

> backend 樹全部 2222 家族（純 key、零攜參——島 G2 一因一鍵形）。四處同 commit：兩語 locale `backend:` 樹
> （zh-cn／en-us；既有授權 (ii)）＋`app.d.ts` backend 型節（(iii)）＋`zh-tw.ts` 治理字典（rev5 純新增檔、
> 僅 backend 鍵）。構造點一律字面 `Cow::Borrowed("…")`。page／route 樹三處（zh-cn／en-us／app.d.ts；zh-tw 不塞）。

## `backend.biz.role.*`（既有 10 鍵＋2）

| 鍵 | 觸發 | 譯文藍本 |
|---|---|---|
| `protectedRevoke` | 三維寫端撤銷集觸及 protected（整批拒） | rev4 同鍵：zh-cn「存在受保护的授权，无法撤销」／en-us「Protected policies cannot be revoked」／zh-tw「存在受保護的授權，無法撤銷」 |
| `protectedGrant`（★新造、rev4 無） | updateRoleEndpoints 把受保護端點政策授予非 R_SUPER（結構性封死） | zh-cn「受保护的端点仅限超级管理员持有」／en-us「Protected endpoints are reserved for the super administrator」／zh-tw「受保護的端點僅限超級管理員持有」 |
| `notFound` | 角色不存在／已刪（三維讀寫；既有鍵復用） | 既有 |

## `backend.biz.policy.*`（新開子樹、1 鍵）

| 鍵 | 觸發 | 譯文藍本 |
|---|---|---|
| `notRestorable` | restorePolicy 識別不存在／任一腿拒／23505 競態 | rev4 同鍵：zh-cn「该归档授权不可复原」／en-us「This archived policy cannot be restored」／zh-tw「該歸檔授權不可復原」 |

backend 樹 50→53 鍵。

## 前端 `page.manage.policyArchive.*`（整節 15 葉鍵；插 `page.manage.role` 之後，兩語同位）

| 鍵 | zh-cn | en-us |
|---|---|---|
| `title` | 授权回收站 | Policy Recycle Bin |
| `sourceRole` | 来源角色 | Source Role |
| `dimension` | 授权维度 | Dimension |
| `target` | 授权标的 | Target |
| `archiveReason` | 归档原因 | Archive Reason |
| `archivedAt` | 归档时间 | Archived At |
| `archivedBy` | 归档者 | Archived By |
| `restore` | 复原 | Restore |
| `confirmRestore` | 确定复原此授权？ | Confirm to restore this policy? |
| `restoreSuccess` | 复原成功 | Restore success |
| `form.sourceRole` | 请输入来源角色编码 | Please enter source role code |
| `form.dimension` | 请选择授权维度 | Please select dimension |
| `dimensionLabel.menu` | 菜单 | Menu |
| `dimensionLabel.button` | 按钮 | Button |
| `dimensionLabel.endpoint` | 端点 | Endpoint |

restore／confirmRestore／restoreSuccess 為第三份同名鍵（ipRule／menu 既有）、不收斂（Q14）。`archiveReason` 欄不映譯。

## 前端其他鍵

- `page.manage.role.endpointAuth`：zh-cn「端点权限」／en-us「Endpoint Auth」（插 `buttonAuth` 之後）。
- `route['manage_policy-archive']`：zh-cn「授权回收站」／en-us「Policy Recycle Bin」（照 `manage_ip-rule` 圈界塊形）。
- `page.manage.menu.home` 既有零新增。

page／route 樹合計新增 17 鍵；`app.d.ts` `App.I18n.Schema.page.manage` 型節同步（`policyArchive` 節＋`role.endpointAuth`）。
