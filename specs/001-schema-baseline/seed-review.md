# seed 淨效果全量清單（001-schema-baseline・clarify 過目素材）

> **用途**：seed 定稿制之過目素材（brainstorm §0 拍板甲）。user 逐表過目、逐筆調整（id 重編／刪列／改值／加列、連動同步）；定稿後本檔＝seed 基線權威、轉錄進 data-model，m002 施工以此為準。
> **produced**: 2026-08-05｜重放容器 postgres:18.4-alpine（獨立一次性、零 host 埠）｜build/runner rev4-admin-rust-api:dev (cargo 1.96.1)
> **來源**：rev4 migration m001–m015 原始碼（rev4 repo @ 2b8a101、working tree 乾淨）抄至 scratchpad 重放（拷貝例外射程、ADR 0001 決定 3；rev4 側零寫入）。
> **雙源互證**：重放庫結構快照 vs rev4 已入版 schema-snapshot.json＝**columns／indexes／constraints 三節全等**（重放環境無失真）。
> **機器權威**：同目錄 `seed-net-effect.json`（本檔由其機器渲染；如有出入以 json 為準）。

## 非決定值告示（重放時每次不同；定稿策略＝工作坊 Q1 已拍板：甲・全面定稿字面）

> **Q1 決議（2026-08-05）**：m002 寫死定稿字面——password＝argon2 PHC 常數（三帳共用、
> 採本次重放萃取值）、created_at＝定稿時戳（預設 `2026-08-05T00:00:00+00:00`）；
> 重放完全決定性、比對零豁免洞。定稿值於過目完成後載於文末定稿節。

1. `sys_user.password`：argon2id PHC、**執行期隨機 salt** 生成（plaintext 皆 `123456`、三列共用同一 hash）。
2. 各表 `created_at`：migration 事務 `now()`——本次重放全庫統一為單一時戳。
3. sequence 落值：隨最終列數而動（見文末 sequences 表）。

## 總覽

| 表 | 列數 | id 密集性 |
|---|---|---|
| casbin_rule | 163 | 1..163 密集 |
| session_event | 0 |  |
| sys_access_log | 0 |  |
| sys_casbin_policy_archive | 0 |  |
| sys_ip_rule | 0 |  |
| sys_login_attempt | 0 |  |
| sys_menu | 78 | 1..78 密集 |
| sys_operation_log | 0 |  |
| sys_pwd_custody | 0 |  |
| sys_role | 3 | 1..3 密集 |
| sys_token | 0 |  |
| sys_user | 3 | 1..3 密集 |
| sys_user_email_verify | 0 |  |
| sys_user_role | 3 |  |
| system_settings | 16 |  |

空表 9 張：session_event、sys_access_log、sys_casbin_policy_archive、sys_ip_rule、sys_login_attempt、sys_operation_log、sys_pwd_custody、sys_token、sys_user_email_verify（seed 淨效果＝零列；runtime 資料表）

## sys_user（3 列）

全表共通：`created_at`=`2026-08-04T19:14:44.255156+00:00`、`created_by`=NULL、`updated_at`=NULL、`updated_by`=NULL、`deleted_at`=NULL、`deleted_by`=NULL、`user_gender`=NULL、`session_policy`=`inherit`、`session_id`=NULL、`user_phone`=NULL、`user_email`=NULL、`user_memo`=NULL、`status`=`1`

`password` 三列共用（PHC 前綴 `$argon2id$v=19$m=19456,t=2,p=1$…`、plaintext `123456`）。

| id | user_name | nick_name | 其餘非空欄 |
|---|---|---|---|
| 1 | Super | Super |  |
| 2 | Admin | Admin |  |
| 3 | User | User01 |  |

## sys_role（3 列）

全表共通：`created_at`=`2026-08-04T19:14:44.255156+00:00`、`created_by`=NULL、`updated_at`=NULL、`updated_by`=NULL、`deleted_at`=NULL、`deleted_by`=NULL、`status`=`1`、`role_memo`=NULL、`role_home`=`home`、`role_desc`=NULL

| id | role_code | role_name | 其餘非空欄 |
|---|---|---|---|
| 1 | R_SUPER | 超级管理员 |  |
| 2 | R_ADMIN | 管理员 |  |
| 3 | R_USER_COMMON | 普通用户 |  |

## sys_user_role（3 列）

| user_id | role_id |
|---|---|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |

## system_settings（16 列；PK=setting_key）

全表共通：`created_at`=`2026-08-04T19:14:44.255156+00:00`、`created_by`=NULL、`updated_at`=NULL、`updated_by`=NULL、`deleted_at`=NULL、`deleted_by`=NULL

| setting_key | setting_value | setting_type | description |
|---|---|---|---|
| ip_captcha_after | 10 | number | 來源節流：來源桶滑動窗內失敗達此數即進驗證碼軟區 |
| ip_max_fails | 50 | number | 來源節流：來源桶滑動窗內失敗達此數即硬鎖 |
| ip_window_minutes | 15 | number | 來源節流：來源維滑動窗長（分鐘） |
| login_throttle_captcha_after | 2 | number | 登入節流：滑動窗內失敗達此數即進驗證碼軟區 |
| login_throttle_max_fails | 5 | number | 登入節流：滑動窗內失敗達此數即鎖定 |
| login_throttle_window_minutes | 15 | number | 登入節流：滑動窗長（分鐘）＝鎖定的最長存續 |
| password_change_min_interval | 60 | number | 設密冷卻（秒；0＝停用） |
| password_forbid_username | off | enum:on,off | 禁止密碼與帳號相同 |
| password_max_length | 64 | number | 密碼最大長度 |
| password_min_length | 8 | number | 密碼最小長度 |
| password_require_digit | off | enum:on,off | 需含數字 |
| password_require_lowercase | off | enum:on,off | 需含小寫字母 |
| password_require_special | off | enum:on,off | 需含特殊符號 |
| password_require_uppercase | off | enum:on,off | 需含大寫字母 |
| session_idle_timeout | 60 | number | 工作階段閒置逾時（分鐘） |
| single_session_default | off | enum:on,off | 全站單一-session 預設 |

## sys_menu（78 列）

全表共通：`created_at`=`2026-08-04T19:14:44.255156+00:00`、`created_by`=NULL、`updated_at`=NULL、`updated_by`=NULL、`deleted_at`=NULL、`deleted_by`=NULL；「其餘非空欄」未列之欄＝NULL。

| id | parent_id | order | menu_type | menu_name | route_name | route_path | component | protected | status | 其餘非空欄 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  | 1 | 2 | home | home | /home | layout.base$view.home | true | 1 | icon=mdi:monitor-dashboard; icon_type=1; i18n_key=route.home |
| 2 |  | 2 | 1 | manage | manage | /manage | layout.base | true | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=carbon:cloud-service-management; icon_type=1; i18n_key=route.manage |
| 3 | 2 | 3 | 2 | manage_user | manage_user | /manage/user | view.manage_user | true | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=ic:round-manage-accounts; icon_type=1; i18n_key=route.manage_user; buttons=[{'code': 'user:add', 'desc': '新增用户'}, {'code': 'user:edit', 'desc': '编辑用户'}, {'code': 'user:delete', 'desc': '删除用户'}, {'code': 'user:reset-pwd', 'desc': '重置密码'}, {'code': 'user:kick', 'desc': '踢除下线'}, {'code': 'user:restore', 'desc': '复原用户'}, {'code': 'user:unlock', 'desc': '解锁登录'}] |
| 4 | 2 | 2 | 2 | manage_role | manage_role | /manage/role | view.manage_role | true | 1 | icon=carbon:user-role; icon_type=1; i18n_key=route.manage_role; buttons=[{'code': 'role:add', 'desc': '新增角色'}, {'code': 'role:edit', 'desc': '编辑角色'}, {'code': 'role:delete', 'desc': '删除角色'}] |
| 5 | 2 | 4 | 2 | manage_menu | manage_menu | /manage/menu | view.manage_menu | true | 1 | hide_in_menu=false; keep_alive=true; constant=false; multi_tab=false; icon=material-symbols:route; icon_type=1; i18n_key=route.manage_menu; buttons=[{'code': 'menu:add', 'desc': '新增菜单'}, {'code': 'menu:edit', 'desc': '编辑菜单'}, {'code': 'menu:delete', 'desc': '删除菜单'}] |
| 6 | 2 | 101 | 2 | manage_user-detail | manage_user-detail | /manage/user-detail/:id | view.manage_user-detail | true | 1 | hide_in_menu=true; keep_alive=false; constant=false; multi_tab=false; icon=; i18n_key=route.manage_user-detail; active_menu=manage_user |
| 7 |  | 1007 | 1 | function | function | /function | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=icon-park-outline:all-application; icon_type=1; i18n_key=route.function |
| 8 | 7 | 4 | 2 | function_toggle-auth | function_toggle-auth | /function/toggle-auth | view.function_toggle-auth | false | 1 | icon=ic:round-construction; icon_type=1; i18n_key=route.function_toggle-auth; buttons=[{'code': 'B_CODE1', 'desc': '超级管理员可见'}, {'code': 'B_CODE2', 'desc': '管理员可见'}, {'code': 'B_CODE3', 'desc': '管理员或普通用户可见'}] |
| 9 | 2 | 1 | 2 | manage_system-settings | manage_system-settings | /manage/system-settings | view.manage_system-settings | true | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=mdi:cog; icon_type=1; i18n_key=route.manage_system-settings |
| 10 | 2 | 5 | 2 | manage_policy-archive | manage_policy-archive | /manage/policy-archive | view.manage_policy-archive | true | 1 | icon=mdi:recycle; icon_type=1; i18n_key=route.manage_policy-archive |
| 11 |  | 1000 | 2 | about | about | /about | layout.base$view.about | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=fluent:book-information-24-regular; icon_type=1; i18n_key=route.about |
| 12 |  | 1005 | 1 | alova | alova | /alova | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=carbon:http; icon_type=1; i18n_key=route.alova |
| 13 |  | 1009 | 1 | multi-menu | multi-menu | /multi-menu | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=; i18n_key=route.multi-menu |
| 14 |  | 1006 | 1 | 插件示例 | plugin | /plugin | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=clarity:plugin-line; icon_type=1; i18n_key=route.plugin |
| 15 |  | 1008 | 1 | pro-naive | pro-naive | /pro-naive | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=material-symbols-light:demography-outline-rounded; icon_type=1; i18n_key=route.pro-naive |
| 16 |  | 999 | 2 | user-center | user-center | /user-center | layout.base$view.user-center | false | 1 | hide_in_menu=true; keep_alive=false; constant=false; multi_tab=false; icon=; i18n_key=route.user-center |
| 17 |  | 1003 | 1 | exception | exception | /exception | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=ant-design:exception-outlined; icon_type=1; i18n_key=route.exception |
| 18 |  | 1002 | 1 | document | document | /document | layout.base | false | 1 | hide_in_menu=false; keep_alive=false; constant=false; multi_tab=false; icon=mdi:file-document-multiple-outline; icon_type=1; i18n_key=route.document |
| 19 | 12 | 1 | 2 | alova_request | alova_request | /alova/request | view.alova_request | false | 1 | i18n_key=route.alova_request |
| 20 | 12 | 3 | 2 | alova_scenes | alova_scenes | /alova/scenes | view.alova_scenes | false | 1 | icon=cbi:scene-dynamic; icon_type=1; i18n_key=route.alova_scenes |
| 21 | 7 | 2 | 1 | function_hide-child | function_hide-child | /function/hide-child |  | false | 1 | icon=material-symbols:filter-list-off; icon_type=1; i18n_key=route.function_hide-child |
| 22 | 7 |  | 2 | function_multi-tab | function_multi-tab | /function/multi-tab | view.function_multi-tab | false | 1 | hide_in_menu=true; multi_tab=true; icon=ic:round-tab; icon_type=1; i18n_key=route.function_multi-tab; active_menu=function_tab |
| 23 | 7 | 3 | 2 | function_request | function_request | /function/request | view.function_request | false | 1 | icon=carbon:network-overlay; icon_type=1; i18n_key=route.function_request |
| 24 | 7 | 5 | 2 | function_super-page | function_super-page | /function/super-page | view.function_super-page | false | 1 | icon=ic:round-supervisor-account; icon_type=1; i18n_key=route.function_super-page |
| 25 | 7 | 1 | 2 | function_tab | function_tab | /function/tab | view.function_tab | false | 1 | icon=ic:round-tab; icon_type=1; i18n_key=route.function_tab |
| 26 | 13 | 1 | 1 | multi-menu_first | multi-menu_first | /multi-menu/first |  | false | 1 | i18n_key=route.multi-menu_first |
| 27 | 13 | 2 | 1 | multi-menu_second | multi-menu_second | /multi-menu/second |  | false | 1 | i18n_key=route.multi-menu_second |
| 28 | 14 |  | 2 | plugin_barcode | plugin_barcode | /plugin/barcode | view.plugin_barcode | false | 1 | icon=ic:round-barcode; icon_type=1; i18n_key=route.plugin_barcode |
| 29 | 14 |  | 1 | plugin_charts | plugin_charts | /plugin/charts |  | false | 1 | icon=mdi:chart-areaspline; icon_type=1; i18n_key=route.plugin_charts |
| 30 | 14 |  | 2 | plugin_copy | plugin_copy | /plugin/copy | view.plugin_copy | false | 1 | icon=mdi:clipboard-outline; icon_type=1; i18n_key=route.plugin_copy |
| 31 | 14 |  | 1 | plugin_editor | plugin_editor | /plugin/editor |  | false | 1 | icon=icon-park-outline:editor; icon_type=1; i18n_key=route.plugin_editor |
| 32 | 14 |  | 2 | plugin_excel | plugin_excel | /plugin/excel | view.plugin_excel | false | 1 | keep_alive=true; icon=ri:file-excel-2-line; icon_type=1; i18n_key=route.plugin_excel |
| 33 | 14 |  | 1 | plugin_gantt | plugin_gantt | /plugin/gantt |  | false | 1 | icon=ant-design:bar-chart-outlined; icon_type=1; i18n_key=route.plugin_gantt |
| 34 | 14 |  | 2 | plugin_icon | plugin_icon | /plugin/icon | view.plugin_icon | false | 1 | icon=custom-icon; icon_type=2; i18n_key=route.plugin_icon |
| 35 | 14 |  | 2 | plugin_map | plugin_map | /plugin/map | view.plugin_map | false | 1 | icon=mdi:map; icon_type=1; i18n_key=route.plugin_map |
| 36 | 14 |  | 2 | plugin_pdf | plugin_pdf | /plugin/pdf | view.plugin_pdf | false | 1 | icon=uiw:file-pdf; icon_type=1; i18n_key=route.plugin_pdf |
| 37 | 14 |  | 2 | plugin_pinyin | plugin_pinyin | /plugin/pinyin | view.plugin_pinyin | false | 1 | icon=entypo-social:google-hangouts; icon_type=1; i18n_key=route.plugin_pinyin |
| 38 | 14 |  | 2 | plugin_print | plugin_print | /plugin/print | view.plugin_print | false | 1 | icon=mdi:printer; icon_type=1; i18n_key=route.plugin_print |
| 39 | 14 |  | 2 | plugin_swiper | plugin_swiper | /plugin/swiper | view.plugin_swiper | false | 1 | icon=simple-icons:swiper; icon_type=1; i18n_key=route.plugin_swiper |
| 40 | 14 |  | 1 | plugin_tables | plugin_tables | /plugin/tables |  | false | 1 | icon=icon-park-outline:table; icon_type=1; i18n_key=route.plugin_tables |
| 41 | 14 |  | 2 | plugin_typeit | plugin_typeit | /plugin/typeit | view.plugin_typeit | false | 1 | icon=mdi:typewriter; icon_type=1; i18n_key=route.plugin_typeit |
| 42 | 14 |  | 2 | plugin_video | plugin_video | /plugin/video | view.plugin_video | false | 1 | icon=mdi:video; icon_type=1; i18n_key=route.plugin_video |
| 43 | 15 |  | 1 | pro-naive_form | pro-naive_form | /pro-naive/form |  | false | 1 | icon=fluent:form-28-regular; icon_type=1; i18n_key=route.pro-naive_form |
| 44 | 15 |  | 1 | pro-naive_table | pro-naive_table | /pro-naive/table |  | false | 1 | icon=mynaui:table; icon_type=1; i18n_key=route.pro-naive_table |
| 45 | 17 |  | 2 | exception_403 | exception_403 | /exception/403 | view.403 | false | 1 | icon=ic:baseline-block; icon_type=1; i18n_key=route.exception_403 |
| 46 | 17 |  | 2 | exception_404 | exception_404 | /exception/404 | view.404 | false | 1 | icon=ic:baseline-web-asset-off; icon_type=1; i18n_key=route.exception_404 |
| 47 | 17 |  | 2 | exception_500 | exception_500 | /exception/500 | view.500 | false | 1 | icon=ic:baseline-wifi-off; icon_type=1; i18n_key=route.exception_500 |
| 48 | 18 | 7 | 2 | document_antd | document_antd | /document/antd | view.iframe-page | false | 1 | icon=logos:ant-design; icon_type=1; i18n_key=route.document_antd; href=https://antdv.com/components/overview-cn |
| 49 | 18 | 6 | 2 | document_naive | document_naive | /document/naive | view.iframe-page | false | 1 | icon=logos:naiveui; icon_type=1; i18n_key=route.document_naive; href=https://www.naiveui.com/zh-CN/os-theme/docs/introduction |
| 50 | 18 | 6 | 2 | document_pro-naive | document_pro-naive | /document/pro-naive | view.iframe-page | false | 1 | icon=logos:naiveui; icon_type=1; i18n_key=route.document_pro-naive; href=https://naive-ui.pro-components.cn/ |
| 51 | 18 | 7 | 2 | document_alova | document_alova | /document/alova | view.iframe-page | false | 1 | icon=alova; icon_type=2; i18n_key=route.document_alova; href=https://alova.js.org |
| 52 | 18 | 1 | 2 | document_project | document_project | /document/project | view.iframe-page | false | 1 | icon=logo; icon_type=2; i18n_key=route.document_project; href=https://docs.soybeanjs.cn/zh |
| 53 | 18 | 2 | 2 | document_project-link | document_project-link | /document/project-link | view.iframe-page | false | 1 | icon=logo; icon_type=2; i18n_key=route.document_project-link; href=https://docs.soybeanjs.cn/zh |
| 54 | 18 | 2 | 2 | document_video | document_video | /document/video | view.iframe-page | false | 1 | icon=logo; icon_type=2; i18n_key=route.document_video; href=https://www.bilibili.com/video/BV1YKdRYXELC |
| 55 | 18 | 5 | 2 | document_unocss | document_unocss | /document/unocss | view.iframe-page | false | 1 | icon=logos:unocss; icon_type=1; i18n_key=route.document_unocss; href=https://unocss.dev/ |
| 56 | 18 | 4 | 2 | document_vite | document_vite | /document/vite | view.iframe-page | false | 1 | icon=logos:vitejs; icon_type=1; i18n_key=route.document_vite; href=https://cn.vitejs.dev/ |
| 57 | 18 | 3 | 2 | document_vue | document_vue | /document/vue | view.iframe-page | false | 1 | icon=logos:vue; icon_type=1; i18n_key=route.document_vue; href=https://cn.vuejs.org/ |
| 58 | 21 |  | 2 | function_hide-child_one | function_hide-child_one | /function/hide-child/one | view.function_hide-child_one | false | 1 | hide_in_menu=true; icon=material-symbols:filter-list-off; icon_type=1; i18n_key=route.function_hide-child_one; active_menu=function_hide-child |
| 59 | 21 |  | 2 | function_hide-child_three | function_hide-child_three | /function/hide-child/three | view.function_hide-child_three | false | 1 | hide_in_menu=true; i18n_key=route.function_hide-child_three; active_menu=function_hide-child |
| 60 | 21 |  | 2 | function_hide-child_two | function_hide-child_two | /function/hide-child/two | view.function_hide-child_two | false | 1 | hide_in_menu=true; i18n_key=route.function_hide-child_two; active_menu=function_hide-child |
| 61 | 26 |  | 2 | multi-menu_first_child | multi-menu_first_child | /multi-menu/first/child | view.multi-menu_first_child | false | 1 | i18n_key=route.multi-menu_first_child |
| 62 | 27 |  | 1 | multi-menu_second_child | multi-menu_second_child | /multi-menu/second/child |  | false | 1 | i18n_key=route.multi-menu_second_child |
| 63 | 29 |  | 2 | plugin_charts_antv | plugin_charts_antv | /plugin/charts/antv | view.plugin_charts_antv | false | 1 | icon=hugeicons:flow-square; icon_type=1; i18n_key=route.plugin_charts_antv |
| 64 | 29 |  | 2 | plugin_charts_echarts | plugin_charts_echarts | /plugin/charts/echarts | view.plugin_charts_echarts | false | 1 | icon=simple-icons:apacheecharts; icon_type=1; i18n_key=route.plugin_charts_echarts |
| 65 | 29 |  | 2 | plugin_charts_vchart | plugin_charts_vchart | /plugin/charts/vchart | view.plugin_charts_vchart | false | 1 | icon=visactor; icon_type=2; i18n_key=route.plugin_charts_vchart |
| 66 | 31 |  | 2 | plugin_editor_markdown | plugin_editor_markdown | /plugin/editor/markdown | view.plugin_editor_markdown | false | 1 | icon=ri:markdown-line; icon_type=1; i18n_key=route.plugin_editor_markdown |
| 67 | 31 |  | 2 | plugin_editor_quill | plugin_editor_quill | /plugin/editor/quill | view.plugin_editor_quill | false | 1 | icon=mdi:file-document-edit-outline; icon_type=1; i18n_key=route.plugin_editor_quill |
| 68 | 33 |  | 2 | plugin_gantt_dhtmlx | plugin_gantt_dhtmlx | /plugin/gantt/dhtmlx | view.plugin_gantt_dhtmlx | false | 1 | i18n_key=route.plugin_gantt_dhtmlx |
| 69 | 33 |  | 2 | plugin_gantt_vtable | plugin_gantt_vtable | /plugin/gantt/vtable | view.plugin_gantt_vtable | false | 1 | icon=visactor; icon_type=2; i18n_key=route.plugin_gantt_vtable |
| 70 | 40 |  | 2 | plugin_tables_vtable | plugin_tables_vtable | /plugin/tables/vtable | view.plugin_tables_vtable | false | 1 | icon=visactor; icon_type=2; i18n_key=route.plugin_tables_vtable |
| 71 | 43 |  | 2 | pro-naive_form_basic | pro-naive_form_basic | /pro-naive/form/basic | view.pro-naive_form_basic | false | 1 | i18n_key=route.pro-naive_form_basic |
| 72 | 43 |  | 2 | pro-naive_form_query | pro-naive_form_query | /pro-naive/form/query | view.pro-naive_form_query | false | 1 | i18n_key=route.pro-naive_form_query |
| 73 | 43 |  | 2 | pro-naive_form_step | pro-naive_form_step | /pro-naive/form/step | view.pro-naive_form_step | false | 1 | i18n_key=route.pro-naive_form_step |
| 74 | 44 |  | 2 | pro-naive_table_remote | pro-naive_table_remote | /pro-naive/table/remote | view.pro-naive_table_remote | false | 1 | i18n_key=route.pro-naive_table_remote |
| 75 | 44 |  | 2 | pro-naive_table_row-edit | pro-naive_table_row-edit | /pro-naive/table/row-edit | view.pro-naive_table_row-edit | false | 1 | i18n_key=route.pro-naive_table_row-edit |
| 76 | 62 |  | 2 | multi-menu_second_child_home | multi-menu_second_child_home | /multi-menu/second/child/home | view.multi-menu_second_child_home | false | 1 | i18n_key=route.multi-menu_second_child_home |
| 77 | 2 | 6 | 2 | manage_audit | manage_audit | /manage/audit | view.manage_audit | false | 1 | icon=mdi:clipboard-text-search-outline; icon_type=1; i18n_key=route.manage_audit |
| 78 | 2 | 7 | 2 | manage_ip-rule | manage_ip-rule | /manage/ip-rule | view.manage_ip-rule | false | 1 | icon=mdi:shield-lock-outline; icon_type=1; i18n_key=route.manage_ip-rule; buttons=[{'code': 'ipRule:add', 'desc': '新增IP规则'}, {'code': 'ipRule:edit', 'desc': '编辑IP规则'}, {'code': 'ipRule:delete', 'desc': '删除IP规则'}, {'code': 'ipRule:restore', 'desc': '恢复IP规则'}] |

## casbin_rule（163 列；委派建表、欄序不入親排）

全表共通：`created_at`=`2026-08-04T19:14:44.255156+00:00`、`created_by`=NULL、`ptype`=`p`、`v3`=``、`v4`=``、`v5`=``（授權政策全為 p 規則；grouping 依 v0 角色）

角色×類別統計：

| v0 | 列數 | v2 分佈 |
|---|---|---|
| R_SUPER | 147 | menu×77、POST×22、GET×21、button×20、DELETE×7 |
| R_ADMIN | 11 | menu×5、GET×3、button×3 |
| R_USER_COMMON | 5 | menu×3、GET×1、button×1 |

### R_SUPER（147 列）

| id | v1 | v2 | protected |
|---|---|---|---|
| 1 | /systemManage/getUserList | GET | false |
| 3 | home | menu | false |
| 6 | manage_user | menu | false |
| 8 | manage_user-detail | menu | false |
| 10 | manage_role | menu | true |
| 11 | manage_menu | menu | true |
| 12 | /systemManage/getRoleList | GET | false |
| 14 | /systemManage/getAllRoles | GET | false |
| 17 | /systemManage/addUser | POST | false |
| 18 | /systemManage/updateUser | POST | false |
| 19 | /systemManage/deleteUser | DELETE | false |
| 20 | /systemManage/batchDeleteUser | DELETE | false |
| 21 | /systemManage/addRole | POST | false |
| 22 | /systemManage/updateRole | POST | false |
| 23 | /systemManage/deleteRole | DELETE | false |
| 24 | /systemManage/batchDeleteRole | DELETE | false |
| 25 | /systemManage/getMenuList/v2 | GET | false |
| 26 | /systemManage/getAllPages | GET | false |
| 27 | /systemManage/getMenuTree | GET | false |
| 28 | /systemManage/addMenu | POST | false |
| 29 | /systemManage/updateMenu | POST | false |
| 30 | /systemManage/deleteMenu | DELETE | false |
| 31 | /systemManage/batchDeleteMenu | DELETE | false |
| 32 | /systemManage/getRoleMenu | GET | true |
| 33 | /systemManage/updateRoleMenu | POST | true |
| 34 | /systemManage/getRoleHome | GET | false |
| 35 | /systemManage/updateRoleHome | POST | false |
| 36 | B_CODE1 | button | false |
| 37 | B_CODE2 | button | false |
| 38 | B_CODE3 | button | false |
| 39 | user:add | button | false |
| 40 | user:edit | button | false |
| 41 | user:delete | button | false |
| 46 | function | menu | false |
| 49 | function_toggle-auth | menu | false |
| 52 | /systemManage/getAllButtons | GET | true |
| 53 | /systemManage/getRoleButton | GET | true |
| 54 | /systemManage/updateRoleButton | POST | true |
| 55 | /systemManage/getAllEndpoints | GET | true |
| 56 | /systemManage/getRoleEndpoints | GET | true |
| 57 | /systemManage/updateRoleEndpoints | POST | true |
| 58 | role:add | button | false |
| 59 | role:edit | button | false |
| 60 | role:delete | button | false |
| 61 | menu:add | button | false |
| 62 | menu:edit | button | false |
| 63 | menu:delete | button | false |
| 64 | /systemManage/getDeletedMenus | GET | true |
| 65 | /systemManage/restoreMenu | POST | true |
| 66 | /systemManage/getSystemSettings | GET | true |
| 67 | /systemManage/updateSystemSetting | POST | true |
| 68 | /systemManage/updateUserSessionPolicy | POST | true |
| 69 | manage_system-settings | menu | true |
| 70 | /systemManage/getArchivedPolicies | GET | true |
| 71 | /systemManage/restorePolicy | POST | true |
| 72 | manage_policy-archive | menu | true |
| 73 | about | menu | false |
| 74 | alova | menu | false |
| 75 | alova_request | menu | false |
| 76 | alova_scenes | menu | false |
| 77 | function_hide-child | menu | false |
| 78 | function_hide-child_one | menu | false |
| 79 | function_hide-child_three | menu | false |
| 80 | function_hide-child_two | menu | false |
| 81 | function_multi-tab | menu | false |
| 82 | function_request | menu | false |
| 83 | function_super-page | menu | false |
| 84 | function_tab | menu | false |
| 85 | multi-menu | menu | false |
| 86 | multi-menu_first | menu | false |
| 87 | multi-menu_first_child | menu | false |
| 88 | multi-menu_second | menu | false |
| 89 | multi-menu_second_child | menu | false |
| 90 | multi-menu_second_child_home | menu | false |
| 91 | plugin | menu | false |
| 92 | plugin_barcode | menu | false |
| 93 | plugin_charts | menu | false |
| 94 | plugin_charts_antv | menu | false |
| 95 | plugin_charts_echarts | menu | false |
| 96 | plugin_charts_vchart | menu | false |
| 97 | plugin_copy | menu | false |
| 98 | plugin_editor | menu | false |
| 99 | plugin_editor_markdown | menu | false |
| 100 | plugin_editor_quill | menu | false |
| 101 | plugin_excel | menu | false |
| 102 | plugin_gantt | menu | false |
| 103 | plugin_gantt_dhtmlx | menu | false |
| 104 | plugin_gantt_vtable | menu | false |
| 105 | plugin_icon | menu | false |
| 106 | plugin_map | menu | false |
| 107 | plugin_pdf | menu | false |
| 108 | plugin_pinyin | menu | false |
| 109 | plugin_print | menu | false |
| 110 | plugin_swiper | menu | false |
| 111 | plugin_tables | menu | false |
| 112 | plugin_tables_vtable | menu | false |
| 113 | plugin_typeit | menu | false |
| 114 | plugin_video | menu | false |
| 115 | pro-naive | menu | false |
| 116 | pro-naive_form | menu | false |
| 117 | pro-naive_form_basic | menu | false |
| 118 | pro-naive_form_query | menu | false |
| 119 | pro-naive_form_step | menu | false |
| 120 | pro-naive_table | menu | false |
| 121 | pro-naive_table_remote | menu | false |
| 122 | pro-naive_table_row-edit | menu | false |
| 123 | user-center | menu | false |
| 124 | exception | menu | false |
| 125 | exception_403 | menu | false |
| 126 | exception_404 | menu | false |
| 127 | exception_500 | menu | false |
| 128 | document | menu | false |
| 129 | document_antd | menu | false |
| 130 | document_naive | menu | false |
| 131 | document_pro-naive | menu | false |
| 132 | document_alova | menu | false |
| 133 | document_project | menu | false |
| 134 | document_project-link | menu | false |
| 135 | document_video | menu | false |
| 136 | document_unocss | menu | false |
| 137 | document_vite | menu | false |
| 138 | document_vue | menu | false |
| 139 | /systemManage/getOperationLog | GET | false |
| 140 | /systemManage/getAccessLog | GET | false |
| 141 | /systemManage/getLoginAttempt | GET | false |
| 142 | manage_audit | menu | false |
| 143 | /systemManage/getIpRuleList | GET | false |
| 144 | /systemManage/addIpRule | POST | false |
| 145 | /systemManage/updateIpRule | POST | false |
| 146 | /systemManage/deleteIpRule | DELETE | false |
| 147 | /systemManage/restoreIpRule | POST | false |
| 148 | /systemManage/unlockLogin | POST | false |
| 149 | manage_ip-rule | menu | false |
| 150 | user:restore | button | false |
| 151 | /systemManage/resetUserPassword | POST | false |
| 152 | /systemManage/restoreUser | POST | false |
| 153 | user:reset-pwd | button | false |
| 154 | /systemManage/kickUser | POST | false |
| 155 | /systemManage/getDeletedUsers | GET | false |
| 156 | user:kick | button | false |
| 157 | user:unlock | button | false |
| 158 | /systemManage/getSessionEvent | GET | false |
| 159 | /systemManage/purgeAuditLog | POST | false |
| 160 | ipRule:add | button | false |
| 161 | ipRule:delete | button | false |
| 162 | ipRule:restore | button | false |
| 163 | ipRule:edit | button | false |

### R_ADMIN（11 列）

| id | v1 | v2 | protected |
|---|---|---|---|
| 2 | /systemManage/getUserList | GET | false |
| 4 | home | menu | false |
| 7 | manage_user | menu | false |
| 9 | manage_user-detail | menu | false |
| 13 | /systemManage/getRoleList | GET | false |
| 15 | /systemManage/getAllRoles | GET | false |
| 42 | B_CODE2 | button | false |
| 43 | B_CODE3 | button | false |
| 44 | user:edit | button | false |
| 47 | function | menu | false |
| 50 | function_toggle-auth | menu | false |

### R_USER_COMMON（5 列）

| id | v1 | v2 | protected |
|---|---|---|---|
| 5 | home | menu | false |
| 16 | /systemManage/getAllRoles | GET | false |
| 45 | B_CODE3 | button | false |
| 48 | function | menu | false |
| 51 | function_toggle-auth | menu | false |

## 空表（9 張、逐一列名）

- session_event（0 列）
- sys_access_log（0 列）
- sys_casbin_policy_archive（0 列）
- sys_ip_rule（0 列）
- sys_login_attempt（0 列）
- sys_operation_log（0 列）
- sys_pwd_custody（0 列）
- sys_token（0 列）
- sys_user_email_verify（0 列）

## sequences 落值（重放終態）

| sequence | last_value |
|---|---|
| casbin_rule_id_seq | 163 |
| session_event_id_seq | （未動用） |
| sys_access_log_id_seq | （未動用） |
| sys_casbin_policy_archive_id_seq | （未動用） |
| sys_ip_rule_id_seq | （未動用） |
| sys_login_attempt_id_seq | （未動用） |
| sys_menu_id_seq | 78 |
| sys_operation_log_id_seq | （未動用） |
| sys_role_id_seq | 3 |
| sys_token_id_seq | （未動用） |
| sys_user_id_seq | 3 |


## 定稿紀錄（工作坊裁定、2026-08-05）

上列各表為 rev4 淨效果**原樣素材**；定稿＝原樣＋下列裁定。機器定稿檔＝同目錄
`seed-decision.json`（m001/m002 施工與 fixtures 凍結以此為準；其 meta 帶素材檔 sha256 血緣）。

**總簽核**：user 確認定稿 2026-08-05（Q1 全面定稿字面／Q2 逐字轉繁＋`登录→登入`、
`菜单→選單` 修正／其餘全表照收，悉數入定）。本檔自此為 seed 基線定稿紀錄、素材節轉史料。

- **Q1（決定性）＝甲・全面定稿字面**：`created_at` 全庫 263 列統一寫死
  `2026-08-05T00:00:00+00:00`；`password` 採本次重放萃取 PHC 為定稿常數（三帳共用、
  plaintext `123456`）：
  `$argon2id$v=19$m=19456,t=2,p=1$+ZAAyoj4MZZ1PExc1Sg6Dg$lo82SGIO9NGwaiefXAmdgf0cHorl5QjrFOm0/wgz0bM`
- **Q2（簡→繁深度）＝B・逐字轉換＋語意陷阱與台灣用語修正**（`登录`→`登入` 1 筆、
  `菜单`→`選單` 3 筆——user 補充裁定）：改值 22 筆（下表）；同形免改 2 筆載錄備查
  （`新增角色`、`插件示例`）；全庫簡體殘留掃描零命中（機器斷言）。
- **其餘全表照收**：user 裁定「簡體轉繁體、其它照 rev4 搬」——6 有料表其餘欄值、
  9 空表、sequences 落值悉照原樣。

| 表#id | 欄 | rev4 原值 | rev5 定稿值 |
|---|---|---|---|
| sys_role#1 | role_name | 超级管理员 | 超級管理員 |
| sys_role#2 | role_name | 管理员 | 管理員 |
| sys_role#3 | role_name | 普通用户 | 普通用戶 |
| sys_menu#3 | buttons[user:add].desc | 新增用户 | 新增用戶 |
| sys_menu#3 | buttons[user:edit].desc | 编辑用户 | 編輯用戶 |
| sys_menu#3 | buttons[user:delete].desc | 删除用户 | 刪除用戶 |
| sys_menu#3 | buttons[user:reset-pwd].desc | 重置密码 | 重置密碼 |
| sys_menu#3 | buttons[user:kick].desc | 踢除下线 | 踢除下線 |
| sys_menu#3 | buttons[user:restore].desc | 复原用户 | 復原用戶 |
| sys_menu#3 | buttons[user:unlock].desc | 解锁登录 | 解鎖登入 |
| sys_menu#4 | buttons[role:edit].desc | 编辑角色 | 編輯角色 |
| sys_menu#4 | buttons[role:delete].desc | 删除角色 | 刪除角色 |
| sys_menu#5 | buttons[menu:add].desc | 新增菜单 | 新增選單 |
| sys_menu#5 | buttons[menu:edit].desc | 编辑菜单 | 編輯選單 |
| sys_menu#5 | buttons[menu:delete].desc | 删除菜单 | 刪除選單 |
| sys_menu#8 | buttons[B_CODE1].desc | 超级管理员可见 | 超級管理員可見 |
| sys_menu#8 | buttons[B_CODE2].desc | 管理员可见 | 管理員可見 |
| sys_menu#8 | buttons[B_CODE3].desc | 管理员或普通用户可见 | 管理員或普通用戶可見 |
| sys_menu#78 | buttons[ipRule:add].desc | 新增IP规则 | 新增IP規則 |
| sys_menu#78 | buttons[ipRule:edit].desc | 编辑IP规则 | 編輯IP規則 |
| sys_menu#78 | buttons[ipRule:delete].desc | 删除IP规则 | 刪除IP規則 |
| sys_menu#78 | buttons[ipRule:restore].desc | 恢复IP规则 | 恢復IP規則 |

