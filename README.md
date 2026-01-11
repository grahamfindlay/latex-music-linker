# latex-music-linker

Automatically detect references to music albums and songs in LaTeX newsletters and insert Songlink/Odesli-style smart links.

## Quickstart

### LaTeX setup

Define these commands in your preamble:

```latex
\newcommand{\album}[1]{\textit{#1}} % Italicize album titles
\newcommand{\song}[1]{``#1''} % Quote song titles
```

Then use `\album{Title}` and `\song{Title}` in your document.

### How it works

The `latex-music-linker` tool:

1. Scans your LaTeX document for `\album{...}` and `\song{...}` commands.
2. Uses either a heuristic parser or an LLM-based agent (recommended) to infer context like artist names from surrounding text, that can be used to improve search accuracy.
3. For each musical item (e.g. song, album), calls the Apple Music API to get an Apple Music link. Why Apple Music? Simply because the Apple Music API and search functions are free, and much better in my hands than e.g. Spotify's. Plus, I use Apple Music myself, so it's easier to check correctness.
4. Passes the Apple Music link to the Songlink/Odesli API to get a universal redirector link.
5. Inserts the resolved link back into the LaTeX output, wrapping the `\album{...}` and `\song{...}` commands in `\href{...}{...}` commands.

### Agent-free invocation

```bash
uv run latex-music-linker examples/newsletter_example.tex examples/newsletter_example_linked.tex
```

This is equivalent to using the `heuristic` agent.

### Agent strategies

The parser can be enriched by pluggable agents:

- `heuristic` (default) – uses only local LaTeX cues.
- `llm` – shells out via the [`llm`](https://github.com/simonw/llm) CLI using `docs/prompts/agent_prompt.md` plus the tool schema in `docs/tools/music_resolvers.yaml`. You can use a local model, but it is easiest to obtain an API key and use a hosted model like Gemini 3.0 Flash (cheap, fast, good). See below (and `llm` docs) for setup instructions.
- `claude-code` (experimental) – uses the [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) which works with claude.ai consumer subscriptions (no API key required).

Select an agent with `--agent llm` (or set `LATEX_MUSIC_LINKER_AGENT`). Select a model with `--llm-model` (or set `LATEX_MUSIC_LINKER_LLM_MODEL`). Override prompt/tool paths with `--agent-prompt` and `--agent-tools`.

If an agent fails or returns nothing, the CLI logs a warning and falls back to the heuristic spans.

Custom backends can register an entry point in the `latex_music_linker.agents` group to appear alongside the built-ins.

### Example usage with Gemini 3.0 Flash

For example, to use Gemini 3.0 Flash, first setup the `llm` CLI:

```bash
uv tool install llm
uv run llm install gemini
uv run llm keys set gemini
# Paste Gemini API key here
```

then invoke with:

```bash
uv run latex-music-linker \
    examples/newsletter_example.tex \
    examples/newsletter_example_linked.tex \
    --agent llm \
    --llm-model gemini-3-flash-preview
```

or

```bash
export LATEX_MUSIC_LINKER_AGENT=llm
export LATEX_MUSIC_LINKER_LLM_MODEL=gemini-3-flash-preview
uv run latex-music-linker \
    examples/newsletter_example.tex \
    examples/newsletter_example_linked.tex
```

## Layout

- `src/latex_music_linker/` – core library
- `docs/` – specification and tool schemas
- `examples/` – example LaTeX inputs
- `tests/` – basic tests
- `scripts/` – helper scripts
