# latex-music-linker

Automatically detect references to music albums and songs in LaTeX newsletters and insert Songlink/Odesli-style smart links.

## Quickstart

```bash
pip install -e .
latex-music-linker examples/newsletter_example.tex examples/newsletter_example_linked.tex
```

This will read the input LaTeX, detect `\album{...}` and `\song{...}` commands, resolve them via Apple Music + song.link redirector, and write a linked LaTeX file.

### LaTeX setup

Define these commands in your preamble:

```latex
\newcommand{\album}[1]{\textit{#1}} % Italicize album titles
\newcommand{\song}[1]{``#1''} % Quote song titles
```

Then use `\album{Title}` and `\song{Title}` in your document.

### Agent strategies

The parser can be enriched by pluggable agents:

- `heuristic` (default) – uses only local LaTeX cues.
- `llm` – shells out via the [`llm`](https://github.com/simonw/llm) CLI using `docs/prompts/agent_prompt.md` plus the tool schema in `docs/tools/music_resolvers.yaml`.
- `claude-code` – uses the [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) which works with claude.ai consumer subscriptions (no API key required).

Select an agent with `--agent llm` (or set `LATEX_MUSIC_LINKER_AGENT`). Override prompt/tool paths with `--agent-prompt` and `--agent-tools`. If an agent fails or returns nothing, the CLI logs a warning and falls back to the heuristic spans.
Custom backends can register an entry point in the `latex_music_linker.agents` group to appear alongside the built-ins.

## Layout

- `src/latex_music_linker/` – core library
- `docs/` – specification and tool schemas
- `examples/` – example LaTeX inputs
- `tests/` – basic tests
- `scripts/` – helper scripts
