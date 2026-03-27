
"""
Safety Analyzer Agent - 계약 안전 분석 에이전트
"""

from typing import TypedDict, Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import operator

class AnalyzerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    document_type: str
    registry_data: dict
    contract_data: dict
    risk_analysis: dict
    cross_validation: dict
    recommendations: list
    current_step: str
    registry_path: str
    contract_path: str


class SafetyAnalyzerAgent:
    """
    등기부등본 + 계약서 교차 검증 에이전트
    """
    
    def __init__(self, openai_api_key: str = None):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)
        self.graph = self._build_graph()
        self.sample_type = "safe"
        self.deposit = 200000000
        self.language = "KO"

    def set_language(self, language: str):
        self.language = language
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AnalyzerState)
        
        workflow.add_node("data_extractor", self._extract_data)
        workflow.add_node("risk_analyzer", self._analyze_risk)
        workflow.add_node("cross_validator", self._validate_consistency)
        workflow.add_node("report_generator", self._generate_report)
        
        workflow.set_entry_point("data_extractor")
        workflow.add_edge("data_extractor", "risk_analyzer")
        workflow.add_edge("risk_analyzer", "cross_validator")
        workflow.add_edge("cross_validator", "report_generator")
        workflow.add_edge("report_generator", END)
        
        return workflow.compile()
    
    def _extract_data(self, state: AnalyzerState) -> dict:
        """문서 데이터 추출"""
        try:
            from src.ocr.parser import DocumentParser
            parser = DocumentParser()
            
            # 1. 등기부등본 파싱
            # 경로가 없으면 샘플 데이터 사용
            reg_path = state.get("registry_path")
            registry_data = parser.parse_registry(reg_path, sample_type=self.sample_type)
            
            # 2. 계약서 파싱 (있으면)
            con_path = state.get("contract_path")
            contract_data = {}
            if con_path or self.sample_type: # 샘플 타입이 있으면 계약서도 샘플로 로드
                contract_data = parser.parse_contract(con_path, sample_type=self.sample_type)
                
            return {
                "registry_data": registry_data,
                "contract_data": contract_data,
                "current_step": "risk_analyzer",
                "messages": [AIMessage(content="Data extracted.")]
            }
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error extracting data: {e}")]}

    def _analyze_risk(self, state: AnalyzerState) -> dict:
        """등기부 위험 분석"""
        try:
            from src.ocr.parser import RiskAnalyzer
            analyzer = RiskAnalyzer()
            
            reg_data = state.get("registry_data", {})
            user_deposit = state.get("contract_data", {}).get("deposit", self.deposit)
            
            analysis = analyzer.analyze(reg_data, deposit=user_deposit)
            
            return {
                "risk_analysis": analysis,
                "current_step": "cross_validator"
            }
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error analyzing risk: {e}")]}

    def _validate_consistency(self, state: AnalyzerState) -> dict:
        """교차 검증: 등기부 vs 계약서"""
        reg = state.get("registry_data", {})
        con = state.get("contract_data", {})
        
        issues = []
        is_safe = True
        
        if not con:
            return {"cross_validation": {"status": "skipped", "issues": []}}
            
        # 1. 소유자 일치 여부
        reg_owner = reg.get("owner", {}).get("name", "").strip()
        con_lessor = con.get("lessor_name", "").strip()
        
        if reg_owner and con_lessor:
            if reg_owner != con_lessor:
                issues.append(f"🔴 **소유자 불일치**: 등기부[{reg_owner}] vs 계약서[{con_lessor}]")
                is_safe = False
            else:
                issues.append(f"✅ 소유자 일치: {reg_owner}")
        
        # 2. 주소 일치 여부 (간단 비교)
        reg_addr = reg.get("property_address", "").split(" ")
        con_addr = con.get("address", "").split(" ")
        # 구, 동, 번지수 정도만 체크
        match_count = 0
        for part in con_addr:
            if part in reg_addr: match_count += 1
            
        if match_count < 2:
            issues.append(f"⚠️ **주소 확인 필요**: 등기부와 계약서의 주소가 달라 보입니다.")
            is_safe = False
        else:
            issues.append("✅ 주소 일치 확인")
            
        return {
            "cross_validation": {
                "status": "done",
                "is_match": is_safe,
                "issues": issues
            }
        }

    def _generate_report(self, state: AnalyzerState) -> dict:
        """최종 리포트 생성"""
        risk = state.get("risk_analysis", {})
        cross = state.get("cross_validation", {})
        reg = state.get("registry_data", {})
        
        report = f"## ⚖️ 안전 분석 리포트\n\n"
        
        # 1. 교차 검증 결과 (최상단)
        if cross.get("status") == "done":
            report += "### 🕵️ 계약서 교차 검증\n"
            for issue in cross.get("issues", []):
                report += f"- {issue}\n"
            
            if not cross.get("is_match"):
                report += "\n> 🚨 **경고**: 계약서 내용이 등기부등본과 일치하지 않습니다. 절대 계약금을 입금하지 마세요!\n\n"
            else:
                report += "\n> ✨ **검증 완료**: 소유자와 주소가 등기부와 일치합니다.\n\n"
        
        # 2. 등기부 위험 분석
        report += "### 📊 등기부 위험 진단\n"
        report += f"- **종합 등급**: {risk.get('risk_level', '미정')}\n"
        report += f"- **위험 점수**: {risk.get('risk_score', 0)}점\n"
        
        if risk.get("risks"):
            report += "\n**발견된 위험 요소:**\n"
            for r in risk.get("risks", []):
                report += f"- ⚠️ [{r['severity']}] {r['type']}: {r['description']}\n"
        else:
            report += "- ✅ 특별한 위험 요소가 발견되지 않았습니다.\n"
            
        # 3. 권고 사항
        report += f"\n### 💡 AI 조언\n{risk.get('recommendation')}"
        
        return {
             "messages": [AIMessage(content=report)]
        }

    def run(self, document_path: str = None, contract_path: str = None, sample_type: str = "safe", deposit: int = 200000000, language: str = "KO") -> str:
        self.sample_type = sample_type
        self.deposit = deposit
        self.set_language(language)
        
        initial_state = {
            "messages": [HumanMessage(content="Start Analysis")],
            "registry_path": document_path,
            "contract_path": contract_path,
            "current_step": "start"
        }
        
        result = self.graph.invoke(initial_state)
        return result["messages"][-1].content

