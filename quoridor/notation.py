"""Turning cells and walls into short names people can type, and back.

Cells are named like chess squares: a column letter a-i and a row number 1-9,
with row 1 at the top. A wall is named after the cell whose bottom right corner
it is anchored on, plus h (horizontal) or v (vertical): "d3 h".
"""
from __future__ import annotations

from .board import SIZE, Cell, Wall

COLUMNS = "abcdefghi"


def cell_name(cell: Cell) -> str:
    row, col = cell
    return f"{COLUMNS[col]}{row + 1}"


def parse_cell(text: str) -> Cell:
    text = text.strip().lower()
    if len(text) != 2 or text[0] not in COLUMNS or not text[1].isdigit():
        raise ValueError(f"'{text}' is not a cell. Use a letter a-i and a number 1-9, like e5.")
    row = int(text[1]) - 1
    if not 0 <= row < SIZE:
        raise ValueError(f"'{text}' is not a cell. Rows go from 1 to 9.")
    return (row, COLUMNS.index(text[0]))


def parse_wall(cell_text: str, orientation_text: str) -> Wall:
    row, col = parse_cell(cell_text)
    orientation = orientation_text.strip().upper()
    if orientation not in ("H", "V"):
        raise ValueError("A wall is either h (horizontal) or v (vertical).")
    return Wall(orientation, row, col)


def wall_name(wall: Wall) -> str:
    return f"{cell_name((wall.row, wall.col))} {wall.orientation.lower()}"
