"""
LoRA adapter を Ollama 用に変換し、Modelfile でカスタムモデル化する。
本実装は v0.9。
"""


def merge_lora_to_gguf(adapter_path: str, base_model: str, out_path: str) -> None:
    """LoRA adapter をベースモデルにマージして GGUF 形式で出力する。"""
    raise NotImplementedError("v0.9 で実装")


def create_ollama_modelfile(gguf_path: str, model_name: str) -> str:
    """Ollama Modelfile を生成し、`ollama create` を実行する。"""
    raise NotImplementedError("v0.9 で実装")


if __name__ == "__main__":
    raise NotImplementedError("deploy.py は v0.9 で実装します。v0.8 はスケルトンのみ。")
