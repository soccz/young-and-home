"""
Safety Analyzer Agent - 계약 안전 분석 에이전트
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import operator
import re


class AnalyzerState(TypedDict):
    """에이전트 상태 정의"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    document_type: str  # "등기부등본", "계약서", "건축물대장"
    extracted_data: dict
    risk_analysis: dict
    recommendations: list
    current_step: str


class SafetyAnalyzerAgent:
    """
    등기부등본/계약서 분석을 통한 안전 진단 에이전트
    
    Flow:
    1. document_classifier: 문서 유형 판별
    2. data_extractor: OCR + 구조화 데이터 추출
    3. risk_analyzer: 위험 요소 분석
    4. recommendation_generator: 조치 사항 추천
    """
    
    def __init__(self, openai_api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # 비용 최소화
            temperature=0,
            api_key=openai_api_key
        )
        self.graph = self._build_graph()
        self.sample_type = "safe"  # 기본값
        self.deposit = 200000000  # 기본 전세금 2억
        self.language = "KO"

    def set_language(self, language: str):
        self.language = language
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(AnalyzerState)
        
        # 노드 추가
        workflow.add_node("document_classifier", self._classify_document)
        workflow.add_node("data_extractor", self._extract_data)
        workflow.add_node("risk_analyzer", self._analyze_risk)
        workflow.add_node("recommendation_generator", self._generate_recommendations)
        
        # 엣지 연결
        workflow.set_entry_point("document_classifier")
        workflow.add_edge("document_classifier", "data_extractor")
        workflow.add_edge("data_extractor", "risk_analyzer")
        workflow.add_edge("risk_analyzer", "recommendation_generator")
        workflow.add_edge("recommendation_generator", END)
        
        return workflow.compile()
    
    def _classify_document(self, state: AnalyzerState) -> dict:
        """문서 유형 분류"""
        # TODO: 실제 Vision API로 문서 분류
        # 현재는 mock
        return {
            "document_type": "등기부등본",
            "current_step": "data_extractor",
            "messages": [AIMessage(content="문서 유형: 등기부등본으로 확인되었습니다.")]
        }
    
    def _extract_data(self, state: AnalyzerState) -> dict:
        """문서에서 핵심 데이터 추출 - OCR 파서 연동"""
        doc_type = state.get("document_type", "")
        
        # OCR 파서 사용
        try:
            from src.ocr.parser import DocumentParser
            parser = DocumentParser()
            
            if doc_type == "등기부등본":
                registry_data = parser.parse_registry(sample_type=self.sample_type)
                
                # 파서 결과를 기존 형식으로 변환
                mortgages = []
                for m in registry_data.get("mortgage", []):
                    mortgages.append({
                        "creditor": m.get("creditor"),
                        "amount": m.get("amount", 0),
                        "date": m.get("date")
                    })
                
                prior_deposits = []
                for l in registry_data.get("lease", []):
                    prior_deposits.append({
                        "amount": l.get("deposit", 0),
                        "date": l.get("date")
                    })
                
                seizures = []
                for s in registry_data.get("seizure", []):
                    seizures.append({
                        "type": s.get("type"),
                        "amount": s.get("amount", 0),
                        "date": s.get("date")
                    })
                
                # 시세 추정 (간단히 근저당 + 전세금 기준)
                total_mortgage = sum(m.get("amount", 0) for m in registry_data.get("mortgage", []))
                total_lease = sum(l.get("deposit", 0) for l in registry_data.get("lease", []))
                estimated_value = max(300000000, (total_mortgage + total_lease) * 1.3)  # 최소 3억
                
                extracted = {
                    "property_type": registry_data.get("property_type", "아파트"),
                    "address": registry_data.get("property_address", "정보 없음"),
                    "area": float(registry_data.get("area", "0㎡").replace("㎡", "").split()[0]) if registry_data.get("area") else 0,
                    "owner": registry_data.get("owner", {}).get("name", "정보 없음"),
                    "mortgages": mortgages,
                    "prior_deposits": prior_deposits,
                    "seizures": seizures,
                    "market_value": estimated_value,
                    "user_deposit": self.deposit
                }
            else:
                extracted = {}
                
        except Exception as e:
            print(f"OCR Parser error: {e}")
            # Fallback: 기존 mock 데이터
            extracted = {
                "property_type": "아파트",
                "address": "서울시 마포구 신촌로 123",
                "area": 59.5,
                "owner": "김OO",
                "mortgages": [{"creditor": "OO은행", "amount": 200000000, "date": "2024-03-15"}],
                "prior_deposits": [{"amount": 50000000, "date": "2023-01-10"}],
                "seizures": [],
                "market_value": 250000000,
                "user_deposit": self.deposit
            }
        
        return {
            "extracted_data": extracted,
            "current_step": "risk_analyzer",
            "messages": [AIMessage(content="문서 데이터를 추출했습니다.")]
        }
    
    def _analyze_risk(self, state: AnalyzerState) -> dict:
        """위험도 분석"""
        data = state.get("extracted_data", {})
        
        risks = []
        risk_score = 0
        
        # 1. 깡통전세 위험 분석
        market_value = data.get("market_value", 0)
        total_mortgage = sum(m.get("amount", 0) for m in data.get("mortgages", []))
        total_prior = sum(p.get("amount", 0) for p in data.get("prior_deposits", []))
        
        ltv = (total_mortgage / market_value * 100) if market_value > 0 else 0
        
        if ltv > 70:
            risks.append({
                "type": "깡통전세 위험",
                "severity": "고위험",
                "detail": f"근저당 설정액({total_mortgage/10000:.0f}만원)이 시세({market_value/10000:.0f}만원) 대비 {ltv:.1f}% 수준"
            })
            risk_score += 40
        elif ltv > 50:
            risks.append({
                "type": "깡통전세 주의",
                "severity": "중위험",
                "detail": f"근저당 비율 {ltv:.1f}%로 주의 필요"
            })
            risk_score += 20
        
        # 2. 선순위 보증금 분석
        if total_prior > 0:
            risks.append({
                "type": "선순위 임차인 존재",
                "severity": "중위험",
                "detail": f"선순위 보증금 {total_prior/10000:.0f}만원 존재"
            })
            risk_score += 15
        
        # 3. 압류 여부
        if data.get("seizures"):
            risks.append({
                "type": "압류 설정",
                "severity": "고위험",
                "detail": "해당 부동산에 압류가 설정되어 있습니다"
            })
            risk_score += 50
        
        # 예상 회수율 계산
        user_deposit = 100000000  # 가정: 1억 보증금
        if market_value > 0:
            remaining = market_value - total_mortgage - total_prior
            recovery_rate = max(0, min(100, remaining / user_deposit * 100))
        else:
            recovery_rate = 0
        
        # 종합 판정
        if risk_score >= 50:
            overall = "고위험"
        elif risk_score >= 25:
            overall = "중위험"
        else:
            overall = "안전"
        
        risk_analysis = {
            "overall_risk": overall,
            "risk_score": risk_score,
            "recovery_rate": recovery_rate,
            "details": risks,
            "ltv": ltv,
            "total_mortgage": total_mortgage,
            "total_prior_deposit": total_prior
        }
        
        return {
            "risk_analysis": risk_analysis,
            "current_step": "recommendation_generator",
            "messages": [AIMessage(content=f"위험 분석 완료: {overall}")]
        }
    
    def _generate_recommendations(self, state: AnalyzerState) -> dict:
        """조치 사항 및 특약 추천"""
        risk = state.get("risk_analysis", {})
        data = state.get("extracted_data", {})
        
        recommendations = []
        
        # 위험도에 따른 권장사항
        if risk.get("overall_risk") == "고위험":
            recommendations.extend([
                "🚨 이 매물은 계약하지 않는 것을 강력히 권장합니다.",
                "반드시 HUG 전세보증보험 가입 가능 여부를 먼저 확인하세요.",
                "다른 안전한 매물을 찾아보시길 권장합니다."
            ])
        elif risk.get("overall_risk") == "중위험":
            recommendations.extend([
                "⚠️ 계약 전 반드시 아래 조치를 취하세요:",
                "HUG/SGI 전세보증보험 가입을 조건으로 계약하세요.",
                "특약 추가: '보증보험 가입 불가 시 계약금 전액 반환'"
            ])
        else:
            recommendations.extend([
                "✅ 상대적으로 안전한 매물입니다.",
                "그래도 전세보증보험 가입을 권장드립니다.",
                "전입신고와 확정일자는 이사 당일 바로 하세요."
            ])
        
        # 최종 리포트 생성
        # Language-based Report Generation
        if self.language == "EN":
            report = f"""
## ⚖️ Safety Risk Report

### 📄 Target Property
- Address: {data.get('address', 'Unknown')}
- Area: {data.get('area', 0)}㎡
- Owner: {data.get('owner', 'Unknown')}

### 📊 Risk Analysis

| Item | Value |
|------|-------|
| **Overall Risk** | **{risk.get('overall_risk', 'Analyzing')}** |
| LTV (Loan/Value) | {risk.get('ltv', 0):.1f}% |
| Total Prior Debt | {risk.get('total_prior_deposit', 0)/10000:.0f}M KRW |
| Est. Recovery Rate | {risk.get('recovery_rate', 0):.0f}% |

### ⚠️ Risk Factors
"""
            for r in risk.get("details", []):
                # Translate severity/type roughly or keep simpler
                report += f"- **[{r['severity']}]** {r['type']}: {r['detail']}\n"
            
            report += "\n### 💡 Recommendations\n"
            if risk.get("overall_risk") == "고위험":
                 report += "- 🚨 **HIGH RISK**: Do not proceed with this contract.\n"
                 report += "- Check HUG Insurance eligibility immediately.\n"
            elif risk.get("overall_risk") == "중위험":
                 report += "- ⚠️ **CAUTION**: Proceed only with safety measures.\n"
                 report += "- Mandate 'HUG Insurance' in special clauses.\n"
            else:
                 report += "- ✅ **SAFE**: Relatively safe property.\n"
                 report += "- Insurance is still recommended.\n"

        else:
            # Korean Report (Original)
            report = f"""
## ⚖️ 계약 안전 진단 리포트

### 📄 분석 대상
- 주소: {data.get('address', '정보 없음')}
- 면적: {data.get('area', 0)}㎡
- 소유자: {data.get('owner', '정보 없음')}

### 📊 위험도 분석

| 항목 | 수치 |
|------|------|
| **종합 위험도** | **{risk.get('overall_risk', '분석 중')}** |
| 근저당/시세 비율 (LTV) | {risk.get('ltv', 0):.1f}% |
| 선순위 채권 합계 | {risk.get('total_prior_deposit', 0)/10000:.0f}만원 |
| 경매 시 예상 회수율 | {risk.get('recovery_rate', 0):.0f}% |

### ⚠️ 발견된 위험 요소
"""
            for r in risk.get("details", []):
                report += f"- **[{r['severity']}]** {r['type']}: {r['detail']}\n"
            
            report += "\n### 💡 권장 조치\n"
            for rec in recommendations:
                report += f"- {rec}\n"
        
        return {
            "recommendations": recommendations,
            "current_step": "done",
            "messages": [AIMessage(content=report)]
        }
    
    def run(self, document_path: str = None, sample_type: str = "safe", deposit: int = 200000000, language: str = "KO") -> str:
        """에이전트 실행
        
        Args:
            document_path: 문서 경로 (실제 구현 시 사용)
            sample_type: 샘플 타입 ("safe", "risky", "moderate")
            deposit: 예정 전세금 (원)
            language: 언어 설정 ("KO", "EN")
        """
        self.sample_type = sample_type
        self.deposit = deposit
        self.set_language(language)
        
        initial_state = {
            "messages": [HumanMessage(content=f"문서 분석 요청: {document_path or 'uploaded_document'}")],
            "document_type": "",
            "extracted_data": {},
            "risk_analysis": {},
            "recommendations": [],
            "current_step": "start"
        }
        
        result = self.graph.invoke(initial_state)
        
        if result.get("messages"):
            return result["messages"][-1].content
        return "분석을 완료하지 못했습니다."


# Test
if __name__ == "__main__":
    agent = SafetyAnalyzerAgent()
    result = agent.run("sample_document.pdf")
    print(result)
