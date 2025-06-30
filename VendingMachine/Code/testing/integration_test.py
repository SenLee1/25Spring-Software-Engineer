import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
import unittest
from PyQt5.QtWidgets import QApplication, QPushButton, QLineEdit, QLabel
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

    def test_login_admin_success(self):
        self.ui.pwd_entry.setText("123456")
        self.vm.insert_coin(5)
        self.assertEqual(self.vm.current_amount, 5.0)
        QTest.qWait(1000)
        self.assertFalse(self.ui.state)
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertTrue(self.ui.state)
        self.assertTrue(self.ui.admin_panel.isVisible())
        self.assertEqual(self.ui.user_status_label.text(), "登录成功")
        self.assertEqual(self.vm.current_amount, 5.0)

    def test_login_admin_failed(self):
        self.ui.pwd_entry.setText("12asd")
        QTest.qWait(1000)
        self.assertFalse(self.ui.state)
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertFalse(self.ui.state)
        self.assertFalse(self.ui.admin_panel.isVisible())
        self.assertIn("登录失败", self.ui.user_status_label.text())

    def test_logout_admin(self):
        self.ui.login_succeeded()
        QTest.qWait(1000)
        self.assertTrue(self.ui.state)
        QTest.mouseClick(self.ui.logout_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertFalse(self.ui.state)
        self.assertFalse(self.ui.admin_panel.isVisible())
        self.assertEqual(self.ui.user_status_label.text(), "请选择商品")

    def test_admin_restock_product_succeeded(self):
        self.ui.login_succeeded()
        QTest.qWait(1000)
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_0")
        self.vm.products[0].stock = 0
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.products[0].stock, 20)
        self.assertEqual(self.ui.product_stock_labels[0].text(), "20")
        self.assertEqual(self.ui.admin_status_label.text(), "商品补货成功")

    def test_admin_restock_product_falied(self):
        restock_btn = self.ui.admin_panel.findChild(QPushButton, "restock_0")
        self.vm.products[0].stock = 0
        QTest.mouseClick(restock_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.products[0].stock, 0)
        self.assertEqual(self.ui.product_stock_labels[0].text(), "0")
        self.assertEqual(self.ui.user_status_label.text(), "请先进入管理员模式")

    def test_admin_refill_coin_succeeded(self):
        self.ui.login_succeeded()
        QTest.qWait(1000)
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_1")
        self.vm.coin_stock[1] = 5
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[1], 20)
        self.assertEqual(self.ui.coin_labels[1].text(), "20")
        self.assertEqual(self.ui.admin_status_label.text(), "钱币补充成功")
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_100")
        self.vm.coin_stock[100] = 5
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[100], 5)
        self.assertEqual(self.ui.coin_labels[100].text(), "5")
        self.assertEqual(self.ui.admin_status_label.text(), "钞票补充成功")

    def test_admin_refill_coin_falied(self):
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_1")
        self.vm.coin_stock[1] = 5
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[1], 5)
        self.assertEqual(self.ui.coin_labels[1].text(), "5")
        self.assertEqual(self.ui.user_status_label.text(), "请先进入管理员模式")
        refill_btn = self.ui.admin_panel.findChild(QPushButton, "refill_5")
        self.vm.coin_stock[5] = 5
        QTest.mouseClick(refill_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[5], 5)
        self.assertEqual(self.ui.coin_labels[5].text(), "5")
        self.assertEqual(self.ui.user_status_label.text(), "请先进入管理员模式")

    def test_admin_withdraw_succeeded(self):
        self.ui.login_succeeded()
        QTest.qWait(1000)
        withdraw_btn = self.ui.admin_panel.findChild(QPushButton, "withdraw_1")
        self.vm.coin_stock[1] = 25
        QTest.mouseClick(withdraw_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[1], 20)
        self.assertEqual(self.ui.coin_labels[1].text(), "20")
        self.assertEqual(self.ui.admin_status_label.text(), "已取钱")
        withdraw_btn = self.ui.admin_panel.findChild(QPushButton, "withdraw_100")
        self.vm.coin_stock[100] = 5
        QTest.mouseClick(withdraw_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[100], 0)
        self.assertEqual(self.ui.coin_labels[100].text(), "0")

    def test_admin_withdraw_falied(self):
        withdraw_btn = self.ui.admin_panel.findChild(QPushButton, "withdraw_1")
        self.vm.coin_stock[1] = 25
        QTest.mouseClick(withdraw_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[1], 25)
        self.assertEqual(self.ui.coin_labels[1].text(), "25")
        self.assertEqual(self.ui.user_status_label.text(), "请先进入管理员模式")
        withdraw_btn = self.ui.admin_panel.findChild(QPushButton, "withdraw_5")
        self.vm.coin_stock[5] = 25
        QTest.mouseClick(withdraw_btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.coin_stock[5], 25)
        self.assertEqual(self.ui.coin_labels[5].text(), "25")
        self.assertEqual(self.ui.user_status_label.text(), "请先进入管理员模式")

    def test_insert_coin_button_succeeded(self):
        btn = self._find_button_by_text("1元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 1.0)
        self.assertEqual(self.ui.amount_label.text(), "1.0 元")
        self.assertEqual(self.ui.user_status_label.text(), "投币成功")
        btn = self._find_button_by_text("5元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 6.0)
        self.assertEqual(self.ui.amount_label.text(), "6.0 元")
        self.assertEqual(self.ui.user_status_label.text(), "投币成功")

    def test_insert_coin_button_failed(self):
        self.ui.login_succeeded()
        QTest.qWait(1000)
        btn = self._find_button_by_text("1元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.ui.amount_label.text(), "0.0 元")
        self.assertEqual(self.ui.user_status_label.text(), "请先退出管理员模式")
        btn = self._find_button_by_text("5元")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.ui.amount_label.text(), "0.0 元")
        self.assertEqual(self.ui.user_status_label.text(), "请先退出管理员模式")

    def test_return_money_succeeded(self):
        self.vm.insert_coin(5)
        self.assertEqual(self.vm.current_amount, 5.0)
        self.assertEqual(self.vm.insert_stock[5], 1)
        self.assertEqual(self.vm.coin_stock[5], 5)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.coin_stock[5], 5)
        self.assertIn("退币成功", self.ui.user_status_label.text())

    def test_return_money_failed_no_refund(self):
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.coin_stock[5], 5)
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.coin_stock[5], 5)
        self.assertIn("没有可退金额", self.ui.user_status_label.text())

    def test_return_money_failed_admin(self):
        self.ui.login_succeeded()
        QTest.qWait(1000)
        btn = self._find_button_by_text("全部退币")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.ui.user_status_label.text(), "请先退出管理员模式")

    def test_select_product_success(self):
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertGreaterEqual(self.vm.selected_products[0], 1)
        self.assertIn("商品已添加", self.ui.user_status_label.text())

    def test_select_product_failed_no_product(self):
        btn = self.ui.findChild(QPushButton, "add_4")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertGreaterEqual(self.vm.selected_products[4], 0)
        self.assertIn("商品选择失败", self.ui.user_status_label.text())

    def test_select_product_failed_in_admin(self):
        self.ui.pwd_entry.setText("123456")
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "add_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.selected_products[0], 0)
        self.assertIn("商品选择失败", self.ui.user_status_label.text())

    def test_deselect_product_success(self):
        self.vm.add_to_cart(0)
        btn = self.ui.findChild(QPushButton, "sub_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.selected_products[0], 0)
        self.assertIn("商品已移除", self.ui.user_status_label.text())

    def test_deselect_product_fail_no_product(self):
        btn = self.ui.findChild(QPushButton, "sub_4")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.vm.selected_products[4], 0)
        self.assertIn("商品移除失败", self.ui.user_status_label.text())

    def test_deselect_product_fail_in_admin(self):
        self.vm.add_to_cart(0)
        self.ui.pwd_entry.setText("123456")
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self.ui.findChild(QPushButton, "sub_0")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertGreater(self.vm.selected_products[0], 0)
        self.assertIn("商品移除失败", self.ui.user_status_label.text())

    def test_purchase_success(self):
        self.vm.insert_coin(10)
        self.vm.add_to_cart(0)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(len(self.vm.selected_products), 0)
        self.assertIn("支付成功", self.ui.user_status_label.text())

    def test_purchase_fail_insufficient_funds(self):
        self.vm.insert_coin(1)
        self.vm.add_to_cart(0)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertIn("金额不足", self.ui.user_status_label.text())

    def test_purchase_fail_no_change(self):
        self.vm.insert_coin(100)
        self.vm.add_to_cart(0)
        self.vm.coin_stock = {coin: 0 for coin in self.vm.valid_coins}
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertIn("零钱不足", self.ui.user_status_label.text())

    def test_purchase_fail_in_admin_mode(self):
        self.vm.insert_coin(10)
        self.vm.add_to_cart(0)
        self.ui.pwd_entry.setText("123456")
        QTest.mouseClick(self.ui.login_btn, Qt.LeftButton)
        QTest.qWait(1000)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertIn("请先退出管理员模式", self.ui.user_status_label.text())

    def test_purchase_no_product(self):
        self.vm.insert_coin(10)
        btn = self._find_button_by_text("确认支付")
        QTest.mouseClick(btn, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(len(self.vm.selected_products), 0)
        self.assertIn("请先选购商品", self.ui.user_status_label.text())

    def _find_button_by_text(self, text):
        return next(btn for btn in self.ui.findChildren(QPushButton) if btn.text() == text)


if __name__ == '__main__':
    unittest.main()
