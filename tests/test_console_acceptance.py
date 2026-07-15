import json
import os
import subprocess
import sys
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / "main.py"


def test_full_console_acceptance_scenario(tmp_path):
    stdin_text = (
        "1\n1\nS-001\nSilicon Wafer 8-inch\n0.5\n0.8\n0\n"  # 시료 등록 후 시료 관리 뒤로가기
        "2\n1\nS-001\nCustomerA\n50\n0\n"  # 주문 접수(재고 부족) 후 뒤로가기
        "3\nORD-0001\nY\n0\n"  # 승인 -> PRODUCING, 뒤로가기
        "4\n2\n0\n"  # 생산 완료 처리 -> CONFIRMED, 뒤로가기
        "5\nORD-0001\n0\n"  # 출고 -> RELEASE, 뒤로가기
        "6\n1\n2\n0\n"  # 모니터링: 주문량 확인, 재고량 확인, 뒤로가기
        "0\n"  # 종료
    )

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(MAIN_PY)],
        input=stdin_text,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "RELEASE" in result.stdout

    data_path = tmp_path / "data" / "sample_management.json"
    saved = json.loads(data_path.read_text(encoding="utf-8"))
    assert saved["orders"][0]["status"] == "RELEASE"
    assert saved["production_queue"] == []
