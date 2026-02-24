"""
경로 관리 모듈 (PyInstaller frozen 모드 호환)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- APP_DIR: 실행파일(.exe) 위치 — 데이터(input/output/config) 기준
- RESOURCE_DIR: 번들 리소스 위치 — 템플릿 등 읽기전용 파일 기준
"""
import sys
from pathlib import Path


def _get_app_dir() -> Path:
    """실행 파일 위치 (frozen) 또는 소스코드 디렉토리 (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _get_resource_dir() -> Path:
    """번들 리소스 위치 (frozen: _MEIPASS, dev: 소스 디렉토리)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


APP_DIR = _get_app_dir()
RESOURCE_DIR = _get_resource_dir()

INPUT_DIR = APP_DIR / "input"
OUTPUT_DIR = APP_DIR / "output"
TEMPLATE_DIR = RESOURCE_DIR / "templates"
CONFIG_PATH = APP_DIR / "config_local.json"
