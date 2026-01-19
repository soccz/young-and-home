"""
RAG Document Loader - 혜택 데이터 로더
비용 최소화: sentence-transformers (무료, 로컬) 사용
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path


class BenefitDocument:
    """혜택 문서 클래스"""
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.page_content = content
        self.metadata = metadata


class BenefitLoader:
    """
    복지/혜택 JSON 데이터를 RAG용 문서로 변환
    """
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            # 프로젝트 루트 기준 경로
            base_dir = Path(__file__).parent.parent.parent
            data_path = base_dir / "data" / "welfare" / "benefits.json"
        self.data_path = Path(data_path)
    
    def load(self) -> List[BenefitDocument]:
        """혜택 데이터를 문서 리스트로 로드"""
        if not self.data_path.exists():
            print(f"Warning: {self.data_path} not found")
            return []
        
        with open(self.data_path, "r", encoding="utf-8") as f:
            benefits = json.load(f)
        
        documents = []
        for benefit in benefits:
            # 검색용 텍스트 생성
            content = self._create_content(benefit)
            
            # 메타데이터 추출
            metadata = {
                "id": benefit.get("id"),
                "name": benefit.get("name"),
                "category": benefit.get("category"),
                "provider": benefit.get("provider"),
                "url": benefit.get("url"),
            }
            
            documents.append(BenefitDocument(content, metadata))
        
        return documents
    
    def _create_content(self, benefit: Dict) -> str:
        """검색용 텍스트 콘텐츠 생성"""
        eligibility = benefit.get("eligibility", {})
        benefit_info = benefit.get("benefit", {})
        
        # 대상 조건 문자열화
        target_conditions = []
        if eligibility.get("age_min") or eligibility.get("age_max"):
            age_min = eligibility.get("age_min", "")
            age_max = eligibility.get("age_max", "")
            target_conditions.append(f"나이: {age_min}~{age_max}세")
        
        if eligibility.get("income_max"):
            target_conditions.append(f"소득: {eligibility['income_max']}{eligibility.get('income_unit', '')}")
        
        if eligibility.get("required_status"):
            target_conditions.append(f"대상: {', '.join(eligibility['required_status'])}")
        
        # 혜택 내용 문자열화
        benefit_details = []
        if benefit_info.get("amount"):
            benefit_details.append(f"지원금: {benefit_info['amount']:,}{benefit_info.get('unit', '')}")
        if benefit_info.get("loan_max"):
            benefit_details.append(f"대출한도: {benefit_info['loan_max']:,}{benefit_info.get('loan_unit', '만원')}")
        if benefit_info.get("rent_ratio"):
            benefit_details.append(f"임대료: {benefit_info['rent_ratio']}")
        if benefit_info.get("interest_rate"):
            benefit_details.append(f"금리: {benefit_info['interest_rate']}%")
        
        content = f"""
혜택명: {benefit.get('name')}
카테고리: {benefit.get('category')}
제공기관: {benefit.get('provider')}
설명: {benefit.get('description')}

신청자격:
{chr(10).join('- ' + c for c in target_conditions)}

혜택내용:
{chr(10).join('- ' + d for d in benefit_details)}
        """.strip()
        
        return content


if __name__ == "__main__":
    loader = BenefitLoader()
    docs = loader.load()
    print(f"Loaded {len(docs)} benefit documents")
    for doc in docs[:2]:
        print("---")
        print(doc.page_content[:200])
