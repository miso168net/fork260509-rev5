---
promoted_to: tools/docs-sync.py 之 jsonl 行界註（行界只認 \n；splitlines 會在 U+2028 等處誤切合法 JSON 字串）
---
- **L-007**｜機械改檔管線以 `splitlines()`＋`"\n".join()` 重組整檔，會把**字面 U+2028／U+2029**
  （Unicode 行／段分隔符）靜默摺成 `\n`——藏在測試樣本字串裡的該類字元就地斷裂成兩行、
  Python 字串未終結（ast SyntaxError），且字元肉眼不可見、報錯行號指向斷點而非成因。
  親歷：B-004 清償對 tools/docs-sync.py 批量插前綴，U+2028 事件測試樣本（`"前 後"`）被摺斷，
  ast 紅在 6164 行。防法：①整檔機械改動用 `str.replace` 或 `split("\n")`、絕不 `splitlines()`
  （它吃 \x1c\x1d\x1e\x85\u2028\u2029 全家）；②動含編碼樣本的檔前先掃 U+2028／U+2029 存量、
  改後以位置上下文縫回；③改完必 `ast.parse` 自證（本例即由此攔下、453 案測試復綠）。

