#!/usr/bin/env python3

"""Spawn a window showing the location and color of the pixel pointed to by the cursor."""

import sys
import pyautogui
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PIL import ImageGrab


class RGBWindow(QWidget):
    """A class representing a window that displays the RGB value of the pixel under the cursor.

    Attributes:
        rgb_label (QLabel): A label to display the RGB value of the pixel.
        pos_label (QLabel): A label to display the cursor position.
        timer (QTimer): A timer to update the RGB value and cursor position.
    """

    def __init__(self):
        """Initialize the RGBWindow class."""
        super().__init__()

        # Setup the layout.
        self.rgb_label = QLabel("RGB Value: (0, 0, 0)", self)
        self.pos_label = QLabel("Cursor Position: (0, 0)", self)

        layout = QVBoxLayout()
        layout.addWidget(self.pos_label)
        layout.addWidget(self.rgb_label)
        self.setLayout(layout)

        # Set window properties.
        self.setWindowTitle("RGB Color Picker")
        self.setGeometry(100, 100, 250, 100)

        # Timer to update the RGB value and position every 100 ms.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(100)

    def update_info(self):
        """Update the labels with the RGB value and cursor location."""
        # Get the current mouse cursor position
        x, y = pyautogui.position()

        # Capture the screen at the cursor position
        screen = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
        rgb_value = screen.getpixel((0, 0))

        # Update the labels with the RGB value and cursor position
        self.pos_label.setText(f"Cursor Position: ({x}, {y})")
        self.rgb_label.setText(f"RGB Value: {rgb_value}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RGBWindow()
    window.show()
    sys.exit(app.exec())
