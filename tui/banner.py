"""ASCII banner + DarkClaude mascot (v0.9-beta)"""
import os
from prompt_toolkit.formatted_text import FormattedText

BANNER = r""" ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
 ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
 ██║  ██║███████║██████╔╝█████╔╝ ██║     ██║     ███████║██║   ██║██║  ██║█████╗
 ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
 ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝"""

MASCOT = r"""   █        █
   ██      ██
  ██▀██████▀██
    ██▄ ████ ▄██
  ████████████████
  ████████████
   █ █    █ █   """

GAP = "  "  # banner と mascot の間隔

VERSION = "v0.9-beta"


def render_banner(config: dict) -> FormattedText:
    """banner + mascot を横並びにした FormattedText を返す。

    レイアウト (A 配置 = mascot の角先端が banner より 1 行上に突出):
      行 0:   [banner 幅の空白] + GAP + MASCOT 行 0  (角先端のみ)
      行 1-6: BANNER 行 i + GAP + MASCOT 行 i+1
    """
    banner_lines = BANNER.split("\n")
    mascot_lines = MASCOT.split("\n")

    assert len(banner_lines) == 6, f"banner must be 6 lines, got {len(banner_lines)}"
    assert len(mascot_lines) == 7, f"mascot must be 7 lines, got {len(mascot_lines)}"

    banner_width = max(len(line) for line in banner_lines)

    parts: list[tuple[str, str]] = []

    # 行 0: banner なし、mascot の最初の行 (角の先端)
    parts.append(("", " " * banner_width))
    parts.append(("", GAP))
    parts.append(("class:mascot", mascot_lines[0]))
    parts.append(("", "\n"))

    # 行 1-6: banner + mascot
    for i in range(6):
        parts.append(("class:banner", banner_lines[i]))
        parts.append(("", GAP))
        parts.append(("class:mascot", mascot_lines[i + 1]))
        parts.append(("", "\n"))

    # 情報行
    model = config.get("model", "?")
    base_url = config.get("base_url", "http://localhost:8080")
    phase = "A6 stabilization"
    cwd = os.getcwd()

    parts.append(("", "\n"))
    parts += [
        ("class:muted", " version    "), ("class:info.version", VERSION), ("", "\n"),
        ("class:muted", " model      "), ("class:info.value", model), ("", "\n"),
        ("class:muted", " server     "), ("class:info.value", base_url), ("", "\n"),
        ("class:muted", " cwd        "), ("class:output", cwd), ("", "\n"),
        ("class:muted", " phase      "), ("class:phase", phase), ("", "\n"),
        ("", "\n"),
        ("class:muted", " Type /help for commands.  Ctrl+C to exit."), ("", "\n"),
        ("", "\n"),
    ]

    return FormattedText(parts)
