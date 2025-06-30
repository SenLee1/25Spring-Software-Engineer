import sys
import threading
from elevator_UI import ElevatorSystemUI
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication
)
if __name__ == '__main__':

    app = QApplication(sys.argv)
    from elevator_system import ElevatorSystem
    system = ElevatorSystem(num_elevators=2, max_floor=3, identity="Team8")
    ui = ElevatorSystemUI(system, num_elevators=2, max_floors=3)
    ui.show()
    for t in system.threads:
        t.start()
    
    sys.exit(app.exec())
