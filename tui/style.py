from prompt_toolkit.styles import Style

DARKCLAUDE_STYLE = Style.from_dict({
    # 構造 (gray)
    "frame.border":       "#5a5a5a",
    "frame.border.sub":   "#3a3a3a",
    "banner":             "#2a2a2a bold",
    "muted":              "#6a6a6a",
    "separator":          "#3a3a3a",

    # 本文
    "output":             "#e0e0e0",
    "assistant":          "#e0e0e0",

    # ツール (teal)
    "tool.call":          "#5a8a98",
    "tool.result":        "#7a7a7a",
    "tool.result.ok":     "#5a8a98",
    "tool.result.error":  "#c84040",

    # ユーザー (白プロンプト + 淡紫テキスト)
    "prompt":             "#ffffff bold",
    "user.text":          "#b095d5",
    "cursor":             "bg:#ffffff #000000",

    # DarkClaude 状態 (muted purple)
    "thinking":           "#7050a0",
    "phase":              "#7050a0",

    # 情報値
    "info.value":         "#5a8a98",
    "info.version":       "#b095d5",
    "status":             "#6a6a6a",
    "status.value":       "#5a8a98",
    "status.mode":        "#b095d5",

    # 入力
    "input":              "bg:#0f0f0f #e0e0e0",
})
