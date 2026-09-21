"""Тесты движка оркестрации.

Фиксируют группировку заявок по кейсу и поведение при отсутствии объёма
и при противоречивых данных.
"""

from snp_heuristic.domain import Request, Supply
from snp_heuristic.engine import AllocationEngine


def test_engine_groups_by_case():
    """Фиксирует группировку по case_id; если её убрать, один кейс съест объём другого."""
    supplies = [Supply("CASE_01", "2026-01", "ITEM_A", "PLANT_1", 100)]
    requests = [
        Request("CASE_01", "R-101", "DC_A", 1, 40, 0, 0),
        Request("CASE_01", "R-102", "DC_B", 1, 40, 0, 0),
    ]
    outcome = AllocationEngine().run(supplies, requests)
    results = outcome.results
    assert len(results) == 1
    assert results[0].case_id == "CASE_01"
    assert results[0].allocated == {"R-101": 40, "R-102": 40}
    assert results[0].remaining == 20


def test_engine_missing_supply_returns_zero():
    """Фиксирует, что кейс без supply даёт 0, а не ошибку; если упасть, батч обрушится."""
    supplies = [Supply("CASE_01", "2026-01", "ITEM_A", "PLANT_1", 100)]
    requests = [
        Request("CASE_01", "R-101", "DC_A", 1, 40, 0, 0),
        Request("CASE_02", "R-201", "DC_B", 1, 50, 0, 0),
    ]
    outcome = AllocationEngine().run(supplies, requests)
    by_case = {r.case_id: r for r in outcome.results}
    assert by_case["CASE_02"].allocated == {"R-201": 0}
    assert by_case["CASE_02"].remaining == 0


def test_engine_surfaces_rejected():
    """Фиксирует, что противоречивые заявки уходят в rejected; если игнорировать, ошибка замаскируется."""
    supplies = [Supply("CASE_01", "2026-01", "ITEM_A", "PLANT_1", 100)]
    requests = [
        Request("CASE_01", "R-101", "DC_A", 1, 40, 0, 0),
        Request("CASE_01", "R-102", "DC_B", 1, 50, -10, 0),
    ]
    outcome = AllocationEngine().run(supplies, requests)
    assert outcome.rejected[0].request_id == "R-102"
    assert outcome.results[0].allocated == {"R-101": 40}


def test_engine_uses_injected_policy():
    """Фиксирует DI политики; если движок создаёт политику сам, нельзя подменить на MILP-решатель."""
    policy = GreedyTieredAllocatorSpy()
    engine = AllocationEngine(policy=policy)
    engine.run(
        [Supply("CASE_01", "2026-01", "ITEM_A", "PLANT_1", 10)],
        [Request("CASE_01", "R-101", "DC_A", 1, 50, 0, 0)],
    )
    assert policy.called


class GreedyTieredAllocatorSpy:
    """Заглушка политики: проверяет, что движок делегирует распределение ей."""

    def __init__(self):
        self.called = False

    def allocate(self, available_qty, requests):
        self.called = True
        return {r.request_id: 0 for r in requests}
