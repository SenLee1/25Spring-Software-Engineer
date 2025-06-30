import threading
import time
from elevator import ElevatorState
from NetClient import ZmqClientThread
from elevator import Elevator, Direction
from enum import IntEnum
from elevator_UI import ElevatorSystemUI
from PyQt6.QtWidgets import QApplication
from elevator import Elevator
from PyQt6.QtCore import QTimer
import sys


class ElevatorState(IntEnum):
    up = 0
    down = 1
    stopped_door_closed = 2
    stopped_door_opened = 3
    stopped_opening_door = 4
    stopped_closing_door = 5


class ElevatorSystem:
    def __init__(self, num_elevators=2, max_floor=3, identity=None):
        self.zmqThread = ZmqClientThread(identity=identity)
        self.elevators = [Elevator(i+1, max_floor,self.zmqThread) for i in range(num_elevators)]
        self.max_floor = max_floor
        self.serverMessage = ""
        self.timeStamp = -1
        self.active_requests = set()
        self.messageUnprocessed = False
        self.threads = []
        self.call_requests = []
        self.running = True

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_events)
        self.timer.start()  # 每1毫秒运行一次
        caller=threading.Thread(target=self.call_elevator)
        caller.name = "call_elevator_thread"
        caller.daemon=True
        self.threads.append(caller)
        #  self.caller_timer = QTimer()
        #  self.timer.timeout.connect(self.call_elevator)
        #  self.timer.start()  # 每1毫秒运行一次
        # caller.start()
        for elevator in self.elevators:
            t = threading.Thread(target=elevator.move)
            t.daemon = True
            # t.start()
            self.threads.append(t)

        # self.run()
    #  def shutdown(self):
    #      for elevator in self.elevators:
    #          elevator.stop()
    #          # 停止定时器
    #          self.timer.stop()
    #
    #          # 等待线程结束
    #      for t in self.threads:
    #          t.join(timeout=1.0)  # 设置超时避免卡死


    def is_received_new_message(self) -> bool:
        if (self.messageUnprocessed):
            return True
        else:
            if (self.timeStamp == self.zmqThread.messageTimeStamp and
               self.serverMessage == self.zmqThread.receivedMessage):
                return False
            else:
                return True


    def call_elevator(self):
        while self.running:
            self.call_requests = [list(i) for i in self.call_requests if i[2] == True]
            call_requests = [list(i) for i in self.call_requests if i[2] == True]

            if call_requests is None:
                return
            for call_request in call_requests:
                floor, is_external_call, _ = call_request
                for elevator in self.elevators:
                    for dest in elevator.destination_floors:
                        if dest[0] == floor and dest[1] == is_external_call:
                            call_request[2] = False
                            continue
                if call_request[2] == False:
                    break

                elevator_choice = []
                for elevator in self.elevators: 
                    # 可以搭顺风车：最优 

                    if elevator.state == ElevatorState.up and (floor - elevator.current_floor >= 2 or elevator.current_floor == 3 and floor == 3):
                            # print(1)
                            total_score =-9999 + floor - elevator.current_floor
                            elevator_choice.append((elevator.id, total_score))
                            continue
                    if elevator.state == ElevatorState.down and elevator.current_floor - floor >= 2: 
                            # print(2)
                            total_score =-9999 - (floor - elevator.current_floor)
                            elevator_choice.append((elevator.id, total_score))
                            continue
                    # if elevator.state == ElevatorState.stopped_door_opened or elevator.state == ElevatorState.stopped_opening_door: 
                    if elevator.direction == Direction.UP and is_external_call == Direction.UP and elevator.state != ElevatorState.up and (floor - elevator.current_floor >= 0):
                                total_score =-9999 + floor - elevator.current_floor
                                elevator_choice.append((elevator.id, total_score))
                                continue
                    if elevator.direction == Direction.DOWN and is_external_call == Direction.DOWN and elevator.state != ElevatorState.down and elevator.current_floor - floor >= 0:
                            
                                total_score =-9999 - (floor - elevator.current_floor)
                                elevator_choice.append((elevator.id, total_score))
                                continue

                    # 电梯空闲：次优 
                    total_score = 0
                    if elevator.finished: 
                        # print(123)
                        # print(call_request)
                        # print(call_requests)
                        total_score = -999
                        total_score += abs(elevator.current_floor - floor) * 5
                        elevator_choice.append((elevator.id, total_score))
                        # call_request[2] = False
                        continue 
                if elevator_choice:
                    elevator = min(elevator_choice, key=lambda x:x[1])
                    self.elevators[elevator[0]-1].add_destination(floor,is_external_call,0)
                    if call_request[0] == floor and call_request[1] == is_external_call:
                        to_remove = set()
                        for f, is_t_c in self.active_requests:
                            if f==floor and is_t_c==is_external_call:
                                to_remove = set()
                                to_remove.add((f,is_t_c))
                        self.active_requests -= to_remove
                    # call_request[2] = False
                    for calreq in self.call_requests:
                        if calreq == call_request:
                            calreq[2] = False
                else:
                    self.active_requests.add((floor, is_external_call))
                time.sleep(1)

    def select_floor(self, elevator_id, floor):
        if 1 <= elevator_id <= len(self.elevators) and (1 <= floor <= self.max_floor  or floor == -1):
            self.elevators[elevator_id-1].add_destination(floor, Direction.IDLE,0)
            time.sleep(1)
    
    def select_oc(self, elevator_id, op):
        if not (1 <= elevator_id <= len(self.elevators)):
            print("Invalid elevator ID!")
            return
        elevator = self.elevators[elevator_id-1]
        if op == 0:
            elevator.open_door()
        else:
            elevator.close_door()

    def process_message(self):
        # 选择电梯
        if self.serverMessage == "reset":
            for elevator in self.elevators:
                elevator.reset()
            self.messageUnprocessed = False
            return 

        elif self.serverMessage.startswith("call_"):
            message = self.serverMessage.split("_")[1]
            direction = message.split("@")[0]
            floor = int(message.split("@")[1])
            if direction == "up":
                self.call_requests.append([floor, Direction.UP, True]) if [floor, Direction.UP, True] not in self.call_requests else None
            elif direction == "down":
                self.call_requests.append([floor, Direction.DOWN, True])if [floor, Direction.DOWN, True] not in self.call_requests else None

        elif self.serverMessage.startswith("select_floor@"):
            data_part = self.serverMessage.split("@")[1]  # obtain Num1#Num2

            num1 = int(data_part.split("#")[0])  # get ["Num1", "Num2"]
            num2 = int(data_part.split("#")[1])  # get ["Num1", "Num2"]
            self.select_floor(num2,num1)

        elif self.serverMessage.startswith("open_door"):
            elevatorId = int(self.serverMessage.split("#")[1])
            self.select_oc(elevatorId, 0)

        elif self.serverMessage.startswith("close_door"):
            elevatorId = int(self.serverMessage.split("#")[1])
            self.select_oc(elevatorId, 1)

        else:
            print("Invalid Instruction!")
        

    def startui(self):
        self.ui = ElevatorSystemUI(self, num_elevators=len(self.elevators), max_floors=self.max_floor)
        self.ui.show()

    # def run(self):

    #     self.app = QApplication(sys.argv)
    #     self.ui = ElevatorSystemUI(self, num_elevators=len(self.elevators), max_floors=self.max_floor)
    #     self.ui.show()
        
    #     self.timer = QTimer()
    #     self.timer.timeout.connect(self.process_events)
    #     self.timer.start(100)  # 每1毫秒运行一次
        
    #     sys.exit(self.app.exec())

    def process_events(self):
        if self.is_received_new_message():
            #  if not self.messageUnprocessed:
            self.timeStamp = self.zmqThread.messageTimeStamp
            self.serverMessage = self.zmqThread.receivedMessage
            self.messageUnprocessed = True
            self.process_message()
            self.messageUnprocessed = False

    def shutdown(self):
        self.caller_running = False

        #  for elevator in self.elevators:
        #      elevator.running = False
        #      elevator.stop()
        #  for t in self.threads:
        #      t.join()
