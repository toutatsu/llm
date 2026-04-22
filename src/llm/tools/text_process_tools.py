"""テキスト処理ツール。

Pydantic スキーマ入力・複数ツールをまとめるパターンのサンプル。
文字数カウント・テキスト切り詰め・正規表現抽出を提供する。
"""

import re

from langchain_core.tools import tool


@tool
def count_chars(text: str) -> dict:
    """テキストの文字数・単語数・行数をカウントする。

    Args:
        text: カウント対象のテキスト。
    """
    return {
        "chars": len(text),
        "chars_no_space": len(text.replace(" ", "").replace("\n", "")),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
    }


@tool
def truncate_text(text: str, max_chars: int, suffix: str = "…") -> str:
    """テキストを指定文字数で切り詰める。

    Args:
        text: 切り詰め対象のテキスト。
        max_chars: 最大文字数。
        suffix: 切り詰め時に末尾に付加する文字列（デフォルト: "…"）。
    """
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


@tool
def extract_pattern(text: str, pattern: str, max_matches: int = 20) -> list[str]:
    """テキストから正規表現パターンに一致する部分をすべて抽出する。

    Args:
        text: 検索対象のテキスト。
        pattern: Python 正規表現パターン。
        max_matches: 最大返却件数（デフォルト: 20）。
    """
    try:
        matches = re.findall(pattern, text)
        return matches[:max_matches]
    except re.error as e:
        return [f"Error: 正規表現が不正です: {e}"]


@tool
def split_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """テキストを指定文字数のチャンクに分割する。RAG のチャンキング用途を想定。

    Args:
        text: 分割対象のテキスト。
        chunk_size: 1チャンクあたりの最大文字数。
        overlap: チャンク間のオーバーラップ文字数（デフォルト: 0）。
    """
    if chunk_size <= 0:
        return [text]
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(text), step):
        chunks.append(text[i : i + chunk_size])
    return chunks


TEXT_PROCESS_TOOLS = [count_chars, truncate_text, extract_pattern, split_text]


if __name__ == "__main__":
    sample = "LangChain は LLM アプリ構築フレームワークです。LangGraph でマルチエージェントを実装できます。"
    print(count_chars.invoke({"text": sample}))
    print(truncate_text.invoke({"text": sample, "max_chars": 20}))
    print(extract_pattern.invoke({"text": sample, "pattern": r"Lang\w+"}))
    print(split_text.invoke({"text": sample, "chunk_size": 20, "overlap": 5}))
