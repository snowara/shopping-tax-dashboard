#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 셀러 세무 자료 수집 대시보드 — 원클릭 설치
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  셀러 세무 자료 수집 대시보드 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Python 확인
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ Python이 설치되어 있지 않습니다."
    echo "   https://www.python.org/downloads/ 에서 설치해주세요."
    exit 1
fi

echo "✅ Python: $($PYTHON --version)"

# 2. 가상환경 생성
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 가상환경 생성 중..."
    $PYTHON -m venv venv
fi

# 3. 가상환경 활성화
source venv/bin/activate

# 4. 패키지 설치
echo ""
echo "📦 필수 패키지 설치 중..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 5. Playwright 선택 설치
echo ""
read -p "🌐 Playwright 설치? (셀러센터 자동 열기 기능, y/N): " install_pw
if [[ "$install_pw" =~ ^[Yy]$ ]]; then
    echo "📦 Playwright 설치 중..."
    pip install -q playwright
    playwright install chromium
    echo "✅ Playwright 설치 완료"
else
    echo "⏭️  Playwright 건너뜀 (나중에 pip install playwright로 설치 가능)"
fi

# 6. 디렉토리 생성
mkdir -p input output

# 7. 실행
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 설치 완료! 대시보드를 시작합니다."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

$PYTHON app.py
