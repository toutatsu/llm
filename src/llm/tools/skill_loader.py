"""スキルローダー。

skills/ ディレクトリ以下の SKILL.md を読んで LangChain ツールを動的に発見・ロードする。
agentskills.io 仕様（https://agentskills.io/specification）に準拠したディレクトリ構成を前提とする。

Directory structure:
    tools/skills/<skill-name>/
        SKILL.md          # フロントマター（name, description）+ 説明
        <module>.py       # *_TOOLS リストを持つ Python モジュール

Usage:
    from llm.tools.skill_loader import load_skills, list_skills

    tools = load_skills()                    # 全スキルのツールを一括取得
    tools = load_skills("datetime-tools")    # 特定スキルのみ
    metadata = list_skills()                 # SKILL.md メタデータ一覧
"""

from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from langchain_core.tools import BaseTool

_SKILLS_DIR = Path(__file__).parent / "skills"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


@dataclass
class SkillMeta:
    name: str
    description: str
    compatibility: str = ""
    skill_dir: Path = field(default_factory=Path)


def _parse_skill_md(skill_dir: Path) -> SkillMeta | None:
    """SKILL.md のフロントマターを読み込んで SkillMeta を返す。"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    text = skill_md.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    data = yaml.safe_load(m.group(1)) or {}
    return SkillMeta(
        name=data.get("name", skill_dir.name),
        description=data.get("description", ""),
        compatibility=data.get("compatibility", ""),
        skill_dir=skill_dir,
    )


def _load_tools_from_skill(skill_dir: Path) -> list[BaseTool]:
    """スキルディレクトリ内の Python モジュールから *_TOOLS リストを収集する。"""
    tools: list[BaseTool] = []
    for py_file in sorted(skill_dir.glob("*.py")):
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr_name in dir(module):
            if attr_name.endswith("_TOOLS"):
                tools.extend(getattr(module, attr_name))
    return tools


def list_skills() -> list[SkillMeta]:
    """skills/ 以下の全スキルメタデータを返す。"""
    metas = []
    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        meta = _parse_skill_md(skill_dir)
        if meta:
            metas.append(meta)
    return metas


def load_skills(skill_name: str | None = None) -> list[BaseTool]:
    """スキルのツールをロードして返す。

    Args:
        skill_name: スキル名を指定すると該当スキルのみ返す。None の場合は全スキルを返す。
    """
    all_tools: list[BaseTool] = []
    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        meta = _parse_skill_md(skill_dir)
        if meta is None:
            continue
        if skill_name is not None and meta.name != skill_name:
            continue
        all_tools.extend(_load_tools_from_skill(skill_dir))
    return all_tools


if __name__ == "__main__":
    print("=== Available Skills ===")
    for meta in list_skills():
        print(f"  [{meta.name}] {meta.description[:60]}...")

    print("\n=== Loaded Tools ===")
    for tool in load_skills():
        print(f"  {tool.name}: {tool.description[:60]}...")
