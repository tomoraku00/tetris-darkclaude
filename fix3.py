content = open("tui/textual_app.py", encoding="utf-8").read()

old = '''    async def _ai_turn(self, user_input: str) -> None:
        log = self.query_one(ChatLog)
        status = self.query_one(StatusBar)
        status.update_status("推論中...")
        self.messages.append({"role": "user", "content": user_input})
        try:
            response = await asyncio.to_thread(
                self.client.chat,
                self.model,
                self.messages,
                [],  # tools なし (Phase B-1 はシンプルチャットから)
            )
            msg = response.get("message", {})
            content = msg.get("content", "")
            self.messages.append(msg)
            log.write(f"[bold yellow]Assistant:[/] {content}")
        except Exception as e:
            log.write(f"[bold red]ERROR:[/] {e}")
        finally:
            status.update_status("VRAM free:'''

new = '''    async def _ai_turn(self, user_input: str) -> None:
        from tools.registry import TOOL_SCHEMAS, dispatch
        log = self.query_one(ChatLog)
        status = self.query_one(StatusBar)
        self.messages.append({"role": "user", "content": user_input})
        tool_call_count = 0
        try:
            while True:
                status.update_status(f"推論中... (tool calls: {tool_call_count})")
                response = await asyncio.to_thread(
                    self.client.chat,
                    self.model,
                    self.messages,
                    TOOL_SCHEMAS,
                )
                msg = response.get("message", {})
                self.messages.append(msg)
                tool_calls = msg.get("tool_calls") or []
                if not tool_calls:
                    content = msg.get("content", "")
                    log.write(f"[bold yellow]Assistant:[/] {content}")
                    break
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    args = tc.get("function", {}).get("arguments", {})
                    log.write(f"[dim]  > {name}({', '.join(f'{k}={repr(v)[:40]}' for k,v in args.items())})[/]")
                    result = await asyncio.to_thread(dispatch, name, args)
                    self.messages.append({"role": "tool", "content": result, "name": name})
                    tool_call_count += 1
        except Exception as e:
            log.write(f"[bold red]ERROR:[/] {e}")
        finally:
            status.update_status("VRAM free:'''

if old in content:
    content = content.replace(old, new)
    open("tui/textual_app.py", "w", encoding="utf-8").write(content)
    print("done")
else:
    print("NOT FOUND - checking...")
    idx = content.find("async def _ai_turn")
    print(repr(content[idx:idx+200]))
