from sample_order_system.service import production_service


class ProductionController:
    def __init__(self, repository, view):
        self.repository = repository
        self.view = view

    def run(self):
        while True:
            self.view.show_submenu()
            choice = self.view.read_choice()
            if choice == "1":
                self._show_queue()
            elif choice == "2":
                self._complete()
            elif choice == "0":
                break
            else:
                self.view.show_message("올바르지 않은 선택입니다.")

    def _show_queue(self):
        queue = production_service.list_production_queue(self.repository)
        current = queue[0] if queue else None
        waiting = queue[1:]
        average_production_time = 0
        if current is not None:
            sample = self.repository.get_sample(current.sample_id)
            average_production_time = sample.average_production_time
        self.view.show_current_job(current, average_production_time)
        self.view.show_waiting_queue(waiting)

    def _complete(self):
        try:
            order = production_service.complete_current_production(self.repository)
            self.view.show_message("생산 완료 처리되었습니다.")
            self.view.show_order(order)
        except ValueError as e:
            self.view.show_message(f"생산 완료 처리 실패: {e}")
