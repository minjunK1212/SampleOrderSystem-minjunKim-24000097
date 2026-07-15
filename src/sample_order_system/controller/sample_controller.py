from sample_order_system.service import sample_service


class SampleController:
    def __init__(self, repository, view):
        self.repository = repository
        self.view = view

    def run(self):
        while True:
            self.view.show_submenu()
            choice = self.view.read_choice()
            if choice == "1":
                self._register()
            elif choice == "2":
                self.view.show_samples(sample_service.list_samples(self.repository))
            elif choice == "3":
                keyword = self.view.read_keyword()
                self.view.show_samples(sample_service.search_samples(self.repository, keyword))
            elif choice == "0":
                break
            else:
                self.view.show_message("올바르지 않은 선택입니다.")

    def _register(self):
        try:
            sample_id, name, average_production_time, yield_rate = self.view.read_new_sample()
            sample = sample_service.register_sample(
                self.repository, sample_id, name, average_production_time, yield_rate
            )
            self.view.show_message(f"등록 완료: {sample}")
        except ValueError as e:
            self.view.show_message(f"등록 실패: {e}")
