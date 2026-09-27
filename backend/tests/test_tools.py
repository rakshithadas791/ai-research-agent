import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tools.calculator_tool import calculator


def test_calculator_basic():
    assert calculator("2 + 3") == "5"


def test_calculator_precedence():
    assert calculator("2 + 3 * 4") == "14"


def test_calculator_rejects_unsafe_input():
    assert calculator("import os").startswith("[calculator error]")
