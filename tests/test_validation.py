"""Тесты валидации входных данных.

Фиксируют политику обращения с некорректными/противоречивыми данными:
спрос зануляется, противоречивые ограничения уходят в rejected (а не
обрушивают весь расчёт).
"""

from snp_heuristic.domain import Request
from snp_heuristic.validation import DataValidator


def _req(**kw) -> Request:
    defaults = dict(
        case_id="CASE_01",
        request_id="R-001",
        dest_location="DC_A",
        priority=1,
        demand_qty=50,
        min_lot=0,
        rounding_value=0,
    )
    defaults.update(kw)
    return Request(**defaults)


def test_negative_demand_clamped_to_zero():
    """Фиксирует, что отрицательный спрос зануляется; если отклонять его, валидная заявка потеряется."""
    out = DataValidator().validate([_req(demand_qty=-10)])
    assert len(out.rejected) == 0
    assert out.valid[0].demand_qty == 0


def test_zero_demand_kept():
    """Фиксирует, что нулевой спрос остаётся в плане; если отбрасывать, заявка исчезнет из вывода."""
    out = DataValidator().validate([_req(demand_qty=0)])
    assert out.valid[0].demand_qty == 0
    assert out.rejected == []


def test_negative_min_lot_rejected():
    """Фиксирует, что отрицательный min_lot уходит в rejected; если вернуть raise, один сбой обрушит расчёт."""
    out = DataValidator().validate([_req(min_lot=-5)])
    assert out.valid == []
    assert len(out.rejected) == 1
    assert out.rejected[0].request_id == "R-001"
    assert "min_lot" in out.rejected[0].reason


def test_negative_rounding_rejected():
    """Фиксирует, что отрицательная кратность уходит в rejected; если вернуть raise, один сбой обрушит расчёт."""
    out = DataValidator().validate([_req(rounding_value=-1)])
    assert out.valid == []
    assert len(out.rejected) == 1
    assert "rounding_value" in out.rejected[0].reason


def test_one_bad_record_does_not_break_others():
    """Фиксирует изоляцию ошибки; если валидатор упадёт на первой записи, остальные не посчитаются."""
    out = DataValidator().validate(
        [_req(request_id="R-1", min_lot=-5), _req(request_id="R-2", demand_qty=40)]
    )
    assert [r.request_id for r in out.valid] == ["R-2"]
    assert [r.request_id for r in out.rejected] == ["R-1"]


def test_valid_requests_pass_through():
    """Фиксирует, что валидатор не портит валидные данные; если меняет их, план искажается."""
    out = DataValidator().validate([_req(demand_qty=40, rounding_value=25)])
    assert out.valid[0].demand_qty == 40
    assert out.valid[0].rounding_value == 25
    assert out.rejected == []
