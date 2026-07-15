from sample_order_system.service import order_service


class OrderApprovalController:
    def __init__(self, repository, view):
        self.repository = repository
        self.view = view

    def run(self):
        while True:
            self.view.show_reserved_orders(order_service.list_reserved_orders(self.repository))
            order_id = self.view.read_order_id()
            if order_id == "0":
                break
            try:
                rejected = order_service.reject_order(self.repository, order_id)
                self.view.show_message("거절 완료.")
                self.view.show_order(rejected)
            except ValueError as e:
                self.view.show_message(f"거절 실패: {e}")
