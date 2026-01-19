"""
Young & Home - FastAPI Backend
n8n 워크플로우와 LangGraph Agent 연동을 위한 API 서버
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import hashlib
from datetime import datetime

# Initialize FastAPI
app = FastAPI(
    title="Young & Home API",
    description="n8n + LangGraph Agent Integration",
    version="1.0.0"
)

# CORS 설정 (n8n, Streamlit 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Data Models =====

class MonitoringCheckRequest(BaseModel):
    address: str
    user_id: str
    previous_hash: Optional[str] = None

class MonitoringAlertRequest(BaseModel):
    user_id: str
    address: str
    change_type: str  # "mortgage", "seizure", "ownership"
    details: str
    risk_score: int

class RAGUpsertRequest(BaseModel):
    id: str
    title: str
    provider: str
    type: str
    location: str
    content: str
    url: Optional[str] = None

class SubscriptionRequest(BaseModel):
    user_id: str
    location: str
    max_deposit: int  # 만원 단위
    max_monthly: int  # 만원 단위
    notify_method: str = "slack"  # "slack", "kakao", "email"

class NotifyRequest(BaseModel):
    user_id: str
    message: str
    channel: str = "slack"

# ===== In-Memory Storage (Demo용) =====
subscriptions_db: Dict[str, SubscriptionRequest] = {}
registry_hashes: Dict[str, str] = {}  # address -> hash
alerts_log: List[Dict] = []

# ===== Helper Functions =====

def load_houses():
    """매물 데이터 로드"""
    try:
        with open("data/housing/houses.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def compute_registry_hash(data: dict) -> str:
    """등기 데이터 해시 계산"""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

# ===== API Endpoints =====

@app.get("/")
async def root():
    return {
        "service": "Young & Home API",
        "status": "running",
        "endpoints": [
            "/api/listings",
            "/api/monitoring/check",
            "/api/monitoring/alert",
            "/api/rag/upsert",
            "/api/subscription/create",
            "/api/notify/user"
        ]
    }

# ----- 시나리오 1: 등기부 모니터링 -----

@app.post("/api/monitoring/check")
async def monitoring_check(request: MonitoringCheckRequest):
    """
    등기부등본 변동 체크
    - n8n 스케줄러가 주기적으로 호출
    - 이전 해시와 비교하여 변동 감지
    """
    # 실제로는 대법원 등기소 API 호출 또는 OCR 분석
    # 데모용으로 샘플 데이터 사용
    from src.ocr.parser import RegistryParser, RiskAnalyzer
    
    try:
        parser = RegistryParser()
        analyzer = RiskAnalyzer()
        
        # 샘플 데이터로 시뮬레이션
        sample_type = "safe"  # 기본값
        registry_data = parser.parse_registry(sample_type=sample_type)
        
        # 해시 계산
        current_hash = compute_registry_hash(registry_data)
        previous = registry_hashes.get(request.address, None)
        
        # 변동 감지
        has_change = previous is not None and previous != current_hash
        
        # 해시 저장
        registry_hashes[request.address] = current_hash
        
        # 위험도 분석
        risk_result = analyzer.analyze(registry_data, deposit=200000000)
        
        return {
            "address": request.address,
            "has_change": has_change,
            "previous_hash": previous,
            "current_hash": current_hash,
            "risk_score": risk_result.get("risk_score", 0),
            "risk_level": risk_result.get("risk_level", "unknown"),
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/alert")
async def monitoring_alert(request: MonitoringAlertRequest, background_tasks: BackgroundTasks):
    """
    등기 변동 알림 트리거 (n8n → App)
    - n8n이 변동 감지 시 호출
    - SafetyAnalyzerAgent 실행 후 알림 발송
    """
    from src.agents.analyzer import SafetyAnalyzerAgent
    
    try:
        # Agent로 위험 분석
        agent = SafetyAnalyzerAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        # 알림 로그 저장
        alert_entry = {
            "user_id": request.user_id,
            "address": request.address,
            "change_type": request.change_type,
            "details": request.details,
            "risk_score": request.risk_score,
            "timestamp": datetime.now().isoformat(),
            "status": "notified"
        }
        alerts_log.append(alert_entry)
        
        return {
            "success": True,
            "message": f"Alert sent for {request.address}",
            "alert_id": len(alerts_log)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 시나리오 2: 공고 수집 & RAG -----

@app.post("/api/rag/upsert")
async def rag_upsert(request: RAGUpsertRequest):
    """
    공고 데이터를 VectorDB에 저장
    - n8n 크롤러가 수집한 데이터 저장
    """
    from src.rag.retriever import BenefitRetriever
    
    try:
        # 문서 내용 구성
        doc_content = f"{request.title}\n{request.type}\n{request.location}\n{request.content}"
        
        # VectorDB에 저장
        retriever = BenefitRetriever()
        
        # 직접 ChromaDB에 추가
        if retriever.collection is not None:
            embedding = retriever._get_embedding(doc_content)
            
            retriever.collection.upsert(
                ids=[request.id],
                embeddings=[embedding],
                metadatas=[{
                    "id": request.id,
                    "name": request.title,
                    "provider": request.provider,
                    "category": request.type,
                    "url": request.url or ""
                }],
                documents=[doc_content]
            )
            
            return {
                "success": True,
                "id": request.id,
                "message": "Document upserted to VectorDB"
            }
        else:
            return {
                "success": False,
                "message": "VectorDB not available"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 시나리오 3: 매물 알림 -----

@app.get("/api/listings")
async def get_listings(
    location: Optional[str] = None,
    max_deposit: Optional[int] = None,
    max_monthly: Optional[int] = None
):
    """
    매물 목록 조회 (n8n 폴링용)
    - 필터링 옵션 지원
    """
    houses = load_houses()
    
    # 필터링
    filtered = []
    for h in houses:
        if location and location not in h.get("address", "") and location not in h.get("location", ""):
            continue
        if max_deposit and h.get("deposit", 0) > max_deposit:
            continue
        if max_monthly and h.get("monthly", 0) > max_monthly:
            continue
        filtered.append(h)
    
    return {
        "total": len(filtered),
        "listings": filtered,
        "fetched_at": datetime.now().isoformat()
    }


@app.post("/api/subscription/create")
async def create_subscription(request: SubscriptionRequest):
    """
    매물 알림 구독 생성
    - 사용자 조건 저장
    - n8n이 주기적으로 체크
    """
    subscriptions_db[request.user_id] = request
    
    return {
        "success": True,
        "user_id": request.user_id,
        "subscription": {
            "location": request.location,
            "max_deposit": request.max_deposit,
            "max_monthly": request.max_monthly,
            "notify_method": request.notify_method
        },
        "message": "Subscription created successfully"
    }


@app.get("/api/subscriptions")
async def get_subscriptions():
    """모든 구독 목록 (n8n용)"""
    return {
        "subscriptions": [
            {
                "user_id": uid,
                "location": sub.location,
                "max_deposit": sub.max_deposit,
                "max_monthly": sub.max_monthly,
                "notify_method": sub.notify_method
            }
            for uid, sub in subscriptions_db.items()
        ]
    }


@app.post("/api/notify/user")
async def notify_user(request: NotifyRequest):
    """
    사용자 알림 발송
    - Slack, 카카오톡, 이메일 등
    """
    # 실제로는 각 채널 API 호출
    # 데모용으로 로그만 기록
    
    notification = {
        "user_id": request.user_id,
        "message": request.message,
        "channel": request.channel,
        "sent_at": datetime.now().isoformat()
    }
    
    print(f"[NOTIFY] {request.channel}: {request.message}")
    
    return {
        "success": True,
        "notification": notification
    }


# ----- Health Check -----

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ----- Agent Endpoints -----

class LegalConsultRequest(BaseModel):
    question: str
    language: str = "KO"

class PrecedentSearchRequest(BaseModel):
    situation: str
    language: str = "KO"

class BenefitSearchRequest(BaseModel):
    query: str
    n_results: int = 5

@app.post("/api/agent/legal/consult")
async def legal_consult(request: LegalConsultRequest):
    """
    LegalAdvisorAgent를 통한 법률 상담
    """
    try:
        from src.agents.legal import LegalAdvisorAgent
        agent = LegalAdvisorAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
        result = agent.consult(request.question, language=request.language)
        return {
            "success": True,
            "question": request.question,
            "answer": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/legal/precedents")
async def legal_precedents(request: PrecedentSearchRequest):
    """
    관련 판례 검색
    """
    try:
        from src.agents.legal import LegalAdvisorAgent
        agent = LegalAdvisorAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
        result = agent.get_case_precedents(request.situation, language=request.language)
        return {
            "success": True,
            "situation": request.situation,
            "precedents": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/benefits")
async def search_benefits(request: BenefitSearchRequest):
    """
    RAG를 통한 복지 혜택 검색
    """
    try:
        from src.rag.retriever import BenefitRetriever
        retriever = BenefitRetriever()
        results = retriever.search(request.query, n_results=request.n_results)
        return {
            "success": True,
            "query": request.query,
            "total": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/benefits")
async def get_all_benefits():
    """
    모든 복지 혜택 목록 조회
    """
    try:
        with open("data/welfare/benefits.json", "r", encoding="utf-8") as f:
            benefits = json.load(f)
        return {
            "total": len(benefits),
            "benefits": benefits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts():
    """
    알림 로그 조회
    """
    return {
        "total": len(alerts_log),
        "alerts": alerts_log[-10:]  # 최근 10개
    }


# ----- Super Agent Endpoints (Single Node Architecture) -----

@app.post("/api/agent/crawler/run")
async def run_crawler_agent(background_tasks: BackgroundTasks):
    """
    [Super Agent] 공고 수집 및 RAG 구축 에이전트
    - LH/SH 공고 수집 -> 데이터 정제 -> VectorDB 저장 (All-in-One)
    """
    def _crawl_and_index():
        try:
            # 1. Mock Data Fetching (실제 크롤링 대체)
            new_notices = [
                {
                    "title": "2026년 1차 청년매입임대주택 입주자 모집",
                    "provider": "LH",
                    "type": "매입임대",
                    "location": "서울 전역",
                    "content": "LH에서 청년 매입임대주택 입주자를 모집합니다. 보증금 100만원~, 월세 시세 40% 수준.",
                    "url": "https://apply.lh.or.kr"
                },
                {
                    "title": "제45차 장기전세주택 입주자 모집공고",
                    "provider": "SH",
                    "type": "장기전세",
                    "location": "서울 송파구, 강동구",
                    "content": "최장 20년 거주 가능한 장기전세주택. 주변 시세 80% 이하.",
                    "url": "https://www.i-sh.co.kr"
                }
            ]
            
            # 2. Logic: RAG Upsert
            from src.rag.retriever import BenefitRetriever
            retriever = BenefitRetriever()
            
            count = 0
            if retriever.collection:
                for notice in new_notices:
                    doc_content = f"{notice['title']}\n{notice['type']}\n{notice['location']}\n{notice['content']}"
                    doc_id = hashlib.md5(doc_content.encode()).hexdigest()
                    
                    embedding = retriever._get_embedding(doc_content)
                    retriever.collection.upsert(
                        ids=[doc_id],
                        embeddings=[embedding],
                        metadatas=[{
                            "id": doc_id,
                            "name": notice['title'],
                            "provider": notice['provider'],
                            "category": notice['type'],
                            "url": notice['url']
                        }],
                        documents=[doc_content]
                    )
                    count += 1
            
            print(f"[SuperAgent] Crawler finished. Indexed {count} documents.")
            
        except Exception as e:
            print(f"[SuperAgent] Crawler failed: {e}")

    background_tasks.add_task(_crawl_and_index)
    return {"status": "started", "message": "Crawler agent started in background"}


@app.post("/api/agent/monitoring/run")
async def run_monitoring_agent(background_tasks: BackgroundTasks):
    """
    [Super Agent] 등기부 모니터링 에이전트
    - 전체 구독 주소 순회 -> 변동 체크 -> 위험 분석 -> 알림 (All-in-One)
    """
    def _monitor_and_alert():
        try:
            from src.ocr.parser import RegistryParser, RiskAnalyzer
            from src.agents.analyzer import SafetyAnalyzerAgent
            
            parser = RegistryParser()
            risk_agent = SafetyAnalyzerAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            
            # 1. 구독 중인 모든 주소 확인 (중복 제거)
            monitored_addresses = set(sub.location for sub in subscriptions_db.values())
            
            alerts_generated = 0
            
            for address in monitored_addresses:
                # 2. 등기 변동 시뮬레이션 (랜덤)
                # 실제로는 hash 비교 로직 사용
                import random
                if random.random() < 0.1: # 10% 확률로 변동 발생 가정
                    
                    # 3. 위험 분석
                    # 샘플 데이터 사용 ('risky' or 'safe')
                    risk_type = "risky" if random.random() < 0.5 else "safe"
                    
                    # Agent 분석 실행
                    analysis_result = risk_agent.run(
                        document_path=None, 
                        sample_type=risk_type,
                        deposit=200000000,
                        language="KO"
                    )
                    
                    # 4. 알림 생성 및 전송
                    # 해당 주소를 구독한 모든 유저에게 알림
                    for user_id, sub in subscriptions_db.items():
                        if sub.location == address:
                            alert_msg = f"[등기변동알림] {address} 변동 감지!\n\n{analysis_result[:100]}..."
                            print(f"[SuperAgent] Sending alert to {user_id}: {alert_msg}")
                            # 실제 전송 로직은 notify_user 등으로 연결
                            alerts_generated += 1
                            
            print(f"[SuperAgent] Monitoring finished. {alerts_generated} alerts sent.")
            
        except Exception as e:
            print(f"[SuperAgent] Monitoring failed: {e}")

    background_tasks.add_task(_monitor_and_alert)
    return {"status": "started", "message": "Monitoring agent started in background"}


@app.post("/api/agent/alert/run")
async def run_alert_agent(background_tasks: BackgroundTasks):
    """
    [Super Agent] 맞춤 매물 알림 에이전트
    - 구독 조건 매칭 -> 안전 매물 필터링 -> 알림 (All-in-One)
    """
    def _match_and_notify():
        try:
            # 1. 데이터 로드
            houses = load_houses()
            
            notifications = 0
            
            # 2. 각 구독자별 매칭
            for user_id, sub in subscriptions_db.items():
                matched_houses = []
                
                for h in houses:
                    # 조건: 지역, 보증금, 월세
                    if sub.location in h.get("address", "") or sub.location in h.get("location", ""):
                        if h.get("deposit", 0) <= sub.max_deposit and h.get("monthly", 0) <= sub.max_monthly:
                            # 3. [Agent Logic] 안전 등급 필터링 (간단히 필드 체크)
                            if h.get("risk_level") == "안전":
                                matched_houses.append(h)
                
                # 4. 알림 발송
                if matched_houses:
                    house_names = ", ".join([h["name"] for h in matched_houses[:3]])
                    msg = f"반가운 소식입니다! {sub.location}에 조건에 맞는 안전한 집 {len(matched_houses)}곳을 찾았어요: {house_names}"
                    print(f"[SuperAgent] Matched for {user_id}: {msg}")
                    notifications += 1
            
            print(f"[SuperAgent] Alert matching finished. {notifications} notifications sent.")
            
        except Exception as e:
            print(f"[SuperAgent] Alert run failed: {e}")

    background_tasks.add_task(_match_and_notify)
    return {"status": "started", "message": "Alert agent started in background"}


# ----- Run Server -----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

