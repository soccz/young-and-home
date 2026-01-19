
"""
Young & Home - FastAPI Backend
n8n 워크플로우와 LangGraph Agent 연동을 위한 API 서버 (SQLite Persistence Applied)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import hashlib
import sqlite3
from datetime import datetime
from contextlib import contextmanager

# Initialize FastAPI
app = FastAPI(
    title="Young & Home API",
    description="n8n + LangGraph Agent Integration with SQLite",
    version="1.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Database Setup =====
DB_PATH = "young_home.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Subscriptions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id TEXT PRIMARY KEY,
            location TEXT,
            max_deposit INTEGER,
            max_monthly INTEGER,
            notify_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Registry Monitoring Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registry_monitoring (
            address TEXT PRIMARY KEY,
            current_hash TEXT,
            last_checked_at TIMESTAMP
        )
        """)
        
        # 3. Alerts Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            address TEXT,
            change_type TEXT,
            details TEXT,
            risk_score INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT
        )
        """)
        conn.commit()

# Initialize DB on startup
init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

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
        "service": "Young & Home API (SQLite)",
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
    등기부등본 변동 체크 (DB 기반)
    """
    from src.ocr.parser import RegistryParser, RiskAnalyzer
    
    try:
        parser = RegistryParser()
        analyzer = RiskAnalyzer()
        
        # 샘플 데이터로 시뮬레이션
        sample_type = "safe"
        registry_data = parser.parse_registry(sample_type=sample_type)
        
        # 해시 계산
        current_hash = compute_registry_hash(registry_data)
        
        # DB 조회
        previous_hash = None
        has_change = False
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_hash FROM registry_monitoring WHERE address = ?", (request.address,))
            row = cursor.fetchone()
            
            if row:
                previous_hash = row["current_hash"]
                if previous_hash != current_hash:
                    has_change = True
            
            # DB 업데이트
            cursor.execute("""
            INSERT OR REPLACE INTO registry_monitoring (address, current_hash, last_checked_at)
            VALUES (?, ?, ?)
            """, (request.address, current_hash, datetime.now().isoformat()))
            conn.commit()
        
        # 위험도 분석
        risk_result = analyzer.analyze(registry_data, deposit=200000000)
        
        return {
            "address": request.address,
            "has_change": has_change,
            "previous_hash": previous_hash,
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
    등기 변동 알림 트리거
    """
    try:
        # 알림 로그 저장 (DB)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO alerts (user_id, address, change_type, details, risk_score, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (request.user_id, request.address, request.change_type, request.details, request.risk_score, "notified"))
            conn.commit()
            
            alert_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": f"Alert sent for {request.address}",
            "alert_id": alert_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 시나리오 2: 공고 수집 & RAG -----

@app.post("/api/rag/upsert")
async def rag_upsert(request: RAGUpsertRequest):
    """
    공고 데이터를 VectorDB에 저장
    """
    from src.rag.retriever import BenefitRetriever
    
    try:
        doc_content = f"{request.title}\n{request.type}\n{request.location}\n{request.content}"
        retriever = BenefitRetriever()
        
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
            return {"success": False, "message": "VectorDB not available"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 시나리오 3: 매물 알림 -----

@app.get("/api/listings")
async def get_listings(
    location: Optional[str] = None,
    max_deposit: Optional[int] = None,
    max_monthly: Optional[int] = None
):
    houses = load_houses()
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
    매물 알림 구독 생성 (DB)
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO subscriptions (user_id, location, max_deposit, max_monthly, notify_method)
            VALUES (?, ?, ?, ?, ?)
            """, (request.user_id, request.location, request.max_deposit, request.max_monthly, request.notify_method))
            conn.commit()
            
        return {
            "success": True,
            "user_id": request.user_id,
            "subscription": {
                "location": request.location,
                "max_deposit": request.max_deposit,
                "max_monthly": request.max_monthly,
                "notify_method": request.notify_method
            },
            "message": "Subscription created in DB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subscriptions")
async def get_subscriptions():
    """모든 구독 목록 (DB -> n8n)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscriptions")
            rows = cursor.fetchall()
            
            return {
                "subscriptions": [
                    {
                        "user_id": row["user_id"],
                        "location": row["location"],
                        "max_deposit": row["max_deposit"],
                        "max_monthly": row["max_monthly"],
                        "notify_method": row["notify_method"]
                    }
                    for row in rows
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notify/user")
async def notify_user(request: NotifyRequest):
    print(f"[NOTIFY] {request.channel}: {request.message}")
    return {"success": True, "message": "Notification logged"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/alerts")
async def get_alerts():
    """알림 로그 조회 (DB)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10")
            rows = cursor.fetchall()
            
            return {
                "total": len(rows),
                "alerts": [dict(row) for row in rows]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- Super Agent Endpoints (All-in-One Logic) -----

@app.post("/api/agent/monitoring/run")
async def run_monitoring_agent(background_tasks: BackgroundTasks):
    """
    [Super Agent] 등기부 모니터링 에이전트
    """
    def _monitor_and_alert():
        try:
            from src.ocr.parser import RegistryParser, RiskAnalyzer
            from src.agents.analyzer import SafetyAnalyzerAgent
            
            # DB에서 구독 정보 Road
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscriptions")
                subs = [dict(row) for row in cursor.fetchall()]

            if not subs:
                print("[SuperAgent] No subscriptions found.")
                return

            risk_agent = SafetyAnalyzerAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            
            # 주소별로 그루핑 (중복 체크 방지)
            unique_addresses = set(s['location'] for s in subs)
            alerts_generated = 0
            
            for address in unique_addresses:
                import random
                # 10% 확률로 변동 가정
                if random.random() < 0.1:
                    risk_type = "risky" if random.random() < 0.5 else "safe"
                    
                    analysis_result = risk_agent.run(
                        document_path=None, 
                        sample_type=risk_type,
                        deposit=200000000,
                        language="KO"
                    )
                    
                    # 해당 주소 구독자에게 알림
                    affected_users = [s for s in subs if s['location'] == address]
                    for user in affected_users:
                        print(f"[SuperAgent] Alert to {user['user_id']}: {address} Change detected!")
                        alerts_generated += 1
                        
                        # DB에 로그 저장
                        with get_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                            INSERT INTO alerts (user_id, address, change_type, details, risk_score, status)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (user['user_id'], address, "registry_change", analysis_result[:50], 80, "sent"))
                            conn.commit()

            print(f"[SuperAgent] Monitoring finished. {alerts_generated} alerts sent.")
            
        except Exception as e:
            print(f"[SuperAgent] Monitoring failed: {e}")

    background_tasks.add_task(_monitor_and_alert)
    return {"status": "started", "message": "Monitoring agent started in background"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
