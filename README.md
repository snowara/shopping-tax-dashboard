# 셀러 세무 자료 수집 대시보드

쇼핑몰 셀러를 위한 **부가세 + 법인세 자료 수집 웹 대시보드**.

세무사에게 전달할 자료를 드래그&드롭으로 수집하고, 체크리스트와 카톡 메시지를 자동 생성합니다.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)

## 주요 기능

- **부가세 자료 수집** — 8개 쇼핑몰(스마트스토어, 쿠팡, 11번가 등) 부가세 신고자료 드래그&드롭 업로드
- **법인세 자료 수집** — 필수 10개 + 기타 8개 항목 체계적 관리
- **셀러센터 바로가기** — 각 플랫폼 셀러센터 원클릭 오픈 (Playwright 선택 설치)
- **세무사 전달 패키지** — 체크리스트 엑셀 + 카톡 메시지 자동 생성
- **부가세 셀프 체크** — 이카운트 vs 홈택스 데이터 대조

## 3분 설치 가이드

### macOS / Linux

```bash
git clone https://github.com/snowara/shopping-tax-dashboard.git
cd shopping-tax-dashboard
bash setup.sh
```

### 수동 설치

```bash
git clone https://github.com/snowara/shopping-tax-dashboard.git
cd shopping-tax-dashboard

# 가상환경 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 실행
python3 app.py
```

첫 실행 시 **설정 마법사**가 자동으로 실행됩니다. 회사명, 대표자명, 세무사명을 입력하면 끝!

## 사용법

```bash
# 기본 실행 (현재 분기)
python3 app.py

# 특정 분기 지정
python3 app.py --quarter 2026Q1

# 포트 변경
python3 app.py --port 8080

# 설정 재실행
python3 app.py --setup
```

브라우저에서 `http://localhost:5000` 접속.

## 파일 구조

```
├── app.py              ← 메인 대시보드 서버
├── config.py           ← 설정 관리 (초기 설정 마법사)
├── config_local.json   ← 내 설정 (자동 생성, git 제외)
├── tax_package.py      ← 체크리스트·카톡 메시지 생성
├── vat_checker.py      ← 부가세 셀프 체크 (이카운트↔홈택스 대조)
├── platform_opener.py  ← Playwright 셀러센터 오픈 (선택)
├── templates/
│   └── dashboard.html  ← 웹 대시보드 UI
├── input/              ← 업로드된 세무 자료 (git 제외)
├── output/             ← 생성된 체크리스트·메시지 (git 제외)
├── setup.sh            ← 원클릭 설치 스크립트
└── requirements.txt
```

## 설정 항목 (config_local.json)

| 항목 | 설명 | 기본값 |
|------|------|--------|
| `company_name` | 회사명 | 내 쇼핑몰 |
| `representative` | 대표자명 | 홍길동 |
| `accountant_name` | 세무사/세무법인명 | 세무사사무소 |
| `accountant_method` | 자료 전달 방식 | 이메일 송부 |
| `corp_tax_year` | 법인세 귀속 연도 | 2025 |
| `platforms` | 사용 쇼핑몰 목록 | 전체 8개 |
| `port` | 서버 포트 | 5000 |

## 지원 쇼핑몰

| 플랫폼 | 부가세 메뉴 | 파일형식 |
|--------|------------|----------|
| 스마트스토어 | 정산관리 > 부가세 신고 내역 | 엑셀 |
| 쿠팡 | 정산 > 부가세 신고 내역 | 엑셀 |
| 11번가 | 정산관리 > 부가세 신고 내역 | PDF/엑셀 |
| 톡스토어 | 정산관리 > 부가세 신고자료 | 엑셀 |
| 지그재그 | 정산관리 > 국내 부가세 참고자료 | 엑셀 |
| 롯데온 | 정산관리 > 부가세 신고자료 조회 | 엑셀 |
| 토스쇼핑 | 쇼핑 > 정산내역 | 확인필요 |
| 올웨이즈 | 정산 > 세금계산서 조회 | 확인필요 |

## 부가세 셀프 체크 (vat_checker.py)

이카운트 매출/매입장과 홈택스 세금계산서를 비교하여 누락·불일치를 찾아줍니다.

```bash
python3 vat_checker.py --quarter 2026Q1
```

`input/` 폴더에 아래 파일을 넣어주세요:
- `ecount_매출.xlsx` — 이카운트 매출장
- `ecount_매입.xlsx` — 이카운트 매입장
- `hometax_매출.xlsx` — 홈택스 전자세금계산서 매출 목록
- `hometax_매입.xlsx` — 홈택스 전자세금계산서 매입 목록

## License

MIT
