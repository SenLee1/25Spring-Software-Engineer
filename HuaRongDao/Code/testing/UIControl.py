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

    # def test_button_click(self):
    #     """Test button click functionality and observe GUI changes"""
    #     # print("test entered")
    #     # QTest.qWait(500)
    #     # self.assertTrue(self.win.dialog.isVisible(), "LevelDialog 应该已经弹出")
    #     # print("LevelDialog 已经弹出")

    #     select_btn = getattr(self.win, "level_btn", None)
    #     self.assertIsNotNone(select_btn, "没有在 GameWindow 中找到 level_btn")
    #     QTest.mouseClick(select_btn, Qt.LeftButton)
    #     QTest.qWait(1000)

    #     menu = self.win.level_menu
    #     self.assertTrue(menu.isVisible())
    #     self.assertGreaterEqual(len(menu.actions()), 1)
        
    #     # 2) 在菜单上点击第一个 action
    #     action = menu.actions()[1]
    #     # 把坐标转换到 menu 的 widget 坐标体系
    #     rect = menu.actionGeometry(action)                  # action 在 menu 中的局部矩形
    #     center_local = rect.center()                        # 局部中心点（QPoint）
    #     center_global = menu.mapToGlobal(center_local)      # 转成屏幕坐标
    #     pyautogui.click(center_global.x(), center_global.y())
    #     QTest.qWait(1000)

    #     # 找到并点击 Hint 按钮
    #     hint_btn = getattr(self.win, 'hint_btn', None)
    #     self.assertIsNotNone(hint_btn, "没有在 GameWindow 中找到 hint_btn")
    #     QTest.mouseClick(hint_btn, Qt.LeftButton)

    #     QTest.qWait(2000)
    #     rect = self.win.board_widget.rect_map['2']
    #     pt = self.win.board_widget.mapToGlobal(rect.center())
    #     pyautogui.click(pt.x(), pt.y())
    #     QTest.qWait(50)
    #     self.assertEqual(self.win.board_widget.selected_id, '2')

    #     QTest.qWait(2000)
        
    def test_button_click(self):
        """Test button click functionality and observe GUI changes"""
        # print("test entered")
        # QTest.qWait(500)
        # self.assertTrue(self.win.dialog.isVisible(), "LevelDialog 应该已经弹出")
        # print("LevelDialog 已经弹出")

        select_btn = getattr(self.win, "level_btn", None)
        self.assertIsNotNone(select_btn, "没有在 GameWindow 中找到 level_btn")
        QTest.mouseClick(select_btn, Qt.LeftButton)
        QTest.qWait(1000)

        menu = self.win.level_menu
        
        # 2) 在菜单上点击第一个 action
        for act in menu.actions():
            if act.text() == "随机关卡":
                rect = menu.actionGeometry(act)
                pt = menu.mapToGlobal(rect.center())
                pyautogui.click(pt.x(), pt.y())
                QTest.qWait(200)
                break

        reset_btn = getattr(self.win, "reset_btn", None)
        QTest.qWait(100)

        # 点击按钮
        QTest.mouseClick(reset_btn, Qt.LeftButton)
        # 等待信号
        QTest.qWait(1000)

        QTest.mouseClick(select_btn, Qt.LeftButton)
        QTest.qWait(1000)

        # 2) 在菜单上点击第一个 action
        action = menu.actions()[1]
        # 把坐标转换到 menu 的 widget 坐标体系
        rect = menu.actionGeometry(action)                  # action 在 menu 中的局部矩形
        center_local = rect.center()                        # 局部中心点（QPoint）
        center_global = menu.mapToGlobal(center_local)      # 转成屏幕坐标
        pyautogui.click(center_global.x(), center_global.y())
        QTest.qWait(1000)

        # 找到并点击 Hint 按钮
        hint_btn = getattr(self.win, 'hint_btn', None)
        QTest.mouseClick(hint_btn, Qt.LeftButton)
        QTest.qWait(1000)

        rect = self.win.board_widget.rect_map['9']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        btn = getattr(self.win, "right_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)

        hint_btn = getattr(self.win, 'hint_btn', None)
        QTest.mouseClick(hint_btn, Qt.LeftButton)
        QTest.qWait(3500)
        
        rect = self.win.board_widget.rect_map['8']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        btn = getattr(self.win, "right_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)
        
        rect = self.win.board_widget.rect_map['1']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        btn = getattr(self.win, "down_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)
        
        rect = self.win.board_widget.rect_map['4']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        btn = getattr(self.win, "left_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)
        
        btn = getattr(self.win, "left_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)

        rect = self.win.board_widget.rect_map['6']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        btn = getattr(self.win, "up_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)
        
        btn = getattr(self.win, "right_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)
        
        rect = self.win.board_widget.rect_map['8']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)
        
        btn = getattr(self.win, "up_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)

        btn = getattr(self.win, "up_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)

        rect = self.win.board_widget.rect_map['1']
        pt = self.win.board_widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        btn = getattr(self.win, "right_btn", None)
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(100)

        QTest.qWait(2000)


if __name__ == "__main__":
    unittest.main()
