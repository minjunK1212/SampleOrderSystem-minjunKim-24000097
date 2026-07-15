class ShipmentView:
    def show_confirmed_orders(self, orders):
        print("-" * 60)
        print("출고 가능 주문 목록 (CONFIRMED)")
        if not orders:
            print("출고 가능한 주문이 없습니다.")
            return
        print(f"{'주문번호':<12}{'고객명':<16}{'시료ID':<10}{'수량':<8}")
        for o in orders:
            print(f"{o.order_id:<12}{o.customer_name:<16}{o.sample_id:<10}{o.quantity:<8}")

    def read_order_id(self):
        return input("출고할 주문번호 (0=뒤로) > ").strip()

    def show_order(self, order):
        print(order)

    def show_message(self, message):
        print(message)
