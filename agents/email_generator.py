"""Stage 5: Personalized Email Generator — two tone variants for A/B testing."""
import json
import os
from groq import Groq
from models.lead_card import LeadCard, QualificationResult, EmailVariants, SellerContext

CLIENT = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM = """You are an expert B2B cold email copywriter. Write concise, specific cold emails
that reference real signals from the lead — never generic filler. Emails should be under 150 words
each. No buzzwords. Always end with a single low-commitment call to action."""

PROMPT_TEMPLATE = """
=== SELLER INFO ===
Sender name: {your_name}
Sender company: {your_company}
What they sell: {what_you_sell}
Deal size: {deal_size}

=== LEAD INTELLIGENCE ===
Company: {company_name}
Industry: {industry}
Pain Points: {pain_points}
Growth Signals: {growth_signals}
Recent News: {recent_news}
Likely Decision Makers: {decision_makers}
Qualification Score: {score}/10

Write TWO cold email variants. Return JSON only:
{{
  "professional_subject": "subject line for professional tone",
  "professional_body": "full email body, professional tone, <150 words",
  "conversational_subject": "subject line for conversational tone",
  "conversational_body": "full email body, conversational/friendly tone, <150 words"
}}

Requirements:
- Reference at least one specific pain point or growth signal
- Mention {company_name} by name in the opening
- Professional variant: formal, exec-level
- Conversational variant: warm, peer-to-peer, use first names
- Both end with one soft CTA (e.g. "Worth a 15-min chat?")

Return ONLY valid JSON, no markdown fences.
"""


def generate_emails(
    lead: LeadCard,
    qualification: QualificationResult,
    seller: SellerContext,
) -> EmailVariants:
    prompt = PROMPT_TEMPLATE.format(
        your_name=seller.your_name or "Your Name",
        your_company=seller.your_company or "Your Company",
        what_you_sell=seller.what_you_sell,
        deal_size=seller.deal_size,
        company_name=lead.company_name,
        industry=lead.industry,
        pain_points=", ".join(lead.inferred_pain_points[:3]),
        growth_signals=", ".join(lead.growth_signals[:3]),
        recent_news=", ".join(lead.recent_news[:2]) if lead.recent_news else "None found",
        decision_makers=", ".join(lead.likely_decision_maker_titles[:3]),
        score=qualification.score,
    )

    response = CLIENT.chat.completions.create(
        model=MODEL,
        max_tokens=1200,
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
    return EmailVariants(**data)
