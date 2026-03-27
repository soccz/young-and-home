# Young & Home - 프로젝트 규칙

## 프로젝트 개요
한국 청년이 처음 집을 구할 때 필요한 모든 것을 AI로 도와주는 Streamlit 앱.
혜택 매칭 → 매물 검색 → 안전 진단 → 계약 → 입주까지 전 과정을 커버.

## 기술 스택
- **Frontend**: Streamlit (Python)
- **AI**: LangChain + LangGraph + OpenAI GPT-4o-mini
- **RAG**: ChromaDB + sentence-transformers (jhgan/ko-sbert-nli)
- **Backend**: FastAPI (미구현, 나중에 추가 예정)
- **Data**: JSON 파일 기반 (data/ 디렉토리)

## 디렉토리 구조
```
Home.py                    # 메인 대시보드 + 온보딩 위저드
pages/                     # Streamlit 멀티페이지
  1_스마트_검색.py          # 매물 + 혜택 AI 검색
  2_👤_내_프로필.py         # 사용자 프로필 (session_state 저장)
  2_🛡️_안전_진단.py        # 등기부 분석 + 깡통전세 자가진단 + SOS
  3_📝_협상_도우미.py       # 협상 메시지 생성
  4_⚖️_법률_상담.py        # 법률 챗봇
  5_💰_금융_계산기.py       # 대출/비교/DSR/생활비 시뮬레이션
  6_📡_모니터링.py          # 등기 변동 감시 (데모)
  7_✅_체크리스트.py        # 집보기/계약/입주 체크리스트
src/
  agents/                  # AI 에이전트
    recommender.py         # 매물+혜택 추천 (LangGraph)
    analyzer.py            # 안전 분석 (LangGraph)
    legal.py               # 법률 상담
    negotiator.py          # 협상 메시지
    finance_agent.py       # 금융 시뮬레이터 (통합)
    finance.py             # deprecated wrapper → finance_agent.py
  rag/                     # RAG 파이프라인
    loader.py              # benefits.json → Document
    retriever.py           # ChromaDB 검색
  ocr/                     # 문서 파싱
    parser.py              # 등기부/계약서 OCR + 위험 분석
  utils/
    ui.py                  # UI 컴포넌트 + 사이드바 + CSS
    lang.py                # i18n (KO/EN)
data/
  welfare/benefits.json    # 정부 혜택 16개
  housing/houses.json      # 매물 35개
  housing/regions_guide.json  # 서울 15구 지역 가이드
  housing/checklists.json  # 체크리스트 (집보기/계약/입주)
  legal/                   # 법령 + 판례
```

## 핵심 규칙

### API 관련
- API(FastAPI)는 아직 미구현. 모든 API 호출 코드는 제거 또는 session_state 저장으로 대체
- `import requests`는 사용하지 않음 (API 없으므로)

### 모델
- 모든 에이전트: `gpt-4o-mini` 통일 (비용 최적화)
- temperature: 0 (결정적 결과)

### 데이터 흐름
- 사용자 프로필은 `st.session_state`에 저장 (user_name, user_status, user_age, user_income, user_assets, user_job_type, user_married, user_location, user_max_deposit, user_max_monthly)
- 페이지 간 데이터 전달은 session_state로
- 온보딩 완료 여부: `st.session_state.onboarding_complete`

### UI
- 모든 페이지는 `setup_page()` + `draw_sidebar()` 호출로 시작
- CSS는 `ui.py`의 `load_css()`에서 중앙 관리
- 카드 UI: `card()` 함수 사용
- i18n: `T()` 함수로 번역 키 조회 (lang.py)
- status 내부 키는 항상 한국어 ("대학생", "직장인" 등), 표시는 언어별

### 코드 스타일
- print() 대신 logging 사용 권장 (현재는 print 혼재)
- 에이전트 내 JSON 파일 로드는 캐시 메서드 사용 (_load_benefits_db, _load_houses)
