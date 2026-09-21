"""Свойства решения (invariants), которые обязаны выполняться всегда.

Проверяем три жёстких требования ТЗ на всех кейсах:
  1) сумма отгрузок <= available_qty;
  2) каждая отгрузка — 0 либо лот-валидна (>= min_lot и кратна rounding_value);
  3) результат детерминирован.
"""

import pytest

from snp_heuristic.allocation import GreedyTieredAllocator
from snp_heuristic.domain import Request


def _req(case, rid, prio, demand, min_lot, rounding):
    return Request(case, rid, "DC_A", prio, demand, min_lot, rounding)


# Кейсы, покрывающие основные развилки: дефицит, min_lot, кратность, нулевой спрос.
CASES = [
    (100, [_req("C", "R-1", 1, 40, 0, 25), _req("C", "R-2", 1, 40, 0, 25), _req("C", "R-3", 1, 40, 0, 25)]),
    (100, [_req("C", "R-1", 1, 50, 30, 10), _req("C", "R-2", 1, 50, 30, 10), _req("C", "R-3", 1, 50, 30, 10)]),
    (60, [_req("C", "R-1", 1, 0, 0, 5), _req("C", "R-2", 3, 45, 0, 5), _req("C", "R-3", 1, 30, 0, 0)]),
    (200, [_req("C", "R-1", 1, 100, 30, 25), _req("C", "R-2", 1, 100, 250, 10), _req("C", "R-3", 2, 80, 0, 7)]),
    (97, [_req("C", f"R-{i}", 2, 25, 0, 1) for i in range(5)]),
]


def _lot_valid(qty, demand, min_lot, rounding):
    """Проверка «0 или валидный лот» независимо от реализации."""
    if qty == 0:
        return True
    rv = rounding if rounding > 0 else 1
    if qty % rv != 0:
        return False
    if min_lot > 0 and qty < min_lot:
        return False
    return qty <= demand  # без овершипа не превышаем спрос


@pytest.mark.parametrize("available,requests", CASES)
def test_invariants(available, requests):
    """Фиксирует инварианты (сумма<=available, лот-валидность); если их нарушить, план станет невалидным."""
    out = GreedyTieredAllocator().allocate(available, requests)
    assert sum(out.values()) <= available
    for r in requests:
        assert _lot_valid(out[r.request_id], r.demand_qty, r.min_lot, r.rounding_value)


@pytest.mark.parametrize("available,requests", CASES)
def test_determinism(available, requests):
    """Фиксирует повторяемость на тех же данных; если внести рандом/float, результат перестанет быть детерминированным."""
    a = GreedyTieredAllocator().allocate(available, requests)
    b = GreedyTieredAllocator().allocate(available, requests)
    assert a == b
