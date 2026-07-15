import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sample_order_system.controller.main_controller import MainController  # noqa: E402


def main():
    MainController().run()


if __name__ == "__main__":
    main()
