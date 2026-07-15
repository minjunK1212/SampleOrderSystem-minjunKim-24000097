class MainMenuView:
    def show_menu(self):
        print("=" * 60)
        print("반도체 시료 생산주문관리 시스템")
        print("=" * 60)
        print("[1] 시료 관리")
        print("[2] 시료 주문")
        print("[0] 종료")

    def read_choice(self):
        return input("선택 > ").strip()

    def show_message(self, message):
        print(message)
