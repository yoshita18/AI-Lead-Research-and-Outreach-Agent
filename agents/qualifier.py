"""Stage 4: Qualification Gate — score lead 1-10 against ICP."""
import json
import os
from groq import Groq
from models.lead_card import LeadCard, QualificationResult, SellerContext

CLIENT = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM = """You are a B2B sales qualification expert. Score leads strictly and honestly.
A score of 7+ means the lead matches the ICP well enough to pursue. Below 7 is low priority."""

PROMPT_TEMPLATE = """
=== SELLER ICP ===
What they sell: {what_you_sell}
Ideal Customer Profile: {icp}
Target deal size: {deal_size}

=== LEAD CARD ===
Company: {company_name} ({company_url})
Industry: {industry}
Size: {company_size}
Summary: {summary}
Pain Points: {pain_points}
Growth Signals: {growth_signals}
Fit Assessment: {fit_assessment}

Score this lead 1-10 against the ICP. Return JSON only:
{{
  "score": <integer 1-10>,
  "priority": "<High Priority|Medium Priority|Low Priority>",
  "reasoning": "2-3 sentence explanation of the score",
  "icp_match_points": ["what matches the ICP"],
  "icp_gap_points": ["what does not match or is missing"],
  "recommended_action": "specific next step for the seller"
}}

Scoring guide: 8-10 = strong ICP match, pursue now. 5-7 = partial match, nurture.
1-4 = poor fit, flag as low priority with explanation.

Return ONLY valid JSON, no markdown fences.
"""


def qualify_lead(lead: LeadCard, seller: SellerContext) -> QualificationResult:
    prompt = PROMPT_TEMPLATE.format(
        what_you_sell=seller.what_you_sell,
        icp=seller.ideal_customer_profile,
        deal_size=seller.deal_size,
        company_name=lead.company_name,
        company_url=lead.company_url,
        industry=lead.industry,
        company_size=lead.company_size,
        summary=lead.company_summary,
        pain_points=", ".join(lead.inferred_pain_points),
        growth_signals=", ".join(lead.growth_signals),
        fit_assessment=lead.fit_assessment,
    )

    response = CLIENT.chat.completions.create(
        model=MODEL,
        max_tokens=800,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    return QualificationResult(**data)
