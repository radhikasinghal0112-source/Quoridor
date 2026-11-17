from quoridor.pathfinding import has_path, shortest_path_length


def open_board(a, b):
    return all(0 <= x < 9 for x in a + b) and abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_straight_line_distance():
    assert shortest_path_length((0, 4), lambda c: c[0] == 8, open_board) == 8


def test_already_at_goal():
    assert shortest_path_length((8, 0), lambda c: c[0] == 8, open_board) == 0


def test_detour_around_a_wall():
    # No step between row 3 and row 4 except in the last column.
    def can_step(a, b):
        if not open_board(a, b):
            return False
        crossing = {a[0], b[0]} == {3, 4}
        return not crossing or a[1] == 8

    assert has_path((0, 0), lambda c: c[0] == 8, can_step)
    assert shortest_path_length((0, 0), lambda c: c[0] == 8, can_step) == 16


def test_no_route():
    def can_step(a, b):
        return open_board(a, b) and {a[0], b[0]} != {3, 4}

    assert shortest_path_length((0, 0), lambda c: c[0] == 8, can_step) is None
    assert not has_path((0, 0), lambda c: c[0] == 8, can_step)
