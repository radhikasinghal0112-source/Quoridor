"""Breadth-first search used to make sure a wall never traps a player."""
from __future__ import annotations

from collections import deque
from typing import Callable, Optional

Cell = tuple[int, int]

STEPS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def shortest_path_length(
    start: Cell,
    is_goal: Callable[[Cell], bool],
    can_step: Callable[[Cell, Cell], bool],
) -> Optional[int]:
    """Number of steps from start to the nearest goal cell, or None if there is no route.

    `can_step(a, b)` says whether a pawn may walk from cell a to the neighbouring
    cell b. Pawns are ignored on purpose: only walls decide whether a route exists.
    """
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        cell, distance = queue.popleft()
        if is_goal(cell):
            return distance
        for dr, dc in STEPS:
            neighbour = (cell[0] + dr, cell[1] + dc)
            if neighbour not in seen and can_step(cell, neighbour):
                seen.add(neighbour)
                queue.append((neighbour, distance + 1))
    return None


def has_path(
    start: Cell,
    is_goal: Callable[[Cell], bool],
    can_step: Callable[[Cell, Cell], bool],
) -> bool:
    return shortest_path_length(start, is_goal, can_step) is not None
