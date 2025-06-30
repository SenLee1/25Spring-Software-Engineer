# test_frontend_ui.py

import sys
import unittest
import pyautogui

from PyQt5.QtWidgets import QApplication, QPushButton, QDialog
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtCore import Qt, QPoint

# 导入你原始的 frontend 脚本中所有顶层类
from frontend import ZmqThread, BoardWidget, GameWindow

class TestBoardWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.widget = BoardWidget()
        # 设置固定大小使得 paintEvent 能正确计算 rect_map
        self.widget.resize(200, 250)
        self.widget.show()
        QTest.qWait(100)  # 等待初次绘制

    def tearDown(self):
        self.widget.close()

    def test_get_piece_span(self):
        """测试 get_piece_span 对不同 pid 的返回值"""
        self.assertEqual(self.widget.get_piece_span('1'), (2, 2))
        for pid in ['0', '2', '3', '5']:
            self.assertEqual(self.widget.get_piece_span(pid), (1, 2))
        self.assertEqual(self.widget.get_piece_span('4'), (2, 1))
        # 其余 pid（如 '6','7','8','9','#'）均为 1x1
        for pid in ['6', '7', '8', '9', '#']:
            self.assertEqual(self.widget.get_piece_span(pid), (1, 1))

    def test_paintEvent_wide(self):
        """
        当 widget 宽/高 > 4/5 时，应进入宽屏分支：h=height, w=int(h*0.8)，
        棋盘矩形会左右居中，导致 rect_map 中的 x 坐标 > 0。
        """
        # 1. 先让 widget 尺寸为 1000×500（宽屏：1000/500 = 2 > 0.8）
        self.widget.resize(1000, 500)
        # 强制触发一次重绘
        self.widget.update()
        QTest.qWait(100)

        # 2. 把棋盘放一个标记棋子，放在 index=0 的位置
        board = ['#'] * 20
        board[0] = '9'     # 假设用 '9' 表示一个 test-pid
        self.widget.board = board

        # 3. 再次 update，让 paintEvent 生效并更新 rect_map
        self.widget.update()
        QTest.qWait(100)

        # 4. 此时宽屏分支应该得到 board_rect.width ≈ 400，且左右各留 (1000-400)/2=300
        #    rect_map['9'] 的 x() 值应接近 300（可以容忍几个像素整型误差），这里只验证 x>0 即可
        self.assertIn('9', self.widget.rect_map)
        rect9 = self.widget.rect_map['9']
        # 只要 x() 明显大于 0，就表明进入了左右居中分支
        self.assertTrue(rect9.x() > 0, 
                        f"宽屏场景下 rect9.x() 应 > 0，但实际是 {rect9.x()}")

        # 也可以进一步校验 x() 约等于 300 左右：例如 |rect9.x() - 300| <= 2
        expected_x = int((1000 - int(500 * (4/5))) / 2)
        self.assertAlmostEqual(rect9.x(), expected_x, delta=3,
                               msg=f"宽屏模式下左边距应 ~{expected_x}，实际 {rect9.x()}")
        QTest.qWait(1000)
        
    def test_paintEvent_tall(self):
        """
        当 widget 宽/高 ≤ 4/5 时，应进入高屏分支：w=width, h=int(w/0.8)，
        棋盘矩形会上下居中，rect_map 中的 y 坐标 > 0。
        """
        # 1. 先让 widget 尺寸为 400×1000（高屏：400/1000 = 0.4 ≤ 0.8）
        self.widget.resize(400, 1000)
        self.widget.update()
        QTest.qWait(100)

        # 2. 把棋盘放一个标记棋子，放在 index=0 的位置
        board = ['#'] * 20
        board[0] = '7'     # 假设用 '7' 表示一个 test-pid
        self.widget.board = board

        # 3. 再次 update，让 paintEvent 生效并更新 rect_map
        self.widget.update()
        QTest.qWait(100)

        # 4. 此时高屏分支应得到 board_rect.height ≈ 500，且上下各留 (1000-500)/2=250
        #    rect_map['7'] 的 y() 值应接近 250。先断言 y() > 0。
        self.assertIn('7', self.widget.rect_map)
        rect7 = self.widget.rect_map['7']
        self.assertTrue(rect7.y() > 0,
                        f"高屏场景下 rect7.y() 应 > 0，但实际是 {rect7.y()}")

        # 也可进一步校验 y() 约等于 250 左右：例如 |rect7.y() - 250| ≤ 3
        expected_y = int((1000 - int(400 / (4/5))) / 2)
        self.assertAlmostEqual(rect7.y(), expected_y, delta=3,
                               msg=f"高屏模式下上边距应 ~{expected_y}，实际 {rect7.y()}")
        QTest.qWait(1000)

    def test_paintEvent_with_valid_pixmap(self):
        """
        测试当 piece_pixmaps 中的 pixmap 有效时，是否走 pixmap 分支
        """
        board = ['#'] * 20
        board[0] = '8'
        self.widget.board = board
        # 调整尺寸以便绘制
        self.widget.resize(200, 250)
        self.widget.update()
        QTest.qWait(100)
        # pixmap 分支应当执行：rect_map 中应该存在 '8'
        self.assertIn('8', self.widget.rect_map)
        rect = self.widget.rect_map['8']
        # 检查 rect 宽高与 span 计算一致（span 为默认 1×1）
        self.assertTrue(rect.width() > 0 and rect.height() > 0,
                        f"pixmap 分支绘制时，rect 应有正宽高，实际 {rect.size()}。")
        QTest.qWait(1000)

    def test_paintEvent_with_null_pixmap(self):
        """
        测试当 piece_pixmaps 中的 pixmap 为空或不含 pid 时，是否走 drawRect 分支
        """
        # 确保 '9' 对应的 pixmap 为空或不存在
        self.widget.piece_pixmaps = {}  # 这是一个 isNull()==True 的 pixmap
        board = ['#'] * 20
        board[0] = '9'
        self.widget.board = board
        self.widget.resize(200, 250)
        self.widget.update()
        QTest.qWait(100)
        # else 分支走 drawRect：rect_map 中应该存在 '9'
        self.assertIn('9', self.widget.rect_map)
        rect = self.widget.rect_map['9']
        # 确认 rect 有效
        self.assertTrue(rect.width() > 0 and rect.height() > 0,
                        f"drawRect 分支绘制时，rect 应有正宽高，实际 {rect.size()}。")
        QTest.qWait(1000)
    def test_selected_highlight(self):
        """
        测试当 pid == selected_id 时，中心像素应呈现黄与蓝的混合色（R/G 均明显大于 B）。
        """
        from PyQt5.QtGui import QColor
        # 使用 pid '0'，其默认颜色为 (150,150,255) 蓝色调
        pid = '0'
        # 设置 board，使 idx=0 为 pid '0'
        board = ['#'] * 20
        board[0] = pid
        self.widget.board = board
        # 选中 '0'
        self.widget.selected_id = pid
        # 使 widget 大小固定，触发绘制
        self.widget.resize(200, 250)
        self.widget.update()
        QTest.qWait(100)

        # 截图 widget
        pix = self.widget.grab()
        img = pix.toImage()
        rect = self.widget.rect_map[pid]
        cx = rect.center().x()
        cy = rect.center().y()
        c = QColor(img.pixel(cx, cy))
        # 选中时，应当 R 与 G 均高于 B
        self.assertTrue(c.red() > c.blue() and c.green() > c.blue(),
                        f"选中情况下，中心像素 R/G 应明显 > B，实际 R={c.red()}, G={c.green()}, B={c.blue()}")
        QTest.qWait(1000)

    def test_show_and_clear_hint(self):
        """测试 show_hint 与定时器清除 hint_info"""
        # 初始时 hint_info 应为 None
        pid = '2'
        # 设置 board，使 idx=0 为 pid '2'
        board = ['#'] * 20
        board[0] = pid
        self.widget.board = board
        # 选中 '2'
        self.widget.selected_id = pid
        self.assertIsNone(self.widget.hint_info)
        # 调用 show_hint 设定 pid='2', direction=3
        self.widget.show_hint('2', 0)
        self.assertEqual(self.widget.hint_info, ('2', 0))
        QTest.qWait(1000)
        self.widget.show_hint('2', 1)
        self.assertEqual(self.widget.hint_info, ('2', 1))
        QTest.qWait(1000)
        self.widget.show_hint('2', 2)
        self.assertEqual(self.widget.hint_info, ('2', 2))
        QTest.qWait(1000)
        self.widget.show_hint('2', 3)
        self.assertEqual(self.widget.hint_info, ('2', 3))
        # 等待超过 3000ms，定时器应当触发 clear_hint
        QTest.qWait(3500)
        self.assertIsNone(self.widget.hint_info)
        
    def test_mousePressEvent_clicked_inside_piece(self):
        board = ['#'] * 20
        board[1] = '3'
        self.widget.board = board
        self.widget.update()
        QTest.qWait(500)

        # 把 selected_id 先设为 'X'（假设和 '3' 不同）
        self.widget.selected_id = 'X'

        # 用 QSignalSpy 监听 pieceSelected
        spy = QSignalSpy(self.widget.pieceSelected)

        # 点击'3'
        rect = self.widget.rect_map['3']
        pt = self.widget.mapToGlobal(rect.center())
        pyautogui.click(pt.x(), pt.y())
        QTest.qWait(50)

        # selected_id 应被修改
        self.assertEqual(self.widget.selected_id, '3',
                         f"点击应改变 selected_id，应该是 '3'，但实际是 {self.widget.selected_id}")

        # 信号应被发射
        self.assertNotEqual(len(spy), 0,
                         f"点击空白处应发射 pieceSelected 信号，但实际发射了 {len(spy)} 次")
        QTest.qWait(1000)

    def test_mousePressEvent_clicked_outside_any_piece(self):
        # 1. 准备棋盘：这里只放置一个 pid='3' 在 idx=1（行 0 列 1），
        #    但点击点放在完全不重叠的地方（例如窗口左上角最左侧或最底部某个空白区域）。
        board = ['#'] * 20
        board[1] = '3'
        self.widget.board = board
        self.widget.update()
        QTest.qWait(100)

        # 2. 把 selected_id 先设为 'X'（假设和 '3' 不同）
        self.widget.selected_id = 'X'

        # 3. 用 QSignalSpy 监听 pieceSelected
        spy = QSignalSpy(self.widget.pieceSelected)

        # 4. 找一个绝对不会落在任何 rect_map 中的点，比如 (0, 0) 左上角（
        #    rect_map 中的棋子都在绘制区域里，(0,0) 有很大概率是“棋盘区域以外”的坐标）
        outside_point = QPoint(0, 0)
        QTest.mouseClick(self.widget, Qt.LeftButton, pos=outside_point)
        QTest.qWait(50)

        # 5. selected_id 不应被修改
        self.assertEqual(self.widget.selected_id, 'X',
                         f"点击空白处不应改变 selected_id，应该仍是 'X'，但实际是 {self.widget.selected_id}")

        # 6. 信号不应被发射
        self.assertEqual(len(spy), 0,
                         f"点击空白处不应发射 pieceSelected 信号，但实际发射了 {len(spy)} 次")

class TestGameWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        # 创建 GameWindow 实例并显示
        self.win = GameWindow()
        self.win.show()
        QTest.qWait(100)
        # 监听 zmq.request 信号
        self.spy_req = QSignalSpy(self.win.zmq.request)

    def tearDown(self):
        self.win.close()

    def test_on_level_selected_with_name(self):
        """传入具体关卡名，应调用 set_level 并 emit select_level@name"""
        # 模拟 _on_level_selected
        self.win._on_level_selected("测试关卡2")
        QTest.qWait(50)
        # 应当设置 current_level
        self.assertEqual(self.win.current_level, "测试关卡2")
        # 应 emit select_level@测试关卡2
        self.assertTrue(any(str(call[0]) == "select_level@测试关卡2" for call in self.spy_req),
                        f"应当 emit select_level@测试关卡2，但实际 emits={self.spy_req}")

    def test_on_level_selected_random(self):
        """传入 None，应调用 set_random_level 并 emit random_level"""
        self.win._on_level_selected(None)
        QTest.qWait(50)
        self.assertEqual(self.win.current_level, "Random")
        self.assertTrue(any(str(call[0]) == "random_level" for call in self.spy_req),
                        f"应当 emit random_level，但实际 emits={self.spy_req}")

    def test_reset_game_with_empty_game(self):
        self.win.reset_game()
        QTest.qWait(50)
        # reset_game 应当 emit select_level@LevelX
        self.assertFalse(any(str(call[0]) for call in self.spy_req),
                        f"reset_game 不应 emit")

    def test_reset_game_with_named_level(self):
        """当 current_level 为非 None 且非默认 None 时，reset_game 调用 set_level"""
        self.win.current_level = "LevelX"
        self.win.reset_game()
        QTest.qWait(50)
        # reset_game 应当 emit select_level@LevelX
        self.assertTrue(any(str(call[0]) == "select_level@LevelX" for call in self.spy_req),
                        f"reset_game 应 emit select_level@LevelX，但 emits={self.spy_req}")

    def test_reset_game_with_random(self):
        """当 current_level 为 "Random" 时，由于上层if优先，会调用 set_level("Random")，emit select_level@Random"""
        self.win.current_level = "Random"
        self.win.reset_game()
        QTest.qWait(50)
        # 根据代码逻辑，应当 emit select_level@Random
        self.assertTrue(any(str(call[0]) == "random_level" for call in self.spy_req),
                        f"reset_game(Random) 应 emit random_level，但 emits={self.spy_req}")

    def test_on_response_LEVELS(self):
        """收到 LEVELS@a,b,c，应设置 levels_list"""
        msg = "LEVELS@A,B,C"
        self.win.on_response(msg)
        self.assertEqual(self.win.levels_list, ["A", "B", "C"] )

    def test_on_response_MSG(self):
        """收到 MSG@text，应更新 info_label"""
        msg = "MSG@hello world"
        self.win.on_response(msg)
        self.assertEqual(self.win.info_label.text(), "hello world")

    def test_on_response_HINT(self):
        """收到 HINT@23，应调用 board_widget.show_hint('3',2)"""
        msg = "HINT@23"
        # 清除原来的 hint_info
        self.win.board_widget.hint_info = None
        self.win.on_response(msg)
        QTest.qWait(10)
        self.assertEqual(self.win.board_widget.hint_info, ('3', 2))

    def test_on_response_STATE(self):
        """收到 STATE@..., 验证多个 label 和 board 更新"""
        # 构造测试数据
        board_str = ''.join(str(i%10) for i in range(20))
        steps_str = "5"
        time_str = "10"
        info = "InfoMsg"
        best_steps = "7"
        best_time = "15"
        msg = f"STATE@{board_str}@{steps_str}@{time_str}@{info}@{best_steps}@{best_time}"
        self.win.on_response(msg)
        QTest.qWait(50)
        # board_widget.board 应与 board_str 一致
        self.assertEqual(self.win.board_widget.board, list(board_str))
        # 步数与时间
        self.assertIn("Steps: 5", self.win.step_label.text())
        self.assertIn("Time: 10s", self.win.timer_label.text())
        # 记录
        self.assertIn("Best: 15 s / 7 steps", self.win.record_label.text())
        # info_label
        self.assertEqual(self.win.info_label.text(), "InfoMsg")

    def test_on_response_STATE_without_record(self):
        """收到 STATE@..., 验证多个 label 和 board 更新"""
        # 构造测试数据
        board_str = ''.join(str(i%10) for i in range(20))
        steps_str = "5"
        time_str = "10"
        info = "InfoMsg"
        best_steps = "None"
        best_time = "None"
        msg = f"STATE@{board_str}@{steps_str}@{time_str}@{info}@{best_steps}@{best_time}"
        self.win.on_response(msg)
        QTest.qWait(50)
        # board_widget.board 应与 board_str 一致
        self.assertEqual(self.win.board_widget.board, list(board_str))
        # 步数与时间
        self.assertIn("Steps: 5", self.win.step_label.text())
        self.assertIn("Time: 10s", self.win.timer_label.text())
        # 记录
        self.assertIn("Best: ∞ s / ∞ steps", self.win.record_label.text())
        # info_label
        self.assertEqual(self.win.info_label.text(), "InfoMsg")

    def test_on_response_DONE(self):
        self.win.current_level = "Lvl2"
        from PyQt5.QtWidgets import QMessageBox
        original = QMessageBox.question
        # 强制返回 Yes
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.Yes
        try:
            self.win.on_response("DONE")
            QTest.qWait(50)
            # reset_game -> emit select_level@Lvl2
            self.assertTrue(any(str(call[0]) == "select_level@Lvl2" for call in self.spy_req))
            # 同时 show_level_menu 会使 level_menu 可见
            self.assertTrue(self.win.level_menu.isVisible())
        finally:
            QMessageBox.question = original

if __name__ == "__main__":
    unittest.main()
