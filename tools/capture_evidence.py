"""Replay actual UI events, save renderer frames and machine-readable evidence."""

import json
import os
from pathlib import Path
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
from PIL import Image
from ArrowGame import App
from game_logic import State, available_moves, can_exit, count_arrows, solve


def main():
    output = ROOT / "docs/images"
    output.mkdir(parents=True, exist_ok=True)
    app = App()
    frames = []
    durations = []
    actions = []

    def frame(duration=90):
        pixels = pygame.image.tobytes(app.screen, "RGB")
        picture = Image.frombytes("RGB", app.screen.get_size(), pixels)
        frames.append(picture.resize((826, 574), Image.Resampling.LANCZOS))
        durations.append(duration)

    def save(name):
        pygame.image.save(app.screen, output / f"{name}.png")

    def click(pos, label):
        before = {"state": app.game.state.value, "level": app.game.level_index + 1,
                  "lives": app.game.lives, "arrows": count_arrows(app.game.board)}
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
        app.step(0)
        actions.append({"action": label, "position": list(pos), "before": before,
                        "after": {"state": app.game.state.value, "level": app.game.level_index + 1,
                                  "lives": app.game.lives, "arrows": count_arrows(app.game.board)},
                        "feedback": app.message})

    save("01_menu")
    frame(1100)
    click(app.buttons["start"].center, "start")
    save("02_playing")
    frame(1000)
    blocked = next((r, c) for r, row in enumerate(app.game.board) for c, v in enumerate(row)
                   if v != "." and not can_exit(app.game.board, r, c))
    click(app.cell_center(*blocked), "blocked_arrow")
    for index in range(10):
        app.step(.045)
        frame(80)
        if index == 2:
            save("03_collision")
    app.step(.1)
    click(app.cell_center(*available_moves(app.game.board)[0]), "clear_arrow")
    for index in range(12):
        app.step(.04)
        frame(80)
        if index == 7:
            save("04_flying")
    app.step(.1)
    save("05_removed")
    frame(800)
    # Repeated blocked clicks finish the actual failure branch.
    for _ in range(2):
        click(app.cell_center(*blocked), "blocked_arrow_until_failure")
        app.step(.6)
    assert app.game.state is State.LOST
    save("06_failed")
    frame(1200)
    click(app.buttons["restart"].center, "retry")
    initial = [row[:] for row in app.game.board]
    for cell in solve(app.game.board):
        click(app.cell_center(*cell), "solve_level_1")
        app.step(.6)
        frame(170)
    assert app.game.state is State.WON
    save("07_level_clear")
    frame(1200)
    certificates = [{"level": 1, "start": initial, "solution": solve(initial)}]
    for level_index in (1, 2):
        click(app.buttons["next"].center, "next_level")
        save(f"0{level_index + 7}_level_{level_index + 1}")
        initial = [row[:] for row in app.game.board]
        order = solve(initial)
        certificates.append({"level": level_index + 1, "start": initial, "solution": order})
        for cell in order:
            click(app.cell_center(*cell), f"solve_level_{level_index + 1}")
            app.step(.6)
    assert app.game.state is State.COMPLETE
    save("10_all_clear")
    frame(1700)
    frames[0].save(output / "demo.gif", save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    result = {"mode": "scripted pygame mouse events / SDL dummy renderer",
              "student_personal_playtest": "not recorded",
              "result": "passed", "actions": actions, "solutions": certificates,
              "image_files": sorted(p.name for p in output.iterdir())}
    (ROOT / "evidence/ui_replay.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pygame.quit()
    print(f"UI replay passed: {len(actions)} actual mouse events, {len(frames)} GIF frames")


if __name__ == "__main__":
    main()
