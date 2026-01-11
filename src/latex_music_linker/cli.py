from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent import default_prompt_path
from .core import process_latex_file
from .parsing import find_candidates


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    if args.dry_run:
        _run_dry_run(input_path)
        return

    if args.output is None:
        raise SystemExit("Output file is required unless using --dry-run")

    output_path = Path(args.output)

    agent_options: dict[str, Any] = {}
    if args.agent == "llm":
        agent_options["model"] = args.llm_model
        if args.agent_prompt:
            agent_options["prompt_path"] = args.agent_prompt
        if args.agent_tools:
            agent_options["tools_path"] = args.agent_tools

    process_latex_file(
        input_path,
        output_path,
        agent_name=args.agent,
        agent_options=agent_options,
        country=args.country,
    )
    print(f"Wrote linked LaTeX to {output_path}")


def _run_dry_run(input_path: Path) -> None:
    """Print the JSON payload that would be sent to an agent, then exit."""
    latex = input_path.read_text(encoding="utf-8")
    candidates = find_candidates(latex)

    payload = {
        "latex": latex,
        "candidates": [
            {"candidate_id": idx, **asdict(c)} for idx, c in enumerate(candidates)
        ],
        "instruction_version": default_prompt_path().name,
    }
    print(json.dumps(payload, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    default_agent = os.environ.get("LATEX_MUSIC_LINKER_AGENT", "heuristic")

    parser = argparse.ArgumentParser(
        description="Automatically link music references in LaTeX using smart links."
    )
    parser.add_argument("input", help="Input LaTeX file")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output LaTeX file (required unless using --dry-run)",
    )
    parser.add_argument(
        "--country",
        default="us",
        help="Country code for platform resolution.",
    )
    parser.add_argument(
        "--agent",
        default=default_agent,
        help="Agent backend to use (heuristic, llm, or entrypoint name). "
        "Defaults to LATEX_MUSIC_LINKER_AGENT or 'heuristic'.",
    )
    parser.add_argument(
        "--llm-model",
        default=os.environ.get("LATEX_MUSIC_LINKER_LLM_MODEL", "gpt-4o-mini"),
        help="Model name for the llm agent (ignored for other agents).",
    )
    parser.add_argument(
        "--agent-prompt",
        default=os.environ.get("LATEX_MUSIC_LINKER_AGENT_PROMPT"),
        help="Path to the Markdown prompt file for the llm agent.",
    )
    parser.add_argument(
        "--agent-tools",
        default=os.environ.get("LATEX_MUSIC_LINKER_AGENT_TOOLS"),
        help="Path to the YAML/JSON tool schema used by the llm agent.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the JSON payload that would be sent to the agent, then exit.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose DEBUG logging.",
    )

    return parser


if __name__ == "__main__":
    main(sys.argv[1:])
