## Plan: Pluggable AI Agent Integration

Add an agent-aware enrichment layer between LaTeX parsing and URL resolution, expose configuration so any AI backend (including `llm`) can populate artist/type data, and provide prompts/tool schemas to guide automated linking runs end-to-end.

### Steps
1. Define `AgentStrategy` interface and configuration (e.g., `src/latex_music_linker/agent.py`, `pyproject.toml` entrypoints) so users can select “heuristic”, “llm”, or future backends.
2. Create prompt/schema assets using the hybrid approach: narrative instructions in Markdown (`docs/prompts/agent_prompt.md`) plus machine-readable tool specs in YAML/JSON (`docs/tools/music_resolvers.yaml`).
3. Implement `LLMStrategy` that shells out through `llm` CLI with configurable model, prompt path, and tool manifest, returning enriched `MusicEntity` data.
4. Update `process_latex_string` and CLI (`src/latex_music_linker/cli.py`) to accept `--agent <name>`/env vars, invoking the chosen strategy before `resolve_entities`.
5. Add tests (`tests/test_agent_integration.py`) with stub strategies ensuring the single-shot agent attempt plus heuristic fallback behaves correctly and verifying linked output for `examples/newsletter_example.tex`.

### Further Considerations
1. Standardize on the `llm` CLI subprocess for agent calls (document installation, configuration, and how availability is checked).
2. Store prompts via the hybrid model (Markdown instructions + YAML/JSON schemas) and version each file explicitly so agent responses are traceable to prompt revisions.
3. Failure policy: attempt the agent once; on error or empty result, fall back to the existing heuristic parser and emit a clear log/CLI message documenting the fallback.
