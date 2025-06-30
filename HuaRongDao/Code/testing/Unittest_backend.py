import unittest
import time
import zmq
import random
import os
import unittest.mock

# 假设上述脚本保存在 huarongdao_game.py 文件中
from backend import HuarongDaoGame, ZmqFrontendServer

class TestHuarongDaoGame(unittest.TestCase):
    def setUp(self):
        self.game = HuarongDaoGame()

    def test_set_board_invalid_length(self):
        """长度不为20时应返回 False 和错误信息"""
        ok, msg = self.game.set_board("short")
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid board string length')

    def test_set_board_invalid_piece(self):
        """含有不在 piece_sizes 中的字符时应返回 False"""
        board = '#' * 19 + 'X'
        ok, msg = self.game.set_board(board)
        self.assertFalse(ok)
        self.assertIn('Invalid piece id: X', msg)

    def test_set_board_valid(self):
        """使用已知关卡字符串初始化应成功"""
        sample = self.game.levels['测试关卡']
        ok, msg = self.game.set_board(sample)
        self.assertTrue(ok)
        self.assertEqual(msg, 'Initialization complete!')
        self.assertEqual(self.game.get_board_str(), sample)
        self.assertIsNotNone(self.game.start_time)
        self.assertEqual(self.game.current_level, '测试关卡')
        sample = "#" * 20
        ok, msg = self.game.set_board(sample)
        self.assertTrue(ok)
        self.assertEqual(msg, 'Initialization complete!')
        self.assertEqual(self.game.get_board_str(), sample)
        self.assertIsNotNone(self.game.start_time)
        self.assertEqual(self.game.current_level, None)
        

    def test_move_piece_invalid_inputs(self):
        """piece 为 None 或不在 board 中时均应返回 False"""
        ok, msg = self.game.move_piece(None, 'Up')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')
        ok, msg = self.game.move_piece('9', 'Down')  # 初始 board 全为 '#'
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')

    def test_move_piece_invalid_direction(self):
        """非法方向时应返回 False"""
        sample = self.game.levels['测试关卡']
        self.game.set_board(sample)
        piece = self.game.board[0]
        ok, msg = self.game.move_piece(piece, 'Diagonal')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')

    def test_move_piece_all_direction_blocked(self):
        sample = self.game.levels['测试关卡2']
        self.game.set_board(sample)
        # Blocked in all direction
        piece = '6'
        ok, msg = self.game.move_piece(piece, 'Up')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')
        ok, msg = self.game.move_piece(piece, 'Down')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')
        ok, msg = self.game.move_piece(piece, 'Left')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')
        ok, msg = self.game.move_piece(piece, 'Right')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')
        # Out of the bound
        ok, msg = self.game.move_piece('1', 'Left')
        self.assertFalse(ok)
        self.assertEqual(msg, 'Invalid move!')

    def test_move_piece_valid(self):
        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        ok, msg = self.game.move_piece('6', 'Up')
        self.assertTrue(ok)
        self.assertEqual(msg, 'Valid move!')
        new_board = self.game.get_board_str()
        self.assertEqual(new_board[1], '6')

        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        ok, msg = self.game.move_piece('6', 'Down')
        self.assertTrue(ok)
        self.assertEqual(msg, 'Valid move!')
        new_board = self.game.get_board_str()
        self.assertEqual(new_board[9], '6')
        
        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        ok, msg = self.game.move_piece('6', 'Left')
        self.assertTrue(ok)
        self.assertEqual(msg, 'Valid move!')
        new_board = self.game.get_board_str()
        self.assertEqual(new_board[4], '6')
        
        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        ok, msg = self.game.move_piece('6', 'Right')
        self.assertTrue(ok)
        self.assertEqual(msg, 'Valid move!')
        new_board = self.game.get_board_str()
        self.assertEqual(new_board[6], '6')
    
    def test_undo_empty(self):
        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        ok, msg = self.game.undo()
        self.assertTrue(ok)
        self.assertEqual(msg, 'Undo complete!')
        new_board = self.game.get_board_str()
        self.assertEqual(new_board[5], '6')

    def test_undo(self):
        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        self.game.history.append(self.game.board.copy())
        ok, info = self.game.move_piece('6', "Right")
        ok, msg = self.game.undo()
        self.assertTrue(ok)
        self.assertEqual(msg, 'Undo complete!')
        new_board = self.game.get_board_str()
        self.assertEqual(new_board[5], '6')
    
    def test_get_state_init(self):
        state = self.game.get_state()
        self.assertEqual(state['board'], self.game.get_board_str())
        self.assertEqual(state['steps'], self.game.steps)
        self.assertEqual(state['time'], 0)

    def test_get_state(self):
        board = '#' * 5 + '6' + '#' * 14
        self.game.set_board(board)
        time.sleep(1)
        state = self.game.get_state()
        self.assertEqual(state['board'], self.game.get_board_str())
        self.assertEqual(state['steps'], self.game.steps)
        self.assertNotEqual(state['time'], 0)

    def test_generate_random_board_invalid(self):
        bg = HuarongDaoGame()
        bg.piece_sizes = {'1': (4, 4), "2": (4, 4)}
        result = bg.generate_random_board()
        self.assertIsNone(result, "尺寸过大时应该返回 None")

    @unittest.mock.patch('random.choice', return_value=(0, 0))
    def test_successful_random(self, mock_choice):
        bg = HuarongDaoGame()
        bg.piece_sizes = {'1' : (2, 2)}

        with unittest.mock.patch.object(random, 'shuffle', lambda x: None):
            board_str = bg.generate_random_board()

        expected = '11' + '#' * 2 + '11' + '#' * 14
        self.assertEqual(board_str, expected, "2×2 棋子被放到 (0,0) 的情况")

class TestZmqFrontendServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 使用 5556 端口启动服务器，避免与真实应用冲突
        cls.server = ZmqFrontendServer(address="tcp://127.0.0.1:5556")
        cls.server.daemon = True
        cls.server.start()
        time.sleep(0.1)
        cls.context = zmq.Context()
        cls.socket = cls.context.socket(zmq.REQ)
        cls.socket.connect("tcp://127.0.0.1:5556")

    @classmethod
    def tearDownClass(cls):
        cls.socket.close()
        cls.context.term()
        # 对于无限循环的服务器线程，直接结束进程或让测试结束即可

    def test_use_api(self):
        self.socket.send_string("use_api")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "api_confirm")

    def test_abandon_api(self):
        self.socket.send_string("abandon_api")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "api_abandon")

    def test_get_levels(self):
        self.socket.send_string("get_levels")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("LEVELS@"))
        parts = reply.split("@", 1)[1].split(",")
        self.assertIn("测试关卡", parts)

    def test_send_state_with_record(self):
        self.server.game.piece_sizes = {
            '1': (2, 2), '0': (1, 2), '2': (1, 2), '3': (1, 2), '5': (1, 2),
            '4': (2, 1), '6': (1, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)
        }
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("move@1#Down")
        reply = self.socket.recv_string()
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("STATE@"))
        fields = reply.split("@")
        # STATE, board, steps, elapsed, info, best_steps, best_time
        self.assertEqual(fields[0], "STATE")
        self.assertNotEqual(fields[5], "None")
        self.assertEqual(fields[4], "Initialization complete!")

    
    def test_send_state_with_none_current(self):
        self.socket.send_string("random_level")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("STATE@"))
        fields = reply.split("@")
        # STATE, board, steps, elapsed, info, best_steps, best_time
        self.assertEqual(fields[0], "STATE")
        self.assertEqual(fields[3], '0')
        self.assertEqual(fields[5], 'None')
        self.assertEqual(fields[4], "Initialization complete!")

    def test_select(self):
        self.server.game.piece_sizes = {
            '1': (2, 2), '0': (1, 2), '2': (1, 2), '3': (1, 2), '5': (1, 2),
            '4': (2, 1), '6': (1, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)
        }
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("move@1#Down")
        reply = self.socket.recv_string()
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("STATE@"))
        fields = reply.split("@")
        # STATE, board, steps, elapsed, info, best_steps, best_time
        self.assertEqual(fields[0], "STATE")
        self.assertNotEqual(fields[5], "None")
        self.assertEqual(fields[4], "Initialization complete!")

    def test_random_solved(self):
        self.server.game.piece_sizes = {'1': (4, 5)}
        self.socket.send_string("random_level")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("MSG@"))
        fields = reply.split("@")
        # STATE, board, steps, elapsed, info, best_steps, best_time
        self.assertEqual(fields[1], "Failed to generate random level")

    def test_random_failure(self):
        self.server.game.piece_sizes = {'1': (6, 6)}
        self.socket.send_string("random_level")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("MSG@"))
        fields = reply.split("@")
        # STATE, board, steps, elapsed, info, best_steps, best_time
        self.assertEqual(fields[1], "Failed to generate random level")
    
    def test_random_success(self):
        self.server.game.piece_sizes = {'2': (4, 5)}
        self.socket.send_string("random_level")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("STATE@"))
        fields = reply.split("@")
        # STATE, board, steps, elapsed, info, best_steps, best_time
        self.assertEqual(fields[1], "2" * 20)

        
    def test_api_move(self):
        self.socket.send_string("use_api")
        reply = self.socket.recv_string()
        self.server.game.piece_sizes = {
            '1': (2, 2), '0': (1, 2), '2': (1, 2), '3': (1, 2), '5': (1, 2),
            '4': (2, 1), '6': (1, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)
        }
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("move@Caocao#Up")
        reply = self.socket.recv_string()
        fields = reply.split("@")
        self.assertEqual(len(self.server.game.history), 0)
        self.assertEqual(fields[0], "24432673011501158##9")
        self.assertEqual(fields[1], "Invalid move!")

    def test_normal_move(self):
        self.socket.send_string("abandon_api")
        reply = self.socket.recv_string()
        self.server.game.piece_sizes = {
            '1': (2, 2), '0': (1, 2), '2': (1, 2), '3': (1, 2), '5': (1, 2),
            '4': (2, 1), '6': (1, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)
        }
        self.socket.send_string("select_level@测试关卡2")
        reply = self.socket.recv_string()
        self.socket.send_string("move@9#Right")
        # print(self.server.use_api)
        reply = self.socket.recv_string()
        fields = reply.split("@")
        self.assertEqual(self.server.game.steps, 1)
        self.assertEqual(fields[1], "0235023511441167#8#9")

    def test_UI_move_and_solve(self):
        self.socket.send_string("abandon_api")
        reply = self.socket.recv_string()
        self.server.game.piece_sizes = {
            '1': (2, 2), '0': (1, 2), '2': (1, 2), '3': (1, 2), '5': (1, 2),
            '4': (2, 1), '6': (1, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)
        }
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("move@1#Down")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "DONE")
        self.assertIsNotNone(self.server.game.high_scores["测试关卡"]["steps"])
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("move@9#Left")
        reply = self.socket.recv_string()
        self.socket.send_string("move@9#Right")
        reply = self.socket.recv_string()
        self.socket.send_string("move@1#Down")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "DONE")
        self.assertLess(self.server.game.high_scores["测试关卡"]["time"], self.server.game.steps)
        
    def test_api_undo(self):
        self.socket.send_string("use_api")
        reply = self.socket.recv_string()
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("undo")
        reply = self.socket.recv_string()
        fields = reply.split("@")
        self.assertEqual(fields[0], "24432673011501158##9")
        self.assertEqual(fields[1], "Undo complete!")

    def test_undo(self):
        self.socket.send_string("abandon_api")
        reply = self.socket.recv_string()
        self.socket.send_string("select_level@测试关卡")
        reply = self.socket.recv_string()
        self.socket.send_string("undo")
        reply = self.socket.recv_string()
        fields = reply.split("@")
        self.assertEqual(fields[1], "24432673011501158##9")
        self.assertEqual(fields[4], "Undo complete!")

    def test_set(self):
        self.socket.send_string("set@24432673011501158##9")
        reply = self.socket.recv_string()
        fields = reply.split("@")
        self.assertEqual(fields[0], "24432673011501158##9")
        self.assertEqual(fields[1], "Initialization complete!")

    def test_hint_valid(self):
        self.socket.send_string("select_level@测试关卡2")
        reply = self.socket.recv_string()
        self.socket.send_string("hint")
        reply = self.socket.recv_string()
        fields = reply.split("@")
        self.assertEqual(fields[0], "HINT")

    def test_hint_overtime(self):
        self.socket.send_string("select_level@横刀立马")
        reply = self.socket.recv_string()
        self.socket.send_string("hint")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "MSG@Hint generation failed")

    def test_hint_empty(self):
        self.socket.send_string("hint")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "MSG@Hint generation failed")
    
    def test_hint_fail(self):
        # 输入无效 hint 环境，服务器应该返回 MSG@Hint generation failed
        q_path = r"D:\_Workspace\SE\Team8\HuaRongDao\Development\main\Check_tool.q"
        temp_path = r"D:\_Workspace\SE\Team8\HuaRongDao\Development\main\Check_tool_temp.q"
        if os.path.exists(q_path):
            os.rename(q_path, temp_path)
        try:
            self.socket.send_string("hint")
            reply = self.socket.recv_string()
            self.assertTrue(reply.startswith("MSG@Hint generation failed"))
        finally:
            # 恢复文件名
            if os.path.exists(temp_path):
                os.rename(temp_path, q_path)

    def test_get_state_server(self):
        self.socket.send_string("get_state")
        reply = self.socket.recv_string()
        self.assertTrue(reply.startswith("STATE@"))
        
    def test_exception(self):
        self.socket.send_string("OnSeaTechUniversity")
        reply = self.socket.recv_string()
        self.assertEqual(reply, "MSG@Unknown command")

if __name__ == '__main__':
    unittest.main()
