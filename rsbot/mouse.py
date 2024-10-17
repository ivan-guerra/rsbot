"""This is an adaptation of the bezmouse project's mouse.py script.

See https://github.com/vincentbavitz/bezmouse.
"""

import os
import subprocess
from random import randint, choice
from math import ceil
import pyautogui

pyautogui.MINIMUM_DURATION = 0.01


def __pascal_row(n: int) -> list[int]:
    """Return the nth row of Pascal's Triangle."""
    result = [1]
    x, numerator = 1, n
    for denominator in range(1, n // 2 + 1):
        x *= numerator
        x /= denominator
        result.append(x)
        numerator -= 1

    if n % 2 == 0:
        result.extend(reversed(result[:-1]))
    else:
        result.extend(reversed(result))

    return result


def __make_bezier(xys: list[tuple[int, int]]):
    """Generate a Bezier curve based on control points.

    Args:
        xys: List of control points.

    Returns:
        Function that computes the curve points.
    """
    n = len(xys)
    combinations = __pascal_row(n - 1)

    def bezier(ts: list[float]) -> list[tuple[float, float]]:
        result = []
        for t in ts:
            tpowers = (t ** i for i in range(n))
            upowers = reversed([(1 - t) ** i for i in range(n)])
            coefs = [c * a * b for c, a,
                     b in zip(combinations, tpowers, upowers)]
            result.append([sum(coef * p for coef, p in zip(coefs, ps))
                          for ps in zip(*xys)])
        return result

    return bezier


def __mouse_bez(init_pos: tuple[int, int],
                fin_pos: tuple[int, int],
                deviation: int,
                speed: int) -> None:
    """Generate Bezier curve points from initial to final mouse positions.

    Args:
        init_pos: Initial position tuple (x, y).
        fin_pos: Final position tuple (x, y).
        deviation: Controls the randomness of the curve.
        speed: Speed multiplier (lower values are faster). 1 is the fastest.

    Returns:
        List of points representing the mouse's path.
    """
    def get_ctrl_point(idx):
        return init_pos[idx] + choice((-1, 1)) * abs(ceil(fin_pos[idx]) -
                                                     ceil(init_pos[idx])) * 0.01 * randint(deviation // 2, deviation)  # pylint: disable=line-too-long

    control_1 = (get_ctrl_point(0), get_ctrl_point(1))
    control_2 = (get_ctrl_point(0), get_ctrl_point(1))
    xys = [init_pos, control_1, control_2, fin_pos]

    ts = [t / (speed * 100.0) for t in range(speed * 101)]
    bezier = __make_bezier(xys)
    mouse_points = bezier(ts)
    # Appending fin_pos guarantees we land at the target location regardless of
    # the deviation setting.
    mouse_points.append(fin_pos)

    return mouse_points


def move(init_pos: tuple[int, int], fin_pos: tuple[int, int], deviation: int, speed: int) -> None:
    """Move the mouse following a list of points (continuous curve).

    Args:
        mouse_points: List of 2-tuples representing (x, y) coordinates.
        draw: If True, saves the curve to a file.
        rand_err: If True, adds randomness to clicks.
    """
    script_path = "/tmp/mouse.sh"
    with open(script_path, "w", encoding="ascii") as outfile:
        outfile.write("#!/bin/bash\n\n")
        mouse_points = __mouse_bez(init_pos, fin_pos, deviation, speed)
        mouse_points = [[round(v) for v in x] if isinstance(
            x, (tuple, list)) else x for x in mouse_points]
        for coord in mouse_points:
            outfile.write(f"xdotool mousemove {coord[0]} {coord[1]}\n")

    os.system(f"chmod +x {script_path}")

    subprocess.call([script_path])
