---
promoted_to: specs/005-role-menu-crud/quickstart.md §2（手動 smoke 節尾警語一句、2026-08-22）
---
- **L-050**｜**對 dev stack 以 seed 帳號真登入做手動 smoke 後緊接全量測試＝throttle 家族暫態紅**：防法前置——①手動 smoke（真登入）一律排在全量測試**之後**；②非排不可時，smoke 後先等節流窗期過、或清指定 redis 鍵再跑；③暫態紅的歸因紀律＝當輪立刻截獲失敗名單（rerun 前先存 log），過期自癒後只剩假說。實暴＝005 U13（2026-08-22）：quickstart §2 手動 smoke 兩次 Super 真登入在 redis 留下節流／帳號窗殘態（TTL 界定），緊接的第一輪全量 server lib 6 支暫態紅；DB 側殘列已清且 schema-gate 三閘綠（與 DB 無關），第二、三輪連兩輪 546/546 全綠＝TTL 過期自癒。★失敗名單當輪未截獲、redis 歸因屬假說級（與症狀、TTL 時序、DB 排除證一致），故防法③同為本條教訓的一部分。
