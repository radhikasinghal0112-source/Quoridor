"""The terminal interface: title screen, command prompt, screen redraws."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable, Optional

from .board import IllegalMove, IllegalWall
from .game import CannotUndo, ChessClock, Game
from .notation import parse_cell, parse_wall
from .render import BOLD, GREEN, RED, paint, render_board, render_status

CLEAR_SCREEN = "\033[2J\033[H"

TITLE = """  QUORIDOR

  Be the first to reach the opposite side of the board.
  On your turn, move one cell or place a wall to slow
  your opponents down. A wall is two cells long, and you
  may not seal anyone in completely.

  {green} is the player whose turn it is, {red} are the
  opponents. Type help during the game for the commands."""

HELP = """  Commands
    move <cell>       Move to a neighbouring cell, e.g. move e5   (short: m e5)
    wall <cell> h|v   Place a wall, e.g. wall d3 h                (short: w d3 h)
    flip              Turn the board around each turn on or off (two players)
    help              Show this list
    history           Show every move so far
    undo              Take back the last turn (time is not refunded)
    resign            Give up the game (two player games)
    quit              Leave the game

  Cells are a column letter and a row number, like e5. Row 1 is at the top.
  A wall named d3 h lies just below cells d3 and e3. A wall named d3 v lies
  just to the right of cells d3 and d4."""


@dataclass
class View:
    """How the board is shown. With flip on, each player sees their own side at the bottom."""

    flip: bool = True

    def flipped_for(self, game: Game) -> bool:
        # Player 1 starts at the top, so only their turns need the board turned around.
        return self.flip and game.num_players == 2 and game.current == 0 and game.winner is None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quoridor", description="Play Quoridor in the terminal.")
    parser.add_argument("--players", type=int, choices=(2, 4), default=2, help="number of players (default 2)")
    parser.add_argument("--walls", type=int, default=None, help="walls per player (default 10 for two players, 5 for four)")
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument("--time", type=float, default=None, metavar="MINUTES", help="minutes per player on the clock (two players only); skips the time limit question")
    timing.add_argument("--untimed", action="store_true", help="play without a clock; skips the time limit question")
    parser.add_argument("--increment", type=float, default=0, metavar="SECONDS", help="seconds added to a player's clock after each move")
    parser.add_argument("--no-color", "--no-colour", dest="no_colour", action="store_true", help="turn colours off")
    parser.add_argument("--no-flip", action="store_true", help="keep the board the same way up instead of turning it for each player")
    parser.add_argument("--no-clear", action="store_true", help="do not clear the screen between turns")
    return parser


TIME_CHOICES = {"1": None, "2": 5, "3": 10}


def choose_time_limit(read: Callable[[str], str], say: Callable[[str], None]) -> Optional[int]:
    """Ask for the minutes each player gets. Returns None for no time limit."""
    say("")
    say("  Time limit for each player:")
    say("    1) No time limit")
    say("    2) 5 minutes")
    say("    3) 10 minutes")
    while True:
        choice = read("  Enter your choice [1]: ").strip() or "1"
        if choice in TIME_CHOICES:
            return TIME_CHOICES[choice]
        say("  Please enter 1, 2 or 3.")


def make_game(args: argparse.Namespace, minutes: Optional[float]) -> Game:
    clock = None
    if minutes is not None and args.players == 2:
        clock = ChessClock(minutes, args.increment, players=2)
    return Game(args.players, args.walls, clock)


def banner(game: Game) -> str:
    winner = game.winner + 1
    if game.end_reason == "time":
        return f"Player {game.loser() + 1} ran out of time. Player {winner} wins!"
    if game.end_reason == "resign":
        return f"Player {game.loser() + 1} resigned. Player {winner} wins!"
    return f"Player {winner} wins by reaching the far side!"


def execute(game: Game, line: str, say: Callable[[str], None], view: Optional[View] = None) -> str:
    """Run one typed command. Returns "turn", "redraw", "stay" or "quit"."""
    words = line.lower().split()
    if not words:
        return "stay"
    command, rest = words[0], words[1:]

    if command in ("move", "m"):
        if len(rest) != 1:
            say("Usage: move <cell>, for example: move e5")
            return "stay"
        try:
            game.move(parse_cell(rest[0]))
        except (ValueError, IllegalMove) as error:
            say(str(error))
            return "stay"
        return "turn"

    if command in ("wall", "w"):
        if len(rest) != 2:
            say("Usage: wall <cell> h|v, for example: wall d3 h")
            return "stay"
        try:
            game.place_wall(parse_wall(rest[0], rest[1]))
        except (ValueError, IllegalWall) as error:
            say(str(error))
            return "stay"
        return "turn"

    if command == "flip":
        if game.num_players != 2:
            say("The board only turns around in two player games.")
            return "stay"
        if view is not None:
            view.flip = not view.flip
        return "redraw"

    if command == "help":
        say(HELP)
    elif command == "history":
        if not game.log:
            say("No moves yet.")
        for number, entry in enumerate(game.log, start=1):
            say(f"  {number:>3}. {entry}")
    elif command == "undo":
        try:
            game.undo()
        except CannotUndo as error:
            say(str(error))
            return "stay"
        return "turn"
    elif command == "resign":
        try:
            game.resign()
        except IllegalMove as error:
            say(str(error))
            return "stay"
        return "turn"
    elif command in ("quit", "exit"):
        return "quit"
    else:
        say(f"I don't know '{command}'. Type help to see the commands.")
    return "stay"


def play(
    game: Game,
    use_colour: bool,
    clear: bool,
    read: Callable[[str], str],
    say: Callable[[str], None],
    view: Optional[View] = None,
) -> bool:
    """Play one game. Returns False if the players chose to quit."""
    view = view or View(flip=False)
    while game.winner is None:
        if clear:
            sys.stdout.write(CLEAR_SCREEN)
        say("  QUORIDOR")
        say("")
        marks = game.board.legal_moves(game.current)
        say(render_board(game.board, game.current, marks, use_colour, view.flipped_for(game)))
        say("")
        say(render_status(game, use_colour))
        say("")
        if game.last_move:
            say(f"  Last move: {game.last_move}")
        say("  • = cells you can move to      (type help for commands)")
        say("")

        outcome = "stay"
        while outcome == "stay" and game.winner is None:
            try:
                line = read(f"Player {game.current + 1} > ")
            except EOFError:
                return False
            outcome = execute(game, line, say, view)
        if outcome == "quit":
            return False

    if clear:
        sys.stdout.write(CLEAR_SCREEN)
    say(render_board(game.board, None, (), use_colour))
    say("")
    say(paint(banner(game), BOLD + GREEN, use_colour))
    say("")
    return True


def main(
    argv: Optional[list[str]] = None,
    read: Callable[[str], str] = input,
    say: Callable[[str], None] = print,
) -> int:
    args = build_parser().parse_args(argv)
    if args.time is not None and args.players == 4:
        say("Note: the clock is only available in two player games, so it is switched off.")

    use_colour = not args.no_colour and "NO_COLOR" not in os.environ and sys.stdout.isatty()
    clear = not args.no_clear and sys.stdout.isatty()
    if os.name == "nt":
        os.system("")  # lets older Windows terminals understand colour codes

    say(TITLE.format(green=paint("Green", GREEN, use_colour), red=paint("red", RED, use_colour)))
    try:
        read("\n  Press Enter to start. ")
    except EOFError:
        return 0

    minutes = args.time
    if args.players == 2 and args.time is None and not args.untimed:
        if clear:
            sys.stdout.write(CLEAR_SCREEN)
            say("  QUORIDOR")
        try:
            minutes = choose_time_limit(read, say)
        except EOFError:
            return 0

    view = View(flip=not args.no_flip)
    while True:
        game = make_game(args, minutes)
        if not play(game, use_colour, clear, read, say, view):
            break
        try:
            again = read("Play again? (y/n) ").strip().lower()
        except EOFError:
            break
        if again not in ("y", "yes"):
            break
    return 0
