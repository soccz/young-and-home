from typing import Dict, Any

class FinancialAgent:
    """
    Agent responsible for financial calculations related to housing.
    Logic includes:
    1. Jeonse (Deposit) vs Monthly Rent comparison.
    2. DSR (Debt Service Ratio) based loan eligibility check.
    """

    def __init__(self):
        pass

    def compare_rent_vs_jeonse(self, 
                             jeonse_deposit: int, 
                             monthly_rent_deposit: int, 
                             monthly_rent: int, 
                             management_fee: int,
                             loan_rate_percent: float = 4.0) -> Dict[str, Any]:
        """
        Compare the monthly cost of Jeonse (via loan) vs Monthly Rent.
        
        Args:
            jeonse_deposit (int): Total deposit for Jeonse (10k KRW).
            monthly_rent_deposit (int): Deposit for monthly rent case (10k KRW).
            monthly_rent (int): Monthly rent amount (10k KRW).
            management_fee (int): Monthly management fee (10k KRW).
            loan_rate_percent (float): Annual interest rate for Jeonse loan (%).

        Returns:
            Dict containing comparison results and recommendation.
        """
        # 1. Jeonse Cost Calculation
        # Assume user can get 80% loan for Jeonse
        loan_amount = jeonse_deposit * 0.8
        self_funding = jeonse_deposit * 0.2
        
        # Monthly interest cost
        # loan_amount (10k) * rate * 10000 / 12
        monthly_interest = (loan_amount * 10000 * (loan_rate_percent / 100)) / 12
        monthly_interest_10k = monthly_interest / 10000
        
        total_jeonse_monthly_cost = monthly_interest_10k + management_fee
        
        # 2. Monthly Rent Cost Calculation
        # Opportunity cost of deposit is ignored for simplicity in this MVP, or can be added.
        # Let's keep it simple: Rent + Manage Fee
        total_rent_monthly_cost = monthly_rent + management_fee
        
        # 3. Comparison
        diff = total_rent_monthly_cost - total_jeonse_monthly_cost
        is_jeonse_cheaper = diff > 0
        
        recommendation = ""
        if is_jeonse_cheaper:
            recommendation = f"전세 대출이 월 {diff:.1f}만원 더 저렴합니다! 💰"
        else:
            recommendation = f"월세가 월 {-diff:.1f}만원 더 저렴합니다. (금리 영향)"
            
        return {
            "jeonse": {
                "monthly_cost": total_jeonse_monthly_cost,
                "breakdown": {
                    "interest": monthly_interest_10k,
                    "management": management_fee
                }
            },
            "rent": {
                "monthly_cost": total_rent_monthly_cost,
                "breakdown": {
                    "rent": monthly_rent,
                    "management": management_fee
                }
            },
            "difference": diff,
            "is_jeonse_cheaper": is_jeonse_cheaper,
            "recommendation": recommendation
        }

    def check_loan_eligibility(self, 
                             annual_income: int, 
                             existing_loans: int, 
                             target_deposit: int) -> Dict[str, Any]:
        """
        Check loan eligibility based on simplified DSR logic.
        
        Args:
            annual_income (int): Annual income (10k KRW).
            existing_loans (int): Existing total loan amount (10k KRW).
            target_deposit (int): Target house deposit (10k KRW).
            
        Returns:
            Dict with eligibility status.
        """
        # Assumptions for MVP
        MAX_DSR = 0.40  # 40%
        ASSUMED_RATE = 0.05  # 5% for stress test
        
        # 1. Estimate maximum loan possible
        # Max annual repayment = Income * DSR
        max_annual_repayment = annual_income * MAX_DSR
        
        # Existing annual repayment (approximate interest only for bullet loans or amortized)
        # Let's assume existing loans pay 5% interest
        existing_annual_repayment = existing_loans * 0.05
        
        remaining_repayment_capacity = max_annual_repayment - existing_annual_repayment
        
        if remaining_repayment_capacity <= 0:
            return {
                "status": "불가능",
                "reason": "기대출 과다로 인한 DSR 한도 초과",
                "max_loan": 0
            }
            
        # Max new loan principal = Capacity / Rate (assuming interest only for Jeonse loan simplicity)
        # Or Principal = Capacity / (Rate + 1/Maturity)??
        # Jeonse loans are typically interest-only for the duration.
        max_new_loan = remaining_repayment_capacity / 0.04  # Assuming 4% for new loan
        
        # Target loan (80% of deposit)
        target_loan = target_deposit * 0.8
        
        if max_new_loan >= target_loan:
            return {
                "status": "안전",
                "reason": f"DSR 규제 내에서 충분히 대출 가능합니다. (한도: {max_new_loan:.0f}만원)",
                "max_loan": max_new_loan
            }
        else:
            return {
                "status": "주의",
                "reason": f"목표 대출액({target_loan:.0f}만원)이 한도({max_new_loan:.0f}만원)를 초과할 수 있습니다.",
                "max_loan": max_new_loan
            }

    def recommend_loan_product(self, age: int, income: int, employment_type: str, is_sme: bool) -> list:
        """
        Recommend youth-specific loan products based on user profile.
        
        Args:
            age: Integer age
            income: Annual income in 10k KRW (e.g. 3500)
            employment_type: '재직자', '취업준비생', '프리랜서'
            is_sme: Boolean, true if working at small/medium enterprise
            
        Returns:
            List of dictionaries containing loan product details.
        """
        recommendations = []
        
        # 1. 중소기업 취업청년 전월세보증금대출 (Best for SME)
        if is_sme and income <= 5000 and age <= 34:
            recommendations.append({
                "name": "중소기업 취업청년 전월세보증금대출",
                "rate": "연 1.5% (고정)",
                "limit": "최대 1억원 (100%)",
                "desc": "중소기업 재직자에게 가장 유리한 상품입니다. 금리가 매우 낮습니다.",
                "tag": "👑 금리최저"
            })
            
        # 2. 청년버팀목 전세자금대출 (General Youth)
        if income <= 5000 and age <= 34:
            recommendations.append({
                "name": "청년버팀목 전세자금대출",
                "rate": "연 1.8% ~ 2.7%",
                "limit": "최대 2억원 (80%)",
                "desc": "가장 일반적인 청년 전용 대출입니다. 소득에 따라 금리가 달라집니다.",
                "tag": "👍 인기"
            })
            
        # 3. 카카오뱅크/토스 청년 전월세보증금대출 (Easy)
        if employment_type == "재직자" and age <= 34:
            recommendations.append({
                "name": "모바일(카카오/토스) 청년 전세대출",
                "rate": "연 3.5% ~ 4.5%",
                "limit": "보증금의 90% 까지",
                "desc": "은행 방문 없이 앱으로 간편하게 신청 가능합니다. (HUG 보증)",
                "tag": "📱 간편"
            })
            
        if not recommendations:
            recommendations.append({
                "name": "버팀목 전세자금대출 (일반)",
                "rate": "연 2.1% ~ 2.9%",
                "limit": "수도권 1.2억원",
                "desc": "청년 전용 상품 조건에 맞지 않을 경우 추천합니다.",
                "tag": "기본"
            })
            
        return recommendations
