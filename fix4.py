content = open("tui/textual_app.py", encoding="utf-8").read()

# 1. 入力欄フォーカス枠を消す
content = content.replace(
    "    CSS = \"\"\"\n    Screen {\n        background: #0a0a0a;\n        layout: vertical;\n    }\n    \"\"\"",
    "    CSS = \"\"\"\n    Screen {\n        background: #0a0a0a;\n        layout: vertical;\n    }\n    Input {\n        border: none;\n        outline: none;\n        background: #0a0a0a;\n        color: #e0e0e0;\n        padding: 0 1;\n    }\n    Input:focus {\n        border: none;\n        outline: none;\n    }\n    Input.-focused {\n        border: none;\n    }\n    \"\"\""
)

# 2. highlight=False に変更 (自動ハイライトで...が別色になる原因)
content = content.replace(
    "yield ChatLog(id=\"chat-log\", markup=True, highlight=True)",
    "yield ChatLog(id=\"chat-log\", markup=True, highlight=False)"
)

# 3. scrollbar を非表示
content = content.replace(
    "        scrollbar-gutter: stable;\n        scrollbar-color: #3a3a3a #0a0a0a;",
    "        scrollbar-size: 0 0;"
)

open("tui/textual_app.py", "w", encoding="utf-8").write(content)
print("done")
