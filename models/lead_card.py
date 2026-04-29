from pydantic import BaseModel, Field
from typing import Optional, List


class SellerContext(BaseModel):
    what_you_sell: str
    ideal_customer_profile: str
    deal_size: str
    your_name: str = ""
    your_company: str = ""


class LeadCard(BaseModel):
    company_name: str
    company_url: str
    company_summary: str
    industry: str
    company_size: str
    inferred_pain_points: List[str]
    growth_signals: List[str]
    likely_decision_maker_titles: List[str]
    recent_news: List[str]
    tech_stack_signals: List[str]
    fit_assessment: str
    raw_data_summary: str


class QualificationResult(BaseModel):
    score: int = Field(ge=1, le=10)
    priority: str  # "High Priority", "Medium Priority", "Low Priority"
    reasoning: str
    icp_match_points: List[str]
    icp_gap_points: List[str]
    recommended_action: str


class EmailVariants(BaseModel):
    professional_subject: str
    professional_body: str
    conversational_subject: str
    conversational_body: str
