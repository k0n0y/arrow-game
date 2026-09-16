"""Search a reproducible set of three varied, solvable level templates."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game_logic import available_moves, generate_level

result = []
for size, count in [(4, 11), (5, 18), (6, 27)]:
    for seed in range(10000):
        board = generate_level(size, count, seed)
        if set("UDLR") <= set("".join(board)) and 3 <= len(available_moves(board)) <= count // 2:
            result.append(dict(size=size, arrows=count, seed=seed, rows=board,
                               initial_available=len(available_moves(board))))
            break
print(json.dumps(result, ensure_ascii=False, indent=2))
