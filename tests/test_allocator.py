"""Тесты эвристики распределения.

Золотые кейсы из data/*.csv (регрессия) плюс собственные кейсы на
каждую ключевую развилку. Каждый тест фиксирует конкретное поведение.
"""

from snp_heuristic.allocation import GreedyTieredAllocator
from snp_heuristic.domain import Request


def req(case, rid, dest, prio, demand, min_lot, rounding):
    return Request(case, rid, dest, prio, demand, min_lot, rounding)


def test_case_01():
    """Фиксирует валидные лоты и остаток от кратности (3x40, лот 25); если разрешить овершип, план изменится."""
    requests = [
        req("CASE_01", "R-101", "DC_A", 1, 40, 0, 25),
        req("CASE_01", "R-102", "DC_B", 1, 40, 0, 25),
        req("CASE_01", "R-103", "DC_C", 1, 40, 0, 25),
    ]
    out = GreedyTieredAllocator().allocate(100, requests)
    assert out == {"R-101": 25, "R-102": 25, "R-103": 25}
    assert sum(out.values()) <= 100


def test_case_02():
    """Фиксирует fallback на min_lot, когда доля 25 < min_lot 30; если убрать проход минималок, выйдет невалидная отгрузка."""
    requests = [
        req("CASE_02", "R-201", "DC_A", 1, 50, 30, 10),
        req("CASE_02", "R-202", "DC_B", 1, 50, 30, 10),
        req("CASE_02", "R-203", "DC_C", 1, 50, 30, 10),
        req("CASE_02", "R-204", "DC_D", 1, 50, 30, 10),
    ]
    out = GreedyTieredAllocator().allocate(100, requests)
    assert out == {"R-201": 40, "R-202": 30, "R-203": 30, "R-204": 0}
    assert sum(out.values()) <= 100


def test_case_03():
    """Фиксирует, что отрицательный/нулевой спрос даёт 0; если отклонять такие заявки, они исчезнут из плана."""
    requests = [
        req("CASE_03", "R-301", "DC_A", 1, 0, 0, 5),
        req("CASE_03", "R-302", "DC_B", 2, -10, 0, 5),
        req("CASE_03", "R-303", "DC_C", 3, 45, 0, 5),
        req("CASE_03", "R-304", "DC_D", 1, 30, 0, 0),
    ]
    out = GreedyTieredAllocator().allocate(60, requests)
    assert out == {"R-301": 0, "R-302": 0, "R-303": 30, "R-304": 30}
    assert sum(out.values()) <= 60


def test_case_04():
    """Фиксирует метод наибольших остатков (97 на 5x25); если заменить на простое округление, сумма не сойдётся с available."""
    requests = [
        req("CASE_04", "R-405", "DC_E", 2, 25, 0, 1),
        req("CASE_04", "R-401", "DC_A", 2, 25, 0, 1),
        req("CASE_04", "R-403", "DC_C", 2, 25, 0, 1),
        req("CASE_04", "R-402", "DC_B", 2, 25, 0, 1),
        req("CASE_04", "R-404", "DC_D", 2, 25, 0, 1),
    ]
    out = GreedyTieredAllocator().allocate(97, requests)
    assert out == {"R-405": 19, "R-401": 20, "R-403": 19, "R-402": 20, "R-404": 19}
    assert sum(out.values()) == 97


def test_case_05():
    """Фиксирует, что при спросе меньше запаса отгружается по лотам, излишек остаётся; если дотягивать, появится овершип."""
    requests = [
        req("CASE_05", "R-501", "DC_A", 1, 40, 0, 25),
        req("CASE_05", "R-502", "DC_B", 2, 33, 0, 10),
        req("CASE_05", "R-503", "DC_C", 3, 7, 0, 5),
    ]
    out = GreedyTieredAllocator().allocate(500, requests)
    assert out == {"R-501": 25, "R-502": 30, "R-503": 5}
    assert sum(out.values()) <= 500


def test_case_06():
    """Фиксирует, что min_lot>спрос делает заявку необслужимой (0); если отдать частично, нарушится требование min_lot."""
    requests = [
        req("CASE_06", "R-601", "DC_A", 1, 100, 30, 25),
        req("CASE_06", "R-602", "DC_B", 1, 100, 250, 10),
        req("CASE_06", "R-603", "DC_C", 2, 80, 0, 7),
    ]
    out = GreedyTieredAllocator().allocate(200, requests)
    assert out == {"R-601": 100, "R-602": 0, "R-603": 77}
    assert sum(out.values()) <= 200


def test_case_07():
    """Фиксирует жёсткий приоритет; если смягчить его, высокоприоритетная заявка может не получить весь объём."""
    requests = [
        req("CASE_07", "R-701", "DC_A", 1, 100, 0, 1),
        req("CASE_07", "R-702", "DC_B", 2, 10, 0, 1),
        req("CASE_07", "R-703", "DC_C", 3, 10, 0, 1),
    ]
    out = GreedyTieredAllocator().allocate(100, requests)
    assert out == {"R-701": 100, "R-702": 0, "R-703": 0}


def test_min_lot_exceeds_available_gives_zero():
    """Фиксирует, что при available<min_lot отгрузка 0; если дать частично, нарушится требование min_lot."""
    requests = [req("C", "R-1", "DC_A", 1, 100, 30, 10)]
    out = GreedyTieredAllocator().allocate(10, requests)
    assert out == {"R-1": 0}


def test_no_deficit_serves_full_demand():
    """Фиксирует, что при достатке каждая заявка получает полный спрос; если ограничить, спрос не покроется."""
    requests = [
        req("C", "R-1", "DC_A", 1, 40, 0, 0),
        req("C", "R-2", "DC_B", 1, 40, 0, 0),
    ]
    out = GreedyTieredAllocator().allocate(100, requests)
    assert out == {"R-1": 40, "R-2": 40}


def test_hard_priority_ordering():
    """Фиксирует жёсткий приоритет; если сортировать иначе, низкоприоритетная заявка может занять объём."""
    requests = [
        req("C", "R-2", "DC_B", 2, 50, 0, 0),
        req("C", "R-1", "DC_A", 1, 50, 0, 0),
    ]
    out = GreedyTieredAllocator().allocate(50, requests)
    assert out == {"R-1": 50, "R-2": 0}


def test_overship_uses_surplus_for_next_lot():
    """Фиксирует, что с овершипом 33->40; если убрать овершип, остаток не дотянется до лота."""
    requests = [req("C", "R-1", "DC_A", 1, 33, 0, 10)]
    out = GreedyTieredAllocator(allow_overship=True).allocate(100, requests)
    assert out == {"R-1": 40}


def test_zero_available_returns_all_zero():
    """Фиксирует, что при available=0 все получают 0; если вернуть что-то иное, план превысит лимит."""
    requests = [req("C", "R-1", "DC_A", 1, 50, 0, 0)]
    out = GreedyTieredAllocator().allocate(0, requests)
    assert out == {"R-1": 0}
