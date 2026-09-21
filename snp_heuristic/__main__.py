"""Позволяет запускать модуль как ``python -m snp_heuristic``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
