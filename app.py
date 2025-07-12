
import streamlit as st
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="Dr. Fordham's U.S. History Lab", layout="wide")

# --- CSS for styling ---
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 12px;
        font-weight: bold;
        padding: 0.75em 1.5em;
        margin: 0.25em;
        background: linear-gradient(to right, #6dd5ed, #2193b0);
        color: white;
        font-size: 1.1em;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "student_name" not in st.session_state:
    st.session_state["student_name"] = ""
if "student_block" not in st.session_state:
    st.session_state["student_block"] = ""
if "unit" not in st.session_state:
    st.session_state["unit"] = ""

# --- Student Login Page ---
def student_login():
    st.markdown("<div class=\"main-title\">Welcome to Dr. Fordham's U.S. History Lab</div>", unsafe_allow_html=True)
    st.subheader("Student Login")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    block = st.selectbox("Class Block", ["First", "Second", "Fourth"])

    if st.button("Login"):
        if first_name and last_name:
            full_name = f"{first_name.strip().title()} {last_name.strip().title()}"
            st.session_state["student_name"] = full_name
            st.session_state["student_block"] = block
            st.session_state["page"] = "main_menu"
            st.rerun()

# --- Main Menu ---
def main_menu():
    st.markdown(f"### Welcome, {st.session_state.student_name}!")
    st.markdown("#### Choose a Unit to Begin or Continue:")

    units = [f"Unit {i}" for i in range(1, 8)] + ["Milestone Practice"]
    for unit in units:
        if st.button(unit):
            st.session_state["unit"] = unit
            st.session_state["page"] = "unit_page"
            st.rerun()

# --- Unit Page ---
def unit_page():
    st.markdown(f"### {st.session_state.unit} Vocabulary Practice")
    st.markdown("Progress bar and AI interaction goes here...")
    if st.button("Back to Menu"):
        st.session_state["page"] = "main_menu"
        st.rerun()
    if st.button("Log Out"):
        st.session_state.clear()
        st.rerun()

# --- Routing ---
if st.session_state.page == "login":
    student_login()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
