from typing import Dict, Any, Optional, List

class FinancialSimulator:
    """
    청년 주거 금융 시뮬레이터 (The Financial Brain)
    사용자의 프로필과 매물 정보를 바탕으로 '실질 월 부담금'을 계산합니다.
    """

    def __init__(self):
        # 2026 Reference Rates (Simplified)
        self.RATES = {
            "sme_loan": 0.012,       # 중기청 1.2%
            "youth_buffer": 0.018,   # 청년버팀목 ~1.8% (평균)
            "normal_bank": 0.045     # 시중은행 ~4.5%
        }
        self.LIMITS = {
            "sme_loan": 100000000,   # 1억
            "youth_buffer": 200000000 # 2억
        }

    def simulate(self, profile: Dict[str, Any], listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        메인 시뮬레이션 함수
        Input: profile(소득, 직장 등), listing(보증금, 월세)
        Output: 최적 대출 상품, 실질 월세, 상세 분석
        """
        
        deposit = listing.get("deposit", 0) * 10000  # 만원 -> 원 단위 변환 check
        # listing data is usually in '10000 KRW', but let's assume raw inputs are handled carefully.
        # Let's standardize: Internal logic uses "Won", Input expects "Won"
        
        target_deposit = listing.get("deposit", 0) # 만원 단위
        target_monthly = listing.get("monthly", 0) # 만원 단위
        
        income = profile.get("income_yearly", 0) # 만원 단위
        age = profile.get("age", 29)
        job = profile.get("employment_type", "unemployed")
        assets = profile.get("total_assets", 0) # 만원 단위
        is_married = profile.get("marital_status", "single") in ("married", "newlywed")
        
        # 1. 대출 상품 탐색 (Loan Strategy)
        best_loan = self._find_best_loan(target_deposit, income, age, job, is_married)
        
        loan_name = best_loan["name"]
        loan_amount = min(best_loan["max_limit"], target_deposit * best_loan["max_ratio"])
        # 자산이 있으면 대출을 줄요? 보통은 풀대출 받고 자산 굴리는게 이득이지만, 여기선 단순화.
        # 실제 필요 대출금 = 보증금 - (보유 현금)? 
        # 전략: "최대 대출" 시나리오로 계산 (현금 세이브 관점)
        
        required_own_money = max(0, target_deposit - loan_amount)
        monthly_interest = (loan_amount * 10000 * best_loan["rate"]) / 12 / 10000 # 만원 단위
        
        # 2. 월세 지원 탐색 (Subsidy Strategy)
        monthly_support = self._check_monthly_support(income, target_deposit, target_monthly, age)
        
        # 3. 최종 계산 (Final Calculation)
        real_monthly_cost = target_monthly + monthly_interest - monthly_support
        
        return {
            "listing": {
                "deposit": target_deposit,
                "monthly": target_monthly
            },
            "recommendation": {
                "loan_product": loan_name,
                "loan_amount": int(loan_amount),
                "loan_rate": f"{best_loan['rate']*100:.1f}%",
                "interest_monthly": int(monthly_interest),
                "subsidy_monthly": int(monthly_support),
                "subsidy_name": "청년월세지원" if monthly_support > 0 else None
            },
            "result": {
                "real_monthly_cost": int(real_monthly_cost),
                "required_own_money": int(required_own_money),
                "summary": self._generate_summary(loan_name, int(real_monthly_cost), int(monthly_support))
            }
        }

    def _find_best_loan(self, deposit, income, age, job, is_married):
        """최적 대출 찾기 로직"""
        # A. 중소기업 취업청년 전월세보증금대출 (1.2%)
        # 조건: 중소기업 재직, 연소득 3500(단독)/5000(부부) 이하
        income_limit = 5000 if is_married else 3500
        if job == "sme" and income <= income_limit and age <= 34:
             return {
                 "name": "중소기업 취업청년 전월세보증금대출",
                 "rate": self.RATES["sme_loan"],
                 "max_limit": 10000, # 1억
                 "max_ratio": 1.0 # 100% (LH/HUG 100% 상품 기준) - 보통 80%지만 공격적 시뮬레이션
             }

        # B. 청년전용 버팀목 (1.5~2.1%)
        # 조건: 소득 5000(단독)/7500(부부) 이하
        income_limit_buf = 7500 if is_married else 5000
        if income <= income_limit_buf and age <= 34:
            # 금리 디테일 (소득 구간별) - 여기선 평균 1.8% 잡음
            return {
                "name": "청년전용 버팀목 전세자금대출",
                "rate": self.RATES["youth_buffer"],
                "max_limit": 20000, # 2억
                "max_ratio": 0.8 # 80%
            }

        # C. 일반 버팀목 or 시중은행
        return {
            "name": "일반 버팀목 / 시중은행 대출",
            "rate": self.RATES["normal_bank"],
            "max_limit": 50000, # 5억
            "max_ratio": 0.8
        }

    def _check_monthly_support(self, income, deposit, monthly, age):
        """서울시 청년 월세 지원 (최대 20만원)"""
        # 조건: 소득 6000이하, 보증금 5000이하, 월세 60이하 (간이 기준)
        if income <= 6000 and deposit <= 5000 and monthly <= 60 and age <= 39:
            return min(monthly, 20) # 최대 20만원, 월세보다 많을순 없음
        return 0

    def _generate_summary(self, loan_name, real_cost, subsidy):
        if subsidy > 0:
            return f"🎉 **{loan_name}** 승인 예상! 월세 지원까지 받으면 실부담금 **{real_cost}만원**입니다."
        else:
            return f"✅ **{loan_name}** 활용 시, 실부담금 **{real_cost}만원**으로 거주 가능합니다."

    # === 전월세 비교 / DSR / 대출 추천 (통합) ===

    def compare_rent_vs_jeonse(self,
                               jeonse_deposit: int,
                               monthly_rent_deposit: int,
                               monthly_rent: int,
                               management_fee: int,
                               loan_rate_percent: float = 4.0) -> Dict[str, Any]:
        """전세 대출 이자 vs 월세 비용 비교 (만원 단위)"""
        loan_amount = jeonse_deposit * 0.8
        monthly_interest = (loan_amount * 10000 * (loan_rate_percent / 100)) / 12 / 10000
        total_jeonse = monthly_interest + management_fee
        total_rent = monthly_rent + management_fee
        diff = total_rent - total_jeonse
        is_jeonse_cheaper = diff > 0

        recommendation = (f"전세 대출이 월 {diff:.1f}만원 더 저렴합니다! 💰"
                          if is_jeonse_cheaper else
                          f"월세가 월 {-diff:.1f}만원 더 저렴합니다. (금리 영향)")

        return {
            "jeonse": {"monthly_cost": total_jeonse, "breakdown": {"interest": monthly_interest, "management": management_fee}},
            "rent": {"monthly_cost": total_rent, "breakdown": {"rent": monthly_rent, "management": management_fee}},
            "difference": diff,
            "is_jeonse_cheaper": is_jeonse_cheaper,
            "recommendation": recommendation
        }

    def check_loan_eligibility(self, annual_income: int, existing_loans: int, target_deposit: int) -> Dict[str, Any]:
        """DSR 기반 대출 가능 여부 간편 진단 (만원 단위)"""
        MAX_DSR = 0.40
        max_annual_repayment = annual_income * MAX_DSR
        existing_annual_repayment = existing_loans * 0.05
        remaining = max_annual_repayment - existing_annual_repayment

        if remaining <= 0:
            return {"status": "불가능", "reason": "기대출 과다로 인한 DSR 한도 초과", "max_loan": 0}

        max_new_loan = remaining / 0.04
        target_loan = target_deposit * 0.8

        if max_new_loan >= target_loan:
            return {"status": "안전", "reason": f"DSR 규제 내에서 충분히 대출 가능합니다. (한도: {max_new_loan:.0f}만원)", "max_loan": max_new_loan}
        return {"status": "주의", "reason": f"목표 대출액({target_loan:.0f}만원)이 한도({max_new_loan:.0f}만원)를 초과할 수 있습니다.", "max_loan": max_new_loan}

    def recommend_loan_product(self, age: int, income: int, employment_type: str, is_sme: bool) -> List[Dict]:
        """프로필 기반 청년 대출 상품 추천"""
        recs = []
        if is_sme and income <= 5000 and age <= 34:
            recs.append({"name": "중소기업 취업청년 전월세보증금대출", "rate": "연 1.2% (고정)", "limit": "최대 1억원 (100%)", "desc": "중소기업 재직자에게 가장 유리한 상품입니다.", "tag": "👑 금리최저", "apply_url": "https://nhuf.molit.go.kr"})
        if income <= 5000 and age <= 34:
            recs.append({"name": "청년버팀목 전세자금대출", "rate": "연 1.8% ~ 2.7%", "limit": "최대 2억원 (80%)", "desc": "가장 일반적인 청년 전용 대출입니다.", "tag": "👍 인기", "apply_url": "https://nhuf.molit.go.kr"})
        if employment_type == "재직자" and age <= 34:
            recs.append({"name": "모바일(카카오/토스) 청년 전세대출", "rate": "연 3.5% ~ 4.5%", "limit": "보증금의 90% 까지", "desc": "은행 방문 없이 앱으로 간편하게 신청 가능합니다.", "tag": "📱 간편", "apply_url": "https://www.kakaobank.com"})
        if not recs:
            recs.append({"name": "버팀목 전세자금대출 (일반)", "rate": "연 2.1% ~ 2.9%", "limit": "수도권 1.2억원", "desc": "청년 전용 상품 조건에 맞지 않을 경우 추천합니다.", "tag": "기본", "apply_url": "https://nhuf.molit.go.kr"})
        return recs
