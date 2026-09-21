"""Валидация и нормализация входных данных.

Задача приходит от бизнеса в «сыром» виде, поэтому в данных встречаются
некорректные или противоречивые значения. Мы явно решаем, что с ними
делать, а не молча угадываем.

Политика:
    * отрицательный спрос     -> зануляем (спрос — просто число, правил не нарушает)
    * нулевой спрос           -> заявка ничего не просит, получает 0
    * отрицательный min_lot   -> противоречивое ограничение, отклоняем (rejected)
    * отрицательный rounding  -> противоречивое ограничение, отклоняем (rejected)

Важно: одна ошибочная запись не обрушивает весь расчёт. Противоречивые
заявки исключаются и показываются отдельно, остальные продолжают считаться.
"""

from __future__ import annotations

from .domain import RejectedRequest, Request, ValidationResult


class DataValidator:
    """Нормализует заявки и изолирует противоречивые записи.

    Валидатор не решает, сколько отгрузить, — он лишь чистит и проверяет
    данные, чтобы аллокатор работал с непротиворечивым набором, а
    проблемные записи были видны в ``rejected``.
    """

    def validate(self, requests: list[Request]) -> ValidationResult:
        """Разделяет заявки на валидные и отклонённые.

        Отрицательный спрос зануляется (не отклонение), отрицательные
        ``min_lot`` / ``rounding_value`` — отклоняются с причиной.
        """
        valid: list[Request] = []
        rejected: list[RejectedRequest] = []
        for req in requests:
            if req.min_lot < 0:
                rejected.append(
                    RejectedRequest(
                        case_id=req.case_id,
                        request_id=req.request_id,
                        reason=f"min_lot={req.min_lot} отрицательный",
                    )
                )
                continue
            if req.rounding_value < 0:
                rejected.append(
                    RejectedRequest(
                        case_id=req.case_id,
                        request_id=req.request_id,
                        reason=f"rounding_value={req.rounding_value} отрицательный",
                    )
                )
                continue
            valid.append(
                Request(
                    case_id=req.case_id,
                    request_id=req.request_id,
                    dest_location=req.dest_location,
                    priority=req.priority,
                    demand_qty=max(req.demand_qty, 0),
                    min_lot=req.min_lot,
                    rounding_value=req.rounding_value,
                )
            )
        return ValidationResult(valid=valid, rejected=rejected)
