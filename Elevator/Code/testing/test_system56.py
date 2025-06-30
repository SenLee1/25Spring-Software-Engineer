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

    def test_05_only_one_elevator(self):
        """Test that only one elevator respond for a call"""
        for t in self.system.threads:
            t.start()
    
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
    
        # Call the elevator to floor 2
        QTest.mouseClick(self.ui.up_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
    
        # Check if the elevator is at the correct floor
        while (self.system.elevators[0].state != ElevatorState.stopped_door_opened):
            self.assertLessEqual(len([call for call in self.system.call_requests if call[2]==True]), 1)
            self.assertLessEqual(len(self.system.elevators[0].destination_floors), 1)
    
            self.assertEqual(len(self.system.elevators[1].destination_floors), 0)
            QTest.qWait(100)
    
        while self.system.elevators[0].state != ElevatorState.stopped_door_closed:
            QTest.qWait(100)
    
        # Check if the elevator is at floor 2
        self.assertEqual(self.system.elevators[0].current_floor, 2)

    def test_06_serve_eventually_satisfied(self):
        """Test that the elevator system eventually satisfies all requests"""
        for t in self.system.threads:
            t.start()
        
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)

        # Call the elevator to lloor 2
        QTest.mouseClick(self.ui.up_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(1000)

        # Check if the elevator is at the correct floor
        while (self.system.elevators[0].state != ElevatorState.stopped_door_opened):
            self.assertLessEqual(len([call for call in self.system.call_requests if call[2]==True]), 1)
            self.assertLessEqual(len(self.system.elevators[0].destination_floors), 1)
            QTest.qWait(100)

        while self.system.elevators[0].state != ElevatorState.stopped_door_closed:
            QTest.qWait(50)

        self.assertEqual(self.system.elevators[0].direction, Direction.IDLE)
        self.assertLessEqual(len([call for call in self.system.call_requests if call[2]==True]), 0)
        # Check if the elevator is at floor 2
        self.assertEqual(self.system.elevators[0].current_floor, 2)


    def tearDown(self):
        """Cleanup after each test case"""

        for t in self.system.threads:
            t.join(timeout=1)
        self.ui.close()
        self.ui.deleteLater()
        QTest.qWait(1000)  # Ensure the UI is closed before the next test

    @classmethod
    def tearDownClass(cls):
        """Cleanup work after all test cases are executed"""
        # Ensure the event loop runs long enough to display the window
        QTest.qWait(1000)  # Delay 1 second to ensure the window is displayed
        cls.app.quit()
if __name__ == '__main__':
    unittest.main()
