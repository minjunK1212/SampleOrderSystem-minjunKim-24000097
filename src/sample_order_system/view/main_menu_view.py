class MainMenuView:
    def show_summary(self, summary):
        print(
            f"등록 시료 {summary.sample_count}종  총 재고 {summary.total_inventory}  "
            f"전체 주문 {summary.order_count}건  생산라인 대기 {summary.production_queue_count}건"
        )

    def show_menu(self):
        print("=" * 60)
        print("반도체 시료 생산주문관리 시스템")
        print("=" * 60)
        print("[1] 시료 관리")
        print("[2] 시료 주문")
        print("[3] 주문 승인/거절")
        print("[4] 생산 라인")
        print("[5] 출고 처리")
        print("[6] 모니터링")
        print("[0] 종료")

    def read_choice(self):
        return input("선택 > ").strip()

    def show_message(self, message):
        print(message)
