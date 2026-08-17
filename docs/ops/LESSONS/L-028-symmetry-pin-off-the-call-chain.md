---
promoted_to: tools/docs-sync.py 之 _erratum_view 守衛註（確認輪校正＝兩把尺各有各的釘子）
---
- **L-028**｜**「守 A 與守 B 判準必須同尺」這種對稱性論證，兩邊各自需要釘子**——只釘一邊
  而在另一邊的註解寫「對稱釘子＝<那支測試>」，是 vacuous 守門的一種高階變形，比沒寫註解更
  危險（後手照註解判斷會以為已覆蓋）。U5 實暴：`_erratum_view` 的格式跳過守衛註解寫「對稱
  釘子＝`test_erratum_bad_corrected_rejected` 的 `int("1"*40)`」，但該測試走
  `lint_events()`→`_check_event`、**從不呼叫 `_erratum_view`**——視圖那半邊完全裸奔，把
  `isinstance(cor, str) and RE_SHA.fullmatch(cor)` 放寬成 `RE_SHA.fullmatch(str(cor))`
  （＝同檔 feature_close 既有慣例，有人照抄很自然）全套 494 測仍全綠。危害不是 no-op 而是
  **反向**：殘缺值混進視圖後 target 列整列不入 merges，原本該出的 ERROR 被靜默吃掉。
  ★兩個可攜作法：①寫「對稱釘子」註解時，先確認那支測試的**呼叫鏈真的經過本函式**；
  ②挑反例值要挑能**穿透兩把尺差集**的（此處 `3` 無用——`str(3)` 非 40 位 hex、兩把尺都拒；
  只有 `int("1"*40)` 分辨得出來）。
