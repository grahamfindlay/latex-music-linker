# LaTeX Music Linker Agent Prompt

Version: 0.1.0  
Audience: Any AI agent connected via the `llm` CLI  
Purpose: Enrich heuristically-detected music entities with artist/type data before URL resolution.

## Task

You receive two inputs:

1. `latex` – the raw LaTeX string for a newsletter item.  
2. `candidates` – heuristic spans already extracted from the LaTeX. Each item includes `candidate_id`, `name`, `artist`, `type`, `year`, `latex_text`, `start_index`, and `end_index`.

Use the LaTeX context to refine each candidate:

- Confirm whether the span is a `track` or `album`.  
- Infer the primary `artist` name.  
- Keep `start_index`, `end_index`, and `latex_text` unchanged so downstream rewriting stays aligned.

## Output

Return **only JSON** with an `entities` array. Each entity **must** include the `candidate_id` from the input so the runtime can merge results safely:

```json
{
  "entities": [
    {
      "candidate_id": 0,
      "name": "God Does Like Ugly",
      "artist": "JID",
      "type": "album",
      "year": 2025,
      "latex_text": "\\textit{God Does Like Ugly}",
      "start_index": 10,
      "end_index": 36
    }
  ]
}
```

If you cannot improve a candidate, return it unchanged but still include the `candidate_id`. Do not invent new spans or shift offsets.

## Tools

You may optionally call the provided tool schema (see YAML attachment) to reason about URL resolution steps, but do **not** perform the HTTP calls yourself. Only populate metadata (`name`, `artist`, `type`, `year`).
