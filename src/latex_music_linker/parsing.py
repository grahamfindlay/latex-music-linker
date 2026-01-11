from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class MusicEntity:
    """Represents a music reference found in the LaTeX text.

    In a full system, artist and year are expected to be filled in by an AI agent
    before resolution. This module focuses on span detection.
    """

    name: str
    artist: str
    type: str  # "album" or "track"
    year: int | None
    latex_text: str
    start_index: int
    end_index: int
    platform_url: str | None = None
    smartlink_url: str | None = None


ALBUM_PATTERN = re.compile(r"\\album\{([^}]*)\}")
SONG_PATTERN = re.compile(r"\\song\{([^}]*)\}")
# Pattern to detect if a position is inside a link command argument
LINK_WRAPPER_PATTERN = re.compile(r"\\(?:href|gref)\{[^}]*\}\{$")
# Pattern to detect failed song.link hrefs that need retry
NOTFOUND_HREF_PATTERN = re.compile(
    r"\\href\{https://song\.link/not-found\}\{(\\(?:song|album)\{[^}]*\})\}"
)


def _is_inside_link(latex: str, match_start: int) -> bool:
    """Check if position is inside a \\href{...}{...} or \\gref{...}{...} command."""
    prefix = latex[:match_start]
    return bool(LINK_WRAPPER_PATTERN.search(prefix))


def find_candidates(latex: str) -> list[MusicEntity]:
    """Heuristically extract album/track candidates from LaTeX.

    - \\album{Title} -> album
    - \\song{Title} -> track

    Artist inference is NOT handled here; in a production system an AI agent
    would infer the artist from context and populate the MusicEntity objects.
    """

    entities: list[MusicEntity] = []

    # \album{...} = album
    for m in ALBUM_PATTERN.finditer(latex):
        if _is_inside_link(latex, m.start()):
            continue
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

    # \song{...} = track
    for m in SONG_PATTERN.finditer(latex):
        if _is_inside_link(latex, m.start()):
            continue
        title = m.group(1)
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


def find_failed_links(latex: str) -> list[MusicEntity]:
    """Find music entities wrapped in failed song.link/not-found hrefs.

    Returns MusicEntity objects where:
    - start_index/end_index span the entire \\href{...}{...} wrapper
    - latex_text is just the inner \\song{} or \\album{} command
    - name/type are extracted from the inner command
    """

    entities: list[MusicEntity] = []

    for m in NOTFOUND_HREF_PATTERN.finditer(latex):
        inner_cmd = m.group(1)  # e.g., \song{Future Legend}

        # Extract type and name from the inner command
        album_match = ALBUM_PATTERN.match(inner_cmd)
        song_match = SONG_PATTERN.match(inner_cmd)

        if album_match:
            name = album_match.group(1).strip()
            entity_type = "album"
        elif song_match:
            name = song_match.group(1).strip()
            entity_type = "track"
        else:
            continue

        if not name:
            continue

        entities.append(
            MusicEntity(
                name=name,
                artist="UNKNOWN",
                type=entity_type,
                year=None,
                latex_text=inner_cmd,
                start_index=m.start(),
                end_index=m.end(),
            )
        )

    entities.sort(key=lambda e: e.start_index)
    return entities


def apply_links_to_latex(latex: str, entities: list[MusicEntity]) -> str:
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
        pieces.append(latex[last_index : e.start_index])

        wrapped = e.latex_text
        # Avoid double-wrapping text that is already hyperlinked
        if "\\href" not in e.latex_text:
            wrapped = f"\\href{{{e.smartlink_url}}}{{{e.latex_text}}}"

        pieces.append(wrapped)
        last_index = e.end_index

    pieces.append(latex[last_index:])
    return "".join(pieces)
