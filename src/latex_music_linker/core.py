from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .agent import apply_agent_strategy
from .parsing import (
    MusicEntity,
    apply_links_to_latex,
    find_candidates,
    find_failed_links,
)
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


def process_latex_string_retry(
    latex: str,
    *,
    agent_name: str = "heuristic",
    agent_options: dict[str, Any] | None = None,
    country: str = "us",
) -> str:
    """Re-process failed song.link/not-found links in a LaTeX string.

    Finds entities wrapped in \\href{https://song.link/not-found}{...},
    strips the broken wrapper, re-resolves them, and applies new links.
    Entities that still fail are left unwrapped (just \\song{} or \\album{}).
    """

    failed_entities = find_failed_links(latex)
    if not failed_entities:
        LOG.info("No failed song.link/not-found links found to retry.")
        return latex

    LOG.info("Found %d failed link(s) to retry.", len(failed_entities))

    # Enrich with agent if requested
    failed_entities, fallback = apply_agent_strategy(
        latex,
        failed_entities,
        agent_name=agent_name,
        agent_options=agent_options,
    )

    if fallback:
        LOG.warning(
            "Agent '%s' failed or returned no entities (%s); falling back to heuristics.",
            agent_name,
            fallback,
        )

    # Re-resolve each entity
    for e in failed_entities:
        LOG.debug("Retrying: %s (%s)", e.name, e.type)
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
            LOG.warning("  -> iTunes lookup failed for '%s'", e.name)
            continue

        smart = smart_link_resolver(platform_url)
        e.smartlink_url = smart.get("smartlink_url")
        if e.smartlink_url:
            LOG.info("  -> Resolved '%s' to %s", e.name, e.smartlink_url)
        else:
            LOG.warning("  -> song.link still failed for '%s': %s", e.name, smart.get("error", "unknown"))

    # Rewrite the LaTeX: replace failed hrefs with either new links or unwrapped commands
    pieces = []
    last_index = 0

    for e in failed_entities:
        pieces.append(latex[last_index:e.start_index])

        if e.smartlink_url:
            # Successfully resolved - wrap with new link
            pieces.append(f"\\href{{{e.smartlink_url}}}{{{e.latex_text}}}")
        else:
            # Still failed - leave unwrapped so it can be retried later
            pieces.append(e.latex_text)

        last_index = e.end_index

    pieces.append(latex[last_index:])
    return "".join(pieces)


def process_latex_file(
    input_path: Path,
    output_path: Path,
    *,
    agent_name: str = "heuristic",
    agent_options: dict[str, Any] | None = None,
    country: str = "us",
    retry: bool = False,
) -> None:
    """Read a LaTeX file, process it, and write the linked version.

    If retry=True, only re-process failed song.link/not-found links.
    """

    latex = input_path.read_text(encoding="utf-8")

    if retry:
        linked = process_latex_string_retry(
            latex,
            agent_name=agent_name,
            agent_options=agent_options,
            country=country,
        )
    else:
        linked = process_latex_string(
            latex,
            agent_name=agent_name,
            agent_options=agent_options,
            country=country,
        )

    output_path.write_text(linked, encoding="utf-8")
