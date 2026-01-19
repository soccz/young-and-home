"""
Legal Advisor Agent - 주택임대차보호법 기반 법률 상담 (Enhanced)
"""

import os
import json
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class LegalAdvisorAgent:
    """
    법률 상담 에이전트 (Enhanced)
    
    기능:
    1. consult() - 법률 질문 답변 (법령 + 판례 기반)
    2. get_case_precedents() - 관련 판례 검색
    3. generate_notice_letter() - 통지서 생성
    4. explain_contract_clause() - 계약서 조항 해석
    """
    
    def __init__(self, openai_api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        self.law_text = self._load_law_text()
        self.precedents = self._load_precedents()
        
    def _load_law_text(self) -> str:
        """법령 텍스트 로드"""
        try:
            with open("data/legal/rental_protection_act.txt", "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "법령 데이터를 찾을 수 없습니다."
    
    def _load_precedents(self) -> List[Dict]:
        """판례 데이터 로드"""
        try:
            with open("data/legal/precedents.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def get_case_precedents(self, situation: str, language: str = "KO") -> str:
        """
        상황에 맞는 관련 판례 검색
        
        Args:
            situation: 사용자 상황 설명
            language: 언어 설정 ("KO" 또는 "EN")
        
        Returns:
            관련 판례 요약 및 시사점
        """
        if not self.precedents:
            return "판례 데이터를 불러올 수 없습니다."
        
        precedents_text = json.dumps(self.precedents, ensure_ascii=False, indent=2)
        lang_instruction = "답변은 반드시 한국어로 작성하세요." if language == "KO" else "Please answer in English."
        
        system_prompt = f"""
        당신은 부동산 법률 전문가입니다.
        아래 판례 데이터를 참고하여 사용자 상황과 가장 관련 있는 판례를 찾아 설명하세요.
        
        [판례 데이터]
        {precedents_text}
        
        [답변 형식]
        1. 관련 판례 제목 및 사건번호
        2. 판결 요지
        3. 사용자 상황에 대한 시사점
        4. 주의사항 또는 권장 조치
        
        {lang_instruction}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"상황: {situation}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def generate_notice_letter(
        self, 
        notice_type: str,
        sender_name: str,
        details: Dict,
        language: str = "KO"
    ) -> str:
        """
        통지서 생성
        
        Args:
            notice_type: "갱신거절", "수리요청", "보증금반환", "증액거부"
            sender_name: 발신자 이름
            details: 상세 정보 딕셔너리
            language: 언어 설정
        
        Returns:
            통지서 내용
        """
        notice_templates = {
            "갱신거절": {
                "title": "임대차계약 갱신거절 통지서",
                "required_fields": ["contract_end_date", "reason"],
                "legal_basis": "주택임대차보호법 제6조의3"
            },
            "수리요청": {
                "title": "시설물 수리 요청서",
                "required_fields": ["repair_items", "urgency"],
                "legal_basis": "민법 제623조 (임대인의 수선의무)"
            },
            "보증금반환": {
                "title": "임대차보증금 반환 청구서",
                "required_fields": ["deposit_amount", "contract_end_date", "deadline"],
                "legal_basis": "주택임대차보호법 제3조의2"
            },
            "증액거부": {
                "title": "차임 증액 거부 통지서",
                "required_fields": ["requested_increase", "legal_limit"],
                "legal_basis": "주택임대차보호법 제7조 (5% 상한)"
            }
        }
        
        template = notice_templates.get(notice_type)
        if not template:
            return f"지원하지 않는 통지서 유형입니다. 지원 유형: {list(notice_templates.keys())}"
        
        lang_instruction = "통지서는 한국어로 작성하세요." if language == "KO" else "Write the notice in English."
        
        system_prompt = f"""
        당신은 법률 문서 작성 전문가입니다.
        아래 정보를 바탕으로 공식적이고 법적 효력이 있는 통지서를 작성하세요.
        
        [통지서 유형]: {template['title']}
        [법적 근거]: {template['legal_basis']}
        [발신자]: {sender_name}
        
        [작성 원칙]
        1. 정중하면서도 단호한 어조
        2. 법적 근거를 명시
        3. 명확한 요청사항과 기한
        4. 불이행 시 조치사항 언급
        
        {lang_instruction}
        """
        
        details_text = "\n".join([f"- {k}: {v}" for k, v in details.items()])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"상세 정보:\n{details_text}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def explain_contract_clause(self, clause: str, language: str = "KO") -> str:
        """
        계약서 조항 해석
        
        Args:
            clause: 해석이 필요한 계약서 조항 텍스트
            language: 언어 설정
        
        Returns:
            조항 해석 및 주의사항
        """
        lang_instruction = "답변은 반드시 한국어로 작성하세요." if language == "KO" else "Please answer in English."
        
        system_prompt = f"""
        당신은 부동산 계약 전문 변호사입니다.
        임대차계약서 조항을 분석하고 쉽게 설명해주세요.
        
        [분석 포인트]
        1. 조항의 의미 (쉬운 말로)
        2. 임차인에게 유리한 점 / 불리한 점
        3. 관련 법령 (주택임대차보호법, 민법)
        4. 수정 권장 사항 (있다면)
        5. 주의사항
        
        [참고 법령]
        {self.law_text}
        
        {lang_instruction}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"분석할 조항:\n\n{clause}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
            
    def consult(self, user_question: str, language: str = "KO") -> str:
        """
        사용자 질문에 대해 법적 근거를 들어 답변 (Enhanced)
        
        법령 + 판례 데이터를 모두 활용하여 더 풍부한 답변 제공
        """
        lang_instruction = "답변은 반드시 한국어로 작성하세요." if language == "KO" else "Please answer in English."
        
        # 판례 데이터 포함
        precedents_summary = ""
        if self.precedents:
            precedents_summary = "\n\n[참고 판례]\n"
            for p in self.precedents[:3]:  # 상위 3개만
                precedents_summary += f"- {p['title']} ({p['case_number']}): {p['summary']}\n"
        
        system_prompt = f"""
        당신은 'Young & Home'의 AI 주거 법률 상담사입니다.
        아래 제공된 [주택임대차보호법] 원문과 [참고 판례]를 근거로 사용자의 질문에 전문적으로 답변하세요.
        
        [답변 원칙]
        1. 반드시 관련된 "제O조 O항"을 명시하여 법적 근거를 대세요.
        2. 관련 판례가 있으면 "OO 사건 (사건번호)"을 인용하세요.
        3. 사용자가 이해하기 쉽게 풀어서 설명하되, 용어는 정확하게 사용하세요.
        4. 법령에 없는 내용은 "법령에 명시되지 않았으나 판례/관례상..."이라고 구분해서 말하세요.
        5. 구체적인 조치 방법이나 다음 단계를 제안해주세요.
        6. 말투는 정중하고 신뢰감 있게 하세요.
        7. {lang_instruction}
        
        [주택임대차보호법 데이터]
        {self.law_text}
        {precedents_summary}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_question)
        ]
        
        response = self.llm.invoke(messages)
        return response.content


# 자주 사용되는 통지서 템플릿
NOTICE_TEMPLATES = {
    "갱신거절_응대": """
[계약갱신요구권 행사 통지]

집주인님께,

임대차계약 갱신과 관련하여 주택임대차보호법 제6조의3에 따라 
계약갱신요구권을 행사하고자 합니다.

해당 법령에 따르면, 임대인은 정당한 사유 없이 임차인의 
갱신요구를 거절할 수 없습니다.

회신 기한: 통지 수령 후 1개월 이내
""",
    "보증금_독촉": """
[보증금 반환 최고서]

임대인 OOO 귀하,

본 임차인은 YYYY년 MM월 DD일자로 임대차계약이 종료되었음에도
아직까지 보증금 OOO만원을 반환받지 못하였습니다.

주택임대차보호법 제3조의2에 따라 조속한 반환을 요청드립니다.
본 최고장 수령 후 14일 이내 이행되지 않을 경우,
법적 조치를 취할 수 있음을 알려드립니다.
"""
}


# Test
if __name__ == "__main__":
    agent = LegalAdvisorAgent()
    
    # 기본 상담 테스트
    print("=== 기본 상담 ===")
    print(agent.consult("집주인이 계약 만료 1달 전에 나가라고 하면 나가야 하나요?"))
    
    # 판례 검색 테스트
    print("\n=== 판례 검색 ===")
    print(agent.get_case_precedents("전세금을 돌려받지 못하고 있어요"))
    
    # 계약 조항 해석 테스트
    print("\n=== 조항 해석 ===")
    print(agent.explain_contract_clause("임차인은 임대인의 동의 없이 본 주택을 제3자에게 전대할 수 없다."))
