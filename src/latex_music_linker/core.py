from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .agent import apply_agent_strategy
from .parsing import MusicEntity, apply_links_to_latex, find_candidates
from .resolvers import music_platform_resolver, smart_link_resolver

LOG = logging.getLogger(__name__)


def resolve_entities(entities: list[MusicEntity], *, country: str = "us") -> list[MusicEntity]:
    """Populate platform_url and smartlink_url for each entity in-place."""

    for e in entities:
        # In a full system, e.artist and e.year could be filled in by an AI agent
        result = music_platform_resolver(
            name=e.name,
            artist=e.artist,
            type=e.type,
            year=e.year,
            country=country,
        )
        platform_url = result.get("url")
        e.platform_url = platform_url
        if not platform_url:
            continue

        smart = smart_link_resolver(platform_url)
        e.smartlink_url = smart.get("smartlink_url")

    return entities


def process_latex_string(
    latex: str,
    *,
    agent_name: str = "heuristic",
    agent_options: dict[str, Any] | None = None,
    country: str = "us",
) -> str:
    """End-to-end processing of a LaTeX string: detect, enrich, resolve, and link."""

    entities = find_candidates(latex)
    entities, fallback = apply_agent_strategy(
        latex,
        entities,
        agent_name=agent_name,
        agent_options=agent_options,
    )

    if fallback:
        LOG.warning(
            "Agent '%s' failed or returned no entities (%s); falling back to heuristics.",
            agent_name,
            fallback,
        )

    resolve_entities(entities, country=country)
    return apply_links_to_latex(latex, entities)


def process_latex_file(
    input_path: Path,
    output_path: Path,
    *,
    agent_name: str = "heuristic",
    agent_options: dict[str, Any] | None = None,
    country: str = "us",
) -> None:
    """Read a LaTeX file, process it, and write the linked version."""

    latex = input_path.read_text(encoding="utf-8")
    linked = process_latex_string(
        latex,
        agent_name=agent_name,
        agent_options=agent_options,
        country=country,
    )
    output_path.write_text(linked, encoding="utf-8")
