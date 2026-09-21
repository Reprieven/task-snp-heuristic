"""Эвристика распределения дефицита (ядро модуля).

Алгоритм ``GreedyTieredAllocator`` — жадная аппроксимация задачи
минимизации взвешенного дефицита:

    min sum_i w_i * (demand_i - x_i)
    s.t.  sum_i x_i <= available
          x_i = 0  или  (x_i >= min_lot  и  x_i кратно rounding_value)

Приоритет трактуется как жёсткий лексикографический порядок (тиры),
внутри тира объём делится пропорционально недополученному спросу.
Ничьи разрешаются детерминированно по ``request_id``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import groupby
from typing import Dict, Iterable

from .domain import Request


def _rounding(req: Request) -> int:
    """Эффективная кратность; 0 (нет ограничения) приводим к 1."""
    return req.rounding_value if req.rounding_value > 0 else 1


def _round_up(value: int, base: int) -> int:
    """Округление вверх до кратного base."""
    return ((value + base - 1) // base) * base


def _round_down(value: int, base: int) -> int:
    """Округление вниз до кратного base."""
    return (value // base) * base


def _min_lot(req: Request) -> int:
    """Эффективная минимальная партия: наименьший валидный лот >= min_lot."""
    if req.min_lot <= 0:
        return 0
    return _round_up(req.min_lot, _rounding(req))


def _cap(req: Request, allow_overship: bool) -> int:
    """Максимально допустимая отгрузка по заявке.

    Без овершипа — наибольшее кратное лота, не превышающее спрос.
    С овершипом — ближайший лот вверх (физическое ограничение кратности).
    """
    rv = _rounding(req)
    if allow_overship:
        return _round_up(req.demand_qty, rv)
    return _round_down(req.demand_qty, rv)


class AllocationPolicy(ABC):
    """Интерфейс политики распределения.

    Позволяет подменить эвристику точным решателем (например, MILP)
    без изменения остального кода.
    """

    @abstractmethod
    def allocate(self, available_qty: int, requests: Iterable[Request]) -> Dict[str, int]:
        """Возвращает отображение request_id -> отгруженное количество."""


class GreedyTieredAllocator(AllocationPolicy):
    """Жадная политика: тиры по приоритету, пропорция внутри тира."""

    def __init__(self, allow_overship: bool = False):
        # Разрешаем ли отгружать больше demand_qty ради кратности лота.
        self.allow_overship = allow_overship

    def allocate(self, available_qty: int, requests: Iterable[Request]) -> Dict[str, int]:
        reqs = list(requests)
        result = {r.request_id: 0 for r in reqs}
        if available_qty <= 0 or not reqs:
            return result

        # Полный детерминированный порядок: приоритет, затем request_id.
        reqs.sort(key=lambda r: (r.priority, r.request_id))

        remaining = available_qty
        for _priority, tier_iter in groupby(reqs, key=lambda r: r.priority):
            tier = list(tier_iter)
            alloc, remaining = self._allocate_tier(remaining, tier)
            result.update(alloc)
        return result

    def _allocate_tier(self, remaining: int, tier: list[Request]) -> tuple[dict, int]:
        """Распределяет остаток объёма внутри одного тира приоритета.

        Три прохода: гарантированные минимальные партии, пропорциональный
        добор, добор остатка до следующего лота.
        """
        alloc = {r.request_id: 0 for r in tier}
        remaining = self._allocate_min_lots(remaining, tier, alloc)
        remaining = self._allocate_proportional(remaining, tier, alloc)
        remaining = self._allocate_remainder(remaining, tier, alloc)
        return alloc, remaining

    def _allocate_min_lots(self, remaining: int, tier: list[Request], alloc: dict) -> int:
        """Проход 1: гарантируем каждому выполнимому запросу его min_lot.

        В детерминированном порядке. Это жёсткое ограничение.
        """
        for req in tier:
            min_lot = _min_lot(req)
            cap = _cap(req, self.allow_overship)
            if min_lot > 0 and cap >= min_lot and remaining >= min_lot:
                alloc[req.request_id] = min_lot
                remaining -= min_lot
        return remaining

    def _allocate_proportional(self, remaining: int, tier: list[Request], alloc: dict) -> int:
        """Проход 2: пропорциональный добор сверх min_lot.

        Оставшийся объём делим пропорционально недополученному спросу
        (метод наибольших остатков), затем прижимаем к кратности лота.
        """
        active = [r for r in tier if _cap(r, self.allow_overship) - alloc[r.request_id] > 0]
        additions = self._proportional(remaining, active, alloc)
        for req in active:
            add = additions.get(req.request_id, 0)
            rv = _rounding(req)
            q = _round_down(add, rv)  # целые лоты, не превышающие долю
            if alloc[req.request_id] == 0 and 0 < q < _min_lot(req):
                continue  # с нуля нельзя взять частичный лот ниже min_lot
            alloc[req.request_id] += q
            remaining -= q
        return remaining

    def _allocate_remainder(self, remaining: int, tier: list[Request], alloc: dict) -> int:
        """Проход 3: добор остатка до следующего лота.

        Небольшой остаток, не легший в пропорцию, отдаём целыми лотами
        тем, кто может принять ещё один лот (в пределах потолка).
        """
        while remaining > 0:
            progress = False
            for req in tier:
                if remaining <= 0:
                    break
                rv = _rounding(req)
                cur = alloc[req.request_id]
                nxt = cur + rv
                cap = _cap(req, self.allow_overship)
                if nxt > cap or remaining < rv:
                    continue
                if cur == 0 and nxt < _min_lot(req):
                    continue  # с нуля — только полная минимальная партия
                alloc[req.request_id] = nxt
                remaining -= rv
                progress = True
            if not progress:
                break
        return remaining

    def _proportional(self, remaining: int, active: list[Request], alloc: dict) -> dict:
        """Пропорциональное деление остатка (метод наибольших остатков).

        Вес заявки — её недополученный спрос (cap - уже выделенное).
        Возвращает ``request_id -> добавка``, сумма добавок == min(remaining, total).
        """
        weights = {
            r.request_id: _cap(r, self.allow_overship) - alloc[r.request_id]
            for r in active
            if _cap(r, self.allow_overship) - alloc[r.request_id] > 0
        }
        total = sum(weights.values())
        if remaining <= 0 or total == 0:
            return {}
        if remaining >= total:
            return dict(weights)  # хватает на всё — отдаём по максимуму

        # Метод наибольших остатков: целая часть + распределение хвоста.
        additions: dict[str, int] = {}
        remainders: list[tuple[int, str]] = []
        for rid, w in weights.items():
            base = (remaining * w) // total
            remainder = (remaining * w) % total
            additions[rid] = base
            remainders.append((remainder, rid))

        leftover = remaining - sum(additions.values())
        # Детерминированное разрешение ничьих по request_id.
        remainders.sort(key=lambda x: (-x[0], x[1]))
        for i in range(leftover):
            additions[remainders[i][1]] += 1
        return additions
