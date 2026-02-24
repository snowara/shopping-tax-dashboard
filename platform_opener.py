"""
Playwright 기반 쇼핑몰 셀러센터 부가세 페이지 자동 오픈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
각 플랫폼의 셀러센터를 열고, 로그인 후 부가세 메뉴까지 자동 이동.
로그인은 사용자가 직접 처리 (2FA, 캡차 등 자동화 불가).

사용법:
    from platform_opener import open_platform
    await open_platform("스마트스토어")
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent

# 각 플랫폼별 셀러센터 URL + 부가세 메뉴 네비게이션 정보
PLATFORM_CONFIG = {
    "스마트스토어": {
        "name": "스마트스토어",
        "login_url": "https://sell.smartstore.naver.com/",
        "steps": [
            {"action": "wait_for_login", "check_url": "sell.smartstore.naver.com", "check_element": None},
            {"action": "navigate", "url": "https://sell.smartstore.naver.com/#/naverpay/sale/vat"},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산관리 > 부가세 신고 내역",
    },
    "쿠팡": {
        "name": "쿠팡",
        "login_url": "https://wing.coupang.com/",
        "steps": [
            {"action": "wait_for_login", "check_url": "wing.coupang.com", "check_element": None},
            {"action": "click", "selector": "text=정산", "optional": True},
            {"action": "wait", "seconds": 1},
            {"action": "click", "selector": "text=부가세 신고 내역", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산 > 부가세 신고 내역",
    },
    "11번가": {
        "name": "11번가",
        "login_url": "https://soffice.11st.co.kr/",
        "steps": [
            {"action": "wait_for_login", "check_url": "soffice.11st.co.kr", "check_element": None},
            {"action": "click", "selector": "text=정산관리", "optional": True},
            {"action": "wait", "seconds": 1},
            {"action": "click", "selector": "text=부가세 신고 내역", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산관리 > 부가세 신고 내역",
    },
    "톡스토어": {
        "name": "톡스토어",
        "login_url": "https://business.kakao.com/",
        "steps": [
            {"action": "wait_for_login", "check_url": "business.kakao.com", "check_element": None},
            {"action": "click", "selector": "text=정산관리", "optional": True},
            {"action": "wait", "seconds": 1},
            {"action": "click", "selector": "text=부가세", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산관리 > 부가세 신고자료",
    },
    "지그재그": {
        "name": "지그재그",
        "login_url": "https://partner.kakaostyle.com/",
        "steps": [
            {"action": "wait_for_login", "check_url": "partner.kakaostyle.com", "check_element": None},
            {"action": "click", "selector": "text=정산관리", "optional": True},
            {"action": "wait", "seconds": 1},
            {"action": "click", "selector": "text=부가세", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산관리 > 국내 부가세 참고자료",
    },
    "롯데온": {
        "name": "롯데온",
        "login_url": "https://partner.lotteon.com/",
        "steps": [
            {"action": "wait_for_login", "check_url": "partner.lotteon.com", "check_element": None},
            {"action": "click", "selector": "text=정산관리", "optional": True},
            {"action": "wait", "seconds": 1},
            {"action": "click", "selector": "text=부가세", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산관리 > 부가세 신고자료 조회",
    },
    "토스쇼핑": {
        "name": "토스쇼핑",
        "login_url": "https://shopping-seller.toss.im/",
        "steps": [
            {"action": "wait_for_login", "check_url": "shopping-seller.toss.im", "check_element": None},
            {"action": "click", "selector": "text=정산", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "쇼핑 > 정산내역",
    },
    "올웨이즈": {
        "name": "올웨이즈",
        "login_url": "https://seller.alwayz.co/",
        "steps": [
            {"action": "wait_for_login", "check_url": "seller.alwayz.co", "check_element": None},
            {"action": "click", "selector": "text=정산", "optional": True},
            {"action": "wait", "seconds": 1},
            {"action": "click", "selector": "text=세금계산서", "optional": True},
            {"action": "wait", "seconds": 2},
        ],
        "description": "정산 > 세금계산서 조회",
    },
}


async def open_platform(platform_name: str, download_dir: str = None):
    """
    지정된 플랫폼의 셀러센터를 열고 부가세 페이지까지 이동.

    Args:
        platform_name: 플랫폼 이름 (예: "스마트스토어")
        download_dir: 다운로드 경로 (None이면 기본 input 폴더)

    Returns:
        dict: {"status": "success"/"error", "message": str, "browser": browser_obj}
    """
    config = PLATFORM_CONFIG.get(platform_name)
    if not config:
        return {"status": "error", "message": f"지원하지 않는 플랫폼: {platform_name}"}

    if download_dir is None:
        download_dir = str(BASE_DIR / "input")

    try:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            viewport=None,
            accept_downloads=True,
        )
        page = await context.new_page()

        # 셀러센터 로그인 페이지 열기
        await page.goto(config["login_url"], wait_until="domcontentloaded", timeout=30000)

        # 단계별 실행
        for step in config["steps"]:
            action = step["action"]

            if action == "wait_for_login":
                # 사용자가 로그인할 때까지 대기 (최대 5분)
                print(f"  ⏳ {platform_name} 로그인을 완료해주세요...")
                try:
                    await page.wait_for_url(
                        f"**/{step['check_url']}/**",
                        timeout=300000,
                    )
                except Exception:
                    # URL 변경이 없어도 계속 진행 (이미 로그인된 경우)
                    pass
                print(f"  ✅ {platform_name} 로그인 감지")

            elif action == "navigate":
                await page.goto(step["url"], wait_until="domcontentloaded", timeout=15000)

            elif action == "click":
                try:
                    element = page.locator(step["selector"]).first
                    await element.click(timeout=5000)
                except Exception:
                    if not step.get("optional"):
                        raise
                    print(f"  ⚠️ 메뉴를 찾지 못함: {step['selector']} (수동 이동 필요)")

            elif action == "wait":
                await asyncio.sleep(step["seconds"])

        # 다운로드 이벤트 대기 설정
        async def handle_download(download):
            path = Path(download_dir) / download.suggested_filename
            await download.save_as(str(path))
            print(f"  📥 다운로드 완료: {path.name}")

        page.on("download", handle_download)

        return {
            "status": "success",
            "message": f"{platform_name} 부가세 페이지 열림 — {config['description']}",
            "browser": browser,
            "page": page,
            "pw": pw,
        }

    except Exception as e:
        return {"status": "error", "message": f"{platform_name} 열기 실패: {str(e)}"}


async def open_platform_simple(platform_name: str, download_dir: str = None):
    """
    간단 버전: 셀러센터 로그인 페이지만 열기 (메뉴 자동 클릭 없음).
    대시보드에서 [열기] 버튼 클릭 시 사용.
    """
    config = PLATFORM_CONFIG.get(platform_name)
    if not config:
        return {"status": "error", "message": f"지원하지 않는 플랫폼: {platform_name}"}

    if download_dir is None:
        download_dir = str(BASE_DIR / "input")

    try:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            viewport=None,
            accept_downloads=True,
        )
        page = await context.new_page()
        await page.goto(config["login_url"], wait_until="domcontentloaded", timeout=30000)

        # 다운로드 자동 저장
        async def handle_download(download):
            path = Path(download_dir) / download.suggested_filename
            await download.save_as(str(path))
            print(f"  📥 다운로드: {path.name}")

        page.on("download", handle_download)

        return {
            "status": "success",
            "message": f"{platform_name} 셀러센터 열림",
            "browser": browser,
            "page": page,
            "pw": pw,
        }

    except Exception as e:
        return {"status": "error", "message": f"{platform_name} 열기 실패: {str(e)}"}


def get_platform_names():
    """등록된 플랫폼 이름 목록 반환"""
    return list(PLATFORM_CONFIG.keys())


def get_platform_info(platform_name: str):
    """플랫폼 설정 정보 반환"""
    return PLATFORM_CONFIG.get(platform_name)
