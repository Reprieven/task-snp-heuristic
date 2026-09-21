"""Гарантирует, что пакет ``snp_heuristic`` импортируется при запуске pytest.

pytest добавляет в sys.path каталог с conftest.py, поэтому корень проекта
оказывается доступен для ``import snp_heuristic``.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
