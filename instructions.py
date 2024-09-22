"""Define the set of instructions supported by the rsbot virtual machine."""

from time import sleep
from random import randint, uniform, random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pyHM import mouse


@dataclass
class Context:
    """A class representing the execution context of the program.

    Attributes:
        pc        (int): A integer representing the program counter.
        registers (dict[str, int]): A dictionary mapping register names to their values.
        labels    (dict[str, int]): A dictionary mapping label names to their addresses.
    """

    pc: int
    registers: dict[str, int]
    labels: dict[str, int]


@dataclass
class Point2D:
    """A class representing a 2D point with x and y coordinates.

    Attributes:
        x (int): The x-coordinate of the point.
        y (int): The y-coordinate of the point.
    """

    x: int
    y: int


class Instruction(ABC):
    """Abstract base class representing an instruction.

    This class defines the structure of an instruction object with a type,
    number of arguments, and methods to parse and execute the instruction.
    """

    def __init__(self, itype: str, nargs: int, ctxt: Context):
        """Initialize an Instruction object with the given type and number of arguments.

        Parameters:
            itype (str): The type of the instruction.
            nargs (int): The number of arguments expected for the instruction.
            ctxt  (Context): The instruction's execution context.
        """
        self._itype = itype
        self._nargs = nargs
        self._args = []
        self._ctxt = ctxt

    @property
    def itype(self) -> str:
        """Get the type of the instruction."""
        return self._itype

    def parse(self, raw_inst: str) -> None:
        """Parse the raw instruction string and store the arguments.

        Parameters:
            raw_inst (str): The raw instruction string to parse.

        Raises:
            ValueError: If the number of arguments in the raw instruction does
                        not match the expected number.
        """
        components = raw_inst.split(" ")[1:]
        if len(components) != self._nargs:
            raise ValueError(
                f"{self._itype} requires {self._nargs} but received {len(components)} args")
        self._args = components

    @abstractmethod
    def execute(self) -> None:
        """Abstract method to execute the instruction."""


class Delay(Instruction):
    """Represents an instruction to insert a randomized delay."""

    def __init__(self, ctxt: Context):
        """Initialize a Delay object with default values."""
        super().__init__("delay", 2, ctxt)

    def execute(self) -> None:
        """Delay by sleeping for a random amount of time between the specified delays."""
        min_delay, max_delay = int(self._args[0]), int(self._args[1])
        sleep(randint(min_delay, max_delay))


class MouseClick(Instruction):
    """Represents an instruction to perform a mouse click."""

    def __init__(self, ctxt: Context):
        """Initialize a MouseClick object with default values."""
        super().__init__("msclk", 1, ctxt)

    def execute(self) -> None:
        """Simulate a mouse click based on the provided button type."""
        button = self._args[0]
        if button not in ["left", "right"]:
            raise ValueError(f"unknown button type '{button}'")

        if button == "left":
            mouse.click()
        elif button == "right":
            mouse.right_click()


class MouseMove(Instruction):
    """Represents an instruction to move the mouse."""

    def __init__(self, ctxt: Context):
        """Initialize a MouseMove instruction object."""
        super().__init__("msmv", 4, ctxt)

    def execute(self) -> None:
        """Move the mouse to the specified coordinates with a random speed."""
        x, y = int(self._args[0]), int(self._args[1])
        spd_min, spd_max = float(self._args[2]), float(self._args[3])
        mouse.move(x, y, multiplier=uniform(spd_min, spd_max))


class MouseMoveClickBox(Instruction):
    """Represents an instruction to move the mouse to a random point within a specified clickbox."""

    def _random_point_in_triangle(self, v1: Point2D, v2: Point2D, v3: Point2D) -> Point2D:
        """Return a point within the bounds of the triangle formed by the parameter vertices."""
        s = random()
        t = random()

        # Ensure the point is inside the triangle.
        if s + t > 1:
            s = 1 - s
            t = 1 - t

        x = v1.x + s * (v2.x - v1.x) + t * (v3.x - v1.x)
        y = v1.y + s * (v2.y - v1.y) + t * (v3.y - v1.y)

        return Point2D(x, y)

    def _get_rand_point(self, clickbox: list[Point2D]) -> Point2D:
        """Return a random point within clickbox bounds."""
        if random() < 0.5:
            # Generate a point in the first triangle.
            return self._random_point_in_triangle(clickbox[0], clickbox[1], clickbox[2])
        # Generate a point in the second triangle.
        return self._random_point_in_triangle(clickbox[0], clickbox[2], clickbox[3])

    def __init__(self, ctxt: Context):
        """Initialize a MouseMoveClickBox instruction object."""
        super().__init__("msmvcb", 10, ctxt)

    def execute(self) -> None:
        """Move the mouse to a random point within the specified click box with a random speed."""
        clickbox = []
        for i in range(0, len(self._args) - 2, 2):
            clickbox.append(Point2D(int(self._args[i]), int(self._args[i+1])))

        pos = self._get_rand_point(clickbox)
        spd_min, spd_max = float(self._args[-2]), float(self._args[-1])
        mouse.move(pos.x, pos.y, multiplier=uniform(spd_min, spd_max))
