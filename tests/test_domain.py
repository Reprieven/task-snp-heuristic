"""Тесты доменных моделей.

Фиксируют, что модели неизменяемы и поля корректно заполняются.
"""

from snp_heuristic.domain import (
    AllocationResult,
    RejectedRequest,
    Request,
    Supply,
    ValidationResult,
)


def test_request_creation():
    """Фиксирует создание Request; если поля/конструктор сломаются, загрузка и движок падают."""
    req = Request("CASE_01", "R-101", "DC_A", 1, 40, 0, 25)
    assert req.case_id == "CASE_01"
    assert req.request_id == "R-101"
    assert req.priority == 1
    assert req.demand_qty == 40


def test_supply_creation():
    """Фиксирует создание Supply; если сломается, не с чего распределять доступный объём."""
    supply = Supply("CASE_01", "2026-01", "ITEM_A", "PLANT_1", 100)
    assert supply.available_qty == 100
    assert supply.source_location == "PLANT_1"


def test_models_are_frozen():
    """Фиксирует неизменяемость моделей; если снять frozen, возможна мутация и ломается детерминизм."""
    req = Request("CASE_01", "R-101", "DC_A", 1, 40, 0, 25)
    try:
        req.demand_qty = 99
        frozen = False
    except Exception:
        frozen = True
    assert frozen


def test_allocation_result_holds_remaining():
    """Фиксирует, что AllocationResult хранит остаток; если убрать, нельзя проверить требование суммы."""
    res = AllocationResult("CASE_01", {"R-101": 25, "R-102": 25}, 50)
    assert res.remaining == 50
    assert res.allocated["R-101"] == 25


def test_rejected_request_and_validation_result():
    """Фиксирует, что rejected несёт причину отклонения; если убрать, ошибка маскируется."""
    rej = RejectedRequest("CASE_01", "R-102", "min_lot=-5 отрицательный")
    result = ValidationResult(valid=[], rejected=[rej])
    assert result.rejected[0].request_id == "R-102"
    assert "min_lot" in result.rejected[0].reason
    assert result.valid == []
