import pyautogui
import signal
import sys
import random
import csv
import time
import argparse
import tkinter as tk

# TODO: Specify the event click location as a click box, not exact coordinates.
# TODO: Add a 3-5 minute idle time randomly in the run


class MouseEvent:
    NUM_FIELDS = 6

    def __init__(self, id: str, x: int, y: int,
                 button: str, min_delay_sec: float, max_delay_sec: float):
        self.id = id
        self.x = x
        self.y = y
        self.button = button
        self.min_delay_sec = min_delay_sec
        self.max_delay_sec = max_delay_sec

    def __str__(self):
        return ",".join([
            f"{self.id}",
            f"{self.x}",
            f"{self.y}",
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
                 max_rand_mvmts: int = 5,
                 mouse_delay_sec: tuple[float] = (0.25, 0.75)):
        self.runtime_sec = runtime_sec
        self.max_rand_mvmts = max_rand_mvmts
        self.mouse_delay_sec = mouse_delay_sec
        self.event_file = event_file

    def __str__(self):
        return "".join([
            "script config:\n\t",
            f"runtime_sec = {self.runtime_sec}\n\t",
            f"event_file = {self.event_file}\n\t",
            f"max_rand_mvmts = {self.max_rand_mvmts}\n\t",
            f"mouse_delay_sec = {self.mouse_delay_sec}"
        ])


class Script:
    def __init__(self, conf: ScriptConfig):
        self._conf = conf
        self._events = self.__parse_events(conf.event_file)
        self._mouse_ctrl = MouseController()

    def __parse_events(self, script_csv: str) -> list[MouseEvent]:
        events = []
        with open(script_csv, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if (len(row) != MouseEvent.NUM_FIELDS):
                    raise ValueError(
                        f"invalid number of fields in CSV row: {row}\n")
                id, x, y, button, min_delay_sec, max_delay_sec = row
                events.append(MouseEvent(id,
                              int(x.strip()),
                              int(y.strip()),
                              button,
                              float(min_delay_sec.strip()),
                              float(max_delay_sec.strip())))
        return events

    def __do_random_mvmts(self):
        nrand_mvmts = random.randrange(self._conf.max_rand_mvmts)
        for _ in range(nrand_mvmts):
            self._mouse_ctrl.perform_random_movement(
                self._conf.mouse_delay_sec)

    def __exec_event(self, event: MouseEvent):
        mouse_delay_sec = random.uniform(*self._conf.mouse_delay_sec)
        print(f"performing event: {event} with delay {mouse_delay_sec}")
        self._mouse_ctrl.move_mouse(event.x, event.y, mouse_delay_sec)

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
        curr_time = time.time()
        while (curr_time - start_time) < self._conf.runtime_sec:
            self.__exec_events()
            curr_time = time.time()


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

        parser = argparse.ArgumentParser(
            description="run a runescape bot script",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("script", type=str,
                            help="path to CSV file containing script commands")
        parser.add_argument("--runtime", "-r", type=int, default=3600,
                            help="script runtime in seconds")
        parser.add_argument("--max-rand-mvmts", "-m", type=int, default=5,
                            help="max number of random mouse movements "
                            "performed before each event")
        parser.add_argument('--mouse-delay', "-d", nargs='+',
                            type=float, default=[0.25, 0.75],
                            help="defines a range in seconds from which a "
                            "delay for each mouse movement will be "
                            "randomly chosen")
        args = parser.parse_args()

        conf = ScriptConfig(
            args.runtime, args.script,
            args.max_rand_mvmts, args.mouse_delay)
        script = Script(conf)

        print("starting script in 5 seconds...")
        time.sleep(5)
        script.run()
    except KeyboardInterrupt:
        print('signal SIGINT caught, exiting')
