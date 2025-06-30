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

    def test_04_call_many_times(self):
        """Test calling the elevator multiple times in quick succession"""
        
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)

        # Call the elevator to floor 2
        QTest.mouseClick(self.ui.up_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(50)

        QTest.mouseClick(self.ui.up_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(50)

        QTest.mouseClick(self.ui.up_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(50)

        # Check if the elevator is at the correct floor
        while (self.system.elevators[0].state != ElevatorState.stopped_closing_door):
            self.assertLessEqual(len([call for call in self.system.call_requests if call[2]==True]), 1)
            self.assertLessEqual(len(self.system.elevators[0].destination_floors), 1)
        
        # wait for the elevator to finish
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)

    def test_03_close_upon_reaching(self):
        """Test closing the elevator door upon reaching a floor"""
    
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
        # Click THE close button when the elevator arrived at 1.
        QTest.mouseClick(self.ui.up_buttons[1], Qt.MouseButton.LeftButton)
        QTest.mouseClick(self.ui.elevators[0].close_btn, Qt.MouseButton.LeftButton)
        while (self.system.elevators[0].state == ElevatorState.stopped_door_closed):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[0].state, [ElevatorState.stopped_door_opened, ElevatorState.stopped_opening_door])
    
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertEqual(self.system.elevators[0].current_floor, 1)

    def tearDown(self):
        """Cleanup after each test case"""

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
