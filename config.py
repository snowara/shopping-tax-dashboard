"""
설정 관리 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
config_local.json을 읽고/쓰고, 첫 실행 시 대화형 설정 마법사를 제공합니다.
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config_local.json"

DEFAULTS = {
    "company_name": "내 쇼핑몰",
    "representative": "홍길동",
    "accountant_name": "세무사사무소",
    "accountant_method": "이메일 송부",
    "corp_tax_year": 2025,
    "corp_tax_period": "2025.01.01 ~ 2025.12.31",
    "corp_filing_deadline": "2026.03.31",
    "corp_submission_deadline": "2026.03.02",
    "platforms": [
        "smartstore", "coupang", "11st", "talkstore",
        "zigzag", "lotteon", "toss", "alwayz",
    ],
    "port": 5000,
}


def load_config() -> dict:
    """config_local.json 로딩. 없으면 DEFAULTS 반환."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # DEFAULTS 키 중 빠진 것 보충
        merged = {**DEFAULTS, **saved}
        return merged
    return dict(DEFAULTS)


def save_config(cfg: dict):
    """config_local.json 저장."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def is_configured() -> bool:
    """설정 파일이 존재하는지 확인."""
    return CONFIG_PATH.exists()


def run_setup_wizard() -> dict:
    """터미널 대화형 설정 마법사."""
    print()
    print("=" * 50)
    print("  세무 자료 수집 대시보드 — 초기 설정")
    print("=" * 50)
    print()
    print("  몇 가지 정보를 입력해주세요.")
    print("  (엔터만 누르면 기본값이 적용됩니다)")
    print()

    cfg = dict(DEFAULTS)

    cfg["company_name"] = (
        input(f"  회사명 [{DEFAULTS['company_name']}]: ").strip()
        or DEFAULTS["company_name"]
    )
    cfg["representative"] = (
        input(f"  대표자명 [{DEFAULTS['representative']}]: ").strip()
        or DEFAULTS["representative"]
    )
    cfg["accountant_name"] = (
        input(f"  세무사/세무법인명 [{DEFAULTS['accountant_name']}]: ").strip()
        or DEFAULTS["accountant_name"]
    )
    cfg["accountant_method"] = (
        input(f"  자료 전달 방식 [{DEFAULTS['accountant_method']}]: ").strip()
        or DEFAULTS["accountant_method"]
    )

    # 법인세 연도
    year_input = input(f"  법인세 귀속 연도 [{DEFAULTS['corp_tax_year']}]: ").strip()
    if year_input.isdigit():
        cfg["corp_tax_year"] = int(year_input)
        cfg["corp_tax_period"] = f"{year_input}.01.01 ~ {year_input}.12.31"
        cfg["corp_filing_deadline"] = f"{int(year_input)+1}.03.31"
        cfg["corp_submission_deadline"] = f"{int(year_input)+1}.03.02"

    # 포트
    port_input = input(f"  서버 포트 [{DEFAULTS['port']}]: ").strip()
    if port_input.isdigit():
        cfg["port"] = int(port_input)

    # 플랫폼 선택
    all_platforms = {
        "smartstore": "스마트스토어",
        "coupang": "쿠팡",
        "11st": "11번가",
        "talkstore": "톡스토어",
        "zigzag": "지그재그",
        "lotteon": "롯데온",
        "toss": "토스쇼핑",
        "alwayz": "올웨이즈",
    }
    print()
    print("  사용 중인 쇼핑몰을 선택하세요 (쉼표 구분, 엔터=전체):")
    for i, (pid, pname) in enumerate(all_platforms.items(), 1):
        print(f"    {i}. {pname}")

    platform_input = input("  선택 [전체]: ").strip()
    if platform_input:
        nums = [n.strip() for n in platform_input.split(",")]
        keys = list(all_platforms.keys())
        selected = []
        for n in nums:
            if n.isdigit() and 1 <= int(n) <= len(keys):
                selected.append(keys[int(n) - 1])
        if selected:
            cfg["platforms"] = selected

    save_config(cfg)
    print()
    print("  ✅ 설정 완료! config_local.json에 저장되었습니다.")
    print(f"     회사명: {cfg['company_name']}")
    print(f"     대표자: {cfg['representative']}")
    print(f"     세무사: {cfg['accountant_name']}")
    print(f"     플랫폼: {len(cfg['platforms'])}개")
    print()

    return cfg
