"""
Negotiator Agent - 협상 메시지 생성 에이전트
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class NegotiatorAgent:
    """
    집주인/중개사에게 보낼 협상 메시지를 생성하는 에이전트
    """
    
    def __init__(self, openai_api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 부동산 계약 협상 전문가입니다. 
임차인을 대신하여 집주인이나 중개사에게 보낼 정중하면서도 확실한 메시지를 작성합니다.

메시지 작성 원칙:
1. 항상 정중하고 존중하는 태도를 유지합니다.
2. 법적 근거가 있다면 부드럽게 언급합니다.
3. 상대방의 입장도 고려하면서 임차인의 권리를 보호합니다.
4. 구체적인 요청사항을 명확히 전달합니다.
5. 협력적인 해결을 제안합니다.

형식:
- 인사말로 시작
- 본론을 간결하게
- 요청사항을 명확히
- 감사 인사로 마무리"""),
            ("human", """다음 상황에 맞는 협상 메시지를 작성해주세요.

발신자 이름: {sender_name}
수신자: {recipient} (집주인/중개사)
협상 목적: {negotiation_type}
상세 상황: {situation}
원하는 결과: {desired_outcome}

메시지를 작성해주세요:""")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def generate_message(
        self,
        sender_name: str,
        recipient: str,
        negotiation_type: str,
        situation: str,
        desired_outcome: str
    ) -> str:
        """협상 메시지 생성"""
        
        result = self.chain.invoke({
            "sender_name": sender_name,
            "recipient": recipient,
            "negotiation_type": negotiation_type,
            "situation": situation,
            "desired_outcome": desired_outcome
        })
        
        return result
    
    def generate_insurance_request(self, sender_name: str, risk_details: str = None) -> str:
        """보증보험 가입 요청 메시지 생성"""
        return self.generate_message(
            sender_name=sender_name,
            recipient="집주인",
            negotiation_type="보증보험 가입 동의 요청",
            situation=f"등기부등본 확인 결과, 안전한 거래를 위해 전세보증보험 가입이 필요한 상황입니다. {risk_details or ''}",
            desired_outcome="HUG 또는 SGI 전세보증보험 가입에 동의해주시고, 필요 서류 협조를 부탁드립니다."
        )
    
    def generate_special_clause_request(self, sender_name: str, clause_content: str) -> str:
        """특약 추가 요청 메시지 생성"""
        return self.generate_message(
            sender_name=sender_name,
            recipient="집주인/중개사",
            negotiation_type="특약 조항 추가 요청",
            situation=f"계약서 검토 결과, 다음 특약 조항 추가가 필요합니다: {clause_content}",
            desired_outcome="해당 특약을 계약서에 추가하여 임차인의 권리를 보호받고자 합니다."
        )
    
    def generate_repair_request(self, sender_name: str, repair_items: list) -> str:
        """수리 요청 메시지 생성"""
        items_str = ", ".join(repair_items)
        return self.generate_message(
            sender_name=sender_name,
            recipient="집주인",
            negotiation_type="입주 전 수리 요청",
            situation=f"집 상태 확인 결과, 다음 항목에 대한 수리가 필요합니다: {items_str}",
            desired_outcome="입주 전까지 해당 항목들의 수리 완료를 부탁드립니다."
        )


# 자주 사용되는 특약 조항 템플릿
COMMON_SPECIAL_CLAUSES = {
    "보증보험_필수": """
임대인은 임차인의 전세보증보험(HUG, SGI 서울보증) 가입에 적극 협조한다.
보증보험 가입이 거절될 경우, 임차인은 계약금 전액을 반환받고 본 계약을 해지할 수 있다.
""",
    
    "전입신고_협조": """
임차인은 잔금 지급일에 전입신고 및 확정일자를 받을 권리가 있으며,
임대인은 이에 필요한 서류(등기권리증 사본 등)를 제공한다.
""",
    
    "시설물_현황": """
본 계약 체결 시 시설물 현황표를 작성하고, 퇴거 시 통상적인 손모를 제외한
시설물 상태로 반환한다. 입주 전 존재하던 하자에 대해서는 임차인이 책임지지 않는다.
""",
    
    "중도_해지": """
임차인이 부득이한 사정으로 중도 해지를 요청하는 경우,
2개월 전 통보를 조건으로 위약금 없이 계약을 해지할 수 있다.
""",
    
    "근저당_변동": """
계약 기간 중 임대인이 근저당권을 추가 설정하거나 
소유권을 이전하는 경우, 사전에 임차인에게 고지하여야 한다.
"""
}


# Test
if __name__ == "__main__":
    agent = NegotiatorAgent()
    
    # 보증보험 요청 테스트
    message = agent.generate_insurance_request(
        sender_name="홍길동",
        risk_details="근저당 비율이 높아 보증보험 가입이 필수적입니다."
    )
    print("=== 보증보험 요청 메시지 ===")
    print(message)
    print()
    
    # 특약 템플릿 출력
    print("=== 보증보험 필수 특약 ===")
    print(COMMON_SPECIAL_CLAUSES["보증보험_필수"])
