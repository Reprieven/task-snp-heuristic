"""SNP Heuristic: распределение дефицита.

Модуль решает элементарную операцию планирования цепи поставок:
распределение доступного объёма одной позиции в одном периоде между
несколькими конкурирующими заявками.

Публичный интерфейс:
    GreedyTieredAllocator      — эвристика распределения (ядро модуля)
    AllocationEngine           — прогон по всем case_id из входных данных
    CsvDataLoader              — загрузка supply/requests из CSV
    ResultFormatter            — человекочитаемый вывод результата
"""

from .allocation import AllocationPolicy, GreedyTieredAllocator
from .domain import (
    AllocationResult,
    RejectedRequest,
    Request,
    Supply,
    ValidationResult,
)
from .engine import AllocationEngine
from .io import CsvDataLoader, ResultFormatter

__all__ = [
    "AllocationPolicy",
    "GreedyTieredAllocator",
    "AllocationResult",
    "Request",
    "Supply",
    "AllocationEngine",
    "CsvDataLoader",
    "ResultFormatter",
    "RejectedRequest",
    "ValidationResult",
]
