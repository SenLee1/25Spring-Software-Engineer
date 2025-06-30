from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QListWidget, QTabWidget, QLineEdit, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer
import threading
import time

class UserInterface(QMainWindow):

    def __init__(self, vm, zmq):
        super().__init__()
        self.vm = vm
        self.zmq = zmq
        self.state = False
        self.setWindowTitle("智能售货机")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.user_frame = QFrame()
        self.user_frame.setFrameShape(QFrame.StyledPanel)
        self.setup_user_interface()
        main_layout.addWidget(self.user_frame, 70)

        self.admin_frame = QFrame()
        self.admin_frame.setFrameShape(QFrame.StyledPanel)
        main_layout.addWidget(self.admin_frame, 30)
        
        admin_layout = QVBoxLayout()
        self.admin_frame.setLayout(admin_layout)

        self.login_panel = QFrame()
        login_layout = QHBoxLayout()
        self.pwd_entry = QLineEdit()
        self.pwd_entry.setEchoMode(QLineEdit.Password)
        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self.login_admin)
        login_layout.addWidget(QLabel("管理员密码:"))
        login_layout.addWidget(self.pwd_entry)
        login_layout.addWidget(self.login_btn)
        self.login_panel.setLayout(login_layout)
        admin_layout.addWidget(self.login_panel)

        self.admin_panel = QFrame()
        self.setup_admin_interface()
        self.admin_panel.setVisible(False)
        admin_layout.addWidget(self.admin_panel)

        self.admin_status_label = QLabel()
        admin_layout.addWidget(self.admin_status_label)

        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_timeout)
        self.check_timer.start(1000)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

    def send_request(self, msg):
        self.zmq.sendMsg(msg)

    def setup_user_interface(self):
        product_layout = QVBoxLayout()
        self.product_widgets = []

        for i, product in enumerate(self.vm.products):
            hbox = QHBoxLayout()
            label = QLabel(f"{product.name}\n{product.price}元")
            add_btn = QPushButton("+")
            add_btn.setObjectName(f"add_{i}")
            add_btn.clicked.connect(lambda _, i=i: self.send_request(f"select_product@{i}"))
            sub_btn = QPushButton("-")
            sub_btn.setObjectName(f"sub_{i}")
            sub_btn.clicked.connect(lambda _, i=i: self.send_request(f"deselect_product@{i}"))
            stock_label = QLabel(f"库存：{product.stock}")
            selected_label = QLabel("已选：0")
            hbox.addWidget(label)
            hbox.addWidget(add_btn)
            hbox.addWidget(sub_btn)
            hbox.addWidget(stock_label)
            hbox.addWidget(selected_label)
            self.product_widgets.append((stock_label, selected_label))
            product_layout.addLayout(hbox)

        control_layout = QVBoxLayout()
        self.cart_list = QListWidget()
        control_layout.addWidget(self.cart_list)

        coin_row = QHBoxLayout()
        for coin in self.vm.valid_coins:
            btn = QPushButton(f"{coin}元")
            if coin in [1, 0.5]:
                btn.clicked.connect(lambda _, c=coin: self.send_request(f"insert_coin@{c}"))
            else:
                btn.clicked.connect(lambda _, c=coin: self.send_request(f"insert_bill@{c}"))
            coin_row.addWidget(btn)
        control_layout.addLayout(coin_row)

        info_row = QHBoxLayout()
        self.amount_label = QLabel("0.0 元")
        self.balance_label = QLabel("0.0 元")
        pay_btn = QPushButton("确认支付")
        pay_btn.clicked.connect(lambda: self.send_request("purchase"))
        refund_btn = QPushButton("全部退币")
        refund_btn.clicked.connect(lambda: self.send_request("return_money"))
        info_row.addWidget(QLabel("已投金额："))
        info_row.addWidget(self.amount_label)
        info_row.addWidget(pay_btn)
        info_row.addWidget(refund_btn)
        info_row.addWidget(QLabel("当前余额："))
        info_row.addWidget(self.balance_label)
        control_layout.addLayout(info_row)

        self.user_status_label = QLabel("请选择商品")
        self.user_timer_label = QLabel("操作剩余时间：300秒")
        control_layout.addWidget(self.user_status_label)
        control_layout.addWidget(self.user_timer_label)

        user_main = QHBoxLayout()
        user_main.addLayout(product_layout, 2)
        user_main.addLayout(control_layout, 3)
        self.user_frame.setLayout(user_main)

    def setup_admin_interface(self):
        layout = QVBoxLayout()
        self.admin_frame.setLayout(layout)

        self.admin_status_label = QLabel()
        self.admin_status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.admin_status_label)

        self.admin_panel = QWidget()
        self.admin_panel_layout = QVBoxLayout()
        self.admin_panel.setLayout(self.admin_panel_layout)

        stock_group = QGridLayout()
        self.product_stock_labels = []
        for i, product in enumerate(self.vm.products):
            label = QLabel(f"{product.name}:")
            stock_label = QLabel(str(product.stock))
            restock_btn = QPushButton("补货")
            restock_btn.setObjectName(f"restock_{i}")
            restock_btn.clicked.connect(lambda _, i=i: self.send_request(f"add_product@{i}"))
            stock_group.addWidget(label, i, 0)
            stock_group.addWidget(stock_label, i, 1)
            stock_group.addWidget(restock_btn, i, 2)
            self.product_stock_labels.append(stock_label)

        self.coin_labels = {}
        for i, coin in enumerate(sorted(self.vm.valid_coins, reverse=True)):
            label = QLabel(f"{coin}元:")
            count_label = QLabel(str(self.vm.coin_stock[coin]))
            refill_btn = QPushButton("补充")
            refill_btn.setObjectName(f"refill_{coin}")
            if coin in [1, 0.5]:
                refill_btn.clicked.connect(lambda _, c=coin: self.send_request(f"add_coin@{c}"))
            else:
                refill_btn.clicked.connect(lambda _, c=coin: self.send_request(f"add_bill@{c}"))
            withdraw_btn = QPushButton("取钱")
            withdraw_btn.setObjectName(f"withdraw_{coin}")
            if coin in [1, 0.5]:
                withdraw_btn.clicked.connect(lambda _, c=coin: self.send_request(f"remove_coin@{c}"))
            else:
                withdraw_btn.clicked.connect(lambda _, c=coin: self.send_request(f"remove_bill@{c}"))
            stock_group.addWidget(label, i, 3)
            stock_group.addWidget(count_label, i, 4)
            stock_group.addWidget(refill_btn, i, 5)
            stock_group.addWidget(withdraw_btn, i, 6)
            self.coin_labels[coin] = count_label

        self.admin_panel_layout.addLayout(stock_group)
        self.alert_label = QLabel()
        self.alert_label.setStyleSheet("color: red")
        self.admin_panel_layout.addWidget(self.alert_label)

        self.logout_btn = QPushButton("安全登出")
        self.logout_btn.clicked.connect(lambda: self.send_request("log_out"))
        self.logout_btn.setVisible(False)
        self.admin_panel_layout.addWidget(self.logout_btn)

        layout.addWidget(self.admin_panel)
        self.admin_frame.setLayout(layout)

    def login_admin(self):
        pwd = self.pwd_entry.text()
        self.send_request(f"log_in@{pwd}")

    def check_timeout(self):
        if self.vm.check_timeout():
            if self.state:
                self.logout_succeeded()
            self.update_display()
        remaining = self.vm.timeout - (time.time() - self.vm.last_operation_time)
        self.user_timer_label.setText(f"操作剩余时间：{max(0, int(remaining))}秒")

    def update_display(self):
        self.cart_list.repaint()
        self.amount_label.repaint()
        self.balance_label.repaint()

        total = self.vm.calculate_total()
        self.cart_list.clear()
        for idx, qty in self.vm.selected_products.items():
            product = self.vm.products[idx]
            self.cart_list.addItem(f"{product.name} ×{qty} ｜单价：{product.price}元｜小计：{product.price*qty:.1f}元")
        self.cart_list.addItem(f"总计：{total:.1f}元")
        self.amount_label.setText(f"{self.vm.current_amount:.1f} 元")
        self.balance_label.setText(f"{self.vm.current_amount:.1f} 元")

        for i, product in enumerate(self.vm.products):
            self.product_widgets[i][0].setText(f"库存：{product.stock}")
            self.product_widgets[i][1].setText(f"已选：{self.vm.selected_products.get(i, 0)}")

        for coin, label in self.coin_labels.items():
            label.setText(str(self.vm.coin_stock[coin]))
        for i, label in enumerate(self.product_stock_labels):
            label.setText(str(self.vm.products[i].stock))

        alerts = []
        self.vm.check_alerts()
        if self.vm.alerts["low_stock"]:
            alerts.append(f"需补货：{', '.join(self.vm.alerts['low_stock'])}")
        if self.vm.alerts["low_coins"]:
            alerts.append(f"需补硬币：{', '.join(map(str, self.vm.alerts['low_coins']))}元")
        if self.vm.alerts["low_bills"]:
            alerts.append(f"需补纸币：{', '.join(map(str, self.vm.alerts['low_bills']))}元")
        if self.vm.alerts["full_cash"]:
            alerts.append(f"需取钱：{', '.join(map(str, self.vm.alerts['full_cash']))}元")
        self.alert_label.setText("\n".join(alerts))

        if self.admin_panel.isVisible():
            self.admin_panel.repaint()

    def login_succeeded(self):
        self.vm.last_operation_time = time.time()
        self.pwd_entry.setText("123456")
        self.admin_panel.setVisible(True)
        self.pwd_entry.clear()
        self.pwd_entry.setEnabled(False)
        self.login_btn.setEnabled(False)
        self.logout_btn.setVisible(True)
        self.admin_status_label.clear()
        self.user_status_label.setText("登录成功")
        self.admin_status_label.setText("管理员模式已激活")
        self.state = True
        self.update_display()
    
    def login_failed(self, password):
        self.pwd_entry.setText(password)
        self.user_status_label.setText("登录失败，请重试")
        self.pwd_entry.clear()
        self.update_display()

    def add_product_succeeded(self):
        self.vm.last_operation_time = time.time()
        self.admin_status_label.setText("商品补货成功")
        self.update_display()

    def add_coin_succeeded(self):
        self.vm.last_operation_time = time.time()
        self.admin_status_label.setText("钱币补充成功")
        self.update_display()

    def add_bill_succeeded(self):
        self.vm.last_operation_time = time.time()
        self.admin_status_label.setText("钞票补充成功")
        self.update_display()

    def remove_money_succeeded(self):
        self.vm.last_operation_time = time.time()
        self.admin_status_label.setText("已取钱")
        self.update_display()

    def admin_failed(self):
        self.user_status_label.setText("请先进入管理员模式")
        self.update_display()
    
    def logout_succeeded(self):
        self.admin_panel.setVisible(False)
        self.pwd_entry.clear()
        self.pwd_entry.setEnabled(True)
        self.login_btn.setEnabled(True)
        self.logout_btn.setVisible(False)
        self.admin_status_label.clear()
        self.user_status_label.setText("请选择商品")
        self.state = False
        self.update_display()

    def insert_money(self):
        self.user_status_label.setText("投币成功")
        self.update_display()
    
    def return_money(self, msg):
        self.user_status_label.setText(msg)
        self.update_display()

    def select_product_succeeded(self):
        self.user_status_label.setText("商品已添加")
        self.update_display()

    def select_product_failed(self):
        self.user_status_label.setText("商品选择失败")
        self.update_display()

    def deselect_product_succeeded(self):
        self.user_status_label.setText("商品已移除")
        self.update_display()

    def deselect_product_failed(self):
        self.user_status_label.setText("商品移除失败")
        self.update_display()

    def purchase(self, msg):
        self.user_status_label.setText(msg)
        self.update_display()

    def user_failed(self):
        self.user_status_label.setText("请先退出管理员模式")
        self.update_display()
