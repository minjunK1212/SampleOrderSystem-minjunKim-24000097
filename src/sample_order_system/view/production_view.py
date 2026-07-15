class ProductionView:
    def show_submenu(self):
        print("-" * 60)
        print("[1] 생산 라인 조회  [2] 생산 완료 처리  [0] 뒤로")

    def read_choice(self):
        return input("선택 > ").strip()

    def show_current_job(self, job, average_production_time):
        print("현재 생산 작업")
        if job is None:
            print("  진행 중인 작업이 없습니다.")
            return
        total_production_time = average_production_time * job.production_quantity
        print(f"  주문번호: {job.order_id}  시료ID: {job.sample_id}")
        print(f"  부족수량: {job.required_quantity}  실생산량: {job.production_quantity}")
        print(f"  총 생산 시간: {total_production_time}")

    def show_waiting_queue(self, waiting_items):
        print("대기 중인 작업 (FIFO)")
        if not waiting_items:
            print("  대기 중인 작업이 없습니다.")
            return
        for idx, item in enumerate(waiting_items, start=1):
            print(
                f"  {idx}. 주문번호: {item.order_id}  시료ID: {item.sample_id}  "
                f"부족수량: {item.required_quantity}  실생산량: {item.production_quantity}"
            )

    def show_order(self, order):
        print(order)

    def show_message(self, message):
        print(message)
