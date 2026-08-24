---
promoted_to: （佔位：候選晉升位＝CLAUDE.md §2 防呆⑥空間邊界條——「允許檔案清單＝該單元 tasks 涉檔＋review findings 指涉檔」宜補「＋會因本單元改動而連動的釘值測所在檔」；待下一次調 §2 時併入）
---
- **L-052**｜**編排單元的允許檔案清單漏列「連動釘值測」所在檔＝implementer 正確 blocked、整支單元多跑一輪審查 run**：防法前置——寫 ALLOWED 前先機器枚舉「本單元會改動的計數／常數／排序終態」在全樹的釘值測檔（`grep -rn "ROUTES_COUNT\|POLICY_ENDPOINT_COUNT\|末條＝" rust-api/server/`），把會因而轉紅的檔一併納入清單（限「釘值測段」、doc 註明）；implementer 端照防呆⑥「清單外要動＝blocked」是正確行為，代價是主線親修＋新開審查 run。實暴＝006-authz-governance U6（2026-08-23）：ROUTES 44→46 後 `handler/role.rs` 既有測 `policy_endpoints_equals_routes_policy_entries_in_registration_order` 釘 `POLICY_ENDPOINT_COUNT=30`／末條 updateRoleEndpoints 必紅，該檔未在 U6 清單 ⇒ implementer blocked、主線親修三行、審查階段以新 run 重跑（多 1 run、約 2 小時）。盲點＝清單只看「tasks 涉檔」，沒看「被涉檔改動的常數在哪裡被釘」。
