"""CLI entry point for the SumTablets pipeline.

Usage:
    uv run python -m src.scripts.run              # Run all steps
    uv run python -m src.scripts.run --from 3      # Resume from step 3
"""

import argparse

from sumtablets.pipeline import run

parser = argparse.ArgumentParser(description="Run the SumTablets pipeline")
parser.add_argument(
    "--from",
    type=int,
    default=1,
    dest="from_step",
    help="Step number to start from (1-6, default: 1)",
)


def main():
    args = parser.parse_args()
    run(from_step=args.from_step)


if __name__ == "__main__":
    main()
