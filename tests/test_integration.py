"""Интеграционный тест: прогон на реальных data/*.csv через движок и загрузчик.

Это проверка «точки входа» по ТЗ: считает все кейсы из CSV и выдаёт
читаемый результат. Если этот тест падает — сломана сборка всего модуля.
"""

from pathlib import Path

from snp_heuristic.engine import AllocationEngine
from snp_heuristic.io import CsvDataLoader, ResultFormatter

DATA = Path(__file__).parent.parent / "data"

EXPECTED = {
    "CASE_01": {"R-101": 25, "R-102": 25, "R-103": 25},
    "CASE_02": {"R-201": 40, "R-202": 30, "R-203": 30, "R-204": 0},
    "CASE_03": {"R-301": 0, "R-302": 0, "R-303": 30, "R-304": 30},
    "CASE_04": {"R-405": 19, "R-401": 20, "R-403": 19, "R-402": 20, "R-404": 19},
    "CASE_05": {"R-501": 25, "R-502": 30, "R-503": 5},
    "CASE_06": {"R-601": 100, "R-602": 0, "R-603": 77},
    "CASE_07": {"R-701": 100, "R-702": 0, "R-703": 0},
}


def test_integration_full_dataset():
    """Фиксирует полный план на всех кейсах из CSV; если алгоритм/загрузчик сломается, план разойдётся."""
    loader = CsvDataLoader(DATA / "supply.csv", DATA / "requests.csv")
    supplies, requests = loader.load()
    outcome = AllocationEngine().run(supplies, requests)
    by_case = {r.case_id: r for r in outcome.results}
    assert set(by_case) == set(EXPECTED)
    for case_id, expected in EXPECTED.items():
        assert by_case[case_id].allocated == expected


def test_integration_sums_do_not_exceed_available():
    """Фиксирует требование суммы<=available на всех кейсах; если нарушить, план превысит лимит."""
    loader = CsvDataLoader(DATA / "supply.csv", DATA / "requests.csv")
    supplies, requests = loader.load()
    outcome = AllocationEngine().run(supplies, requests)
    supply_by_case = {s.case_id: s.available_qty for s in supplies}
    for res in outcome.results:
        assert sum(res.allocated.values()) <= supply_by_case[res.case_id]


def test_integration_formatter_runs():
    """Фиксирует, что вывод точки входа без ошибок; если упасть, сломана сборка модуля."""
    loader = CsvDataLoader(DATA / "supply.csv", DATA / "requests.csv")
    supplies, requests = loader.load()
    outcome = AllocationEngine().run(supplies, requests)
    text = ResultFormatter().format(outcome.results, outcome.rejected)
    assert "Кейс CASE_01" in text
    assert "остаток" in text


def test_integration_no_rejected_on_clean_data():
    """Фиксирует, что на чистых данных нет отклонённых; если валидатор слишком строг, появятся ложные rejected."""
    loader = CsvDataLoader(DATA / "supply.csv", DATA / "requests.csv")
    supplies, requests = loader.load()
    outcome = AllocationEngine().run(supplies, requests)
    assert outcome.rejected == []
