"""AI Lead Research & Outreach Agent — Streamlit UI (Stages 1 + 6)."""
import os
import io
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from models.lead_card import SellerContext
from agents.research_agent import run_research
from agents.synthesizer import synthesize_lead_card
from agents.qualifier import qualify_lead
from agents.email_generator import generate_emails

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Lead Research & Outreach Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.score-high   { color: #22c55e; font-size: 2rem; font-weight: 700; }
.score-medium { color: #f59e0b; font-size: 2rem; font-weight: 700; }
.score-low    { color: #ef4444; font-size: 2rem; font-weight: 700; }
.tag { display:inline-block; background:#1e3a5f; color:#93c5fd;
       padding:2px 8px; border-radius:12px; margin:2px; font-size:0.8rem; }
.signal-tag { display:inline-block; background:#14532d; color:#86efac;
              padding:2px 8px; border-radius:12px; margin:2px; font-size:0.8rem; }
.pain-tag { display:inline-block; background:#450a0a; color:#fca5a5;
            padding:2px 8px; border-radius:12px; margin:2px; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["lead_card", "qualification", "emails", "research", "seller"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "batch_results" not in st.session_state:
    st.session_state.batch_results = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# ── Helpers ───────────────────────────────────────────────────────────────────
def score_class(score: int) -> str:
    if score >= 7:
        return "score-high"
    if score >= 5:
        return "score-medium"
    return "score-low"


def tags_html(items: list, css_class: str) -> str:
    return " ".join(f'<span class="{css_class}">{i}</span>' for i in items)


def run_full_pipeline(url: str, seller: SellerContext):
    steps = [
        "Researching company website + web signals...",
        "Synthesizing Lead Card...",
        "Running qualification gate...",
        "Generating personalized emails...",
    ]
    progress = st.progress(0, text=steps[0])

    research = run_research(url)
    progress.progress(25, text=steps[1])

    lead_card = synthesize_lead_card(research, seller)
    progress.progress(50, text=steps[2])

    qualification = qualify_lead(lead_card, seller)
    progress.progress(75, text=steps[3])

    emails = generate_emails(lead_card, qualification, seller)
    progress.progress(100, text="Done!")
    progress.empty()

    return research, lead_card, qualification, emails


def to_csv(results: list) -> bytes:
    rows = []
    for r in results:
        lc = r["lead_card"]
        q = r["qualification"]
        e = r["emails"]
        rows.append({
            "Company": lc.company_name,
            "URL": lc.company_url,
            "Industry": lc.industry,
            "Size": lc.company_size,
            "Score": q.score,
            "Priority": q.priority,
            "Reasoning": q.reasoning,
            "Recommended Action": q.recommended_action,
            "Pain Points": " | ".join(lc.inferred_pain_points),
            "Growth Signals": " | ".join(lc.growth_signals),
            "Decision Makers": " | ".join(lc.likely_decision_maker_titles),
            "Professional Subject": e.professional_subject,
            "Professional Email": e.professional_body,
            "Conversational Subject": e.conversational_subject,
            "Conversational Email": e.conversational_body,
        })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ── Sidebar — Stage 1: Seller Context ─────────────────────────────────────────
with st.sidebar:
    st.title("🎯 Lead Research Agent")
    st.caption("Powered by Groq (Llama 3.3) + DuckDuckGo — 100% free")
    st.divider()

    st.subheader("Your Seller Context")
    your_name = st.text_input("Your Name", placeholder="Jane Smith")
    your_company = st.text_input("Your Company", placeholder="Acme Corp")
    what_you_sell = st.text_area(
        "What You Sell",
        placeholder="AI-powered inventory management software for e-commerce stores",
        height=80,
    )
    icp = st.text_area(
        "Ideal Customer Profile (ICP)",
        placeholder="E-commerce companies with $1M-$20M revenue, 10-100 employees, struggling with stockouts or overselling",
        height=100,
    )
    deal_size = st.text_input("Typical Deal Size", placeholder="$5,000 - $25,000/year")

    st.divider()
    qual_threshold = st.slider("Qualification Threshold", 1, 10, 6,
                               help="Leads below this score are flagged Low Priority")
    st.caption(f"Leads scoring ≥{qual_threshold} proceed to email generation.")


# ── Main panel ────────────────────────────────────────────────────────────────
st.title("AI Lead Research & Outreach Agent")

tab_single, tab_batch, tab_history = st.tabs(["Single Lead", "Batch Processing", "Results History"])

# ── Tab 1: Single Lead ────────────────────────────────────────────────────────
with tab_single:
    col_input, _ = st.columns([2, 1])
    with col_input:
        company_url = st.text_input(
            "Company URL",
            placeholder="https://example.com",
            label_visibility="visible",
        )
        run_btn = st.button("Research Lead", type="primary", use_container_width=True)

    if run_btn:
        if not company_url:
            st.error("Enter a company URL.")
        elif not what_you_sell or not icp:
            st.error("Fill in your seller context in the sidebar first.")
        elif not os.getenv("GROQ_API_KEY"):
            st.error("Set GROQ_API_KEY in your .env file.")
        else:
            seller = SellerContext(
                what_you_sell=what_you_sell,
                ideal_customer_profile=icp,
                deal_size=deal_size,
                your_name=your_name,
                your_company=your_company,
            )
            with st.spinner("Running 4-stage pipeline..."):
                try:
                    research, lead_card, qualification, emails = run_full_pipeline(
                        company_url, seller
                    )
                    st.session_state.lead_card = lead_card
                    st.session_state.qualification = qualification
                    st.session_state.emails = emails
                    st.session_state.research = research
                    st.session_state.seller = seller

                    # Add to history
                    st.session_state.batch_results.append({
                        "lead_card": lead_card,
                        "qualification": qualification,
                        "emails": emails,
                    })
                    st.success(f"Done! Score: {qualification.score}/10 — {qualification.priority}")
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

    # ── Stage 6: Output Dashboard ─────────────────────────────────────────────
    if st.session_state.lead_card:
        lc = st.session_state.lead_card
        q = st.session_state.qualification
        e = st.session_state.emails

        st.divider()

        # Header row
        hcol1, hcol2, hcol3 = st.columns([3, 1, 2])
        with hcol1:
            st.subheader(f"🏢 {lc.company_name}")
            st.caption(f"{lc.company_url}  ·  {lc.industry}  ·  {lc.company_size}")
        with hcol2:
            st.markdown(f'<div class="{score_class(q.score)}">{q.score}/10</div>', unsafe_allow_html=True)
            priority_color = {"High Priority": "🟢", "Medium Priority": "🟡", "Low Priority": "🔴"}
            st.markdown(f"{priority_color.get(q.priority, '')} **{q.priority}**")
        with hcol3:
            st.info(f"**Next Step:** {q.recommended_action}")

        # Lead Card + Qualification
        lcol, qcol = st.columns(2)
        with lcol:
            with st.expander("📋 Lead Card", expanded=True):
                st.write("**Summary**")
                st.write(lc.company_summary)

                st.write("**Pain Points**")
                st.markdown(tags_html(lc.inferred_pain_points, "pain-tag"), unsafe_allow_html=True)

                st.write("**Growth Signals**")
                st.markdown(tags_html(lc.growth_signals, "signal-tag"), unsafe_allow_html=True)

                if lc.recent_news:
                    st.write("**Recent News**")
                    for n in lc.recent_news:
                        st.markdown(f"• {n}")

                st.write("**Decision Maker Titles**")
                st.markdown(tags_html(lc.likely_decision_maker_titles, "tag"), unsafe_allow_html=True)

                if lc.tech_stack_signals:
                    st.write("**Tech Stack Signals**")
                    st.markdown(tags_html(lc.tech_stack_signals, "tag"), unsafe_allow_html=True)

                st.write("**ICP Fit Assessment**")
                st.write(lc.fit_assessment)

        with qcol:
            with st.expander("🎯 Qualification Details", expanded=True):
                st.write("**Reasoning**")
                st.write(q.reasoning)

                if q.icp_match_points:
                    st.write("**✅ ICP Matches**")
                    for p in q.icp_match_points:
                        st.markdown(f"• {p}")

                if q.icp_gap_points:
                    st.write("**⚠️ ICP Gaps**")
                    for g in q.icp_gap_points:
                        st.markdown(f"• {g}")

        # Email variants — A/B side by side
        if q.score >= qual_threshold:
            st.divider()
            st.subheader("✉️ Personalized Outreach Emails")

            ecol1, ecol2 = st.columns(2)

            with ecol1:
                st.markdown("**Variant A — Professional**")
                pro_subject = st.text_input("Subject (Professional)", value=e.professional_subject, key="pro_sub")
                pro_body = st.text_area("Body (Professional)", value=e.professional_body, height=220, key="pro_body")
                if st.button("Copy Professional Email", key="copy_pro"):
                    full = f"Subject: {pro_subject}\n\n{pro_body}"
                    st.code(full, language=None)

            with ecol2:
                st.markdown("**Variant B — Conversational**")
                conv_subject = st.text_input("Subject (Conversational)", value=e.conversational_subject, key="conv_sub")
                conv_body = st.text_area("Body (Conversational)", value=e.conversational_body, height=220, key="conv_body")
                if st.button("Copy Conversational Email", key="copy_conv"):
                    full = f"Subject: {conv_subject}\n\n{conv_body}"
                    st.code(full, language=None)
        else:
            st.warning(
                f"⚠️ Score {q.score}/10 is below your threshold of {qual_threshold}. "
                "Email generation skipped — this lead is flagged **Low Priority**."
            )

        # Export single lead
        st.divider()
        csv_bytes = to_csv([{
            "lead_card": lc,
            "qualification": q,
            "emails": e,
        }])
        st.download_button(
            "⬇️ Export Lead to CSV",
            data=csv_bytes,
            file_name=f"{lc.company_name.replace(' ', '_')}_lead.csv",
            mime="text/csv",
        )


# ── Tab 2: Batch Processing ───────────────────────────────────────────────────
with tab_batch:
    st.subheader("Batch URL Processing")
    st.caption("Enter one URL per line. Each lead runs through the full pipeline.")
    batch_urls_raw = st.text_area("Company URLs (one per line)", height=150,
                                  placeholder="https://company1.com\nhttps://company2.com")
    batch_btn = st.button("Process Batch", type="primary")

    if batch_btn:
        if not what_you_sell or not icp:
            st.error("Fill in your seller context in the sidebar first.")
        elif not batch_urls_raw.strip():
            st.error("Enter at least one URL.")
        elif not os.getenv("GROQ_API_KEY"):
            st.error("Set GROQ_API_KEY in your .env file.")
        else:
            urls = [u.strip() for u in batch_urls_raw.strip().splitlines() if u.strip()]
            seller = SellerContext(
                what_you_sell=what_you_sell,
                ideal_customer_profile=icp,
                deal_size=deal_size,
                your_name=your_name,
                your_company=your_company,
            )
            batch_new = []
            prog = st.progress(0)
            for i, url in enumerate(urls):
                st.write(f"Processing {i+1}/{len(urls)}: {url}")
                try:
                    _, lc, q, e = run_full_pipeline(url, seller)
                    batch_new.append({"lead_card": lc, "qualification": q, "emails": e})
                except Exception as ex:
                    st.warning(f"Failed for {url}: {ex}")
                prog.progress((i + 1) / len(urls))

            st.session_state.batch_results.extend(batch_new)
            st.success(f"Processed {len(batch_new)}/{len(urls)} leads.")

            if batch_new:
                csv = to_csv(batch_new)
                st.download_button("⬇️ Export Batch to CSV", data=csv,
                                   file_name="batch_leads.csv", mime="text/csv")


# ── Tab 3: Results History ────────────────────────────────────────────────────
with tab_history:
    st.subheader("All Researched Leads")
    results = st.session_state.batch_results
    if not results:
        st.info("No leads researched yet. Run the pipeline from the Single Lead or Batch tabs.")
    else:
        rows = []
        for r in results:
            lc, q = r["lead_card"], r["qualification"]
            rows.append({
                "Company": lc.company_name,
                "Industry": lc.industry,
                "Size": lc.company_size,
                "Score": q.score,
                "Priority": q.priority,
                "Action": q.recommended_action,
                "URL": lc.company_url,
            })
        df = pd.DataFrame(rows).sort_values("Score", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("⬇️ Export All to CSV"):
            csv = to_csv(results)
            st.download_button("Download CSV", data=csv, file_name="all_leads.csv", mime="text/csv")

        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.batch_results = []
            st.rerun()
