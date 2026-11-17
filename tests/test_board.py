import pytest

from quoridor.board import Board, IllegalMove, IllegalWall, Wall


def H(row, col):
    return Wall("H", row, col)


def V(row, col):
    return Wall("V", row, col)


# ----- setup and goals -----------------------------------------------------

def test_two_player_start():
    board = Board(2)
    assert board.pawns == [(0, 4), (8, 4)]
    assert board.walls_left == [10, 10]


def test_four_player_start_is_clockwise_from_the_top():
    board = Board(4)
    assert board.pawns == [(0, 4), (4, 8), (8, 4), (4, 0)]
    assert board.walls_left == [5, 5, 5, 5]


def test_custom_wall_count():
    assert Board(2, walls_per_player=3).walls_left == [3, 3]


def test_invalid_setup():
    with pytest.raises(ValueError):
        Board(3)
    with pytest.raises(ValueError):
        Board(2, walls_per_player=-1)


def test_goals_two_players():
    board = Board(2)
    assert board.is_goal(0, (8, 0)) and board.is_goal(0, (8, 8))
    assert not board.is_goal(0, (7, 4))
    assert board.is_goal(1, (0, 3)) and not board.is_goal(1, (1, 3))


def test_goals_four_players():
    board = Board(4)
    assert board.is_goal(0, (8, 2))   # top starter heads to the bottom
    assert board.is_goal(1, (5, 0))   # right starter heads to the left
    assert board.is_goal(2, (0, 7))   # bottom starter heads to the top
    assert board.is_goal(3, (3, 8))   # left starter heads to the right
    assert not board.is_goal(1, (0, 4))


def test_has_won():
    board = Board(2)
    assert not board.has_won(0)
    board.pawns[0] = (8, 2)
    assert board.has_won(0)


# ----- ordinary moves ------------------------------------------------------

def test_basic_moves():
    board = Board(2)
    board.move(0, (1, 4))
    assert board.pawns[0] == (1, 4)
    board.move(0, (1, 3))
    board.move(0, (1, 4))
    assert board.pawns[0] == (1, 4)


def test_cannot_leave_the_board():
    board = Board(2)
    with pytest.raises(IllegalMove, match="off the board"):
        board.move(0, (-1, 4))
    board.pawns[0] = (0, 0)
    assert (0, -1) not in board.legal_moves(0)
    assert (-1, 0) not in board.legal_moves(0)


def test_cannot_move_far_or_diagonally():
    board = Board(2)
    for cell in [(2, 4), (1, 3), (1, 5), (0, 6)]:
        with pytest.raises(IllegalMove):
            board.move(0, cell)


def test_cannot_stay_put():
    with pytest.raises(IllegalMove):
        Board(2).move(0, (0, 4))


def test_wall_blocks_a_move():
    board = Board(2)
    board.place_wall(1, H(0, 3))     # between rows 1 and 2, covering columns d and e
    with pytest.raises(IllegalMove, match="wall"):
        board.move(0, (1, 4))
    assert board.legal_moves(0) == [(0, 3), (0, 5)]


def test_cannot_step_onto_a_pawn():
    board = Board(2)
    board.pawns = [(4, 4), (5, 4)]
    with pytest.raises(IllegalMove, match="pawn"):
        board.move(0, (5, 4))


# ----- jumping -------------------------------------------------------------

def test_straight_jump():
    board = Board(2)
    board.pawns = [(4, 4), (5, 4)]
    assert set(board.legal_moves(0)) == {(3, 4), (4, 3), (4, 5), (6, 4)}
    board.move(0, (6, 4))
    assert board.pawns[0] == (6, 4)


def test_straight_jump_works_sideways_too():
    board = Board(2)
    board.pawns = [(4, 4), (4, 5)]
    assert (4, 6) in board.legal_moves(0)


def test_diagonal_when_a_wall_is_behind_the_pawn():
    board = Board(2)
    board.pawns = [(4, 4), (5, 4)]
    board.place_wall(1, H(5, 4))     # directly behind the other pawn
    assert set(board.legal_moves(0)) == {(3, 4), (4, 3), (4, 5), (5, 3), (5, 5)}


def test_diagonal_when_the_edge_is_behind_the_pawn():
    board = Board(2)
    board.pawns = [(7, 4), (8, 4)]
    assert set(board.legal_moves(0)) == {(6, 4), (7, 3), (7, 5), (8, 3), (8, 5)}


def test_diagonal_blocked_by_a_wall_beside_the_pawn():
    board = Board(2)
    board.pawns = [(4, 4), (5, 4)]
    board.place_wall(1, H(5, 4))     # behind the other pawn
    board.place_wall(1, V(5, 3))     # between (5, 3) and (5, 4)
    assert set(board.legal_moves(0)) == {(3, 4), (4, 3), (4, 5), (5, 5)}


def test_no_jump_through_a_wall_between_the_pawns():
    board = Board(2)
    board.pawns = [(4, 4), (5, 4)]
    board.place_wall(1, H(4, 4))     # between the two pawns
    assert set(board.legal_moves(0)) == {(3, 4), (4, 3), (4, 5)}


def test_pawn_behind_a_pawn_gives_diagonals_in_four_player_games():
    board = Board(4)
    board.pawns = [(4, 4), (5, 4), (6, 4), (0, 0)]
    assert set(board.legal_moves(0)) == {(3, 4), (4, 3), (4, 5), (5, 3), (5, 5)}


# ----- placing walls -------------------------------------------------------

@pytest.mark.parametrize(
    "wall",
    [H(-1, 0), H(8, 0), H(0, 8), H(0, -1), V(-1, 0), V(8, 0), V(0, 8), V(0, -1)],
)
def test_walls_must_sit_inside_the_board(wall):
    with pytest.raises(IllegalWall, match="inside the board"):
        Board(2).place_wall(0, wall)


@pytest.mark.parametrize("wall", [H(0, 0), H(7, 7), V(0, 0), V(7, 7), H(0, 7), V(7, 0)])
def test_walls_in_every_corner_are_allowed(wall):
    board = Board(2)
    board.place_wall(0, wall)
    assert wall in board.walls


def test_unknown_orientation_is_rejected():
    with pytest.raises(IllegalWall):
        Board(2).place_wall(0, Wall("X", 0, 0))


def test_horizontal_wall_blocks_two_edges():
    board = Board(2)
    board.place_wall(0, H(3, 3))
    assert not board.can_step((3, 3), (4, 3))
    assert not board.can_step((3, 4), (4, 4))
    assert not board.can_step((4, 3), (3, 3))
    assert board.can_step((3, 5), (4, 5))
    assert board.can_step((3, 2), (4, 2))
    assert board.can_step((3, 3), (3, 4))   # sideways along the wall is fine


def test_vertical_wall_blocks_two_edges():
    board = Board(2)
    board.place_wall(0, V(3, 3))
    assert not board.can_step((3, 3), (3, 4))
    assert not board.can_step((4, 3), (4, 4))
    assert board.can_step((5, 3), (5, 4))
    assert board.can_step((2, 3), (2, 4))
    assert board.can_step((3, 3), (4, 3))   # up and down along the wall is fine


def test_horizontal_walls_overlap():
    board = Board(2)
    board.place_wall(0, H(3, 3))
    with pytest.raises(IllegalWall, match="already"):
        board.place_wall(0, H(3, 3))
    with pytest.raises(IllegalWall, match="overlap"):
        board.place_wall(0, H(3, 4))
    with pytest.raises(IllegalWall, match="overlap"):
        board.place_wall(0, H(3, 2))


def test_horizontal_walls_that_only_touch_or_sit_in_other_rows_are_fine():
    board = Board(2)
    board.place_wall(0, H(3, 3))
    for wall in [H(3, 5), H(3, 1), H(2, 3), H(4, 3), H(2, 5), H(4, 1)]:
        board.place_wall(0, wall)


def test_vertical_walls_overlap():
    board = Board(2)
    board.place_wall(0, V(3, 3))
    with pytest.raises(IllegalWall, match="overlap"):
        board.place_wall(0, V(4, 3))
    with pytest.raises(IllegalWall, match="overlap"):
        board.place_wall(0, V(2, 3))


def test_vertical_walls_that_only_touch_or_sit_in_other_columns_are_fine():
    board = Board(2)
    board.place_wall(0, V(3, 3))
    for wall in [V(5, 3), V(1, 3), V(3, 4), V(3, 2), V(5, 4), V(1, 2)]:
        board.place_wall(0, wall)


def test_walls_cannot_cross():
    board = Board(2)
    board.place_wall(0, H(3, 3))
    with pytest.raises(IllegalWall, match="cross"):
        board.place_wall(0, V(3, 3))

    board = Board(2)
    board.place_wall(0, V(3, 3))
    with pytest.raises(IllegalWall, match="cross"):
        board.place_wall(0, H(3, 3))


def test_t_shapes_and_corner_contacts_are_allowed():
    board = Board(2)
    board.place_wall(0, H(3, 3))          # covers columns 3 and 4, ending at corners (3, 2) and (3, 4)
    board.place_wall(0, V(3, 4))          # centred on the right end corner: a T
    board.place_wall(0, V(2, 2))          # its lower end touches the left end corner: an L
    board.place_wall(0, V(4, 2))          # continues that line downwards, end to end


def test_wall_count_goes_down_and_runs_out():
    board = Board(2, walls_per_player=2)
    board.place_wall(0, H(1, 0))
    assert board.walls_left == [1, 2]
    board.place_wall(0, H(1, 2))
    assert board.walls_left == [0, 2]
    with pytest.raises(IllegalWall, match="no walls left"):
        board.place_wall(0, H(1, 4))
    board.place_wall(1, H(1, 4))           # the other player can still place walls
    assert board.walls_left == [0, 1]


def test_rejected_walls_cost_nothing_and_change_nothing():
    board = Board(2)
    board.place_wall(0, H(3, 3))
    walls, blocked = set(board.walls), set(board.blocked)
    with pytest.raises(IllegalWall):
        board.place_wall(0, V(3, 3))
    assert board.walls_left == [9, 10]
    assert board.walls == walls and board.blocked == blocked


# ----- the "no sealing anyone in" rule -------------------------------------

def build_barrier_with_one_gap(board):
    """Closes row 4 off from row 5 except for a single doorway at column i."""
    for wall in [H(3, 0), H(3, 2), H(3, 4), H(3, 6), H(2, 7)]:
        board.place_wall(0, wall)


def test_a_wall_that_traps_a_player_is_rejected():
    board = Board(2)
    build_barrier_with_one_gap(board)
    assert board.has_route(0) and board.has_route(1)

    walls, blocked, left = set(board.walls), set(board.blocked), list(board.walls_left)
    with pytest.raises(IllegalWall, match="no way to reach"):
        board.place_wall(0, V(3, 7))       # would seal the last doorway

    assert board.walls == walls
    assert board.blocked == blocked
    assert board.walls_left == left


def test_a_similar_wall_that_leaves_a_route_is_accepted():
    board = Board(2)
    build_barrier_with_one_gap(board)
    board.place_wall(0, V(5, 7))           # nowhere near the doorway
    assert board.has_route(0)


def test_pawns_do_not_count_as_blocking_a_route():
    board = Board(2)
    board.pawns = [(0, 4), (1, 4)]
    board.place_wall(0, H(0, 3))
    assert board.has_route(0)


def test_every_player_is_checked_in_a_four_player_game():
    board = Board(4, walls_per_player=10)
    for wall in [H(3, 0), H(3, 2), H(3, 4), H(3, 6), H(2, 7)]:
        board.place_wall(0, wall)
    # Player 1 (top) and player 3 (bottom) are separated by the barrier but both
    # can still get through the doorway, so this wall is the one that must fail.
    with pytest.raises(IllegalWall):
        board.place_wall(0, V(3, 7))


def test_copy_is_independent():
    board = Board(2)
    clone = board.copy()
    clone.place_wall(0, H(3, 3))
    clone.move(0, (1, 4))
    assert board.walls == set() and board.pawns[0] == (0, 4)
