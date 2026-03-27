# Young & Home

**청년을 위한 AI 주거 어시스턴트**

집 구하기, 계약 안전 확인, 정부 혜택 매칭까지 — 아무것도 모르는 상태에서 혼자 집 구할 때 옆에서 도와주는 AI입니다.

## 기능

| 기능 | 설명 |
|------|------|
| **스마트 검색** | 나이·소득·자산 입력하면 받을 수 있는 정부 혜택 + 조건 맞는 매물 추천 |
| **안전 진단** | 등기부등본 분석 — 깡통전세·전세사기 패턴 자동 감지 |
| **협상 도우미** | 집주인에게 보낼 협상 메시지 자동 생성 |
| **법률 상담** | 주택임대차보호법 기반 법률 질문 답변 |
| **금융 계산기** | 청년 버팀목·중소기업 청년 전세대출 한도 계산, 전세 vs 월세 비교 |
| **모니터링** | 관심 매물 등기 변동 모니터링 |

## 시작하기

```bash
# 1. 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. API 키 설정
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 입력

# 4. 실행
streamlit run Home.py
```

> 첫 실행 시 한국어 임베딩 모델(~400MB)이 자동 다운로드됩니다.

## 필요한 것

- **OpenAI API 키** 하나면 모든 AI 기능 동작
- 금융 계산기는 API 없이도 사용 가능

## 기술 스택

- **Frontend**: Streamlit (멀티페이지)
- **Backend**: FastAPI
- **AI/Agent**: LangChain, LangGraph, GPT-4o-mini
- **RAG**: ChromaDB, sentence-transformers (jhgan/ko-sbert-nli)
- **Automation**: n8n
- **Infra**: Docker
