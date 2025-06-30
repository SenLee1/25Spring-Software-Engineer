import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
import unittest
from VM import VendingMachine
from UI import UserInterface
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

class fakezmq():
    def __init__(self):
        self.last_msg = None
    
    def sendMsg(self, msg):
        self.last_msg = msg

class TestVendingMachine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        self.vm = VendingMachine()
        self.zmq = fakezmq()
        self.ui = UserInterface(self.vm, self.zmq)
        self.ui.hide()

    def test_add_to_cart(self):
        result = self.vm.add_to_cart(0)
        self.assertTrue(result)
        self.assertEqual(self.vm.selected_products[0], 1)

    def test_add_to_cart_fail(self):
        result = self.vm.add_to_cart(4)
        self.assertFalse(result)
        self.assertEqual(self.vm.selected_products[0], 0)

    def test_add_to_cart_invalid(self):
        result = self.vm.add_to_cart(5)
        self.assertFalse(result)

    def test_remove_from_cart(self):
        self.vm.add_to_cart(0)
        result = self.vm.remove_from_cart(0)
        self.assertTrue(result)
        self.assertEqual(self.vm.selected_products[0], 0)

    def test_remove_from_cart_fail(self):
        result = self.vm.remove_from_cart(0)
        self.assertFalse(result)
        self.assertEqual(self.vm.selected_products[0], 0)

    def test_remove_from_cart_remain(self):
        self.vm.add_to_cart(0)
        self.vm.add_to_cart(0)
        result = self.vm.remove_from_cart(0)
        self.assertTrue(result)
        self.assertEqual(self.vm.selected_products[0], 1)

    def test_remove_from_cart_invalid(self):
        result = self.vm.remove_from_cart(5)
        self.assertFalse(result)

    def test_process_payment_success(self):
        self.vm.add_to_cart(0)
        self.vm.insert_coin(10)
        success, products, msg = self.vm.process_payment()
        self.assertTrue(success)
        self.assertEqual(products, {1: 1})
        self.assertIn("支付成功", msg)
        self.assertEqual(self.vm.current_amount, 6.0)

    def test_process_payment_insufficient(self):
        self.vm.add_to_cart(0)
        success, products, msg = self.vm.process_payment()
        self.assertFalse(success)
        self.assertIn("金额不足", msg)

    def test_process_payment_not_refund(self):
        for _ in range(5):
            self.vm.add_to_cart(1)
            self.vm.insert_coin(5)
            self.vm.process_payment()
            self.vm.refund_all()
        self.vm.add_to_cart(1)
        self.vm.insert_coin(5)
        success, products, msg = self.vm.process_payment()
        self.assertFalse(success)
        self.assertIn("零钱不足", msg)

    def test_process_payment_no_product(self):
        success, products, msg = self.vm.process_payment()
        self.assertFalse(success)
        self.assertIn("请先选购商品", msg)

    def test_refund_all(self):
        self.vm.insert_coin(10)
        success, returned_money, msg = self.vm.refund_all()
        self.assertTrue(success)
        self.assertEqual(returned_money, {100: 0, 50: 0, 20: 0, 10: 1, 5: 0, 1: 0, 0.5: 0})
        self.assertIn("退币成功", msg)
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.coin_stock[10], 5)

    def test_refund_all_no_money(self):
        success, returned_money, msg = self.vm.refund_all()
        self.assertFalse(success)
        self.assertEqual(returned_money, {})
        self.assertIn("当前没有可退金额", msg)
        self.assertEqual(self.vm.current_amount, 0.0)

    def test_can_give_change(self):
        self.vm.coin_stock = {100: 0, 50: 0, 20: 3, 10: 0, 5: 0, 1: 0, 0.5: 0}
        success = self.vm.can_give_change(50)
        self.assertFalse(success)
        self.vm.coin_stock = {100: 0, 50: 0, 20: 3, 10: 1, 5: 0, 1: 0, 0.5: 0}
        success = self.vm.can_give_change(50)
        self.assertTrue(success)

    def test_check_timeout(self):
        self.vm.last_operation_time = 0
        self.vm.check_timeout()
        self.assertEqual(self.vm.selected_products, {})
        self.assertEqual(self.vm.current_amount, 0.0)

    def test_check_timeout_product_remain(self):
        self.vm.add_to_cart(0)
        self.vm.last_operation_time = 0
        self.vm.check_timeout()
        self.assertEqual(self.vm.selected_products, {})
        self.assertEqual(self.vm.current_amount, 0.0)

    def test_check_timeout_money_remain(self):
        self.vm.insert_coin(10)
        self.vm.last_operation_time = 0
        self.vm.check_timeout()
        self.assertEqual(self.vm.selected_products, {})
        self.assertEqual(self.vm.current_amount, 0.0)
        self.assertEqual(self.vm.products[0].stock, 15)
        self.assertEqual(self.vm.coin_stock[10], 6)
        self.assertEqual(self.vm.insert_stock[10], 0)

    def test_verify_admin(self):
        success = self.vm.verify_admin("123456")
        self.assertTrue(success)
        success = self.vm.verify_admin("12_4a6")
        self.assertFalse(success)

    def test_refill_coins(self):
        self.vm.coin_stock[50] = 10
        self.vm.refill_coin(50)
        self.assertEqual(self.vm.coin_stock[50], 10)
        num = self.vm.coin_stock[100]
        self.vm.refill_coin(100)
        self.assertEqual(self.vm.coin_stock[100], num)
        success = self.vm.refill_coin(2)
        self.assertFalse(success)

    def test_refill_coins_sufficient(self):
        self.vm.coin_stock[50] = 25
        self.vm.refill_coin(50)
        self.assertEqual(self.vm.coin_stock[50], 25)

    def test_withdraw_coins(self):
        self.vm.withdraw_coin(50)
        self.assertEqual(self.vm.coin_stock[50], 5)
        self.vm.withdraw_coin(100)
        self.assertEqual(self.vm.coin_stock[100], 0)

    def test_withdraw_coins_sufficient(self):
        self.vm.coin_stock[50] = 25
        self.vm.withdraw_coin(50)
        self.assertEqual(self.vm.coin_stock[50], 5)

    def test_withdraw_coins_invalid(self):
        result = self.vm.withdraw_coin(3)
        self.assertFalse(result)

    def test_insert_coin(self):
        self.vm.insert_coin(1)
        self.assertEqual(self.vm.current_amount, 1.0)
        self.assertEqual(self.vm.insert_stock[1], 1)
        self.assertEqual(self.vm.coin_stock[1], 5)

    def test_insert_invalid_coin(self):
        self.vm.insert_coin(3)
        self.assertEqual(self.vm.current_amount, 0.0)
        for i in [100, 50, 20, 10, 5, 1, 0.5]:
            self.assertEqual(self.vm.insert_stock[i], 0)
            self.assertEqual(self.vm.coin_stock[i], 5)

    def test_restock_products(self):
        self.vm.restock_product(0)
        self.assertEqual(self.vm.products[0].stock, 20)

    def test_restock_products(self):
        result = self.vm.restock_product(5)
        self.assertFalse(result)

    def _find_button_by_text(self, text):
        return next(btn for btn in self.ui.findChildren(QPushButton) if btn.text() == text)

    def test_insert_coin_binding(self):
        btn = self._find_button_by_text("1元")
        self.assertIsNotNone(btn)
        QTest.mouseClick(btn, Qt.LeftButton)
        self.assertEqual(self.zmq.last_msg, "insert_coin@1")
        btn = self._find_button_by_text("5元")
        self.assertIsNotNone(btn)
        QTest.mouseClick(btn, Qt.LeftButton)
        self.assertEqual(self.zmq.last_msg, "insert_bill@5")

    def test_refill_coin_binding(self):
        btn = self.ui.findChild(QPushButton, "refill_1")
        self.assertIsNotNone(btn)
        QTest.mouseClick(btn, Qt.LeftButton)
        self.assertEqual(self.zmq.last_msg, "add_coin@1")
        btn = self.ui.findChild(QPushButton, "refill_5")
        self.assertIsNotNone(btn)
        QTest.mouseClick(btn, Qt.LeftButton)
        self.assertEqual(self.zmq.last_msg, "add_bill@5")

    def test_withdraw_binding(self):
        btn = self.ui.findChild(QPushButton, "withdraw_1")
        self.assertIsNotNone(btn)
        QTest.mouseClick(btn, Qt.LeftButton)
        self.assertEqual(self.zmq.last_msg, "remove_coin@1")
        btn = self.ui.findChild(QPushButton, "withdraw_5")
        self.assertIsNotNone(btn)
        QTest.mouseClick(btn, Qt.LeftButton)
        self.assertEqual(self.zmq.last_msg, "remove_bill@5")

    def test_check_timeout_diaplay(self):
        self.ui.login_succeeded()
        self.assertTrue(self.ui.state)
        self.vm.last_operation_time = 0
        self.ui.check_timeout()
        self.assertEqual(self.ui.user_timer_label.text(), "操作剩余时间：0秒")
        self.assertFalse(self.ui.state)

    def test_check_timein_diaplay(self):
        self.ui.check_timeout()
        self.assertEqual(self.ui.user_timer_label.text(), "操作剩余时间：299秒")

    def test_check_timein_diaplay_admin(self):
        self.ui.login_succeeded()
        self.ui.check_timeout()
        self.assertEqual(self.ui.user_timer_label.text(), "操作剩余时间：299秒")

    def test_update_display(self):
        self.vm.coin_stock[50] = 50
        self.ui.update_display()
        self.assertEqual("需补货：薯片, 辣条\n需补硬币：1, 0.5元\n需补纸币：20, 10, 5元\n需取钱：50元", self.ui.alert_label.text())

    def test_check_alerts(self):
        self.vm.check_alerts()
        self.assertIn("low_coins", self.vm.alerts)
        self.assertIn("low_bills", self.vm.alerts)
        self.assertIn("low_stock", self.vm.alerts)
        for product in [0, 1, 2, 3, 4]:
            self.vm.restock_product(product)
        self.vm.check_alerts()
        self.assertEqual(self.vm.alerts["low_stock"], [])

    def test_login_succeed(self):
        self.ui.login_succeeded()
        self.assertTrue(self.ui.state)
        self.assertFalse(self.ui.admin_panel.isHidden())
        self.assertEqual(self.ui.user_status_label.text(), "登录成功")
    
    def test_login_failed(self):
        self.ui.login_failed("password")
        self.assertFalse(self.ui.state)
        self.assertTrue(self.ui.admin_panel.isHidden())
        self.assertIn("登录失败", self.ui.user_status_label.text())

    def test_logout_succeed(self):
        self.ui.logout_succeeded()
        self.assertFalse(self.ui.state)
        self.assertTrue(self.ui.admin_panel.isHidden())
        self.assertEqual(self.ui.user_status_label.text(), "请选择商品")
        self.assertEqual(self.ui.admin_status_label.text(), "")

    def test_add_product_succeeded(self):
        self.ui.add_product_succeeded()
        self.assertIn("商品补货成功", self.ui.admin_status_label.text())

    def test_add_coin_succeeded(self):
        self.ui.add_coin_succeeded()
        self.assertIn("钱币补充成功", self.ui.admin_status_label.text())

    def test_add_bill_succeeded(self):
        self.ui.add_bill_succeeded()
        self.assertIn("钞票补充成功", self.ui.admin_status_label.text())

    def test_remove_money_succeeded(self):
        self.ui.remove_money_succeeded()
        self.assertIn("已取钱", self.ui.admin_status_label.text())

    def test_admin_failed(self):
        self.ui.admin_failed()
        self.assertIn("请先进入管理员模式", self.ui.user_status_label.text())

    def test_insert_money(self):
        self.ui.insert_money()
        self.assertIn("投币成功", self.ui.user_status_label.text())

    def test_return_money_succeeded(self):
        self.vm.insert_coin(5)
        success, _, msg = self.vm.refund_all()
        self.ui.return_money(msg)
        self.assertTrue(success)
        self.assertIn("退币成功", self.ui.user_status_label.text())
        
    def test_return_money_failed(self):
        success, _, msg = self.vm.refund_all()
        self.ui.return_money(msg)
        self.assertFalse(success)
        self.assertIn("当前没有可退金额", self.ui.user_status_label.text())

    def test_select_product_succeeded(self):
        self.ui.select_product_succeeded()
        self.assertIn("商品已添加", self.ui.user_status_label.text())

    def test_select_product_failed(self):
        self.ui.select_product_failed()
        self.assertIn("商品选择失败", self.ui.user_status_label.text())

    def test_deslect_product_succeeded(self):
        self.ui.deselect_product_succeeded()
        self.assertIn("商品已移除", self.ui.user_status_label.text())

    def test_deselect_product_failed(self):
        self.ui.deselect_product_failed()
        self.assertIn("商品移除失败", self.ui.user_status_label.text())

    def test_purchase(self):
        self.vm.add_to_cart(0)
        self.vm.insert_coin(10)
        _, _, msg = self.vm.process_payment()
        self.ui.purchase(msg)
        self.assertIn("支付成功", self.ui.user_status_label.text())
        self.assertEqual(self.ui.cart_list.count(), 1)

    def test_purchase_insufficient_funds(self):
        self.vm.add_to_cart(0)
        self.vm.insert_coin(1)
        _, _, msg = self.vm.process_payment()
        self.ui.purchase(msg)
        self.assertIn("金额不足", self.ui.user_status_label.text())
        self.assertEqual(self.ui.cart_list.count(), 2)

    def test_purchase_no_change(self):
        self.vm.coin_stock = {coin: 0 for coin in self.vm.valid_coins}
        self.vm.add_to_cart(0)
        self.vm.insert_coin(10)
        _, _, msg = self.vm.process_payment()
        self.ui.purchase(msg)
        self.assertIn("零钱不足", self.ui.user_status_label.text())
        self.assertEqual(self.ui.cart_list.count(), 2)

    def test_purchase_no_product(self):
        _, _, msg = self.vm.process_payment()
        self.ui.purchase(msg)
        self.assertIn("请先选购商品", self.ui.user_status_label.text())

    def test_user_failed(self):
        self.ui.user_failed()
        self.assertIn("请先退出管理员模式", self.ui.user_status_label.text())
    
    def tearDown(self):
        self.ui.close()
        self.vm = None
        self.ui = None

if __name__ == '__main__':
    unittest.main()