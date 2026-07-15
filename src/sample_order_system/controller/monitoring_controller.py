from sample_order_system.service import monitoring_service


class MonitoringController:
    def __init__(self, repository, view):
        self.repository = repository
        self.view = view

    def run(self):
        while True:
            self.view.show_submenu()
            choice = self.view.read_choice()
            if choice == "1":
                self.view.show_order_counts(monitoring_service.get_order_status_counts(self.repository))
            elif choice == "2":
                self.view.show_inventory_report(monitoring_service.get_sample_inventory_report(self.repository))
            elif choice == "0":
                break
            else:
                self.view.show_message("올바르지 않은 선택입니다.")
