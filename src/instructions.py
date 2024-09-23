"""Define the set of instructions supported by the rsbot virtual machine."""

from time import sleep
from random import uniform, random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import deque
from PIL import ImageGrab
from pynput.keyboard import Controller, Key
from pyautogui import moveTo, click


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

        Args:
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

        Args:
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
        min_delay, max_delay = float(self._args[0]), float(self._args[1])
        sleep(uniform(min_delay, max_delay))

        self._ctxt.pc += 1


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
        click(button=button)

        self._ctxt.pc += 1


class MouseMove(Instruction):
    """Represents an instruction to move the mouse."""

    def __init__(self, ctxt: Context):
        """Initialize a MouseMove instruction object."""
        super().__init__("msmv", 3, ctxt)

    def execute(self) -> None:
        """Move the mouse to the specified coordinates with a random speed."""
        x, y = int(self._args[0]), int(self._args[1])
        duration = float(self._args[2])
        moveTo(x, y, duration=duration)

        self._ctxt.pc += 1


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
        super().__init__("msmvcb", 9, ctxt)

    def execute(self) -> None:
        """Move the mouse to a random point within the specified click box with a random speed."""
        clickbox = []
        for i in range(0, len(self._args) - 1, 2):
            clickbox.append(Point2D(int(self._args[i]), int(self._args[i+1])))

        pos = self._get_rand_point(clickbox)
        duration = float(self._args[-1])
        moveTo(pos.x, pos.y, duration=duration)

        self._ctxt.pc += 1


class MouseMoveColor(Instruction):
    """Represents an instruction to move the mouse to the center of a color cluster on the screen."""  # pylint: disable=line-too-long

    def _flood_fill(self,  # pylint: disable=too-many-locals, too-many-arguments
                    start_x,
                    start_y,
                    img,
                    width,
                    height,
                    target_rgb,
                    tolerance,
                    visited) -> list[tuple[int]]:
        """Perform flood fill algorithm starting from the specified coordinates (start_x, start_y) on the image 'img'.

        The algorithm fills the area of connected pixels that match the target color within the given tolerance.

        Args:
            start_x: The x-coordinate to start the flood fill.
            start_y: The y-coordinate to start the flood fill.
            img: The image to perform flood fill on.
            width: The width of the image.
            height: The height of the image.
            target_rgb: The target RGB color to match within the tolerance.
            tolerance: The tolerance value for color matching.
            visited: A set to keep track of visited pixels.

        Returns:
            A list of coordinates (tuples) representing the filled area.
        """
        # Stack for pixels to visit (breadth-first search).
        queue = deque([(start_x, start_y)])
        cluster_coords = []

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue

            visited.add((x, y))
            r, g, b = img[x, y]

            # Check if the pixel color matches the target color within the tolerance.
            if (abs(r - target_rgb[0]) <= tolerance and
                abs(g - target_rgb[1]) <= tolerance and
                    abs(b - target_rgb[2]) <= tolerance):

                cluster_coords.append((x, y))

                # Explore neighboring pixels (4-connectivity).
                if x > 0:
                    queue.append((x - 1, y))  # left
                if x < width - 1:
                    queue.append((x + 1, y))  # right
                if y > 0:
                    queue.append((x, y - 1))  # up
                if y < height - 1:
                    queue.append((x, y + 1))  # down

        return cluster_coords

    def _find_largest_color_cluster(self, target_rgb, tolerance=10, min_cluster_size=10) -> Point2D:  # pylint: disable=too-many-locals
        """Find the largest cluster of pixels in a screenshot that match the target color within a given tolerance.

        Args:
            target_rgb (Tuple[int, int, int]): The RGB values of the target color to search for.
            tolerance (int): The maximum difference allowed in RGB values to consider a pixel a match (default is 10).
            min_cluster_size (int): The minimum size of a cluster to be considered the largest (default is 4).

        Returns:
            Point2D: The center point of the largest cluster if it meets the minimum size threshold, otherwise None.
        """
        # Capture the screen
        screenshot = ImageGrab.grab()
        img = screenshot.load()

        width, height = screenshot.size
        visited = set()

        largest_cluster = []

        # Search for pixels matching the target color and group them into clusters.
        for x in range(width):
            for y in range(height):
                if (x, y) not in visited:
                    r, g, b = img[x, y]
                    if (
                        abs(r - target_rgb[0]) <= tolerance and
                        abs(g - target_rgb[1]) <= tolerance and
                        abs(b - target_rgb[2]) <= tolerance
                    ):
                        # Perform flood fill to find the cluster of nearby matching pixels.
                        cluster = self._flood_fill(
                            x, y, img, width, height, target_rgb, tolerance, visited)

                        # If this cluster is the largest so far, store it.
                        if len(cluster) > len(largest_cluster):
                            largest_cluster = cluster

        # Return the center of the largest cluster if it's larger than the minimum threshold.
        if len(largest_cluster) >= min_cluster_size:
            # Calculate the center of the cluster.
            x_coords = [coord[0] for coord in largest_cluster]
            y_coords = [coord[1] for coord in largest_cluster]
            center_x = sum(x_coords) // len(x_coords)
            center_y = sum(y_coords) // len(y_coords)
            return Point2D(center_x, center_y)

        return None

    def __init__(self, ctxt: Context):
        """Initialize a MouseMoveColor instruction object."""
        super().__init__("msmvcolor", 6, ctxt)

    def execute(self) -> None:
        """Find the largest color cluster with the specified RGB values.

        Raises:
            ValueError: If unable to find a color cluster with the specified RGB values
        """
        rgb = (int(self._args[0]), int(self._args[1]), int(self._args[2]))
        tolerance, min_cluster_size = int(self._args[3]), int(self._args[4])
        pos = self._find_largest_color_cluster(
            rgb, tolerance=tolerance, min_cluster_size=min_cluster_size)
        if not pos:
            raise ValueError(
                f"unable to find color cluster with color={rgb}, "
                f"search params are tolerance={tolerance} and min_cluster_size={min_cluster_size}")

        duration = float(self._args[5])
        moveTo(pos.x, pos.y, duration=duration)

        self._ctxt.pc += 1


class PressKey(Instruction):
    """Represents an instruction to simulate pressing a key for a specified duration."""

    def __init__(self, ctxt: Context):
        """Initialize a PressKey instruction object with the given execution context."""
        super().__init__("pkey", 2, ctxt)

    def execute(self) -> None:
        """Simulate pressing a key for a specified duration.

        Raises:
            ValueError: If the specified key is not supported.
        """
        key = self._args[0]
        # Space is the only "special" key supported.
        if key == "space":
            key = Key.space
        delay = float(self._args[1])

        keyboard = Controller()
        keyboard.press(key)
        sleep(delay)
        keyboard.release(key)

        self._ctxt.pc += 1


class Subtract(Instruction):
    """Represents an instruction to subtract an immediate value from a register."""

    def __init__(self, ctxt: Context):
        """Initialize a Subtract instruction object."""
        super().__init__("sub", 2, ctxt)

    def execute(self) -> None:
        """Subtract the immediate value from the specified register."""
        register = self._args[0]
        immediate = int(self._args[1])

        if register not in self._ctxt.registers:
            raise ValueError(
                f"attempted to access unknown register '{register}'")
        self._ctxt.registers[register] -= immediate
        self._ctxt.pc += 1


class Store(Instruction):
    """Represents an instruction to store an immediate value in a register."""

    def __init__(self, ctxt: Context):
        """Initialize a Store instruction object."""
        super().__init__("store", 2, ctxt)

    def execute(self) -> None:
        """Store the immediate value in the specified register."""
        register = self._args[0]
        immediate = int(self._args[1])

        if register not in self._ctxt.registers:
            raise ValueError(
                f"attempted to access unknown register '{register}'")
        self._ctxt.registers[register] = immediate
        self._ctxt.pc += 1


class JumpNotEqual(Instruction):
    """Represents an instruction to jump to a label if the value in register R0 is not zero."""

    def __init__(self, ctxt: Context):
        """Initialize a JumpNotEqual instruction object."""
        super().__init__("jne", 1, ctxt)

    def execute(self) -> None:
        """Jump to the specified label if the value in register R0 is not 0."""
        label = self._args[0]

        if self._ctxt.registers["R0"] == 0:
            self._ctxt.pc += 1
        else:
            if label not in self._ctxt.labels:
                raise ValueError(f"unknown label referenced '{label}'")
            self._ctxt.pc = self._ctxt.labels[label]
