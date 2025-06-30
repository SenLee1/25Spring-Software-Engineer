import zmq
import time
from PyQt5.QtCore import QThread, pyqtSignal

class ZmqThread(QThread):
    responseReceived = pyqtSignal(str)
    handshakeFailed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        self.testcase_path = "./Development/TestCase/testcase/testcase.txt"
        self.answer_path = "./Development/TestCase/answer/answer.txt"
        self.running = True

    def stop(self):
        self.running = False
        self.wait()

if __name__ == "__main__":
    zmq_thread = ZmqThread()

    # 1. 握手阶段
    try:
        zmq_thread.socket.send_string("use_api")
        if zmq_thread.socket.recv_string() != "api_confirm":
            zmq_thread.handshakeFailed.emit("Handshake failed: no api_confirm")
            exit(1)
    except zmq.ZMQError as e:
        zmq_thread.handshakeFailed.emit(f"Handshake error: {e}")
        exit(1)

    # 2. 读取 testcases 和 answers
    with open(zmq_thread.testcase_path, "r", encoding="utf-8") as f:
        test_lines = [line.strip() for line in f if line.strip()]
    with open(zmq_thread.answer_path, "r", encoding="utf-8") as f:
        answer_lines = [line.strip() for line in f if line.strip()]

    # 要求 answer_lines 刚好是 test_lines 行数的两倍
    if len(answer_lines) != 2 * len(test_lines):
        print(f"Answer file line count mismatch: expected {2*len(test_lines)}, got {len(answer_lines)}")
        exit(1)

    all_match = True
    answer_idx = 0

    # 3. 循环发送并接收，比对
    for msg in test_lines:
        if not zmq_thread.running:
            break

        # 3.1 发送请求
        zmq_thread.socket.send_string(msg)

        # 3.2 接收回复
        try:
            reply = zmq_thread.socket.recv_string()
        except zmq.ZMQError as e:
            print(f"<Error receiving reply: {e}>")
            all_match = False
            break

        # 3.3 分割 reply，并取出预期答案
        parts = reply.split("@", 1)
        expected_part1 = answer_lines[answer_idx]
        expected_part2 = answer_lines[answer_idx + 1]
        answer_idx += 2

        # 3.4 打印并通过信号传递
        print(f"Sent: {msg}")
        print(f"Recv parts: '{parts[0]}', '{parts[1]}'")
        zmq_thread.responseReceived.emit(f"Sent: {msg}   |   Recv: {reply}")

        # 3.5 比对
        if parts[0] != expected_part1 or parts[1] != expected_part2:
            print(f"❌ Mismatch on testcase '{msg}':")
            print(f"    got   → '{parts[0]}' | '{parts[1]}'")
            print(f"    want  → '{expected_part1}' | '{expected_part2}'")
            all_match = False
            break

        # 3.6 等待 1 秒
        time.sleep(1)

    # 4. 最后输出结果
    if all_match:
        print("✅ PASSED")
    else:
        print("❌ FAILED")

# python Development\main\unittest.py
# python Development\main\backend.py