"""Stage 3: Lead Intelligence Synthesizer — raw data → structured Lead Card."""
import json
import os
from groq import Groq
from models.lead_card import LeadCard, SellerContext

CLIENT = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM = """You are a B2B sales intelligence analyst. Given raw web scrape and search data
about a company, produce a structured Lead Card in JSON. Be specific and factual — only
infer what the data supports. Never fabricate signals."""

PROMPT_TEMPLATE = """
Company URL: {url}
Company Name: {name}

=== WEBSITE CONTENT ===
{scraped}

=== WEB SEARCH RESULTS ===
{searched}

=== SELLER CONTEXT ===
What they sell: {what_you_sell}
ICP: {icp}
Deal size: {deal_size}

Produce a JSON object matching this schema exactly:
{{
  "company_name": "string",
  "company_url": "string",
  "company_summary": "2-3 sentence summary",
  "industry": "string",
  "company_size": "e.g. 10-50 employees",
  "inferred_pain_points": ["pain1", "pain2", "pain3"],
  "growth_signals": ["signal1", "signal2"],
  "likely_decision_maker_titles": ["title1", "title2"],
  "recent_news": ["news item 1", "news item 2"],
  "tech_stack_signals": ["tech1", "tech2"],
  "fit_assessment": "1-2 sentence assessment of how well this company fits the seller's ICP",
  "raw_data_summary": "brief note on data quality/completeness"
}}

Return ONLY valid JSON, no markdown fences.
"""


def synthesize_lead_card(research: dict, seller: SellerContext) -> LeadCard:
    prompt = PROMPT_TEMPLATE.format(
        url=research["company_url"],
        name=research["company_name"],
        scraped=research["scraped"].get("content", "No website data")[:5000],
        searched=research["searched"].get("summary", "No search data")[:4000],
        what_you_sell=seller.what_you_sell,
        icp=seller.ideal_customer_profile,
        deal_size=seller.deal_size,
    )

    response = CLIENT.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown fences if model adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    return LeadCard(**data)
