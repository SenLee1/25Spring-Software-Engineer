import unittest
import sys
import threading
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import sys
import time
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
from elevator_system import ElevatorSystem
from elevator import ElevatorState, Direction
from elevator_UI import ElevatorSystemUI
class TestElevatorSystemIntegration(unittest.TestCase):
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
        QTest.qWait(2000)  # wait for the UI to load

    def test_04_elevator_scheduling(self):
        """Scheduling"""

        for t in self.system.threads:
            t.start()
        #  floor 1 up; floor 2 up; floor 2 down
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(600)
        QTest.mouseClick(self.ui.up_buttons[1], Qt.MouseButton.LeftButton)
        QTest.qWait(200)
        QTest.mouseClick(self.ui.up_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(200)
        self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_opening_door)
        QTest.mouseClick(self.ui.down_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(1500)

        self.assertEqual(self.system.elevators[0].current_floor, 1)
        self.assertEqual(self.system.elevators[1].state, ElevatorState.up)
        QTest.mouseClick(self.ui.elevators[0].floor_buttons[3], Qt.MouseButton.LeftButton)
        QTest.qWait(200)
        self.assertEqual(self.system.elevators[1].destination_floors[0][0], 2)
        QTest.mouseClick(self.ui.elevators[1].floor_buttons[0], Qt.MouseButton.LeftButton)

        while not (self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertEqual(self.system.elevators[0].current_floor, 3)
        self.assertEqual(self.system.elevators[1].current_floor, 0)

    def test_02_select_floor_buttons(self):
        """Test select floor buttons"""
        #  1: (1, 2) -> TCOVER1, TCOVER2, TCOVER11, TCOVER12
        
        #   2: (2, -1) -> TCOVER1, TCOVER3, TCOVER11, TCOVER13
        for t in self.system.threads:
            t.start()
 
        QTest.mouseClick(self.ui.elevators[0].floor_buttons[2], Qt.MouseButton.LeftButton)
        QTest.qWait(100)
        QTest.mouseClick(self.ui.elevators[1].floor_buttons[0], Qt.MouseButton.LeftButton)
        QTest.qWait(100)
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertEqual(self.system.elevators[0].current_floor, 2)
        self.assertEqual(self.system.elevators[1].current_floor, 0)
        for elevator in self.system.elevators:
            self.assertEqual(elevator.direction, Direction.IDLE)

    def test_03_door_control_buttons(self):
        """Test (select_oc())"""
        # Testcase1: 
        # 1. click open door button on elevator 1
        for t in self.system.threads:
            t.start()
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
        open_btn = self.ui.elevators[0].open_btn
        QTest.mouseClick(open_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_opening_door)
        self.assertEqual(self.system.elevators[0].current_floor, 1)
        self.assertEqual(self.system.elevators[1].state, ElevatorState.stopped_door_closed)
        #  QTest.qWait(5000)
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[1].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])

        # Testcase2:
        # 2.1 click close door button on elevator when the state is stopped_door_closed
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(2000)
        open_btn = self.ui.elevators[1].open_btn
        QTest.mouseClick(open_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        self.assertEqual(self.system.elevators[1].state, ElevatorState.stopped_opening_door)
        self.assertEqual(self.system.elevators[1].current_floor, 1)
        self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_door_closed)
        QTest.mouseClick(self.ui.elevators[1].close_btn, Qt.MouseButton.LeftButton)
        #  QTest.qWait(5000)
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[1].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])

        # 2.2 click close door button when openning
        QTest.mouseClick(self.ui.reset_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(2000)
        open_btn = self.ui.elevators[1].open_btn
        QTest.mouseClick(open_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(100)
        close_btn = self.ui.elevators[1].close_btn
        QTest.mouseClick(close_btn, Qt.MouseButton.LeftButton)
        self.assertEqual(self.system.elevators[1].state, ElevatorState.stopped_opening_door)
        self.assertEqual(self.system.elevators[1].current_floor, 1)
        self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_door_closed)
        QTest.mouseClick(self.ui.elevators[1].close_btn, Qt.MouseButton.LeftButton)
        #  QTest.qWait(5000)
        while not(self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[1].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])

    
    def test_01_process_message(self):
        """Test processing messages from zmqThread"""
        # TestCase1: reset
        for t in self.system.threads:
            t.start()
        self.system.elevators[0].current_floor = 2
        if self.system.elevators[0].update_callback:
            self.system.elevators[0].update_callback(self.system.elevators[0].id)
        self.system.elevators[1].current_floor = 3
        if self.system.elevators[1].update_callback:
            self.system.elevators[1].update_callback(self.system.elevators[1].id)
        QTest.qWait(500)
        
        self.system.zmqThread.receivedMessage= "reset"
        self.system.zmqThread.messageTimeStamp = time.time()
        self.system.messageUnprocessed = True
        while(self.system.messageUnprocessed):
            QTest.qWait(10)
        #  QTest.qWait(5000)  
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[1].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])
        self.assertEqual(self.system.elevators[0].current_floor, 1)
        self.assertEqual(self.system.elevators[1].current_floor, 1)

        # TestCase2: call_up@2
        self.system.zmqThread.receivedMessage = "call_up@2"
        self.system.zmqThread.messageTimeStamp = time.time()
        self.system.messageUnprocessed = True
        #  for t in self.system.threads:
        #      t.start()
        while(self.system.messageUnprocessed):
            QTest.qWait(10)
        QTest.qWait(300)  # wait for the elevator to move and UI to respond
        while (self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(10)
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(10)
        self.assertIn(self.system.elevators[1].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])
        self.assertEqual(self.system.elevators[0].current_floor, 2)
        self.assertEqual(self.system.elevators[1].current_floor, 1)

        # TestCase3: select_floor@3#1
        self.system.zmqThread.receivedMessage = "select_floor@3#1"
        self.system.zmqThread.messageTimeStamp = time.time()
        car_loc_2 = self.system.elevators[1].car[0]
        self.system.messageUnprocessed = True
        while(self.system.messageUnprocessed):
            QTest.qWait(10)
        #  QTest.qWait(6000)  
        while (self.system.elevators[0].finished and self.system.elevators[1].finished):
            # Test the elevator can only move in its cart.
            self.assertEqual(car_loc_2, self.system.elevators[1].car[0])
            QTest.qWait(50)
        while not(self.system.elevators[0].finished and self.system.elevators[1].finished):
            QTest.qWait(50)
        self.assertIn(self.system.elevators[1].state, [ElevatorState.stopped_door_closed, ElevatorState.stopped_closing_door])
        self.assertEqual(self.system.elevators[0].current_floor, 3)
        self.assertEqual(self.system.elevators[1].current_floor, 1)

        while(self.system.elevators[0].state != ElevatorState.stopped_door_closed and self.system.elevators[0].finished == False):
            QTest.qWait(10)

        # TestCase4: open_door#1
        self.system.zmqThread.receivedMessage = "open_door#1"
        self.system.zmqThread.messageTimeStamp = time.time()
        self.system.messageUnprocessed = True
        while(self.system.messageUnprocessed):
            QTest.qWait(10)
        #  QTest.qWait(1000) 
        while self.system.elevators[0].state == ElevatorState.stopped_door_closed:
            QTest.qWait(1)
        self.assertEqual(self.system.elevators[0].current_floor, 3)
        self.assertIn(self.system.elevators[0].state, [ElevatorState.stopped_door_opened, ElevatorState.stopped_opening_door])
        self.assertEqual(self.system.elevators[1].current_floor, 1)
        QTest.qWait(2000)

        # TestCase5: close_door#1
        #  self.system.elevators[0].running = False
        #  self.system.threads[1].join()  #

        self.system.remain_open_time = 1000
        self.system.elevators[0].open_door()
        while (self.system.elevators[0].state != ElevatorState.stopped_door_opened):
            QTest.qWait(10)
        self.system.elevators[0].finished = False

        self.system.elevators[0].message = ""
        self.system.zmqThread.receivedMessage = "close_door#1"
        self.system.zmqThread.messageTimeStamp = time.time()
        self.system.messageUnprocessed = True
        while(self.system.messageUnprocessed):
            QTest.qWait(10)
            
        while not (self.system.elevators[0].finished):
            QTest.qWait(10)

        self.assertEqual(self.system.elevators[0].current_floor, 3)
        #  self.assertEqual(self.system.elevators[0].state, ElevatorState.stopped_closing_door)
        self.assertEqual(self.system.elevators[0].message, "door_closed#1")

        # TestCase6: open_door#6
        # self.system.elevators[1].running = False
        self.system.elevators[1].state = ElevatorState.stopped_door_closed
        # self.system.elevators[1].finished = False

        self.system.zmqThread.receivedMessage = "open_door#6"
        self.system.zmqThread.messageTimeStamp = time.time()
        self.system.messageUnprocessed = True
        while(self.system.messageUnprocessed):
            QTest.qWait(10)
        self.assertEqual(self.system.elevators[0].finished, True)
        self.assertEqual(self.system.elevators[1].finished, True)
        for elevator in self.system.elevators:
            self.assertEqual(elevator.direction, Direction.IDLE)
        self.assertEqual(self.system.elevators[0].current_floor, 3)
        self.assertEqual(self.system.elevators[0].current_floor, 3)
        self.assertEqual(self.system.elevators[1].state, ElevatorState.stopped_door_closed)

    def tearDown(self):
        """Cleanup after each test case"""

        for t in self.system.threads:
            t.join(timeout=1)

        self.ui.close()
        self.ui.deleteLater()
        # self.system.deleteLater()
        QTest.qWait(1000)  # Ensure the UI is closed before the next test

        import gc
        gc.collect()

    @classmethod
    def tearDownClass(cls):
        """Cleanup work after all test cases are executed"""
        # Ensure the event loop runs long enough to display the window
        QTest.qWait(1000)  # Delay 1 second to ensure the window is displayed
        cls.app.quit()
if __name__ == '__main__':
    unittest.main()
