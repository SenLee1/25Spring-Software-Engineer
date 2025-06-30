import sys
import time
import zmq
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QDialog, QFormLayout, QMenu
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QThread, QPoint

# ZMQ communication thread
class ZmqThread(QThread):
    responseReceived = pyqtSignal(str)  # 接收字符串
    request = pyqtSignal(str)           # 发字符串

    def __init__(self):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        self.request.connect(self.send_request)

    def send_request(self, msg):
        self.socket.send_string(msg)
        reply = self.socket.recv_string()
        self.responseReceived.emit(reply)

    def run(self):
        self.exec_()

# Board rendering and selection widget
class BoardWidget(QWidget):
    pieceSelected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.board = ['#'] * 20
        self.selected_id = '1'
        self.piece_colors = {
            '0': QColor(150, 150, 255), '1': QColor(255, 200, 200),
            '2': QColor(200, 255, 200), '3': QColor(255, 255, 150),
            '4': QColor(200, 200, 255), '5': QColor(255, 180, 255),
            '6': QColor(200, 255, 255), '7': QColor(255, 220, 180),
            '8': QColor(180, 255, 220), '9': QColor(220, 180, 255),
            '#': QColor(240, 240, 240)
        }
        self.rect_map = {}
        self.piece_pixmaps = {}
        for pid in ['0','1','2','3','4','5','6']:
            pix = QPixmap(f"Development\\main\\{pid}.png")
            self.piece_pixmaps[pid] = pix
            
        self.hint_info = None  # (pid, direction)
        self.hint_timer = QTimer()
        self.hint_timer.setSingleShot(True)
        self.hint_timer.timeout.connect(self.clear_hint)

    def get_piece_span(self, pid):
        if pid == '1':
            return 2, 2
        elif pid in {'0', '2', '3', '5'}:
            return 1, 2
        elif pid == '4':
            return 2, 1
        else:
            return 1, 1
        
    def show_hint(self, pid, direction):
        self.hint_info = (pid, direction)
        self.hint_timer.start(3000)
        self.update()

    def clear_hint(self):
        self.hint_info = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        area = self.rect()
        target_ratio = 4 / 5
        if area.width() / area.height() > target_ratio:
            h = area.height()
            w = int(h * target_ratio)
        else:
            w = area.width()
            h = int(w / target_ratio)
        board_x = area.x() + (area.width() - w) // 2
        board_y = area.y() + (area.height() - h) // 2
        board_rect = QRect(board_x, board_y, w, h)

        cell_w = board_rect.width() / 4
        cell_h = board_rect.height() / 5

        self.rect_map.clear()
        drawn = set()
        for idx, pid in enumerate(self.board):
            if pid == '#' or pid in drawn:
                continue
            drawn.add(pid)

            span_w, span_h = self.get_piece_span(pid)
            r, c = divmod(idx, 4)
            x = board_rect.x() + c * cell_w
            y = board_rect.y() + r * cell_h
            rect = QRect(int(x), int(y), int(span_w * cell_w), int(span_h * cell_h))
            self.rect_map[pid] = rect

            key = pid if pid in {'0','1','2','3','4','5'} else '6'
            pix = self.piece_pixmaps.get(key)
            if pix and not pix.isNull():
                scaled = pix.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                dx = (rect.width() - scaled.width()) // 2
                dy = (rect.height() - scaled.height()) // 2
                target = QRect(rect.x() + dx, rect.y() + dy, scaled.width(), scaled.height())
                painter.drawPixmap(target, scaled)
            else:
                painter.setPen(QPen(Qt.black, 2))
                painter.setBrush(self.piece_colors.get(pid, QColor(200,200,200)))
                painter.drawRect(rect)

            if pid == self.selected_id:
                color = QColor(255, 255, 0, 60)
                painter.fillRect(rect, color)
                inner = rect.adjusted(2, 2, -2, -2)
                painter.drawRect(inner)
            else:
                painter.setPen(QPen(Qt.black, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
        # 绘制提示箭头（如有）
        if self.hint_info:
            pid, direction = self.hint_info
            if pid in self.rect_map:
                rect = self.rect_map[pid]
                painter.setPen(QPen(Qt.white, 4))
                painter.setBrush(Qt.white)
                center = rect.center()
                arrow_size = min(rect.width(), rect.height()) // 4

                if direction == 0:  # ↑
                    points = [
                        QPoint(center.x(), center.y() - arrow_size),
                        QPoint(center.x() - arrow_size, center.y() + arrow_size),
                        QPoint(center.x() + arrow_size, center.y() + arrow_size)
                    ]
                elif direction == 1:  # ↓
                    points = [
                        QPoint(center.x(), center.y() + arrow_size),
                        QPoint(center.x() - arrow_size, center.y() - arrow_size),
                        QPoint(center.x() + arrow_size, center.y() - arrow_size)
                    ]
                elif direction == 2:  # ←
                    points = [
                        QPoint(center.x() - arrow_size, center.y()),
                        QPoint(center.x() + arrow_size, center.y() - arrow_size),
                        QPoint(center.x() + arrow_size, center.y() + arrow_size)
                    ]
                elif direction == 3:  # →
                    points = [
                        QPoint(center.x() + arrow_size, center.y()),
                        QPoint(center.x() - arrow_size, center.y() - arrow_size),
                        QPoint(center.x() - arrow_size, center.y() + arrow_size)
                    ]
                painter.drawPolygon(*points)
        notch_w = cell_w * 2
        notch_start_x = int(board_rect.x() + (board_rect.width() - notch_w) / 2)
        notch_end_x   = int(notch_start_x + notch_w)
        y0 = board_rect.y() + board_rect.height()

        # print(notch_start_x, notch_end_x)

        # 构造多段折线，绕一圈但在底边跳过缺口
        points = [
            # 从左上角开始，顺时针
            QPoint(board_rect.x(), board_rect.y()),
            QPoint(board_rect.x() + board_rect.width(), board_rect.y()),
            QPoint(board_rect.x() + board_rect.width(), y0),
            # 底边右半段：从右下角到缺口右端
            QPoint(notch_end_x, y0),
            QPoint(notch_end_x, y0 + 5),
            # 跳过缺口，接着从缺口左端到左下角
            QPoint(notch_start_x, y0 + 5),
            QPoint(notch_start_x, y0),
            QPoint(board_rect.x(), y0),
            # 回到起点
            QPoint(board_rect.x(), board_rect.y())
        ]

        painter.setPen(QPen(Qt.red, 10))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(*points)
        painter.end()

    def mousePressEvent(self, event):
        self.clear_hint()
        pos = event.pos()
        for pid, rect in self.rect_map.items():
            if rect.contains(pos):
                self.selected_id = pid
                self.update()
                self.pieceSelected.emit(pid)
                break

class GameWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HuaRongDao - Frontend")
        self.setGeometry(200, 200, 600, 400)

        self.steps = 0
        self.elapsed = 0
        self.current_level = None
        self.selected_piece = '1'

        self.zmq = ZmqThread()
        self.zmq.responseReceived.connect(self.on_response)
        self.zmq.start()

        self.board_widget = BoardWidget()
        self.board_widget.pieceSelected.connect(self.on_piece_selected)
        self.info_label = QLabel("Initializing...")
        self.timer_label = QLabel("Time: 0s")
        self.step_label = QLabel("Steps: 0")
        self.record_label = QLabel("Best: ∞ s / ∞ steps")

        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.left_btn = QPushButton("←")
        self.right_btn = QPushButton("→")
        self.undo_btn = QPushButton("Undo")
        self.reset_btn = QPushButton("Reset")
        self.level_btn = QPushButton("Select Level")
        self.hint_btn = QPushButton("Hint")

        self.level_menu = QMenu(self)

        move_layout = QGridLayout()
        move_layout.addWidget(self.up_btn, 0, 1)
        move_layout.addWidget(self.left_btn, 1, 0)
        move_layout.addWidget(self.right_btn, 1, 2)
        move_layout.addWidget(self.down_btn, 2, 1)
        move_layout.addWidget(self.undo_btn, 3, 0)
        move_layout.addWidget(self.reset_btn, 3, 2)
        move_layout.addWidget(self.level_btn, 4, 1)
        move_layout.addWidget(self.hint_btn, 5, 1)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.timer_label)
        right_layout.addWidget(self.step_label)
        right_layout.addWidget(self.record_label)
        right_layout.addLayout(move_layout)
        right_layout.addWidget(self.info_label)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.board_widget, stretch=3)
        main_layout.addLayout(right_layout, stretch=1)
        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.zmq.request.emit("get_levels")

        self.up_btn.clicked.connect(lambda: self.send_move('Up'))
        self.down_btn.clicked.connect(lambda: self.send_move('Down'))
        self.left_btn.clicked.connect(lambda: self.send_move('Left'))
        self.right_btn.clicked.connect(lambda: self.send_move('Right'))
        self.undo_btn.clicked.connect(lambda: self.zmq.request.emit("undo"))
        self.reset_btn.clicked.connect(self.reset_game)
        self.level_btn.clicked.connect(self.show_level_menu)
        self.hint_btn.clicked.connect(lambda: self.zmq.request.emit("hint"))

    def populate_level_menu(self):
        self.level_menu.clear()
        for name in self.levels_list:
            self.level_menu.addAction(name, lambda n=name: self._on_level_selected(n))
        self.level_menu.addSeparator()
        self.level_menu.addAction("随机挑战", lambda: self._on_level_selected(None))

    def show_level_menu(self):
        # 在按钮下方弹出菜单
        pos = self.level_btn.mapToGlobal(QPoint(0, self.level_btn.height()))
        self.populate_level_menu()
        self.level_menu.popup(pos)

    def _on_level_selected(self, level_name):
        # 隐藏菜单后设置关卡
        self.level_menu.hide()
        if level_name is None:
            self.set_random_level()
        else:
            self.set_level(level_name)

    def on_piece_selected(self, pid):
        self.selected_piece = pid
        self.board_widget.clear_hint()
        self.info_label.setText(f"Selected piece: {pid}")

    def send_move(self, direction):
        self.board_widget.clear_hizant()
        self.zmq.request.emit(f"move@{self.selected_piece}#{direction}")

    def set_level(self, level_name):
        self.current_level = level_name
        self.steps = 0
        self.elapsed = 0
        self.step_label.setText("Steps: 0")
        self.timer_label.setText("Time: 0s")
        self.record_label.setText("Best: ∞ s / ∞ steps")
        self.zmq.request.emit(f"select_level@{level_name}")

    def set_random_level(self):
        self.steps = 0
        self.elapsed = 0
        self.current_level = "Random"
        self.step_label.setText("Steps: 0")
        self.timer_label.setText("Time: 0s")
        self.record_label.setText("Best: ∞ s / ∞ steps")
        self.zmq.request.emit("random_level")
        # time.sleep(1)

    def reset_game(self):
        if self.current_level:
            self.set_level(self.current_level)
        elif self.current_level == "Random":
            self.set_random_level()

    def update_timer(self):
        self.elapsed += 1
        self.timer_label.setText(f"Time: {self.elapsed}s")

    def on_response(self, msg):
        # 合并状态：STATE@<board>@<steps>@<time>@<info>
        if msg.startswith("STATE@"):
            # 最多分 5 段：["STATE", board, steps, time, info, best_steps, best_time]
            _, board_str, steps_str, time_str, info, best_steps, best_time = msg.split("@", 6)

            # 更新棋盘
            board = list(board_str)
            self.board_widget.board = board
            self.board_widget.update()

            # 更新步数
            self.steps = int(steps_str)
            self.step_label.setText(f"Steps: {self.steps}")

            # 更新计时
            self.elapsed = int(time_str)
            self.timer_label.setText(f"Time: {self.elapsed}s")

            if best_steps != "None" and best_time != "None":
                self.record_label.setText(f"Best: {best_time} s / {best_steps} steps")
            else :
                self.record_label.setText("Best: ∞ s / ∞ steps")

            # 更新提示信息
            if info:
                self.info_label.setText(info)
            return

        # LEVELS@l1,l2,...
        if msg.startswith("LEVELS@"):
            self.levels_list = msg.split("@",1)[1].split(",")
            return

        # HINT@<dir><pid>
        if msg.startswith("HINT@"):
            code = int(msg.split("@", 1)[1])
            pid = code % 10
            dir_code = code // 10
            self.board_widget.show_hint(str(pid), dir_code)
            return

        # 单独的普通消息
        if msg.startswith("MSG@"):
            text = msg.split("@", 1)[1]
            self.info_label.setText(text)
            return

        # DONE
        if msg == "DONE":
            reply = QMessageBox.question(
                self,
                "Victory!",
                "Congratulations, CaoCao has successfully escaped! Would you like to play again?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.reset_game()
            if reply == QMessageBox.No:
                self.reset_game()
                self.show_level_menu()
            return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GameWindow()
    win.show()
    sys.exit(app.exec_())
# python Development\main\frontend_int.py
# python Development\main\backend.py
