"""Pure rules for the single-cell arrow puzzle; no pygame dependency."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import Sequence

Board = Sequence[Sequence[str]]
DIRECTIONS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def validate_board(board: Board) -> None:
    """Validate once at the data boundary, not on every scanned cell."""
    if not board or not board[0]:
        raise ValueError("A level must have at least one cell")
    width = len(board[0])
    if any(len(row) != width for row in board):
        raise ValueError("A board must be rectangular")
    if any(cell not in ".UDLR" or len(cell) != 1 for row in board for cell in row):
        raise ValueError("Cells must be '.', 'U', 'D', 'L', or 'R'")


def has_arrow(board: Board, row: int, col: int) -> bool:
    return (0 <= row < len(board) and 0 <= col < len(board[row])
            and board[row][col] in DIRECTIONS)


def first_blocker(board: Board, row: int, col: int) -> tuple[int, int] | None:
    """Return the nearest obstacle on a valid arrow's entire forward ray."""
    if not has_arrow(board, row, col):
        return None
    dr, dc = DIRECTIONS[board[row][col]]
    r, c = row + dr, col + dc
    while 0 <= r < len(board) and 0 <= c < len(board[0]):
        if board[r][c] != ".":
            return r, c
        r, c = r + dr, c + dc
    return None


def can_exit(board: Board, row: int, col: int) -> bool:
    """On a rectangular board, inspect every cell ahead up to the edge."""
    return has_arrow(board, row, col) and first_blocker(board, row, col) is None


def count_arrows(board: Board) -> int:
    return sum(cell in DIRECTIONS for row in board for cell in row)


def is_level_clear(board: Board) -> bool:
    return count_arrows(board) == 0


def available_moves(board: Board) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(board) for c, _ in enumerate(row)
            if can_exit(board, r, c)]


def solve(board: Board) -> list[tuple[int, int]] | None:
    """Find a valid removal order, or None on deadlock; never mutate input.

    Removing an arrow can only remove obstacles, so any available move is safe.
    A greedy removal sequence therefore suffices; no backtracking is needed.
    """
    if not board:
        return []
    validate_board(board)
    work = [list(row) for row in board]
    order: list[tuple[int, int]] = []
    while count_arrows(work):
        moves = available_moves(work)
        if not moves:
            return None
        for r, c in moves:
            work[r][c] = "."
            order.append((r, c))
    return order


def is_solvable(board: Board) -> bool:
    return solve(board) is not None


def generate_level(size: int, arrows: int, seed: int) -> tuple[str, ...]:
    """Reverse insertion gives a guaranteed removal order (reverse insertion).

    Used to prepare the fixed levels, also available as a reproducible helper.
    It is a deterministic algorithm, not a learned AI model.
    """
    if not 2 <= size <= 10 or not 1 <= arrows <= size * size:
        raise ValueError("Require 2 <= size <= 10 and 1 <= arrows <= size**2")
    rng = Random(seed)
    for _ in range(100):
        board = [["."] * size for _ in range(size)]
        for _ in range(arrows):
            candidates = []
            for r in range(size):
                for c in range(size):
                    if board[r][c] != ".":
                        continue
                    for direction in DIRECTIONS:
                        board[r][c] = direction
                        if can_exit(board, r, c):
                            candidates.append((r, c, direction))
                    board[r][c] = "."
            if not candidates:
                break
            r, c, direction = rng.choice(candidates)
            board[r][c] = direction
        if count_arrows(board) == arrows:
            return tuple("".join(row) for row in board)
    raise RuntimeError("Unable to construct requested level")


@dataclass(frozen=True)
class Level:
    name: str
    subtitle: str
    rows: tuple[str, ...]


class State(str, Enum):
    MENU = "menu"
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"
    COMPLETE = "complete"


@dataclass(frozen=True)
class MoveResult:
    kind: str
    row: int = -1
    col: int = -1
    direction: str = "."
    blocker: tuple[int, int] | None = None


class Game:
    """State transitions independent of drawing and input devices."""

    MAX_LIVES = 3

    def __init__(self, levels: Sequence[Level]):
        if not levels:
            raise ValueError("At least one level is required")
        self.levels = tuple(levels)
        for level in levels:
            validate_board(level.rows)
            if not count_arrows(level.rows) or not is_solvable(level.rows):
                raise ValueError("Every level must be nonempty and solvable")
        self.state = State.MENU
        self.level_index = 0
        self.board: list[list[str]] = []
        self.lives = self.MAX_LIVES
        self.moves = 0
        self.hints = 0

    def start(self, index: int = 0) -> None:
        if not 0 <= index < len(self.levels):
            raise ValueError("Invalid level index")
        self.level_index = index
        self.board = [list(row) for row in self.levels[index].rows]
        self.lives = self.MAX_LIVES
        self.moves = 0
        self.hints = 0
        self.state = State.PLAYING

    def restart(self) -> None:
        self.start(self.level_index)

    def to_menu(self) -> None:
        self.state = State.MENU

    def next_level(self) -> bool:
        if self.state is not State.WON:
            return False
        self.start(self.level_index + 1)
        return True

    def hint(self) -> tuple[int, int] | None:
        if self.state is not State.PLAYING:
            return None
        moves = available_moves(self.board)
        if not moves:
            return None
        self.hints += 1
        return moves[0]

    def click(self, row: int, col: int) -> MoveResult:
        if self.state is not State.PLAYING or not has_arrow(self.board, row, col):
            return MoveResult("ignored")
        direction = self.board[row][col]
        self.moves += 1
        obstacle = first_blocker(self.board, row, col)
        if obstacle is not None:
            self.lives -= 1
            if self.lives == 0:
                self.state = State.LOST
            return MoveResult("blocked", row, col, direction, obstacle)
        self.board[row][col] = "."
        if is_level_clear(self.board):
            self.state = (State.COMPLETE if self.level_index == len(self.levels) - 1
                          else State.WON)
        return MoveResult("removed", row, col, direction)
