import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import time

class Product:
    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

class VendingMachine:
    def __init__(self):
        self.products = [
            Product("可乐", 3.5, 20),
            Product("矿泉水", 2.0, 15),
            Product("薯片", 5.0, 1),
            Product("巧克力", 4.0, 15),
            Product("辣条", 1.0, 0)
        ]
        self.valid_coins = [100, 50, 20, 10, 5, 1, 0.5]
        self.coin_stock = {coin: 5 for coin in self.valid_coins}
        self.coin_threshold = {
            100: 5, 50: 5, 20: 10, 
            10: 20, 5: 20, 1: 20, 0.5: 10
        }
        self.current_amount = 0.0
        self.total_income = 0.0
        self.selected_products = defaultdict(int)
        self.last_operation_time = time.time()
        self.timeout = 300

        self.alerts = {
            "low_stock": [],
            "low_coins": [],
            "low_bills": [],
            "full_cash": []
        }

    def check_alerts(self):
        self.alerts["low_stock"] = [p.name for p in self.products if p.stock < 5]
        self.alerts["low_coins"] = [
            coin for coin in [1, 0.5]
            if self.coin_stock[coin] < self.coin_threshold[coin]
        ]
        self.alerts["low_bills"] = [
            coin for coin in [100, 50, 20, 10, 5]
            if self.coin_stock[coin] < self.coin_threshold[coin]
        ]
        self.alerts["full_cash"] = [
            coin for coin in self.valid_coins
            if self.coin_stock[coin] >= 20
        ]

    def add_to_cart(self, product_idx):
        product = self.products[product_idx]
        if product.stock > 0 and (product.stock > self.selected_products[product_idx]):
            self.selected_products[product_idx] += 1
            self.last_operation_time = time.time()
            return True
        return False

    def remove_from_cart(self, product_idx):
        if product_idx in self.selected_products:
            self.selected_products[product_idx] -= 1
            if self.selected_products[product_idx] <= 0:
                del self.selected_products[product_idx]
            return True
        return False

    def calculate_total(self):
        return sum(
            self.products[idx].price * qty 
            for idx, qty in self.selected_products.items()
        )

    def insert_coin(self, coin):
        self.current_amount += coin
        self.coin_stock[coin] += 1
        self.last_operation_time = time.time()

    def process_payment(self):
        total = self.calculate_total()
        if self.current_amount < total:
            return False, f"金额不足，还需{total - self.current_amount:.1f}元"
        
        change = self.current_amount - total
        if change > 0 and not self.can_give_change(change):
            return False, "零钱不足，请先退币"
        
        self.current_amount -= total
        for idx, qty in self.selected_products.items():
            self.products[idx].stock -= qty
        self.total_income += total
        
        success_msg = f"支付成功！当前余额：{self.current_amount:.1f}元"
        self.selected_products.clear()
        return True, success_msg
    
    def refund_all(self):
        if self.current_amount == 0:
            return "当前没有可退金额"
        
        actual_refund = self.give_change(self.current_amount)
        self.current_amount = 0
        return f"退币成功！退还：{actual_refund:.1f}元"

    def can_give_change(self, amount):
        temp_stock = self.coin_stock.copy()
        remaining = amount
        for coin in self.valid_coins:
            if remaining <= 0.05:
                return True
            count = min(remaining // coin, temp_stock[coin])
            remaining -= count * coin
        return remaining <= 0.05

    def give_change(self, amount):
        remaining = amount
        change_given = 0.0
        for coin in self.valid_coins:
            if remaining <= 0:
                break
            count = min(remaining // coin, self.coin_stock[coin])
            if count > 0:
                self.coin_stock[coin] -= count
                remaining -= count * coin
                change_given += count * coin
        return change_given

    def check_timeout(self):
        if (time.time() - self.last_operation_time) > self.timeout:
            need_clear = False
            if self.selected_products:
                self.selected_products.clear()
                need_clear = True
            if self.current_amount > 0:
                self.refund_all()
                need_clear = True
            return need_clear
        return False

class UnifiedInterface(tk.Tk):
    def __init__(self, vm):
        super().__init__()
        self.vm = vm
        self.admin_password = "123456"
        self.title("智能售货机")
        self.geometry("1200x800")

        self.notebook = ttk.Notebook(self)
        self.user_tab = ttk.Frame(self.notebook)
        self.admin_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.user_tab, text="用户界面")
        self.notebook.add(self.admin_tab, text="管理界面")
        self.notebook.pack(expand=True, fill="both")

        self.setup_user_interface()
        self.setup_admin_interface()
        self.check_timeout()
        self.update_display()

    def setup_user_interface(self):
        main_frame = ttk.Frame(self.user_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)

        product_frame = ttk.LabelFrame(main_frame, text="商品列表", width=400)
        product_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.product_widgets = []
        for i, product in enumerate(self.vm.products):
            frame = ttk.Frame(product_frame)
            frame.pack(padx=10, pady=5, fill=tk.X)
            
            ttk.Label(frame, text=f"{product.name}\n{product.price}元", width=15).pack(side=tk.LEFT)
            ttk.Button(frame, text="+", width=3, 
                      command=lambda i=i: self.add_to_cart(i)).pack(side=tk.LEFT)
            ttk.Button(frame, text="-", width=3,
                      command=lambda i=i: self.remove_from_cart(i)).pack(side=tk.LEFT)
            
            stock_label = ttk.Label(frame, text=f"库存：{product.stock}")
            selected_label = ttk.Label(frame, text="已选：0")
            stock_label.pack(side=tk.LEFT, padx=5)
            selected_label.pack(side=tk.LEFT)
            self.product_widgets.append((stock_label, selected_label))

        control_frame = ttk.LabelFrame(main_frame, text="操作面板")
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.cart_list = tk.Listbox(control_frame, height=15, font=('Arial', 12, 'bold'))
        self.cart_list.pack(pady=10, fill=tk.BOTH, expand=True)

        coin_frame = ttk.Frame(control_frame)
        coin_frame.pack(fill=tk.X, pady=5)
        for coin in self.vm.valid_coins:
            ttk.Button(coin_frame, text=f"{coin}元", 
                      command=lambda c=coin: self.insert_coin(c)).pack(side=tk.LEFT, padx=2)

        info_frame = ttk.Frame(control_frame)
        info_frame.pack(fill=tk.X)
        ttk.Label(info_frame, text="已投金额：").pack(side=tk.LEFT)
        self.amount_label = ttk.Label(info_frame, text="0.0 元")
        self.amount_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(info_frame, text="确认支付", 
                  command=self.process_payment).pack(side=tk.LEFT, padx=5)
        ttk.Button(info_frame, text="全部退币", 
                  command=self.process_refund, style="Danger.TButton").pack(side=tk.RIGHT)

        ttk.Label(info_frame, text="当前余额：").pack(side=tk.LEFT)
        self.balance_label = ttk.Label(info_frame, text="0.0 元", foreground="green")
        self.balance_label.pack(side=tk.LEFT, padx=10)

        self.status_label = ttk.Label(control_frame, text="请选择商品", foreground="blue")
        self.status_label.pack()
        self.timer_label = ttk.Label(control_frame, text="操作剩余时间：300秒")
        self.timer_label.pack()

    def setup_admin_interface(self):
        admin_frame = ttk.Frame(self.admin_tab)
        admin_frame.pack(fill=tk.BOTH, expand=True)

        auth_frame = ttk.Frame(admin_frame)
        auth_frame.pack(pady=20)
    
        ttk.Label(auth_frame, text="管理员密码:").pack(side=tk.LEFT)
        self.pwd_entry = ttk.Entry(auth_frame, show="*", width=15)
        self.pwd_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(auth_frame, text="登录", command=self.verify_admin).pack(side=tk.LEFT)

        self.admin_panel = ttk.Frame(admin_frame)
    
        stock_frame = ttk.LabelFrame(self.admin_panel, text="实时库存监控")
        stock_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(stock_frame, text="商品库存", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.product_stock_labels = []
        for i, product in enumerate(self.vm.products):
            frame = ttk.Frame(stock_frame)
            frame.grid(row=i+1, column=0, sticky=tk.W, pady=2)
            ttk.Label(frame, text=f"{product.name}:", width=15).pack(side=tk.LEFT)
            label = ttk.Label(frame, text=str(product.stock), width=5)
            label.pack(side=tk.LEFT)
            ttk.Button(frame, text="补货", command=lambda idx=i: self.restock_product(idx)).pack(side=tk.LEFT, padx=5)
            self.product_stock_labels.append(label)

        ttk.Label(stock_frame, text="钱币库存", font=('Arial', 12, 'bold')).grid(row=0, column=1, sticky=tk.W)
        self.coin_labels = {}
        for idx, coin in enumerate(sorted(self.vm.valid_coins, reverse=True)):
            frame = ttk.Frame(stock_frame)
            frame.grid(row=idx+1, column=1, sticky=tk.W, pady=2)
            ttk.Label(frame, text=f"{coin}元:", width=8).pack(side=tk.LEFT)
            label = ttk.Label(frame, text=str(self.vm.coin_stock[coin]), width=5)
            label.pack(side=tk.LEFT)
            ttk.Button(frame, text="补充", command=lambda c=coin: self.refill_coin(c)).pack(side=tk.LEFT, padx=5)
            ttk.Button(frame, text="取钱", command=lambda c=coin: self.withdraw_coin(c)).pack(side=tk.LEFT, padx=5)
            self.coin_labels[coin] = label

        alert_frame = ttk.LabelFrame(self.admin_panel, text="系统警报")
        alert_frame.pack(fill=tk.X, padx=10, pady=10)
        self.alert_label = ttk.Label(alert_frame, text="", foreground="red")
        self.alert_label.pack()

        btn_frame = ttk.Frame(self.admin_panel)
        btn_frame.pack(pady=10)
    
        logout_frame = ttk.Frame(self.admin_panel)
        logout_frame.pack(pady=10)
        ttk.Button(logout_frame, text="安全登出", command=self.logout_admin, style="Danger.TButton").pack()

        self.admin_panel.pack_forget()

    def check_timeout(self):
        if self.vm.check_timeout():
            self.update_display()
            messagebox.showwarning("操作超时", "长时间未操作，已清空购物车和余额")
        remaining = self.vm.timeout - (time.time() - self.vm.last_operation_time)
        self.timer_label.config(text=f"操作剩余时间：{max(0, int(remaining))}秒")
        self.after(1000, self.check_timeout)

    def update_display(self):
        total = self.vm.calculate_total()
        
        self.cart_list.delete(0, tk.END)
        for idx, qty in self.vm.selected_products.items():
            product = self.vm.products[idx]
            self.cart_list.insert(tk.END, 
                f"{product.name} ×{qty} ｜单价：{product.price}元｜小计：{product.price*qty:.1f}元"
            )
        self.cart_list.insert(tk.END, f"{'总计：':<15}{total:.1f}元")
        
        self.amount_label.config(text=f"{self.vm.current_amount:.1f} 元")

        self.balance_label.config(text=f"{self.vm.current_amount:.1f} 元")
        
        for i, product in enumerate(self.vm.products):
            self.product_widgets[i][0].config(text=f"库存：{product.stock}")
            self.product_widgets[i][1].config(
                text=f"已选：{self.vm.selected_products.get(i, 0)}"
            )
        
        if hasattr(self, 'coin_labels'):
            for coin, label in self.coin_labels.items():
                label.config(text=str(self.vm.coin_stock[coin]))
            for i, label in enumerate(self.product_stock_labels):
                label.config(text=str(self.vm.products[i].stock))
        
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
        self.alert_label.config(text="\n".join(alerts))

        self.after(1000, self.update_display)

    def add_to_cart(self, product_idx):
        if self.vm.add_to_cart(product_idx):
            self.status_label.config(text="已添加商品到购物车", foreground="green")
            self.update_display()

    def remove_from_cart(self, product_idx):
        if self.vm.remove_from_cart(product_idx):
            self.status_label.config(text="已从购物车移除商品", foreground="orange")
            self.update_display()

    def insert_coin(self, coin):
        self.vm.insert_coin(coin)
        self.status_label.config(text=f"已投入 {coin} 元", foreground="darkgreen")
        self.update_display()

    def process_payment(self):
        success, msg = self.vm.process_payment()
        if success:
            self.amount_label.config(text=f"{self.vm.current_amount:.1f} 元")
            messagebox.showinfo("支付成功", msg)
            self.status_label.config(text="支付成功，可继续购物", foreground="darkblue")
        else:
            messagebox.showerror("支付失败", msg)
            self.status_label.config(text=msg, foreground="red")
        self.update_display()

    def process_refund(self):
        result = self.vm.refund_all()
        messagebox.showinfo("退币结果", result)
        self.status_label.config(text=result, foreground="purple")
        self.update_display()

    def verify_admin(self):
        input_pwd = self.pwd_entry.get()
        if input_pwd == self.admin_password:
            self.admin_panel.pack(fill=tk.BOTH, expand=True)
            self.pwd_entry.delete(0, tk.END)
            messagebox.showinfo("验证成功", "管理员权限已启用")
        else:
            messagebox.showerror("验证失败", "密码错误")
            self.pwd_entry.delete(0, tk.END)

    def logout_admin(self):
        self.admin_panel.pack_forget()
        self.pwd_entry.delete(0, tk.END)
        messagebox.showinfo("已登出", "管理员权限已关闭")
        self.update_display()

    def restock_product(self, product_idx):
        product = self.vm.products[product_idx]
        product.stock = 20
        self.vm.check_alerts()
        messagebox.showinfo("补货完成", f"{product.name}已补充至20件")
        self.update_display()

    def refill_coin(self, coin):
        self.vm.coin_stock[coin] = 20
        self.vm.check_alerts()
        messagebox.showinfo("补充完成", f"{coin}元已补充至20枚")
        self.update_display()

    def withdraw_coin(self, coin):
        if coin == 100:
            self.vm.coin_stock[coin] = 0
        elif self.vm.coin_stock[coin] > 20:
            self.vm.coin_stock[coin] = 20
            messagebox.showinfo("已取钱")
        # else:
            messagebox.showwarning("取钱失败", f"{coin}元不足20枚，无法取钱")
        self.vm.check_alerts()
        self.update_display()


if __name__ == "__main__":
    vm = VendingMachine()
    app = UnifiedInterface(vm)
    app.mainloop()
