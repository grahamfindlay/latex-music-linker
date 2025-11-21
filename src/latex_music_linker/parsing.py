from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import re


@dataclass
class MusicEntity:
    """Represents a music reference found in the LaTeX text.

    In a full system, artist and year are expected to be filled in by an AI agent
    before resolution. This module focuses on span detection.
    """

    name: str
    artist: str
    type: str  # "album" or "track"
    year: Optional[int]
    latex_text: str
    start_index: int
    end_index: int
    platform_url: Optional[str] = None
    smartlink_url: Optional[str] = None


ITALIC_PATTERN = re.compile(r"\\textit\{([^}]*)\}")
QUOTE_PATTERN = re.compile(r"``([^']*)''|\"([^\"]+)\"")


def find_candidates(latex: str) -> List[MusicEntity]:
    """Heuristically extract album/track candidates from LaTeX.

    - \textit{Title} -> assume album
    - ``Title'' or "Title" -> assume track

    Artist inference is NOT handled here; in a production system an AI agent
    would infer the artist from context and populate the MusicEntity objects.
    """

    entities: List[MusicEntity] = []

    # Italic = album
    for m in ITALIC_PATTERN.finditer(latex):
        title = m.group(1).strip()
        if not title:
            continue
        entities.append(
            MusicEntity(
                name=title,
                artist="UNKNOWN",
                type="album",
                year=None,
                latex_text=m.group(0),
                start_index=m.start(),
                end_index=m.end(),
            )
        )

    # Quoted = track
    for m in QUOTE_PATTERN.finditer(latex):
        title = m.group(1) or m.group(2)
        if not title:
            continue
        entities.append(
            MusicEntity(
                name=title.strip(),
                artist="UNKNOWN",
                type="track",
                year=None,
                latex_text=m.group(0),
                start_index=m.start(),
                end_index=m.end(),
            )
        )

    entities.sort(key=lambda e: e.start_index)
    return entities


def apply_links_to_latex(latex: str, entities: List[MusicEntity]) -> str:
    """Rewrite LaTeX by wrapping detected spans in \\href{...}{...}.

    Assumes entity spans do not overlap and are sorted by start_index.
    Only entities that already have smartlink_url set are applied.
    """

    entities = [e for e in entities if e.smartlink_url]
    if not entities:
        return latex

    pieces = []
    last_index = 0

    for e in entities:
        pieces.append(latex[last_index:e.start_index])

        wrapped = e.latex_text
        # crude guard: skip if already in a \href region
        context_slice = latex[max(0, last_index - 50) : e.end_index + 50]
        if "\\href" not in context_slice:
            wrapped = f"\\href{{{e.smartlink_url}}}{{{e.latex_text}}}"

        pieces.append(wrapped)
        last_index = e.end_index

    pieces.append(latex[last_index:])
    return "".join(pieces)
