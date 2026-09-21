"""CLI-обёртка: считает все кейсы из CSV и печатает результат.

Запуск:
    python -m snp_heuristic
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .allocation import GreedyTieredAllocator
from .engine import AllocationEngine
from .io import CsvDataLoader, ResultFormatter

# Пути по умолчанию — относительно пакета, чтобы запуск работал из любой директории.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="snp_heuristic",
        description="SNP Heuristic: распределение дефицита по кейсам из CSV.",
    )
    parser.add_argument(
        "--supply",
        default=str(_DATA_DIR / "supply.csv"),
        help="Путь к файлу с доступным объёмом (по умолчанию data/supply.csv)",
    )
    parser.add_argument(
        "--requests",
        default=str(_DATA_DIR / "requests.csv"),
        help="Путь к файлу с заявками (по умолчанию data/requests.csv)",
    )
    parser.add_argument(
        "--allow-overship",
        action="store_true",
        help="Разрешить отгружать больше demand_qty ради кратности лота",
    )
    args = parser.parse_args(argv)

    loader = CsvDataLoader(args.supply, args.requests)
    supplies, requests = loader.load()

    policy = GreedyTieredAllocator(allow_overship=args.allow_overship)
    engine = AllocationEngine(policy=policy)
    outcome = engine.run(supplies, requests)

    print(ResultFormatter().format(outcome.results, outcome.rejected))
    return 0
