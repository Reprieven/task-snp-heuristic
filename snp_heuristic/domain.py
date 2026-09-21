"""Доменные модели модуля SNP Heuristic.

Все модели — неизменяемые (frozen) dataclasses: после создания их нельзя
мутировать, что исключает случайное изменение данных при распределении
и делает результат предсказуемым и тестируемым.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    """Заявка на доступный объём одной позиции в одном периоде.

    Поля соответствуют колонкам data/requests.csv.
    """

    case_id: str
    request_id: str
    dest_location: str
    priority: int
    demand_qty: int
    min_lot: int
    rounding_value: int


@dataclass(frozen=True)
class Supply:
    """Доступный объём по позиции и источнику.

    Поля соответствуют колонкам data/supply.csv.
    """

    case_id: str
    period: str
    item: str
    source_location: str
    available_qty: int


@dataclass(frozen=True)
class AllocationResult:
    """Итог распределения по одному case_id.

    ``allocated`` отображает request_id -> отгруженное количество
    (включая нули), ``remaining`` — нераспределённый остаток.
    """

    case_id: str
    allocated: dict[str, int]
    remaining: int


@dataclass(frozen=True)
class RejectedRequest:
    """Запись, исключённая из распределения из-за противоречивых ограничений.

    Не валидируется (спрос), а именно отклоняется: отрицательные
    ``min_lot`` / ``rounding_value`` ломают логику аллокатора.
    """

    case_id: str
    request_id: str
    reason: str


@dataclass(frozen=True)
class ValidationResult:
    """Результат валидации: валидные заявки и отклонённые записи.

    ``valid`` — нормализованный список для аллокатора;
    ``rejected`` — записи с причиной отклонения, чтобы ошибка была видна.
    """

    valid: list[Request]
    rejected: list[RejectedRequest]
