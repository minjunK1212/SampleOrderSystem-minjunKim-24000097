from sample_order_system.service import shipment_service


class ShipmentController:
    def __init__(self, repository, view):
        self.repository = repository
        self.view = view

    def run(self):
        while True:
            self.view.show_confirmed_orders(shipment_service.list_confirmed_orders(self.repository))
            order_id = self.view.read_order_id()
            if order_id == "0":
                break
            try:
                released = shipment_service.release_order(self.repository, order_id)
                self.view.show_message("출고 처리 완료.")
                self.view.show_order(released)
            except ValueError as e:
                self.view.show_message(f"출고 처리 실패: {e}")
