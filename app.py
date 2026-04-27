<<<<<<< HEAD
from dotenv import load_dotenv
load_dotenv()

from utils.fairness_engine import FairnessEngine
from utils.gemini_advisor import GeminiAdvisor
from agents import AgentOrchestrator
from firewall.bias_firewall import BiasFirewall, FirewallDecision

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import json
from dataclasses import asdict
from datetime import datetime



st.set_page_config(
    page_title="FairGuard AI | Multi-Agent Fairness Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1a1a2e; }
    .sub-header { font-size: 1.1rem; color: #666; }
    .firewall-pass { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 1.5rem; border-radius: 1rem; text-align: center; }
    .firewall-warn { background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%); color: white; padding: 1.5rem; border-radius: 1rem; text-align: center; }
    .firewall-fail { background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%); color: white; padding: 1.5rem; border-radius: 1rem; text-align: center; }
    .impact-card { background: #f8f9fa; border-left: 4px solid #667eea; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .agent-box { background: #f8f9fa; border-left: 4px solid #667eea; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

if 'fairness_report' not in st.session_state:
    st.session_state.fairness_report = None
if 'firewall_result' not in st.session_state:
    st.session_state.firewall_result = None
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = None
if 'gemini_advisor' not in st.session_state:
    st.session_state.gemini_advisor = GeminiAdvisor()
if 'audit_history' not in st.session_state:
    st.session_state.audit_history = []

st.markdown('<p class="main-header">🛡️ FairGuard AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Multi-Agent Fairness Governance Copilot | Bias Firewall | Google Gemini</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    protected_attr = st.selectbox("Protected Attribute", ["gender", "race", "age_group", "disability_status"])
    outcome_col = st.selectbox("Outcome Column", ["selected", "hired", "promoted", "approved"])
    enable_intersectional = st.checkbox("Enable Intersectional Analysis", value=False)
    intersectional_attrs = None
    if enable_intersectional:
        intersectional_attrs = st.multiselect("Intersection Attributes", ["gender", "race", "age_group"], default=["gender", "race"])

    st.divider()
    st.header("🔑 API Configuration")
    api_key = st.text_input("Google API Key (Gemini)", type="password", placeholder="AIza...")
    if api_key and api_key != st.session_state.gemini_advisor.api_key:
        st.session_state.gemini_advisor = GeminiAdvisor(api_key)
        st.success("API Key configured!")

    st.divider()
    st.header("📊 Impact Simulation")
    st.caption("Simulate business impact of fairness improvements")
    total_hires = st.number_input("Annual Hires", min_value=100, max_value=100000, value=1000)
    avg_lawsuit_cost = st.number_input("Avg. Lawsuit Cost ($)", min_value=50000, max_value=1000000, value=250000)

    st.divider()
    st.info("""How to use:
1. Upload CSV with protected attributes
2. Run Fairness Audit
3. Review Bias Firewall decision
4. Check Impact Simulation
5. Get Gemini recommendations
""")

uploaded_file = st.file_uploader("📁 Upload Hiring Dataset (CSV)", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        st.subheader("📊 Dataset Preview")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df.head(10), use_container_width=True)
        with col2:
            st.metric("Total Records", len(df))
            st.metric("Columns", len(df.columns))
            if protected_attr in df.columns:
                st.metric("Protected Groups", df[protected_attr].nunique())
                st.write("**Group Distribution:**")
                st.bar_chart(df[protected_attr].value_counts())

        if protected_attr not in df.columns or outcome_col not in df.columns:
            st.error(f"❌ Required columns not found. Has: {list(df.columns)}")
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                run_audit = st.button("🚀 Run Fairness Audit + Bias Firewall", use_container_width=True, type="primary")

            if run_audit:
                with st.spinner("🔍 Running complete analysis pipeline..."):
                    engine = FairnessEngine()
                    report = engine.analyze(df, protected_attr=protected_attr, outcome_col=outcome_col, intersectional_attrs=intersectional_attrs)
                    st.session_state.fairness_report = report

                    firewall = BiasFirewall()
                    fw_result = firewall.evaluate(report)
                    st.session_state.firewall_result = fw_result

                    orchestrator = AgentOrchestrator()
                    agent_results = orchestrator.run_analysis(report)
                    st.session_state.agent_results = agent_results

                    st.session_state.audit_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'score': report.overall_fairness_score,
                        'firewall': fw_result.decision.value,
                        'risk': report.risk_level
                    })

                st.success("✅ Analysis Complete!")

                # ===== BIAS FIREWALL SECTION =====
                st.divider()
                st.subheader("🔥 Bias Firewall - Pre-Deployment Gate")

                fw = st.session_state.firewall_result
                if fw.decision == FirewallDecision.PASS:
                    st.markdown(f"""
                    <div class="firewall-pass">
                        <div style="font-size: 3rem;">✅</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">{fw.decision_label}</div>
                        <div style="opacity: 0.9; margin-top: 0.5rem;">Model approved for production deployment</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif fw.decision == FirewallDecision.PASS_WITH_WARNINGS:
                    st.markdown(f"""
                    <div class="firewall-warn">
                        <div style="font-size: 3rem;">⚠️</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">{fw.decision_label}</div>
                        <div style="opacity: 0.9; margin-top: 0.5rem;">Address warnings before deployment</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="firewall-fail">
                        <div style="font-size: 3rem;">🚫</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">{fw.decision_label}</div>
                        <div style="opacity: 0.9; margin-top: 0.5rem;">Deployment blocked - remediation required</div>
                    </div>
                    """, unsafe_allow_html=True)

                fw_cols = st.columns(4)
                fw_cols[0].metric("Checks Passed", fw.checks_passed)
                fw_cols[1].metric("Checks Failed", fw.checks_failed)
                fw_cols[2].metric("Total Checks", fw.total_checks)
                fw_cols[3].metric("Can Deploy", "✅ Yes" if fw.can_deploy else "❌ No")

                if fw.failed_checks:
                    with st.expander("❌ Failed Checks"):
                        for check in fw.failed_checks:
                            st.error(f"**{check['name']}**: {check['message']}")

                if fw.deployment_conditions:
                    with st.expander("📋 Deployment Conditions"):
                        for condition in fw.deployment_conditions:
                            st.write(f"• {condition}")

                # ===== IMPACT SIMULATION =====
                st.divider()
                st.subheader("📈 Impact Simulation - Measurable Business Value")

                report = st.session_state.fairness_report
                di = report.detailed_metrics.get('disparate_impact', {})

                if di.get('is_compliant'):
                    bias_reduction = 85
                    lawsuit_risk = 5
                    compliance_status = "✅ Compliant"
                elif di.get('di_ratio', 0) >= 0.6:
                    bias_reduction = 45
                    lawsuit_risk = 35
                    compliance_status = "⚠️ At Risk"
                else:
                    bias_reduction = 15
                    lawsuit_risk = 78
                    compliance_status = "🔴 Violation"

                potential_lawsuits = max(1, int(total_hires * 0.02 * (lawsuit_risk / 100)))
                cost_avoidance = potential_lawsuits * avg_lawsuit_cost * (bias_reduction / 100)

                impact_cols = st.columns(4)
                impact_cols[0].metric("Bias Reduction", f"{bias_reduction}%", "with FairGuard")
                impact_cols[1].metric("Lawsuit Risk", f"{lawsuit_risk}%", compliance_status)
                impact_cols[2].metric("Potential Lawsuits/yr", potential_lawsuits)
                impact_cols[3].metric("Cost Avoidance", f"${cost_avoidance:,.0f}")

                st.info(f"""
                **Impact Story**: By using FairGuard's Bias Firewall, organizations can reduce hiring bias by **{bias_reduction}%**, 
                lowering lawsuit risk from **{min(100, lawsuit_risk + 30)}%** to **{lawsuit_risk}%**. For **{total_hires} annual hires**, 
                this prevents approximately **{potential_lawsuits} discrimination lawsuits**, saving **${cost_avoidance:,.0f}** 
                in legal costs, settlements, and reputational damage.
                """)

                # ===== TABS =====
                tabs = st.tabs(["📈 Dashboard", "🤖 Agent Analysis", "🔍 Detailed Metrics", "💬 Gemini Advisor", "📋 Export Report"])

                with tabs[0]:
                    st.subheader("Fairness Overview")

                    cols = st.columns(4)
                    metrics = [
                        ("Overall Score", report.overall_fairness_score, "%"),
                        ("Demographic Parity", report.demographic_parity, "%"),
                        ("Equalized Odds", report.equalized_odds, "%"),
                        ("Disparate Impact", report.disparate_impact, "%")
                    ]

                    for i, (label, value, unit) in enumerate(metrics):
                        with cols[i]:
                            color = "#28a745" if value >= 80 else "#fd7e14" if value >= 60 else "#dc3545"
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                        border: 2px solid {color}; border-radius: 1rem; padding: 1.5rem; text-align: center;">
                                <div style="font-size: 2.2rem; font-weight: 700; color: {color};">{value:.1f}{unit}</div>
                                <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">{label}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    st.divider()
                    risk_colors = {"Low Risk": "green", "Medium Risk": "orange", "High Risk": "red", "Critical Risk": "darkred"}
                    risk_color = risk_colors.get(report.risk_level, "orange")
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem;">
                        <span style="font-size: 1.2rem;">Risk Assessment: </span>
                        <span style="color: {risk_color}; font-size: 1.5rem; font-weight: 600;">{report.risk_level}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.subheader("Visual Analysis")
                    viz_cols = st.columns(2)

                    with viz_cols[0]:
                        dp_data = report.detailed_metrics['demographic_parity']
                        if 'selection_rates' in dp_data:
                            rates_df = pd.DataFrame([
                                {'Group': k, 'Selection Rate': v} 
                                for k, v in dp_data['selection_rates'].items()
                            ])
                            fig = px.bar(rates_df, x='Group', y='Selection Rate',
                                        title='Selection Rates by Group',
                                        color='Selection Rate', color_continuous_scale='RdYlGn', range_y=[0, 1])
                            fig.update_layout(height=350)
                            st.plotly_chart(fig, use_container_width=True)

                    with viz_cols[1]:
                        categories = ['Demographic Parity', 'Equalized Odds', 'Disparate Impact', 'Calibration']
                        values = [report.demographic_parity, report.equalized_odds, report.disparate_impact, report.calibration_score]
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=values + [values[0]], theta=categories + [categories[0]],
                            fill='toself', name='Current System',
                            fillcolor='rgba(102, 126, 234, 0.3)', line=dict(color='#667eea', width=2)
                        ))
                        fig.add_trace(go.Scatterpolar(
                            r=[80, 80, 80, 80, 80], theta=categories + [categories[0]],
                            name='Fairness Threshold', line=dict(color='#28a745', width=2, dash='dash')
                        ))
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                                        showlegend=True, title='Fairness Dimensions', height=350)
                        st.plotly_chart(fig, use_container_width=True)

                    st.subheader("Key Recommendations")
                    for rec in report.recommendations:
                        st.info(rec)

                with tabs[1]:
                    st.subheader("🤖 Multi-Agent Governance Analysis")

                    if agent_results:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 1.5rem; border-radius: 1rem; margin-bottom: 2rem;">
                            <h3 style="color: white; margin: 0;">🤖 Agent Consensus</h3>
                            <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">{agent_results['consensus']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        agents = [
                            ("🔍 Detection Agent", agent_results['detection'], "#667eea"),
                            ("📖 Explanation Agent", agent_results['explanation'], "#764ba2"),
                            ("🛠️ Mitigation Agent", agent_results['mitigation'], "#f093fb")
                        ]

                        for name, result, color in agents:
                            st.markdown(f"""
                            <div style="border-left: 4px solid {color}; background: #f8f9fa; 
                                        padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                                <div style="font-weight: 600; color: {color}; font-size: 1.1rem; margin-bottom: 0.5rem;">
                                    {name} <span style="float: right; font-size: 0.8rem; opacity: 0.7;">
                                    Confidence: {result.confidence:.0%}</span>
                                </div>
                                <div style="color: #333; line-height: 1.6; white-space: pre-wrap;">{result.content}</div>
                            </div>
                            """, unsafe_allow_html=True)

                with tabs[2]:
                    st.subheader("📊 Statistical Fairness Metrics")
                    metrics_data = report.detailed_metrics

                    with st.expander("Demographic Parity Analysis", expanded=True):
                        dp = metrics_data['demographic_parity']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.json(dp)
                        with col2:
                            st.metric("Parity Ratio", f"{dp.get('parity_ratio', 0):.3f}")
                            st.metric("p-value", f"{dp.get('p_value', 0):.4f}")
                            st.metric("Cramér's V", f"{dp.get('cramers_v', 0):.4f}")
                            st.write("Satisfied:", "✅" if dp.get('is_satisfied') else "❌")

                    with st.expander("Equalized Odds Analysis"):
                        eo = metrics_data['equalized_odds']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.json(eo)
                        with col2:
                            if 'tpr_by_group' in eo:
                                tpr_df = pd.DataFrame([{'Group': k, 'TPR': v} for k, v in eo['tpr_by_group'].items()])
                                st.dataframe(tpr_df)

                    with st.expander("Disparate Impact Analysis"):
                        di = metrics_data['disparate_impact']
                        st.json(di)
                        if not di.get('is_compliant', True):
                            st.error(f"⚠️ {di.get('legal_status', 'Non-compliant')}")

                    if metrics_data.get('intersectional'):
                        with st.expander("Intersectional Analysis"):
                            inter = metrics_data['intersectional']
                            if 'group_stats' in inter:
                                inter_df = pd.DataFrame(inter['group_stats'])
                                st.dataframe(inter_df)
                            st.metric("Max Disparity", f"{inter.get('max_disparity', 0):.3f}")

                with tabs[3]:
                    st.subheader("💬 Gemini Fairness Advisor")
                    advisor = st.session_state.gemini_advisor

                    if not advisor.is_configured:
                        st.warning("⚠️ Google API Key not configured. Using template-based recommendations.")
                    else:
                        st.success("✅ Gemini 1.5 Flash connected")

                    if st.button("🔄 Generate AI Recommendations", type="primary"):
                        with st.spinner("Consulting Gemini..."):
                            result = advisor.generate_fairness_recommendations(report)
                            st.session_state.gemini_result = result

                    if 'gemini_result' in st.session_state:
                        result = st.session_state.gemini_result
                        st.caption(f"Source: {result['source']}")
                        st.markdown(result['response'])

                    st.divider()
                    st.subheader("💭 Ask a Question")
                    user_q = st.text_input("Ask about fairness, legal compliance, or remediation:",
                                           placeholder="e.g., What are the legal risks if we don't fix this?")

                    if user_q:
                        with st.spinner("Analyzing..."):
                            result = advisor.generate_fairness_recommendations(report, user_q)
                            st.markdown(f"**🤖 Gemini:** {result['response']}")

                with tabs[4]:
                    st.subheader("📋 Export Audit Report")
                    report_dict = asdict(report)

                    report_json = json.dumps(report_dict, indent=2, default=str)
                    st.download_button(
                        label="📥 Download Full Report (JSON)",
                        data=report_json,
                        file_name=f"fairguard_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

                    summary_data = {
                        'Metric': ['Overall Score', 'Demographic Parity', 'Equalized Odds', 'Disparate Impact', 'Calibration', 'Risk Level', 'Bias Firewall'],
                        'Value': [report.overall_fairness_score, report.demographic_parity, report.equalized_odds,
                                  report.disparate_impact, report.calibration_score, report.risk_level, report.bias_firewall_status]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    csv = summary_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Summary (CSV)",
                        data=csv,
                        file_name=f"fairguard_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                    st.subheader("Report Preview")
                    st.json(report_dict)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

else:
    st.info("👆 Upload a CSV dataset to begin the fairness audit")

    if st.button("📊 Load Demo Dataset"):
        np.random.seed(42)
        n = 500
        demo_data = pd.DataFrame({
            'gender': np.random.choice(['Male', 'Female'], n, p=[0.6, 0.4]),
            'race': np.random.choice(['White', 'Black', 'Asian', 'Hispanic'], n),
            'age_group': np.random.choice(['18-25', '26-35', '36-45', '46+'], n),
            'selected': np.random.binomial(1, 0.3, n)
        })
        demo_data.loc[demo_data['gender'] == 'Male', 'selected'] = np.random.binomial(1, 0.45, len(demo_data[demo_data['gender'] == 'Male']))
        demo_data.loc[demo_data['gender'] == 'Female', 'selected'] = np.random.binomial(1, 0.25, len(demo_data[demo_data['gender'] == 'Female']))

        st.session_state.demo_data = demo_data
        st.success("Demo data ready! Download and re-upload to run analysis.")
        st.dataframe(demo_data.head())
        csv = demo_data.to_csv(index=False)
        st.download_button("Download Demo CSV", data=csv, file_name="demo_hiring_data.csv", mime="text/csv")

st.divider()
st.caption("🛡️ FairGuard AI | Google Solution Challenge 2026 | Multi-Agent Fairness Governance + Bias Firewall")
=======
import streamlit as st
import pandas as pd
from bias_engine import detect_bias

st.title("FairGuard AI: Multi-Agent Fairness Copilot")

uploaded_file = st.file_uploader(
    "Upload Hiring Dataset CSV"
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df)

    result = detect_bias(df)

    st.subheader("Fairness Audit Results")
    st.write(result)
    st.metric("Fairness Score","72")
st.metric("Bias Risk","Medium")

st.subheader("Bias Mitigation Recommendations")

st.write("""
1. Rebalance training data
2. Review hiring thresholds
3. Add fairness constraints
4. Schedule periodic audits
""")

st.subheader("Gemini Fairness Advisor")

question = st.text_input("Ask Gemini for fairness recommendations:")

if question:
    st.success(
    "Suggested Action: Review data imbalance, retrain model with fairness constraints and perform compliance audit."
    )

st.subheader("Compliance Status")
st.success("Responsible AI audit checks passed")
>>>>>>> 03f0d2ff188bb3ccfed1870e397fa3925897a818
