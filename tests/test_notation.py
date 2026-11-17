import pytest

from quoridor.board import Wall
from quoridor.notation import cell_name, parse_cell, parse_wall, wall_name


def test_cell_names_round_trip():
    for row in range(9):
        for col in range(9):
            assert parse_cell(cell_name((row, col))) == (row, col)


def test_known_cells():
    assert parse_cell("a1") == (0, 0)
    assert parse_cell("e5") == (4, 4)
    assert parse_cell("i9") == (8, 8)
    assert cell_name((2, 3)) == "d3"


def test_parse_cell_is_case_and_space_tolerant():
    assert parse_cell(" E5 ") == (4, 4)


@pytest.mark.parametrize("text", ["", "e", "e0", "j5", "e10", "55", "ee", "5e"])
def test_bad_cells_are_rejected(text):
    with pytest.raises(ValueError):
        parse_cell(text)


def test_walls():
    assert parse_wall("d3", "h") == Wall("H", 2, 3)
    assert parse_wall("d3", "V") == Wall("V", 2, 3)
    assert wall_name(Wall("H", 2, 3)) == "d3 h"


def test_bad_wall_orientation():
    with pytest.raises(ValueError):
        parse_wall("d3", "x")
