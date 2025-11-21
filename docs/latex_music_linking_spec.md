# Specification Document: Automated Linking of Music References in LaTeX Newsletters

**Version:** 1.0  
**Audience:** Any AI agent or automated system  
**Purpose:** Provide a complete, model-agnostic description of the task, motivations, constraints, and the proposed solution pipeline.

---

## 1. Overview

This document describes a system for automatically detecting references to music albums and songs inside a LaTeX document (specifically, a music newsletter), resolving those references to canonical streaming-platform URLs, and inserting platform-agnostic smart links (Songlink/Odesli links) into the LaTeX source.

The AI agent receiving this document should be able to:

1. Understand the structure of typical music mentions in prose.
2. Infer which textual spans correspond to **albums**, **songs**, and **artists**, even when not explicitly labeled.
3. Use external tools (provided separately) to:
   - Resolve the inferred entity to a specific platform URL (e.g., Apple Music).
   - Convert that platform URL into a universal smart link using a redirect resolver.
4. Rewrite the LaTeX input by inserting `\href{…}{…}` in the correct positions.
5. Output a complete, modified LaTeX document.

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
- Instead, it should rely on:
  - Public music platform search APIs (e.g., Apple's iTunes Search API).
  - A lightweight redirect-based link-expansion method (“song.link redirector”).
- The system should reliably differentiate **songs** from **albums** using contextual language cues.
- The system must not require prior annotation in the LaTeX.
- The system must preserve all original LaTeX formatting except where hyperlinks are added.

---

## 3. Types of Entities to Identify

The agent must identify the following categories.

### 3.1 Artists

Usually proper nouns, often preceding possessive forms:

- `JID's`, `Prince`, `The Smile`, `Earl Sweatshirt and Alchemist`

### 3.2 Albums

Cues for album references include:

- Appearing in `\textit{…}` markup  
- Following patterns like:  
  - `Artist's <Title> (Year)`  
  - `<Title> (Year)` when context indicates album
- Local context words: “album”, “LP”, “record”, “project”

### 3.3 Songs / Tracks

Cues for track references:

- Appearing in quotation marks: `"Gz"` or `` ``Gz'' ``  
- Following words like: “track”, “song”, “single”  
- Being referenced as part of an album discussion

### 3.4 Mixed or Ambiguous Cases

When ambiguous:

- Prefer album classification for italicized titles with years.
- Prefer song classification for quoted titles.
- Use semantic context (“this album”, “this song”, etc.).

---

## 4. Example Input and Expected Output

### 4.1 Example Input (Partial LaTeX Snippet)

```latex
\item JID's \textit{God Does Like Ugly} (2025). 
So great was my anticipation for this album...
I liked the \href{https://youtu.be/GhOUB6IGs6Y}{freestyle} that announced the album...
If you live near any major roads, it is possible that you have already heard ``Gz''...
```

### 4.2 Example Output (With Links)

```latex
\item JID's \href{https://album.link/i/1832251919}{\textit{God Does Like Ugly}} (2025).
So great was my anticipation for this album...
I liked the \href{https://youtu.be/GhOUB6IGs6Y}{freestyle} that announced the album...
If you live near any major roads, it is possible that you have already heard 
\href{https://song.link/i/1812517950}{``Gz''}...
```

---

## 5. Architecture Overview

To accomplish the task, the system uses **three components**:

1. **LaTeX Content Analyzer** (AI agent step)  
2. **Music Metadata Resolver** (external tool or script)  
3. **LaTeX Rewriter** (AI agent step)

Each component is described below.

---

## 6. Step-by-Step Plan

### Step 1 — Parse the LaTeX File

The agent should extract:

1. Plain text segments  
2. Formatting markup (`\textit`, quotes, `\href`)  
3. Positions of potential candidates for linking  

No linking should occur inside existing `\href{…}{…}` blocks.

### Step 2 — Identify Candidate Music Entities

The agent should examine:

- Italicized text → strong album candidate  
- Quoted text → strong song candidate  
- Nearby artist names  
- Explicit contextual cues (“album”, “song”, “track”)  
- Syntactic patterns (`Artist’s Title (Year)`)

The agent should produce a structured list such as:

```json
[
  {
    "name": "God Does Like Ugly",
    "type": "album",
    "artist": "JID",
    "year": 2025,
    "latex_text": "\\textit{God Does Like Ugly}",
    "occurrence_index": 17
  },
  {
    "name": "Gz",
    "type": "track",
    "artist": "JID",
    "year": 2025,
    "latex_text": "``Gz''",
    "occurrence_index": 92
  }
]
```

### Step 3 — Resolve Each Entity to a Canonical Music-Platform URL

The system does **not** use the Odesli API.

Instead, the agent must call or trigger the following independent tools (to be provided separately).

#### Tool A – Platform Search Resolver

**Inputs:**

- `name`  
- `artist`  
- `type` (album / track)  
- Optional `year`  

**Expected behavior:**

- Queries a public search API (e.g., Apple iTunes Search API).  
- Filters results for best match.  
- Returns a canonical Apple Music URL.

Example output:

```text
https://music.apple.com/us/album/god-does-like-ugly/1832251919
```

#### Tool B – Smart Link Resolver

**Inputs:**

- Platform URL

**Expected behavior:**

- Constructs a redirect URL:

  ```text
  https://song.link/<platform-url>
  ```

- Sends an HTTP GET with redirects disabled.  
- Extracts the `Location` header.  
- Returns the final smart link:

  ```text
  https://album.link/i/1832251919
  ```

### Step 4 — Insert Links into the LaTeX

For albums:

```latex
\href{SMARTLINK}{\textit{Album Title}}
```

For songs:

```latex
\href{SMARTLINK}{``Song Title''}
```

The agent must:

- Modify only the intended target spans.  
- Preserve all original formatting.  
- Avoid double-linking text already inside `\href`.

### Step 5 — Produce Final LaTeX Output

Return the entire LaTeX document with all music entities linked.

---

## 7. Tools Required (External to the Agent)

The AI agent does **not** need to implement these tools; it only needs to call them or request their outputs.

### Tool A: Music Platform Resolver

- Function-level interface or web service  
- Inputs: `{name, artist, type, year?}`  
- Output: platform URL (string)

### Tool B: Smart Link Resolver

- Function-level interface or web service  
- Inputs: `{platform_url}`  
- Output: `{smartlink_url}`

Both should be callable in sequence.

---

## 8. Error Handling Guidelines

### If Multiple Plausible Matches

Select the best match using:

- Exact title match preferred  
- Artist match required (or very close)  
- Year proximity if available  

### If No Match Found

- Skip linking.  
- Return original LaTeX unchanged for that span.  
- Log a warning rather than failing the whole document.

### If Linking Conflicts with Existing `\href`

Do not modify that span.

---

## 9. Extensibility

The system may later support:

- Spotify search instead of (or in addition to) Apple Music  
- Bandcamp album or track resolution  
- YouTube Music metadata  
- Extraction of music entities from Markdown or HTML  
- Replacement with other smart-link providers  

All improvements should remain compatible with the plan described above.

---

## 10. Summary of Expected Agent Behavior

The agent must:

1. **Understand** prose context and infer whether a referenced title is:
   - an album  
   - a song/track  
   - an artist  
2. **Extract** these references from LaTeX cleanly.  
3. **Request** external tools to resolve each one.  
4. **Generate** correct `\href{…}{…}` wrappers.  
5. **Rewrite** the full LaTeX document.  
6. **Preserve** formatting and leave unrelated content untouched.
