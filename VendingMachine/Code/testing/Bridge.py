from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from threading import Thread
from queue import Queue
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
from UIbridge import UIFeedbackBridge

class FakeZmqHandler:
    def __init__(self, ui, vm, ui_bridge):
        self.queue = Queue()
        self.ui = ui
        self.vm = vm
        self.ui_bridge = ui_bridge
        self.running = True
        self.thread = Thread(target=self.loop, daemon=True)
        self.thread.start()

    def sendMsg(self, msg):
        self.queue.put(msg)

    def stop(self):
        self.running = False

    def loop(self):
        while self.running:
            try:
                msg = self.queue.get(timeout=0.01)
                self.handle_message(msg)
            except:
                continue

    def handle_message(self, msg):
        if msg.startswith("log_in"):
            pwd = msg.split("@")[1]
            if self.vm.verify_admin(pwd):
                self.ui_bridge.update_ui(lambda: self.ui.login_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.user_status_label.setText("登录失败"))

        elif msg.startswith("add_product"):
            idx = int(msg.split("@")[1])
            if self.ui.state and self.vm.restock_product(idx):
                self.ui_bridge.update_ui(lambda: self.ui.add_product_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.admin_failed())

        elif msg.startswith("add_coin"):
            val = float(msg.split("@")[1])
            if self.ui.state and self.vm.refill_coin(val):
                self.ui_bridge.update_ui(lambda: self.ui.add_coin_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.admin_failed())

        elif msg.startswith("add_bill"):
            val = int(msg.split("@")[1])
            if self.ui.state and self.vm.refill_coin(val):
                self.ui_bridge.update_ui(lambda: self.ui.add_bill_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.admin_failed())

        elif msg.startswith("remove_coin"):
            val = float(msg.split("@")[1])
            if self.ui.state and self.vm.withdraw_coin(val):
                self.ui_bridge.update_ui(lambda: self.ui.remove_money_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.admin_failed())
        
        elif msg.startswith("remove_bill"):
            val = int(msg.split("@")[1])
            if self.ui.state and self.vm.withdraw_coin(val):
                self.ui_bridge.update_ui(lambda: self.ui.remove_money_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.admin_failed())

        elif msg.startswith("log_out"):
            if self.ui.state:
                self.ui_bridge.update_ui(lambda: self.ui.logout_succeeded())

        elif msg.startswith("insert_coin"):
            coin = float(msg.split("@")[1])
            if not self.ui.state:
                self.vm.insert_coin(coin)
                self.ui_bridge.update_ui(lambda: self.ui.insert_money())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.user_failed())

        elif msg.startswith("insert_bill"):
            coin = int(msg.split("@")[1])
            if not self.ui.state:
                self.vm.insert_coin(coin)
                self.ui_bridge.update_ui(lambda: self.ui.insert_money())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.user_failed())

        elif msg.startswith("return_money"):
            if not self.ui.state:
                _, _, msg_ = self.vm.refund_all()
                self.ui_bridge.update_ui(lambda: self.ui.return_money(msg_))
            else:
                self.ui_bridge.update_ui(lambda: self.ui.user_failed())

        elif msg.startswith("select_product"):
            idx = int(msg.split("@")[1])
            if not self.ui.state and self.vm.add_to_cart(idx):
                self.ui_bridge.update_ui(lambda: self.ui.select_product_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.select_product_failed())

        elif msg.startswith("deselect_product"):
            idx = int(msg.split("@")[1])
            if not self.ui.state and self.vm.remove_from_cart(idx):
                self.ui_bridge.update_ui(lambda: self.ui.deselect_product_succeeded())
            else:
                self.ui_bridge.update_ui(lambda: self.ui.deselect_product_failed())

        elif msg.startswith("purchase"):
            if not self.ui.state:
                _, _, msg_ = self.vm.process_payment()
                self.ui_bridge.update_ui(lambda: self.ui.purchase(msg_))
            else:
                self.ui_bridge.update_ui(lambda: self.ui.user_failed())

        else:
                print("Unknown message received:", msg)
