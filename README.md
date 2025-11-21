# latex-music-linker

Automatically detect references to music albums and songs in LaTeX newsletters and insert Songlink/Odesli-style smart links.

## Quickstart

```bash
pip install -e .
latex-music-linker examples/newsletter_example.tex examples/newsletter_example_linked.tex
```

This will read the input LaTeX, detect italicised and quoted titles, resolve them via Apple Music + song.link redirector, and write a linked LaTeX file.

## Layout

- `src/latex_music_linker/` – core library
- `docs/` – specification and tool schemas
- `examples/` – example LaTeX inputs
- `tests/` – basic tests
- `scripts/` – helper scripts
