# Specification Document: Automated Linking of Music References in LaTeX Newsletters

**Version:** 2.0
**Audience:** Any AI agent or automated system
**Purpose:** Provide a complete, model-agnostic description of the task, motivations, constraints, and the solution pipeline.

---

## 1. Overview

This document describes a system for automatically detecting references to music albums and songs inside a LaTeX document (specifically, a music newsletter), resolving those references to canonical streaming-platform URLs, and inserting platform-agnostic smart links (Songlink/Odesli links) into the LaTeX source.

The system:

1. Detects `\album{...}` and `\song{...}` LaTeX commands in the document.
2. Uses a pluggable agent strategy to enrich entities with artist names, years, and other metadata from context.
3. Resolves each entity to a platform URL (Apple Music) via the iTunes Search API.
4. Converts platform URLs to universal smart links using the song.link redirector.
5. Rewrites the LaTeX by wrapping detected commands in `\href{...}{...}` hyperlinks.

---

## 2. Motivation and Constraints

### 2.1 Motivations

- LaTeX newsletters frequently reference albums/songs without linking to them.
- Manual insertion of smart links is time-consuming, error-prone, and involves repeated lookup.
- Automated linking improves:
  - Reader experience
  - Consistency
  - Author productivity

### 2.2 Constraints

- The system must work **without requiring the Songlink/Odesli API**, which has strict rate limits.
- Instead, it relies on:
  - Public music platform search APIs (Apple's iTunes Search API).
  - A lightweight redirect-based link-expansion method (song.link redirector).
- The system uses explicit `\album{...}` and `\song{...}` commands for detection (not prose analysis).
- The system must preserve all original LaTeX formatting except where hyperlinks are added.
- The system must not double-link text already inside `\href{...}{...}` or `\gref{...}{...}`.

---

## 3. LaTeX Commands

The system expects authors to use two custom LaTeX commands to mark music references:

### 3.1 Command Definitions

Authors should define these commands in their document preamble:

```latex
\newcommand{\album}[1]{\textit{#1}}    % Italicize album titles
\newcommand{\song}[1]{``#1''}           % Quote song titles
```

### 3.2 Usage

```latex
\album{God Does Like Ugly}              % Detected as album
\song{Gz}                               % Detected as track
```

### 3.3 Detection Patterns

The parser uses regex patterns to detect these commands:

- Albums: `\\album\{([^}]*)\}`
- Songs: `\\song\{([^}]*)\}`

### 3.4 Already-Linked Detection

The system skips entities already wrapped in hyperlinks:

```latex
\href{https://example.com}{\album{Title}}  % Skipped (not re-wrapped)
\gref{https://example.com}{\album{Title}}  % Skipped (gref also detected)
```

---

## 4. Example Input and Expected Output

### 4.1 Example Input

```latex
\documentclass{article}
\newcommand{\album}[1]{\textit{#1}}
\newcommand{\song}[1]{``#1''}

\begin{document}
\item JID's \album{God Does Like Ugly} (2025).
So great was my anticipation for this album...
I liked the \href{https://youtu.be/GhOUB6IGs6Y}{freestyle} that announced the album...
If you live near any major roads, it is possible that you have already heard \song{Gz}...
\end{document}
```

### 4.2 Example Output (With Links)

```latex
\documentclass{article}
\newcommand{\album}[1]{\textit{#1}}
\newcommand{\song}[1]{``#1''}

\begin{document}
\item JID's \href{https://album.link/i/1832251919}{\album{God Does Like Ugly}} (2025).
So great was my anticipation for this album...
I liked the \href{https://youtu.be/GhOUB6IGs6Y}{freestyle} that announced the album...
If you live near any major roads, it is possible that you have already heard
\href{https://song.link/i/1812517950}{\song{Gz}}...
\end{document}
```

---

## 5. Architecture Overview

The system uses a **four-step pipeline**:

```text
LaTeX Input
    │
    ▼
[Step 1] find_candidates()
         Extract \album{} and \song{} spans using regex
    │
    ▼
[Step 2] apply_agent_strategy()
         Enrich entities with artist/year from document context
    │
    ▼
[Step 3] resolve_entities()
         ├→ music_platform_resolver() → iTunes Search API
         │                            → Returns Apple Music URL
         └→ smart_link_resolver()     → song.link redirector
                                       → Returns universal smart link
    │
    ▼
[Step 4] apply_links_to_latex()
         Wrap entities in \href{...}{...}
    │
    ▼
Linked LaTeX Output
```

---

## 6. Agent Strategy System

The system uses a pluggable agent architecture for enriching entities with metadata (artist, year) inferred from document context.

### 6.1 Available Strategies

| Strategy       | Description                                    | Requirements           |
| -------------- | ---------------------------------------------- | ---------------------- |
| `heuristic`    | Returns candidates unchanged (no enrichment)   | None                   |
| `llm`          | Uses external LLM via `llm` CLI                | `llm` CLI installed    |
| `claude-code`  | Uses Claude via `claude` CLI                   | `claude` CLI installed |

### 6.2 Agent Behavior

Agents receive:

- The full LaTeX document
- A list of candidate entities with positions

Agents return enriched entities with:

- `name`: Title of album/track (may be refined)
- `artist`: Primary artist (inferred from context)
- `type`: "album" or "track"
- `year`: Release year (inferred from context)

### 6.3 Agent Response Format

Agents return JSON:

```json
{
  "entities": [
    {
      "candidate_id": 0,
      "name": "God Does Like Ugly",
      "artist": "JID",
      "type": "album",
      "year": 2025,
      "latex_text": "\\album{God Does Like Ugly}",
      "start_index": 10,
      "end_index": 36
    }
  ]
}
```

### 6.4 Fallback Behavior

If an agent fails (network error, parsing error, etc.), the system falls back to the heuristic strategy and logs a warning.

---

## 7. Music Resolution Tools

### 7.1 Platform Search Resolver

Queries the Apple iTunes Search API to find matching music entities.

**Inputs:**

- `name`: Title of album/track
- `artist`: Primary artist
- `type`: "album" or "track"
- `year`: Optional release year
- `country`: Two-letter country code (default: "us")

**Behavior:**

1. Queries iTunes Search API with term = `"{name} {artist}"`
2. Filters results by entity type
3. Scores results using matching algorithm:
   - Title exact match: +0.6
   - Title partial match: +0.3
   - Artist match: +0.3
   - Year exact: +0.2
   - Year ±1: +0.1
4. Returns best match with confidence score

**Output:**

```python
{
    "platform": "apple_music",
    "url": "https://music.apple.com/us/album/god-does-like-ugly/1832251919",
    "confidence": 0.9,
    "raw_response": {...}
}
```

### 7.2 Smart Link Resolver

Converts platform URLs to universal smart links using the song.link redirector.

**Inputs:**

- `platform_url`: Apple Music URL

**Behavior:**

1. Constructs redirector URL: `https://song.link/<platform_url>`
2. Makes HTTP GET request with `allow_redirects=False`
3. Extracts final smart link from `Location` header

**Output:**

```python
{
    "smartlink_url": "https://album.link/i/1832251919",
    "redirector_url": "https://song.link/https://music.apple.com/..."
}
```

---

## 8. Command-Line Interface

### 8.1 Basic Usage

```bash
latex-music-linker <input.tex> <output.tex> [OPTIONS]
```

### 8.2 Options

| Option           | Description                                    | Default       |
| ---------------- | ---------------------------------------------- | ------------- |
| `--country`      | Country code for iTunes Search                 | `us`          |
| `--agent`        | Agent strategy (heuristic, llm, claude-code)   | `heuristic`   |
| `--llm-model`    | Model for LLM agent                            | `gpt-4o-mini` |
| `--agent-prompt` | Path to custom prompt file                     | Built-in      |
| `--agent-tools`  | Path to custom tool schema file                | Built-in      |

### 8.3 Environment Variables

| Variable                           | Description            |
| ---------------------------------- | ---------------------- |
| `LATEX_MUSIC_LINKER_AGENT`         | Default agent strategy |
| `LATEX_MUSIC_LINKER_LLM_MODEL`     | Default LLM model      |
| `LATEX_MUSIC_LINKER_AGENT_PROMPT`  | Default prompt path    |
| `LATEX_MUSIC_LINKER_AGENT_TOOLS`   | Default tools path     |

### 8.4 Examples

```bash
# Basic usage with heuristic agent
latex-music-linker input.tex output.tex

# Using Claude Code agent
latex-music-linker input.tex output.tex --agent claude-code

# Using LLM agent with specific model
latex-music-linker input.tex output.tex --agent llm --llm-model gpt-4-turbo

# Using UK iTunes store
latex-music-linker input.tex output.tex --country gb
```

---

## 9. Programmatic API

### 9.1 String Processing

```python
from latex_music_linker import process_latex_string

linked_latex = process_latex_string(
    latex_string,
    agent_name="claude-code",
    agent_options={"prompt_path": "/path/to/prompt.md"},
    country="us"
)
```

### 9.2 File Processing

```python
from pathlib import Path
from latex_music_linker import process_latex_file

process_latex_file(
    Path("input.tex"),
    Path("output.tex"),
    agent_name="llm",
    agent_options={"model": "gpt-4o"},
    country="gb"
)
```

---

## 10. Error Handling Guidelines

### 10.1 Multiple Plausible Matches

The scoring algorithm selects the best match using:

- Exact title match preferred
- Artist match required (or very close)
- Year proximity if available

### 10.2 No Match Found

- Skip linking for that entity
- Return original LaTeX unchanged for that span
- Log a warning (do not fail the whole document)

### 10.3 Network Failures

- Retry up to 3 times with exponential backoff
- If all retries fail, skip that entity

### 10.4 Agent Failures

- Fall back to heuristic strategy
- Log warning with error details

### 10.5 Already-Linked Content

- Detect existing `\href{...}` and `\gref{...}` wrappers
- Do not modify those spans

---

## 11. Data Structures

### 11.1 MusicEntity

```python
@dataclass
class MusicEntity:
    name: str                          # Title of album/track
    artist: str                        # Primary artist
    type: str                          # "album" or "track"
    year: Optional[int]                # Release year
    latex_text: str                    # Original LaTeX (e.g., "\\album{Title}")
    start_index: int                   # Start position in LaTeX string
    end_index: int                     # End position in LaTeX string
    platform_url: Optional[str]        # Resolved Apple Music URL
    smartlink_url: Optional[str]       # Final smart link URL
```

---

## 12. Extensibility

### 12.1 Custom Agent Strategies

New agent strategies can be registered via setuptools entry points:

```toml
[project.entry-points."latex_music_linker.agents"]
my_agent = "my_package.agent:MyAgentStrategy"
```

### 12.2 Future Platform Support

The architecture supports adding:

- Spotify search (in addition to Apple Music)
- Bandcamp album/track resolution
- YouTube Music metadata
- Alternative smart-link providers

### 12.3 Format Extensions

The parsing approach could be extended to:

- Support additional LaTeX commands
- Extract from Markdown or HTML
- Custom regex patterns

---

## 13. Summary of System Behavior

The system:

1. **Detects** `\album{...}` and `\song{...}` commands in LaTeX documents.
2. **Enriches** entities with artist/year metadata using pluggable agent strategies.
3. **Resolves** each entity to an Apple Music URL via iTunes Search API.
4. **Converts** platform URLs to universal smart links via song.link redirector.
5. **Rewrites** the LaTeX document with `\href{...}{...}` wrappers.
6. **Preserves** all original formatting and avoids double-linking.
