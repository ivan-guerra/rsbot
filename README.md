# rsbot

Run a Runescape 3 or Old School Runescape autoclicker script.

Randomization is a big part of this autoclicker's strategy for avoiding Jagex's
bot detection system. Many of the command line options are min/max pairs that
allow the user to tailor a range of random values. Additionally, the [pyHM][1]
module is used to simulate human like mouse movements. See [this blog post][3]
to learn more about the design of this autoclicker bot.

### Running the Script

To run this script, your system must meet the following requirements:

- Windows or Linux OS.
- A working Internet connection.
- [Python3][2]

Follow these steps to launch the script:

1. Create a Python virtualenv:

```bash
python -m venv rsbot_venv
```

2. Source the virtual environment:

```bash
rsbot_venv\Scripts\activate.bat # Windows
source rsbot_venv/bin/activate.sh # Linux
```

3. Install all dependencies using `pip`:

```bash
pip install -r requirements.txt
```

4. Run the script with the `--help/-h` option to view the program usage message
   and available options:

```bash
./bot.py --help
```

Below is an example that runs the included RS3 fletching script:

```bash
./bot.py --runtime 7200 --start-delay 3 --idle-time 2 4 scripts/fletching.json
```

It's likely that running the above command led to bunch of misclicks. You should
generate your own click event file following the steps outlined in the next
section.

### Writing Custom Scripts

RSbot has one required argument which is the path to a JSON file containing
click events. The event script must have the following format:

```json
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
```

The event script contains a top-level `events` array with one or more click
events. Each click event has five fields:

- `id`: A string describing the event.
- `click_box`: An array of 2D points that form a click box. When this event
  executes, a click will be performed within the click box's bounds. **Note, the
  points do not need to form a perfect square.** Any four points forming a
  box-ish region will be accepted.
- `button`: Which mouse button to click. Only "left" and "right" buttons are
  currently supported.
- `min_delay_sec`: The minimum delay in seconds the script will insert after the
  click is performed.
- `max_delay_sec`: The maximum delay in seconds the script will insert after the
  click is performed.

> **Note**
> If you change the game camera's orientation or if the screen resolution
> changes, you must regenerate the event script!

It can be tedious to write a click event script by hand, especially when it
comes to defining the `click_box` field. Included in this repo is the
`mkscript.py` script. `mkscript.py` allows you to input one or more click events
and outputs a rsbot ready click event file. The script will prompt you to input
all fields with the exception of the `click_box` field. For the `click_box`
field, the script will ask you to select four points by positioning your cursor
over the desired location and then pressing the `;` key. Once you've selected
your four points, press `ESC` to continue entering events. Press `CTRL+c` in the
terminal in which you launched `mkscript.py` to save all events to disk and
exit.

Follow these steps to generate a custom click event file:

1. Create a Python virtualenv:

```bash
python -m venv rsbot_venv
```

2. Source the virtual environment:

```bash
rsbot_venv\Scripts\activate.bat # Windows
source rsbot_venv/bin/activate.sh # Linux
```

3. Install all dependencies using `pip`:

```bash
pip install -r requirements.txt
```

4. Run the script passing in the path to the output script file:

```bash
./mkscript.py scripts/fletching.json
```

5. Follow the prompts to input one or more click events.

6. Press `CTRL+c` to save all events to disk and exit.

[1]: https://pypi.org/project/pyHM/
[2]: https://www.python.org/downloads/
[3]: https://programmador.com/posts/2024/rsbot/
