"""
세무 자료 수집 웹 대시보드 (부가세 + 법인세)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 부가세: 8개 쇼핑몰 자료 드래그&드롭 수집 + Playwright 셀러센터 오픈
- 법인세: 필수 10개 + 기타 8개 항목 자료 드래그&드롭 수집

사용법:
    python3 app.py                          (기본: 현재 분기)
    python3 app.py --quarter 2026Q1         (특정 분기)
    python3 app.py --port 8080              (포트 변경)
    python3 app.py --setup                  (설정 마법사 재실행)
"""
import argparse
import asyncio
import json
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file

from config import load_config, is_configured, run_setup_wizard

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_DIR = BASE_DIR / "templates"

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 플랫폼 정의 (tax_package.py와 동일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLATFORMS = [
    {
        "id": "smartstore",
        "name": "스마트스토어",
        "seller_url": "https://sell.smartstore.naver.com/",
        "menu": "정산관리 > 부가세 신고 내역",
        "file_format": "엑셀(.xlsx)",
        "filename": "스마트스토어",
        "icon": "🟢",
    },
    {
        "id": "coupang",
        "name": "쿠팡",
        "seller_url": "https://wing.coupang.com/",
        "menu": "정산 > 부가세 신고 내역",
        "file_format": "엑셀(.xlsx)",
        "filename": "쿠팡",
        "icon": "🟠",
    },
    {
        "id": "11st",
        "name": "11번가",
        "seller_url": "https://soffice.11st.co.kr/",
        "menu": "정산관리 > 부가세 신고 내역",
        "file_format": "PDF/엑셀",
        "filename": "11번가",
        "icon": "🔴",
    },
    {
        "id": "talkstore",
        "name": "톡스토어",
        "seller_url": "https://business.kakao.com/",
        "menu": "정산관리 > 부가세 신고자료",
        "file_format": "엑셀(.xlsx)",
        "filename": "톡스토어",
        "icon": "🟡",
    },
    {
        "id": "zigzag",
        "name": "지그재그",
        "seller_url": "https://partner.kakaostyle.com/",
        "menu": "정산관리 > 국내 부가세 참고자료",
        "file_format": "엑셀(.xlsx)",
        "filename": "지그재그",
        "icon": "🩷",
    },
    {
        "id": "lotteon",
        "name": "롯데온",
        "seller_url": "https://partner.lotteon.com/",
        "menu": "정산관리 > 부가세 신고자료 조회",
        "file_format": "엑셀(.xlsx)",
        "filename": "롯데온",
        "icon": "🔵",
    },
    {
        "id": "toss",
        "name": "토스쇼핑",
        "seller_url": "https://shopping-seller.toss.im/",
        "menu": "쇼핑 > 정산내역",
        "file_format": "확인 필요",
        "filename": "토스쇼핑",
        "icon": "🔷",
    },
    {
        "id": "alwayz",
        "name": "올웨이즈",
        "seller_url": "https://seller.alwayz.co/",
        "menu": "정산 > 세금계산서 조회",
        "file_format": "확인 필요",
        "filename": "올웨이즈",
        "icon": "🟣",
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 법인세 제출 항목 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORP_TAX_ITEMS = [
    # ── 필수 제출 자료 (10개) ──
    {
        "id": "corp_stock",
        "name": "주식 관련 자료",
        "category": "required",
        "description": "주식 변동 내역, 주주 명부, 법인 등기부 등본",
        "detail": "2025년도 주식 변동 내역(주식양수도계약서, 주식증여계약서 포함), 2025.12.31 기준 주주 명부, 법인 등기부 등본",
        "source": "법원 인터넷등기소 / 수동",
        "filename": "주식관련자료",
        "icon": "📊",
    },
    {
        "id": "corp_bank",
        "name": "법인 통장·카드 내역",
        "category": "required",
        "description": "미연동 법인 통장 및 법인카드 내역 엑셀",
        "detail": "보통 예금, 정기 예적금, 적립식 펀드, 외화 통장 등",
        "source": "은행 인터넷뱅킹",
        "filename": "법인통장카드내역",
        "icon": "🏦",
    },
    {
        "id": "corp_interest",
        "name": "이자소득원천징수영수증",
        "category": "required",
        "description": "법인 명의 통장 이자 수익 원천징수영수증",
        "detail": "법인 명의 통장에서 발생한 이자 수익(해당 은행에서 발급) 및 기타 대여금에 대한 이자 수익",
        "source": "은행 발급",
        "filename": "이자소득원천징수",
        "icon": "💰",
    },
    {
        "id": "corp_subsidy",
        "name": "국고 보조금·장려금",
        "category": "required",
        "description": "국가 보조금 협약서 및 입금 내역, 판매 장려금",
        "detail": "국가에서 지급 받은 보조금(협약서 및 보조금 입금 내역), 거래처로부터 지급 받은 판매 장려금 등",
        "source": "관련 기관 / 거래처",
        "filename": "국고보조금장려금",
        "icon": "🏛️",
    },
    {
        "id": "corp_vehicle",
        "name": "법인 차량 관련 자료",
        "category": "required",
        "description": "차량 등록증, 운행기록부, 리스료/할부금 상환표",
        "detail": "법인 차량 등록증, 차량 운행 기록부, 차량 할부/리스 구입한 경우 리스료/할부금 상환표",
        "source": "리스사 / 수동",
        "filename": "법인차량자료",
        "icon": "🚗",
    },
    {
        "id": "corp_inventory",
        "name": "재고명세서",
        "category": "required",
        "description": "2025.12.31 현재 재고 금액",
        "detail": "2025년 12월 31일 기준 재고 금액 명세서",
        "source": "ERP / 수동",
        "filename": "재고명세서",
        "icon": "📦",
    },
    {
        "id": "corp_import",
        "name": "수입통관서류",
        "category": "required",
        "description": "수입 정산서, 수입신고필증 등",
        "detail": "수입 정산서, 수입신고필증 등 수입 관련 서류",
        "source": "관세청 / 관세사",
        "filename": "수입통관서류",
        "icon": "🚢",
    },
    {
        "id": "corp_pension",
        "name": "퇴직연금 명세서",
        "category": "required",
        "description": "DB형/DC형 퇴직연금 불입내역 및 잔고증명",
        "detail": "DB형, DC형 등의 퇴직연금을 불입하고 있는 경우 2025년 불입내역 및 2025.12.31 잔고증명",
        "source": "퇴직연금 운용사",
        "filename": "퇴직연금명세서",
        "icon": "👴",
    },
    {
        "id": "corp_localtax",
        "name": "지방세 세목별 과세증명서",
        "category": "required",
        "description": "위택스 또는 정부24에서 발급",
        "detail": "위텍스(www.wetax.go.kr) 또는 정부24(www.gov.kr) 사이트에서 발급 가능",
        "source": "위택스 / 정부24",
        "filename": "지방세과세증명서",
        "icon": "🏢",
    },
    {
        "id": "corp_taxcredit",
        "name": "세액공제·감면 확인 서류",
        "category": "required",
        "description": "기업부설연구소 인증서, 벤처인증서 등",
        "detail": "기업부설연구소/연구전담부서 인증서, 벤처인증서 등",
        "source": "해당 기관",
        "filename": "세액공제감면서류",
        "icon": "📜",
    },
    # ── 기타 제출 자료 (8개) ──
    {
        "id": "corp_lease",
        "name": "임대차 계약서",
        "category": "optional",
        "description": "2025년도 중 변동이 있는 경우",
        "detail": "사무실, 창고 등 임대차 계약서",
        "source": "수동",
        "filename": "임대차계약서",
        "icon": "🏠",
    },
    {
        "id": "corp_receivable",
        "name": "외상매출금·매입금 잔액명세서",
        "category": "optional",
        "description": "거래처별 미수금/미지급금 잔액",
        "detail": "거래처별 외상매출금(미수금), 외상매입금(미지급금) 잔액명세서",
        "source": "ERP / 수동",
        "filename": "외상매출매입잔액",
        "icon": "📋",
    },
    {
        "id": "corp_loan",
        "name": "법인 대출금 내역",
        "category": "optional",
        "description": "대출금 변동, 이자지급, 잔고증명서",
        "detail": "법인명의 대출금 변동 내역, 이자지급내역, 대출금잔고증명서",
        "source": "은행",
        "filename": "법인대출금내역",
        "icon": "💳",
    },
    {
        "id": "corp_bill",
        "name": "어음거래 내역",
        "category": "optional",
        "description": "전자어음, 할인내역, 부도수표, 장기미회수채권",
        "detail": "전자어음포함, 할인내역, 부도수표 및 어음, 장기미회수채권 등",
        "source": "은행 / 수동",
        "filename": "어음거래내역",
        "icon": "📝",
    },
    {
        "id": "corp_receipt",
        "name": "기타 경비사용 영수증",
        "category": "optional",
        "description": "기부금영수증, 전화/전기요금, 건물관리비, 현금영수증 등",
        "detail": "기부금영수증(법인명의로 기부한 경우), 전화요금고지서, 전기세고지서, 건물관리비, 일반 현금사용 영수증, 청첩장 등",
        "source": "수동",
        "filename": "기타경비영수증",
        "icon": "🧾",
    },
    {
        "id": "corp_insurance",
        "name": "보험료내역서",
        "category": "optional",
        "description": "자동차 보험료, 화재보험료 등",
        "detail": "자동차 보험료, 화재보험료 등",
        "source": "보험사",
        "filename": "보험료내역서",
        "icon": "🛡️",
    },
    {
        "id": "corp_rnd",
        "name": "연구인력개발비 내역",
        "category": "optional",
        "description": "연구개발전담부서 직원 급여, 연구개발 비용",
        "detail": "연구개발전담부서 직원의 급여, 연구개발 비용 등",
        "source": "수동",
        "filename": "연구인력개발비",
        "icon": "🔬",
    },
    {
        "id": "corp_investment",
        "name": "투자자산 내역",
        "category": "optional",
        "description": "지분 투자내역, 금융상품, 해외현지법인 명세",
        "detail": "해당 법인에서 다른 회사의 지분을 갖고 있는 경우 지분 투자내역 및 기타 금융상품 투자내역, 해외지분투자가 있는 경우 해외현지법인 명세",
        "source": "수동",
        "filename": "투자자산내역",
        "icon": "📈",
    },
]


def get_corp_tax_info(cfg):
    """config에서 법인세 신고 정보 dict 생성."""
    return {
        "year": cfg["corp_tax_year"],
        "period": cfg["corp_tax_period"],
        "filing_deadline": cfg["corp_filing_deadline"],
        "submission_deadline": cfg["corp_submission_deadline"],
        "method": cfg["accountant_method"],
        "accountant": cfg["accountant_name"],
    }


# 현재 분기 (서버 시작 시 설정)
CURRENT_QUARTER = None


def get_current_quarter():
    now = datetime.now()
    q = (now.month - 1) // 3 + 1
    return f"{now.year}Q{q}"


def get_quarter_dir(quarter=None):
    q = quarter or CURRENT_QUARTER or get_current_quarter()
    d = INPUT_DIR / q
    d.mkdir(exist_ok=True)
    return d


def get_corp_dir(year=None):
    """법인세 자료 저장 디렉토리"""
    cfg = load_config()
    y = year or str(cfg["corp_tax_year"])
    d = INPUT_DIR / f"법인세_{y}"
    d.mkdir(exist_ok=True)
    return d


def scan_collected_files(quarter=None):
    """부가세 수집된 파일 현황 스캔"""
    q_dir = get_quarter_dir(quarter)
    results = []

    for p in PLATFORMS:
        files = []
        if q_dir.exists():
            for f in q_dir.iterdir():
                if f.is_file() and f.suffix.lower() in ['.xlsx', '.xls', '.pdf', '.csv', '.zip']:
                    if p["filename"] in f.name:
                        files.append({
                            "name": f.name,
                            "size": f.stat().st_size,
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M"),
                        })

        results.append({
            **p,
            "collected": len(files) > 0,
            "files": files,
        })

    return results


def scan_corp_files(year=None):
    """법인세 수집된 파일 현황 스캔"""
    c_dir = get_corp_dir(year)
    results = []

    for item in CORP_TAX_ITEMS:
        files = []
        if c_dir.exists():
            for f in c_dir.iterdir():
                if f.is_file() and f.suffix.lower() in ['.xlsx', '.xls', '.pdf', '.csv', '.zip', '.jpg', '.jpeg', '.png', '.hwp', '.doc', '.docx']:
                    if item["filename"] in f.name:
                        files.append({
                            "name": f.name,
                            "size": f.stat().st_size,
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M"),
                        })

        results.append({
            **item,
            "collected": len(files) > 0,
            "files": files,
        })

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Flask 라우트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/")
def index():
    cfg = load_config()
    quarter = request.args.get("quarter", CURRENT_QUARTER or get_current_quarter())
    return render_template(
        "dashboard.html",
        quarter=quarter,
        company_name=cfg["company_name"],
        accountant_name=cfg["accountant_name"],
        accountant_method=cfg["accountant_method"],
    )


@app.route("/api/status")
def api_status():
    """수집 현황 API"""
    quarter = request.args.get("quarter", CURRENT_QUARTER or get_current_quarter())
    platforms = scan_collected_files(quarter)
    collected = sum(1 for p in platforms if p["collected"])

    return jsonify({
        "quarter": quarter,
        "platforms": platforms,
        "collected": collected,
        "total": len(PLATFORMS),
        "complete": collected == len(PLATFORMS),
    })


@app.route("/api/upload/<platform_id>", methods=["POST"])
def api_upload(platform_id):
    """파일 업로드 (드래그&드롭)"""
    quarter = request.form.get("quarter", CURRENT_QUARTER or get_current_quarter())
    q_dir = get_quarter_dir(quarter)

    # 플랫폼 찾기
    platform = next((p for p in PLATFORMS if p["id"] == platform_id), None)
    if not platform:
        return jsonify({"status": "error", "message": "알 수 없는 플랫폼"}), 400

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "파일이 없습니다"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "파일명이 비어있습니다"}), 400

    # 확장자 확인
    ext = Path(file.filename).suffix.lower()
    allowed = ['.xlsx', '.xls', '.pdf', '.csv', '.zip']
    if ext not in allowed:
        return jsonify({
            "status": "error",
            "message": f"지원하지 않는 형식: {ext} (허용: {', '.join(allowed)})"
        }), 400

    # 저장: {플랫폼명}_{원본파일명} (복수 파일 지원)
    original_name = Path(file.filename).stem
    save_name = f"{platform['filename']}_{original_name}{ext}"
    save_path = q_dir / save_name

    # 동일 파일명 존재 시 번호 부여
    counter = 1
    while save_path.exists():
        save_name = f"{platform['filename']}_{original_name}_{counter}{ext}"
        save_path = q_dir / save_name
        counter += 1

    file.save(str(save_path))

    return jsonify({
        "status": "success",
        "message": f"{platform['name']} 파일 저장 완료",
        "filename": save_name,
        "size": save_path.stat().st_size,
    })


@app.route("/api/delete/<platform_id>", methods=["DELETE"])
def api_delete(platform_id):
    """업로드된 파일 삭제 (filename 파라미터: 개별 삭제, 없으면 전체 삭제)"""
    quarter = request.args.get("quarter", CURRENT_QUARTER or get_current_quarter())
    target_file = request.args.get("filename")
    q_dir = get_quarter_dir(quarter)

    platform = next((p for p in PLATFORMS if p["id"] == platform_id), None)
    if not platform:
        return jsonify({"status": "error", "message": "알 수 없는 플랫폼"}), 400

    deleted = []
    for f in q_dir.iterdir():
        if f.is_file() and platform["filename"] in f.name:
            if target_file and f.name != target_file:
                continue
            f.unlink()
            deleted.append(f.name)

    return jsonify({
        "status": "success",
        "message": f"{len(deleted)}개 파일 삭제",
        "deleted": deleted,
    })


@app.route("/api/open/<platform_id>", methods=["POST"])
def api_open_platform(platform_id):
    """Playwright로 셀러센터 열기"""
    quarter = request.form.get("quarter", CURRENT_QUARTER or get_current_quarter())
    q_dir = get_quarter_dir(quarter)

    platform = next((p for p in PLATFORMS if p["id"] == platform_id), None)
    if not platform:
        return jsonify({"status": "error", "message": "알 수 없는 플랫폼"}), 400

    # Playwright를 별도 스레드에서 비동기 실행
    def run_playwright():
        try:
            from platform_opener import open_platform_simple
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                open_platform_simple(platform["name"], str(q_dir))
            )
            loop.close()
            if result["status"] == "error":
                print(f"  ❌ {result['message']}")
        except ImportError:
            print("  ⚠️ playwright 미설치 — pip install playwright && playwright install chromium")
        except Exception as e:
            print(f"  ❌ Playwright 오류: {e}")

    thread = threading.Thread(target=run_playwright, daemon=True)
    thread.start()

    return jsonify({
        "status": "success",
        "message": f"{platform['name']} 셀러센터 여는 중...",
    })


@app.route("/api/package", methods=["POST"])
def api_create_package():
    """세무사 전달 패키지 생성"""
    quarter = request.form.get("quarter", CURRENT_QUARTER or get_current_quarter())
    q_dir = get_quarter_dir(quarter)

    # 수집 현황 체크
    platforms = scan_collected_files(quarter)
    collected = [p for p in platforms if p["collected"]]
    missing = [p for p in platforms if not p["collected"]]

    # tax_package.py의 기능 호출
    try:
        from tax_package import create_vat_checklist, create_kakao_message
        checklist_path = create_vat_checklist(quarter)
        kakao_path, kakao_text = create_kakao_message("vat", quarter)
    except Exception as e:
        checklist_path = None
        kakao_text = f"[오류] 패키지 생성 실패: {e}"

    return jsonify({
        "status": "success",
        "quarter": quarter,
        "collected": len(collected),
        "missing": [p["name"] for p in missing],
        "checklist": str(checklist_path) if checklist_path else None,
        "kakao_message": kakao_text,
        "files": [
            {"platform": p["name"], "files": [f["name"] for f in p["files"]]}
            for p in collected
        ],
    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 법인세 API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/api/corp/status")
def api_corp_status():
    """법인세 자료 수집 현황"""
    cfg = load_config()
    corp_tax_info = get_corp_tax_info(cfg)
    year = request.args.get("year", str(corp_tax_info["year"]))
    items = scan_corp_files(year)
    required_items = [i for i in items if i["category"] == "required"]
    optional_items = [i for i in items if i["category"] == "optional"]
    req_collected = sum(1 for i in required_items if i["collected"])
    opt_collected = sum(1 for i in optional_items if i["collected"])

    return jsonify({
        "year": year,
        "info": corp_tax_info,
        "items": items,
        "required_collected": req_collected,
        "required_total": len(required_items),
        "optional_collected": opt_collected,
        "optional_total": len(optional_items),
        "total_collected": req_collected + opt_collected,
        "total": len(CORP_TAX_ITEMS),
    })


@app.route("/api/corp/upload/<item_id>", methods=["POST"])
def api_corp_upload(item_id):
    """법인세 파일 업로드"""
    cfg = load_config()
    corp_tax_info = get_corp_tax_info(cfg)
    year = request.form.get("year", str(corp_tax_info["year"]))
    c_dir = get_corp_dir(year)

    item = next((i for i in CORP_TAX_ITEMS if i["id"] == item_id), None)
    if not item:
        return jsonify({"status": "error", "message": "알 수 없는 항목"}), 400

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "파일이 없습니다"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "파일명이 비어있습니다"}), 400

    ext = Path(file.filename).suffix.lower()
    allowed = ['.xlsx', '.xls', '.pdf', '.csv', '.zip', '.jpg', '.jpeg', '.png', '.hwp', '.doc', '.docx']
    if ext not in allowed:
        return jsonify({
            "status": "error",
            "message": f"지원하지 않는 형식: {ext}"
        }), 400

    # 저장: {항목명}_{원본파일명} (복수 파일 지원)
    original_name = Path(file.filename).stem
    save_name = f"{item['filename']}_{original_name}{ext}"
    save_path = c_dir / save_name

    # 동일 파일명 존재 시 번호 부여
    counter = 1
    while save_path.exists():
        save_name = f"{item['filename']}_{original_name}_{counter}{ext}"
        save_path = c_dir / save_name
        counter += 1

    file.save(str(save_path))

    return jsonify({
        "status": "success",
        "message": f"{item['name']} 파일 저장 완료",
        "filename": save_name,
        "size": save_path.stat().st_size,
    })


@app.route("/api/corp/delete/<item_id>", methods=["DELETE"])
def api_corp_delete(item_id):
    """법인세 파일 삭제 (filename 파라미터: 개별 삭제, 없으면 전체 삭제)"""
    cfg = load_config()
    corp_tax_info = get_corp_tax_info(cfg)
    year = request.args.get("year", str(corp_tax_info["year"]))
    target_file = request.args.get("filename")
    c_dir = get_corp_dir(year)

    item = next((i for i in CORP_TAX_ITEMS if i["id"] == item_id), None)
    if not item:
        return jsonify({"status": "error", "message": "알 수 없는 항목"}), 400

    deleted = []
    for f in c_dir.iterdir():
        if f.is_file() and item["filename"] in f.name:
            if target_file and f.name != target_file:
                continue
            f.unlink()
            deleted.append(f.name)

    return jsonify({
        "status": "success",
        "message": f"{len(deleted)}개 파일 삭제",
        "deleted": deleted,
    })


@app.route("/api/corp/package", methods=["POST"])
def api_corp_package():
    """법인세 세무사 전달 패키지"""
    cfg = load_config()
    corp_tax_info = get_corp_tax_info(cfg)
    year = request.form.get("year", str(corp_tax_info["year"]))
    items = scan_corp_files(year)
    collected = [i for i in items if i["collected"]]
    missing_req = [i for i in items if not i["collected"] and i["category"] == "required"]
    missing_opt = [i for i in items if not i["collected"] and i["category"] == "optional"]

    # 카톡 메시지 생성
    lines = [
        f"[{cfg['company_name']}] {year}년 귀속 법인세 자료",
        "=" * 30,
        "",
        f"■ 수집 완료: {len(collected)}개 항목",
    ]
    for c in collected:
        lines.append(f"  ✅ {c['name']}")

    if missing_req:
        lines.append(f"\n■ 필수 미제출: {len(missing_req)}개")
        for m in missing_req:
            lines.append(f"  ❌ {m['name']}")

    if missing_opt:
        lines.append(f"\n■ 기타 미제출: {len(missing_opt)}개")
        for m in missing_opt:
            lines.append(f"  ☐ {m['name']} (해당시)")

    lines.extend([
        "",
        f"■ 제출 기한: {corp_tax_info['submission_deadline']}",
        f"■ 신고 기한: {corp_tax_info['filing_deadline']}",
        "",
        "첨부 파일 확인 부탁드립니다.",
        "",
        "━" * 30,
        f"{cfg['company_name']} {cfg['representative']}",
    ])

    kakao_text = "\n".join(lines)

    # 카톡 메시지 파일 저장
    kakao_path = OUTPUT_DIR / f"법인세_카톡메시지_{year}.txt"
    kakao_path.write_text(kakao_text, encoding="utf-8")

    return jsonify({
        "status": "success",
        "year": year,
        "collected": len(collected),
        "missing_required": [i["name"] for i in missing_req],
        "missing_optional": [i["name"] for i in missing_opt],
        "kakao_message": kakao_text,
        "files": [
            {"item": i["name"], "files": [f["name"] for f in i["files"]]}
            for i in collected
        ],
    })


@app.route("/api/quarters")
def api_quarters():
    """사용 가능한 분기 목록"""
    quarters = []
    if INPUT_DIR.exists():
        for d in sorted(INPUT_DIR.iterdir(), reverse=True):
            if d.is_dir() and len(d.name) == 6 and d.name[4] == "Q":
                quarters.append(d.name)

    # 현재 분기가 없으면 추가
    current = CURRENT_QUARTER or get_current_quarter()
    if current not in quarters:
        quarters.insert(0, current)

    return jsonify({"quarters": quarters, "current": current})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    global CURRENT_QUARTER

    parser = argparse.ArgumentParser(description="세무 자료 수집 대시보드")
    parser.add_argument("--quarter", default=None, help="분기 (예: 2026Q1)")
    parser.add_argument("--port", type=int, default=None, help="서버 포트")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    parser.add_argument("--setup", action="store_true", help="설정 마법사 실행")
    args = parser.parse_args()

    # 설정 마법사 (--setup 또는 첫 실행)
    if args.setup or not is_configured():
        run_setup_wizard()

    cfg = load_config()
    corp_tax_info = get_corp_tax_info(cfg)

    port = args.port or cfg.get("port", 5000)
    CURRENT_QUARTER = args.quarter or get_current_quarter()
    get_quarter_dir()  # 분기 폴더 생성

    print("=" * 50)
    print(f"  {cfg['company_name']} 세무 자료 수집 대시보드")
    print(f"  부가세: {CURRENT_QUARTER}")
    print(f"  법인세: {corp_tax_info['year']}년 귀속 (제출기한: {corp_tax_info['submission_deadline']})")
    print(f"  URL:  http://localhost:{port}")
    print("=" * 50)

    # 부가세 현황
    platforms = scan_collected_files()
    collected = sum(1 for p in platforms if p["collected"])
    print(f"\n  [부가세] {collected}/{len(PLATFORMS)}")
    for p in platforms:
        status = "✅" if p["collected"] else "☐ "
        files = ", ".join(f["name"] for f in p["files"]) if p["files"] else "미수집"
        print(f"    {status} {p['name']:12s} {files}")

    # 법인세 현황
    corp_items = scan_corp_files()
    req = [i for i in corp_items if i["category"] == "required"]
    opt = [i for i in corp_items if i["category"] == "optional"]
    req_c = sum(1 for i in req if i["collected"])
    opt_c = sum(1 for i in opt if i["collected"])
    print(f"\n  [법인세] 필수 {req_c}/{len(req)} · 기타 {opt_c}/{len(opt)}")

    print(f"\n  브라우저에서 http://localhost:{port} 접속하세요.\n")

    app.run(host="0.0.0.0", port=port, debug=args.debug)


if __name__ == "__main__":
    main()
