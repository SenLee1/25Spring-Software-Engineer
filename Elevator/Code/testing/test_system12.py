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
        for t in self.system.threads:
            t.start()
        #  self.system.elevators[0].delt = 0.2
        #  self.system.elevators[1].delt = 0.2
        self.system.elevators[0].remain_open_time=1
        self.ui.show()
        QTest.qWait(2000)  # 确保UI完全加载

    def test_01_stop_at_non_int_floor(self):
        """Test opening the elevator door at a non-integer floor"""
    
        # Click the open door button on elevator 1
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
        floor_btn = self.ui.elevators[0].floor_buttons[3]
        QTest.mouseClick(floor_btn, Qt.MouseButton.LeftButton)
        while (self.system.elevators[0].state != ElevatorState.stopped_door_closed or self.system.elevators[0].current_floor != 3):
            self.assertFalse((self.system.elevators[0].car[0] != 2 and self.system.elevators[0].car[0] != 3 and self.system.elevators[0].car[0] != 1) and self.system.elevators[0].state != ElevatorState.up)
            QTest.qWait(100)
    
        # Check the state of the elevator
        self.assertEqual(self.system.elevators[0].current_floor, 3)
        self.assertEqual(self.system.elevators[1].state, ElevatorState.stopped_door_closed)
    
        # Wait for the door to remain open
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[0].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])

    def test_02_1_goingdown_exceeding_floors(self):
        """Test going to a floor that exceeds the maximum floor limit"""

        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
        floor_btn = self.ui.elevators[0].floor_buttons[0] 
        QTest.mouseClick(floor_btn, Qt.MouseButton.LeftButton)
        while (self.system.elevators[0].car[0]>1):
            QTest.qWait(50)

        # Click 1 when elevator exceeds 1 and going to -1
        QTest.mouseClick(self.ui.elevators[0].floor_buttons[1], Qt.MouseButton.LeftButton)
        # Check the state of the elevator
        
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)

        # check the elevator will eventually stop at floor 1
        self.assertEqual(self.system.elevators[0].current_floor, 1)

    def test_02_2_goingup_exceeding_floors(self):
        """Test going to a floor that exceeds the maximum floor limit"""

        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
        floor_btn = self.ui.elevators[0].floor_buttons[3] 
        QTest.mouseClick(floor_btn, Qt.MouseButton.LeftButton)
        while (self.system.elevators[0].car[0]<2):
            QTest.qWait(50)

        # Click 2 when elevator exceeds 2 and going to 3
        QTest.mouseClick(self.ui.elevators[0].floor_buttons[2], Qt.MouseButton.LeftButton)
        
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)

        # check the elevator will eventually stop at floor 2
        self.assertEqual(self.system.elevators[0].current_floor, 2)

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
