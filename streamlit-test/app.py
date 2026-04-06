"""
Katonic App Deployment — Streamlit Test App
Framework: Streamlit | Port: 8501
Run: streamlit run app.py --server.port=8501
"""
import streamlit as st
import datetime
import os

st.set_page_config(page_title="Katonic Streamlit Test", page_icon="🚀", layout="wide")

st.title("🚀 Katonic Streamlit Test App")
st.success("✅ Streamlit is running successfully on Katonic!")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Environment Info")
    st.json({
        "framework": "Streamlit",
        "port": 8501,
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "python_version": os.popen("python --version").read().strip(),
        "timestamp": datetime.datetime.now().isoformat(),
    })

with col2:
    st.subheader("🧪 Interactive Test")
    name = st.text_input("Enter your name", value="Katonic User")
    if st.button("Say Hello"):
        st.balloons()
        st.write(f"Hello, **{name}**! Your Streamlit app is working! 🎉")

st.subheader("📊 Sample Chart")
import random
chart_data = {f"Day {i}": random.randint(10, 100) for i in range(1, 8)}
st.bar_chart(chart_data)

st.divider()
st.caption(f"Katonic App Deployment Test | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
