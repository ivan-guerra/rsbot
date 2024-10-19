import unittest
from unittest.mock import patch
from rsbot.bot import ClickBox, MouseController


class TestClickBox(unittest.TestCase):

    def test_init_valid_vertices(self):
        vertices = [(0, 0), (0, 1), (1, 1), (1, 0)]
        click_box = ClickBox(vertices)
        self.assertEqual(click_box.vertices(), vertices)

    def test_init_invalid_vertices(self):
        vertices = [(0, 0), (0, 1), (1, 1)]
        with self.assertRaises(ValueError):
            ClickBox(vertices)

    def test_get_rand_point(self):
        vertices = [(0, 0), (0, 1), (1, 1), (1, 0)]
        click_box = ClickBox(vertices)
        rand_point = click_box.get_rand_point()
        x, y = rand_point
        self.assertTrue(0 <= x <= 1)
        self.assertTrue(0 <= y <= 1)

    def test_str_representation(self):
        vertices = [(0, 0), (0, 1), (1, 1), (1, 0)]
        click_box = ClickBox(vertices)
        self.assertEqual(str(click_box), "(0,0),(0,1),(1,1),(1,0)")


class TestMouseController(unittest.TestCase):

    def test_move_within_bounds(self):
        mouse_controller = MouseController()
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.position', return_value=(100, 100)):
                with self.assertRaises(ValueError):
                    mouse_controller.move((2000, 100), 5, 1)
                with self.assertRaises(ValueError):
                    mouse_controller.move((100, -50), 5, 1)

    def test_move_invalid_speed(self):
        mouse_controller = MouseController()
        with patch('pyautogui.size', return_value=(1920, 1080)):
            with patch('pyautogui.position', return_value=(100, 100)):
                with self.assertRaises(ValueError):
                    mouse_controller.move((500, 500), 5, 0)

    def test_click_invalid_button(self):
        mouse_controller = MouseController()
        with self.assertRaises(ValueError):
            mouse_controller.click("middle")


if __name__ == '__main__':
    unittest.main()
