from sample_order_system.service.main_menu_summary_service import MainMenuSummary
from sample_order_system.view.main_menu_view import MainMenuView


def test_show_summary_prints_all_fields(capsys):
    view = MainMenuView()
    summary = MainMenuSummary(sample_count=2, total_inventory=30, order_count=3, production_queue_count=1)

    view.show_summary(summary)

    output = capsys.readouterr().out
    assert "2" in output
    assert "30" in output
    assert "3" in output
    assert "1" in output
