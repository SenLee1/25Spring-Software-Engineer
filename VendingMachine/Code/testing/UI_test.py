import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
import unittest
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from UI import UserInterface
from VM import VendingMachine
from UIbridge import UIFeedbackBridge
from Bridge import FakeZmqHandler

class TestVendingMachineUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    @classmethod
    def tearDownClass(cls):
        QTest.qWait(1000)
        cls.app.quit()

    def setUp(self):
        self.vm = VendingMachine()
        self.ui = UserInterface(self.vm, None)
        self.ui_bridge = UIFeedbackBridge(self.ui)
        self.fake_backend = FakeZmqHandler(self.ui, self.vm, self.ui_bridge)
        self.ui.send_request = self.fake_backend.sendMsg
        self.ui.show()
        QTest.qWait(1000)

    def tearDown(self):
        self.fake_backend.stop()
        self.ui.close()

    def _find_button_by_text(self, text):
        return next(btn for btn in self.ui.findChildren(QPushButton) if btn.text() == text)

    def test_common1(self):
        self.ui.pwd_entry.setText("123456")
        QTest.qWait(1000)
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_0")
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_1")
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_2")
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_3")
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_4")
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        withdraw_btn = self.ui.admin_panel.findChild(QPushButton, "withdraw_100")
        QTest.mouseClick(withdraw_btn, Qt.LeftButton)
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_0.5")
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_1")
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_5")
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_10")
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_20")
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_50")
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.ui.logout_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.alerts["low_stock"], [])
        self.assertEqual(self.vm.alerts["low_coins"], [])
        self.assertEqual(self.vm.alerts["low_bills"], [])
        self.assertEqual(self.vm.alerts["full_cash"], [])
        self.assertEqual(self.vm.coin_stock, {100: 0, 50: 20, 20: 20, 10: 20, 5: 20, 1: 20, 0.5: 20})
        for i in range (0, 5):
            self.assertEqual(self.vm.products[i].stock, 20)

    def test_common2(self):
        btn = self._find_button_by_text("1元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("5元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.products[0].stock, 14)
        self.assertEqual(self.vm.products[1].stock, 20)
        self.assertEqual(self.vm.products[2].stock, 15)
        self.assertEqual(self.vm.products[3].stock, 1)
        self.assertEqual(self.vm.products[4].stock, 0)
        self.assertEqual(self.vm.coin_stock[1], 4)
        self.assertEqual(self.vm.coin_stock[5], 6)
        for coin in [100, 50, 20, 10, 0.5]:
            self.assertEqual(self.vm.coin_stock[coin], 5)

    def test_common3(self):
        btn = self._find_button_by_text("1元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.products[0].stock, 15)
        self.assertEqual(self.vm.products[1].stock, 20)
        self.assertEqual(self.vm.products[2].stock, 15)
        self.assertEqual(self.vm.products[3].stock, 1)
        self.assertEqual(self.vm.products[4].stock, 0)
        for coin in [100, 50, 20, 10, 5, 1, 0.5]:
            self.assertEqual(self.vm.coin_stock[coin], 5)

    def test_common4(self):
        self.vm.coin_stock = {coin: 0 for coin in self.vm.valid_coins} #先制条件
        btn = self._find_button_by_text("1元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("5元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.products[0].stock, 15)
        self.assertEqual(self.vm.products[1].stock, 20)
        self.assertEqual(self.vm.products[2].stock, 15)
        self.assertEqual(self.vm.products[3].stock, 1)
        self.assertEqual(self.vm.products[4].stock, 0)
        for coin in [100, 50, 20, 10, 5, 1, 0.5]:
            self.assertEqual(self.vm.coin_stock[coin], 0)

    def test_rare1(self):
        btn = self._find_button_by_text("100元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.ui.pwd_entry.setText("123456")
        QTest.qWait(1000)
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        withdraw_btn = self.ui.admin_panel.findChild(QPushButton, "withdraw_100")
        QTest.mouseClick(withdraw_btn, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.ui.logout_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 100.0)
        self.assertEqual(self.vm.products[0].stock, 15)
        self.assertEqual(self.vm.products[1].stock, 20)
        self.assertEqual(self.vm.products[2].stock, 15)
        self.assertEqual(self.vm.products[3].stock, 1)
        self.assertEqual(self.vm.products[4].stock, 0)
        self.assertEqual(self.vm.coin_stock[100], 0)
        for coin in [50, 20, 10, 5, 1, 0.5]:
            self.assertEqual(self.vm.coin_stock[coin], 5)
        self.assertEqual(self.vm.insert_stock[100], 1)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 96.0)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.products[0].stock, 14)
        self.assertEqual(self.vm.coin_stock[100], 1)
        self.assertEqual(self.vm.coin_stock[50], 4)
        self.assertEqual(self.vm.coin_stock[20], 3)
        self.assertEqual(self.vm.coin_stock[10], 5)
        self.assertEqual(self.vm.coin_stock[5], 4)
        self.assertEqual(self.vm.coin_stock[1], 4)
        self.assertEqual(self.vm.coin_stock[0.5], 5)

    def test_rare2(self):
        self.vm.coin_stock = {coin: 0 for coin in self.vm.valid_coins} #先制条件
        btn = self._find_button_by_text("100元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[100], 0)
        self.assertEqual(self.vm.insert_stock[100], 0)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.products[0].stock, 15)

    def test_rare3(self):
        btn = self._find_button_by_text("100元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_4")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.ui.user_status_label.text(), "商品选择失败")
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[100], 5)
        self.assertEqual(self.vm.insert_stock[100], 0)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.products[0].stock, 15)
        self.assertEqual(self.vm.products[1].stock, 20)
        self.assertEqual(self.vm.products[2].stock, 15)
        self.assertEqual(self.vm.products[3].stock, 1)
        self.assertEqual(self.vm.products[4].stock, 0)

    def test_rare4(self):
        self.vm.timeout = 10 #方便测试
        self.ui.pwd_entry.setText("123456")
        QTest.qWait(1000)
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(11000)
        self.assertFalse(self.ui.admin_panel.isVisible())



if __name__ == '__main__':
    unittest.main()