from quoridor.cli import main


def run(inputs, *flags):
    feed = iter(inputs)
    out = []

    def read(prompt):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError

    extra = [] if "--time" in flags else ["--untimed"]
    code = main(["--no-color", "--no-clear", *extra, *flags], read=read, say=out.append)
    assert code == 0
    return "\n".join(out)


def run_with_menu(inputs, *flags):
    """Like run, but leaves the time limit question switched on."""
    feed = iter(inputs)
    out = []
    asked = []

    def read(prompt):
        asked.append(prompt)
        try:
            return next(feed)
        except StopIteration:
            raise EOFError

    code = main(["--no-color", "--no-clear", *flags], read=read, say=out.append)
    assert code == 0
    return "\n".join(out), asked


def test_a_whole_game_to_the_far_side():
    inputs = [""]  # press Enter at the title screen
    # Player 1 walks straight down; player 2 steps aside and walks up another column.
    p1 = [f"m e{r}" for r in range(2, 10)]
    p2 = ["m d9"] + [f"m d{r}" for r in range(8, 2, -1)]
    for a, b in zip(p1, p2 + [None]):
        inputs.append(a)
        if b:
            inputs.append(b)
    inputs.append("n")
    shown = run(inputs)
    assert "Player 1 wins by reaching the far side!" in shown
    assert "Last move: Player 2 moved to d3" in shown


def test_title_help_and_errors():
    shown = run(["", "help", "dance", "move", "move z9", "move e5", "wall d3", "wall d3 x", "undo", "quit"])
    assert "QUORIDOR" in shown
    assert "Commands" in shown
    assert "I don't know 'dance'" in shown
    assert "Usage: move <cell>" in shown
    assert "'z9' is not a cell" in shown
    assert "neighbouring cell" in shown          # e5 is too far away
    assert "Usage: wall <cell> h|v" in shown
    assert "either h (horizontal) or v (vertical)" in shown
    assert "nothing to undo" in shown


def test_wall_command_changes_the_wall_count_and_log():
    shown = run(["", "w d3 h", "history", "quit"])
    assert "Last move: Player 1 placed a wall at d3 h" in shown
    assert "Player 1    walls left: 9" in shown
    assert "1. Player 1 placed a wall at d3 h" in shown


def test_illegal_wall_message_reaches_the_player():
    shown = run(["", "wall d3 h", "wall d3 v", "quit"])   # second turn: same corner, so it crosses
    assert "That wall would cross another wall." in shown


def test_undo_takes_back_a_move():
    shown = run(["", "move e2", "undo", "quit"])
    assert shown.count("Last move: Player 1 moved to e2") == 1


def test_resign_and_play_again():
    shown = run(["", "resign", "y", "move e2", "resign", "n"])
    assert shown.count("resigned. Player") == 2
    assert "Player 1 resigned. Player 2 wins!" in shown
    assert "Player 2 resigned. Player 1 wins!" in shown


def test_resign_is_not_available_with_four_players():
    shown = run(["", "resign", "quit"], "--players", "4")
    assert "only available in two player games" in shown


def test_four_player_start_screen_has_four_pawns():
    shown = run(["", "quit"], "--players", "4")
    for pawn in "1234":
        assert pawn in shown
    assert "walls left: 5" in shown


def test_clock_is_shown_for_two_players_and_ignored_for_four():
    assert "time: 10:00" in run(["", "quit"], "--time", "10")
    shown = run(["", "quit"], "--players", "4", "--time", "10")
    assert "only available in two player games" in shown
    assert "time:" not in shown


def test_custom_wall_count():
    assert "walls left: 3" in run(["", "quit"], "--walls", "3")


def test_ending_input_early_is_not_an_error():
    run([])
    run([""])
    run(["", "move e2"])


# ----- the time limit question ---------------------------------------------

def test_menu_lists_the_three_choices():
    shown, _ = run_with_menu(["", "1", "quit"])
    assert "1) No time limit" in shown
    assert "2) 5 minutes" in shown
    assert "3) 10 minutes" in shown


def test_menu_choice_one_means_no_clock():
    shown, _ = run_with_menu(["", "1", "quit"])
    assert "time:" not in shown


def test_menu_choice_two_gives_five_minutes():
    shown, _ = run_with_menu(["", "2", "quit"])
    assert "time: 5:00" in shown


def test_menu_choice_three_gives_ten_minutes():
    shown, _ = run_with_menu(["", "3", "quit"])
    assert "time: 10:00" in shown


def test_pressing_enter_means_no_time_limit():
    shown, _ = run_with_menu(["", "", "quit"])
    assert "time:" not in shown


def test_bad_menu_answers_are_asked_again():
    shown, asked = run_with_menu(["", "7", "five", "2", "quit"])
    assert shown.count("Please enter 1, 2 or 3.") == 2
    assert "time: 5:00" in shown


def test_the_question_is_asked_once_and_kept_for_a_rematch():
    shown, asked = run_with_menu(["", "2", "resign", "y", "resign", "n"])
    question = "  Enter your choice [1]: "
    assert asked.count(question) == 1
    assert shown.count("time: 5:00") >= 2        # shown on both games' first screens


def test_time_option_skips_the_question():
    shown, asked = run_with_menu(["", "quit"], "--time", "7")
    assert "Time limit for each player" not in shown
    assert "time: 7:00" in shown


def test_untimed_option_skips_the_question():
    shown, asked = run_with_menu(["", "quit"], "--untimed")
    assert "Time limit for each player" not in shown
    assert "time:" not in shown


def test_four_player_games_are_not_asked():
    shown, asked = run_with_menu(["", "quit"], "--players", "4")
    assert "Time limit for each player" not in shown


def test_time_and_untimed_cannot_be_combined():
    import pytest

    with pytest.raises(SystemExit):
        main(["--time", "5", "--untimed"], read=lambda prompt: "", say=lambda text: None)


def test_closing_input_at_the_question_is_not_an_error():
    run_with_menu(["", ])


def rows_of(shown):
    return [line for line in shown.split("\n") if line[:3].strip().isdigit() and "│" in line]


def test_board_turns_for_player_one_and_back_for_player_two():
    shown = run([""] + ["quit"])
    first = rows_of(shown)
    assert first[0].startswith("  9 ") and first[-1].startswith("  1 ")   # player 1 at the bottom

    shown = run(["", "m e2", "quit"])
    boards = shown.split("QUORIDOR")  # one block per drawn screen, title first
    screens = [rows_of(block) for block in boards if rows_of(block)]
    assert screens[0][0].startswith("  9 ")      # player 1's turn, turned around
    assert screens[1][0].startswith("  1 ")      # player 2's turn, normal way up


def test_no_flip_keeps_the_board_the_same_way_up():
    shown = run(["", "m e2", "quit"], "--no-flip")
    assert all(rows_of(block)[0].startswith("  1 ") for block in shown.split("QUORIDOR") if rows_of(block))


def test_flip_command_switches_the_turning_off_and_on():
    shown = run(["", "flip", "flip", "quit"])
    screens = [rows_of(block) for block in shown.split("QUORIDOR") if rows_of(block)]
    assert [s[0][:3] for s in screens] == ["  9", "  1", "  9"]


def test_flip_does_nothing_in_four_player_games():
    shown = run(["", "flip", "quit"], "--players", "4")
    assert "only turns around in two player games" in shown
    assert all(rows_of(block)[0].startswith("  1 ") for block in shown.split("QUORIDOR") if rows_of(block))
