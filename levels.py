"""Original fixed levels built by tools/design_levels.py; no external assets."""

from game_logic import Level

LEVELS = (
    Level("初见方向", "先观察边缘，再寻找出口", (".DUR", "L.U.", "LLUU", "..DU")),
    Level("交错之间", "空一格，也可能被远处阻挡", ("ULUUD", "UU..R", "..U.R", ".ULDR", "RR.RR")),
    Level("顺序的答案", "每一次消除，都让路径更清晰", ("ULUUUU", "LLU.UD", ".D..UL", "U..L.D", "L.DR.R", "DDDRDD")),
)
