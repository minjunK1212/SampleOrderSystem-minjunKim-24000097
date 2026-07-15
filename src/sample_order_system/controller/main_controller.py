from pathlib import Path

from sample_order_system.controller.order_approval_controller import OrderApprovalController
from sample_order_system.controller.order_controller import OrderController
from sample_order_system.controller.production_controller import ProductionController
from sample_order_system.controller.sample_controller import SampleController
from sample_order_system.controller.shipment_controller import ShipmentController
from sample_order_system.repository.order_system_repository import OrderSystemRepository
from sample_order_system.view.main_menu_view import MainMenuView
from sample_order_system.view.order_approval_view import OrderApprovalView
from sample_order_system.view.order_view import OrderView
from sample_order_system.view.production_view import ProductionView
from sample_order_system.view.sample_view import SampleView
from sample_order_system.view.shipment_view import ShipmentView

DEFAULT_DATA_PATH = Path("data/sample_management.json")


class MainController:
    def __init__(self, data_path=DEFAULT_DATA_PATH):
        self.repository = OrderSystemRepository(data_path)
        self.main_menu_view = MainMenuView()
        self.sample_controller = SampleController(self.repository, SampleView())
        self.order_controller = OrderController(self.repository, OrderView())
        self.order_approval_controller = OrderApprovalController(self.repository, OrderApprovalView())
        self.production_controller = ProductionController(self.repository, ProductionView())
        self.shipment_controller = ShipmentController(self.repository, ShipmentView())

    def run(self):
        while True:
            self.main_menu_view.show_menu()
            choice = self.main_menu_view.read_choice()
            if choice == "1":
                self.sample_controller.run()
            elif choice == "2":
                self.order_controller.run()
            elif choice == "3":
                self.order_approval_controller.run()
            elif choice == "4":
                self.production_controller.run()
            elif choice == "5":
                self.shipment_controller.run()
            elif choice == "0":
                self.main_menu_view.show_message("시스템을 종료합니다.")
                break
            else:
                self.main_menu_view.show_message("올바르지 않은 선택입니다.")
