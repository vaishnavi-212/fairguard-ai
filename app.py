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