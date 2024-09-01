# RSBot

Run a Runescape 3 or Old School Runescape autoclicker script.

Randomization is a big part of this autoclicker's strategy for avoiding Jagex's
bot detection system. Many of the command line options are min/max pairs that
allow the user to tailor a range of random values. Additionally, the [pyHM][1]
module is used to simulate human like mouse movements.

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

Below is an example that runs the included RS3 fletching script on a 1920x1080
display:

```bash
./bot.py --idle-time 2 4.8 --runtime 7200 --start-delay 3 --idle-time 2 4
scripts/fletching.json
```

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
> Each script is resolution dependent. If you create a script for a 1920x1080
> display and then switch to a 1366x768 display, the script will misclick!

[1]: https://pypi.org/project/pyHM/
[2]: https://www.python.org/downloads/
