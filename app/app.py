"""Streamlit Review Dashboard and Grounded Q&A for Routewatch."""

from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Routewatch - Freight Cost Intelligence",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Indian Road Freight Aesthetic per UI_SPEC.md)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1B1F23;
        background-color: #FAF8F3;
    }
    
    .stApp {
        background-color: #FAF8F3;
    }
    
    /* Header & Branding */
    .brand-header {
        background-color: #0B5D3B;
        color: #FAF8F3;
        padding: 18px 24px;
        border-radius: 4px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-subtitle {
        font-size: 14px;
        color: #D1E7DD;
        margin: 0;
    }
    
    /* Summary Metric Strip */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 4px;
        padding: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    /* Evidence Card (Waybill Slip Style) */
    .evidence-card {
        background-color: #FFFFFF;
        border: 1px dashed #6B7280;
        border-radius: 4px;
        padding: 16px 20px;
        margin-top: 12px;
        position: relative;
    }
    .evidence-tag {
        display: inline-block;
        background-color: #0F7A8A;
        color: #FFFFFF;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 2px;
        margin-bottom: 8px;
    }
    .evidence-text {
        font-size: 14px;
        line-height: 1.5;
        color: #1B1F23;
        font-style: italic;
    }
    
    /* Badges */
    .badge-review {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #FCD34D;
        display: inline-block;
    }
    .badge-justified {
        background-color: #E6FFFA;
        color: #047481;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #81E6D9;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache pipeline datasets."""
    out_path = Path("outputs/output.csv")
    metrics_path = Path("outputs/weekly_metrics.csv")
    notes_path = Path("data/notes_structured.json")

    if not out_path.exists() or not metrics_path.exists():
        st.error("Missing output files. Run `python run.py` first.")
        st.stop()

    df_out = pd.read_csv(out_path)
    df_metrics = pd.read_csv(metrics_path)

    with open(notes_path, "r", encoding="utf-8") as f:
        notes_data = json.load(f)
    notes_dict = {n["note_id"]: n for n in notes_data}

    return df_out, df_metrics, notes_dict


df_out, df_metrics, notes_dict = load_data()

# Top Navigation Bar
st.markdown("""
<div class="brand-header">
    <div>
        <div class="brand-title">Routewatch Freight Intelligence</div>
        <div class="brand-subtitle">Smart Shipping-Cost Assistant & Anomaly Verifier</div>
    </div>
    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; opacity: 0.9;">
        Dataset: 104 Weeks (2024–2025) | 7 Commercial Routes
    </div>
</div>
""", unsafe_allow_html=True)

tab_review, tab_ask = st.tabs(["📋 Anomaly Review Dashboard", "💬 Ask Routewatch (Grounded Q&A)"])

# ==============================================================================
# TAB 1: REVIEW DASHBOARD
# ==============================================================================
with tab_review:
    # Summary Metrics
    total_anomalies = len(df_out)
    unexplained_count = (df_out["flagged"] == "Yes").sum()
    justified_count = (df_out["flagged"] == "No (justified)").sum()
    routes_covered = df_out["route"].nunique()

    st.markdown(f"### **{total_anomalies} route-weeks looked unusually expensive. {unexplained_count} need a human look.**")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #F2A900;">
            <div class="metric-val" style="color: #B45309;">{unexplained_count}</div>
            <div class="metric-label">Needs Human Review</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #0F7A8A;">
            <div class="metric-val" style="color: #0F7A8A;">{justified_count}</div>
            <div class="metric-label">Explained by Note</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #0B5D3B;">
            <div class="metric-val" style="color: #0B5D3B;">{total_anomalies}</div>
            <div class="metric-label">Total Flagged Spikes</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #6B7280;">
            <div class="metric-val" style="color: #374151;">{routes_covered} / 7</div>
            <div class="metric-label">Routes Impacted</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        selected_route = st.selectbox(
            "Filter by Route",
            options=["All Routes"] + sorted(df_out["route"].unique().tolist()),
            index=0
        )
    with col_f2:
        selected_status = st.selectbox(
            "Filter by Status",
            options=["All Statuses", "Needs Review (Unexplained)", "Explained (Justified)"],
            index=0
        )

    # Apply filters
    filtered_df = df_out.copy()
    if selected_route != "All Routes":
        filtered_df = filtered_df[filtered_df["route"] == selected_route]
    if selected_status == "Needs Review (Unexplained)":
        filtered_df = filtered_df[filtered_df["flagged"] == "Yes"]
    elif selected_status == "Explained (Justified)":
        filtered_df = filtered_df[filtered_df["flagged"] == "No (justified)"]

    # Table & Details
    col_tbl, col_detail = st.columns([6, 5])

    with col_tbl:
        st.markdown("#### Flagged Route-Weeks")
        if filtered_df.empty:
            st.info("No unusual cost rises found for these filters.")
            selected_idx = None
        else:
            display_rows = []
            for idx, r in filtered_df.iterrows():
                status_badge = "⚠️ Needs Review" if r["flagged"] == "Yes" else "✅ Justified"
                display_rows.append({
                    "Index": idx,
                    "Route": r["route"],
                    "Week": r["week_of"],
                    "Rate (₹/t-km)": f"₹{r['cost_per_tonne_km']:.2f}",
                    "vs Own History": r["vs_own_history"].split(" vs ")[0],
                    "vs Similar Tier": r["vs_similar_routes"].split(" vs ")[0],
                    "Status": status_badge,
                })
            table_df = pd.DataFrame(display_rows)
            st.dataframe(
                table_df.drop(columns=["Index"]),
                use_container_width=True,
                height=350,
                hide_index=True
            )

            row_options = [f"{r['Route']} ({r['Week']}) - {r['Status']}" for r in display_rows]
            chosen_row_label = st.selectbox("Inspect Corridor Details", options=row_options, index=0)
            selected_idx = display_rows[row_options.index(chosen_row_label)]["Index"]

    with col_detail:
        st.markdown("#### Anomaly Audit & Historical Trajectory")
        if selected_idx is not None:
            sel_row = df_out.loc[selected_idx]
            curr_route = sel_row["route"]
            curr_week = sel_row["week_of"]

            # Plot trajectory for the corridor
            route_history = df_metrics[df_metrics["route"] == curr_route].sort_values("week_of").copy()

            fig = go.Figure()
            # Trailing 8-week baseline rolling average
            route_history["rolling_8"] = route_history["cost_per_tonne_km"].shift(1).rolling(8, min_periods=1).mean()

            fig.add_trace(go.Scatter(
                x=route_history["week_of"],
                y=route_history["rolling_8"],
                name="8-Week Prior Baseline",
                line=dict(color="#9CA3AF", dash="dot", width=1.5),
            ))
            fig.add_trace(go.Scatter(
                x=route_history["week_of"],
                y=route_history["cost_per_tonne_km"],
                name="Actual Cost/t-km",
                line=dict(color="#0B5D3B", width=2.5),
            ))

            # Mark flagged week
            flagged_val = sel_row["cost_per_tonne_km"]
            fig.add_trace(go.Scatter(
                x=[curr_week],
                y=[flagged_val],
                mode="markers+text",
                marker=dict(color="#F2A900" if sel_row["flagged"] == "Yes" else "#0F7A8A", size=12),
                text=[f"₹{flagged_val:.2f}"],
                textposition="top center",
                name="Flagged Week",
            ))

            fig.update_layout(
                margin=dict(l=10, r=10, t=25, b=20),
                height=240,
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FAF8F3",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
                yaxis=dict(showgrid=True, gridcolor="#E5E7EB", title="₹ / Tonne-Km"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Evidence Card
            st.markdown("**Evidence Grounding:**")
            nid = str(sel_row["matched_note_id"]).strip() if not pd.isna(sel_row["matched_note_id"]) else ""

            if nid and nid in notes_dict:
                note_info = notes_dict[nid]
                st.markdown(f"""
                <div class="evidence-card">
                    <span class="evidence-tag">VERIFIED NOTE: {note_info['note_id']}</span>
                    <span style="font-size: 12px; color: #6B7280; margin-left: 8px;">Date: {note_info['date']} | Applies to: {note_info['applies_to']}</span>
                    <div class="evidence-text">"{note_info['original_text']}"</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="evidence-card" style="border-color: #F59E0B;">
                    <span class="evidence-tag" style="background-color: #B45309;">UNEXPLAINED ANOMALY</span>
                    <div class="evidence-text">No matching justification note found for this corridor and date window. Recommended for manual commercial review.</div>
                </div>
                """, unsafe_allow_html=True)

            st.info(f"**Audit Verdict Reason:** {sel_row['reason']}")

# ==============================================================================
# TAB 2: GROUNDED Q&A ASSISTANT
# ==============================================================================
with tab_ask:
    st.markdown("### Ask Routewatch")
    st.caption("Ask questions about any flagged shipping route, surge period, or justification note. Answers are strictly grounded in verified pipeline data.")

    # Chip shortcuts
    if "user_query" not in st.session_state:
        st.session_state["user_query"] = ""

    col_chip1, col_chip2, col_chip3 = st.columns(3)
    if col_chip1.button("Why did Chennai-Bangalore get pricier in March 2025?"):
        st.session_state["user_query"] = "Why did Chennai-Bangalore get pricier in March 2025?"
        st.rerun()
    if col_chip2.button("Which flags have no explanation?"):
        st.session_state["user_query"] = "Which flags have no explanation?"
        st.rerun()
    if col_chip3.button("Why was Ahmedabad-Mumbai flagged in January 2025?"):
        st.session_state["user_query"] = "Why was Ahmedabad-Mumbai flagged in January 2025?"
        st.rerun()

    user_query = st.text_input(
        "Enter your question:",
        value=st.session_state["user_query"],
        placeholder="e.g., Why did Delhi-Jaipur spike in November 2024?"
    )

    if st.button("Ask Assistant", type="primary") and user_query.strip():
        with st.spinner("Analyzing verified audit notes and trajectory baselines..."):
            from src.costwatch.qa import GroundedQA
            qa_engine = GroundedQA()
            answer, cited_rows, cited_notes = qa_engine.answer_question(user_query)

        st.markdown("#### Answer")
        st.markdown(f">{answer}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"**Based on Verified Rows:** {', '.join(cited_rows) if cited_rows else 'None'}")
        if cited_notes:
            st.caption(f"**Referenced Notes:** {', '.join(cited_notes)}")
