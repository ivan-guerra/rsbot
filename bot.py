#!/usr/bin/env python3
"""Run a Runescape botting script.

This script executes a Runescape 3 or Old School Runescape auto clicker script. A number of
command line options are supported. To see all available options and their description, run this
script with the --help/-h option.

This script has one required argument which is the path to a JSON file containing the click events.
The bot script must have the following format:

{
  "events": [
    {
      "id": "click bank",
      "click_box": [
        [925, 308],
        [1001, 319],
        [926, 512],
        [1001, 507]
      ],
      "button": "left",
      "min_delay_sec": 1,
      "max_delay_sec": 3
    },
    ...
}

The JSON bot script contains a top-level "events" array. Each click event has five fields:
    * id: A string describing the event.
    * click_box: An array of 2D points that form a click box. When this event executes, a click
                 will be performed within the click box's bounds.
    * button: Which mouse button to click. Only "left" and "right" buttons are currently supported.
    * min_delay_sec: The minimum delay in seconds the script will insert after the click
                     is performed.
    * max_delay_sec: The maximum delay in seconds the script will insert after the click
                     is performed.

Randomization is a big part of this botting script's strategy for avoiding Jagex's bot detection
system. The delay after an event is executed is randomized using the min_delay_sec and max_delay_sec
fields. Similarly, many of the command line options are min/max pairs that allow the user to
tailor additional delays.
"""
import signal
import sys
import random
import json
import time
import argparse
import logging
import tkinter as tk
from dataclasses import dataclass
import pyautogui


class ClickBox:
    """Define a quadrilateral representing an in game click box.

    To avoid bot detection, don't click the exact same pixel location for hours on end.
    ClickBox provides an API for consistently clicking a target object (e.g., bank chest, NPC, etc.)
    without hardcoding a specific pixel location.
    """

    def __init__(self, vertices: list[tuple[int]]) -> None:
        """Construct a quadrilateral.

        Args:
            vertices: A list of four 2D points representing the corners of the click box.
        Throws:
            ValueError: When the length of the parameter vertices list is not exactly four.
        """
        num_vertices = 4
        if len(vertices) != num_vertices:
            raise ValueError(
                f"invalid number of vertices, expected {num_vertices} got {len(vertices)}")
        self._vertices = vertices

    def _random_point_in_triangle(self, v1, v2, v3) -> tuple[int]:
        """Return a point within the bounds of the triangle formed by the paramater vertices."""
        s = random.random()
        t = random.random()

        # Ensure the point is inside the triangle.
        if s + t > 1:
            s = 1 - s
            t = 1 - t

        x = v1[0] + s * (v2[0] - v1[0]) + t * (v3[0] - v1[0])
        y = v1[1] + s * (v2[1] - v1[1]) + t * (v3[1] - v1[1])

        return (x, y)

    def get_rand_point(self) -> tuple[int]:
        """Return a random point within click box bounds."""
        if random.random() < 0.5:
            # Generate a point in the first triangle.
            return self._random_point_in_triangle(
                self._vertices[0], self._vertices[1], self._vertices[2])
        # Generate a point in the second triangle.
        return self._random_point_in_triangle(
            self._vertices[0], self._vertices[2], self._vertices[3])

    def __str__(self) -> str:
        """Return this ClickBox's string representation."""
        vertice_strs = [f"({v[0]},{v[1]})" for v in self._vertices]
        return ",".join(vertice_strs)


@dataclass
class MouseEvent:
    """Representation of a bot click event.

    Fields:
        event_id: A string describing this event.
        click_box: The area within which this event will perform its click.
        button: The mouse button that will be clicked. Must be one of "left" or "right".
        min_delay_sec: The minimum delay in seconds following the click.
        max_delay_sec: The maximum delay in seconds following the click.
    """

    event_id: str
    click_box: ClickBox
    button: str
    min_delay_sec: float
    max_delay_sec: float

    def __str__(self) -> str:
        """Return this MouseEvent's string representation."""
        return ",".join([
            f"id={self.event_id}",
            f"click_box={self.click_box}",
            f"button={self.button}",
            f"min_delay_sec={self.min_delay_sec}",
            f"max_delay_sec={self.max_delay_sec}",
        ])


class MouseController:
    """Provide an API for controlling the mouse.

    The mouse controller is aware of the dimensions of the user's screen. The controller will
    report an error whenever the user attempts to perform an operation outside screen bounds.
    """

    def __init__(self) -> None:
        """Construct the mouse controller."""
        root = tk.Tk()
        self._screen_width = root.winfo_screenwidth()
        self._screen_height = root.winfo_screenheight()

    def move_mouse(self, x: int, y: int, duration_sec: float = 0.0) -> None:
        """Move the mouse to the parameter (x, y) location.

        Args:
            x: Screen column.
            y: Screen row.
            duration_sec: The duration over which the move from the current location to the target
                          location will be made. If the value is less than 0.1, then the mouse will
                          move instantly.
        Throws:
            ValueError: When x or y are out of the screen's bounds.
        """
        if x < 0 or x > self._screen_width:
            raise ValueError("requested column {x} is out of bounds")
        if y < 0 or y > self._screen_height:
            raise ValueError("requested row {y} is out of bounds")
        pyautogui.moveTo(x, y, duration_sec)

    def click(self, button: str) -> None:
        """Perform a left or right mouse button click.

        Args:
            button: The mouse button that will be clicked. Must be one of "left" or "right".
        Throws:
            ValueError: When an unsupported button type is detected.
        """
        if button not in ["left", "right"]:
            raise ValueError(f"unexpected button value: {button}")
        pyautogui.click(button=button)

    def perform_random_movement(self, duration_sec: tuple[float]) -> None:
        """Move the mouse to a random location over a randomized period of time.

        Args:
            duration_sec: A tuple of two elements representing a mouse movement delay range.
                          A random delay in seconds is chosen from this range.
        """
        x = random.randrange(0, self._screen_width - 1)
        y = random.randrange(0, self._screen_height - 1)
        rand_duration_sec = random.uniform(duration_sec[0], duration_sec[1])
        logging.debug(
            "random mouse movement params: x=%d y=%d duration=%0.4f sec",
            x, y, rand_duration_sec)
        self.move_mouse(x, y, rand_duration_sec)


class Script:  # pylint: disable=locally-disabled, too-few-public-methods
    """Load and execute a bot script."""

    def __init__(self, conf) -> None:
        """Load all mouse events from disk and initialize the mouse controller.

        Args:
            conf: A argparse dictionary containing the script's command line options.
        Throws:
            ValueError: When the JSON event file cannot be parsed or an invalid field is detected.
        """
        self._conf = conf
        self._events = self._parse_events(conf.script)
        self._mouse_ctrl = MouseController()

    def _parse_events(self, script_json: str) -> list[MouseEvent]:
        """Read events from a JSON script file.

        Args:
            script_json: The path to a JSON file containing mouse event descriptions.
        Throws:
            FileNotFoundError: When the script file cannot be found.
            ValueError: When an invalid field or JSON file is detected.
        """
        data = None
        with open(script_json, "r", encoding="ascii") as file:
            data = json.load(file)

        def validate_fields(event) -> None:
            required_fields = ["id", "click_box",
                               "button", "min_delay_sec", "max_delay_sec"]
            for field in required_fields:
                if field not in event:
                    raise ValueError(
                        f"one or more events missing required field '{field}'")

            # There are no requirements on the event id, it can be any ASCII string.
            # ClickBox does it's own validation at construct time, no need to dupe that code here.
            if event["button"] not in ["left", "right"]:
                raise ValueError(
                    "parse error, button must be one of 'left' or 'right'")
            if event["min_delay_sec"] < 0:
                raise ValueError(
                    "parse error, min_delay_sec must be zero or positive")
            if event["max_delay_sec"] < 0:
                raise ValueError(
                    "parse error, max_delay_sec must be zero or positive")

        events = []
        for event in data["events"]:
            validate_fields(event)
            events.append(MouseEvent(
                event["id"],
                ClickBox(list(event["click_box"])),
                event["button"],
                event["min_delay_sec"],
                event["max_delay_sec"]))
        return events

    def _do_random_mvmts(self) -> None:
        """Execute a number of random mouse movements."""
        nrand_mvmts = random.randrange(self._conf.max_rand_mvmts)
        logging.debug("performing %d random mouse movement(s)", nrand_mvmts)
        for _ in range(nrand_mvmts):
            self._mouse_ctrl.perform_random_movement(
                self._conf.mouse_delay)

    def _exec_event(self, event: MouseEvent) -> None:
        """Execute a scripted mouse event."""
        # Simulate clicking a target NPC or object. The randomization in both the click delay and
        # point is meant to avoid bot detection.
        mouse_delay_sec = random.uniform(*self._conf.mouse_delay)
        mouse_pos = event.click_box.get_rand_point()
        logging.info("executing event: %s", event.event_id)
        logging.debug(
            "delaying movement to position by %0.4f sec ", mouse_delay_sec)
        logging.debug("clicking at position (%d, %d)",
                      mouse_pos[0], mouse_pos[1])
        self._mouse_ctrl.move_mouse(
            mouse_pos[0], mouse_pos[1], mouse_delay_sec)
        self._mouse_ctrl.click(event.button)

        # Some events require lengthy delays. For example, when fletching an inventory of logs.
        # Randomizing that delay by adding just a few seconds/fractions of a second helps avoid
        # detection.
        event_delay_sec = random.uniform(
            event.min_delay_sec, event.max_delay_sec)
        logging.debug("executing post event delay of %0.4f sec",
                      event_delay_sec)
        time.sleep(event_delay_sec)

    def _exec_events(self) -> None:
        """Execute all mouse events inserting random gestures before each event execution.

        It's debated on botting forums whether adding a few random gestures helps avoid detection.
        As a precaution, we are adding random gestures before each event execution. The reduction
        in exp/hr is worth the potential gains in detection avoidance.
        """
        for event in self._events:
            self._do_random_mvmts()
            self._exec_event(event)

    def run(self) -> None:
        """Execute the bot's event script.

        This is a blocking method call. The script can only be interrupted by sending SIGINT to
        the running process or pressing CTRL+c at the prompt from which the program was run.

        The script runs for the configured runtime. The configured events are performed repeatedly.
        Idles are inserted periodically to reduce the probability of detection. The idle period
        and idle time are configurable at the command line.
        """
        start_time = time.time()
        curr_time = start_time
        idle_time = start_time
        while (curr_time - start_time) < self._conf.runtime:
            self._exec_events()
            if (curr_time - idle_time) > self._conf.idle_period:
                idle_time_sec = random.uniform(
                    self._conf.idle_time[0] * 60,
                    self._conf.idle_time[1] * 60)
                logging.info("idling for %0.4f sec", idle_time_sec)
                time.sleep(idle_time_sec)
                idle_time = time.time()
            curr_time = time.time()


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(sig))

        parser = argparse.ArgumentParser(
            description="run a runescape bot script",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("script", type=str,
                            help="path to JSON file containing script "
                            "commands")
        parser.add_argument("--runtime", "-r", type=int, default=3600,
                            help="script runtime in seconds")
        parser.add_argument("--start-delay", "-s", type=int,
                            help="script start delay in seconds")
        parser.add_argument("--max-rand-mvmts", "-m", type=int, default=5,
                            help="max number of random mouse movements "
                            "performed before each event")
        parser.add_argument('--mouse-delay', "-d", nargs=2,
                            type=float, default=[0.25, 0.75],
                            help="defines a range in seconds from which a "
                            "delay for each mouse movement will be "
                            "randomly chosen")
        parser.add_argument("--idle-period", "-p", type=float, default=900,
                            help="number of seconds until an idle wait is "
                            "started")
        parser.add_argument("--idle-time", "-i", nargs=2,
                            type=float, default=[2, 5],
                            help="defines a range in minutes from which an "
                            "idle time will be randomly chosen")
        parser.add_argument("--debug", "-g", action="store_true",
                            help="enable logging of debug messages")
        parser.add_argument("--log-file", "-l", type=str,
                            help="output all log messages to the specified file")
        args = parser.parse_args()

        if args.log_file:
            logging.basicConfig(style="{",
                                level=logging.DEBUG if args.debug else logging.INFO,
                                filename=args.log_file,
                                filemode="a",
                                encoding="ascii",
                                format="{asctime} [{levelname}]: {message}")
        else:
            logging.basicConfig(style="{",
                                level=logging.DEBUG if args.debug else logging.INFO,
                                format="{asctime} [{levelname}]: {message}")

        script = Script(args)
        if args.start_delay:
            logging.info("running script in %d seconds...", args.start_delay)
            time.sleep(args.start_delay)
        script.run()
    except ValueError as error:
        logging.fatal("value error, %s", error)
