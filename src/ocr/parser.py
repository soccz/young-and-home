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


class RegistryParser:
    """
    등기부등본 및 계약서 파싱 (GPT-4o Vision 활용)
    """
    
    def __init__(self, openai_api_key: str = None):
        self.sample_data = SAMPLE_REGISTRY_DATA
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=self.api_key)
    
    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def parse_registry(self, file_path: str = None, sample_type: str = "safe") -> Dict[str, Any]:
        """
        등기부등본 파싱
        
        Args:
            file_path: 파일 경로 (PDF 또는 이미지)
            sample_type: 데모용 샘플 타입 (파일 없을 경우 사용)
        """
        if file_path and os.path.exists(file_path):
            try:
                # 파일 확장자 확인
                ext = os.path.splitext(file_path)[1].lower()
                
                # 이미지 파일인 경우 바로 처리
                if ext in ['.jpg', '.jpeg', '.png']:
                    return self._analyze_image(file_path)
                
                # PDF인 경우 - pymupdf (fitz) 우선 시도
                elif ext == '.pdf':
                    # 방법 1: pymupdf (fitz) - poppler 불필요
                    try:
                        import fitz  # pymupdf
                        doc = fitz.open(file_path)
                        if len(doc) > 0:
                            # 첫 페이지를 이미지로 변환
                            page = doc[0]
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 해상도
                            temp_img = "temp_registry_page.png"
                            pix.save(temp_img)
                            doc.close()
                            result = self._analyze_image(temp_img)
                            if os.path.exists(temp_img):
                                os.remove(temp_img)
                            return result
                    except ImportError:
                        print("pymupdf not installed, trying pdf2image...")
                    except Exception as e:
                        print(f"pymupdf error: {e}, trying pdf2image...")
                    
                    # 방법 2: pdf2image fallback (poppler 필요)
                    try:
                        from pdf2image import convert_from_path
                        images = convert_from_path(file_path, first_page=1, last_page=2)
                        if images:
                            temp_img = "temp_registry_page.jpg"
                            images[0].save(temp_img, "JPEG")
                            result = self._analyze_image(temp_img)
                            if os.path.exists(temp_img):
                                os.remove(temp_img)
                            return result
                    except ImportError:
                        print("pdf2image not installed, falling back to sample")
                    except Exception as e:
                        print(f"PDF processing error: {e}")
                        
            except Exception as e:
                print(f"File analysis failed: {e}")
        
        # Fallback: 샘플 데이터 반환
        print(f"Using sample data: {sample_type}")
        sample_key = {
            "safe": "safe_property",
            "risky": "risky_property",
            "moderate": "moderate_property"
        }.get(sample_type, "safe_property")
        
        return self.sample_data.get(sample_key, self.sample_data["safe_property"])

    def _analyze_image(self, image_path: str) -> Dict[str, Any]:
        """GPT-4o Vision으로 이미지 분석"""
        base64_image = self._encode_image(image_path)
        
        prompt = """
        이 이미지는 대한민국 등기부등본(등기사항전부증명서)입니다.
        다음 정보를 추출하여 JSON 형식으로 반환해주세요.
        응답은 오직 JSON만 반환해야 하며 markdown code block을 포함하지 마세요.
        
        {
            "property_address": "주소",
            "property_type": "건물내역에 따른 유형 (아파트, 빌라, 다세대 등)",
            "area": "전용면적 (㎡)",
            "owner": {
                "name": "소유자명 (갑구 마지막 소유권 이전 내용)",
                "acquisition_date": "접수일자",
                "acquisition_reason": "등기원인"
            },
            "mortgage": [
                {
                    "creditor": "근저당권자 (을구)",
                    "amount": 123456789 (채권최고액, 숫자만),
                    "date": "접수일자",
                    "interest_rate": "있는 경우만"
                }
            ],
            "seizure": [
                {
                    "creditor": "권리자 (갑구/을구의 압류/가압류)",
                    "amount": 금액 (숫자만),
                    "date": "접수일자",
                    "type": "압류 또는 가압류"
                }
            ],
            "lease": [
                {
                    "tenant": "전세권 설정이 있는 경우 전세권자",
                    "deposit": 전세금 (숫자만),
                    "date": "접수일자"
                }
            ]
        }
        
        값이 없거나 불확실하면 빈 리스트 [] 또는 ""로 처리하세요.
        금액은 반드시 정수형(Integer)으로 변환하세요. (예: "금 120,000,000원" -> 120000000)
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        )
        
        response = self.llm.invoke([message])
        content = response.content.strip()
        
        # JSON 파싱 (Markdown code block 제거)
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            return json.loads(content.strip())
        except:
            # 파싱 실패 시 빈 딕셔너리 반환하지 말고 샘플 리턴? 아니면 에러 로깅
            print(f"Failed to parse JSON response: {content}")
            return {}

# 하위 호환성을 위해 Alias 제공
DocumentParser = RegistryParser


class RiskAnalyzer:
    """
    등기부등본 기반 위험도 분석
    """
    
    # 서울 구별 평당가 (2024년 기준, 만원/평)
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
        """주소에서 구 이름 추출"""
        for district in self.DISTRICT_PRICE_TABLE:
            if district in address:
                return district
        return ""
    
    def _estimate_market_value(self, address: str, area_sqm: float) -> int:
        """
        지역 + 면적 기반 시세 추정
        
        Args:
            address: 주소 문자열 (구 포함)
            area_sqm: 전용면적 (㎡)
        
        Returns:
            추정 시세 (원)
        """
        district = self._extract_district(address)
        
        # 평당가 조회 (없으면 기본값 2500만원/평)
        price_per_pyeong = self.DISTRICT_PRICE_TABLE.get(district, 2500)
        
        # ㎡ → 평 변환 (1평 = 3.3058㎡)
        pyeong = area_sqm / 3.3058
        
        # 시세 계산 (만원 → 원)
        estimated_value = int(price_per_pyeong * pyeong * 10000)
        
        # 최소 시세 1.5억 보장 (원룸 등)
        return max(estimated_value, 150000000)
    
    def analyze(self, registry_data: Dict[str, Any], deposit: int = 0) -> Dict[str, Any]:
        """
        위험도 분석 수행
        """
        risks = []
        risk_score = 0  # 0-100, 높을수록 위험
        
        # 데이터가 없을 경우 처리
        if not registry_data:
            return {
                "risk_score": 0,
                "risk_level": "분석 불가",
                "risks": [],
                "recommendation": "문서를 분석할 수 없습니다.",
                "total_mortgage": 0,
                "total_seizure": 0,
                "total_prior_lease": 0
            }

        # 1. 근저당 분석
        mortgages = registry_data.get("mortgage", [])
        total_mortgage = sum(m.get("amount", 0) for m in mortgages)
        
        if mortgages:
            mortgage_count = len(mortgages)
            if mortgage_count > 1:
                risks.append({
                    "type": "근저당 다중설정",
                    "severity": "높음",
                    "description": f"근저당권이 {mortgage_count}건 설정되어 있습니다. 총 {total_mortgage/10000:,.0f}만원"
                })
                risk_score += 30
            else:
                risks.append({
                    "type": "근저당 설정",
                    "severity": "보통",
                    "description": f"근저당권이 설정되어 있습니다. {total_mortgage/10000:,.0f}만원"
                })
                risk_score += 15
        
        # 2. 압류/가압류 분석
        seizures = registry_data.get("seizure", [])
        if seizures:
            total_seizure = sum(s.get("amount", 0) for s in seizures)
            risks.append({
                "type": "압류/가압류",
                "severity": "매우높음",
                "description": f"압류/가압류가 {len(seizures)}건 있습니다. 총 {total_seizure/10000:,.0f}만원. 계약 전 해제 필수!"
            })
            risk_score += 40
        else:
            total_seizure = 0 # Initialize variable
        
        # 3. 기존 임차인 분석
        leases = registry_data.get("lease", [])
        if leases:
            total_lease = sum(l.get("deposit", 0) for l in leases)
            risks.append({
                "type": "선순위 임차인",
                "severity": "높음",
                "description": f"선순위 임차인이 {len(leases)}명 있습니다. 보증금 합계 {total_lease/10000:,.0f}만원"
            })
            risk_score += 25
        else:
            total_lease = 0 # Initialize variable
        
        # 4. 채권 초과 분석 (전세금 안전성) - 지역별 시세 기반
        if deposit > 0:
            total_debt = total_mortgage + total_lease
            
            # 지역 + 면적 기반 시세 추정
            address = registry_data.get("property_address", "")
            area_str = registry_data.get("area", "59.5㎡")
            try:
                # "59.5㎡ (18평)" 형태에서 숫자만 추출
                area_sqm = float(area_str.replace("㎡", "").split()[0].replace(",", ""))
            except:
                area_sqm = 59.5  # 기본값
            
            # 동적 시세 추정 (지역별 평당가 적용)
            estimated_value = self._estimate_market_value(address, area_sqm)
            safe_limit = estimated_value * 0.7  # 시세의 70%가 안전 기준
            
            # 시세 정보 추가
            district = self._extract_district(address) or "미확인"
            
            if total_debt + deposit > safe_limit:
                risks.append({
                    "type": "채권초과 위험",
                    "severity": "매우높음",
                    "description": f"전세금 포함 총 채권({(total_debt + deposit)/10000:,.0f}만원)이 추정 시세({estimated_value/10000:,.0f}만원, {district})의 70%를 초과합니다."
                })
                risk_score += 35
            elif total_debt + deposit > safe_limit * 0.9:
                # 경고 추가: 70% 근접
                risks.append({
                    "type": "채권 근접 경고",
                    "severity": "보통",
                    "description": f"총 채권이 안전 기준({safe_limit/10000:,.0f}만원)에 근접합니다. 추정 시세: {estimated_value/10000:,.0f}만원 ({district})"
                })
                risk_score += 10
        
        # 위험 등급 결정
        if risk_score >= 60:
            risk_level = "위험"
            recommendation = "계약을 권장하지 않습니다. 반드시 전문가 상담 후 결정하세요."
        elif risk_score >= 30:
            risk_level = "주의"
            recommendation = "전세보증보험 가입을 강력히 권장합니다. 특약 조항 추가를 요청하세요."
        else:
            risk_level = "안전"
            recommendation = "비교적 안전한 매물입니다. 전세보증보험 가입을 권장합니다."
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risks": risks,
            "recommendation": recommendation,
            "total_mortgage": total_mortgage,
            "total_seizure": total_seizure,
            "total_prior_lease": total_lease
        }


if __name__ == "__main__":
    parser = RegistryParser()
    analyzer = RiskAnalyzer()
    
    # 테스트: 위험한 매물 분석 (샘플)
    print("=== 위험 매물 분석 ===")
    risky = parser.parse_registry(sample_type="risky")
    result = analyzer.analyze(risky, deposit=200000000)
    print(f"위험 점수: {result['risk_score']}/100")
    print(f"위험 등급: {result['risk_level']}")
