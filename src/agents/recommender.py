"""
Recommender Agent - 맞춤형 주거 추천 에이전트
"""

from typing import TypedDict, Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import operator


def _format_man_won(amount_man: int) -> str:
    """만원 단위를 읽기 좋게 변환 (10000만→1억, 3500만→3,500만원)"""
    if amount_man >= 10000:
        eok = amount_man // 10000
        remainder = amount_man % 10000
        if remainder:
            return f"{eok}억 {remainder:,}만원"
        return f"{eok}억원"
    return f"{amount_man:,}만원"


class RecommenderState(TypedDict):
    """에이전트 상태 정의"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_profile: dict
    benefits: list
    recommendations: list
    current_step: str


class RecommenderAgent:
    """
    사용자 상황에 맞는 주거 추천 & 혜택 매칭 에이전트
    
    Flow:
    1. profile_collector: 사용자 정보 수집 (나이, 소득, 자산 등)
    2. benefit_matcher: 받을 수 있는 정부 혜택 매칭 (RAG)
    3. house_recommender: 조건에 맞는 매물 추천
    4. report_generator: 최종 리포트 생성
    """
    
    def __init__(self, openai_api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=openai_api_key
        )
        self.graph = self._build_graph()
        self.language = "KO"
        self._user_profile = None  # 외부에서 전달받은 프로필 저장

    def set_language(self, language: str):
        self.language = language
    
    def set_user_profile(self, profile: dict):
        """외부에서 사용자 프로필 설정"""
        self._user_profile = profile
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(RecommenderState)
        
        # 노드 추가
        workflow.add_node("profile_collector", self._collect_profile)
        workflow.add_node("benefit_matcher", self._match_benefits)
        workflow.add_node("house_recommender", self._recommend_houses)
        workflow.add_node("report_generator", self._generate_report)
        
        # 엣지 연결
        workflow.set_entry_point("profile_collector")
        workflow.add_edge("profile_collector", "benefit_matcher")
        workflow.add_edge("benefit_matcher", "house_recommender")
        workflow.add_edge("house_recommender", "report_generator")
        workflow.add_edge("report_generator", END)
        
        return workflow.compile()
    
    def _collect_profile(self, state: RecommenderState) -> dict:
        """사용자 프로필 수집 및 정리"""
        # 외부에서 전달받은 프로필이 있으면 사용
        if self._user_profile:
            profile = self._user_profile
        else:
            # Fallback: 기본값
            profile = {
                "age": 25,
                "status": "대학생",
                "income": 0,  # 만원
                "assets": 2000,  # 만원
                "location_preference": "신촌",
                "max_commute": 30,  # 분
                "max_rent": 50,  # 만원
            }
        
        return {
            "user_profile": profile,
            "current_step": "benefit_matcher",
            "messages": [AIMessage(content="프로필 정보를 수집했습니다.")]
        }
    
    def _load_benefits_db(self):
        """혜택 DB를 한 번만 로드 (캐시)"""
        if not hasattr(self, '_benefits_cache'):
            import json
            try:
                with open("data/welfare/benefits.json", "r", encoding="utf-8") as f:
                    all_benefits = json.load(f)
                self._benefits_cache = {b["id"]: b for b in all_benefits}
                self._all_benefits_list = all_benefits
            except Exception:
                self._benefits_cache = {}
                self._all_benefits_list = []
        return self._benefits_cache, self._all_benefits_list

    def _filter_and_format_benefits(self, candidate_ids: set, profile: dict) -> list:
        """공통 혜택 필터링 + 포맷팅 로직"""
        benefits_db, all_benefits = self._load_benefits_db()
        user_age = profile.get("age", 25)
        user_income = profile.get("income", 0)

        # 주거대출은 항상 후보에 포함
        for b in all_benefits:
            if b.get("category") == "주거대출":
                candidate_ids.add(b["id"])

        final = []
        for bid in candidate_ids:
            benefit = benefits_db.get(bid)
            if not benefit:
                continue
            elig = benefit.get("eligibility", {})

            # 나이 검증
            age_min = elig.get("age_min", 0)
            age_max = elig.get("age_max") or 100
            if not (age_min <= user_age <= age_max):
                continue

            # 소득 검증
            if elig.get("income_unit") == "만원/년" and user_income > elig.get("income_max", 999999):
                continue

            # 포맷 (원/만원 단위 자동 변환)
            b_info = benefit.get("benefit", {})
            raw_amount = b_info.get("amount", b_info.get("loan_max", b_info.get("amount_max", "확인필요")))
            amount_str = str(raw_amount)
            if amount_str.isdigit():
                num = int(amount_str)
                unit = b_info.get("unit", b_info.get("loan_unit", ""))
                if "원" in unit and "만" not in unit and num >= 10000:
                    amount_str = f"{num // 10000:,}만원/월"
                elif num >= 10000 and not unit:
                    amount_str = _format_man_won(num // 10000)
                else:
                    amount_str = _format_man_won(num)

            is_loan = benefit.get("category") == "주거대출"
            final.append({
                "id": benefit["id"],
                "name": f"{'[기본]' if is_loan else '[추천]'} {benefit['name']}",
                "category": benefit.get("category"),
                "provider": benefit.get("provider"),
                "amount": amount_str,
                "url": benefit.get("url"),
                "is_base": is_loan
            })

        final.sort(key=lambda x: (not x['is_base'], x['category']))
        return final[:7]

    def _match_benefits(self, state: RecommenderState) -> dict:
        """RAG를 활용한 혜택 매칭 + 자격 조건 필터링"""
        profile = state.get("user_profile", {})
        user_age = profile.get("age", 25)

        candidate_ids = set()

        # RAG 검색 시도 (retriever 캐싱)
        try:
            from src.rag.retriever import BenefitRetriever
            if not hasattr(self, '_retriever'):
                self._retriever = BenefitRetriever()
            retriever = self._retriever

            status = profile.get("status", "청년")
            location = profile.get("location_preference", "서울")
            max_rent = profile.get("max_rent", 50)
            query = f"{status} {location} 월세 {max_rent}만원 주거 지원"

            # age_max가 null인 혜택도 포함되도록 $or 필터 사용
            rag_filters = {
                "$and": [
                    {"age_min": {"$lte": user_age}}
                ]
            }
            search_results = retriever.search(query, n_results=5, filters=rag_filters)

            for result in search_results:
                bid = result.get("metadata", {}).get("id")
                if bid:
                    candidate_ids.add(bid)

        except Exception as e:
            print(f"RAG search failed: {e}, falling back to JSON")
            # Fallback: 전체 혜택에서 나이 매칭
            _, all_benefits = self._load_benefits_db()
            for b in all_benefits:
                candidate_ids.add(b.get("id"))

        matched = self._filter_and_format_benefits(candidate_ids, profile)

        return {
            "benefits": matched,
            "current_step": "house_recommender",
            "messages": [AIMessage(content=f"{len(matched)}개의 맞춤 혜택을 찾았습니다.")]
        }
    
    def _score_house(self, house: dict, profile: dict) -> float:
        """매물 점수 계산 (높을수록 좋음)"""
        score = 0.0
        
        # 1. 위험도 점수 (최우선)
        risk_level = house.get("risk_level", "보통")
        if risk_level == "안전":
            score += 30
        elif risk_level == "보통":
            score += 15
        elif risk_level == "주의":
            score += 5
        # 고위험은 0점
        
        # 2. 예산 적합도
        max_monthly = profile.get("max_rent", 50)
        monthly = house.get("monthly", 0)
        if monthly <= max_monthly:
            score += 25
        elif monthly <= max_monthly * 1.1:
            score += 15
        elif monthly <= max_monthly * 1.2:
            score += 5
        
        # 3. 통근 시간
        max_commute = profile.get("max_commute", 30)
        commute = house.get("commute_time", 999)
        if commute <= max_commute * 0.5:
            score += 20  # 목표의 절반 이하
        elif commute <= max_commute:
            score += 15
        elif commute <= max_commute * 1.2:
            score += 5
        
        # 4. 주거 타입 가산점
        house_type = house.get("type", "")
        if "공공" in house_type:
            score += 10  # 공공임대 우선
        
        # 5. 특수 기능 가산점
        features = house.get("features", [])
        if "신축" in features:
            score += 5
        if "풀옵션" in features:
            score += 5
        
        return score
    
    def _load_houses(self):
        """매물 DB 로드 (캐시)"""
        if not hasattr(self, '_houses_cache'):
            import json, os
            try:
                db_path = "data/housing/houses.json"
                if os.path.exists(db_path):
                    with open(db_path, "r", encoding="utf-8") as f:
                        self._houses_cache = json.load(f)
                else:
                    self._houses_cache = []
            except Exception:
                self._houses_cache = []
        return self._houses_cache

    def _recommend_houses(self, state: RecommenderState) -> dict:
        """조건에 맞는 매물 추천 (스코어링 + 위험 필터링)"""
        profile = state.get("user_profile", {})
        houses = self._load_houses()
            
        # 데이터가 없으면 빈 리스트
        if not houses:
            # Fallback mock data
            recommendations = [
                {
                    "name": "SH 신촌 행복주택",
                    "type": "공공임대",
                    "deposit": 500,
                    "monthly": 35,
                    "location": "신촌역 도보 10분",
                    "commute_time": 15,
                    "risk_level": "안전"
                }
            ]
        else:
            recommendations = houses
            
        # 2. 필터링 + 스코어링
        scored_houses = []
        
        target_loc = profile.get("location_preference", "")
        max_deposit = profile.get("assets", 2000)
        max_monthly = profile.get("max_rent", 50)
        max_commute = profile.get("max_commute", 30)
        
        for house in recommendations:
            # 고위험 매물 자동 제외
            if house.get("risk_level") == "고위험":
                continue
            
            # 지역 필터링
            if target_loc:
                loc_match = (target_loc in house.get("location", "")) or \
                            (target_loc in house.get("address", "")) or \
                            (target_loc in house.get("name", ""))
                if not loc_match:
                    continue
            
            # 예산 필터링 (보증금: 자산의 150%까지 - 대출 고려)
            if house.get("deposit", 0) > max_deposit * 1.5: 
                continue
            
            # 월세 필터링 (희망 월세 + 30% 까지)
            if house.get("monthly", 0) > max_monthly * 1.3:
                continue
            
            # 통근 시간 필터링 (50% 초과까지 허용)
            if house.get("commute_time", 999) > max_commute * 1.5:
                continue
            
            # 점수 계산
            score = self._score_house(house, profile)
            
            # 주의 매물 마킹
            if house.get("risk_level") == "주의":
                house["_warning"] = "⚠️ 안전 분석 권장"
                
            # ----- [Deep Agent] Real Cost Calculation -----
            try:
                from src.agents.finance_agent import FinancialSimulator
                sim_profile = {
                    "income_yearly": profile.get("income", 0),
                    "total_assets": profile.get("assets", 2000),
                    "employment_type": profile.get("employment_type", "unemployed"),
                    "age": profile.get("age", 29),
                    "marital_status": profile.get("marital_status", "single")
                }

                if not hasattr(self, '_fin_sim'):
                    self._fin_sim = FinancialSimulator()
                sim_result = self._fin_sim.simulate(sim_profile, house)
                
                # Enrich House Data
                real_cost = sim_result["result"]["real_monthly_cost"]
                loan_name = sim_result["recommendation"]["loan_product"]
                
                house["real_monthly_cost"] = real_cost
                house["best_loan"] = loan_name
                house["_badge"] = f"실질월세 {real_cost}만"
                
            except Exception as e:
                print(f"Finance Sim Failed: {e}")
                house["real_monthly_cost"] = house.get("monthly", 0)
            # ----------------------------------------------
            
            scored_houses.append((score, house))
        
        # 3. 점수 기반 정렬 (높은 점수 우선)
        scored_houses.sort(key=lambda x: x[0], reverse=True)
        
        # 조건에 맞는 매물 없으면 전체에서 상위 (고위험 제외)
        if not scored_houses:
            safe_houses = [h for h in recommendations if h.get("risk_level") != "고위험"]
            for h in safe_houses[:3]:
                scored_houses.append((0, h))
        
        # 상위 5개 추천 (더 많은 선택지 제공)
        top_picks = [house for _, house in scored_houses[:5]]
        
        return {
            "recommendations": top_picks,
            "current_step": "report_generator",
            "messages": [AIMessage(content=f"{len(scored_houses)}개의 적합한 매물 중 TOP {len(top_picks)}개를 추천합니다.")]
        }
    
    def _generate_report(self, state: RecommenderState) -> dict:
        """최종 추천 리포트 생성"""
        profile = state.get("user_profile", {})
        benefits = state.get("benefits", [])
        recommendations = state.get("recommendations", [])
        
        # Language-based Report Generation
        if self.language == "EN":
            report = f"""
## 🏠 Housing Recommendation Report

### 👤 User Profile
- Status: {profile.get('status')}
- Location: {profile.get('location_preference')}
- Asset: {profile.get('assets')}0k KRW
- Max Rent: {profile.get('max_rent')}0k KRW

### 💰 Eligible Benefits ({len(benefits)})
"""
            for b in benefits:
                report += f"- **{b['name']}**: {b['amount']}\n"
            
            report += f"\n### 🏡 Recommended Listings ({len(recommendations)})\n"
            for i, r in enumerate(recommendations, 1):
                loan_info = f"\n   - 🏦 Best Loan: {r['best_loan']}" if r.get('best_loan') else ""
                real_cost = f" (Real cost: {r['real_monthly_cost']}0k)" if r.get('real_monthly_cost') else ""
                report += f"""
**{i}. {r['name']}** ({r['type']})
   - 💰 Deposit {r['deposit']}0k / Rent {r['monthly']}0k{real_cost}
   - 📍 {r['location']} (Commute {r['commute_time']}min)
   - 🛡️ Risk: {r['risk_level']}{loan_info}
"""

        else:
            # Korean Report
            report = f"""
## 🏠 맞춤형 주거 추천 리포트

### 👤 사용자 프로필
- 신분: {profile.get('status')}
- 희망 지역: {profile.get('location_preference')}
- 가용 자산: {profile.get('assets')}만원
- 희망 월세: {profile.get('max_rent')}만원 이하

### 💰 받을 수 있는 혜택 ({len(benefits)}건)
"""
            for b in benefits:
                report += f"- **{b['name']}**: {b['amount']}\n"
            
            # Triple-Match: 혜택 금액 합산
            total_subsidy = 0
            subsidy_names = []
            for b in benefits:
                if not b.get("is_base"):
                    amt_str = b.get("amount", "0")
                    # 숫자만 추출 시도
                    try:
                        amt_num = int(''.join(c for c in amt_str.replace(",", "") if c.isdigit()))
                        if "원" in amt_str and "만" not in amt_str:
                            amt_num = amt_num // 10000  # 원→만원
                        total_subsidy += amt_num
                        subsidy_names.append(b['name'].replace('[추천]', '').replace('[기본]', '').strip())
                    except (ValueError, ZeroDivisionError):
                        pass

            report += f"\n### 🏡 추천 매물 ({len(recommendations)}건)\n"
            for i, r in enumerate(recommendations, 1):
                loan_info = f"\n   - 🏦 추천 대출: {r['best_loan']}" if r.get('best_loan') else ""
                real_cost_val = r.get('real_monthly_cost', r['monthly'])
                real_cost = f" (실질 월부담 {real_cost_val}만)" if r.get('real_monthly_cost') else ""
                report += f"""
**{i}. {r['name']}** ({r['type']})
   - 💰 보증금 {r['deposit']}만 / 월세 {r['monthly']}만{real_cost}
   - 📍 {r['location']} (통근 {r['commute_time']}분)
   - 🛡️ 위험도: {r['risk_level']}{loan_info}
"""

            # Triple-Match 요약
            if recommendations and benefits:
                top = recommendations[0]
                report += f"\n### 🎯 Triple-Match 요약 (1순위 기준)\n"
                report += f"- 매물: **{top['name']}** (월세 {top['monthly']}만)\n"
                report += f"- 대출: **{top.get('best_loan', '분석 중')}** → 실질 월 {top.get('real_monthly_cost', top['monthly'])}만\n"
                if subsidy_names:
                    report += f"- 지원금: {', '.join(subsidy_names[:3])}\n"
                report += f"- **→ 예상 최종 월 부담: {top.get('real_monthly_cost', top['monthly'])}만원**\n"
        
        return {
            "current_step": "done",
            "messages": [AIMessage(content=report)]
        }
    
    def run(self, user_message: str, language: str = "KO", user_profile: dict = None) -> str:
        """에이전트 실행
        
        Args:
            user_message: 사용자 요청 메시지
            language: 언어 설정 ("KO" 또는 "EN")
            user_profile: 사용자 프로필 딕셔너리 (선택)
                - age: 나이
                - status: 신분 (대학생, 직장인 등)
                - assets: 자산 (만원)
                - location_preference: 희망 지역
                - max_commute: 최대 통근 시간 (분)
                - max_rent: 희망 월세 (만원)
        """
        self.set_language(language)
        
        # 외부에서 프로필 전달받은 경우 저장
        if user_profile:
            self.set_user_profile(user_profile)
        
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_profile": {},
            "benefits": [],
            "recommendations": [],
            "current_step": "start"
        }
        
        result = self.graph.invoke(initial_state)
        
        # 마지막 메시지 반환 (기존 호환성 위해 text 포함)
        response = {
            "text": "추천을 생성하지 못했습니다.",
            "benefits": result.get("benefits", []),
            "recommendations": result.get("recommendations", [])
        }
        
        if result.get("messages"):
            response["text"] = result["messages"][-1].content
            
        return response


# Test
if __name__ == "__main__":
    agent = RecommenderAgent()
    result = agent.run("신촌 근처에서 월세 50만원 이하로 집을 구하고 싶어요")
    print(result)
