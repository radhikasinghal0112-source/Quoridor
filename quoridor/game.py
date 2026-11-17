"""Turns, history, undo and the optional chess clock, built on top of Board."""
from __future__ import annotations

import time
from typing import Callable, Optional

from .board import Board, Cell, IllegalMove, Wall
from .notation import cell_name, wall_name


class GameOver(Exception):
    """Raised when someone tries to act after the game has ended."""


class CannotUndo(Exception):
    """Raised when there is nothing to take back."""


class ChessClock:
    """A per-player time bank.

    A player's clock runs from the moment their turn starts until they make a
    valid move, so thinking time and failed attempts all count. The clock cannot
    interrupt a player who is waiting at a prompt: the loss is declared when
    they next submit something.
    """

    def __init__(
        self,
        minutes: float,
        increment: float = 0,
        players: int = 2,
        time_source: Callable[[], float] = time.monotonic,
    ):
        self.remaining = [minutes * 60.0] * players
        self.increment = increment
        self._now = time_source
        self._running: Optional[int] = None
        self._started_at = 0.0

    def start(self, player: int) -> None:
        self._running = player
        self._started_at = self._now()

    def stop(self) -> None:
        """Charge the running player for their turn, then add the increment."""
        if self._running is None:
            return
        elapsed = self._now() - self._started_at
        self.remaining[self._running] = max(0.0, self.remaining[self._running] - elapsed) + self.increment
        self._running = None

    def time_left(self, player: int) -> float:
        left = self.remaining[player]
        if player == self._running:
            left -= self._now() - self._started_at
        return max(0.0, left)

    def flagged(self, player: int) -> bool:
        return self.time_left(player) <= 0


class Game:
    def __init__(
        self,
        num_players: int = 2,
        walls_per_player: Optional[int] = None,
        clock: Optional[ChessClock] = None,
    ):
        self.board = Board(num_players, walls_per_player)
        self.num_players = num_players
        self.clock = clock
        self.current = 0
        self.winner: Optional[int] = None
        self.end_reason: Optional[str] = None  # "reached", "time" or "resign"
        self.log: list[str] = []
        self.last_move: Optional[str] = None
        self._snapshots: list[tuple] = []
        if self.clock:
            self.clock.start(self.current)

    # ----- actions ---------------------------------------------------------

    def move(self, cell: Cell) -> None:
        self._take_turn(
            lambda: self.board.move(self.current, cell),
            lambda: f"moved to {cell_name(cell)}",
        )

    def place_wall(self, wall: Wall) -> None:
        self._take_turn(
            lambda: self.board.place_wall(self.current, wall),
            lambda: f"placed a wall at {wall_name(wall)}",
        )

    def resign(self) -> None:
        if self.winner is not None:
            raise GameOver()
        if self.num_players != 2:
            raise IllegalMove("Resigning is only available in two player games.")
        self._finish(1 - self.current, "resign")

    def undo(self) -> None:
        """Take back the last turn. Time already spent on the clock is not refunded."""
        if self.winner is not None:
            raise CannotUndo("The game is over.")
        if not self._snapshots:
            raise CannotUndo("There is nothing to undo.")
        self.board, self.current, self.last_move, self.log = self._snapshots.pop()
        if self.clock:
            self.clock.start(self.current)

    # ----- helpers ---------------------------------------------------------

    def loser(self) -> Optional[int]:
        """In a two player game, the player who did not win."""
        if self.winner is None or self.num_players != 2:
            return None
        return 1 - self.winner

    def _take_turn(
        self,
        apply_action: Callable[[], None],
        describe: Callable[[], str],
    ) -> None:
        if self.winner is not None:
            raise GameOver()

        # Out of time before this action: it does not count.
        if self.clock and self.clock.flagged(self.current):
            self.clock.stop()
            self._finish(1 - self.current, "time")
            return

        snapshot = (self.board.copy(), self.current, self.last_move, list(self.log))
        apply_action()  # raises IllegalMove or IllegalWall, leaving the turn unchanged
        self._snapshots.append(snapshot)

        text = f"Player {self.current + 1} {describe()}"
        self.log.append(text)
        self.last_move = text

        if self.clock:
            self.clock.stop()
        if self.board.has_won(self.current):
            self._finish(self.current, "reached")
        else:
            self.current = (self.current + 1) % self.num_players
            if self.clock:
                self.clock.start(self.current)

    def _finish(self, winner: int, reason: str) -> None:
        self.winner = winner
        self.end_reason = reason
        if self.clock:
            self.clock.stop()
