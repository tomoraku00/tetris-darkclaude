"""DarkClaude TUI 配色定義 (v0.9-beta 最終確定版)"""
from prompt_toolkit.styles import Style

DARKCLAUDE_STYLE = Style.from_dict({
    # === 構造 (gray) ===
    "frame.border":         "#5a5a5a",
    "frame.border.sub":     "#3a3a3a",
    "banner":               "#2a2a2a bold",
    "mascot":               "#2a2a2a bold",    # banner と同色 (一体化)
    "muted":                "#6a6a6a",
    "separator":            "#3a3a3a",

    # === 本文 (白/グレー基本) ===
    "output":               "#e0e0e0",
    "assistant":            "#e0e0e0",
    "inline_code":          "#e0e0e0",
    "code_block":           "bg:#1a1a1a #e0e0e0",
    "code_block.border":    "#3a3a3a",
    "user.line":            "bg:#1a1a1a",      # ユーザー入力 echo 行の薄背景

    # === ユーザー ===
    "prompt":               "#ffffff bold",
    "user.text":            "#7a7a7a",          # 灰色 echo (本家準拠)
    "cursor":               "bg:#ffffff #000000",

    # === ツール (teal、本家の青/緑両方を吸収) ===
    "tool.call":            "#5a8a98",
    "tool.result":          "#7a7a7a",
    "tool.result.ok":       "#5a8a98",
    "tool.result.error":    "#a85050",          # 赤抑え
    "tool.success.bullet":  "#5a8a98",

    # === セクションヘッダー (薄紫、本家青の置換) ===
    "section.header":       "#b095d5 bold",
    "section.subhead":      "#7a7a7a",
    "section.divider":      "#b095d5",          # 上下ラインも薄紫

    # === 承認ダイアログ ===
    "option.cursor":        "#ffffff bold",
    "option.selected":      "#ffffff bold",
    "option.unselected":    "#7a7a7a",
    "option.emphasis":      "#ffffff bold",
    "option.hint":          "#5a5a5a",

    # === diff (赤抑え、緑→teal) ===
    "diff.removed":         "bg:#3a1010 #ffffff",
    "diff.added":           "bg:#0a3a3f #ffffff",
    "diff.line_number":     "#5a5a5a",
    "diff.marker.minus":    "#a85050",
    "diff.marker.plus":     "#5a8a98",
    "diff.summary":         "#7a7a7a",
    "diff.context":         "#e0e0e0",

    # === 状態 (薄紫) ===
    "thinking":             "#b095d5",
    "phase":                "#b095d5",
    "recap":                "#7a7a7a italic",

    # === 情報値 ===
    "info.value":           "#5a8a98",
    "info.version":         "#b095d5",
    "status":               "#6a6a6a",
    "status.value":         "#5a8a98",
    "status.mode":          "#b095d5",

    # === 入力 (背景指定削除、透明) ===
    "input":                "#e0e0e0",
})
