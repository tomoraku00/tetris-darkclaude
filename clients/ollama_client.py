"""Ollama (ollama-python) 経由のクライアント。既存挙動の保持用。"""
import ollama


def _to_dict(obj):
    """Pydantic オブジェクトを dict 化する。"""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    try:
        return vars(obj)
    except TypeError:
        return {"raw_repr": str(obj)}


class OllamaClient:
    """ollama.chat() をラップして既存挙動を維持。"""

    _think_fallback_warned = False

    def chat(self, model, messages, tools, think=False):
        if think:
            try:
                response = ollama.chat(
                    model=model,
                    messages=messages,
                    tools=tools,
                    think=False,
                )
            except TypeError:
                if not OllamaClient._think_fallback_warned:
                    print("[warn] ollama-python does not support 'think' param, "
                          "falling back to /no_think prompt only")
                    OllamaClient._think_fallback_warned = True
                response = ollama.chat(
                    model=model,
                    messages=messages,
                    tools=tools,
                )
        else:
            response = ollama.chat(
                model=model,
                messages=messages,
                tools=tools,
            )

        # Pydantic オブジェクト → dict 化 (後続処理が dict 前提のため)
        msg = _to_dict(response["message"])
        return {"message": msg}

    def list_models(self):
        try:
            resp = ollama.list()
            if hasattr(resp, "models"):
                return [m.model for m in resp.models if m.model]
            return [m.get("model", m.get("name", "")) for m in resp.get("models", [])]
        except Exception:
            return []
