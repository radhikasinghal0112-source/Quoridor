"""Drawing the board and the status panel as text.

The board uses a box frame, letters across the top and numbers down the side.
    ·  empty cell        1-4  pawns        •  a cell the current player can move to
    ━  horizontal wall   ┃    vertical wall
Colour is optional: the current player's pawn and move markers are green and
the opponents' pawns are red. With flip=True the board is turned around by
half a turn, so the player who starts at the top sees their own side at the
bottom. Cell names never change, only the way the board is drawn.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .board import SIZE, Board, Cell, Wall
from .game import Game
from .notation import COLUMNS

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Width of the area between the frame's side bars: nine cells, eight gaps and a space each side.
INNER = 2 * SIZE + 1


def paint(text: str, colour: str, use_colour: bool) -> str:
    return f"{colour}{text}{RESET}" if use_colour else text


def format_time(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def render_board(
    board: Board,
    current: Optional[int] = None,
    marks: Iterable[Cell] = (),
    use_colour: bool = False,
    flip: bool = False,
) -> str:
    marks = set(marks)
    pawn_at = {cell: player for player, cell in enumerate(board.pawns)}
    order = list(range(SIZE))
    rows = order[::-1] if flip else order
    cols = order[::-1] if flip else order

    lines = []
    lines.append("      " + " ".join(COLUMNS[c] for c in cols))
    lines.append("    ┌" + "─" * INNER + "┐")

    for i, r in enumerate(rows):
        row = " "
        for j, c in enumerate(cols):
            cell = (r, c)
            if cell in pawn_at:
                player = pawn_at[cell]
                colour = GREEN if player == current else RED
                row += paint(str(player + 1), colour, use_colour and current is not None)
            elif cell in marks:
                row += paint("•", GREEN, use_colour)
            else:
                row += "·"
            if j < SIZE - 1:
                side = (r, cols[j + 1])
                row += "┃" if frozenset({cell, side}) in board.blocked else " "
        lines.append(f"  {r + 1} │{row} │")

        if i < SIZE - 1:
            below = rows[i + 1]
            gap = " "
            for j, c in enumerate(cols):
                gap += "━" if frozenset({(r, c), (below, c)}) in board.blocked else " "
                if j < SIZE - 1:
                    top, left = min(r, below), min(c, cols[j + 1])
                    if Wall("H", top, left) in board.walls:
                        gap += "━"
                    elif Wall("V", top, left) in board.walls:
                        gap += "┃"
                    else:
                        gap += " "
            lines.append(f"    │{gap} │")

    lines.append("    └" + "─" * INNER + "┘")
    return "\n".join(lines)


def render_status(game: Game, use_colour: bool = False) -> str:
    lines = []
    for player in range(game.num_players):
        is_current = player == game.current and game.winner is None
        marker = "▶" if is_current else " "
        name = f"Player {player + 1}"
        if use_colour:
            name = paint(name, GREEN if is_current else RED, True)
        text = f"  {marker} {name}    walls left: {game.board.walls_left[player]:<3}"
        if game.clock:
            left = game.clock.time_left(player)
            clock_text = f"time: {format_time(left)}"
            if use_colour and left < 60:
                clock_text = paint(clock_text, YELLOW if left > 0 else RED, True)
            text += "  " + clock_text
        lines.append(text.rstrip())
    return "\n".join(lines)
