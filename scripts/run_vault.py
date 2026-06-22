"""Thin command-line shell for Vault local workflows."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the Vault CLI parser."""
    return argparse.ArgumentParser(
        description="Vault local CLI helper. No workflows are implemented yet.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Vault CLI shell."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
