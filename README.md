# rsbot

Create and run a Runescape 3 or Old School Runescape autoclicker script. See
[this blog post][1] to learn more about the design of this autoclicker bot.

### Requirements

rsbot only supports Linux. To run this utility, your system must meet the
following requirements:

- Python3.11+
- [xdotool][2]

Both requirements can be installed using your distro's package manager. For
example, on an Arch Linux system:

```bash
pacman -S python xdotool
```

### Installation

rsbot is a Python package. Follow the steps below to install the package:

1. Clone the repo:

```bash
git clone https://github.com/ivan-guerra/rsbot.github
```

2. Install the package with `pip`:

```bash
pip install rsbot/
```

Once the package is installed, you can run rsbot from the command line via the
`rsbot` command. Run `rsbot --help` for complete usage info.

### Bot Script Format

rsbot has one required argument which is the path to a JSON file containing
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
    }
  ]
}
```

The event script contains a top-level `events` array with one or more click
events. Each click event has five fields:

- `id`: A string describing the event.
- `click_box`: An array of 2D points that form a click box. When this event
  executes, a click will be performed within the click box's bounds. **Note, the
  points do not need to form a perfect square.** Any four points forming a box-ish
  region will be accepted.
- `button`: Which mouse button to click. Only "left" and "right" buttons are
  currently supported.
- `min_delay_sec`: The minimum delay in seconds the script will insert after the
  click is performed.
- `max_delay_sec`: The maximum delay in seconds the script will insert after the
  click is performed.

It can be tedious to write a click event script by hand. Included in this repo
is the [`mkscript.py`](scripts/mkscript.py) script. `mkscript.py` allows you to
input one or more click events and outputs a rsbot ready click event file. Run
`mkscript.py --help` for complete usage info.

[1]: https://programmador.com/posts/2024/rsbot/
[2]: https://www.semicomplete.com/projects/xdotool/
