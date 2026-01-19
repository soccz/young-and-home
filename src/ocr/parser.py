
"""
OCR Parser - 등기부등본/계약서 문서 분석
비용 최소화: GPT-4o-mini 텍스트 분석 (Vision 없이 샘플 데이터 기반)
"""

import os
import base64
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 샘플 등기부등본 데이터 (데모용)
SAMPLE_REGISTRY_DATA = {
    "safe_property": {
        "property_address": "서울특별시 마포구 신촌동 123-45 신촌타워 101호",
        "property_type": "아파트",
        "area": "59.5㎡ (18평)",
        "owner": {
            "name": "김건물",
            "acquisition_date": "2020-03-15",
            "acquisition_reason": "매매"
        },
        "mortgage": [],  # 근저당 없음
        "seizure": [],   # 가압류/압류 없음
        "lease": [],
        "other_rights": []
    },
    "risky_property": {
        "property_address": "서울특별시 강남구 역삼동 789-10 역삼빌라 201호",
        "property_type": "다세대주택",
        "area": "49.5㎡ (15평)",
        "owner": {
            "name": "박임대",
            "acquisition_date": "2018-07-20",
            "acquisition_reason": "매매"
        },
        "mortgage": [
            {
                "creditor": "국민은행",
                "amount": 250000000,  # 2억 5천만원
                "date": "2018-08-01",
                "interest_rate": "연 4.5%"
            },
            {
                "creditor": "신한은행",
                "amount": 100000000,  # 1억원
                "date": "2023-05-15",
                "interest_rate": "연 5.2%"
            }
        ],
        "seizure": [
            {
                "creditor": "서울지방세무서",
                "amount": 5000000,  # 500만원
                "date": "2024-11-20",
                "type": "압류"
            }
        ],
        "lease": [
            {
                "tenant": "이세입",
                "deposit": 150000000,  # 1억 5천만원
                "date": "2022-01-15"
            }
        ],
        "other_rights": []
    },
    "moderate_property": {
        "property_address": "서울특별시 서대문구 연희동 456-78 연희주공 304호",
        "property_type": "아파트",
        "area": "84.9㎡ (26평)",
        "owner": {
            "name": "최안전",
            "acquisition_date": "2015-11-10",
            "acquisition_reason": "매매"
        },
        "mortgage": [
            {
                "creditor": "우리은행",
                "amount": 200000000,  # 2억원
                "date": "2015-12-01",
                "interest_rate": "연 3.8%"
            }
        ],
        "seizure": [],
        "lease": [],
        "other_rights": []
    }
}

# 샘플 계약서 데이터 (데모용 - 등기부와 교차 검증용)
SAMPLE_CONTRACT_DATA = {
    "safe_property": {
        "lessor_name": "김건물",  # 등기부 일치
        "address": "서울특별시 마포구 신촌동 123-45 신촌타워 101호", # 일치
        "deposit": 200000000,
        "contract_date": "2024-01-15",
        "type": "전세"
    },
    "risky_property": {
        "lessor_name": "김사기",  # 등기부(박임대)와 불일치!!!
        "address": "서울특별시 강남구 역삼동 789-10 역삼빌라 201호", # 주소는 일치
        "deposit": 300000000,
        "contract_date": "2024-01-20",
        "type": "전세"
    },
    "moderate_property": {
        "lessor_name": "최안전", # 일치
        "address": "서울특별시 서대문구 연희동 456-78 연희주공 304호",
        "deposit": 250000000,
        "contract_date": "2024-02-01",
        "type": "전세"
    }
}


class RegistryParser:
    """
    등기부등본 및 계약서 파싱 (GPT-4o Vision 활용)
    """
    
    def __init__(self, openai_api_key: str = None):
        self.sample_registry = SAMPLE_REGISTRY_DATA
        self.sample_contract = SAMPLE_CONTRACT_DATA
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=self.api_key)
    
    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def parse_registry(self, file_path: str = None, sample_type: str = "safe") -> Dict[str, Any]:
        """등기부등본 파싱"""
        if file_path and os.path.exists(file_path):
            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png']:
                    return self._analyze_image(file_path, doc_type="registry")
                elif ext == '.pdf':
                    return self._process_pdf(file_path, doc_type="registry")
            except Exception as e:
                print(f"File analysis failed: {e}")
        
        # Fallback
        sample_key = {
            "safe": "safe_property",
            "risky": "risky_property",
            "moderate": "moderate_property"
        }.get(sample_type, "safe_property")
        return self.sample_registry.get(sample_key, self.sample_registry["safe_property"])

    def parse_contract(self, file_path: str = None, sample_type: str = "safe") -> Dict[str, Any]:
        """임대차 계약서 파싱"""
        if file_path and os.path.exists(file_path):
            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png']:
                    return self._analyze_image(file_path, doc_type="contract")
                elif ext == '.pdf':
                    return self._process_pdf(file_path, doc_type="contract")
            except Exception as e:
                print(f"Contract analysis failed: {e}")
        
        # Fallback
        sample_key = {
            "safe": "safe_property",
            "risky": "risky_property",
            "moderate": "moderate_property"
        }.get(sample_type, "safe_property")
        return self.sample_contract.get(sample_key, self.sample_contract["safe_property"])

    def _process_pdf(self, file_path, doc_type="registry"):
        """PDF 처리 공통 로직"""
        try:
            import fitz
            doc = fitz.open(file_path)
            if len(doc) > 0:
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                temp_img = f"temp_{doc_type}_page.png"
                pix.save(temp_img)
                doc.close()
                result = self._analyze_image(temp_img, doc_type=doc_type)
                if os.path.exists(temp_img):
                    os.remove(temp_img)
                return result
        except ImportError:
            # Fallback to pdf2image if available or simple fail
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, first_page=1, last_page=1)
                if images:
                    temp_img = f"temp_{doc_type}_page.jpg"
                    images[0].save(temp_img, "JPEG")
                    result = self._analyze_image(temp_img, doc_type=doc_type)
                    if os.path.exists(temp_img):
                        os.remove(temp_img)
                    return result
            except:
                pass
        return {}

    def _analyze_image(self, image_path: str, doc_type: str = "registry") -> Dict[str, Any]:
        """GPT-4o Vision으로 이미지 분석"""
        base64_image = self._encode_image(image_path)
        
        if doc_type == "registry":
            prompt = """
            이 이미지는 대한민국 등기부등본(등기사항전부증명서)입니다.
            다음 정보를 추출하여 JSON 형식으로 반환:
            {
                "property_address": "주소",
                "property_type": "건물내역 유 (아파트, 다세대 등)",
                "area": "전용면적 (㎡)",
                "owner": {"name": "갑구 최종 소유자명", "acquisition_date": "접수일자", "acquisition_reason": "등기원인"},
                "mortgage": [{"creditor": "채권자", "amount": 채권최고액(정수), "date": "접수일자"}],
                "seizure": [{"creditor": "권리자", "amount": 청구금액(정수), "date": "접수일자", "type": "압류/가압류"}],
                "lease": [{"tenant": "전세권자", "deposit": 전세금(정수), "date": "접수일자"}]
            }
            """
        else:
            prompt = """
            이 이미지는 부동산 임대차 계약서입니다.
            다음 정보를 추출하여 JSON 형식으로 반환:
            {
                "lessor_name": "임대인 이름",
                "address": "소재지",
                "deposit": 보증금(정수),
                "contract_date": "계약일",
                "type": "전세/월세"
            }
            """
            
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt + "\nJSON only, no markdown."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        )
        
        try:
            response = self.llm.invoke([message])
            content = response.content.strip()
            
            if content.startswith("```json"): content = content[7:]
            if content.endswith("```"): content = content[:-3]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"GPT Analysis Failed: {e}")
            return {}

# Alias
DocumentParser = RegistryParser


class RiskAnalyzer:
    """
    등기부등본 기반 위험도 분석
    """
    
    DISTRICT_PRICE_TABLE = {
        "강남구": 5500, "서초구": 4800, "송파구": 4200, "용산구": 4000,
        "성동구": 3500, "광진구": 3200, "마포구": 3200, "영등포구": 3000,
        "동작구": 2900, "서대문구": 2800, "종로구": 2800, "중구": 2700,
        "강동구": 2600, "양천구": 2500, "강서구": 2400, "성북구": 2300,
        "동대문구": 2200, "관악구": 2200, "은평구": 2100, "구로구": 2000,
        "노원구": 1900, "도봉구": 1800, "금천구": 1800, "중랑구": 1700,
        "강북구": 1600,
    }
    
    def __init__(self):
        pass
    
    def _extract_district(self, address: str) -> str:
        for district in self.DISTRICT_PRICE_TABLE:
            if district in address:
                return district
        return ""
    
    def _estimate_market_value(self, address: str, area_sqm: float) -> int:
        district = self._extract_district(address)
        price_per_pyeong = self.DISTRICT_PRICE_TABLE.get(district, 2500)
        pyeong = area_sqm / 3.3058
        estimated_value = int(price_per_pyeong * pyeong * 10000)
        return max(estimated_value, 150000000)
    
    def analyze(self, registry_data: Dict[str, Any], deposit: int = 0) -> Dict[str, Any]:
        risks = []
        risk_score = 0
        
        if not registry_data:
            return {"risk_score": 0, "risk_level": "분석 불가", "risks": [], "recommendation": "문서를 분석할 수 없습니다."}

        mortgages = registry_data.get("mortgage", [])
        total_mortgage = sum(m.get("amount", 0) for m in mortgages)
        
        if mortgages:
            if len(mortgages) > 1:
                risks.append({"type": "근저당 다중설정", "severity": "높음", "description": f"근저당권 {len(mortgages)}건: {total_mortgage/10000:,.0f}만원"})
                risk_score += 30
            else:
                risks.append({"type": "근저당 설정", "severity": "보통", "description": f"근저당권 설정: {total_mortgage/10000:,.0f}만원"})
                risk_score += 15
        
        seizures = registry_data.get("seizure", [])
        total_seizure = 0
        if seizures:
            total_seizure = sum(s.get("amount", 0) for s in seizures)
            risks.append({"type": "압류/가압류", "severity": "매우높음", "description": f"압류/가압류 {len(seizures)}건 존재!"})
            risk_score += 40
        
        leases = registry_data.get("lease", [])
        total_lease = 0
        if leases:
            total_lease = sum(l.get("deposit", 0) for l in leases)
            risks.append({"type": "선순위 임차인", "severity": "높음", "description": f"선순위 임차인 {len(leases)}명 존재"})
            risk_score += 25
        
        if deposit > 0:
            total_debt = total_mortgage + total_lease
            address = registry_data.get("property_address", "")
            try:
                area_sqm = float(registry_data.get("area", "59.5").split("㎡")[0].strip())
            except:
                area_sqm = 59.5
            
            estimated_value = self._estimate_market_value(address, area_sqm)
            safe_limit = estimated_value * 0.7
            
            if total_debt + deposit > safe_limit:
                risks.append({"type": "채권초과 위험", "severity": "매우높음", "description": f"총 채권이 시세의 70% 초과 (깡통전세 위험)"})
                risk_score += 35
            elif total_debt + deposit > safe_limit * 0.9:
                risks.append({"type": "채권 근접 경고", "severity": "보통", "description": "총 채권이 안전 기준에 근접"})
                risk_score += 10
        
        if risk_score >= 60:
            risk_level = "위험"
            recommendation = "계약을 권장하지 않습니다."
        elif risk_score >= 30:
            risk_level = "주의"
            recommendation = "전세보증보험 가입 필수."
        else:
            risk_level = "안전"
            recommendation = "대체로 안전하나 보험 가입 권장."
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risks": risks,
            "recommendation": recommendation,
            "total_mortgage": total_mortgage,
            "estimated_value": estimated_value if deposit > 0 else 0
        }
