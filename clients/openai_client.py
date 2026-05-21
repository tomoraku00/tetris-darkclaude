"""OpenAI 互換 API (llama-server) 経由のクライアント。"""
import json
import requests


class OpenAIClient:
    """llama-server の OpenAI 互換エンドポイントに HTTP で接続。

    Note:
        thinking 抑制は llama-server 起動時に環境変数経由で行う想定。
        この think パラメタは無視される。
    """

    def __init__(self, base_url="http://localhost:8080", model=""):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, model, messages, tools, think=False):
        normalized = self._normalize_messages(messages)

        body = {
            "model": model or self.model or "default",
            "messages": normalized,
        }
        if tools:
            body["tools"] = tools
        # Qwen3.6 公式推奨サンプリングパラメータ
        body["temperature"] = 1.0
        body["top_p"] = 0.95
        body["top_k"] = 20
        body["presence_penalty"] = 1.5

        try:
            r = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=body,
                timeout=600,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            return {"message": {
                "role": "assistant",
                "content": f"ERROR: HTTP request failed: {type(e).__name__}: {e}",
            }}

        data = r.json()
        msg = data["choices"][0]["message"]

        # tool_calls の arguments は JSON 文字列で来るので dict 化
        # (dispatch が **args で展開するため)
        for tc in msg.get("tool_calls") or []:
            args = tc.get("function", {}).get("arguments")
            if isinstance(args, str):
                try:
                    tc["function"]["arguments"] = json.loads(args)
                except json.JSONDecodeError:
                    tc["function"]["arguments"] = {}

        return {"message": msg}

    def _normalize_messages(self, messages):
        """tool 結果メッセージを Ollama 形式 → OpenAI 形式に変換。

        Ollama: {"role": "tool", "content": ..., "name": "read_file"}
        OpenAI: {"role": "tool", "content": ..., "tool_call_id": "..."}
        """
        result = []
        last_tool_call_ids = {}  # name -> id

        for msg in messages:
            role = msg.get("role")

            if role == "assistant" and msg.get("tool_calls"):
                # tool_call_id をマッピング、arguments を JSON 文字列に戻す
                new_msg = dict(msg)
                new_tcs = []
                for tc in msg["tool_calls"]:
                    name = tc.get("function", {}).get("name", "")
                    tc_id = tc.get("id", "")
                    if name and tc_id:
                        last_tool_call_ids[name] = tc_id

                    new_tc = dict(tc)
                    new_tc["function"] = dict(tc.get("function", {}))
                    args = new_tc["function"].get("arguments")
                    if not isinstance(args, str):
                        new_tc["function"]["arguments"] = json.dumps(
                            args or {}, ensure_ascii=False
                        )
                    new_tcs.append(new_tc)
                new_msg["tool_calls"] = new_tcs
                result.append(new_msg)

            elif role == "tool":
                # name -> tool_call_id 変換
                new_msg = dict(msg)
                name = msg.get("name", "")
                if name and name in last_tool_call_ids:
                    new_msg["tool_call_id"] = last_tool_call_ids[name]
                result.append(new_msg)

            else:
                result.append(msg)

        return result

    def list_models(self):
        if self.model:
            return [self.model]
        try:
            r = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if r.ok:
                return [m["id"] for m in r.json().get("data", [])]
        except Exception:
            pass
        return []
