from sample_order_system.service import order_service


class OrderController:
    def __init__(self, repository, view):
        self.repository = repository
        self.view = view

    def run(self):
        while True:
            self.view.show_submenu()
            choice = self.view.read_choice()
            if choice == "1":
                self._reserve()
            elif choice == "0":
                break
            else:
                self.view.show_message("올바르지 않은 선택입니다.")

    def _reserve(self):
        try:
            sample_id, customer_name, quantity = self.view.read_new_order()
            order = order_service.reserve_order(self.repository, sample_id, customer_name, quantity)
            self.view.show_message("주문 접수 완료.")
            self.view.show_order(order)
        except ValueError as e:
            self.view.show_message(f"주문 접수 실패: {e}")
