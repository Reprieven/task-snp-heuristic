"""Оркестрация распределения по всем case_id входных данных.

``AllocationEngine`` группирует заявки по case_id, сопоставляет их с
доступным объёмом и прогоняет через политику распределения. Кейсы
независимы, поэтому движок не хранит состояние между ними.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .allocation import AllocationPolicy, GreedyTieredAllocator
from .domain import AllocationResult, RejectedRequest, Request, Supply
from .validation import DataValidator


@dataclass(frozen=True)
class EngineResult:
    """Итог прогона: распределения по кейсам и отклонённые записи."""

    results: list[AllocationResult]
    rejected: list[RejectedRequest]


class AllocationEngine:
    """Считает распределение для набора кейсов."""

    def __init__(
        self,
        policy: AllocationPolicy | None = None,
        validator: DataValidator | None = None,
    ):
        # Политика и валидатор инжектируются снаружи: их легко подменить
        # (например, на точный MILP-решатель) без изменения движка.
        self.policy = policy or GreedyTieredAllocator()
        self.validator = validator or DataValidator()

    def run(self, supplies: list[Supply], requests: list[Request]) -> EngineResult:
        """Возвращает распределения по кейсам и отклонённые записи.

        Заявки, для которых нет записи в ``supplies``, получают нулевую
        отгрузку (объём неизвестен — отгружать нечего). Противоречивые
        записи уходят в ``rejected`` и не обрушивают расчёт.
        """
        supply_by_case = {s.case_id: s for s in supplies}
        requests_by_case: dict[str, list[Request]] = defaultdict(list)
        for req in requests:
            requests_by_case[req.case_id].append(req)

        results: list[AllocationResult] = []
        rejected: list[RejectedRequest] = []
        for case_id, case_requests in requests_by_case.items():
            supply = supply_by_case.get(case_id)
            available = supply.available_qty if supply is not None else 0
            validation = self.validator.validate(case_requests)
            rejected.extend(validation.rejected)
            if not validation.valid:
                # Нет валидных заявок — кейс не распределяем, но не ломаем батч.
                results.append(
                    AllocationResult(
                        case_id=case_id,
                        allocated={},
                        remaining=available,
                    )
                )
                continue
            allocated = self.policy.allocate(available, validation.valid)
            results.append(
                AllocationResult(
                    case_id=case_id,
                    allocated=allocated,
                    remaining=available - sum(allocated.values()),
                )
            )
        return EngineResult(results=results, rejected=rejected)
