"""一箭又一箭 — pygame presentation, input, and time-based animation."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from game_logic import DIRECTIONS, Game, MoveResult, State, count_arrows
from levels import LEVELS

WIDTH, HEIGHT = 1180, 820
BG = "#101923"
PANEL = "#192633"
TILE = "#243646"
LINE = "#314554"
WHITE = "#F1F5F3"
MUTED = "#A0B3BE"
TEAL = "#8CE5CE"
CORAL = "#FF9487"
GOLD = "#F0CC87"
BLUE = "#99C5FA"
COLORS = {"U": TEAL, "D": GOLD, "L": BLUE, "R": CORAL}


class App:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("一箭又一箭 | Arrow by Arrow")
        self.clock = pygame.time.Clock()
        self.game = Game(LEVELS)
        self.running = True
        self.elapsed = 0.0
        self.effect: MoveResult | None = None
        self.effect_time = 0.0
        self.effect_duration = 0.48
        self.hint_cell: tuple[int, int] | None = None
        self.hint_time = 0.0
        self.message = "观察箭头方向，寻找一条通向边缘的路。"
        self.message_bad = False
        self.fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        windir = Path(os.environ.get("WINDIR", "C:/Windows"))
        candidates = [windir / "Fonts/msyh.ttc", windir / "Fonts/simhei.ttf",
                      Path("/System/Library/Fonts/PingFang.ttc"),
                      Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")]
        self.font_path = next((str(p) for p in candidates if p.exists()), None)
        if not self.font_path:
            self.font_path = pygame.font.match_font("microsoftyahei,notosanscjk,simhei")
        self.buttons: dict[str, pygame.Rect] = {}
        self.draw()

    def font(self, size: int, bold: bool = False):
        key = size, bold
        if key not in self.fonts:
            value = pygame.font.Font(self.font_path, size)
            value.set_bold(bold)
            self.fonts[key] = value
        return self.fonts[key]

    def text(self, text, pos, size=20, color=WHITE, bold=False, center=False):
        surface = self.font(size, bold).render(str(text), True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        self.screen.blit(surface, rect)
        return rect

    def panel(self, rect, color=PANEL, radius=22, border=None):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=radius)

    def button(self, key, label, rect, primary=False, small=False):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(pygame.mouse.get_pos())
        color = ("#A6F5E0" if hover else TEAL) if primary else ("#304755" if hover else TILE)
        self.panel(rect, color, 14, None if primary else LINE)
        self.text(label, rect.center, 17 if small else 20, BG if primary else WHITE,
                  bold=primary, center=True)
        self.buttons[key] = rect

    def arrow(self, center, size, direction, color):
        # Draw geometrically to avoid missing arrow glyphs in system fonts.
        dr, dc = DIRECTIONS[direction]
        vx, vy = dc, dr
        px, py = -vy, vx
        cx, cy = center
        tail = (cx - vx * size * .42, cy - vy * size * .42)
        head = (cx + vx * size * .42, cy + vy * size * .42)
        neck = (cx + vx * size * .06, cy + vy * size * .06)
        width = max(3, int(size * .105))
        pygame.draw.line(self.screen, color, tail, head, width)
        for sign in (-1, 1):
            wing = (neck[0] + sign * px * size * .32,
                    neck[1] + sign * py * size * .32)
            pygame.draw.line(self.screen, color, head, wing, width)

    def geometry(self):
        size = len(self.game.board) or 4
        cell = 520 // size
        extent = size * cell
        return pygame.Rect(110 + (520 - extent) // 2, 204, extent, extent), cell

    def cell_center(self, row, col):
        rect, cell = self.geometry()
        return rect.x + col * cell + cell // 2, rect.y + row * cell + cell // 2

    def position_to_cell(self, pos):
        rect, cell = self.geometry()
        if not rect.collidepoint(pos):
            return None
        col, row = (pos[0] - rect.x) // cell, (pos[1] - rect.y) // cell
        tile = pygame.Rect(rect.x + col * cell + 7, rect.y + row * cell + 7,
                           cell - 14, cell - 14)
        return (row, col) if tile.collidepoint(pos) else None

    def reset_view(self):
        self.elapsed = 0.0
        self.effect = None
        self.effect_time = 0.0
        self.hint_cell = None
        self.hint_time = 0.0
        self.message = "观察整条路径，而不只是相邻的格子。"
        self.message_bad = False

    def start(self, index=0):
        self.game.start(index)
        self.reset_view()

    def act(self, key):
        if key == "start":
            self.start()
        elif key.startswith("level_"):
            self.start(int(key.split("_")[1]))
        elif key == "menu":
            self.game.to_menu()
            self.reset_view()
        elif key == "restart":
            self.game.restart()
            self.reset_view()
        elif key == "next":
            if self.game.next_level():
                self.reset_view()
        elif key == "hint" and not self.effect:
            self.hint_cell = self.game.hint()
            self.hint_time = 2.5
            if self.hint_cell:
                self.message = "描边的箭头前方畅通，试着点击它。"
                self.message_bad = False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.act("menu")
            elif event.key == pygame.K_r and self.game.state is not State.MENU:
                self.act("restart")
            elif event.key == pygame.K_h and self.game.state is State.PLAYING:
                self.act("hint")
            elif event.key == pygame.K_RETURN:
                if self.game.state is State.MENU:
                    self.act("start")
                elif not self.effect and self.game.state is State.WON:
                    self.act("next")
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for key, rect in self.buttons.items():
            if rect.collidepoint(event.pos):
                self.act(key)
                return
        if self.game.state is not State.PLAYING or self.effect:
            return
        cell = self.position_to_cell(event.pos)
        if cell is None:
            return
        result = self.game.click(*cell)
        if result.kind == "ignored":
            return
        self.effect, self.effect_time = result, 0.0
        self.hint_cell = None
        self.message_bad = result.kind == "blocked"
        self.message = (f"前方有阻挡！还剩 {self.game.lives} 次失误机会。" if self.message_bad
                        else "路径畅通，箭头已飞出！")

    def update(self, dt):
        if self.game.state is State.PLAYING:
            self.elapsed += dt
        if self.effect:
            self.effect_time += dt
            if self.effect_time >= self.effect_duration:
                self.effect = None
        self.hint_time = max(0, self.hint_time - dt)
        if self.hint_time == 0:
            self.hint_cell = None

    def time_label(self):
        value = int(self.elapsed)
        return f"{value // 60:02d}:{value % 60:02d}"

    def draw_menu(self):
        self.text("ARROW / 2026", (44, 32), 16, TEAL, True)
        self.text("一个方向，一步思考。", (44, 118), 20, MUTED)
        self.text("一箭又一箭", (40, 157), 65, WHITE, True)
        self.text("让每一支箭，找到自己的出口。", (44, 262), 24, WHITE)
        self.text("点击箭头 · 看清路径 · 清空棋盘", (44, 312), 18, MUTED)
        self.button("start", "开始挑战   →", (44, 370, 276, 62), True)
        self.text("每关 3 次机会。先从没有阻挡的箭头开始。", (44, 456), 17, MUTED)

        self.panel((668, 95, 468, 416), PANEL, 30, LINE)
        demo = LEVELS[0].rows
        for r, row in enumerate(demo):
            for c, value in enumerate(row):
                rect = pygame.Rect(730 + c * 87, 128 + r * 87, 73, 73)
                self.panel(rect, TILE if value != "." else "#14212B", 16)
                if value in DIRECTIONS:
                    self.arrow(rect.center, 39, value, COLORS[value])
                else:
                    pygame.draw.circle(self.screen, LINE, rect.center, 3)
        self.text("FOLLOW THE DIRECTION", (902, 486), 12, MUTED, center=True)

        self.text("选择一个起点", (44, 540), 22, WHITE, True)
        self.text("三个关卡，逐步加深", (934, 546), 16, MUTED)
        for i, level in enumerate(LEVELS):
            x = 44 + i * 370
            self.panel((x, 587, 352, 153), PANEL, 20, LINE)
            self.text(f"0{i + 1}", (x + 22, 600), 42, (TEAL, BLUE, GOLD)[i], True)
            self.text(level.name, (x + 93, 611), 22, WHITE, True)
            self.text(f"{len(level.rows)} × {len(level.rows)}   /   {count_arrows(level.rows)} 支箭头",
                      (x + 94, 649), 15, MUTED)
            self.button(f"level_{i}", "进入关卡", (x + 22, 692, 308, 34), small=True)
        self.text("PYTHON + PYGAME", (44, 783), 12, MUTED)
        self.text("Enter 开始  /  鼠标操作", (928, 780), 14, MUTED)

    def draw_board(self):
        self.panel((40, 154, 660, 610), PANEL, 24, LINE)
        self.text("BOARD", (62, 169), 12, MUTED, True)
        rect, cell = self.geometry()
        for r, row in enumerate(self.game.board):
            for c, value in enumerate(row):
                tile = pygame.Rect(rect.x + c * cell + 7, rect.y + r * cell + 7,
                                   cell - 14, cell - 14)
                selected = (r, c) == self.hint_cell
                hit = (self.effect is not None and self.effect.kind == "blocked"
                       and (r, c) == (self.effect.row, self.effect.col))
                hover = (not self.effect and self.game.state is State.PLAYING
                         and tile.collidepoint(pygame.mouse.get_pos()) and value != ".")
                fill = "#523C43" if hit else ("#334E5A" if hover else TILE)
                self.panel(tile, fill if value != "." else "#14212B", 16,
                           TEAL if selected else (CORAL if hit else None))
                if selected:
                    pygame.draw.rect(self.screen, TEAL, tile, 3, border_radius=16)
                if value in DIRECTIONS:
                    x, y = tile.center
                    if hit:
                        dr, dc = DIRECTIONS[value]
                        offset = math.sin(self.effect_time * 45) * 9 * (1 - self.effect_time / self.effect_duration)
                        x, y = x + dc * offset, y + dr * offset
                    self.arrow((x, y), cell * .43, value, CORAL if hit else COLORS[value])
                else:
                    pygame.draw.circle(self.screen, LINE, tile.center, 3)
        if self.effect and self.effect.kind == "removed":
            e = self.effect
            t = min(1, self.effect_time / self.effect_duration)
            x, y = self.cell_center(e.row, e.col)
            dr, dc = DIRECTIONS[e.direction]
            if dc > 0:
                distance = rect.right - x + cell
            elif dc < 0:
                distance = x - rect.left + cell
            elif dr > 0:
                distance = rect.bottom - y + cell
            else:
                distance = y - rect.top + cell
            offset = distance * (t * t)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(pygame.Rect(47, 194, 646, 558))
            self.arrow((x + dc * offset, y + dr * offset), cell * .43,
                       e.direction, COLORS[e.direction])
            self.screen.set_clip(old_clip)

    def draw_play(self):
        level = LEVELS[self.game.level_index]
        self.text("一箭又一箭", (40, 27), 28, WHITE, True)
        self.text("ARROW BY ARROW", (42, 69), 12, MUTED)
        self.button("menu", "返回菜单", (990, 34, 150, 46), small=True)
        self.text(f"0{self.game.level_index + 1} / 03", (42, 109), 20, TEAL, True)
        self.text(level.name, (163, 104), 25, WHITE, True)
        self.text(level.subtitle, (729, 112), 17, MUTED)
        self.draw_board()

        self.panel((728, 154, 412, 174), PANEL, 22, LINE)
        self.text("剩余箭头", (753, 174), 16, MUTED)
        self.text(f"{count_arrows(self.game.board):02d}", (750, 198), 56, TEAL, True)
        self.text("本关用时", (962, 174), 16, MUTED)
        self.text(self.time_label(), (960, 211), 29, WHITE, True)
        self.text("失误机会", (754, 287), 15, MUTED)
        for i in range(3):
            center = 908 + i * 47, 299
            pygame.draw.circle(self.screen, CORAL if i < self.game.lives else LINE, center, 12)
        self.text(f"{self.game.lives}/3", (1042, 286), 16, WHITE)

        self.panel((728, 349, 412, 226), PANEL, 22, LINE)
        self.text("先观察，再点击", (752, 369), 22, WHITE, True)
        for y, number, title, detail in [
            (418, "01", "看方向", "箭头只沿自己的方向前进。"),
            (470, "02", "看整条路", "直到边缘，没有其他箭头才能飞出。"),
            (522, "03", "看顺序", "先消除外围，再打开新的路径。"),
        ]:
            self.text(number, (753, y), 14, TEAL, True)
            self.text(title, (788, y - 3), 17, WHITE, True)
            self.text(detail, (788, y + 21), 14, MUTED)

        self.panel((728, 596, 412, 80), "#3D2E36" if self.message_bad else "#203D3B", 17)
        self.text("碰撞提示" if self.message_bad else "当前提示", (750, 606), 14,
                  CORAL if self.message_bad else TEAL, True)
        self.text(self.message, (750, 636), 16, WHITE)
        self.button("hint", "提示  H", (728, 697, 195, 58))
        self.button("restart", "重新开始  R", (937, 697, 203, 58))
        self.text("点击格子中的箭头  ·  空格与棋盘外点击不扣机会", (42, 786), 13, MUTED)
        self.text("Esc 返回菜单", (1030, 785), 13, MUTED)

    def draw_result(self):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((7, 13, 20, 208))
        self.screen.blit(shade, (0, 0))
        self.buttons.clear()
        lost = self.game.state is State.LOST
        complete = self.game.state is State.COMPLETE
        color = CORAL if lost else TEAL
        self.panel((280, 201, 620, 420), PANEL, 28, LINE)
        pygame.draw.circle(self.screen, "#2D4249", (590, 266), 34)
        self.text("!" if lost else "✓", (590, 264), 37, color, True, center=True)
        title = "挑战失败" if lost else ("全部通关！" if complete else "本关通过！")
        self.text(title, (590, 343), 42, WHITE, True, center=True)
        subtitle = ("机会已经用完，换一个顺序再试一次。" if lost else
                    ("三个关卡，全部找到出口。" if complete else "棋盘已清空，准备迎接下一关。"))
        self.text(subtitle, (590, 400), 20, MUTED, center=True)
        self.text(f"本关用时 {self.time_label()}    点击 {self.game.moves} 次    提示 {self.game.hints} 次",
                  (590, 454), 17, color, center=True)
        self.button("menu", "返回菜单", (322, 527, 248, 57))
        key = "restart" if lost else ("start" if complete else "next")
        self.button(key, "重新挑战" if lost else ("从头挑战" if complete else "下一关   →"),
                    (610, 527, 248, 57), True)

    def draw(self):
        self.screen.fill(BG)
        self.buttons.clear()
        if self.game.state is State.MENU:
            self.draw_menu()
        else:
            self.draw_play()
            if self.game.state is not State.PLAYING and not self.effect:
                self.draw_result()
        pygame.display.flip()

    def step(self, dt=None):
        if dt is None:
            dt = min(self.clock.tick(60) / 1000, .1)
        for event in pygame.event.get():
            self.handle_event(event)
            # A new page invalidates the previous page's button map immediately.
            self.draw()
        self.update(dt)
        self.draw()

    def run(self):
        while self.running:
            self.step()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="一箭又一箭")
    parser.add_argument("--smoke-test", metavar="REPORT", help="Run one real SDL frame, save JSON, then exit")
    args = parser.parse_args()
    app = App()
    if args.smoke_test:
        # Dedicated self-check for source/executable startup verification.
        app.step(1 / 60)
        app.start(0)
        app.step(1 / 60)
        report = {"status": "ok", "driver": pygame.display.get_driver(),
                  "pygame": pygame.version.ver, "python": sys.version.split()[0],
                  "screen": list(app.screen.get_size()), "font": app.font_path,
                  "levels": len(LEVELS), "state": app.game.state.value,
                  "frozen": bool(getattr(sys, "frozen", False))}
        Path(args.smoke_test).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        pygame.quit()
    else:
        app.run()


if __name__ == "__main__":
    main()
