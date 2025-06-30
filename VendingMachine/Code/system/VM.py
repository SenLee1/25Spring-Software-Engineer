import time
from collections import defaultdict


class Product:
    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

class VendingMachine:
    def __init__(self):
        self.products = [
            Product("巧克力", 4.0, 15),
            Product("可乐", 3.5, 20),
            Product("矿泉水", 2.0, 15),
            Product("薯片", 5.0, 1),
            Product("辣条", 1.0, 0)
        ]
        self.admin_password = "123456"
        self.valid_coins = [100, 50, 20, 10, 5, 1, 0.5]
        self.coin_stock = {coin: 5 for coin in self.valid_coins}
        self.insert_stock = {coin: 0 for coin in self.valid_coins}
        self.coin_threshold = {
            100: 0, 50: 5, 20: 10, 
            10: 20, 5: 20, 1: 20, 0.5: 10
        }
        self.current_amount = 0.0
        self.selected_products = defaultdict(int)
        self.last_operation_time = time.time()
        self.admin_last_active_time = 0
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
            if self.coin_stock[coin] > 20
        ]

    def add_to_cart(self, product_idx):
        if product_idx not in [0, 1, 2, 3, 4]:
            return False
        product = self.products[product_idx]
        if product.stock > 0 and (product.stock > self.selected_products[product_idx]):
            self.selected_products[product_idx] += 1
            self.last_operation_time = time.time()
            return True
        return False

    def remove_from_cart(self, product_idx):
        if product_idx not in [0, 1, 2, 3, 4]:
            return False
        if product_idx in self.selected_products:
            self.selected_products[product_idx] -= 1
            if self.selected_products[product_idx] <= 0:
                del self.selected_products[product_idx]
            self.last_operation_time = time.time()
            return True
        return False

    def calculate_total(self):
        return sum(
            self.products[idx].price * qty 
            for idx, qty in self.selected_products.items()
        )

    def insert_coin(self, coin):
        if coin in self.valid_coins:
            self.current_amount += coin
            self.insert_stock[coin] += 1
            self.last_operation_time = time.time()

    def process_payment(self):
        total = self.calculate_total()
        self.last_operation_time = time.time()
        if total == 0:
            return False, {}, "请先选购商品"
        if self.current_amount < total:
            return False, {}, f"金额不足，还需{total - self.current_amount:.1f}元"
            
        change = self.current_amount - total
        if change > 0 and not self.can_give_change(change):
            return False, {}, "零钱不足，请先退币"
            
        self.current_amount -= total
        for idx, qty in self.selected_products.items():
            self.products[idx].stock -= qty

        success_msg = f"支付成功！当前余额：{self.current_amount:.1f}元"
        raw_products = dict(self.selected_products)
        self.selected_products.clear()
        products = {idx + 1: qty for idx, qty in raw_products.items() if qty > 0}
        return True, products, success_msg
    
    def refund_all(self):
        self.last_operation_time = time.time()
        if self.current_amount == 0:
            return False, {}, "当前没有可退金额"
        
        actual_refund, change_result = self.give_change(self.current_amount)
        self.current_amount = 0
        return (self.current_amount == 0), change_result, f"退币成功！退还：{actual_refund:.1f}元"

    # greedy edtion
    def can_give_change(self, amount):
        temp_stock = self.coin_stock.copy()
        for coin in self.valid_coins:
            temp_stock[coin] += self.insert_stock[coin]
        remaining = amount
        for coin in self.valid_coins:
            if remaining <= 0.05:
                return True
            count = min(remaining // coin, temp_stock[coin])
            remaining -= count * coin
        return remaining <= 0.05

    def give_change(self, amount):
        for coin in self.valid_coins:
            self.coin_stock[coin] += self.insert_stock[coin]
            self.insert_stock[coin] = 0
        remaining = amount
        change_given = 0
        change_result = {coin: 0 for coin in self.valid_coins}
        for coin in self.valid_coins:
            if remaining <= 0:
                break
            count = min(remaining // coin, self.coin_stock[coin])
            if count > 0:
                self.coin_stock[coin] -= count
                remaining -= count * coin
                change_given += count * coin
                change_result[coin] = int(count)
        return change_given, change_result
    
    # # dp edition
    # def can_give_change(self, amount):
    #     amount = round(amount * 2)
    #     coins = [int(c * 2) for c in self.valid_coins]
    #     stock = self.coin_stock
    #     dp = [False] * (amount + 1)
    #     dp[0] = True
    #     for i, coin in enumerate(coins):
    #         max_count = stock[self.valid_coins[i]]
    #         for j in range(amount, coin - 1, -1):
    #             for k in range(1, max_count + 1):
    #                 if j >= k * coin and dp[j - k * coin]:
    #                     dp[j] = True

    #     return dp[amount]
    
    # def give_change(self, amount):
    #     amount = round(amount * 2)
    #     coins = [int(c * 2) for c in self.valid_coins]
    #     real_coins = self.valid_coins
    #     stock = self.coin_stock
    #     n = len(coins)
    #     dp = [None] * (amount + 1)
    #     dp[0] = {}
    #     for i in range(n):
    #         coin = coins[i]
    #         coin_val = real_coins[i]
    #         max_count = stock[coin_val]
    #         for j in range(amount, -1, -1):
    #             if dp[j] is not None:
    #                 for k in range(1, max_count + 1):
    #                     new_amt = j + coin * k
    #                     if new_amt > amount:
    #                         break
    #                     if dp[new_amt] is None:
    #                         dp[new_amt] = dp[j].copy()
    #                         dp[new_amt][coin_val] = dp[new_amt].get(coin_val, 0) + k
    #     if dp[amount] is None:
    #         return 0, {}
    #     for denom, count in dp[amount].items():
    #         self.coin_stock[denom] -= count

    #     total = sum(denom * count for denom, count in dp[amount].items())
    #     return total, dp[amount]

    def check_timeout(self):
        need_clear = (time.time() - self.last_operation_time) > self.timeout
        if need_clear:
            if self.selected_products:
                self.selected_products.clear()
            if self.current_amount > 0:
                for coin in self.valid_coins:
                    self.coin_stock[coin] += self.insert_stock[coin]
                    self.insert_stock[coin] = 0
                self.current_amount = 0
        return need_clear

    def verify_admin(self, input_pwd):
        if input_pwd == self.admin_password:
            return True
        return False
    
    def restock_product(self, product_idx):
        if product_idx not in [0, 1, 2, 3, 4]:
            return False
        product = self.products[product_idx]
        product.stock = 20
        self.check_alerts()
        return True

    def refill_coin(self, coin):
        if coin in self.valid_coins:
            if self.coin_stock[coin] < self.coin_threshold[coin]:
                self.coin_stock[coin] = self.coin_threshold[coin]
        else: 
            return False
        self.check_alerts()
        return True

    def withdraw_coin(self, coin):
        if coin in self.valid_coins: 
            if self.coin_stock[coin] > self.coin_threshold[coin]:
                self.coin_stock[coin] = self.coin_threshold[coin]
        else:
            return False
        self.check_alerts()
        return True
        
