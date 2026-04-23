# ログ処理設計

**日付**: 2026-04-23  
**スコープ**: エージェント実行・ツール呼び出し・MCP接続のログ記録

---

## 背景と目的

現状、ツール呼び出しのログは `wrap_tool_call` ミドルウェアが `Console(stderr=True)` で Rich パネルをターミナルに表示するのみで、ファイルには記録されない。エージェントの実行開始・終了・所要時間や MCP 接続の詳細も記録されていない。

本設計では `llm.logger` の loguru ロガーに統合し、ターミナルとログファイルの両方に適切なレベルで記録されるようにする。

---

## ログレベル方針

| イベント | レベル | 出力先 |
|---|---|---|
| エージェント開始・完了 | INFO | ターミナル + `llm-20-INFO.log` |
| ツール呼び出し名 | INFO | ターミナル + `llm-20-INFO.log` |
| ツール引数・結果の詳細 | DEBUG | `llm-10-DEBUG.log` |
| MCP サーバ接続・ツール読み込み | DEBUG | `llm-10-DEBUG.log` |
| エラー | ERROR | ターミナル + `llm-40-ERROR.log` |

---

## セクション1: ツール呼び出しログ (`wrap_tool_call`)

### 変更内容

`monitor_tool` 関数をファクトリ関数 `make_monitor_tool(verbose: bool = False)` に変更する。

```python
def make_monitor_tool(verbose: bool = False):
    @wrap_tool_call
    def monitor_tool(request, handler):
        name = request.tool_call['name']
        args_json = json.dumps(request.tool_call["args"], ensure_ascii=False, indent=2)

        logger.info(f"Tool call: {name}")
        logger.debug(f"Args:\n{args_json}")

        if verbose:
            _console.print(Panel(
                Syntax(args_json, "json", theme="monokai"),
                title=f"[bold cyan]Tool Call:[/bold cyan] [yellow]{name}[/yellow]",
                border_style="cyan",
            ))

        try:
            result = handler(request)
            content = result.content if isinstance(result, ToolMessage) else str(result)
            logger.info(f"Tool result: {name}")
            logger.debug(f"Content:\n{content}")

            if verbose:
                _console.print(Panel(
                    Text(str(content)),
                    title="[bold green]Tool Result[/bold green]",
                    border_style="green",
                ))
            return result
        except Exception as e:
            logger.error(f"Tool error [{name}]: {e}")
            if verbose:
                _console.print(Panel(
                    Text(str(e), style="red"),
                    title="[bold red]Tool Error[/bold red]",
                    border_style="red",
                ))
            raise

    return monitor_tool
```

### `deep_agent.py` 側の変更

`make_monitor_tool` を常時ミドルウェアに追加する。`verbose` はパネル表示の制御のみに変わる。

```python
# 変更前
middleware = [_build_skills_middleware()]
if verbose:
    middleware.append(monitor_tool)

# 変更後
middleware = [_build_skills_middleware(), make_monitor_tool(verbose=verbose)]
```

---

## セクション2: MCP接続ログ (`mcp/client/_utils.py`)

`open_mcp_tools` の各サーバ接続ループに `logger.debug` を追加する。

```python
for server_name in server_config:
    logger.debug(f"MCPサーバ '{server_name}' に接続中...")
    session = await stack.enter_async_context(client.session(server_name))
    tools = await load_mcp_tools(session)
    tool_names = [t.name for t in tools]
    logger.debug(f"MCPサーバ '{server_name}': {len(tools)} ツールを読み込み → {tool_names}")
    all_tools.extend(tools)
```

---

## セクション3: エージェント実行ログ

### `LoggedRunnable` ラッパー

`deep_agent.py` 内に直接定義し、サブエージェントの実行を計測する。

```python
import time

class LoggedRunnable:
    def __init__(self, runnable, name: str):
        self._runnable = runnable
        self._name = name

    async def ainvoke(self, input, config=None, **kwargs):
        logger.info(f"サブエージェント開始: {self._name}")
        start = time.monotonic()
        try:
            result = await self._runnable.ainvoke(input, config=config, **kwargs)
            elapsed = time.monotonic() - start
            logger.info(f"サブエージェント完了: {self._name} ({elapsed:.2f}s)")
            return result
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(f"サブエージェントエラー: {self._name} ({elapsed:.2f}s): {e}")
            raise

    def __getattr__(self, name):
        return getattr(self._runnable, name)
```

### `CompiledSubAgent` への適用

```python
CompiledSubAgent(
    name="research_agent",
    description="情報収集を行うエージェント",
    runnable=LoggedRunnable(create_research_agent(research_tools), "research_agent"),
),
CompiledSubAgent(
    name="vlm_agent",
    description="...",
    runnable=LoggedRunnable(create_vlm_agent(vlm_tools, skill_tools=vlm_skill_tools), "vlm_agent"),
),
CompiledSubAgent(
    name="coding_agent",
    description="...",
    runnable=LoggedRunnable(create_coding_agent(coding_tools), "coding_agent"),
),
```

### deep_agent 起動ログ

`yield deep_agent` の直前に起動情報を記録する。

```python
logger.info(f"deep_agent 起動: {len(deep_agent_tools)} ツール利用可能 → {[t.name for t in deep_agent_tools]}")
yield deep_agent
```

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/llm/agent/middleware/wrap_tool_call/__init__.py` | `monitor_tool` → `make_monitor_tool(verbose)` に変更、`logger` を使用 |
| `src/llm/agent/deep_agent.py` | `make_monitor_tool` を常時追加、`LoggedRunnable` を定義・適用、起動ログ追加 |
| `src/llm/mcp/client/_utils.py` | `open_mcp_tools` に接続ログを追加 |
