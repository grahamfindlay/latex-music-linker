from __future__ import annotations

from pathlib import Path
from typing import List

from .parsing import find_candidates, apply_links_to_latex, MusicEntity
from .resolvers import music_platform_resolver, smart_link_resolver


def resolve_entities(entities: List[MusicEntity]) -> List[MusicEntity]:
    """Populate platform_url and smartlink_url for each entity in-place."""

    for e in entities:
        # In a full system, e.artist and e.year could be filled in by an AI agent
        result = music_platform_resolver(
            name=e.name,
            artist=e.artist,
            type=e.type,
            year=e.year,
        )
        platform_url = result.get("url")
        e.platform_url = platform_url
        if not platform_url:
            continue

        smart = smart_link_resolver(platform_url)
        e.smartlink_url = smart.get("smartlink_url")

    return entities


def process_latex_string(latex: str) -> str:
    """End-to-end processing of a LaTeX string: detect, resolve, and link."""

    entities = find_candidates(latex)
    resolve_entities(entities)
    return apply_links_to_latex(latex, entities)


def process_latex_file(input_path: Path, output_path: Path) -> None:
    """Read a LaTeX file, process it, and write the linked version."""

    latex = input_path.read_text(encoding="utf-8")
    linked = process_latex_string(latex)
    output_path.write_text(linked, encoding="utf-8")
