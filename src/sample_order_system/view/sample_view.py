class SampleView:
    def show_submenu(self):
        print("-" * 60)
        print("[1] 시료 등록  [2] 시료 목록  [3] 시료 검색  [0] 뒤로")

    def read_choice(self):
        return input("선택 > ").strip()

    def read_new_sample(self):
        sample_id = input("시료 ID > ").strip()
        name = input("이름 > ").strip()
        average_production_time = float(input("평균 생산시간 > ").strip())
        yield_rate = float(input("수율(0~1) > ").strip())
        return sample_id, name, average_production_time, yield_rate

    def read_keyword(self):
        return input("검색어 > ").strip()

    def show_samples(self, samples):
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        print(f"{'ID':<10}{'이름':<24}{'평균생산시간':<14}{'수율':<8}{'재고':<8}")
        for s in samples:
            print(f"{s.sample_id:<10}{s.name:<24}{s.average_production_time:<14}{s.yield_rate:<8}{s.inventory:<8}")

    def show_message(self, message):
        print(message)
