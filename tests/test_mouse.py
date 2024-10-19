import unittest
from unittest.mock import patch
from rsbot.mouse import move


class TestMoveMouse(unittest.TestCase):

    @patch('rsbot.mouse.os.system')
    @patch('rsbot.mouse.subprocess.call')
    def test_move(self, mock_subprocess_call, mock_os_system):
        init_pos = (0, 0)
        fin_pos = (100, 100)
        deviation = 5
        speed = 10

        move(init_pos, fin_pos, deviation, speed)

        mock_os_system.assert_called_with('chmod +x /tmp/mouse.sh')
        mock_subprocess_call.assert_called_with(['/tmp/mouse.sh'])


if __name__ == '__main__':
    unittest.main()
