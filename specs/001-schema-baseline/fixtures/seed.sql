--
-- PostgreSQL database dump
--


-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: casbin_rule; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.casbin_rule (id, ptype, v0, v1, v2, v3, v4, v5, protected, created_at, created_by) FROM stdin;
1	p	R_SUPER	/systemManage/getUserList	GET				f	2026-08-05 00:00:00+00	\N
10	p	R_SUPER	manage_role	menu				t	2026-08-05 00:00:00+00	\N
100	p	R_SUPER	plugin_editor_quill	menu				f	2026-08-05 00:00:00+00	\N
101	p	R_SUPER	plugin_excel	menu				f	2026-08-05 00:00:00+00	\N
102	p	R_SUPER	plugin_gantt	menu				f	2026-08-05 00:00:00+00	\N
103	p	R_SUPER	plugin_gantt_dhtmlx	menu				f	2026-08-05 00:00:00+00	\N
104	p	R_SUPER	plugin_gantt_vtable	menu				f	2026-08-05 00:00:00+00	\N
105	p	R_SUPER	plugin_icon	menu				f	2026-08-05 00:00:00+00	\N
106	p	R_SUPER	plugin_map	menu				f	2026-08-05 00:00:00+00	\N
107	p	R_SUPER	plugin_pdf	menu				f	2026-08-05 00:00:00+00	\N
108	p	R_SUPER	plugin_pinyin	menu				f	2026-08-05 00:00:00+00	\N
109	p	R_SUPER	plugin_print	menu				f	2026-08-05 00:00:00+00	\N
11	p	R_SUPER	manage_menu	menu				t	2026-08-05 00:00:00+00	\N
110	p	R_SUPER	plugin_swiper	menu				f	2026-08-05 00:00:00+00	\N
111	p	R_SUPER	plugin_tables	menu				f	2026-08-05 00:00:00+00	\N
112	p	R_SUPER	plugin_tables_vtable	menu				f	2026-08-05 00:00:00+00	\N
113	p	R_SUPER	plugin_typeit	menu				f	2026-08-05 00:00:00+00	\N
114	p	R_SUPER	plugin_video	menu				f	2026-08-05 00:00:00+00	\N
115	p	R_SUPER	pro-naive	menu				f	2026-08-05 00:00:00+00	\N
116	p	R_SUPER	pro-naive_form	menu				f	2026-08-05 00:00:00+00	\N
117	p	R_SUPER	pro-naive_form_basic	menu				f	2026-08-05 00:00:00+00	\N
118	p	R_SUPER	pro-naive_form_query	menu				f	2026-08-05 00:00:00+00	\N
119	p	R_SUPER	pro-naive_form_step	menu				f	2026-08-05 00:00:00+00	\N
12	p	R_SUPER	/systemManage/getRoleList	GET				f	2026-08-05 00:00:00+00	\N
120	p	R_SUPER	pro-naive_table	menu				f	2026-08-05 00:00:00+00	\N
121	p	R_SUPER	pro-naive_table_remote	menu				f	2026-08-05 00:00:00+00	\N
122	p	R_SUPER	pro-naive_table_row-edit	menu				f	2026-08-05 00:00:00+00	\N
123	p	R_SUPER	user-center	menu				f	2026-08-05 00:00:00+00	\N
124	p	R_SUPER	exception	menu				f	2026-08-05 00:00:00+00	\N
125	p	R_SUPER	exception_403	menu				f	2026-08-05 00:00:00+00	\N
126	p	R_SUPER	exception_404	menu				f	2026-08-05 00:00:00+00	\N
127	p	R_SUPER	exception_500	menu				f	2026-08-05 00:00:00+00	\N
128	p	R_SUPER	document	menu				f	2026-08-05 00:00:00+00	\N
129	p	R_SUPER	document_antd	menu				f	2026-08-05 00:00:00+00	\N
13	p	R_ADMIN	/systemManage/getRoleList	GET				f	2026-08-05 00:00:00+00	\N
130	p	R_SUPER	document_naive	menu				f	2026-08-05 00:00:00+00	\N
131	p	R_SUPER	document_pro-naive	menu				f	2026-08-05 00:00:00+00	\N
132	p	R_SUPER	document_alova	menu				f	2026-08-05 00:00:00+00	\N
133	p	R_SUPER	document_project	menu				f	2026-08-05 00:00:00+00	\N
134	p	R_SUPER	document_project-link	menu				f	2026-08-05 00:00:00+00	\N
135	p	R_SUPER	document_video	menu				f	2026-08-05 00:00:00+00	\N
136	p	R_SUPER	document_unocss	menu				f	2026-08-05 00:00:00+00	\N
137	p	R_SUPER	document_vite	menu				f	2026-08-05 00:00:00+00	\N
138	p	R_SUPER	document_vue	menu				f	2026-08-05 00:00:00+00	\N
139	p	R_SUPER	/systemManage/getOperationLog	GET				f	2026-08-05 00:00:00+00	\N
14	p	R_SUPER	/systemManage/getAllRoles	GET				f	2026-08-05 00:00:00+00	\N
140	p	R_SUPER	/systemManage/getAccessLog	GET				f	2026-08-05 00:00:00+00	\N
141	p	R_SUPER	/systemManage/getLoginAttempt	GET				f	2026-08-05 00:00:00+00	\N
142	p	R_SUPER	manage_audit	menu				f	2026-08-05 00:00:00+00	\N
143	p	R_SUPER	/systemManage/getIpRuleList	GET				f	2026-08-05 00:00:00+00	\N
144	p	R_SUPER	/systemManage/addIpRule	POST				f	2026-08-05 00:00:00+00	\N
145	p	R_SUPER	/systemManage/updateIpRule	POST				f	2026-08-05 00:00:00+00	\N
146	p	R_SUPER	/systemManage/deleteIpRule	DELETE				f	2026-08-05 00:00:00+00	\N
147	p	R_SUPER	/systemManage/restoreIpRule	POST				f	2026-08-05 00:00:00+00	\N
148	p	R_SUPER	/systemManage/unlockLogin	POST				f	2026-08-05 00:00:00+00	\N
149	p	R_SUPER	manage_ip-rule	menu				f	2026-08-05 00:00:00+00	\N
15	p	R_ADMIN	/systemManage/getAllRoles	GET				f	2026-08-05 00:00:00+00	\N
150	p	R_SUPER	user:restore	button				f	2026-08-05 00:00:00+00	\N
151	p	R_SUPER	/systemManage/resetUserPassword	POST				f	2026-08-05 00:00:00+00	\N
152	p	R_SUPER	/systemManage/restoreUser	POST				f	2026-08-05 00:00:00+00	\N
153	p	R_SUPER	user:reset-pwd	button				f	2026-08-05 00:00:00+00	\N
154	p	R_SUPER	/systemManage/kickUser	POST				f	2026-08-05 00:00:00+00	\N
155	p	R_SUPER	/systemManage/getDeletedUsers	GET				f	2026-08-05 00:00:00+00	\N
156	p	R_SUPER	user:kick	button				f	2026-08-05 00:00:00+00	\N
157	p	R_SUPER	user:unlock	button				f	2026-08-05 00:00:00+00	\N
158	p	R_SUPER	/systemManage/getSessionEvent	GET				f	2026-08-05 00:00:00+00	\N
159	p	R_SUPER	/systemManage/purgeAuditLog	POST				f	2026-08-05 00:00:00+00	\N
16	p	R_USER_COMMON	/systemManage/getAllRoles	GET				f	2026-08-05 00:00:00+00	\N
160	p	R_SUPER	ipRule:add	button				f	2026-08-05 00:00:00+00	\N
161	p	R_SUPER	ipRule:delete	button				f	2026-08-05 00:00:00+00	\N
162	p	R_SUPER	ipRule:restore	button				f	2026-08-05 00:00:00+00	\N
163	p	R_SUPER	ipRule:edit	button				f	2026-08-05 00:00:00+00	\N
17	p	R_SUPER	/systemManage/addUser	POST				f	2026-08-05 00:00:00+00	\N
18	p	R_SUPER	/systemManage/updateUser	POST				f	2026-08-05 00:00:00+00	\N
19	p	R_SUPER	/systemManage/deleteUser	DELETE				f	2026-08-05 00:00:00+00	\N
2	p	R_ADMIN	/systemManage/getUserList	GET				f	2026-08-05 00:00:00+00	\N
20	p	R_SUPER	/systemManage/batchDeleteUser	DELETE				f	2026-08-05 00:00:00+00	\N
21	p	R_SUPER	/systemManage/addRole	POST				f	2026-08-05 00:00:00+00	\N
22	p	R_SUPER	/systemManage/updateRole	POST				f	2026-08-05 00:00:00+00	\N
23	p	R_SUPER	/systemManage/deleteRole	DELETE				f	2026-08-05 00:00:00+00	\N
24	p	R_SUPER	/systemManage/batchDeleteRole	DELETE				f	2026-08-05 00:00:00+00	\N
25	p	R_SUPER	/systemManage/getMenuList/v2	GET				f	2026-08-05 00:00:00+00	\N
26	p	R_SUPER	/systemManage/getAllPages	GET				f	2026-08-05 00:00:00+00	\N
27	p	R_SUPER	/systemManage/getMenuTree	GET				f	2026-08-05 00:00:00+00	\N
28	p	R_SUPER	/systemManage/addMenu	POST				f	2026-08-05 00:00:00+00	\N
29	p	R_SUPER	/systemManage/updateMenu	POST				f	2026-08-05 00:00:00+00	\N
3	p	R_SUPER	home	menu				f	2026-08-05 00:00:00+00	\N
30	p	R_SUPER	/systemManage/deleteMenu	DELETE				f	2026-08-05 00:00:00+00	\N
31	p	R_SUPER	/systemManage/batchDeleteMenu	DELETE				f	2026-08-05 00:00:00+00	\N
32	p	R_SUPER	/systemManage/getRoleMenu	GET				t	2026-08-05 00:00:00+00	\N
33	p	R_SUPER	/systemManage/updateRoleMenu	POST				t	2026-08-05 00:00:00+00	\N
34	p	R_SUPER	/systemManage/getRoleHome	GET				f	2026-08-05 00:00:00+00	\N
35	p	R_SUPER	/systemManage/updateRoleHome	POST				f	2026-08-05 00:00:00+00	\N
36	p	R_SUPER	B_CODE1	button				f	2026-08-05 00:00:00+00	\N
37	p	R_SUPER	B_CODE2	button				f	2026-08-05 00:00:00+00	\N
38	p	R_SUPER	B_CODE3	button				f	2026-08-05 00:00:00+00	\N
39	p	R_SUPER	user:add	button				f	2026-08-05 00:00:00+00	\N
4	p	R_ADMIN	home	menu				f	2026-08-05 00:00:00+00	\N
40	p	R_SUPER	user:edit	button				f	2026-08-05 00:00:00+00	\N
41	p	R_SUPER	user:delete	button				f	2026-08-05 00:00:00+00	\N
42	p	R_ADMIN	B_CODE2	button				f	2026-08-05 00:00:00+00	\N
43	p	R_ADMIN	B_CODE3	button				f	2026-08-05 00:00:00+00	\N
44	p	R_ADMIN	user:edit	button				f	2026-08-05 00:00:00+00	\N
45	p	R_USER_COMMON	B_CODE3	button				f	2026-08-05 00:00:00+00	\N
46	p	R_SUPER	function	menu				f	2026-08-05 00:00:00+00	\N
47	p	R_ADMIN	function	menu				f	2026-08-05 00:00:00+00	\N
48	p	R_USER_COMMON	function	menu				f	2026-08-05 00:00:00+00	\N
49	p	R_SUPER	function_toggle-auth	menu				f	2026-08-05 00:00:00+00	\N
5	p	R_USER_COMMON	home	menu				f	2026-08-05 00:00:00+00	\N
50	p	R_ADMIN	function_toggle-auth	menu				f	2026-08-05 00:00:00+00	\N
51	p	R_USER_COMMON	function_toggle-auth	menu				f	2026-08-05 00:00:00+00	\N
52	p	R_SUPER	/systemManage/getAllButtons	GET				t	2026-08-05 00:00:00+00	\N
53	p	R_SUPER	/systemManage/getRoleButton	GET				t	2026-08-05 00:00:00+00	\N
54	p	R_SUPER	/systemManage/updateRoleButton	POST				t	2026-08-05 00:00:00+00	\N
55	p	R_SUPER	/systemManage/getAllEndpoints	GET				t	2026-08-05 00:00:00+00	\N
56	p	R_SUPER	/systemManage/getRoleEndpoints	GET				t	2026-08-05 00:00:00+00	\N
57	p	R_SUPER	/systemManage/updateRoleEndpoints	POST				t	2026-08-05 00:00:00+00	\N
58	p	R_SUPER	role:add	button				f	2026-08-05 00:00:00+00	\N
59	p	R_SUPER	role:edit	button				f	2026-08-05 00:00:00+00	\N
6	p	R_SUPER	manage_user	menu				f	2026-08-05 00:00:00+00	\N
60	p	R_SUPER	role:delete	button				f	2026-08-05 00:00:00+00	\N
61	p	R_SUPER	menu:add	button				f	2026-08-05 00:00:00+00	\N
62	p	R_SUPER	menu:edit	button				f	2026-08-05 00:00:00+00	\N
63	p	R_SUPER	menu:delete	button				f	2026-08-05 00:00:00+00	\N
64	p	R_SUPER	/systemManage/getDeletedMenus	GET				t	2026-08-05 00:00:00+00	\N
65	p	R_SUPER	/systemManage/restoreMenu	POST				t	2026-08-05 00:00:00+00	\N
66	p	R_SUPER	/systemManage/getSystemSettings	GET				t	2026-08-05 00:00:00+00	\N
67	p	R_SUPER	/systemManage/updateSystemSetting	POST				t	2026-08-05 00:00:00+00	\N
68	p	R_SUPER	/systemManage/updateUserSessionPolicy	POST				t	2026-08-05 00:00:00+00	\N
69	p	R_SUPER	manage_system-settings	menu				t	2026-08-05 00:00:00+00	\N
7	p	R_ADMIN	manage_user	menu				f	2026-08-05 00:00:00+00	\N
70	p	R_SUPER	/systemManage/getArchivedPolicies	GET				t	2026-08-05 00:00:00+00	\N
71	p	R_SUPER	/systemManage/restorePolicy	POST				t	2026-08-05 00:00:00+00	\N
72	p	R_SUPER	manage_policy-archive	menu				t	2026-08-05 00:00:00+00	\N
73	p	R_SUPER	about	menu				f	2026-08-05 00:00:00+00	\N
74	p	R_SUPER	alova	menu				f	2026-08-05 00:00:00+00	\N
75	p	R_SUPER	alova_request	menu				f	2026-08-05 00:00:00+00	\N
76	p	R_SUPER	alova_scenes	menu				f	2026-08-05 00:00:00+00	\N
77	p	R_SUPER	function_hide-child	menu				f	2026-08-05 00:00:00+00	\N
78	p	R_SUPER	function_hide-child_one	menu				f	2026-08-05 00:00:00+00	\N
79	p	R_SUPER	function_hide-child_three	menu				f	2026-08-05 00:00:00+00	\N
8	p	R_SUPER	manage_user-detail	menu				f	2026-08-05 00:00:00+00	\N
80	p	R_SUPER	function_hide-child_two	menu				f	2026-08-05 00:00:00+00	\N
81	p	R_SUPER	function_multi-tab	menu				f	2026-08-05 00:00:00+00	\N
82	p	R_SUPER	function_request	menu				f	2026-08-05 00:00:00+00	\N
83	p	R_SUPER	function_super-page	menu				f	2026-08-05 00:00:00+00	\N
84	p	R_SUPER	function_tab	menu				f	2026-08-05 00:00:00+00	\N
85	p	R_SUPER	multi-menu	menu				f	2026-08-05 00:00:00+00	\N
86	p	R_SUPER	multi-menu_first	menu				f	2026-08-05 00:00:00+00	\N
87	p	R_SUPER	multi-menu_first_child	menu				f	2026-08-05 00:00:00+00	\N
88	p	R_SUPER	multi-menu_second	menu				f	2026-08-05 00:00:00+00	\N
89	p	R_SUPER	multi-menu_second_child	menu				f	2026-08-05 00:00:00+00	\N
9	p	R_ADMIN	manage_user-detail	menu				f	2026-08-05 00:00:00+00	\N
90	p	R_SUPER	multi-menu_second_child_home	menu				f	2026-08-05 00:00:00+00	\N
91	p	R_SUPER	plugin	menu				f	2026-08-05 00:00:00+00	\N
92	p	R_SUPER	plugin_barcode	menu				f	2026-08-05 00:00:00+00	\N
93	p	R_SUPER	plugin_charts	menu				f	2026-08-05 00:00:00+00	\N
94	p	R_SUPER	plugin_charts_antv	menu				f	2026-08-05 00:00:00+00	\N
95	p	R_SUPER	plugin_charts_echarts	menu				f	2026-08-05 00:00:00+00	\N
96	p	R_SUPER	plugin_charts_vchart	menu				f	2026-08-05 00:00:00+00	\N
97	p	R_SUPER	plugin_copy	menu				f	2026-08-05 00:00:00+00	\N
98	p	R_SUPER	plugin_editor	menu				f	2026-08-05 00:00:00+00	\N
99	p	R_SUPER	plugin_editor_markdown	menu				f	2026-08-05 00:00:00+00	\N
\.


--
-- Data for Name: session_event; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.session_event (id, created_at, created_by, user_id, sid, event_type, reason, source_ip) FROM stdin;
\.


--
-- Data for Name: sys_access_log; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_access_log (id, created_at, created_by, http_status, http_method, http_path, real_ip, peer_ip, x_forwarded_for, ip_confidence, region, trace_id) FROM stdin;
\.


--
-- Data for Name: sys_casbin_policy_archive; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_casbin_policy_archive (id, role_id, created_at, created_by, archived_at, archived_by, archive_reason, ptype, v0, v1, v2, v3, v4, v5) FROM stdin;
\.


--
-- Data for Name: sys_ip_rule; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_ip_rule (id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, "order", wbip_type, wbip_cidr, wbip_memo) FROM stdin;
\.


--
-- Data for Name: sys_login_attempt; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_login_attempt (id, created_at, created_by, success, attempted_user_name, real_ip, peer_ip, x_forwarded_for, ip_confidence, region, trace_id) FROM stdin;
\.


--
-- Data for Name: sys_menu; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_menu (id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, status, "order", hide_in_menu, keep_alive, constant, multi_tab, protected, parent_id, menu_type, menu_name, menu_memo, route_name, route_path, component, icon, icon_type, i18n_key, href, active_menu, fixed_index_in_tab, query, buttons) FROM stdin;
1	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1	\N	\N	\N	\N	t	\N	2	home	\N	home	/home	layout.base$view.home	mdi:monitor-dashboard	1	route.home	\N	\N	\N	\N	\N
10	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	5	\N	\N	\N	\N	t	2	2	manage_policy-archive	\N	manage_policy-archive	/manage/policy-archive	view.manage_policy-archive	mdi:recycle	1	route.manage_policy-archive	\N	\N	\N	\N	\N
11	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1000	f	f	f	f	f	\N	2	about	\N	about	/about	layout.base$view.about	fluent:book-information-24-regular	1	route.about	\N	\N	\N	\N	\N
12	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1005	f	f	f	f	f	\N	1	alova	\N	alova	/alova	layout.base	carbon:http	1	route.alova	\N	\N	\N	\N	\N
13	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1009	f	f	f	f	f	\N	1	multi-menu	\N	multi-menu	/multi-menu	layout.base		\N	route.multi-menu	\N	\N	\N	\N	\N
14	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1006	f	f	f	f	f	\N	1	插件示例	\N	plugin	/plugin	layout.base	clarity:plugin-line	1	route.plugin	\N	\N	\N	\N	\N
15	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1008	f	f	f	f	f	\N	1	pro-naive	\N	pro-naive	/pro-naive	layout.base	material-symbols-light:demography-outline-rounded	1	route.pro-naive	\N	\N	\N	\N	\N
16	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	999	t	f	f	f	f	\N	2	user-center	\N	user-center	/user-center	layout.base$view.user-center		\N	route.user-center	\N	\N	\N	\N	\N
17	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1003	f	f	f	f	f	\N	1	exception	\N	exception	/exception	layout.base	ant-design:exception-outlined	1	route.exception	\N	\N	\N	\N	\N
18	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1002	f	f	f	f	f	\N	1	document	\N	document	/document	layout.base	mdi:file-document-multiple-outline	1	route.document	\N	\N	\N	\N	\N
19	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1	\N	\N	\N	\N	f	12	2	alova_request	\N	alova_request	/alova/request	view.alova_request	\N	\N	route.alova_request	\N	\N	\N	\N	\N
2	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	2	f	f	f	f	t	\N	1	manage	\N	manage	/manage	layout.base	carbon:cloud-service-management	1	route.manage	\N	\N	\N	\N	\N
20	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	3	\N	\N	\N	\N	f	12	2	alova_scenes	\N	alova_scenes	/alova/scenes	view.alova_scenes	cbi:scene-dynamic	1	route.alova_scenes	\N	\N	\N	\N	\N
21	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	2	\N	\N	\N	\N	f	7	1	function_hide-child	\N	function_hide-child	/function/hide-child	\N	material-symbols:filter-list-off	1	route.function_hide-child	\N	\N	\N	\N	\N
22	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	t	\N	\N	t	f	7	2	function_multi-tab	\N	function_multi-tab	/function/multi-tab	view.function_multi-tab	ic:round-tab	1	route.function_multi-tab	\N	function_tab	\N	\N	\N
23	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	3	\N	\N	\N	\N	f	7	2	function_request	\N	function_request	/function/request	view.function_request	carbon:network-overlay	1	route.function_request	\N	\N	\N	\N	\N
24	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	5	\N	\N	\N	\N	f	7	2	function_super-page	\N	function_super-page	/function/super-page	view.function_super-page	ic:round-supervisor-account	1	route.function_super-page	\N	\N	\N	\N	\N
25	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1	\N	\N	\N	\N	f	7	2	function_tab	\N	function_tab	/function/tab	view.function_tab	ic:round-tab	1	route.function_tab	\N	\N	\N	\N	\N
26	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1	\N	\N	\N	\N	f	13	1	multi-menu_first	\N	multi-menu_first	/multi-menu/first	\N	\N	\N	route.multi-menu_first	\N	\N	\N	\N	\N
27	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	2	\N	\N	\N	\N	f	13	1	multi-menu_second	\N	multi-menu_second	/multi-menu/second	\N	\N	\N	route.multi-menu_second	\N	\N	\N	\N	\N
28	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_barcode	\N	plugin_barcode	/plugin/barcode	view.plugin_barcode	ic:round-barcode	1	route.plugin_barcode	\N	\N	\N	\N	\N
29	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	1	plugin_charts	\N	plugin_charts	/plugin/charts	\N	mdi:chart-areaspline	1	route.plugin_charts	\N	\N	\N	\N	\N
3	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	3	f	f	f	f	t	2	2	manage_user	\N	manage_user	/manage/user	view.manage_user	ic:round-manage-accounts	1	route.manage_user	\N	\N	\N	\N	[{"code": "user:add", "desc": "新增用戶"}, {"code": "user:edit", "desc": "編輯用戶"}, {"code": "user:delete", "desc": "刪除用戶"}, {"code": "user:reset-pwd", "desc": "重置密碼"}, {"code": "user:kick", "desc": "踢除下線"}, {"code": "user:restore", "desc": "復原用戶"}, {"code": "user:unlock", "desc": "解鎖登入"}]
30	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_copy	\N	plugin_copy	/plugin/copy	view.plugin_copy	mdi:clipboard-outline	1	route.plugin_copy	\N	\N	\N	\N	\N
31	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	1	plugin_editor	\N	plugin_editor	/plugin/editor	\N	icon-park-outline:editor	1	route.plugin_editor	\N	\N	\N	\N	\N
32	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	t	\N	\N	f	14	2	plugin_excel	\N	plugin_excel	/plugin/excel	view.plugin_excel	ri:file-excel-2-line	1	route.plugin_excel	\N	\N	\N	\N	\N
33	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	1	plugin_gantt	\N	plugin_gantt	/plugin/gantt	\N	ant-design:bar-chart-outlined	1	route.plugin_gantt	\N	\N	\N	\N	\N
34	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_icon	\N	plugin_icon	/plugin/icon	view.plugin_icon	custom-icon	2	route.plugin_icon	\N	\N	\N	\N	\N
35	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_map	\N	plugin_map	/plugin/map	view.plugin_map	mdi:map	1	route.plugin_map	\N	\N	\N	\N	\N
36	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_pdf	\N	plugin_pdf	/plugin/pdf	view.plugin_pdf	uiw:file-pdf	1	route.plugin_pdf	\N	\N	\N	\N	\N
37	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_pinyin	\N	plugin_pinyin	/plugin/pinyin	view.plugin_pinyin	entypo-social:google-hangouts	1	route.plugin_pinyin	\N	\N	\N	\N	\N
38	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_print	\N	plugin_print	/plugin/print	view.plugin_print	mdi:printer	1	route.plugin_print	\N	\N	\N	\N	\N
39	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_swiper	\N	plugin_swiper	/plugin/swiper	view.plugin_swiper	simple-icons:swiper	1	route.plugin_swiper	\N	\N	\N	\N	\N
4	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	2	\N	\N	\N	\N	t	2	2	manage_role	\N	manage_role	/manage/role	view.manage_role	carbon:user-role	1	route.manage_role	\N	\N	\N	\N	[{"code": "role:add", "desc": "新增角色"}, {"code": "role:edit", "desc": "編輯角色"}, {"code": "role:delete", "desc": "刪除角色"}]
40	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	1	plugin_tables	\N	plugin_tables	/plugin/tables	\N	icon-park-outline:table	1	route.plugin_tables	\N	\N	\N	\N	\N
41	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_typeit	\N	plugin_typeit	/plugin/typeit	view.plugin_typeit	mdi:typewriter	1	route.plugin_typeit	\N	\N	\N	\N	\N
42	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	14	2	plugin_video	\N	plugin_video	/plugin/video	view.plugin_video	mdi:video	1	route.plugin_video	\N	\N	\N	\N	\N
43	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	15	1	pro-naive_form	\N	pro-naive_form	/pro-naive/form	\N	fluent:form-28-regular	1	route.pro-naive_form	\N	\N	\N	\N	\N
44	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	15	1	pro-naive_table	\N	pro-naive_table	/pro-naive/table	\N	mynaui:table	1	route.pro-naive_table	\N	\N	\N	\N	\N
45	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	17	2	exception_403	\N	exception_403	/exception/403	view.403	ic:baseline-block	1	route.exception_403	\N	\N	\N	\N	\N
46	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	17	2	exception_404	\N	exception_404	/exception/404	view.404	ic:baseline-web-asset-off	1	route.exception_404	\N	\N	\N	\N	\N
47	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	17	2	exception_500	\N	exception_500	/exception/500	view.500	ic:baseline-wifi-off	1	route.exception_500	\N	\N	\N	\N	\N
48	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	7	\N	\N	\N	\N	f	18	2	document_antd	\N	document_antd	/document/antd	view.iframe-page	logos:ant-design	1	route.document_antd	https://antdv.com/components/overview-cn	\N	\N	\N	\N
49	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	6	\N	\N	\N	\N	f	18	2	document_naive	\N	document_naive	/document/naive	view.iframe-page	logos:naiveui	1	route.document_naive	https://www.naiveui.com/zh-CN/os-theme/docs/introduction	\N	\N	\N	\N
5	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	4	f	t	f	f	t	2	2	manage_menu	\N	manage_menu	/manage/menu	view.manage_menu	material-symbols:route	1	route.manage_menu	\N	\N	\N	\N	[{"code": "menu:add", "desc": "新增選單"}, {"code": "menu:edit", "desc": "編輯選單"}, {"code": "menu:delete", "desc": "刪除選單"}]
50	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	6	\N	\N	\N	\N	f	18	2	document_pro-naive	\N	document_pro-naive	/document/pro-naive	view.iframe-page	logos:naiveui	1	route.document_pro-naive	https://naive-ui.pro-components.cn/	\N	\N	\N	\N
51	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	7	\N	\N	\N	\N	f	18	2	document_alova	\N	document_alova	/document/alova	view.iframe-page	alova	2	route.document_alova	https://alova.js.org	\N	\N	\N	\N
52	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1	\N	\N	\N	\N	f	18	2	document_project	\N	document_project	/document/project	view.iframe-page	logo	2	route.document_project	https://docs.soybeanjs.cn/zh	\N	\N	\N	\N
53	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	2	\N	\N	\N	\N	f	18	2	document_project-link	\N	document_project-link	/document/project-link	view.iframe-page	logo	2	route.document_project-link	https://docs.soybeanjs.cn/zh	\N	\N	\N	\N
54	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	2	\N	\N	\N	\N	f	18	2	document_video	\N	document_video	/document/video	view.iframe-page	logo	2	route.document_video	https://www.bilibili.com/video/BV1YKdRYXELC	\N	\N	\N	\N
55	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	5	\N	\N	\N	\N	f	18	2	document_unocss	\N	document_unocss	/document/unocss	view.iframe-page	logos:unocss	1	route.document_unocss	https://unocss.dev/	\N	\N	\N	\N
56	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	4	\N	\N	\N	\N	f	18	2	document_vite	\N	document_vite	/document/vite	view.iframe-page	logos:vitejs	1	route.document_vite	https://cn.vitejs.dev/	\N	\N	\N	\N
57	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	3	\N	\N	\N	\N	f	18	2	document_vue	\N	document_vue	/document/vue	view.iframe-page	logos:vue	1	route.document_vue	https://cn.vuejs.org/	\N	\N	\N	\N
58	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	t	\N	\N	\N	f	21	2	function_hide-child_one	\N	function_hide-child_one	/function/hide-child/one	view.function_hide-child_one	material-symbols:filter-list-off	1	route.function_hide-child_one	\N	function_hide-child	\N	\N	\N
59	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	t	\N	\N	\N	f	21	2	function_hide-child_three	\N	function_hide-child_three	/function/hide-child/three	view.function_hide-child_three	\N	\N	route.function_hide-child_three	\N	function_hide-child	\N	\N	\N
6	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	101	t	f	f	f	t	2	2	manage_user-detail	\N	manage_user-detail	/manage/user-detail/:id	view.manage_user-detail		\N	route.manage_user-detail	\N	manage_user	\N	\N	\N
60	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	t	\N	\N	\N	f	21	2	function_hide-child_two	\N	function_hide-child_two	/function/hide-child/two	view.function_hide-child_two	\N	\N	route.function_hide-child_two	\N	function_hide-child	\N	\N	\N
61	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	26	2	multi-menu_first_child	\N	multi-menu_first_child	/multi-menu/first/child	view.multi-menu_first_child	\N	\N	route.multi-menu_first_child	\N	\N	\N	\N	\N
62	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	27	1	multi-menu_second_child	\N	multi-menu_second_child	/multi-menu/second/child	\N	\N	\N	route.multi-menu_second_child	\N	\N	\N	\N	\N
63	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	29	2	plugin_charts_antv	\N	plugin_charts_antv	/plugin/charts/antv	view.plugin_charts_antv	hugeicons:flow-square	1	route.plugin_charts_antv	\N	\N	\N	\N	\N
64	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	29	2	plugin_charts_echarts	\N	plugin_charts_echarts	/plugin/charts/echarts	view.plugin_charts_echarts	simple-icons:apacheecharts	1	route.plugin_charts_echarts	\N	\N	\N	\N	\N
65	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	29	2	plugin_charts_vchart	\N	plugin_charts_vchart	/plugin/charts/vchart	view.plugin_charts_vchart	visactor	2	route.plugin_charts_vchart	\N	\N	\N	\N	\N
66	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	31	2	plugin_editor_markdown	\N	plugin_editor_markdown	/plugin/editor/markdown	view.plugin_editor_markdown	ri:markdown-line	1	route.plugin_editor_markdown	\N	\N	\N	\N	\N
67	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	31	2	plugin_editor_quill	\N	plugin_editor_quill	/plugin/editor/quill	view.plugin_editor_quill	mdi:file-document-edit-outline	1	route.plugin_editor_quill	\N	\N	\N	\N	\N
68	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	33	2	plugin_gantt_dhtmlx	\N	plugin_gantt_dhtmlx	/plugin/gantt/dhtmlx	view.plugin_gantt_dhtmlx	\N	\N	route.plugin_gantt_dhtmlx	\N	\N	\N	\N	\N
69	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	33	2	plugin_gantt_vtable	\N	plugin_gantt_vtable	/plugin/gantt/vtable	view.plugin_gantt_vtable	visactor	2	route.plugin_gantt_vtable	\N	\N	\N	\N	\N
7	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1007	f	f	f	f	f	\N	1	function	\N	function	/function	layout.base	icon-park-outline:all-application	1	route.function	\N	\N	\N	\N	\N
70	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	40	2	plugin_tables_vtable	\N	plugin_tables_vtable	/plugin/tables/vtable	view.plugin_tables_vtable	visactor	2	route.plugin_tables_vtable	\N	\N	\N	\N	\N
71	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	43	2	pro-naive_form_basic	\N	pro-naive_form_basic	/pro-naive/form/basic	view.pro-naive_form_basic	\N	\N	route.pro-naive_form_basic	\N	\N	\N	\N	\N
72	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	43	2	pro-naive_form_query	\N	pro-naive_form_query	/pro-naive/form/query	view.pro-naive_form_query	\N	\N	route.pro-naive_form_query	\N	\N	\N	\N	\N
73	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	43	2	pro-naive_form_step	\N	pro-naive_form_step	/pro-naive/form/step	view.pro-naive_form_step	\N	\N	route.pro-naive_form_step	\N	\N	\N	\N	\N
74	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	44	2	pro-naive_table_remote	\N	pro-naive_table_remote	/pro-naive/table/remote	view.pro-naive_table_remote	\N	\N	route.pro-naive_table_remote	\N	\N	\N	\N	\N
75	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	44	2	pro-naive_table_row-edit	\N	pro-naive_table_row-edit	/pro-naive/table/row-edit	view.pro-naive_table_row-edit	\N	\N	route.pro-naive_table_row-edit	\N	\N	\N	\N	\N
76	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	\N	\N	\N	\N	f	62	2	multi-menu_second_child_home	\N	multi-menu_second_child_home	/multi-menu/second/child/home	view.multi-menu_second_child_home	\N	\N	route.multi-menu_second_child_home	\N	\N	\N	\N	\N
77	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	6	\N	\N	\N	\N	f	2	2	manage_audit	\N	manage_audit	/manage/audit	view.manage_audit	mdi:clipboard-text-search-outline	1	route.manage_audit	\N	\N	\N	\N	\N
78	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	7	\N	\N	\N	\N	f	2	2	manage_ip-rule	\N	manage_ip-rule	/manage/ip-rule	view.manage_ip-rule	mdi:shield-lock-outline	1	route.manage_ip-rule	\N	\N	\N	\N	[{"code": "ipRule:add", "desc": "新增IP規則"}, {"code": "ipRule:edit", "desc": "編輯IP規則"}, {"code": "ipRule:delete", "desc": "刪除IP規則"}, {"code": "ipRule:restore", "desc": "恢復IP規則"}]
8	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	4	\N	\N	\N	\N	f	7	2	function_toggle-auth	\N	function_toggle-auth	/function/toggle-auth	view.function_toggle-auth	ic:round-construction	1	route.function_toggle-auth	\N	\N	\N	\N	[{"code": "B_CODE1", "desc": "超級管理員可見"}, {"code": "B_CODE2", "desc": "管理員可見"}, {"code": "B_CODE3", "desc": "管理員或普通用戶可見"}]
9	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	1	f	f	f	f	t	2	2	manage_system-settings	\N	manage_system-settings	/manage/system-settings	view.manage_system-settings	mdi:cog	1	route.manage_system-settings	\N	\N	\N	\N	\N
\.


--
-- Data for Name: sys_operation_log; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_operation_log (id, created_at, created_by, operation, entity_table, entity_id, payload_before, payload_after, real_ip, peer_ip, x_forwarded_for, ip_confidence, region, trace_id) FROM stdin;
\.


--
-- Data for Name: sys_pwd_custody; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_pwd_custody (user_id, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: sys_role; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_role (id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, status, role_code, role_name, role_memo, role_home, role_desc) FROM stdin;
1	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	R_SUPER	超級管理員	\N	home	\N
2	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	R_ADMIN	管理員	\N	home	\N
3	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	R_USER_COMMON	普通用戶	\N	home	\N
\.


--
-- Data for Name: sys_token; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_token (id, created_at, created_by, status, token_hash, rotation_chain, issued_at, expires_at, used_at) FROM stdin;
\.


--
-- Data for Name: sys_user; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_user (id, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, status, user_gender, user_name, password, nick_name, session_policy, session_id, user_phone, user_email, user_memo) FROM stdin;
1	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	Super	$argon2id$v=19$m=19456,t=2,p=1$+ZAAyoj4MZZ1PExc1Sg6Dg$lo82SGIO9NGwaiefXAmdgf0cHorl5QjrFOm0/wgz0bM	Super	inherit	\N	\N	\N	\N
2	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	Admin	$argon2id$v=19$m=19456,t=2,p=1$+ZAAyoj4MZZ1PExc1Sg6Dg$lo82SGIO9NGwaiefXAmdgf0cHorl5QjrFOm0/wgz0bM	Admin	inherit	\N	\N	\N	\N
3	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	1	\N	User	$argon2id$v=19$m=19456,t=2,p=1$+ZAAyoj4MZZ1PExc1Sg6Dg$lo82SGIO9NGwaiefXAmdgf0cHorl5QjrFOm0/wgz0bM	User01	inherit	\N	\N	\N	\N
\.


--
-- Data for Name: sys_user_email_verify; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_user_email_verify (user_id, created_at, created_by, verified_at, verified_email) FROM stdin;
\.


--
-- Data for Name: sys_user_role; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.sys_user_role (user_id, role_id) FROM stdin;
1	1
2	2
3	3
\.


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: soybean
--

COPY public.system_settings (setting_key, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by, setting_type, setting_value, description) FROM stdin;
ip_captcha_after	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	10	來源節流：來源桶滑動窗內失敗達此數即進驗證碼軟區
ip_max_fails	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	50	來源節流：來源桶滑動窗內失敗達此數即硬鎖
ip_window_minutes	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	15	來源節流：來源維滑動窗長（分鐘）
login_throttle_captcha_after	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	2	登入節流：滑動窗內失敗達此數即進驗證碼軟區
login_throttle_max_fails	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	5	登入節流：滑動窗內失敗達此數即鎖定
login_throttle_window_minutes	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	15	登入節流：滑動窗長（分鐘）＝鎖定的最長存續
password_change_min_interval	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	60	設密冷卻（秒；0＝停用）
password_forbid_username	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	enum:on,off	off	禁止密碼與帳號相同
password_max_length	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	64	密碼最大長度
password_min_length	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	8	密碼最小長度
password_require_digit	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	enum:on,off	off	需含數字
password_require_lowercase	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	enum:on,off	off	需含小寫字母
password_require_special	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	enum:on,off	off	需含特殊符號
password_require_uppercase	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	enum:on,off	off	需含大寫字母
session_idle_timeout	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	number	60	工作階段閒置逾時（分鐘）
single_session_default	2026-08-05 00:00:00+00	\N	\N	\N	\N	\N	enum:on,off	off	全站單一-session 預設
\.


--
-- Name: casbin_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.casbin_rule_id_seq', 163, true);


--
-- Name: session_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.session_event_id_seq', 1, false);


--
-- Name: sys_access_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_access_log_id_seq', 1, false);


--
-- Name: sys_casbin_policy_archive_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_casbin_policy_archive_id_seq', 1, false);


--
-- Name: sys_ip_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_ip_rule_id_seq', 1, false);


--
-- Name: sys_login_attempt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_login_attempt_id_seq', 1, false);


--
-- Name: sys_menu_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_menu_id_seq', 78, true);


--
-- Name: sys_operation_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_operation_log_id_seq', 1, false);


--
-- Name: sys_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_role_id_seq', 3, true);


--
-- Name: sys_token_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_token_id_seq', 1, false);


--
-- Name: sys_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: soybean
--

SELECT pg_catalog.setval('public.sys_user_id_seq', 3, true);


--
-- PostgreSQL database dump complete
--


