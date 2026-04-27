import streamlit as st
import pandas as pd
from bias_engine import detect_bias

st.title("FairGuard Copilot")

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