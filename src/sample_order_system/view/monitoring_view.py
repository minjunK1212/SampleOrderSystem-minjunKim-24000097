class MonitoringView:
    def show_submenu(self):
        print("-" * 60)
        print("[1] 주문량 확인  [2] 재고량 확인  [0] 뒤로")

    def read_choice(self):
        return input("선택 > ").strip()

    def show_order_counts(self, counts):
        print("상태별 주문 현황")
        for status, count in counts.items():
            print(f"  {status.value:<12}{count}건")

    def show_inventory_report(self, rows):
        if not rows:
            print("등록된 시료가 없습니다.")
            return
        print(f"{'시료ID':<10}{'이름':<24}{'재고':<8}{'유효주문':<10}{'상태':<6}")
        for row in rows:
            print(f"{row.sample_id:<10}{row.name:<24}{row.inventory:<8}{row.valid_quantity:<10}{row.status:<6}")

    def show_message(self, message):
        print(message)
