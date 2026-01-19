# Young & Home (청년 안심 주거&복지 코디네이터)

> 2026 서강대 AI 겨울캠프 해커톤 출품작

**"집 구하기부터 계약, 그리고 혜택까지. AI가 떠먹여주는 청년 주거 토탈 케어"**

## 🎯 프로젝트 개요

사회초년생과 대학생을 위한 AI 기반 주거 지원 에이전트입니다.

### 핵심 기능
1. **Phase 0 - 맞춤 추천**: 사용자 상황(소득, 자산)에 맞는 SH/LH 공공주택 및 정부 지원 혜택 매칭
2. **Phase 1 - 안전 진단**: 등기부등본/계약서 분석을 통한 전세사기 위험도 진단
3. **Phase 2 - 협상 지원**: 집주인에게 보낼 특약 수정 요청 메시지 자동 생성
4. **Phase 3 - 모니터링**: 거주 중 등기 변동(압류, 소유자 변경) 실시간 알림

## 📖 Documentation
- **[사용자 가이드 (User Guide)](USER_GUIDE.md)**: 기능별 상세 사용법
- **Tech Stack**: Streamlit, LangChain, LangGraph, FastAPI, ChromaDB

## 🛠️ 기술 스택

| Category | Tech |
|----------|------|
| Agent Framework | LangChain, LangGraph |
| Automation | n8n |
| Knowledge Base | ChromaDB (VectorDB), RAG |
| Vision/OCR | GPT-4o Vision / Upstage OCR |
| Frontend | Streamlit |
| Backend | FastAPI |

## 📁 프로젝트 구조

```
young-and-home/
├── README.md
├── requirements.txt
├── data/                    # 샘플 데이터 (공고, 등기부등본 등)
│   ├── welfare/             # 복지/금융 혜택 데이터
│   └── samples/             # 테스트용 문서 샘플
├── src/
│   ├── agents/              # LangGraph 에이전트 (5개)
│   │   ├── recommender.py   # 추천 에이전트
│   │   ├── analyzer.py      # 위험 분석 에이전트
│   │   ├── negotiator.py    # 협상 지원 에이전트
│   │   ├── finance.py       # 금융 계산 에이전트
│   │   └── legal.py         # 법률 상담 에이전트
│   ├── rag/                 # RAG 파이프라인
│   │   ├── loader.py
│   │   └── retriever.py
│   ├── ocr/                 # 문서 인식
│   │   └── parser.py
│   └── utils/
├── n8n/                     # n8n 워크플로우 JSON
└── app.py                   # Streamlit 메인 앱
```

## 👥 팀 역할 분담

| Role | 담당 영역 |
|------|----------|
| **Agent Architect** | LangGraph 설계, 프롬프트 엔지니어링, RAG 구축 |
| **Data/Backend Engineer** | n8n 자동화, 외부 API 연동, 데이터 파이프라인 |
| **Frontend/Product** | Streamlit UI, 시나리오 기획, 발표 자료 |

## 🚀 Quick Start

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 등 설정

# 3. 앱 실행
streamlit run app.py
```

## 📜 License

MIT License
