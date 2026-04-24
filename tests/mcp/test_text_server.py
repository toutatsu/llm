from llm.mcp.server.text_server import (
    word_count,
    truncate_text,
    extract_pattern,
    split_text,
)


def test_word_count_includes_chars_no_space():
    result = word_count("hello world")
    assert result["chars"] == 11
    assert result["chars_no_space"] == 10  # "helloworld"
    assert result["words"] == 2
    assert result["lines"] == 1


def test_truncate_text_truncates():
    result = truncate_text("abcdefghij", 5)
    assert result == "abcd…"
    assert len(result) == 5


def test_truncate_text_no_truncation():
    result = truncate_text("abc", 10)
    assert result == "abc"


def test_truncate_text_custom_suffix():
    result = truncate_text("abcdefghij", 6, suffix="...")
    assert result == "abc..."
    assert len(result) == 6


def test_extract_pattern_finds_digits():
    result = extract_pattern("foo123 bar456", r"\d+")
    assert result == ["123", "456"]


def test_extract_pattern_invalid_regex():
    result = extract_pattern("text", r"[invalid")
    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0].lower() or "エラー" in result[0].lower()


def test_split_text_basic():
    result = split_text("abcdefghij", 4, 0)
    assert result == ["abcd", "efgh", "ij"]


def test_split_text_with_overlap():
    result = split_text("abcdefgh", 4, 2)
    # step = max(1, 4-2) = 2
    # chunks: [0:4]="abcd", [2:6]="cdef", [4:8]="efgh", [6:10]="gh"
    assert result == ["abcd", "cdef", "efgh", "gh"]


def test_split_text_zero_chunk_size():
    result = split_text("abc", 0)
    assert result == ["abc"]


def test_truncate_text_suffix_longer_than_max():
    # max_chars < len(suffix) の場合は suffix だけ返す (切り詰め通知のみ)
    result = truncate_text("abcde", 2, suffix="...")
    assert len(result) <= 5  # 元の文字列より長くなってはいけない


def test_extract_pattern_with_capture_group():
    result = extract_pattern("2025-01-01", r"(\d{4})-(\d{2})-(\d{2})")
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)
