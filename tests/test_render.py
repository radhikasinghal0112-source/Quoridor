from quoridor.board import Board, Wall
from quoridor.game import ChessClock, Game
from quoridor.render import GREEN, RED, RESET, format_time, render_board, render_status


def lines_of(board, **kwargs):
    return render_board(board, **kwargs).split("\n")


def test_empty_board_layout():
    lines = lines_of(Board(2))
    assert len(lines) == 20
    assert lines[0] == "      a b c d e f g h i"
    assert lines[1] == "    ┌───────────────────┐"
    assert lines[2] == "  1 │ · · · · 1 · · · · │"
    assert lines[3] == "    │                   │"
    assert lines[18] == "  9 │ · · · · 2 · · · · │"
    assert lines[19] == "    └───────────────────┘"
    assert all(len(line) == len(lines[1]) for line in lines[1:])


def test_row_numbers_run_down_the_side():
    lines = lines_of(Board(2))
    for row in range(9):
        assert lines[2 + 2 * row].startswith(f"  {row + 1} │")


def test_four_player_pawns():
    lines = lines_of(Board(4))
    assert lines[2][14] == "1"        # top middle
    assert lines[18][14] == "3"       # bottom middle
    assert lines[10][6] == "4"        # left middle
    assert lines[10][22] == "2"       # right middle


def test_move_markers():
    board = Board(2)
    lines = lines_of(board, current=0, marks=board.legal_moves(0))
    assert sum(line.count("•") for line in lines) == 3
    assert lines[2] == "  1 │ · · · • 1 • · · · │"


def test_horizontal_wall_is_drawn_between_the_rows_it_separates():
    board = Board(2)
    board.place_wall(0, Wall("H", 2, 2))        # below row 3, under columns c and d
    lines = lines_of(board)
    assert lines[7] == "    │     ━━━           │"
    assert sum(line.count("━") for line in lines) == 3


def test_vertical_wall_is_drawn_between_the_columns_it_separates():
    board = Board(2)
    board.place_wall(0, Wall("V", 4, 3))        # right of column d, beside rows 5 and 6
    lines = lines_of(board)
    assert [line[13] for line in lines[10:14]] == ["┃", "┃", "┃", " "]
    assert sum(line.count("┃") for line in lines) == 3


def test_colours():
    board = Board(2)
    shown = render_board(board, current=0, marks=board.legal_moves(0), use_colour=True)
    assert f"{GREEN}1{RESET}" in shown
    assert f"{RED}2{RESET}" in shown
    assert f"{GREEN}•{RESET}" in shown


def test_no_colour_codes_when_colour_is_off():
    assert "\033" not in render_board(Board(2), current=0, marks=[(1, 4)], use_colour=False)


def test_status_without_a_clock():
    status = render_status(Game(2))
    assert status.split("\n") == [
        "  ▶ Player 1    walls left: 10",
        "    Player 2    walls left: 10",
    ]


def test_status_follows_the_current_player_and_wall_counts():
    game = Game(2)
    game.place_wall(Wall("H", 1, 1))
    status = render_status(game).split("\n")
    assert status[0] == "    Player 1    walls left: 9"
    assert status[1] == "  ▶ Player 2    walls left: 10"


def test_status_with_a_clock():
    game = Game(2, clock=ChessClock(10))
    assert "time: 10:00" in render_status(game)


def test_format_time():
    assert format_time(600) == "10:00"
    assert format_time(59.9) == "0:59"
    assert format_time(61) == "1:01"
    assert format_time(0) == "0:00"


def test_flipped_board_turns_half_a_turn():
    lines = lines_of(Board(2), flip=True)
    assert lines[0] == "      i h g f e d c b a"
    assert lines[2] == "  9 │ · · · · 2 · · · · │"
    assert lines[18] == "  1 │ · · · · 1 · · · · │"
    for row in range(9):
        assert lines[2 + 2 * row].startswith(f"  {9 - row} │")


def test_flipped_board_still_shows_walls_in_the_right_place():
    board = Board(2)
    board.place_wall(0, Wall("H", 7, 4))   # e8 h: below e8 and f8
    board.place_wall(1, Wall("V", 7, 3))   # d8 v: right of d8 and d9
    # Turning the board is the same as reading the drawing of the walls from the other end.
    plain, turned = lines_of(board), lines_of(board, flip=True)
    assert turned[3] == "    │       ━━━┃        │"
    assert turned[4] == "  8 │ · · · · ·┃· · · · │"
    assert [line.count("━") for line in plain[2:-1]] == [line.count("━") for line in turned[2:-1]][::-1]
    assert [line.count("┃") for line in plain[2:-1]] == [line.count("┃") for line in turned[2:-1]][::-1]
