content = open("tui/textual_app.py", encoding="utf-8").read()
old = "from clients import get_client\n        self.client = get_client(\n            client_type=config.get(\"client\", \"openai\"),\n            model=self.model,\n            base_url=self.base_url,\n        )"
new = "from clients import get_client\n        self.client = get_client(config)"
content = content.replace(old, new)
open("tui/textual_app.py", "w", encoding="utf-8").write(content)
print("done:", "get_client(config)" in content)
