"""Тесты ввода/вывода.

Фиксируют чтение CSV и человекочитаемый вывод результата.
"""

from snp_heuristic.domain import AllocationResult, RejectedRequest
from snp_heuristic.io import CsvDataLoader, ResultFormatter

import pytest

SUPPLY_CSV = """case_id,period,item,source_location,available_qty
CASE_01,2026-01,ITEM_A,PLANT_1,100
CASE_02,2026-01,ITEM_A,PLANT_1,200
"""

REQUESTS_CSV = """case_id,request_id,dest_location,priority,demand_qty,min_lot,rounding_value
CASE_01,R-101,DC_A,1,40,0,25
CASE_01,R-102,DC_B,1,40,0,25
CASE_02,R-201,DC_A,1,50,30,10
"""


def test_csv_loader_reads_supply(tmp_path):
    """Фиксирует чтение supply; если сломается, движок не получит доступный объём."""
    supply_path = tmp_path / "supply.csv"
    supply_path.write_text(SUPPLY_CSV, encoding="utf-8")
    (tmp_path / "requests.csv").write_text(REQUESTS_CSV, encoding="utf-8")
    loader = CsvDataLoader(supply_path, tmp_path / "requests.csv")
    supplies, _ = loader.load()
    assert supplies[0].case_id == "CASE_01"
    assert supplies[0].available_qty == 100
    assert supplies[1].available_qty == 200


def test_csv_loader_reads_requests(tmp_path):
    """Фиксирует чтение requests; если сломается, не будет заявок на распределение."""
    requests_path = tmp_path / "requests.csv"
    requests_path.write_text(REQUESTS_CSV, encoding="utf-8")
    (tmp_path / "supply.csv").write_text(SUPPLY_CSV, encoding="utf-8")
    loader = CsvDataLoader(tmp_path / "supply.csv", requests_path)
    _, requests = loader.load()
    assert requests[0].request_id == "R-101"
    assert requests[0].rounding_value == 25
    assert requests[2].min_lot == 30


def test_csv_loader_raises_on_non_numeric_qty(tmp_path):
    """Битая строка (нечисловой объём) не должна молча проскочить."""
    supply_path = tmp_path / "supply.csv"
    supply_path.write_text(
        "case_id,period,item,source_location,available_qty\n"
        "CASE_01,2026-01,ITEM_A,PLANT_1,abc\n",
        encoding="utf-8",
    )
    (tmp_path / "requests.csv").write_text(REQUESTS_CSV, encoding="utf-8")
    loader = CsvDataLoader(supply_path, tmp_path / "requests.csv")
    with pytest.raises(ValueError) as exc_info:
        loader.load()
    msg = str(exc_info.value)
    assert "supply.csv" in msg
    assert "строка 2" in msg
    assert "available_qty" in msg
    assert "abc" in msg


def test_csv_loader_raises_on_missing_column(tmp_path):
    """Отсутствующая колонка даёт понятную ошибку, а не сырой KeyError."""
    requests_path = tmp_path / "requests.csv"
    requests_path.write_text(
        "case_id,request_id,dest_location,priority,demand_qty,min_lot\n"
        "CASE_01,R-101,DC_A,1,40,0\n",
        encoding="utf-8",
    )
    (tmp_path / "supply.csv").write_text(SUPPLY_CSV, encoding="utf-8")
    loader = CsvDataLoader(tmp_path / "supply.csv", requests_path)
    with pytest.raises(ValueError) as exc_info:
        loader.load()
    assert "requests.csv" in str(exc_info.value)
    assert "rounding_value" in str(exc_info.value)


def test_csv_loader_raises_on_missing_file(tmp_path):
    """Несуществующий файл даёт понятную ошибку вместо сырого FileNotFoundError."""
    loader = CsvDataLoader(tmp_path / "nope.csv", tmp_path / "requests.csv")
    with pytest.raises(ValueError) as exc_info:
        loader.load()
    assert "Файл не найден" in str(exc_info.value)
    assert "nope.csv" in str(exc_info.value)


def test_csv_loader_raises_on_empty_file(tmp_path):
    """Пустой файл (нет заголовка) не должен тихо вернуть пустой список."""
    empty = tmp_path / "supply.csv"
    empty.write_text("", encoding="utf-8")
    (tmp_path / "requests.csv").write_text(REQUESTS_CSV, encoding="utf-8")
    loader = CsvDataLoader(empty, tmp_path / "requests.csv")
    with pytest.raises(ValueError) as exc_info:
        loader.load()
    assert "Файл пуст" in str(exc_info.value)


def test_csv_loader_raises_on_header_only_file(tmp_path):
    """Файл с шапкой, но без данных, тоже считается ошибочным."""
    header_only = tmp_path / "requests.csv"
    header_only.write_text(
        "case_id,request_id,dest_location,priority,demand_qty,min_lot,rounding_value\n",
        encoding="utf-8",
    )
    (tmp_path / "supply.csv").write_text(SUPPLY_CSV, encoding="utf-8")
    loader = CsvDataLoader(tmp_path / "supply.csv", header_only)
    with pytest.raises(ValueError) as exc_info:
        loader.load()
    assert "не содержит данных" in str(exc_info.value)


def test_formatter_output():
    """Фиксирует формат вывода; если изменить, человек не поймёт результат."""
    res = [AllocationResult("CASE_01", {"R-101": 25, "R-102": 25}, 50)]
    text = ResultFormatter().format(res, rejected=[])
    assert "Кейс CASE_01" in text
    assert "остаток 50" in text
    assert "R-101: 25" in text
    assert "R-102: 25" in text


def test_formatter_shows_rejected():
    """Фиксирует, что форматтер показывает rejected; если скрыть, ошибка маскируется."""
    res = [AllocationResult("CASE_01", {"R-101": 25}, 75)]
    rejected = [RejectedRequest("CASE_01", "R-102", "min_lot=-5 отрицательный")]
    text = ResultFormatter().format(res, rejected=rejected)
    assert "Отклонённые записи" in text
    assert "R-102" in text
    assert "min_lot" in text
