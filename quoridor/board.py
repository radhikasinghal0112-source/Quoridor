"""The rules of Quoridor: pawns, walls, movement and jumping.

Coordinates
    A cell is (row, col) with both from 0 to 8 and (0, 0) at the top left.

    A wall is anchored on a *corner*: the point where four cells meet. The wall
    at (row, col) sits on the corner at the bottom right of cell (row, col).
        "H" runs left to right along that corner and covers columns col and col+1
            (it lies between rows row and row+1).
        "V" runs top to bottom along that corner and covers rows row and row+1
            (it lies between columns col and col+1).
    Both orientations use anchors from 0 to 7, so a wall can never hang off the
    board or run along its outer edge.

Walls are stored twice: as a set of Wall values (for the placement rules) and as
a set of blocked edges (for movement and the path check). An edge is a
frozenset of two neighbouring cells, so "is this step blocked?" is one lookup.
"""
from __future__ import annotations

import copy
from typing import NamedTuple, Optional

from .pathfinding import has_path

SIZE = 9

Cell = tuple[int, int]

STEPS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Players start in the middle of an edge, clockwise from the top.
START_CELLS = {
    2: [(0, 4), (8, 4)],
    4: [(0, 4), (4, 8), (8, 4), (4, 0)],
}
DEFAULT_WALLS = {2: 10, 4: 5}


class Wall(NamedTuple):
    orientation: str  # "H" or "V"
    row: int
    col: int


class IllegalMove(Exception):
    """A pawn move that the rules do not allow. The message says why."""


class IllegalWall(Exception):
    """A wall placement that the rules do not allow. The message says why."""


def blocked_edges(wall: Wall) -> list[frozenset]:
    """The two cell-to-cell edges that a wall blocks."""
    r, c = wall.row, wall.col
    if wall.orientation == "H":
        return [frozenset({(r, c), (r + 1, c)}), frozenset({(r, c + 1), (r + 1, c + 1)})]
    return [frozenset({(r, c), (r, c + 1)}), frozenset({(r + 1, c), (r + 1, c + 1)})]


def in_bounds(cell: Cell) -> bool:
    return 0 <= cell[0] < SIZE and 0 <= cell[1] < SIZE


def _sideways(step: Cell) -> list[Cell]:
    """The two steps at right angles to a step."""
    if step[0] != 0:
        return [(0, -1), (0, 1)]
    return [(-1, 0), (1, 0)]


class Board:
    def __init__(self, num_players: int = 2, walls_per_player: Optional[int] = None):
        if num_players not in START_CELLS:
            raise ValueError("Quoridor is played by 2 or 4 players.")
        if walls_per_player is None:
            walls_per_player = DEFAULT_WALLS[num_players]
        if walls_per_player < 0:
            raise ValueError("Players cannot start with a negative number of walls.")

        self.num_players = num_players
        self.start_cells = list(START_CELLS[num_players])
        self.pawns: list[Cell] = list(self.start_cells)
        self.walls_left = [walls_per_player] * num_players
        self.walls: set[Wall] = set()
        self.blocked: set[frozenset] = set()

    def copy(self) -> "Board":
        return copy.deepcopy(self)

    # ----- goals -----------------------------------------------------------

    def is_goal(self, player: int, cell: Cell) -> bool:
        """A player's goal is any cell on the edge opposite the one they started on."""
        start_row, start_col = self.start_cells[player]
        if start_row == 0:
            return cell[0] == SIZE - 1
        if start_row == SIZE - 1:
            return cell[0] == 0
        if start_col == 0:
            return cell[1] == SIZE - 1
        return cell[1] == 0

    def has_won(self, player: int) -> bool:
        return self.is_goal(player, self.pawns[player])

    # ----- movement --------------------------------------------------------

    def can_step(self, a: Cell, b: Cell) -> bool:
        """True if b is a neighbour of a with no wall in between."""
        if not in_bounds(a) or not in_bounds(b):
            return False
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            return False
        return frozenset({a, b}) not in self.blocked

    def is_occupied(self, cell: Cell) -> bool:
        return cell in self.pawns

    def legal_moves(self, player: int) -> list[Cell]:
        """Every cell the player may move to, including jumps over an adjacent pawn.

        A pawn that stands in the way can be jumped straight over. If a wall, the
        edge of the board or another pawn is directly behind it, the player may
        instead step diagonally to either side of it (unless a wall stops that).
        """
        here = self.pawns[player]
        moves: list[Cell] = []
        for step in STEPS:
            ahead = (here[0] + step[0], here[1] + step[1])
            if not self.can_step(here, ahead):
                continue
            if not self.is_occupied(ahead):
                moves.append(ahead)
                continue
            behind = (ahead[0] + step[0], ahead[1] + step[1])
            if self.can_step(ahead, behind) and not self.is_occupied(behind):
                moves.append(behind)
            else:
                for side in _sideways(step):
                    diagonal = (ahead[0] + side[0], ahead[1] + side[1])
                    if self.can_step(ahead, diagonal) and not self.is_occupied(diagonal):
                        moves.append(diagonal)
        return moves

    def move(self, player: int, cell: Cell) -> None:
        if cell not in self.legal_moves(player):
            raise IllegalMove(self._why_not(player, cell))
        self.pawns[player] = cell

    def _why_not(self, player: int, cell: Cell) -> str:
        here = self.pawns[player]
        if not in_bounds(cell):
            return "That cell is off the board."
        if cell == here:
            return "You are already on that cell."
        if self.is_occupied(cell):
            return "Another pawn is on that cell."
        if abs(cell[0] - here[0]) + abs(cell[1] - here[1]) == 1:
            return "A wall is in the way."
        return "You can only move to a neighbouring cell, or jump over an adjacent pawn."

    # ----- walls -----------------------------------------------------------

    def _conflict(self, wall: Wall) -> Optional[str]:
        """Why this wall cannot go next to the existing ones, or None if it can."""
        r, c = wall.row, wall.col
        if wall in self.walls:
            return "There is already a wall there."
        if wall.orientation == "H":
            if Wall("V", r, c) in self.walls:
                return "That wall would cross another wall."
            if Wall("H", r, c - 1) in self.walls or Wall("H", r, c + 1) in self.walls:
                return "That wall would overlap another wall."
        else:
            if Wall("H", r, c) in self.walls:
                return "That wall would cross another wall."
            if Wall("V", r - 1, c) in self.walls or Wall("V", r + 1, c) in self.walls:
                return "That wall would overlap another wall."
        return None

    def has_route(self, player: int) -> bool:
        """True if the player can still reach their goal edge, ignoring other pawns."""
        return has_path(
            self.pawns[player],
            lambda cell: self.is_goal(player, cell),
            self.can_step,
        )

    def place_wall(self, player: int, wall: Wall) -> None:
        if wall.orientation not in ("H", "V"):
            raise IllegalWall("A wall is either horizontal or vertical.")
        if self.walls_left[player] <= 0:
            raise IllegalWall("You have no walls left.")
        if not (0 <= wall.row <= SIZE - 2 and 0 <= wall.col <= SIZE - 2):
            raise IllegalWall("A wall must sit inside the board, not along its outer edge.")
        problem = self._conflict(wall)
        if problem:
            raise IllegalWall(problem)

        # Try the wall, and take it back if it traps anyone.
        edges = blocked_edges(wall)
        self.walls.add(wall)
        self.blocked.update(edges)
        for other in range(self.num_players):
            if not self.has_route(other):
                self.walls.discard(wall)
                self.blocked.difference_update(edges)
                raise IllegalWall(
                    f"That wall would leave player {other + 1} with no way to reach their goal."
                )
        self.walls_left[player] -= 1
