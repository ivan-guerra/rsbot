# rsbot

Run a Runescape 3 or Old School Runescape bot script. This bot is suitable for
automating basic tasks and skill training. It's essentially a programmable
autoclicker or color bot. You program the bot using an assembly like language
that we'll refer to as rsbot script. You then run your script through the
`rsbot.py` virtual machine. The virtual machine will repeatedly execute your
script until a configurable stop time is reached.

### Installation

To run this script, your system must meet the following requirements:

- Windows or Linux OS.
- A working Internet connection.
- Python3

Follow these steps to launch the script:

1. Create a Python virtualenv:

```bash
python -m venv venv
```

2. Source the virtual environment:

```bash
venv\Scripts\activate.bat # Windows
source venv/bin/activate.sh # Linux
```

3. Install all dependencies using `pip`:

```bash
pip install -r requirements.txt
```

4. Run the script with the `--help/-h` option to view the program usage message
   and available options:

```bash
./rsbot.py --help
```

Below is an example that runs the included RS3 fletching script:

```bash
./bot.py --runtime 7200 --start-delay 3 --idle-time 2 4 scripts/fletching.rsbot
```

You'll need to write your own script or tune the examples. See the next section
for a list of the available instructions.

### Writing Custom Scripts

RSbot has one required argument which is the path to a text file containing
rsbot script code. RSbot script is an assembly like language that allows you to
perform high level tasks such as clicking a cluster of pixels with a particular
color or moving the mouse. Many of the instructions include arguments that
randomize the action to help with bot detection avoidance. Below is a complete
list of the instructions available to you:

- `delay min:float max:float`: Inserts a random delay in the range [min, max].
- `msclk button:str`: Clicks a mouse button. `button` must be one of either
  `left` or `right`.
- `msmv x:int y:int duration:float`: Moves the mouse to position (x, y). The
  movement is carried out over duration seconds.
- `msmvcb x1:int y1:int x2:int y2:int x3:int y3:int x4:int y4:int
duration:float`: Moves the mouse to a random point within the bounds of the
  quadrilateral formed by the four parameter vertices.
  The movement is carried out over duration seconds.
- `msmvcolor r:int g:int b:int tolerance:int min_cluster_size:int duration:float`: Moves the mouse to the largest cluster of pixels within the specified tolerance. The movement is carried out over duration seconds.
- `pkey key:str delay:float`: Presses and releases the parameter key with the
  specified delay inserted between the press and release events.
- `sub register:str value:int`: Subtracts `value` from the contents of
  `register`.
- `store register:str value:int`: Stores `value` in `register`.
- `jne label:str`: Jump to the label if the value in register `R0` is not zero.
  This instruction in conjunction with `sub` and `store` can be used to implement
  a loop.

> **Note**: The RSbot virtual machine currently includes only a single register:
> `R0`. `R0` is primarily used for looping. I haven't found a need to include
> additional registers yet.
