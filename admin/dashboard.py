import streamlit as st
import requests

st.set_page_config(page_title="Wellbeing Admin", layout="wide")

st.title("Wellbeing Admin Dashboard")

st.write("### Backend Status")
try:
    response = requests.get("http://backend:8000/")
    st.success(f"Backend online: {response.json()}")
except:
    st.error("Backend offline")

st.write("### User Management")
user_id = st.text_input("User ID")
if user_id:
    response = requests.get(f"http://backend:8000/tasks/{user_id}")
    st.json(response.json())
