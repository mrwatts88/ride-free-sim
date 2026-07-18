"""Run the trainer: uv run python -m ridefree.trainer [--port 8877] [--seed N]"""

import argparse

from ridefree.trainer.server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="crouch15 blackjack trainer")
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument("--db", default="data/trainer.db")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="fixed session seed (default: wall clock per session; always recorded)",
    )
    args = parser.parse_args()
    serve(args.port, args.db, seed=args.seed)


if __name__ == "__main__":
    main()
