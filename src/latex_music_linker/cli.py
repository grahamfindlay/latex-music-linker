from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .core import process_latex_file


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    default_agent = os.environ.get("LATEX_MUSIC_LINKER_AGENT", "heuristic")
    parser = argparse.ArgumentParser(
        description="Automatically link music references in LaTeX using smart links."
    )
    parser.add_argument("input", help="Input LaTeX file")
    parser.add_argument("output", help="Output LaTeX file")
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

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

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


if __name__ == "__main__":
    main(sys.argv[1:])
