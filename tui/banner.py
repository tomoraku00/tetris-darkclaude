import os

BANNER = r""" ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
 ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
 ██║  ██║███████║██████╔╝█████╔╝ ██║     ██║     ███████║██║   ██║██║  ██║█████╗
 ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
 ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝"""

VERSION = "v0.9-alpha"


def render_banner(config: dict) -> str:
    model = config.get("model", "?")
    base_url = config.get("base_url", "http://localhost:8080")
    phase = "A6 stabilization"
    cwd = os.getcwd()

    lines = [
        BANNER,
        "",
        f" version    {VERSION}",
        f" model      {model}",
        f" server     {base_url}",
        f" cwd        {cwd}",
        f" phase      {phase}",
        "",
        " Type /help for commands.  Ctrl+C to exit.",
        "",
    ]
    return "\n".join(lines)
