import zmq
import time
import threading
import random
import os
import subprocess
import json

API_DICT = {
    "Zhangfei": "0",
    "Caocao": "1",
    "Machao": "2",
    "Huangzhong": "3",
    "Guanyu": "4",
    "Zhaoyun": "5",
    "Zu1": "6",
    "Zu2": "7",
    "Zu3": "8",
    "Zu4": "9"
}

class HuarongDaoGame:
    def __init__(self):
        self.levels = {
            "测试关卡": "24432673011501158##9",
            "测试关卡2": "0235023511441167#89#",
            "横刀立马": "01150115244327836##9",
            "指挥若定": "01150115644927832##3",
            "将拥曹营": "#11#0112035263574489",
            "齐头并进": "01120112678934453##5",
            "兵分三路": "61190112044237853##5",
            "雨声淅沥": "01160117244325#385#9",
            "左右布兵": "6117811902350235#44#",
            "桃花园中": "6117011203528359#44#",
            "测试样例": "9#82#112611530753044", 
        }
        self.board = ['#'] * 20
        self.history = []
        self.steps = 0
        self.start_time = None
        # 最高分记录：每个关卡对应最少步数和最短时间
        self.current_level = None
        self.high_scores = {level: {'steps': None, 'time': None} for level in self.levels}
        self.piece_sizes = {
            '1': (2, 2), '0': (1, 2), '2': (1, 2), '3': (1, 2), '5': (1, 2),
            '4': (2, 1), '6': (1, 1), '7': (1, 1), '8': (1, 1), '9': (1, 1)
        }

    def set_board(self, board_str):
        if len(board_str) != 20:
            return False, 'Invalid board string length'
        for ch in board_str:
            if ch != '#' and ch not in self.piece_sizes:
                return False, f'Invalid piece id: {ch}'
        self.board = list(board_str)
        self.history.clear()
        self.steps = 0
        self.start_time = time.time()
        # 判断是否是已知关卡
        self.current_level = next((name for name, s in self.levels.items() if s == board_str), None)
        return True, 'Initialization complete!'

    def get_board_str(self):
        return ''.join(self.board)

    def move_piece(self, piece, direction):
        if piece is None:
            return False, 'Invalid move!'
        if piece not in self.board:
            return False, 'Invalid move!'
        w, h = self.piece_sizes.get(piece, (1, 1))
        positions = [i for i, p in enumerate(self.board) if p == piece]
        rows = [pos // 4 for pos in positions]
        cols = [pos % 4 for pos in positions]
        min_r, min_c = min(rows), min(cols)
        dr, dc = 0, 0
        if direction == 'Up': dr = -1
        elif direction == 'Down': dr = 1
        elif direction == 'Left': dc = -1
        elif direction == 'Right': dc = 1
        else: return False, 'Invalid move!'
        new_r = min_r + dr
        new_c = min_c + dc
        if new_r < 0 or new_c < 0 or new_c + w > 4 or new_r + h > 5:
            return False, 'Invalid move!'
        if dr == -1:
            for c in range(min_c, min_c + w):
                if self.board[(min_r - 1) * 4 + c] not in ('#', piece): return False, 'Invalid move!'
        elif dr == 1:
            for c in range(min_c, min_c + w):
                if self.board[(min_r + h) * 4 + c] not in ('#', piece): return False, 'Invalid move!'
        elif dc == -1:
            for r in range(min_r, min_r + h):
                if self.board[r * 4 + (min_c - 1)] not in ('#', piece): return False, 'Invalid move!'
        elif dc == 1:
            for r in range(min_r, min_r + h):
                if self.board[r * 4 + (min_c + w)] not in ('#', piece): return False, 'Invalid move!'
        for pos in positions:
            self.board[pos] = '#'
        for rr in range(new_r, new_r + h):
            for cc in range(new_c, new_c + w):
                self.board[rr * 4 + cc] = piece
        return True, 'Valid move!'

    def undo(self):
        if self.history:
            self.board = self.history.pop()
            self.steps -= 1
        return True, 'Undo complete!'

    def is_solved(self):
        return self.board[17] == '1' and self.board[18] == '1'

    def get_state(self):
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        return {'board': self.get_board_str(), 'steps': self.steps, 'time': elapsed}

    def generate_random_board(self):
        positions = [None] * 10
        board = ['#'] * 20
        ids = list(self.piece_sizes.keys())
        random.shuffle(ids)
        for pid in ids:
            w, h = self.piece_sizes[pid]
            candidates = []
            for r in range(5 - h + 1):
                for c in range(4 - w + 1):
                    if pid == '1' and (r * 4 + c in (17, 18)):
                        continue  # avoid solving position
                    valid = True
                    for dr in range(h):
                        for dc in range(w):
                            idx = (r + dr) * 4 + (c + dc)
                            if board[idx] != '#':
                                valid = False
                    if valid:
                        candidates.append((r, c))
            if not candidates:
                return None
            r, c = random.choice(candidates)
            for dr in range(h):
                for dc in range(w):
                    board[(r + dr) * 4 + (c + dc)] = pid
        return ''.join(board)

class ZmqFrontendServer(threading.Thread):
    def __init__(self, address="tcp://*:5555"):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(address)
        self.game = HuarongDaoGame()
        self.use_api = False

    def _send_state(self, msg: str = ""):
        """统一发送当前 board/steps/time 以及可选的 INFO 消息"""
        board = self.game.get_board_str()
        steps = self.game.steps
        elapsed = int(time.time() - self.game.start_time) if self.game.start_time else 0
        if self.game.current_level == None:
            best_steps, best_time = None, None
        else :
            best_steps = self.game.high_scores[self.game.current_level]['steps']
            best_time = self.game.high_scores[self.game.current_level]['time']
        payload = f"STATE@{board}@{steps}@{elapsed}@{msg}@{best_steps}@{best_time}"
        self.socket.send_string(payload)
        print(f"sent {payload}")

    def _send_api(self, msg: str = ""):
        board = self.game.get_board_str()
        payload = f"{board}@{msg}"
        self.socket.send_string(payload)

    def handle_message(self, msg: str = ""):
        if msg == "use_api":
            self.use_api = True
            self.socket.send_string("api_confirm")
        elif msg == "get_levels":
            self.game.__init__()
            levels = ",".join(self.game.levels.keys())
            self.socket.send_string(f"LEVELS@{levels}")
        elif msg.startswith("select_level@"):
            lvl = msg.split("@", 1)[1]
            board_str = self.game.levels.get(lvl, "")
            ok, info = self.game.set_board(board_str)
            self._send_state(info)
        elif msg == "random_level":
            for _ in range(1000):
                candidate = self.game.generate_random_board()
                if candidate:
                    ok, info = self.game.set_board(candidate)
                    if self.game.is_solved():
                        continue
                    print(candidate)
                    self._send_state(info)
                    break
            else:
                self.socket.send_string("MSG@Failed to generate random level")
        elif msg.startswith("move@"):
            body = msg.split("@", 1)[1]
            piece, direction = body.split("#", 1)
            if piece in API_DICT.keys():
                self.use_api = True
                piece = API_DICT[piece]
            self.game.history.append(self.game.board.copy())
            ok, info = self.game.move_piece(piece, direction)
            if ok:
                self.game.steps += 1
            else:
                self.game.history.pop()
            if self.use_api:
                self._send_api(info)
                return
            # 如果刚刚解出
            if ok and self.game.is_solved():
                elapsed = int(time.time() - self.game.start_time)
                record = self.game.high_scores[self.game.current_level]
                better = record['steps'] is None or self.game.steps < record['steps'] or (
                    self.game.steps == record['steps'] and elapsed < record['time']
                )
                if better:
                    self.game.high_scores[self.game.current_level] = {'steps': self.game.steps, 'time': elapsed}
                self.socket.send_multipart([
                    f"DONE".encode()
                ])
            else:
                self._send_state(info)
        elif msg == "undo":
            ok, info = self.game.undo()
            if self.use_api:
                self._send_api(info)
            else:
                self._send_state(info)
        elif msg.startswith("set@"):
            board_str = msg.split("@", 1)[1]
            ok, info = self.game.set_board(board_str)
            self._send_api(info)
        elif msg == 'hint':
            try:
                with open("Development/main/Check_tool_template.xml", "r", encoding="utf-8") as f:
                    xml = f.read()
                board_str = self.game.get_board_str()
                board_lines = ["for (i : int[0, ROWS * COLS - 1]) board[i] = -1;\n\n  // Set board contents from string \"" + board_str + "\""]
                for i, ch in enumerate(board_str):
                    if ch == '#':
                        board_lines.append(f"  board[{i}] = -1;")
                    else:
                        board_lines.append(f"  board[{i}] = {ch};")
                board_lines.append("\n  // Assign positions")
                used = set()
                for idx, ch in enumerate(board_str):
                    if ch not in used and ch != '#':
                        board_lines.append(f"  positions[{int(ch)}] = {idx};  // Piece {ch}")
                        used.add(ch)
                board_lines.append("  main_check();")
                init_code = '\n'.join(board_lines)
                xml = xml.replace("CODE_TEMPLATE", init_code)
                with open("Development/main/Check_tool.xml", "w", encoding="utf-8") as f:
                    f.write(xml)

                cmd = ["verifyta", "-t1", "-f", "solution", "Check_tool.xml", "Check_tool.q"]
                try:
                    # 增加 timeout 参数（这里设为 30 秒，根据需要调整）
                    subprocess.run(cmd, cwd="Development/main", check=True, timeout=3)
                except subprocess.TimeoutExpired:
                    # 超时直接发失败消息并跳过后续处理
                    self.socket.send_string("MSG@Hint generation failed")
                    return
                with open("Development/main/solution-1", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                start_idx = end_idx = None
                for i in range(len(lines)-1, -1, -1):
                    if ';' in lines[i]:
                        if end_idx is None:
                            end_idx = i
                        elif start_idx is None:
                            start_idx = i
                            break
                if start_idx is not None and end_idx is not None and start_idx < end_idx:
                    hint_block = ''.join(lines[start_idx+1:end_idx])
                    parts = hint_block.split('.')
                    next_movement = parts[3].split(' ')[3]
                    # print(next_movement)
                    self.socket.send_string(f"HINT@{next_movement}")
                    return
                self.socket.send_string("MSG@Hint generation failed")
            except Exception as e:
                self.socket.send_string(f"MSG@Hint generation failed: {e}")
        elif msg == 'get_state':
            self._send_state()
        elif msg.startswith("set@"):
            # 直接按照老 API 初始化棋盘
            board_str = msg.split("@", 1)[1]
            ok, info = self.game.set_board(board_str)
            self._send_state(info)
        elif msg.startswith("move@"):
            # 老 API 中 move@name#dir，需要映射名称到数字 ID
            body = msg.split("@", 1)[1]
            if "#" in body:
                name, direction = body.split("#", 1)
                # 这里假设 game.move_piece 接受数字字符串作为 piece
                ok, info = self.game.move_piece(name, direction)
                if ok:
                    self.game.steps += 1
                # 返回当前棋盘 + 提示
                self._send_state(info)
            else:
                self._send_state("Invalid move format")
        elif msg == "undo":
            ok, info = self.game.undo()
            self._send_state(info)
        else:
            self.socket.send_string("MSG@Unknown command")

    def run(self):
        print("ZMQ server listening...")
        while True:
            try:
                msg = self.socket.recv_string()
                print(msg)
                self.handle_message(msg)
            except Exception as e:
                self.socket.send_string(f'error: {e}')

if __name__ == '__main__':
    server = ZmqFrontendServer()
    server.start()
    server.join()
# python Development\main\frontend.py
# python Development\main\backend.py
# python Development\main\Unittest_frontend.py
