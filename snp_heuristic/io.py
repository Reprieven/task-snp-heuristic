"""Ввод/вывод: чтение CSV и человекочитаемый вывод результата.

Используется только стандартная библиотека (``csv``), чтобы модуль
запускался на чистом окружении без сторонних зависимостей.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from .domain import AllocationResult, RejectedRequest, Request, Supply


def _to_int(value: str, column: str) -> int:
    """Числовое поле CSV; при ошибке указываем колонку и значение."""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{column}={value!r}: ожидается целое число")


class CsvDataLoader:
    """Загружает входные данные из CSV-файлов в доменные объекты."""

    def __init__(self, supply_path: str | Path, requests_path: str | Path):
        self.supply_path = Path(supply_path)
        self.requests_path = Path(requests_path)

    def load(self) -> tuple[list[Supply], list[Request]]:
        """Возвращает (supply, requests)."""
        return self._load_supply(), self._load_requests()

    def _read_rows(self, path: Path, parse_row) -> list:
        """Читает CSV и применяет маппер к каждой строке.

        Ошибки разбора (нечисловое число, отсутствующая колонка)
        собираются и бросаются одной ``ValueError`` с указанием файла
        и номера строки, чтобы проблема была видна сразу.
        """
        try:
            fh = open(path, newline="", encoding="utf-8")
        except FileNotFoundError:
            raise ValueError(f"Файл не найден: {path}")

        rows: list = []
        errors: list[str] = []
        with fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                raise ValueError(f"Файл пуст (нет заголовка): {path}")
            for row in reader:
                try:
                    rows.append(parse_row(row))
                except (KeyError, ValueError, TypeError) as exc:
                    errors.append(f"{path.name}: строка {reader.line_num}: {exc}")
        if errors:
            raise ValueError("Некорректные строки в CSV:\n" + "\n".join(errors))
        if not rows:
            raise ValueError(f"Файл не содержит данных: {path}")
        return rows

    def _load_supply(self) -> list[Supply]:
        return self._read_rows(self.supply_path, self._parse_supply_row)

    def _load_requests(self) -> list[Request]:
        return self._read_rows(self.requests_path, self._parse_request_row)

    @staticmethod
    def _parse_supply_row(row: dict) -> Supply:
        return Supply(
            case_id=row["case_id"],
            period=row["period"],
            item=row["item"],
            source_location=row["source_location"],
            available_qty=_to_int(row["available_qty"], "available_qty"),
        )

    @staticmethod
    def _parse_request_row(row: dict) -> Request:
        return Request(
            case_id=row["case_id"],
            request_id=row["request_id"],
            dest_location=row["dest_location"],
            priority=_to_int(row["priority"], "priority"),
            demand_qty=_to_int(row["demand_qty"], "demand_qty"),
            min_lot=_to_int(row["min_lot"], "min_lot"),
            rounding_value=_to_int(row["rounding_value"], "rounding_value"),
        )


class ResultFormatter:
    """Форматирует результаты распределения в читаемый текст."""

    def format(self, results: Sequence[AllocationResult], rejected: Sequence[RejectedRequest]) -> str:
        lines: list[str] = []
        for res in results:
            lines.append(f"Кейс {res.case_id}: остаток {res.remaining}")
            for request_id, qty in res.allocated.items():
                lines.append(f"  {request_id}: {qty}")
        if rejected:
            lines.append("")
            lines.append("Отклонённые записи (не участвовали в распределении):")
            for rej in rejected:
                lines.append(f"  {rej.case_id}/{rej.request_id}: {rej.reason}")
        return "\n".join(lines)
