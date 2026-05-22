import re
content = open("src/App.css", encoding="utf-8").read()
for m in re.finditer(r"\.msg-[^}]+}", content):
    print(m.group())
    print()
