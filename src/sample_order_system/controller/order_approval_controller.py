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
            decision = self.view.read_decision()
            try:
                if decision == "Y":
                    order = order_service.approve_order(self.repository, order_id)
                elif decision == "N":
                    order = order_service.reject_order(self.repository, order_id)
                else:
                    self.view.show_message("올바르지 않은 선택입니다.")
                    continue
                self.view.show_message("처리 완료.")
                self.view.show_order(order)
            except (ValueError, NotImplementedError) as e:
                self.view.show_message(f"처리 실패: {e}")
