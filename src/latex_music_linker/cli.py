from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import process_latex_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Automatically link music references in LaTeX using smart links."
    )
    parser.add_argument("input", help="Input LaTeX file")
    parser.add_argument("output", help="Output LaTeX file")
    parser.add_argument(
        "--country",
        default="us",
        help="Country code for platform resolution (currently unused, placeholder)",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    process_latex_file(input_path, output_path)
    print(f"Wrote linked LaTeX to {output_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
