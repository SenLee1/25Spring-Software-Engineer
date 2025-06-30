import sys
from PyQt5.QtWidgets import QApplication
import VM
import UI

class LocalRunner:
    def __init__(self):
        self.vm = VM.VendingMachine()
        self.app = QApplication(sys.argv)
        self.ui =UI.UnifiedInterface(self.vm, self)
        self.state = False
        
    def sendMsg(self, msg):
        print(f"[LOCAL] 发送指令: {msg}")
        if msg.startswith("log_in"):
            password = msg.split("@")[1]
            if self.vm.verify_admin(password):
                self.state = True
                self.ui.admin_panel.setVisible(True)
                self.ui.pwd_entry.clear()
                self.ui.pwd_entry.setEnabled(False)
                self.ui.login_btn.setEnabled(False)
                self.ui.logout_btn.setVisible(True)
                self.ui.admin_status_label.clear()
                self.ui.admin_status_label.setText("登录成功")
                self.ui.user_status_label.setText("管理员模式已激活")
                self.vm.refund_all()
                self.ui.update_display()
            else:
                self.ui.admin_status_label.setText("登录失败")
                self.ui.pwd_entry.clear()
                self.ui.update_display()

        elif msg.startswith("add_product"):
            index = msg.split("@")[1]
            if self.state and self.vm.restock_product(int(index)):
                self.ui.admin_status_label.setText("商品补货成功")
                self.ui.update_display()

        elif msg.startswith("add_coin"):
            coin = msg.split("@")[1]
            if self.state and self.vm.refill_coin(float(coin)):
                self.ui.admin_status_label.setText("钱币补充成功")
                self.ui.update_display()

        elif msg.startswith("add_bill"):
            money = msg.split("@")[1]
            if self.state and self.vm.refill_coin(int(money)):
                self.ui.admin_status_label.setText("钞票补充成功")
                self.ui.update_display()

        elif msg.startswith("remove_coin"):
            coin = msg.split("@")[1]
            if self.state and self.vm.withdraw_coin(float(coin)):
                self.ui.admin_status_label.setText("已取钱")
                self.ui.update_display()

        elif msg.startswith("remove_bill"):
            bill = msg.split("@")[1]
            if self.state and self.vm.withdraw_coin(int(bill)):
                self.ui.admin_status_label.setText("已取钱")
                self.ui.update_display()

        elif msg.startswith("log_out"):
            if self.state:
                self.state = False
                self.ui.admin_panel.setVisible(False)
                self.ui.pwd_entry.clear()
                self.ui.pwd_entry.setEnabled(True)
                self.ui.login_btn.setEnabled(True)
                self.ui.logout_btn.setVisible(False)
                self.ui.admin_status_label.clear()
                self.ui.user_status_label.setText("请选择商品")
                self.ui.update_display()

        elif msg.startswith("insert_coin"):
            coin = msg.split("@")[1]
            if not self.state and self.vm.insert_coin(float(coin)):
                self.ui.user_status_label.setText("投币成功")
                self.ui.update_display()

        elif msg.startswith("insert_bill"):
            bill = msg.split("@")[1]
            if not self.state and self.vm.insert_coin(int(bill)):
                self.ui.user_status_label.setText("投币成功")
                self.ui.update_display()

        elif (msg.startswith("return_money")):
            if not self.state:
                msg = self.vm.refund_all()
                self.ui.user_status_label.setText(msg),
                self.ui.update_display()

        elif msg.startswith("select_product"):
            index = msg.split("@")[1]
            if not self.state and self.vm.add_to_cart(int(index)):
                self.ui.user_status_label.setText("商品已添加"),
                self.ui.update_display()
            else:
                self.ui.user_status_label.setText("商品添加失败"),
                self.ui.update_display()

        elif msg.startswith("deselect_product"):
            index = msg.split("@")[1]
            if not self.state and self.vm.remove_from_cart(int(index)):
                self.ui.user_status_label.setText("商品已移除"),
                self.ui.update_display()
            else:
                self.ui.user_status_label.setText("商品移除失败"),
                self.ui.update_display()

        elif (msg.startswith("purchase")):
            if not self.state:
                _, msg = self.vm.process_payment()
                self.ui.user_status_label.setText(msg),
                self.ui.update_display()
                
    def run(self):
        self.ui.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    LocalRunner().run()
