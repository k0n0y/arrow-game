"""Independent examples, boundary cases, and exhaustive solvability checks."""

from functools import lru_cache
from itertools import product

import pytest

from game_logic import (Game, Level, State, available_moves, can_exit,
                        count_arrows, generate_level, is_solvable, solve,
                        validate_board)


@pytest.mark.parametrize("board,pos", [
    (["R..."], (0, 0)), (["...L"], (0, 3)),
    (["D", ".", ".", "."], (0, 0)), ([".", ".", ".", "U"], (3, 0)),
])
def test_T01_clear_path_all_directions(board, pos):
    assert can_exit(board, *pos)


@pytest.mark.parametrize("board,pos", [
    (["R..U"], (0, 0)), (["D..L"], (0, 3)),
    (["D", ".", ".", "L"], (0, 0)), (["R", ".", ".", "U"], (3, 0)),
])
def test_T02_distant_obstacle_all_directions(board, pos):
    assert not can_exit(board, *pos)


@pytest.mark.parametrize("board,pos", [
    (["UR", "LD"], (0, 0)), (["UR", "LD"], (0, 1)),
    (["UR", "LD"], (1, 0)), (["UR", "LD"], (1, 1)),
])
def test_T03_outward_edge(board, pos):
    assert can_exit(board, *pos)


@pytest.fixture
def game():
    return Game([Level("a", "", ("RU", ".D")), Level("b", "", ("U.", "LR"))])


def test_T02_lives_decrement_without_removal(game):
    game.start()
    before = [row[:] for row in game.board]
    assert game.click(0, 0).kind == "blocked"
    assert game.board == before
    assert game.lives == 2


def test_T04_win_next_and_final(game):
    game.start()
    for r, c in solve(game.board):
        assert game.click(r, c).kind == "removed"
    assert game.state is State.WON
    assert game.next_level()
    assert game.level_index == 1 and game.lives == 3
    for r, c in solve(game.board):
        game.click(r, c)
    assert game.state is State.COMPLETE
    assert not game.next_level()


def test_T05_failure_freezes_board_and_retry(game):
    game.start()
    for _ in range(3):
        game.click(0, 0)
    assert game.state is State.LOST and game.lives == 0
    assert game.click(0, 1).kind == "ignored"
    assert game.lives == 0 and count_arrows(game.board) == 3
    game.restart()
    assert game.state is State.PLAYING and game.lives == 3


def test_T06_restart_restores_current_level_and_template(game):
    game.start(1)
    original = tuple("".join(row) for row in game.board)
    game.click(0, 0)
    game.hint()
    game.restart()
    assert game.level_index == 1
    assert tuple("".join(row) for row in game.board) == original
    assert game.levels[1].rows == original
    assert (game.lives, game.moves, game.hints) == (3, 0, 0)


@pytest.mark.parametrize("pos", [(-1, 0), (0, -1), (2, 0), (0, 2), (1, 0)])
def test_empty_and_invalid_click_do_not_cost_lives(game, pos):
    game.start()
    assert game.click(*pos).kind == "ignored"
    assert game.lives == 3 and game.moves == 0


def test_menu_and_midgame_cannot_advance(game):
    assert not game.next_level()
    assert game.click(0, 0).kind == "ignored"
    game.start()
    assert not game.next_level()
    game.to_menu()
    assert game.state is State.MENU


def test_empty_and_single_cell_board():
    assert not can_exit([], 0, 0)
    assert not can_exit(["."], 0, 0)
    for direction in "UDLR":
        assert can_exit([direction], 0, 0)
    assert solve([]) == []
    assert solve(["."]) == []


@pytest.mark.parametrize("board", [[], [""], ["U", "RR"], ["X"]])
def test_reject_invalid_level_data(board):
    with pytest.raises(ValueError):
        validate_board(board)


def test_deadlock_and_non_mutation():
    board = [list("RL")]
    assert solve(board) is None
    assert board == [list("RL")]
    with pytest.raises(ValueError):
        Game([Level("deadlock", "", ("RL",))])


def test_all_official_levels_have_four_directions_and_solution():
    from levels import LEVELS
    assert len(LEVELS) >= 3
    for level, expected in zip(LEVELS, (11, 18, 27)):
        assert set("UDLR") <= set("".join(level.rows))
        assert count_arrows(level.rows) == expected
        assert len(solve(level.rows)) == expected


@pytest.mark.parametrize("size,count", [(4, 11), (5, 18), (6, 27)])
def test_generated_levels_solvable(size, count):
    for seed in range(15):
        board = generate_level(size, count, seed)
        original = tuple(board)
        solution = solve(board)
        assert solution is not None and len(solution) == count
        assert board == original
        work = [list(row) for row in board]
        for r, c in solution:
            assert can_exit(work, r, c)
            work[r][c] = "."
        assert count_arrows(work) == 0


def test_all_625_two_by_two_boards_against_independent_search():
    # The oracle uses slicing and recursive search, not can_exit/solve.
    def reference_exits(state, i):
        r, c = divmod(i, 2)
        rays = {
            "U": [state[rr * 2 + c] for rr in range(r)],
            "D": [state[rr * 2 + c] for rr in range(r + 1, 2)],
            "L": [state[r * 2 + cc] for cc in range(c)],
            "R": [state[r * 2 + cc] for cc in range(c + 1, 2)],
        }
        return state[i] in rays and all(x == "." for x in rays[state[i]])

    @lru_cache(None)
    def reference_solvable(state):
        if state == "....":
            return True
        return any(reference_exits(state, i)
                   and reference_solvable(state[:i] + "." + state[i + 1:])
                   for i in range(4))

    for cells in product(".UDLR", repeat=4):
        state = "".join(cells)
        board = (state[:2], state[2:])
        for i in range(4):
            assert can_exit(board, *divmod(i, 2)) == reference_exits(state, i)
        assert is_solvable(board) == reference_solvable(state)
