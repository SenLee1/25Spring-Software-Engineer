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
        self.spy_rec = QSignalSpy(self.win.zmq.responseReceived)

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

    def test_invalid_move(self):
        """点击上箭头后验证收到后端的 Invalid move 消息"""
        # 找到上箭头按钮
        up_btn = getattr(self.win, "up_btn", None)
        self.assertIsNotNone(up_btn, "没有找到 up_btn")
        # 点击按钮
        QTest.mouseClick(up_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        # 获取信号中发送的数据
        req = self.spy[0][0]
        self.assertEqual(req, "move@1#Up")
        msg = self.spy_rec[0][0]
        # 验证消息格式：STATE@...，第四个@后面是"Invalid move!"
        parts = msg.split("@")
        self.assertGreaterEqual(len(parts), 5, f"消息格式不正确: {msg}")
        self.assertEqual(parts[4], "Invalid move!", f"期望 Invalid move!，但收到: {parts[4]}")

    def test_undo(self):
        undo_btn = getattr(self.win, "undo_btn", None)
        self.assertIsNotNone(undo_btn, "没有找到 undo_btn")
        # 点击按钮
        QTest.mouseClick(undo_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        req = self.spy[0][0]
        self.assertEqual(req, "undo")
        # 获取信号中发送的数据
        msg = self.spy_rec[0][0]
        # 验证消息格式：STATE@...，第四个@后面是"Undo complete!"
        parts = msg.split("@")
        self.assertGreaterEqual(len(parts), 5, f"消息格式不正确: {msg}")
        self.assertEqual(parts[4], "Undo complete!", f"期望 Undo complete!，但收到: {parts[4]}")

    def test_invalid_reset(self):
        # 找到reset按钮
        reset_btn = getattr(self.win, "reset_btn", None)
        self.assertIsNotNone(reset_btn, "没有找到 reset_btn")
        # 点击按钮
        QTest.mouseClick(reset_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        self.assertEqual(len(self.spy), 0, f"spy非空: {self.spy}")

    def test_invalid_hint(self):
        """点击上箭头后验证收到后端的 Invalid move 消息"""
        # 找到上箭头按钮
        hint_btn = getattr(self.win, "hint_btn", None)
        self.assertIsNotNone(hint_btn, "没有找到 hint_btn")
        # 点击按钮
        QTest.mouseClick(hint_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        req = self.spy[0][0]
        self.assertEqual(req, "hint")
        self.assertEqual(self.spy_rec[0][0], "MSG@Hint generation failed")
        
    def test_valid_select(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "测试关卡2":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        req = self.spy[0][0]
        self.assertEqual(req, "select_level@测试关卡2")
        self.assertEqual(self.spy_rec[0][0], "STATE@0235023511441167#89#@0@0@Initialization complete!@None@None")
                
    def test_move(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "测试关卡2":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        rect = self.win.board_widget.rect_map['9']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        
        left_btn = getattr(self.win, "left_btn", None)
        self.assertIsNotNone(left_btn, "没有找到 left_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(left_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)

        req = self.spy[1][0]
        self.assertEqual(req, "move@9#Left")
        self.assertTrue(self.spy_rec[1][0].startswith("STATE@"))
        parts = self.spy_rec[1][0].split("@")
        self.assertEqual(parts[4], "Invalid move!")
        
        right_btn = getattr(self.win, "right_btn", None)
        self.assertIsNotNone(right_btn, "没有找到 right_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(right_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)

        req = self.spy[2][0]
        self.assertEqual(req, "move@9#Right")
        self.assertTrue(self.spy_rec[1][0].startswith("STATE@"))
        parts = self.spy_rec[2][0].split("@")
        self.assertEqual(parts[4], "Valid move!")
        
    def test_valid_reset(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "测试关卡2":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        rect = self.win.board_widget.rect_map['9']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        
        right_btn = getattr(self.win, "right_btn", None)
        self.assertIsNotNone(right_btn, "没有找到 right_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(right_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(1000)
        
        reset_btn = getattr(self.win, "reset_btn", None)
        self.assertIsNotNone(reset_btn, "没有找到 reset_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(reset_btn, Qt.LeftButton)
        req = self.spy[2][0]
        self.assertEqual(req, "select_level@测试关卡2")
        # 等待信号
        QTest.qWait(100)
        self.assertTrue(self.spy_rec[2][0].startswith("STATE@0235023511441167#89#"))
        QTest.qWait(1000)
           
    def test_valid_hint(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "测试关卡2":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        rect = self.win.board_widget.rect_map['9']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        
        hint_btn = getattr(self.win, "hint_btn", None)
        self.assertIsNotNone(hint_btn, "没有找到 hint_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(hint_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        req = self.spy[1][0]
        self.assertEqual(req, "hint")

        self.assertTrue(self.spy_rec[1][0].startswith("HINT@"))
        self.assertEqual(self.spy_rec[1][0], "HINT@39")
        
    def test_valid_random(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "随机挑战":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break

        req = self.spy[0][0]
        self.assertEqual(req, "random_level")
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@"))
        QTest.qWait(1000)
        
    def test_valid_random_reset(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "随机挑战":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break

        req = self.spy[0][0]
        self.assertEqual(req, "random_level")
        self.assertTrue(self.spy_rec[0][0].startswith("STATE@"))
        origin_board = self.spy_rec[0][0].split("@")[1]
        QTest.qWait(1000)
        
        reset_btn = getattr(self.win, "reset_btn", None)
        self.assertIsNotNone(reset_btn, "没有找到 reset_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(reset_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        req = self.spy[1][0]
        self.assertEqual(req, "random_level")
        self.assertTrue(self.spy_rec[1][0].startswith("STATE@"))
        now_board = self.spy_rec[1][0].split("@")[1]
        self.assertNotEqual(now_board, origin_board)
        QTest.qWait(1000)
        
    def test_success(self):
        level_btn = getattr(self.win, "level_btn")
        self.assertIsNotNone(level_btn, "没有找到 level_btn")
        QTest.qWait(200)
        # 点击按钮
        QTest.mouseClick(level_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(200)
        
        menu = self.win.level_menu
        self.assertTrue(menu.isVisible(), True)
        for act in menu.actions():
            if act.text() == "测试关卡":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break
        req = self.spy[0][0]
        self.assertEqual(req, "select_level@测试关卡")
        rect = self.win.board_widget.rect_map['1']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        
        down_btn = getattr(self.win, "down_btn", None)
        self.assertIsNotNone(down_btn, "没有找到 down_btn")
        # 点击按钮
        QTest.qWait(100)
        QTest.mouseClick(down_btn, Qt.LeftButton)
        req = self.spy[2][0]
        self.assertEqual(req, "move@1#Down")
        # 等待信号
        QTest.qWait(1000)
        self.assertEqual(self.spy_rec[2][0], "DONE")
        
        from PyQt5.QtWidgets import QMessageBox
        modal = QApplication.activeModalWidget()
        # 确认这个窗口确实是 QMessageBox
        if isinstance(modal, QMessageBox):
            yes_btn = modal.button(QMessageBox.Yes)
            # 以鼠标左键点击它
            QTest.mouseClick(yes_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(100)
        # print(self.spy_rec[3])
        self.assertTrue(self.win.level_menu.isVisible())
        QTest.qWait(1000)

if __name__ == "__main__":
    unittest.main()
