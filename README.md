# rsbot

A RuneScape automation tool written in Rust that executes scripted mouse clicks
and keypresses. Supports both RuneScape 3 and Old School RuneScape.

## Features

- **Natural mouse movement**: Uses Bézier curves for human-like cursor paths
- **Randomized delays**: Configurable delay ranges to avoid detection patterns
- **Mouse and keyboard events**: Support for clicks and keypresses
- **Configurable runtime**: Set how long the bot should run
- **Debug logging**: Optional logging to troubleshoot scripts

## Requirements

rsbot only supports Linux. Your system must have:

- Rust toolchain (rustc 1.70+, cargo)
- X11 display server

## Usage

```bash
rsbot [OPTIONS] <SCRIPT>
```

**Arguments:**

- `<SCRIPT>` - Path to the bot script JSON file

**Options:**

- `-r, --runtime <SECONDS>` - Script runtime in seconds (default: 3600)
- `-g, --debug` - Enable debug logging
- `-h, --help` - Print help information
- `-V, --version` - Print version information

**Example:**

```bash
# Run a ivy woodcutting script for 30 minutes with debug logging enabled
rsbot -r 1800 -g scripts/ivy_wc.json
```

## Bot Script Format

Bot scripts are JSON arrays containing event objects. Two event types are
supported:

### Mouse Event

```json
{
  "type": "mouse",
  "id": "click bank",
  "pos": [925, 308],
  "delay_rng": [1000, 3000]
}
```

- `type`: Must be `"mouse"`
- `id`: Description of the event
- `pos`: `[x, y]` screen coordinates to click
- `delay_rng`: `[min_ms, max_ms]` random delay range after click

### KeyPress Event

```json
{
  "type": "keypress",
  "id": "drop items",
  "keycode": "d",
  "delay_rng": [100, 200],
  "count": 28
}
```

- `type`: Must be `"keypress"`
- `id`: Description of the event
- `keycode`: Single character to press
- `delay_rng`: `[min_ms, max_ms]` random delay range after all keypresses
- `count`: Number of times to press the key
