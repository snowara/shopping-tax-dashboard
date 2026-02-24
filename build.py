"""
PyInstaller 빌드 스크립트
━━━━━━━━━━━━━━━━━━━━━━━━━━
사용법:
    python build.py            (기본 빌드)
    python build.py --onefile  (단일 실행파일)
    python build.py --clean    (빌드 캐시 삭제 후 빌드)

결과물:
    dist/세무자료수집/         (onedir 모드)
    dist/세무자료수집.exe      (onefile 모드, Windows)
    dist/세무자료수집          (onefile 모드, macOS)
"""
import io
import os
import sys
import shutil
import argparse
from pathlib import Path

# Windows 콘솔 한글 인코딩 문제 방지
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

APP_NAME = "세무자료수집"
ENTRY = "app.py"
BASE_DIR = Path(__file__).parent


def build(onefile=False, clean=False):
    # PyInstaller 설치 확인
    try:
        import PyInstaller.__main__
    except ImportError:
        print("PyInstaller가 설치되어 있지 않습니다.")
        print("  pip install pyinstaller")
        sys.exit(1)

    if clean:
        for d in ["build", "dist"]:
            p = BASE_DIR / d
            if p.exists():
                shutil.rmtree(p)
                print(f"  삭제: {p}")
        spec = BASE_DIR / f"{APP_NAME}.spec"
        if spec.exists():
            spec.unlink()
            print(f"  삭제: {spec}")

    # OS별 경로 구분자
    sep = ";" if sys.platform == "win32" else ":"

    args = [
        str(BASE_DIR / ENTRY),
        f"--name={APP_NAME}",
        f"--add-data=templates{sep}templates",
        "--console",
        "--noconfirm",
        "--clean",
        # 숨김 import (flask, openpyxl 등은 자동 감지됨)
        "--hidden-import=config",
        "--hidden-import=paths",
        "--hidden-import=tax_package",
        "--hidden-import=vat_checker",
        "--hidden-import=platform_opener",
        # 불필요 모듈 제외 (용량 줄이기)
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=notebook",
        "--exclude-module=IPython",
    ]

    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    # 아이콘 (있으면 사용)
    icon_path = BASE_DIR / "icon.ico"
    if icon_path.exists():
        args.append(f"--icon={icon_path}")

    print()
    print("=" * 50)
    print(f"  {APP_NAME} 빌드 시작")
    print(f"  모드: {'단일파일' if onefile else '폴더'}")
    print(f"  OS: {sys.platform}")
    print("=" * 50)
    print()

    PyInstaller.__main__.run(args)

    # 빌드 결과 안내
    if onefile:
        if sys.platform == "win32":
            exe_path = BASE_DIR / "dist" / f"{APP_NAME}.exe"
        else:
            exe_path = BASE_DIR / "dist" / APP_NAME
    else:
        exe_path = BASE_DIR / "dist" / APP_NAME

    print()
    print("=" * 50)
    if exe_path.exists():
        print(f"  빌드 완료!")
        print(f"  경로: {exe_path}")
        if not onefile:
            print(f"\n  배포: dist/{APP_NAME}/ 폴더를 통째로 복사하세요.")
            print(f"  실행: dist/{APP_NAME}/{APP_NAME} (또는 .exe)")
    else:
        print("  빌드 실패. 위 로그를 확인하세요.")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{APP_NAME} 빌드")
    parser.add_argument("--onefile", action="store_true", help="단일 실행파일 (느리지만 배포 간편)")
    parser.add_argument("--clean", action="store_true", help="빌드 캐시 삭제 후 빌드")
    args = parser.parse_args()
    build(onefile=args.onefile, clean=args.clean)
