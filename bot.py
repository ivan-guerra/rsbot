import pyautogui
import signal
import sys
import random
import json
import time
import argparse
import tkinter as tk

# TODO: Add logging to file
# TODO: Add a startup delay in seconds


class ClickBox:
    def __init__(self, vertices: list[tuple[int]]):
        self._vertices = vertices

    def __random_point_in_triangle(self, v1, v2, v3) -> tuple[int]:
        s = random.random()
        t = random.random()
        # Ensure the point is inside the triangle
        if s + t > 1:
            s = 1 - s
            t = 1 - t
        x = v1[0] + s * (v2[0] - v1[0]) + t * (v3[0] - v1[0])
        y = v1[1] + s * (v2[1] - v1[1]) + t * (v3[1] - v1[1])
        return (x, y)

    def get_rand_point(self):
        if random.random() < 0.5:
            # Generate a point in the first triangle
            return self.__random_point_in_triangle(
                self._vertices[0], self._vertices[1], self._vertices[2])
        else:
            # Generate a point in the second triangle
            return self.__random_point_in_triangle(
                self._vertices[0], self._vertices[2], self._vertices[3])

    def __str__(self):
        vertice_strs = [f"({v[0]},{v[1]})" for v in self._vertices]
        return ",".join(vertice_strs)


class MouseEvent:
    def __init__(self, id: str, click_box: ClickBox,
                 button: str, min_delay_sec: float, max_delay_sec: float):
        self.id = id
        self.click_box = click_box
        self.button = button
        self.min_delay_sec = min_delay_sec
        self.max_delay_sec = max_delay_sec

    def __str__(self):
        return ",".join([
            f"{self.id}",
            f"{self.click_box}",
            f"{self.button}",
            f"{self.min_delay_sec}"
            f"{self.max_delay_sec}"
        ])


class MouseController:
    def __init__(self):
        root = tk.Tk()
        self._screen_width = root.winfo_screenwidth()
        self._screen_height = root.winfo_screenheight()

    def move_mouse(self, x: int, y: int, duration_sec: float = 0.0):
        pyautogui.moveTo(x, y, duration_sec)

    def click(self, button):
        pyautogui.click(button=button)

    def perform_random_movement(self, duration_sec: tuple[float]):
        x = random.randrange(0, self._screen_width - 1)
        y = random.randrange(0, self._screen_height - 1)
        rand_duration_sec = random.uniform(duration_sec[0], duration_sec[1])
        self.move_mouse(x, y, rand_duration_sec)


class ScriptConfig:
    def __init__(self, runtime_sec: int, event_file: str,
                 idle_period_sec: float, idle_time_min: list[float],
                 max_rand_mvmts: int = 5,
                 mouse_delay_sec: tuple[float] = (0.25, 0.75)):
        self.runtime_sec = runtime_sec
        self.idle_period_sec = idle_period_sec
        self.idle_time_min = idle_time_min
        self.max_rand_mvmts = max_rand_mvmts
        self.mouse_delay_sec = mouse_delay_sec
        self.event_file = event_file

    def __str__(self):
        return "".join([
            "script config:\n\t",
            f"runtime_sec = {self.runtime_sec}\n\t",
            f"event_file = {self.event_file}\n\t",
            f"idle_period_sec = {self.idle_period_sec}\n\t",
            f"idle_time_min = {self.idle_time_min}\n\t",
            f"max_rand_mvmts = {self.max_rand_mvmts}\n\t",
            f"mouse_delay_sec = {self.mouse_delay_sec}"
        ])


class Script:
    def __init__(self, conf: ScriptConfig):
        self._conf = conf
        self._events = self.__parse_events(conf.event_file)
        self._mouse_ctrl = MouseController()

    def __parse_events(self, script_json: str) -> list[MouseEvent]:
        data = None
        with open(script_json, 'r') as file:
            data = json.load(file)

        events = []
        for e in data["events"]:
            events.append(MouseEvent(
                e["id"],
                ClickBox([(x, y) for x, y in e["click_box"]]),
                e["button"],
                e["min_delay_sec"],
                e["max_delay_sec"]))
        return events

    def __do_random_mvmts(self):
        nrand_mvmts = random.randrange(self._conf.max_rand_mvmts)
        for _ in range(nrand_mvmts):
            self._mouse_ctrl.perform_random_movement(
                self._conf.mouse_delay_sec)

    def __exec_event(self, event: MouseEvent):
        mouse_delay_sec = random.uniform(*self._conf.mouse_delay_sec)
        mouse_pos = event.click_box.get_rand_point()
        print(f"performing event: {event}")
        print(f"event_delay_sec={mouse_delay_sec} sec "
              f"mouse_pos=({mouse_pos[0]}, {mouse_pos[1]})")
        self._mouse_ctrl.move_mouse(
            mouse_pos[0], mouse_pos[1], mouse_delay_sec)

        if event.button:
            self._mouse_ctrl.click(event.button)

        event_delay_sec = random.uniform(
            event.min_delay_sec, event.max_delay_sec)
        print(f"adding post event delay of {event_delay_sec} sec")
        time.sleep(event_delay_sec)

    def __exec_events(self):
        for event in self._events:
            self.__do_random_mvmts()
            self.__exec_event(event)

    def run(self):
        start_time = time.time()
        curr_time = start_time
        idle_time = start_time
        while (curr_time - start_time) < self._conf.runtime_sec:
            self.__exec_events()
            if (curr_time - idle_time) > self._conf.idle_period_sec:
                idle_time_sec = random.uniform(
                    self._conf.idle_time_min[0] * 60,
                    self._conf.idle_time_min[1] * 60)
                print(f"idling for {idle_time_sec} sec")
                time.sleep(idle_time_sec)
                idle_time = time.time()
            curr_time = time.time()


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

        parser = argparse.ArgumentParser(
            description="run a runescape bot script",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("script", type=str,
                            help="path to JSON file containing script "
                            "commands")
        parser.add_argument("--runtime", "-r", type=int, default=3600,
                            help="script runtime in seconds")
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
        args = parser.parse_args()

        conf = ScriptConfig(
            args.runtime, args.script,
            args.idle_period, args.idle_time,
            args.max_rand_mvmts, args.mouse_delay)
        script = Script(conf)

        print("starting script in 5 seconds...")
        time.sleep(5)
        script.run()
    except KeyboardInterrupt:
        print('signal SIGINT caught, exiting')
