class OrderView:
    def show_submenu(self):
        print("-" * 60)
        print("[1] 주문 접수  [0] 뒤로")

    def read_choice(self):
        return input("선택 > ").strip()

    def read_new_order(self):
        sample_id = input("시료 ID > ").strip()
        customer_name = input("고객명 > ").strip()
        quantity = int(input("주문 수량 > ").strip())
        return sample_id, customer_name, quantity

    def show_order(self, order):
        print(order)

    def show_message(self, message):
        print(message)
