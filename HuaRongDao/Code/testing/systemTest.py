# test_frontend_ui.py

import sys
import unittest
import pyautogui

from PyQt5.QtWidgets import QApplication, QPushButton, QDialog
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtCore import Qt

# 导入你原始的 frontend 脚本中所有顶层类
from frontend import ZmqThread, BoardWidget, GameWindow


class TestFrontendUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 全局只需要一个 QApplication 实例
        cls.app = QApplication(sys.argv)

    def setUp(self):
        # 启动主窗口，自动会创建并启动内部的 ZmqThread
        self.win = GameWindow()
        self.win.show()
        self.spy = QSignalSpy(self.win.zmq.request)

        # 确保 zmq 线程已经启动
        # （取决于你的 GameWindow 实现，如果需要手动 start，请取消下面注释）
        # self.zmq = ZmqThread()
        # self.zmq.responseReceived.connect(self.on_response)
        # self.win.zmq.start()

    def tearDown(self):
        self.win.close()
        # 如果你手动 start 了线程，这里也可以停止它
        # self.win.zmq.stop()
        # self.win.zmq.wait()
        
    def test_expected_opt(self):
        """Test button click functionality and observe GUI changes"""

        select_btn = getattr(self.win, "level_btn", None)
        self.assertIsNotNone(select_btn, "没有在 GameWindow 中找到 level_btn")
        QTest.mouseClick(select_btn, Qt.LeftButton)
        QTest.qWait(1000)

        menu = self.win.level_menu
        
        # 2) 在菜单上点击第一个 action
        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        for act in menu.actions():
            if act.text() == "随机挑战":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@"))
        origin_board = self.spy_rec[0][0].split("@")[1]
        

        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        reset_btn = getattr(self.win, "reset_btn", None)
        self.assertIsNotNone(reset_btn, "没有在 GameWindow 中找到 reset_btn")
        QTest.qWait(100)
        QTest.mouseClick(reset_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@"))
        now_board = self.spy_rec[0][0].split("@")[1]
        self.assertNotEqual(now_board, origin_board)

        QTest.mouseClick(select_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertTrue(menu.isVisible(), True)

        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        # 2) 在菜单上点击第一个 action
        for act in menu.actions():
            if act.text() == "测试关卡":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@24432673011501158##9"))

        # 找到并点击 Hint 按钮
        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        hint_btn = getattr(self.win, 'hint_btn', None)
        QTest.mouseClick(hint_btn, Qt.LeftButton)
        self.assertEqual(self.spy_rec[0][0], "HINT@11")
        QTest.qWait(100)
        
        rect = self.win.board_widget.rect_map['9']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(100)
        self.assertEqual(self.win.board_widget.selected_id, "9")

        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        left_btn = getattr(self.win, 'left_btn', None)
        QTest.mouseClick(left_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@24432673011501158#9#"))

        
        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        undo_btn = getattr(self.win, 'undo_btn', None)
        QTest.mouseClick(undo_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@24432673011501158##9"))

        rect = self.win.board_widget.rect_map['1']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(100)
        self.assertEqual(self.win.board_widget.selected_id, "1")

        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        down_btn = getattr(self.win, 'down_btn', None)
        QTest.mouseClick(down_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@24432673011501158##9"))
        QTest.qWait(100)

    def test_unexpected_opt(self):
        """Test button click functionality and observe GUI changes"""

        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        down_btn = getattr(self.win, 'down_btn', None)
        QTest.mouseClick(down_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@####################"))
        self.assertEqual(self.spy_rec[0][0].split("@")[4], "Invalid move!")
        QTest.qWait(100)
        
        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        undo_btn = getattr(self.win, 'undo_btn', None)
        QTest.mouseClick(undo_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@####################"))
        self.assertEqual(self.spy_rec[0][0].split("@")[4], "Undo complete!")
        QTest.qWait(100)
        
        self.spy = QSignalSpy(self.win.zmq.request)
        reset_btn = getattr(self.win, 'reset_btn', None)
        QTest.mouseClick(reset_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertEqual(len(self.spy), 0)
        QTest.qWait(100)

        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)
        hint_btn = getattr(self.win, 'hint_btn', None)
        QTest.mouseClick(hint_btn, Qt.LeftButton)
        QTest.qWait(100)
        self.assertEqual(self.spy_rec[0][0], "MSG@Hint generation failed")
        QTest.qWait(100)

        QTest.qWait(2000)


if __name__ == "__main__":
    unittest.main()
