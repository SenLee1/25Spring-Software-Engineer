import unittest
import threading
import time
from unittest.mock import Mock
from PyQt6.QtWidgets import QApplication
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
from NetClient import ZmqClientThread
from elevator import Elevator, ElevatorState, Direction
from elevator_system import ElevatorSystem
from elevator_UI import ElevatorSystemUI, ElevatorUI
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

class TestElevator(unittest.TestCase):
    def setUp(self):
        # Create a mock ZMQ client thread
        self.zmq_mock = ZmqClientThread(identity="Team8")
        # self.shared_lock = threading.Lock()
        
        # Create an elevator instance for testing
        self.elevator = Elevator(id=1, max_floor=3, zmqThread=self.zmq_mock)
        
        # Start the elevator thread
        self.elevator.stop()
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        # self.elevator_thread.start()
        
        # Short sleep to allow thread to initialize
        time.sleep(0.1)


    def test_1_0_initial_state(self):
        """Test that elevator initializes with correct default values"""
        self.assertEqual(self.elevator.current_floor, 1)
        self.assertEqual(self.elevator.direction, Direction.IDLE)
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
        self.assertEqual(len(self.elevator.destination_floors), 0)
        self.assertEqual(len(self.elevator.active_requests), 0)

    def test_1_1_add_destination(self):
        """Test adding destinations to the elevator"""
        # TestCase 1.1.1
        self.elevator.add_destination(-1, Direction.IDLE, 0)
        self.assertEqual(self.elevator.destination_floors[0], [0, Direction.IDLE, 0])


        # TestCase 1.1.2
        self.elevator.reset()
        self.elevator.add_destination(2, Direction.UP, 0)
        self.elevator.add_destination(2, Direction.UP, 0)
        self.assertEqual(len(self.elevator.active_requests), 1)
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(self.elevator.destination_floors[0], [2, Direction.UP, 0])
        self.assertIn((2, Direction.UP), self.elevator.active_requests)
        self.assertEqual(self.elevator.direction, Direction.UP)

        # TestCase 1.1.3
        self.elevator.reset()
        self.elevator.add_destination(2, Direction.IDLE, 0)
        self.elevator.add_destination(3, Direction.IDLE, 0)
        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.direction, Direction.UP)

        # TestCase 1.1.4
        self.elevator.reset()
        self.elevator.add_destination(1, Direction.UP, 0)
        self.assertEqual(len(self.elevator.active_requests), 1)
        self.assertEqual(self.elevator.destination_floors[0], [1, Direction.UP, 0])
        self.assertEqual(len(self.elevator.destination_floors), 1)

        # fakely simulate the elevator deal with the request
        self.elevator.update_destination()
        self.assertEqual(len(self.elevator.destination_floors), 0)
        self.assertEqual(len(self.elevator.active_requests), 0)
        self.elevator.state = ElevatorState.stopped_door_opened
        self.elevator.add_destination(1, Direction.UP, 0)
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(len(self.elevator.active_requests), 1)

    def test_1_2_resort_destination(self):
        """Test that destinations are resorted correctly"""

        # TestCase 1.2.1:
        #  self.destination_floors = [[2, Direction.IDLE, 0.0], [3, Direction.IDLE, 0.0]]
        #  self.state=stopped_door_closed;
        #  self.direction=Direction.IDLE;
        #  self.current_floor=1
        #  self.car=[1,0]

        # add 3 before 2
        self.elevator.destination_floors = [[2, Direction.IDLE, 0.0], [3, Direction.IDLE, 0.0]]
        self.currentDestination = [1, Direction.IDLE, 0.0]
        self.elevator.resort_destination()
        # Check the order of destinations: 2 shoule be before 3
        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[1][0], 3)

        # TestCase 1.2.2:
        # destination_floors=[(2, Direction.DOWN, 0), (1,Direction.IDLE, 0)]
        #  self.state=down; self.direction=DOWN;
        #  self.current_floor=3;self.car=[3,0]
        self.elevator.reset()
        self.elevator.currentDestination = [0, Direction.IDLE, 0.0]
        self.elevator.state = ElevatorState.down
        self.elevator.direction = Direction.DOWN
        self.elevator.current_floor = 3
        self.elevator.car = [3, 0]
        self.elevator.destination_floors = [[2, Direction.DOWN, 0], [1, Direction.IDLE, 0]]
        self.elevator.resort_destination()

        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[1][0], 1)

        # #  Test Case 1.2.3:
        # #  destination_floors=[(1, Direction.IDLE, 0), (2,Direction.IDLE, 0)]
        # #  self.state=up; self.direction=UP;
        # #  self.current_floor=1;self.car=[1.7,0]
        self.elevator.reset()
        self.elevator.currentDestination = [0, Direction.IDLE, 0.0]
        self.elevator.state = ElevatorState.up
        self.elevator.direction = Direction.UP
        self.elevator.current_floor = 1
        self.elevator.car = [1.7, 0]
        self.elevator.current_floor = 3
        self.elevator.destination_floors = [[0, Direction.IDLE, 0], [2, Direction.UP, 0]]
        self.elevator.resort_destination()

        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[1][0], 0)

        #  Test Case 1.2.4:
        #  self.state=down;
        #  self.direction=DOWN;
        #  self.current_floor=3;
        #  self.car=[2.7,0]
        #  destination_floors=[(3, Direction.IDLE, 0), (1,Direction.IDLE, 0)]
        self.elevator.reset()
        self.elevator.state = ElevatorState.down
        self.elevator.direction = Direction.DOWN
        self.elevator.current_floor = 3
        self.elevator.car = [2,7, 0]
        self.elevator.destination_floors = [[3, Direction.IDLE, 0], [1, Direction.DOWN, 0]]
        self.elevator.currentDestination = [2, Direction.IDLE, 0]
        self.elevator.resort_destination()

        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 1)
        self.assertEqual(self.elevator.destination_floors[1][0], 3)


    def test_1_3_open_door(self):
        """Test that the elevator can properly open its door"""
        #  Test Case 1.3.1: self.state=stopped_door_opened :
        self.elevator.state = ElevatorState.stopped_door_opened
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_opened)

        #  Test Case 1.3.2: self.state=stopped_door_closed : TC2, TC4, TC5, TC7
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_door_closed
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_opening_door)

        #  Test Case 1.3.3: self.state=up: TC1
        self.elevator.reset()
        self.elevator.state = ElevatorState.up
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.up)

        #  Test Case 1.3.4: self.state=stopped_opening_door: TC2, TC4, TC6, TC8
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_opening_door
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_opening_door)

    def test_1_4_close_door(self):
        """Test that the elevator can properly close its door"""
        # Test Case 1.4.1: self.state=stopped_door_opened
        self.elevator.state = ElevatorState.stopped_door_opened
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_closing_door)

        # Test Case 1.4.2: self.state=stopped_door_closed
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_door_closed
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        # Test Case 1.4.3: self.state=up
        self.elevator.reset()
        self.elevator.state = ElevatorState.up
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.up)

        # Test Case 1.4.4: self.state=stopped_opening_door
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_opening_door
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_opening_door)

    def test_1_5_update_destination(self):
        """Test that the elevator updates its destination correctly"""

        #  Test Case 1.5.1:
        #  self.current_floor=3, self.direction = Direction.DOWN
        #  self.destination_floors=[(3, Direction.DOWN, 0), (2, Direction.IDLE, 0)]
        #  self.active_requests = {(3, Direction.DOWN)}:  TC1, TC2, TC3, TC5
        self.elevator.current_floor = 3
        self.elevator.direction = Direction.DOWN
        self.elevator.destination_floors = [(3, Direction.DOWN, 0), (2, Direction.IDLE, 0)]
        self.elevator.active_requests.add((3, Direction.DOWN))
        self.elevator.update_destination()
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(len(self.elevator.active_requests), 0)

        #  Test Case 1.5.2:
        #  self.current_floor=2  self.direction = Direction.DOWN
        #  self.destination_floors=[(2, Direction.UP, 0), (2, Direction.DOWN, 0)]
        #  self.active_requests = {(2, Direction.DOWN),(2,Direction.UP)}:  TC1, TC3, TC4,TC5 TC6
        self.elevator.current_floor = 2
        self.elevator.direction = Direction.DOWN
        self.elevator.destination_floors = [(2, Direction.UP, 0), (2, Direction.DOWN, 0)]
        self.elevator.active_requests.add((2, Direction.DOWN))
        self.elevator.active_requests.add((2, Direction.UP))
        self.elevator.update_destination()
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[0][1], Direction.UP)
        self.assertEqual(len(self.elevator.active_requests), 1)
        self.assertIn((2, Direction.UP), self.elevator.active_requests)

    def test_1_7_reset(self):
        self.elevator.reset()
        self.assertEqual(self.elevator.current_floor, 1)
        self.assertEqual(self.elevator.direction, Direction.IDLE)
        self.assertEqual(len(self.elevator.destination_floors), 0)
        self.assertEqual(len(self.elevator.active_requests), 0)
        self.assertEqual(self.elevator.finished, True)
        self.assertEqual(self.elevator.car, [1.0, 0.0])
        self.assertEqual(self.elevator.running, True)
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
        self.assertEqual(self.elevator.serverMessage, "")
        self.assertEqual(self.elevator.current_floor, 1)

    def test_1_6_move(self):
        """Test the move method of the elevator"""
        # Start the elevator thread
        #  Test Case 1.6.1: 初始状态无目标楼层 (覆盖基础分支)
        #  : TC2, TC4, TC6, TC14, TC20, TC22, TC24, TC32, TC42, TC60, TC74, TC82
        self.elevator.reset()
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
        time.sleep(0.1)


        #  Test Case 1.6.2: 地下层特殊处理 (覆盖-1 逻辑)
        #  : TC1, TC5, TC13, TC19, TC21, TC25, TC28
        self.elevator.reset()
        self.current_floor = 0 
        self.destination_floors = [(-1, Direction.UP, 0)]
        self.state = ElevatorState.stopped_door_closed
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.3: 顶层特殊处理+方向转换
        #  : TC3, TC7, TC9, TC11, TC15, TC17, TC23, TC26, TC27, TC29
        self.elevator.reset()
        self.current_floor = 3
        self.destination_floors = [(2, Direction.DOWN, 0), (1, Direction.UP, 0)]
        self.state = ElevatorState.stopped_door_closed
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        # Test Case 1.6.4: 精确楼层到达检测
        # : TC8, TC10, TC12, TC16, TC18, TC30, TC75, TC79
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(2, Direction.IDLE, 0)]
        self.state = ElevatorState.up
        self.car = [1.49, 0.0] # 即将到达
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.5: 开门过程+新请求插入
        #  : TC31, TC33, TC35, TC37, TC39, TC40, TC43
        self.elevator.reset()
        self.current_floor = 2
        self.destination_floors = [(2, Direction.UP, 0)]
        self.state = ElevatorState.stopped_opening_door
        self.car = [2.0, 0.9]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.6: 关门中断(新请求)
        #  : TC41, TC44, TC45, TC49, TC51, TC53, TC55, TC57
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(1, Direction.DOWN, 0)]
        self.state = ElevatorState.stopped_closing_door
        self.car = [1.0, 0.1]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.7: 完全关门
        #  : TC46, TC48, TC50, TC52, TC54, TC56, TC58
        self.elevator.reset()
        self.current_floor = 2
        self.destination_floors = []
        self.state = ElevatorState.stopped_closing_door
        self.car = [2.0, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.8: 门全开状态
        #  : TC59, TC61, TC63, TC65, TC67, TC69, TC71
        self.elevator.reset()
        self.current_floor = 3
        self.destination_floors = [(3, Direction.DOWN, 0)]
        self.state = ElevatorState.stopped_door_opened
        self.remain_open_time = 1.5
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.9: 上升运动+楼层计数
        #  : TC73, TC76, TC77, TC80
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(2, Direction.UP, 0)]
        self.state = ElevatorState.up
        self.car = [1.1, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.10: 下降运动+精确停止
        #  : TC81, TC83, TC85, TC87
        self.elevator.reset()
        self.current_floor = 2
        self.destination_floors = [(1, Direction.DOWN, 0)]
        self.state = ElevatorState.down
        self.car = [1.1, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.11: 空闲状态完成
        #  : TC34, TC36, TC38, TC47, TC62, TC64, TC66, TC68, TC70, TC72
        self.elevator.reset()
        self.current_floor = 0
        self.destination_floors = []
        self.state = ElevatorState.stopped_door_opened
        self.finished = True
        self.remain_open_time = 0
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 1.6.12: 楼层精确匹配检测
        #  : TC78, TC84, TC86, TC88
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(1, Direction.IDLE, 0)]
        self.state = ElevatorState.down
        self.car = [1.3, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)


class TestElevatorUI(unittest.TestCase):
   @classmethod
   def setUpClass(cls):
       cls.app = QApplication(sys.argv)

   def setUp(self):
       self.elevator_ui = ElevatorUI(1, max_floors=3)

   def test_3_0_1_initial_state(self):

       self.assertEqual(self.elevator_ui.windowTitle(), "Elevator 1")

       self.assertEqual(len(self.elevator_ui.floor_buttons), 4)

       # 检查按钮文本
       self.assertEqual(self.elevator_ui.floor_buttons[3].text(), "3")
       self.assertEqual(self.elevator_ui.floor_buttons[0].text(), "-1")

       # 检查初始楼层显示
       self.assertEqual(self.elevator_ui.floor_display.text(), "1")

       # 检查初始方向显示
       self.assertEqual(self.elevator_ui.direction_display.text(), "■")

   def test_3_1_highlight_floor_button(self):
       """Test highlight_floor_button() method"""
       # Testcase 3.1.1
       self.elevator_ui.highlight_floor_button(1, True)
       f1_btn = self.elevator_ui.floor_buttons[1]
       self.assertEqual(f1_btn.styleSheet(), "background-color: #FFA500; font-weight: bold;")
       # Testcase 3.1.2
       self.elevator_ui.highlight_floor_button(1, False)
       self.assertEqual(f1_btn.styleSheet(), "")
       # Testcase 3.1.3
       self.elevator_ui.highlight_floor_button(8, True)
       self.assertEqual(f1_btn.styleSheet(), "")

   def test_3_2_update_state(self):
       """Test update_state() method"""

       # Testcase 3.2.1
       self.elevator_ui.update_state(1, 1)
       self.assertEqual(self.elevator_ui.direction_display.text(), "↑")
       self.assertEqual(self.elevator_ui.direction_display.styleSheet(), "color: green;")

       # Testcase 3.2.2
       self.elevator_ui.update_state(1, -1)
       self.assertEqual(self.elevator_ui.direction_display.text(), "↓")
       self.assertEqual(self.elevator_ui.direction_display.styleSheet(), "color: red;")

       # Testcase 3.2.3
       self.elevator_ui.update_state(1, 0)
       self.assertEqual(self.elevator_ui.direction_display.text(), "■")
       self.assertEqual(self.elevator_ui.direction_display.styleSheet(), "color: gray;")

class TestElevatorSystemUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        self.elevator_system = ElevatorSystem(num_elevators=2, max_floor=3, identity="TestUI")
        self.ui = ElevatorSystemUI(self.elevator_system, num_elevators=2, max_floors=3)

    def test_3_0_2_initial_state(self):
        """Test Init states"""

        self.assertEqual(self.ui.windowTitle(), "Elevator Control System")
        
        self.assertEqual(len(self.ui.up_buttons), 3)
        self.assertEqual(len(self.ui.down_buttons), 3)
        
        # 检查按钮文本
        self.assertEqual(self.ui.up_buttons[2].text(), "▲")
        self.assertEqual(self.ui.up_buttons[1].text(), "▲")
        self.assertEqual(self.ui.up_buttons[0].text(), "▲")
        # 检查按钮文本
        self.assertEqual(self.ui.down_buttons[3].text(), "▼")
        self.assertEqual(self.ui.down_buttons[2].text(), "▼")
        self.assertEqual(self.ui.down_buttons[1].text(), "▼")
        
        # 检查初始楼层显示
        self.assertEqual(self.ui.elevator_1_floor3.text(), "1")
        self.assertEqual(self.ui.elevator_2_floor3.text(), "1")
        
        # 检查初始方向显示
        self.assertEqual(self.ui.elevator_1_direction3.text(), "")
        self.assertEqual(self.ui.elevator_2_direction3.text(), "")


    def test_3_3_highlight_call_button(self):
        """Test highlight_call_button() in ElevatorSystem"""

        # Testcase 3.3.1
        self.ui.highlight_call_button(1, 1 ,True)
        self.assertEqual(self.ui.up_buttons[1].styleSheet(), "background-color: #FFA500; font-weight: bold;")

        # Testcase 3.3.2
        self.ui.highlight_call_button(-1, 1 ,False)
        self.assertEqual(self.ui.down_buttons[1].styleSheet(), "")

        # Testcase 3.3.3
        self.ui.highlight_call_button(-1, -1 ,True)

    def test_3_4_update_button_highlights(self):
        """Test update_button_highlights()"""

        # Testcase 3.4.1
        self.ui.elevator_system.elevators[0].destination_floors=[]
        self.ui.elevator_system.elevators[0].destination_floors.append((1, Direction.IDLE,0))
        self.ui.update_button_highlights()
        f1_btn = self.ui.elevators[0].floor_buttons[1]
        self.assertEqual(f1_btn.styleSheet(), "background-color: #FFA500; font-weight: bold;")

        # Testcase 3.4.2
        self.ui.elevator_system.elevators[0].destination_floors=[]
        self.ui.elevator_system.elevators[0].destination_floors.append((1, Direction.UP,0))
        self.ui.update_button_highlights()
        f1_btn = self.ui.elevators[0].floor_buttons[1]
        self.assertEqual(f1_btn.styleSheet(), "")

    def test_3_5_handle_door_command(self):
        """Test handle_door_command()"""

        # Testcase 3.5.1
        self.ui.handle_door_command(1, 0)
        self.assertEqual(self.elevator_system.zmqThread.receivedMessage, "open_door#1")

        # Testcase 3.5.2
        self.ui.handle_door_command(2, 1)
        self.assertEqual(self.elevator_system.zmqThread.receivedMessage, "close_door#2")

    def tesat_3_6_update_ui_from_system(self):
        """Test update_ui_from_system()"""

        # Testcase 3.6.1
        #  1: elevators[0].direction = 1; elevators[1].direction = -1; elevators[0].current_floor = 0, elevators[1],current_floor = 0 -> TC 1, TC3, TC4, TC5
        self.ui.elevator_system.elevators[0].direction = 1
        self.ui.elevator_system.elevators[0].current_floor = 0

        self.ui.elevator_system.elevators[1].direction = -1
        self.ui.elevator_system.elevators[1].current_floor = 0
        self.ui.update_ui_from_system()
        self.assertEqual(self.ui.elevator_1_direction3.text(), "▲")
        self.assertEqual(self.ui.elevator_2_direction3.text(), "▼")
        self.assertEqual(self.ui.elevator_1_floor3.text(), "-1")
        self.assertEqual(self.ui.elevator_2_floor3.text(), "-1")


        # Testcase 3.6.2
        #  2: elevators[0].direction = 0; elevators[1].direction = 0; elevators[0].current_floor = 1 , elevators[0].current_floor = 1-> TC2, Tc4， TC6
        self.ui.elevator_system.elevators[0].direction = 0
        self.ui.elevator_system.elevators[0].current_floor = 1

        self.ui.elevator_system.elevators[1].direction = 0
        self.ui.elevator_system.elevators[1].current_floor = 1
        self.ui.update_ui_from_system()
        self.assertEqual(self.ui.elevator_1_direction3.text(),"■")
        self.assertEqual(self.ui.elevator_2_direction3.text(), "■")
        self.assertEqual(self.ui.elevator_1_floor3.text(), "1")
        self.assertEqual(self.ui.elevator_2_floor3.text(), "1")

    def tearDown(self):
        """Cleanup after each test case"""

        QTest.qWait(1000)  # Ensure the UI is closed before the next test

        # import gc
        # gc.collect()

    @classmethod
    def tearDownClass(cls):
        """Cleanup work after all test cases are executed"""
        # Ensure the event loop runs long enough to display the window
        QTest.qWait(1000)  # Delay 1 second to ensure the window is displayed
        cls.app.quit()

class TestElevatorSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance once for all tests
        cls.app = QApplication(sys.argv)

    def setUp(self):
        # Create an elevator system with 2 elevators and 3 floors for testing
        self.elevator_system = ElevatorSystem(num_elevators=2, max_floor=3, identity="TestSystem")
        self.call_elevator_thread = None
        for t in self.elevator_system.threads:
            if t.name == "call_elevator_thread":
                self.call_elevator_thread = t
                break
        
        # Short sleep to allow threads to initialize
        time.sleep(0.1)

    def test_2_0_initial_state(self):
        """Test that elevator system initializes with correct default values"""
        self.assertEqual(len(self.elevator_system.elevators), 2)
        self.assertEqual(self.elevator_system.max_floor, 3)
        self.assertEqual(len(self.elevator_system.call_requests), 0)
        self.assertEqual(len(self.elevator_system.active_requests), 0)
        
        # Check each elevator's initial state
        # ensure there are only four door state by 
        # there exists four door states
        self.assertIn(ElevatorState.stopped_door_closed, ElevatorState)
        self.assertIn(ElevatorState.stopped_door_opened, ElevatorState)
        self.assertIn(ElevatorState.stopped_closing_door, ElevatorState)
        self.assertIn(ElevatorState.stopped_opening_door, ElevatorState)

        # there are six elevator states totally, two of then are not door states.
        self.assertEqual(len(ElevatorState), 6)
        self.assertIn(ElevatorState.up, ElevatorState)
        self.assertIn(ElevatorState.down, ElevatorState)
        i = 1
        for i, elevator in enumerate(self.elevator_system.elevators):
            self.assertEqual(elevator.id, i+1)
            self.assertEqual(elevator.current_floor, 1)
            self.assertNotEqual(elevator.car, None)
            self.assertEqual(elevator.state, ElevatorState.stopped_door_closed)

    def test_2_1_call_elevator(self):

        """Test the call elevator logic"""

        #  Test Case 2.1.1:
        #  self.call_requests = [(1,Direction.UP, True),(2, Direction.UP, True), (1, Direction.DOWN, True), (1, Direction.DOWN, True)],
        #  self.elevators.current_floors = [-1, 3]
        #  self.elevators.states = [up, down]
        self.elevator_system.call_requests = [(1,Direction.UP, True),(2, Direction.UP, True), (1, Direction.DOWN, True), (1, Direction.DOWN, True)]
        self.elevator_system.elevators[0].current_floor = 0
        self.elevator_system.elevators[1].current_floor = 3
        self.elevator_system.elevators[0].state = ElevatorState.up
        self.elevator_system.elevators[1].state = ElevatorState.down
        self.call_elevator_thread.start()
        while self.elevator_system.call_requests:
            continue
        self.elevator_system.running = False
        self.assertEqual(len(self.elevator_system.call_requests), 0)
        self.assertIn([2,Direction.UP,0], self.elevator_system.elevators[0].destination_floors)
        self.assertIn([1,Direction.DOWN,0], self.elevator_system.elevators[1].destination_floors)
        self.assertIn([1,Direction.UP,0], self.elevator_system.elevators[1].destination_floors)
        self.assertEqual(len(self.elevator_system.elevators[1].destination_floors), 2)

        #  Test Case 2.1.2:
        #  self.call_requests = None
        #
        #  : TC3
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.call_elevator_thread = threading.Thread(target=self.elevator_system.call_elevator)
        self.call_elevator_thread.deamon = True
        self.elevator_system.call_requests = []
        self.elevator_system.running = True
        self.call_elevator_thread.start()
        while self.elevator_system.call_requests:
            continue
        self.elevator_system.running = False
        self.assertEqual(len(self.elevator_system.call_requests), 0)
        self.assertEqual(len(self.elevator_system.elevators[0].destination_floors), 0)
        self.assertEqual(len(self.elevator_system.elevators[1].destination_floors), 0)


        #  Test Case 2.1.3:
        #  self.call_requests = [(2,Direction.UP, True),(2, Direction.DOWN, True)],
        #  self.elevators.current_floors = [1, 3]
        #  self.elevators.states = [stopped_closing_door, stopped_closing_door]
        #  self.elevators.directions = [Direction.UP, Direction.DOWN]
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.call_elevator_thread = threading.Thread(target=self.elevator_system.call_elevator)
        self.call_elevator_thread.deamon = True
        self.elevator_system.call_requests = [(2,Direction.UP, True),(2, Direction.DOWN, True)]
        self.elevator_system.elevators[0].current_floor = 1
        self.elevator_system.elevators[1].current_floor = 3
        self.elevator_system.elevators[0].state = ElevatorState.stopped_closing_door
        self.elevator_system.elevators[1].state = ElevatorState.stopped_closing_door
        self.elevator_system.elevators[0].direction = Direction.UP
        self.elevator_system.elevators[1].direction = Direction.DOWN
        self.elevator_system.running = True
        self.call_elevator_thread.start()
        while self.elevator_system.call_requests:
            continue
        self.elevator_system.running = False
        self.assertEqual(len(self.elevator_system.call_requests), 0)
        self.assertIn([2,Direction.UP,0], self.elevator_system.elevators[0].destination_floors)
        self.assertIn([2,Direction.DOWN,0], self.elevator_system.elevators[1].destination_floors)
        self.assertEqual(len(self.elevator_system.elevators[0].destination_floors), 1)
        self.assertEqual(len(self.elevator_system.elevators[1].destination_floors), 1)

    def test_2_2_select_floor(self):
        """Test selecting floors in elevators"""
        # TestCase 2.2.1: Select floor 2 in elevator 1
        self.elevator_system.select_floor(1, 2)
        self.assertEqual(len(self.elevator_system.elevators[0].destination_floors), 1)
        self.assertEqual(len(self.elevator_system.elevators[1].destination_floors), 0)
        self.assertEqual(self.elevator_system.elevators[0].destination_floors[0][0], 2)
        self.assertEqual(self.elevator_system.elevators[0].destination_floors[0][1], Direction.IDLE)

        # TestCase 2.2.2: Select invalid floor
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.elevator_system.select_floor(1, 5)
        self.assertEqual(len(self.elevator_system.elevators[1].destination_floors), 0)
        self.assertEqual(len(self.elevator_system.elevators[0].destination_floors), 0)

    def test_2_3_select_oc(self):
        """Test door open/close operations"""
        #  Test Case 2.3.1:
        #  elevator_id=1, op=0
        self.elevator_system.select_oc(1, 0)
        self.assertEqual(self.elevator_system.elevators[0].state, ElevatorState.stopped_opening_door)

        #  Test Case 2.3.2:
        #  elevator_id=2, op=1 : TC2
        self.elevator_system.select_oc(2, 1)
        self.assertEqual(self.elevator_system.elevators[1].state, ElevatorState.stopped_door_closed)

        #  Test Case 2.3.3:
        #  elevator_id=6, op=1 : TC2
        self.elevator_system.select_oc(2, 1)
        self.assertEqual(self.elevator_system.elevators[1].state, ElevatorState.stopped_door_closed)

    def test_2_4_process_message(self):
        """Test processing messages from the server"""
        # TestCase 2.4.1: Reset message
        self.elevator_system.serverMessage = "reset"
        self.elevator_system.process_message()
        for elevator in self.elevator_system.elevators:
            self.assertEqual(elevator.current_floor, 1)
            self.assertEqual(len(elevator.destination_floors), 0)
            self.assertEqual(elevator.state, ElevatorState.stopped_door_closed)


        # TestCase 2.4.2: Call up message
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.elevator_system.call_requests = []  
        self.elevator_system.serverMessage = "call_up@2"
        self.elevator_system.process_message()
        self.assertEqual(len(self.elevator_system.call_requests), 1)
        self.assertEqual(self.elevator_system.call_requests[0][0], 2)
        self.assertEqual(self.elevator_system.call_requests[0][1], Direction.UP)

        # TestCase 2.4.3: Select floor message
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.elevator_system.call_requests = []  
        self.elevator_system.serverMessage = "select_floor@2#1"
        self.elevator_system.process_message()
        self.assertEqual(len(self.elevator_system.elevators[0].destination_floors), 1)
        self.assertEqual(len(self.elevator_system.elevators[1].destination_floors), 0)
        self.assertEqual(self.elevator_system.elevators[0].destination_floors[0][0], 2)
        self.assertEqual(self.elevator_system.elevators[0].destination_floors[0][1], Direction.IDLE)

        #  Test Case 2.4.4:
        #  self.serverMessage = "open_door#1" 
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.elevator_system.call_requests = []  
        self.elevator_system.serverMessage = "open_door#1"
        self.elevator_system.process_message()
        self.assertEqual(self.elevator_system.elevators[0].state, ElevatorState.stopped_opening_door)

        #  Test Case 2.4.5:
        #  self.serverMessage = "close_door#1" : TC9
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.elevator_system.call_requests = []  
        self.elevator_system.serverMessage = "close_door#1"
        self.elevator_system.process_message()
        self.assertEqual(self.elevator_system.elevators[1].state, ElevatorState.stopped_door_closed)

        #  Test Case 2.4.6:
        #  self.serverMessage = "invalid_command" : TC2, TC4, TC6, TC8, TC10
        for elevator in self.elevator_system.elevators:
            elevator.reset()
        self.elevator_system.call_requests = []  
        self.elevator_system.serverMessage = "invalid_command"
        self.elevator_system.process_message()
        self.assertEqual(len(self.elevator_system.call_requests), 0)
        for elevator in self.elevator_system.elevators:
            self.assertEqual(elevator.state, ElevatorState.stopped_door_closed)
            self.assertEqual(len(elevator.destination_floors), 0)

    def tearDown(self):
        # Clean up by shutting down the elevator system
        self.elevator_system.shutdown()
        # self.patcher.stop()
        time.sleep(0.1)  # Allow time for threads to stop

class TestElevator(unittest.TestCase):
    def setUp(self):
        # Create a mock ZMQ client thread
        self.zmq_mock = ZmqClientThread(identity="Team8")
        # self.shared_lock = threading.Lock()
        
        # Create an elevator instance for testing
        self.elevator = Elevator(id=1, max_floor=3, zmqThread=self.zmq_mock)
        
        # Start the elevator thread
        self.elevator.stop()
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        # self.elevator_thread.start()
        
        # Short sleep to allow thread to initialize
        time.sleep(0.1)


    def test_2_0_initial_state(self):
        """Test that elevator initializes with correct default values"""
        self.assertEqual(self.elevator.current_floor, 1)
        self.assertEqual(self.elevator.direction, Direction.IDLE)
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
        self.assertEqual(len(self.elevator.destination_floors), 0)
        self.assertEqual(len(self.elevator.active_requests), 0)

    def test_1_1_add_destination(self):
        """Test adding destinations to the elevator"""
        # TestCase 1
        self.elevator.add_destination(-1, Direction.IDLE, 0)
        self.assertEqual(self.elevator.destination_floors[0], [0, Direction.IDLE, 0])


        # TestCase 2
        self.elevator.reset()
        self.elevator.add_destination(2, Direction.UP, 0)
        self.elevator.add_destination(2, Direction.UP, 0)
        self.assertEqual(len(self.elevator.active_requests), 1)
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(self.elevator.destination_floors[0], [2, Direction.UP, 0])
        self.assertIn((2, Direction.UP), self.elevator.active_requests)
        self.assertEqual(self.elevator.direction, Direction.UP)

        # TestCase 3
        self.elevator.reset()
        self.elevator.add_destination(2, Direction.IDLE, 0)
        self.elevator.add_destination(3, Direction.IDLE, 0)
        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.direction, Direction.UP)

        # TestCase 4
        self.elevator.reset()
        self.elevator.add_destination(1, Direction.UP, 0)
        self.assertEqual(len(self.elevator.active_requests), 1)
        self.assertEqual(self.elevator.destination_floors[0], [1, Direction.UP, 0])
        self.assertEqual(len(self.elevator.destination_floors), 1)

        # fakely simulate the elevator deal with the request
        self.elevator.update_destination()
        self.assertEqual(len(self.elevator.destination_floors), 0)
        self.assertEqual(len(self.elevator.active_requests), 0)
        self.elevator.state = ElevatorState.stopped_door_opened
        self.elevator.add_destination(1, Direction.UP, 0)
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(len(self.elevator.active_requests), 1)

    def test_1_2_resort_destination(self):
        """Test that destinations are resorted correctly"""

        # TestCase 1:
        #  self.destination_floors = [[2, Direction.IDLE, 0.0], [3, Direction.IDLE, 0.0]]
        #  self.state=stopped_door_closed;
        #  self.direction=Direction.IDLE;
        #  self.current_floor=1
        #  self.car=[1,0]

        # add 3 before 2
        self.elevator.destination_floors = [[2, Direction.IDLE, 0.0], [3, Direction.IDLE, 0.0]]
        self.currentDestination = [1, Direction.IDLE, 0.0]
        self.elevator.resort_destination()
        # Check the order of destinations: 2 shoule be before 3
        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[1][0], 3)

        # TestCase 2:
        # destination_floors=[(2, Direction.DOWN, 0), (1,Direction.IDLE, 0)]
        #  self.state=down; self.direction=DOWN;
        #  self.current_floor=3;self.car=[3,0]
        self.elevator.reset()
        self.elevator.currentDestination = [0, Direction.IDLE, 0.0]
        self.elevator.state = ElevatorState.down
        self.elevator.direction = Direction.DOWN
        self.elevator.current_floor = 3
        self.elevator.car = [3, 0]
        self.elevator.destination_floors = [[2, Direction.DOWN, 0], [1, Direction.IDLE, 0]]
        self.elevator.resort_destination()

        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[1][0], 1)

        # #  Test Case 3:
        # #  destination_floors=[(1, Direction.IDLE, 0), (2,Direction.IDLE, 0)]
        # #  self.state=up; self.direction=UP;
        # #  self.current_floor=1;self.car=[1.7,0]
        self.elevator.reset()
        self.elevator.currentDestination = [0, Direction.IDLE, 0.0]
        self.elevator.state = ElevatorState.up
        self.elevator.direction = Direction.UP
        self.elevator.current_floor = 1
        self.elevator.car = [1.7, 0]
        self.elevator.current_floor = 3
        self.elevator.destination_floors = [[0, Direction.IDLE, 0], [2, Direction.UP, 0]]
        self.elevator.resort_destination()

        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[1][0], 0)

        #  Test Case 4:
        #  self.state=down;
        #  self.direction=DOWN;
        #  self.current_floor=3;
        #  self.car=[2.7,0]
        #  destination_floors=[(3, Direction.IDLE, 0), (1,Direction.IDLE, 0)]
        self.elevator.reset()
        self.elevator.state = ElevatorState.down
        self.elevator.direction = Direction.DOWN
        self.elevator.current_floor = 3
        self.elevator.car = [2,7, 0]
        self.elevator.destination_floors = [[3, Direction.IDLE, 0], [1, Direction.DOWN, 0]]
        self.elevator.currentDestination = [2, Direction.IDLE, 0]
        self.elevator.resort_destination()

        self.assertEqual(len(self.elevator.destination_floors), 2)
        self.assertEqual(self.elevator.destination_floors[0][0], 1)
        self.assertEqual(self.elevator.destination_floors[1][0], 3)


    def test_1_3_open_door(self):
        """Test that the elevator can properly open its door"""
        #  Test Case 1: self.state=stopped_door_opened :
        self.elevator.state = ElevatorState.stopped_door_opened
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_opened)

        #  Test Case 2: self.state=stopped_door_closed : TC2, TC4, TC5, TC7
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_door_closed
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_opening_door)

        #  Test Case 3: self.state=up: TC1
        self.elevator.reset()
        self.elevator.state = ElevatorState.up
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.up)

        #  Test Case 4: self.state=stopped_opening_door: TC2, TC4, TC6, TC8
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_opening_door
        self.elevator.open_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_opening_door)

    def test_1_4_close_door(self):
        """Test that the elevator can properly close its door"""
        # Test Case 1: self.state=stopped_door_opened
        self.elevator.state = ElevatorState.stopped_door_opened
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_closing_door)

        # Test Case 2: self.state=stopped_door_closed
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_door_closed
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        # Test Case 3: self.state=up
        self.elevator.reset()
        self.elevator.state = ElevatorState.up
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.up)

        # Test Case 4: self.state=stopped_opening_door
        self.elevator.reset()
        self.elevator.state = ElevatorState.stopped_opening_door
        self.elevator.close_door()
        self.assertEqual(self.elevator.state, ElevatorState.stopped_opening_door)

    def test_1_5_update_destination(self):
        """Test that the elevator updates its destination correctly"""

        #  Test Case 1:
        #  self.current_floor=3, self.direction = Direction.DOWN
        #  self.destination_floors=[(3, Direction.DOWN, 0), (2, Direction.IDLE, 0)]
        #  self.active_requests = {(3, Direction.DOWN)}:  TC1, TC2, TC3, TC5
        self.elevator.current_floor = 3
        self.elevator.direction = Direction.DOWN
        self.elevator.destination_floors = [(3, Direction.DOWN, 0), (2, Direction.IDLE, 0)]
        self.elevator.active_requests.add((3, Direction.DOWN))
        self.elevator.update_destination()
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(len(self.elevator.active_requests), 0)

        #  Test Case 2:
        #  self.current_floor=2  self.direction = Direction.DOWN
        #  self.destination_floors=[(2, Direction.UP, 0), (2, Direction.DOWN, 0)]
        #  self.active_requests = {(2, Direction.DOWN),(2,Direction.UP)}:  TC1, TC3, TC4,TC5 TC6
        self.elevator.current_floor = 2
        self.elevator.direction = Direction.DOWN
        self.elevator.destination_floors = [(2, Direction.UP, 0), (2, Direction.DOWN, 0)]
        self.elevator.active_requests.add((2, Direction.DOWN))
        self.elevator.active_requests.add((2, Direction.UP))
        self.elevator.update_destination()
        self.assertEqual(len(self.elevator.destination_floors), 1)
        self.assertEqual(self.elevator.destination_floors[0][0], 2)
        self.assertEqual(self.elevator.destination_floors[0][1], Direction.UP)
        self.assertEqual(len(self.elevator.active_requests), 1)
        self.assertIn((2, Direction.UP), self.elevator.active_requests)

    def test_1_7_reset(self):
        self.elevator.reset()
        self.assertEqual(self.elevator.current_floor, 1)
        self.assertEqual(self.elevator.direction, Direction.IDLE)
        self.assertEqual(len(self.elevator.destination_floors), 0)
        self.assertEqual(len(self.elevator.active_requests), 0)
        self.assertEqual(self.elevator.finished, True)
        self.assertEqual(self.elevator.car, [1.0, 0.0])
        self.assertEqual(self.elevator.running, True)
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
        self.assertEqual(self.elevator.serverMessage, "")
        self.assertEqual(self.elevator.current_floor, 1)

    def test_1_6_move(self):
        """Test the move method of the elevator"""
        # Start the elevator thread
        #  Test Case 1: 初始状态无目标楼层 (覆盖基础分支)
        #  : TC2, TC4, TC6, TC14, TC20, TC22, TC24, TC32, TC42, TC60, TC74, TC82
        self.elevator.reset()
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
        time.sleep(0.1)


        #  Test Case 2: 地下层特殊处理 (覆盖-1 逻辑)
        #  : TC1, TC5, TC13, TC19, TC21, TC25, TC28
        self.elevator.reset()
        self.current_floor = 0 
        self.destination_floors = [(-1, Direction.UP, 0)]
        self.state = ElevatorState.stopped_door_closed
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 3: 顶层特殊处理+方向转换
        #  : TC3, TC7, TC9, TC11, TC15, TC17, TC23, TC26, TC27, TC29
        self.elevator.reset()
        self.current_floor = 3
        self.destination_floors = [(2, Direction.DOWN, 0), (1, Direction.UP, 0)]
        self.state = ElevatorState.stopped_door_closed
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        # Test Case 4: 精确楼层到达检测
        # : TC8, TC10, TC12, TC16, TC18, TC30, TC75, TC79
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(2, Direction.IDLE, 0)]
        self.state = ElevatorState.up
        self.car = [1.49, 0.0] # 即将到达
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 5: 开门过程+新请求插入
        #  : TC31, TC33, TC35, TC37, TC39, TC40, TC43
        self.elevator.reset()
        self.current_floor = 2
        self.destination_floors = [(2, Direction.UP, 0)]
        self.state = ElevatorState.stopped_opening_door
        self.car = [2.0, 0.9]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 6: 关门中断(新请求)
        #  : TC41, TC44, TC45, TC49, TC51, TC53, TC55, TC57
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(1, Direction.DOWN, 0)]
        self.state = ElevatorState.stopped_closing_door
        self.car = [1.0, 0.1]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 7: 完全关门
        #  : TC46, TC48, TC50, TC52, TC54, TC56, TC58
        self.elevator.reset()
        self.current_floor = 2
        self.destination_floors = []
        self.state = ElevatorState.stopped_closing_door
        self.car = [2.0, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 8: 门全开状态
        #  : TC59, TC61, TC63, TC65, TC67, TC69, TC71
        self.elevator.reset()
        self.current_floor = 3
        self.destination_floors = [(3, Direction.DOWN, 0)]
        self.state = ElevatorState.stopped_door_opened
        self.remain_open_time = 1.5
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 9: 上升运动+楼层计数
        #  : TC73, TC76, TC77, TC80
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(2, Direction.UP, 0)]
        self.state = ElevatorState.up
        self.car = [1.1, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 10: 下降运动+精确停止
        #  : TC81, TC83, TC85, TC87
        self.elevator.reset()
        self.current_floor = 2
        self.destination_floors = [(1, Direction.DOWN, 0)]
        self.state = ElevatorState.down
        self.car = [1.1, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 11: 空闲状态完成
        #  : TC34, TC36, TC38, TC47, TC62, TC64, TC66, TC68, TC70, TC72
        self.elevator.reset()
        self.current_floor = 0
        self.destination_floors = []
        self.state = ElevatorState.stopped_door_opened
        self.finished = True
        self.remain_open_time = 0
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)

        #  Test Case 12: 楼层精确匹配检测
        #  : TC78, TC84, TC86, TC88
        self.elevator.reset()
        self.current_floor = 1
        self.destination_floors = [(1, Direction.IDLE, 0)]
        self.state = ElevatorState.down
        self.car = [1.3, 0.0]
        self.elevator_thread = threading.Thread(target=self.elevator.move)
        self.elevator_thread.daemon = True
        self.elevator_thread.start()
        while not self.elevator.finished:
            continue
        self.elevator.running = False
        self.assertEqual(self.elevator.state, ElevatorState.stopped_door_closed)
if __name__ == '__main__':
    unittest.main()
