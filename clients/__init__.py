"""LLM クライアント抽象化レイヤー。

config.json の "client" フィールドに応じて適切なクライアントを生成する。
- "ollama": OllamaClient (既存挙動)
- "openai": OpenAIClient (llama-server 経由)
"""
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient


def get_client(config: dict):
    client_type = config.get("client", "ollama")
    if client_type == "ollama":
        return OllamaClient()
    elif client_type == "openai":
        return OpenAIClient(
            base_url=config.get("base_url", "http://localhost:8080"),
            model=config.get("model", ""),
        )
    else:
        raise ValueError(f"Unknown client type: {client_type}")
