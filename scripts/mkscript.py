#!/usr/bin/env python3
"""Record a rsbot click event JSON script file.

This script allows the user to enter one or more rsbot click events and outputs
them to a JSON file. The script has one required argument which is the file to
which click events will be written. The user inputs click event information
through the console with the exception of the click box points. After prompting
the user to input click box points, the script will listen for four ';'
keypresses. Each ';' keypress causes the script to record the location of the
mouse (i.e., one of the four points forming the click box region). The script
can be terminated at any time by pressing CTRL+C or sending SIGINT directly to
the process. Upon termination, the all click events if any will be written to
the output file.
"""

import argparse
import json
from pynput import keyboard, mouse
from rsbot import bot

# Global used to store mouse positions (see on_press()).
points = []


def on_press(key):
    """Detect ';' keypresses.

    If the user presses ';', the function records the current mouse location in
    the global list of locations, points. Four ';' presses terminate the
    listener.
    """
    try:
        if key.char == ";":
            mouse_ctrl = mouse.Controller()
            points.append(mouse_ctrl.position)

            target_num_points = 4
            if len(points) == target_num_points:
                return False
        return True
    except AttributeError:
        # This is in case the key has no `char` attribute (like special keys).
        return True


def save_events(outfile: str, click_events: list[bot.MouseEvent]) -> None:
    """Save click events in JSON format."""
    with open(outfile, mode="w", encoding="ascii") as json_file:
        event_dicts = []
        for e in click_events:
            event_dict = {
                "id": e.event_id,
                "click_box": e.click_box.vertices(),
                "button": e.button,
                "min_delay_sec": e.min_delay_sec,
                "max_delay_sec": e.max_delay_sec
            }
            event_dicts.append(event_dict)

        output = {"events": event_dicts}
        json.dump(output, json_file, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="record an rsbot click event script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("outfile", type=str,
                        help="JSON outputfile where events will be written")
    args = parser.parse_args()

    try:
        print("press CTRL+c to exit")
        events = []
        while True:
            event = bot.MouseEvent(event_id="",
                                   click_box=None,
                                   button="left",
                                   min_delay_sec=0,
                                   max_delay_sec=0)
            event.event_id = input("id: ")
            event.button = input("button ('left' or 'right'): ")
            event.min_delay_sec = float(input("min delay (sec): "))
            event.max_delay_sec = float(input("max delay (sec): "))
            print("press ';' at each of the four click box locations")
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()

            event.click_box = bot.ClickBox(points)
            events.append(event)
            print(f"saved event: {event}")
            points.clear()
    except ValueError as e:
        print(e)
    except KeyboardInterrupt:
        if events:
            print(f"writing events to {args.outfile}")
            save_events(args.outfile, events)
