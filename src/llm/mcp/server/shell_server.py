"""シェルコマンド実行ツールを提供するMCPサーバ。

Tools:
  - run_shell : シェルコマンドを実行して標準出力・標準エラーを返す
"""

import subprocess
import sys

from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("shell-server")

_DEFAULT_WORKDIR = "/home/llm/data/agent_filesystem/"
_MAX_OUTPUT_CHARS = 3000


@mcp.tool()
@tool_error_handler
def run_shell(command: str, working_dir: str = _DEFAULT_WORKDIR) -> str:
    """シェルコマンドを実行し、標準出力と標準エラーを返します。

    Args:
        command: 実行するシェルコマンド。
        working_dir: 作業ディレクトリ。デフォルトは /home/llm/data/agent_filesystem/（エージェントのサンドボックス領域）。
    """
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=working_dir,
    )
    output = result.stdout
    if result.stderr:
        output += f"\n[stderr]\n{result.stderr}"
    output = output or "(no output)"
    if len(output) > _MAX_OUTPUT_CHARS:
        output = output[:_MAX_OUTPUT_CHARS] + f"\n... (truncated, {len(output)} chars total)"
    return output


def main() -> None:
    print("shell-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
