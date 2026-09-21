"""Тесты детерминизма.

Жёсткое требование ТЗ: повторный запуск на тех же данных даёт ровно тот же план.
"""

from snp_heuristic.allocation import GreedyTieredAllocator
from snp_heuristic.domain import Request


def test_allocate_is_deterministic():
    """Фиксирует детерминизм при разном порядке входа; если убрать сортировку, план зависит от порядка строк."""
    requests = [
        Request("C", "R-1", "DC_A", 1, 40, 0, 25),
        Request("C", "R-2", "DC_B", 1, 40, 0, 25),
        Request("C", "R-3", "DC_C", 1, 40, 0, 25),
    ]
    a = GreedyTieredAllocator().allocate(100, requests)
    b = GreedyTieredAllocator().allocate(100, list(reversed(requests)))
    assert a == b


def test_allocate_same_object_consistently():
    """Фиксирует независимость от порядка входа; если полагаться на порядок списка, результат станет нестабильным."""
    requests = [
        Request("C", "R-2", "DC_B", 1, 50, 30, 10),
        Request("C", "R-1", "DC_A", 1, 50, 30, 10),
    ]
    out1 = GreedyTieredAllocator().allocate(100, requests)
    out2 = GreedyTieredAllocator().allocate(100, list(reversed(requests)))
    assert out1 == out2
