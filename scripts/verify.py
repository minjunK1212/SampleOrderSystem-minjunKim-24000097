import compileall
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_syntax():
    print("== 문법/컴파일 검사 (src/, tests/) ==")
    ok_src = compileall.compile_dir(str(ROOT / "src"), quiet=1)
    ok_tests = compileall.compile_dir(str(ROOT / "tests"), quiet=1)
    ok = ok_src and ok_tests
    print("OK" if ok else "FAILED")
    return ok


def run_pytest():
    print("== pytest 전체 실행 ==")
    result = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=str(ROOT))
    return result.returncode == 0


def run_ruff():
    print("== ruff 검사 ==")
    if importlib.util.find_spec("ruff") is None:
        print("ruff가 설치되어 있지 않아 건너뜁니다.")
        return True
    result = subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=str(ROOT))
    return result.returncode == 0


def main():
    steps = [
        ("syntax", check_syntax),
        ("pytest", run_pytest),
        ("ruff", run_ruff),
    ]
    failed = [name for name, check in steps if not check()]

    print()
    if failed:
        print(f"Harness FAILED: {', '.join(failed)}")
        return 1
    print("Harness PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
