import sys
from pathlib import Path

# src/ 레이아웃이므로 테스트가 sample_order_system 패키지를 임포트할 수 있도록 경로를 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
