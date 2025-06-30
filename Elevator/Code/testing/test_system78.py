import unittest
import time
import sys
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
from elevator_system import ElevatorSystem
from elevator import ElevatorState, Direction
from elevator_UI import ElevatorSystemUI

class TestSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        self.system = ElevatorSystem(num_elevators=2, max_floor=3, identity="Test")
        self.ui = ElevatorSystemUI(self.system, num_elevators=2, max_floors=3)
        #  self.system.elevators[0].delt = 0.2
        #  self.system.elevators[1].delt = 0.2
        self.system.elevators[0].remain_open_time=1
        self.ui.show()
        QTest.qWait(2000)  # 确保UI完全加载

    def test_08_call_when_closing(self):
        """Test calling the elevator while it is closing its door"""
        for t in self.system.threads:
            t.start()

        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)

        # Call the elevator to floor 1
        QTest.mouseClick(self.ui.up_buttons[1], Qt.MouseButton.LeftButton)
        QTest.qWait(1000)

        while (self.system.elevators[0].state != ElevatorState.stopped_closing_door):
            QTest.qWait(20)

        self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_closing_door)
        # let the door close for some time, but not close totally.
        QTest.qWait(200)
        self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_closing_door)
        QTest.mouseClick(self.ui.up_buttons[1], Qt.MouseButton.LeftButton)
        QTest.qWait(200)
        self.assertIn(self.system.elevators[0].state, [ElevatorState.stopped_door_opened, ElevatorState.stopped_opening_door])

    def test_07_open_door_when_moving(self):
        """Test opening the elevator door while it is moving"""
        for t in self.system.threads:
            t.start()

        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)

        # Call the elevator to floor 3
        QTest.mouseClick(self.ui.down_buttons[3], Qt.MouseButton.LeftButton)
        QTest.qWait(400)

        while self.system.elevators[0].state != ElevatorState.stopped_door_closed:
            # Open the door while the elevator is moving
            QTest.mouseClick(self.ui.elevators[0].open_btn, Qt.MouseButton.LeftButton)
            # Check if the elevator is still moving
            self.assertIn(self.system.elevators[0].state, [ElevatorState.up, ElevatorState.down])
            QTest.qWait(100)

        # Check if the door is opened
        self.assertEqual(self.system.elevators[0].current_floor, 3)


    def tearDown(self):
        """Cleanup after each test case"""

        for t in self.system.threads:
            t.join(timeout=1)
        self.ui.close()
        self.ui.deleteLater()
        QTest.qWait(1000)  # Ensure the UI is closed before the next test

        # import gc
        # gc.collect()

    @classmethod
    def tearDownClass(cls):
        """Cleanup work after all test cases are executed"""
        # Ensure the event loop runs long enough to display the window
        QTest.qWait(1000)  # Delay 1 second to ensure the window is displayed
        cls.app.quit()
if __name__ == '__main__':
    unittest.main()
