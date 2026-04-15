"""FastMCP Client を使ったMCPサーバ接続のサンプル。

各サーバのインスタンスに直接接続し、ツール・リソース・プロンプトを確認する。
"""

import asyncio

from fastmcp import Client

from llm.mcp.server.filesystem_server import mcp as filesystem_mcp
from llm.mcp.server.math_server import mcp as math_mcp
from llm.mcp.server.search_server import mcp as search_mcp
from llm.mcp.server.shell_server import mcp as shell_mcp
from llm.mcp.server.text_server import mcp as text_mcp


async def demo_math_server() -> None:
    print("=== math-server ===")
    async with Client(math_mcp) as client:
        tools = await client.list_tools()
        print(f"Tools: {[t.name for t in tools]}")

        result = await client.call_tool("add", {"a": 3, "b": 5})
        print(f"add(3, 5) = {result.data}")

        result = await client.call_tool("calculate", {"expression": "math.sqrt(144)"})
        print(f"calculate('math.sqrt(144)') = {result.data}")


async def demo_text_server() -> None:
    print("\n=== text-server ===")
    async with Client(text_mcp) as client:
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        print(f"Tools: {[t.name for t in tools]}")
        print(f"Prompts: {[p.name for p in prompts]}")

        result = await client.call_tool("word_count", {"text": "Hello world\nfoo bar"})
        print(f"word_count('Hello world\\nfoo bar') = {result.data}")


async def demo_filesystem_server() -> None:
    print("\n=== filesystem-server ===")
    async with Client(filesystem_mcp) as client:
        resources = await client.list_resources()
        tools = await client.list_tools()
        print(f"Resources: {[str(r.uri) for r in resources]}")
        print(f"Tools: {[t.name for t in tools]}")


async def demo_search_server() -> None:
    print("\n=== search-server ===")
    async with Client(search_mcp) as client:
        tools = await client.list_tools()
        print(f"Tools: {[t.name for t in tools]}")


async def demo_shell_server() -> None:
    print("\n=== shell-server ===")
    async with Client(shell_mcp) as client:
        tools = await client.list_tools()
        print(f"Tools: {[t.name for t in tools]}")

        result = await client.call_tool("run_shell", {"command": "echo 'hello from shell-server'"})
        print(f"run_shell('echo ...') = {result.data}")


async def main() -> None:
    await demo_math_server()
    await demo_text_server()
    await demo_filesystem_server()
    await demo_search_server()
    await demo_shell_server()


if __name__ == "__main__":
    asyncio.run(main())
