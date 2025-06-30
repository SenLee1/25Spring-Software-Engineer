import sys
from elevator import ElevatorState, Direction
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont

class ElevatorUI(QWidget):
    floor_changed = pyqtSignal(int, int)  # elevator_id, floor
    state_changed = pyqtSignal(int, int)  # elevator_id, state (0=open, 1=close)

    def __init__(self, elevator_id, max_floors=3):
        super().__init__()
        self.elevator_id = elevator_id
        self.max_floors = max_floors
        self.total_floors = max_floors + 1  
        self.current_floor = 1
        self.state = ElevatorState.stopped_door_closed
        self.direction = 0  # IDLE
        self.floor_buttons = {}
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(200, 750)
        self.setWindowTitle(f'Elevator {self.elevator_id}')

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 电梯井
        self.shaft = QFrame(self)
        self.shaft.setFrameShape(QFrame.Shape.Box)
        self.shaft.setLineWidth(2)
        self.shaft.setGeometry(10, 10, 180, 400)  

        floor_height = 400 // self.total_floors

        for i in range(self.total_floors):
            floor = QFrame(self.shaft)
            floor.setFrameShape(QFrame.Shape.Box)
            floor.setGeometry(0, i * floor_height, 180, floor_height)

        # 左门
        self.left_door = QLabel(self.shaft)
        self.left_door.setStyleSheet("background-color: #4682B4; border: 1px solid #1E3F66;")
        self.left_door.setGeometry(1, 200, 88, 100)  # (x, y, width, height)

        # 右门
        self.right_door = QLabel(self.shaft)
        self.right_door.setStyleSheet("background-color: #4682B4; border: 1px solid #1E3F66;")
        self.right_door.setGeometry(91, 200, 88, 100)


        display_frame = QFrame(self)
        display_frame.setFrameShape(QFrame.Shape.Box)
        display_frame.setGeometry(10, 440, 180, 300)  
        display_layout = QVBoxLayout()
        display_frame.setLayout(display_layout)

        # --- 楼层数字 ---
        self.floor_display = QLabel("1")
        self.floor_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.floor_display.setFixedHeight(30)
        self.floor_display.setFont(QFont('Arial', 24, QFont.Weight.Bold))

        # --- 方向箭头 ---
        self.direction_display = QLabel("■")
        self.direction_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.direction_display.setFixedHeight(30)
        self.direction_display.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        self.direction_display.setStyleSheet("color: gray;")

        # --- 楼层按钮区域 ---
        button_layout = QVBoxLayout()
        for floor_num in [3, 2, 1, 0]:
            if floor_num == 0:
                button = QPushButton(str(-1))
                button.setFixedHeight(30)
                button_layout.addWidget(button)
                button.clicked.connect(self.create_floor_handler(-1))
                self.floor_buttons[floor_num] = button
            else:
                button = QPushButton(str(floor_num))
                button.setFixedHeight(30)
                button_layout.addWidget(button)
                button.clicked.connect(self.create_floor_handler(floor_num))
                self.floor_buttons[floor_num] = button

        control_layout = QHBoxLayout()

        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(lambda: self.open_door())
        control_layout.addWidget(self.open_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(lambda: self.close_door())
        control_layout.addWidget(self.close_btn)

        # 添加三个部分到 display_layout 中
        display_layout.addWidget(self.floor_display)
        display_layout.addWidget(self.direction_display)
        display_layout.addLayout(button_layout)
        display_layout.addLayout(control_layout)

        #  main_layout.addLayout(display_layout)
    def create_floor_handler(self, floor):
        def handler():
            self.floor_changed.emit(self.elevator_id, floor)
        return handler

    def update_position(self, car):

        current_floor = car[0]
        current_door = car[1]
        floor_loc = int((3 - current_floor) * 100)
        door_loc = int((1-current_door)*88)

        #  self.left_door.setGeometry(1, 200, 88, 100)  # (x, y, width, height)

        self.left_door.setGeometry(1, floor_loc, door_loc, 100)  # (x, y, width, height)
        self.right_door.setGeometry(91+87-door_loc, floor_loc, door_loc, 100)
        return

    def highlight_floor_button(self, floor, highlight=True):
        if floor in self.floor_buttons:
            btn = self.floor_buttons[floor]
            if highlight:
                btn.setStyleSheet("background-color: #FFA500; font-weight: bold;")
            else:
                btn.setStyleSheet("")  # Reset to default

    # update the status display: direction, color
    def update_state(self, state, direction=0):
        self.state = state
        self.direction = direction

        direction = int(direction) if direction is not None else 0
        if direction == 1:  # Up
            direction_symbol = "↑"
            color = "green"
        elif direction == -1:  # Down
            direction_symbol = "↓"
            color = "red"
        else:  # Idle
            direction_symbol = "■"
            color = "gray"

        # Update direction display
        self.direction_display.setText(direction_symbol)
        self.direction_display.setStyleSheet(f"color: {color};")

    def open_door(self):
        if self.state == ElevatorState.stopped_closing_door or self.state == ElevatorState.stopped_door_closed :  # Can only close from open state
            self.state_changed.emit(self.elevator_id, 0)  # 0 for open

    def close_door(self):
        if self.state == ElevatorState.stopped_door_opened or self.state == ElevatorState.stopped_opening_door :  # Can only close from open state
            self.state_changed.emit(self.elevator_id, 1)  # 1 for close

class ElevatorSystemUI(QMainWindow):
    def __init__(self, elevator_system, num_elevators=2, max_floors=3):
        super().__init__()
        self.elevator_system = elevator_system
        self.num_elevators = num_elevators
        self.max_floors = max_floors
        self.total_floors = max_floors + 1  # Including B1
        self.elevators = []
        self.up_buttons = {}
        self.down_buttons = {}
        self.reset_btn = None
        self.init_finished = False
        self.lasttime=0

        self.init_ui()

        # Setup timer to periodically check elevator states
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui_from_system)
        self.update_timer.start(17)  # Update every 100ms
        # self.update_timer.start(20)  # Update every 100ms
        self.init_finished = True

        #  self.door_animation_timer = QTimer()
        #  self.door_animation_timer.timeout.connect(self.update_door_animation)

    def init_ui(self):
        self.setWindowTitle('Elevator Control System')
        self.setGeometry(100, 100, 600, 700)  

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Create elevator UIs
        for i in range(2):
            elevator = ElevatorUI(i+1, 3)
            elevator.floor_changed.connect(self.handle_floor_request)
            elevator.state_changed.connect(self.handle_door_command)
            main_layout.addWidget(elevator)
            self.elevators.append(elevator)

        # Call panel
        call_panel = QFrame()
        call_panel.setFrameShape(QFrame.Shape.Box)
        call_panel.setLineWidth(2)
        call_panel.setFixedWidth(200)


        call_layout = QVBoxLayout()
        call_panel.setLayout(call_layout)

        call_label = QLabel("External Calls")
        call_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        call_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        call_layout.addWidget(call_label)

        # Add elevator status displays at the top
        c = 0
        # Create floor list including basement
        floors = list(range(self.max_floors, 0, -1))  # From max floor to basement
        floors.append(0)
        status_frame = QFrame()
        status_layout = QHBoxLayout()
        status_frame.setLayout(status_layout)
        for i in range(self.num_elevators):
            display_frame = QFrame()
            display_frame.setFrameShape(QFrame.Shape.Box)
            display_layout = QVBoxLayout()
            display_frame.setLayout(display_layout)

            elevator_label = QLabel(f"Elevator {i+1}")
            elevator_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            display_layout.addWidget(elevator_label)

            floor_display = QLabel("1")
            floor_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            floor_display.setFont(QFont('Arial', 14, QFont.Weight.Bold))
            display_layout.addWidget(floor_display)

            direction_display = QLabel("")
            direction_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            direction_display.setFont(QFont('Arial', 14, QFont.Weight.Bold))
            display_layout.addWidget(direction_display)
            status_layout.addWidget(display_frame)
            # used for update
            setattr(self, f'elevator_{i+1}_floor{3}', floor_display)
            setattr(self, f'elevator_{i+1}_direction{3}', direction_display)
        call_layout.addWidget(status_frame)
        for floor in floors:
            status_frame = QFrame()
            status_layout = QHBoxLayout()
            status_frame.setLayout(status_layout)
            c += 1
            call_layout.addWidget(status_frame)

            floor_frame = QFrame()
            floor_layout = QHBoxLayout()
            floor_frame.setLayout(floor_layout)

            floor_label = QLabel("-1" if floor == 0 else str(floor))
            floor_label.setFixedSize(20,20)

            floor_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # align left
            floor_layout.addWidget(floor_label)

            # Add up button (except for top floor)
            if floor != self.max_floors:
                up_btn = QPushButton("▲")
                up_btn.setFixedWidth(40)
                up_btn.clicked.connect(self.create_call_handler(floor, 1))
                floor_layout.addWidget(up_btn)
                self.up_buttons[floor] = up_btn

            # Add down button (except for basement)
            if floor != 0:
                down_btn = QPushButton("▼")
                down_btn.setFixedWidth(40)
                down_btn.clicked.connect(self.create_call_handler(floor, -1))
                floor_layout.addWidget(down_btn)
                self.down_buttons[floor] = down_btn

            call_layout.addWidget(floor_frame)

        # Reset button
        self.reset_btn = QPushButton("Reset System")
        self.reset_btn.clicked.connect(self.reset_system)
        call_layout.addWidget(self.reset_btn)

        call_layout.addStretch()

        main_layout.addWidget(call_panel)

    def update_ui_from_system(self):
        for i, elevator in enumerate(self.elevator_system.elevators):
            # Update floor position
            self.elevators[i].update_position(elevator.car)
            self.elevators[i].floor_display.setText(str(elevator.current_floor)if elevator.current_floor != 0 else "-1")

            # Update state and direction
            state = elevator.state
            direction = elevator.direction.value if hasattr(elevator.direction, 'value') else 0
            self.elevators[i].update_state(state, direction)

            # Update the displays in the call panel
            #  for j in range(self.total_floors):
            #      if j == 3:
            floor_display = getattr(self, f'elevator_{i+1}_floor{3}')
            direction_display = getattr(self, f'elevator_{i+1}_direction{3}')

            # Set floor display
            floor_str = "-1" if elevator.current_floor == 0 else str(elevator.current_floor)
            floor_display.setText(floor_str)

            # Set direction display
            if direction == 1:
                direction_display.setText("▲")
                direction_display.setStyleSheet("color: green;")
            elif direction == -1:
                direction_display.setText("▼")
                direction_display.setStyleSheet("color: red;")
            else:
                direction_display.setText("■")
                direction_display.setStyleSheet("color: gray;")
        self.update_button_highlights()



    def highlight_call_button(self, floor, direction, highlight=True):
        """Highlight external call buttons"""
        if direction == 1 and floor in self.up_buttons:
            btn = self.up_buttons[floor]
        elif direction == -1 and floor in self.down_buttons:
            btn = self.down_buttons[floor]
        else:
            return

        if highlight:
            btn.setStyleSheet("background-color: #FFA500; font-weight: bold;")
        else:
            btn.setStyleSheet("")  # Reset to default

    def create_call_handler(self, floor, direction):
        def handler():
            direction_str = "up" if direction == 1 else "down"
            floor_str = str(floor) 
            #  print(floor)
            # self.elevator_system.zmqThread.sendMsg(f"call_{direction_str}@{floor_str}")
            self.elevator_system.zmqThread.receivedMessage = f"call_{direction_str}@{floor_str}"
            self.elevator_system.zmqThread.messageTimeStamp = time.time()
        return handler

    def handle_floor_request(self, elevator_id, floor):
        floor_str = str(floor) 
        #  print(floor)

        self.elevator_system.zmqThread.receivedMessage = f"select_floor@{floor_str}#{elevator_id}"
        self.elevator_system.zmqThread.messageTimeStamp = time.time()
        # self.elevator_system.zmqThread.messageTimeStamp = time.time() + 1000-self.lasttime

    def handle_door_command(self, elevator_id, command):
        cmd = "open_door" if command == 0 else "close_door"
        self.elevator_system.zmqThread.receivedMessage = f"{cmd}#{elevator_id}"
        self.elevator_system.zmqThread.messagetimestamp = time.time()

    # Update button highlights based on elevator system state
    def update_button_highlights(self):
        # Reset all button highlights
        for floor in self.up_buttons:
            self.highlight_call_button(floor, 1, False)
        for floor in self.down_buttons:
            self.highlight_call_button(floor, -1, False)
        for elevator_ui in self.elevators:
            for floor in elevator_ui.floor_buttons:
                elevator_ui.highlight_floor_button(floor, False)

        # Highlight based on current destinations and requests

        # Highlight external calls
        for elevator in self.elevator_system.elevators:
            for floor, direction in self.elevator_system.active_requests:
                #  self.highlight_call_button(floor, direction.value if hasattr(direction, 'value') else direction, True)
                self.highlight_call_button(floor, direction.value, True)
            for floor, direction in elevator.active_requests:
                self.highlight_call_button(floor, direction.value, True)
                #  self.highlight_call_button(floor, direction.value if hasattr(direction, 'value') else direction, True)

        # Highlight internal selections
        for i in range(self.num_elevators):
            elevator = self.elevator_system.elevators[i]
            for dest in elevator.destination_floors:
                if dest[1] == Direction.IDLE:
                    self.elevators[i].highlight_floor_button(dest[0], True)

    def reset_system(self):
        self.elevator_system.zmqThread.receivedMessage = "reset"
        self.elevator_system.zmqThread.messageTimeStamp = time.time()

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     from elevator_system import ElevatorSystem
#     system = ElevatorSystem(num_elevators=2, max_floor=3, identity="TestUI")
#     window = ElevatorSystemUI(system, num_elevators=2, max_floors=3)
#     window.show()
#     sys.exit(app.exec())
