import threading
import time
from NetClient import ZmqClientThread
from enum import Enum
from enum import IntEnum


class ElevatorState(IntEnum):
    up = 0
    down = 1
    stopped_door_closed = 2
    stopped_door_opened = 3
    stopped_opening_door = 4
    stopped_closing_door = 5


class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0


class Elevator:
    def __init__(self, id, max_floor=3, zmqThread=ZmqClientThread):
        self.id = id
        self.current_floor: int = 1
        self.direction = Direction.IDLE
        self.max_floor = max_floor
        self.remain_open_time = 3
        self.remain_open_time = 3
        # destination floors that is called in the elevator
        self.call_direction = Direction.IDLE
        # element: [floor, direction,priority].
        #  where if direction = IDLE->inside call
        #  if direction = UP -> outside call_up
        #  if direction = DOWN -> outside call_down
        self.destination_floors = []

        self.currentDestination = None
        self.running = True
        self.delt = 0.05

        self.update_callback = None
        self.request_lock = threading.Lock()
        # destination floors called outside the elevator
        self.active_requests = set()
        self.state = ElevatorState.stopped_door_closed
        self.finished = True
        self.zmqThread = zmqThread
        self.message = ""
        # Car UI representation
        self.car = [1.0, 0.0] 

    def update_destination(self):
        to_remove = set()
        for floor in self.destination_floors.copy():
            if floor[0] == self.current_floor:
                if (floor[1] == Direction.IDLE or (self.direction == floor[1]) and self.direction == floor[1]):
                    self.destination_floors.remove(floor)
        for require in self.active_requests:
            if require[0] == self.current_floor and require[1] == self.direction:
                to_remove.add(require)
        self.active_requests -= to_remove

    def reset(self):
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.destination_floors = []
        self.currentDestination = None
        self.active_requests = set()
        self.finished = True
        self.car = [1.0, 0.0]  # Reset car position and door state
        self.running = True
        self.state = ElevatorState.stopped_door_closed
        self.serverMessage = ""

    def start_run(self):
        self.running = True

    def add_destination(self, floor, is_external_call=Direction.IDLE, pri=0.0):
        if floor == -1:
            floor = 0
        existing = [f for f in self.destination_floors if f[0]
                    == floor and f[1] == is_external_call]
        if not existing and (0 <= floor <= self.max_floor or floor == -1):
            self.destination_floors.append([int(floor), is_external_call, pri])
            if self.currentDestination is None:
                self.currentDestination = self.destination_floors[0]
                if self.state == ElevatorState.stopped_door_closed:
                    if self.currentDestination[0] > self.current_floor or self.currentDestination[0] or self.currentDestination[1] == Direction.UP:
                        #  self.state = ElevatorState.up
                        self.direction = Direction.UP
                    elif self.currentDestination[0] < self.current_floor or self.currentDestination[0] or self.currentDestination[1] == Direction.DOWN:
                        #  self.state = ElevatorState.down
                        self.direction = Direction.DOWN
            self.destination_floors.sort(key=lambda x: (x[2], x[0]))
            if is_external_call != Direction.IDLE:
                self.active_requests.add((int(floor), is_external_call))

    def resort_destination(self):
        if self.destination_floors and self.currentDestination:
            for dest in self.destination_floors:
                if self.direction == Direction.IDLE:
                    dest[2] = -5*abs(dest[0] - self.current_floor)
                else:
                    dest[2] = 1 if dest[1] == Direction.IDLE else 0
                    if self.state== ElevatorState.up:
                        if float(dest[0]) - self.car[0] >= 0:
                            if self.currentDestination[0] == dest[0]:
                                dest[2] += -99999.0 + 10*float(float(dest[0]) - self.car[0])
                            dest[2] += -9999.0 + 10*float(float(dest[0]) - self.car[0])
                            # continue
                    elif self.state == ElevatorState.down:
                        if self.car[0] - float(dest[0]) >= 0:
                            if self.currentDestination[0] == dest[0]:
                                dest[2] += -99999.0 + 10*float(float(dest[0]) - self.car[0])
                            dest[2] += -9999.0 - 10*float(float(dest[0]) - self.car[0])
                            # continue
                    else:
                        if self.direction == Direction.UP:
                            if dest[0] - self.current_floor >= 0:
                                if dest[0] == self.current_floor:

                                    dest[2] += -99999.0 + 10*float(float(dest[0]) - self.car[0])
                                dest[2] += -9999 + dest[0] - self.current_floor
                                # continue
                        elif self.direction == Direction.DOWN:
                            if self.current_floor - dest[0] >= 0:
                                if dest[0] == self.current_floor:
                                    dest[2] += -99999.0 + 10*float(float(dest[0]) - self.car[0])
                                dest[2] += -9999 - (dest[0] - self.current_floor)
                                # continue
                    dest[2] += abs(dest[0] - self.current_floor) * 5

            self.destination_floors.sort(key=lambda x: (x[2]))

    def open_door(self):
        if self.state == ElevatorState.up or self.state == ElevatorState.down:
            return
        self.running = False
        if self.state == ElevatorState.stopped_door_opened:
            self.remain_open_time = 3
        elif self.state == ElevatorState.stopped_door_closed or self.state == ElevatorState.stopped_closing_door:
            self.state = ElevatorState.stopped_opening_door
        self.door_open = True
        if self.update_callback:
            self.update_callback(self.id)
        self.running = True
        self.finished = False

    def close_door(self):
        if self.state == ElevatorState.up or self.state == ElevatorState.down or self.state == ElevatorState.stopped_closing_door:
            return
        self.running = False
        if self.state == ElevatorState.stopped_door_opened:
            self.state = ElevatorState.stopped_closing_door
        elif self.state == ElevatorState.stopped_door_closed:
            self.zmqThread.sendMsg("door_closed#"+str(self.id))
        self.door_open = False
        if self.update_callback:
            self.update_callback(self.id)
        self.running = True
        self.running = True

    def stop(self):
        self.running = False
        self.reset()

    def move(self):
        # while self.running:
        ############ Your timed automata design ############
        # Example for the naive testcase
        self.resort_destination()
        if self.current_floor == -1:
            self.direction = Direction.UP
        elif self.current_floor == 3:
            self.direction = Direction.DOWN
        if self.destination_floors:
            self.currentDestination = self.destination_floors[0]
            if self.currentDestination[0] > self.current_floor:
                self.direction = Direction.UP
            elif self.currentDestination[0] < self.current_floor:
                self.direction = Direction.DOWN
            else:
                if self.currentDestination[1] != Direction.IDLE:
                    self.direction = self.currentDestination[1]

            self.finished = False
        else:
            self.currentDestination = None

        if self.currentDestination is not None:
            if self.currentDestination[1].value == 1:
                self.call_direction = Direction.UP
            elif self.currentDestination[1].value == -1:
                self.call_direction = Direction.DOWN
            else:
                self.call_direction = self.direction
        

        if self.finished:
            self.direction = Direction.IDLE
            self.call_direction = Direction.IDLE
        else:
            # print("1",self.currentDestination)
            # print("2",self.destination_floors)
            match self.state:
                case ElevatorState.stopped_door_closed:
                    if self.currentDestination is not None:
                        if (self.currentDestination[0] == self.current_floor):
                            if self.current_floor != 0:
                                self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{self.current_floor}#{self.id}"
                            else:
                                self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{-1}#{self.id}"

                            self.zmqThread.sendMsg(self.message)
                            self.state = ElevatorState.stopped_opening_door
                            self.update_destination()
                            # time.sleep(1)
                        elif (self.currentDestination[0] > self.current_floor):
                            self.state = ElevatorState.up
                            self.direction = Direction.UP
                        else:
                            self.state = ElevatorState.down
                            self.direction = Direction.DOWN

                case ElevatorState.stopped_opening_door:
                    self.car[1] += self.delt
                    self.car[1] = round(self.car[1], 2)  
                    if self.destination_floors:
                        if self.destination_floors[0][0] == self.current_floor:
                            if self.current_floor != 0:
                                self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{self.current_floor}#{self.id}"
                            else:
                                self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{-1}#{self.id}"
                            self.zmqThread.sendMsg(self.message)
                            self.update_destination()
                    if self.car[1] == 1.00:
                        self.message = f"door_opened#{self.id}"
                        self.zmqThread.sendMsg(self.message)
                        self.state = ElevatorState.stopped_door_opened
                    # time.sleep(0.1)

                case ElevatorState.stopped_closing_door:
                    if self.car[1] > 0:
                        self.car[1] -= self.delt
                        self.car[1] = round(self.car[1], 2)  
                    #  while self.remain_open_time > 0 and self.state == ElevatorState.stopped_closing_door:
                    if self.destination_floors:
                        if self.destination_floors[0][0] == self.current_floor:
                            self.state = ElevatorState.stopped_opening_door
                            if self.current_floor != 0:
                                self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{self.current_floor}#{self.id}"
                            else:
                                self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{-1}#{self.id}"
                            self.zmqThread.sendMsg(self.message)
                            self.update_destination()
                    # time.sleep(0.1)
                    if self.state != ElevatorState.stopped_closing_door:
                        self.state = ElevatorState.stopped_opening_door
                        # continue
                    if self.car[1] == 0 and self.state == ElevatorState.stopped_closing_door:
                        self.state = ElevatorState.stopped_door_closed
                        self.message = f"door_closed#{self.id}"
                        self.zmqThread.sendMsg(self.message)
                        if len(self.destination_floors) == 0:
                            self.finished = True
                    #  time.sleep(0.2)
                        


                case ElevatorState.stopped_door_opened:
                    while self.remain_open_time > 0 and self.state == ElevatorState.stopped_door_opened:
                        if self.destination_floors:
                            if self.destination_floors[0][0] == self.current_floor:
                                # print(3)
                                self.state = ElevatorState.stopped_door_opened
                                self.remain_open_time=2
                                if self.current_floor != 0:
                                    self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{self.current_floor}#{self.id}"
                                else:
                                    self.message = f"{str(self.call_direction.name).lower()}_floor_arrived@{-1}#{self.id}"
                                self.zmqThread.sendMsg(self.message)
                                self.update_destination()
                                continue
                        self.remain_open_time -= 1
                        # time.sleep(0.1)
                        if self.state != ElevatorState.stopped_door_opened:
                            break
                        if self.remain_open_time == 0 and self.state == ElevatorState.stopped_door_opened:
                            self.state = ElevatorState.stopped_closing_door
                            self.message = f"door_closed#{self.id}"
                            self.zmqThread.sendMsg(self.message)
                            break
                    self.remain_open_time = 2

                case ElevatorState.up:
                    self.car[0] += self.delt
                    self.car[0] = round(self.car[0], 2)  
                    if self.car[0] == round(int(self.car[0]), 2):
                        self.current_floor += 1
                    if self.currentDestination is not None:
                        if (float(self.currentDestination[0]) == self.car[0]):
                            self.current_floor = int(self.car[0])
                            self.state = ElevatorState.stopped_door_closed
                    # time.sleep(0.2)

                case ElevatorState.down:
                    self.car[0] -= self.delt
                    self.car[0] = round(self.car[0], 2)  
                    if self.car[0] == round(int(self.car[0]), 2):
                        self.current_floor -= 1
                    if self.currentDestination is not None:
                        if (float(self.currentDestination[0]) == self.car[0]):
                            self.current_floor = int(self.car[0])
                            self.state = ElevatorState.stopped_door_closed
                    # time.sleep(0.2)

            # time.sleep(0.01)

