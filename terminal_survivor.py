import curses
import random
import time
import math


BASE_FRAME_DELAY = 0.08


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Player
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # Enemy
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Player Bullet
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Enemy Bullet
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Boss

    height, width = stdscr.getmaxyx()

    stdscr.nodelay(False)
    stdscr.clear()
    stdscr.addstr(height//2 - 1, width//2 - 10, "TERMINAL SURVIVOR", curses.A_BOLD)
    stdscr.addstr(height//2 + 1, width//2 - 12, "Press any key to start")
    stdscr.refresh()
    stdscr.getch()
    stdscr.nodelay(True)

    player_x = width // 2
    player_y = height // 2

    health = 3
    score = 0
    wave = 1

    enemies = []
    enemy_bullets = []
    player_bullets = []
    boss = None

    game_over = False

    def spawn_wave(w):
        if w % 5 == 0:
            return []
        spawned = []
        for _ in range(w * 3):
            while True:
                y = random.randint(2, height - 3)
                x = random.randint(2, width - 3)
                if abs(y - player_y) > 6 and abs(x - player_x) > 10:
                    spawned.append([y, x])
                    break
        return spawned

    def spawn_boss(w):
        return {
            "y": 2,
            "x": width // 2,
            "hp": 20 + w * 2
        }

    enemies = spawn_wave(wave)

    last_enemy_shot = time.time()
    last_frame = time.time()

    while True:
        now = time.time()
        frame_delay = max(BASE_FRAME_DELAY - wave * 0.005, 0.03)

        if now - last_frame < frame_delay:
            continue
        last_frame = now

        stdscr.erase()
        stdscr.border()

        key = stdscr.getch()

        # Movement
        if key == ord("w") and player_y > 1:
            player_y -= 1
        elif key == ord("s") and player_y < height - 2:
            player_y += 1
        elif key == ord("a") and player_x > 1:
            player_x -= 1
        elif key == ord("d") and player_x < width - 2:
            player_x += 1
        elif key == ord(" "):
            targets = enemies.copy()
            if boss:
                targets.append([boss["y"], boss["x"]])
            if targets:
                nearest = min(
                    targets,
                    key=lambda e: math.hypot(e[0] - player_y, e[1] - player_x),
                )
                dy = nearest[0] - player_y
                dx = nearest[1] - player_x
                dist = math.hypot(dy, dx)
                if dist != 0:
                    player_bullets.append([player_y, player_x, dy / dist, dx / dist])
        elif key == ord("q"):
            break

        # Boss spawn
        if wave % 5 == 0 and not boss:
            boss = spawn_boss(wave)

        # Enemy movement
        for enemy in enemies:
            if random.random() < (0.15 + wave * 0.02):
                enemy[0] += 1 if enemy[0] < player_y else -1 if enemy[0] > player_y else 0
                enemy[1] += 1 if enemy[1] < player_x else -1 if enemy[1] > player_x else 0

        # Boss movement
        if boss:
            if boss["x"] < player_x:
                boss["x"] += 1
            elif boss["x"] > player_x:
                boss["x"] -= 1

        # Enemy shooting
        if time.time() - last_enemy_shot > max(1.2 - wave * 0.07, 0.3):
            if enemies:
                shooter = random.choice(enemies)
                dy = player_y - shooter[0]
                enemy_bullets.append([shooter[0], shooter[1], 1 if dy > 0 else -1])
            if boss:
                enemy_bullets.append([boss["y"] + 1, boss["x"], 1])
            last_enemy_shot = time.time()

        # Player bullets
        new_player_bullets = []
        for bullet in player_bullets:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            by = int(round(bullet[0]))
            bx = int(round(bullet[1]))

            hit = False

            for enemy in enemies:
                if enemy[0] == by and enemy[1] == bx:
                    enemies.remove(enemy)
                    score += 25
                    hit = True
                    break

            if boss and by == boss["y"] and bx == boss["x"]:
                boss["hp"] -= 1
                score += 5
                hit = True
                if boss["hp"] <= 0:
                    score += 200
                    boss = None
                    wave += 1
                    enemies = spawn_wave(wave)

            if not hit and 1 < by < height - 1 and 1 < bx < width - 1:
                new_player_bullets.append(bullet)

        player_bullets = new_player_bullets

        # Enemy bullets
        new_enemy_bullets = []
        for bullet in enemy_bullets:
            bullet[0] += bullet[2]
            by = bullet[0]
            bx = bullet[1]

            if by == player_y and bx == player_x:
                health -= 1
                if health <= 0:
                    game_over = True
                    break
                continue

            if 1 < by < height - 1:
                new_enemy_bullets.append(bullet)

        enemy_bullets = new_enemy_bullets

        # Direct collision
        for enemy in enemies:
            if enemy[0] == player_y and enemy[1] == player_x:
                health -= 1
                enemies.remove(enemy)
                if health <= 0:
                    game_over = True
                    break

        if game_over:
            break

        # Wave progression
        if not enemies and not boss:
            wave += 1
            enemies = spawn_wave(wave)
            enemy_bullets.clear()
            player_bullets.clear()

        # Draw
        stdscr.addstr(player_y, player_x, "@", curses.color_pair(1) | curses.A_BOLD)

        for enemy in enemies:
            stdscr.addstr(enemy[0], enemy[1], "X", curses.color_pair(2) | curses.A_BOLD)

        if boss:
            stdscr.addstr(boss["y"], boss["x"], "B", curses.color_pair(5) | curses.A_BOLD)
            stdscr.addstr(1, width - 20, f"Boss HP: {boss['hp']}")

        for bullet in player_bullets:
            stdscr.addstr(int(round(bullet[0])), int(round(bullet[1])), "•", curses.color_pair(3))

        for bullet in enemy_bullets:
            stdscr.addstr(bullet[0], bullet[1], "|", curses.color_pair(4))

        stdscr.addstr(0, 2, f"Wave: {wave}")
        stdscr.addstr(0, 15, f"Score: {score}")
        stdscr.addstr(0, 30, f"Health: {health}")
        stdscr.addstr(0, width - 20, "SPACE=Shoot  Q=Quit")

        stdscr.noutrefresh()
        curses.doupdate()

    # -------- GAME OVER SCREEN --------
    stdscr.nodelay(False)
    stdscr.clear()

    stdscr.addstr(height//2 - 3, width//2 - 5, "GAME OVER", curses.A_BOLD)
    stdscr.addstr(height//2 - 1, width//2 - 8, f"Final Score: {score}")
    stdscr.addstr(height//2, width//2 - 8, f"Reached Wave: {wave}")

    stdscr.addstr(height//2 + 3, width//2 - 10, "==== SCOREBOARD ====")
    stdscr.addstr(height//2 + 5, width//2 - 10, f"| Player | {score:<6} |")

    stdscr.addstr(height//2 + 8, width//2 - 14, "Press any key to exit")
    stdscr.refresh()
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)
