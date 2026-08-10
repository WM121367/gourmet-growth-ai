import streamlit as st
import requests

st.set_page_config(page_title="Next Flow Marketing Pipeline", layout="wide")
st.title("🚀 Next Flow Marketing - Multi-Agent System")

with st.sidebar:
    api_key = st.text_input("OpenAI API Key", type="password")
    agent1_url = st.text_input("Agent 1 Endpoint", value="http://127.0.0.1:8001/submit")

col1, col2 = st.columns(2)
with col1:
    restaurant_name = st.text_input("Restaurant Name", value="Trattoria Verona")
    genre = st.selectbox("Cuisine / Genre", ["Casual Italian", "Japanese Izakaya", "Cafe & Bakery", "Yakiniku / BBQ"])
    location = st.text_input("Location / Area", value="Downtown Core")
with col2:
    target_customer = st.text_input("Target Audience", value="Working professionals aged 25–40")
    unique_selling_point = st.text_area("USP", value="Organic natural wine and house-made fresh pasta.")
    current_issue = st.text_input("Primary Challenge", value="Low customer traffic on weekday evenings")

if st.button("🚀 Trigger Agent Pipeline", type="primary"):
    if not api_key:
        st.error("Please enter your OpenAI API Key.")
    else:
        payload = {
            "name": restaurant_name, "genre": genre, "location": location,
            "target": target_customer, "usp": unique_selling_point,
            "issue": current_issue, "openai_api_key": api_key
        }
        try:
            res = requests.post(agent1_url, json=payload, timeout=60)
            st.success("Pipeline Triggered Successfully!")
            st.json(res.json())
        except Exception as e:
            st.error(f"Connection Error: {e}")
