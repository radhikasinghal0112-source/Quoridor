import pytest

from quoridor.board import IllegalMove, IllegalWall, Wall
from quoridor.game import CannotUndo, ChessClock, Game, GameOver


class FakeTime:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_players_alternate_and_the_log_records_turns():
    game = Game(2)
    assert game.current == 0
    game.move((1, 4))
    assert game.current == 1
    game.place_wall(Wall("H", 5, 0))
    assert game.current == 0
    assert game.log == ["Player 1 moved to e2", "Player 2 placed a wall at a6 h"]
    assert game.last_move == "Player 2 placed a wall at a6 h"


def test_four_players_take_turns_in_order():
    game = Game(4)
    seen = []
    for cell in [(1, 4), (4, 7), (7, 4), (4, 1)]:
        seen.append(game.current)
        game.move(cell)
    assert seen == [0, 1, 2, 3]
    assert game.current == 0


def test_an_illegal_action_leaves_the_turn_alone():
    game = Game(2)
    with pytest.raises(IllegalMove):
        game.move((5, 5))
    with pytest.raises(IllegalWall):
        game.place_wall(Wall("H", 9, 9))
    assert game.current == 0
    assert game.log == []
    assert game.board.pawns[0] == (0, 4)
    assert game.board.walls_left == [10, 10]


def test_reaching_the_far_side_wins():
    game = Game(2)
    game.board.pawns = [(7, 4), (8, 0)]
    game.move((8, 4))
    assert game.winner == 0
    assert game.end_reason == "reached"
    assert game.loser() == 1
    with pytest.raises(GameOver):
        game.move((8, 3))
    with pytest.raises(GameOver):
        game.place_wall(Wall("H", 1, 1))


def test_four_player_winner_is_the_one_who_reaches_their_own_goal():
    game = Game(4)
    game.board.pawns = [(0, 4), (4, 1), (8, 4), (4, 7)]
    game.current = 1
    game.move((4, 0))
    assert game.winner == 1
    assert game.loser() is None  # only defined for two players


def test_undo_restores_everything():
    game = Game(2)
    game.move((1, 4))
    before = (list(game.board.pawns), list(game.board.walls_left), game.current, list(game.log), game.last_move)
    game.place_wall(Wall("H", 5, 0))
    game.undo()
    after = (list(game.board.pawns), list(game.board.walls_left), game.current, list(game.log), game.last_move)
    assert after == before
    assert game.board.walls == set()
    game.undo()
    assert game.board.pawns[0] == (0, 4) and game.current == 0 and game.log == []


def test_undo_with_nothing_to_undo():
    with pytest.raises(CannotUndo):
        Game(2).undo()


def test_undo_after_the_game_is_over():
    game = Game(2)
    game.board.pawns = [(7, 4), (8, 0)]
    game.move((8, 4))
    with pytest.raises(CannotUndo):
        game.undo()


def test_resign():
    game = Game(2)
    game.move((1, 4))
    game.resign()      # player 2 resigns
    assert game.winner == 0
    assert game.end_reason == "resign"
    assert game.loser() == 1


def test_resign_is_two_player_only():
    with pytest.raises(IllegalMove):
        Game(4).resign()


# ----- the clock -----------------------------------------------------------

def make_timed_game(minutes=1, increment=0):
    fake = FakeTime()
    clock = ChessClock(minutes, increment, players=2, time_source=fake)
    return Game(2, clock=clock), fake


def test_clock_charges_the_player_who_moved():
    game, fake = make_timed_game(minutes=1)
    fake.now += 30
    game.move((1, 4))
    fake.now += 10
    game.move((7, 4))
    assert game.clock.remaining == [30.0, 50.0]


def test_time_left_includes_the_running_turn():
    game, fake = make_timed_game(minutes=1)
    fake.now += 15
    assert game.clock.time_left(0) == 45
    assert game.clock.time_left(1) == 60


def test_failed_attempts_still_cost_time():
    game, fake = make_timed_game(minutes=1)
    fake.now += 20
    with pytest.raises(IllegalMove):
        game.move((5, 5))
    fake.now += 10
    game.move((1, 4))
    assert game.clock.remaining[0] == 30


def test_increment_is_added_after_each_move():
    game, fake = make_timed_game(minutes=1, increment=5)
    fake.now += 10
    game.move((1, 4))
    assert game.clock.remaining[0] == 55


def test_running_out_of_time_loses_and_the_action_does_not_count():
    game, fake = make_timed_game(minutes=1)
    fake.now += 61
    game.move((1, 4))
    assert game.winner == 1
    assert game.end_reason == "time"
    assert game.loser() == 0
    assert game.board.pawns[0] == (0, 4)


def test_exactly_zero_counts_as_out_of_time():
    game, fake = make_timed_game(minutes=1)
    fake.now += 60
    assert game.clock.flagged(0)


def test_undo_does_not_refund_time():
    game, fake = make_timed_game(minutes=1)
    fake.now += 20
    game.move((1, 4))
    game.undo()
    assert game.clock.remaining[0] == 40
    assert game.current == 0
