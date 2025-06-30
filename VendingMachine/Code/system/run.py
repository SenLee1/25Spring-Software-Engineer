import sys
from PyQt5.QtWidgets import QApplication
import VM
import UI

class LocalRunner:
    def __init__(self):
        self.vm = VM.VendingMachine()
        self.app = QApplication(sys.argv)
        self.ui =UI.UserInterface(self.vm, self)

    def sendMsg(self, msg):
        print(f"[LOCAL] 发送指令: {msg}")
        if msg.startswith("log_in"):
            password = msg.split("@")[1]
            if self.vm.verify_admin(password):
                self.ui.login_succeeded()
            else:
                self.ui.login_failed(password)

        elif msg.startswith("add_product"):
            index = msg.split("@")[1]
            if self.ui.state and self.vm.restock_product(int(index)):
                self.ui.add_product_succeeded()
            else:
                self.ui.admin_failed()

        elif msg.startswith("add_coin"):
            coin = msg.split("@")[1]
            if self.ui.state and self.vm.refill_coin(float(coin)):
                self.ui.add_coin_succeeded()
            else:
                self.ui.admin_failed()

        elif msg.startswith("add_bill"):
            money = msg.split("@")[1]
            if self.ui.state and self.vm.refill_coin(int(money)):
                self.ui.add_bill_succeeded()
            else:
                self.ui.admin_failed()

        elif msg.startswith("remove_coin"):
            coin = msg.split("@")[1]
            if self.ui.state and self.vm.withdraw_coin(float(coin)):
                self.ui.remove_money_succeeded()
            else:
                self.ui.admin_failed()

        elif msg.startswith("remove_bill"):
            bill = msg.split("@")[1]
            if self.ui.state and self.vm.withdraw_coin(int(bill)):
                self.ui.remove_money_succeeded()
            else:
                self.ui.admin_failed()

        elif msg.startswith("log_out"):
            if self.ui.state:
                self.ui.logout_succeeded()
            else:
                self.ui.admin_failed()

        elif msg.startswith("insert_coin"):
            coin = msg.split("@")[1]
            if not self.ui.state:
                self.vm.insert_coin(float(coin))
                self.ui.insert_money()
            else:
                self.ui.user_failed()

        elif msg.startswith("insert_bill"):
            bill = msg.split("@")[1]
            if not self.ui.state:
                self.vm.insert_coin(int(bill))
                self.ui.insert_money()
            else:
                self.ui.user_failed()

        elif (msg.startswith("return_money")):
            if not self.ui.state:
                success, _, msg = self.vm.refund_all()
                self.ui.return_money(msg)
            else:
                self.ui.user_failed()

        elif msg.startswith("select_product"):
            index = msg.split("@")[1]
            if not self.ui.state and self.vm.add_to_cart(int(index)):
                self.ui.select_product_succeeded()
            else:
                self.ui.select_product_failed()

        elif msg.startswith("deselect_product"):
            index = msg.split("@")[1]
            if not self.ui.state and self.vm.remove_from_cart(int(index)):
                self.ui.deselect_product_succeeded()
            else:
                self.ui.deselect_product_failed()

        elif (msg.startswith("purchase")):
            if not self.ui.state:
                _, _, msg = self.vm.process_payment()
                self.ui.purchase(msg)
            else:
                self.ui.user_failed()
        else:
            print(f"[LOCAL] 未知指令: {msg}")
                
    def run(self):
        self.ui.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    LocalRunner().run()
