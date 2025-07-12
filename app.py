import streamlit as st
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="Dr. Fordham's US History Lab", layout="wide")

# Custom CSS styling
st.markdown("""
    <style>
    .main-title {
        font-size: 36px;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 30px;
    }
    .unit-button {
        background: linear-gradient(to right, #6dd5ed, #2193b0);
        border: none;
        border-radius: 15px;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin: 10px;
        width: 200px;
        height: 100px;
        transition: transform 0.2s;
    }
    .unit-button:hover {
        transform: scale(1.05);
        cursor: pointer;
    }
    .logout-button {
        color: white;
        background-color: #e74c3c;
        padding: 0.5em 1.5em;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        margin-top: 1em;
    }
    .logout-button:hover {
        background-color: #c0392b;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "page" not in st.session_state:
    st.session_state.page = "login"

# Login logic
def login_page():
    st.markdown('<div class="main-title">Welcome to Dr. Fordham's U.S. History Lab</div>', unsafe_allow_html=True)
    st.subheader("Student Login")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Which block are you in?", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if first and last:
            st.session_state.user_name = f"{last.strip().title()}, {first.strip().title()}"
            st.session_state.logged_in = True
            st.session_state.page = "main_menu"
            st.rerun()

# Main menu logic
def main_menu():
    st.markdown(f'<div class="main-title">Welcome, {st.session_state.user_name}!</div>', unsafe_allow_html=True)
    st.markdown("### Select a Unit to Begin Practice:")
    col1, col2, col3 = st.columns(3)
    units = [f"Unit {i}" for i in range(1, 8)] + ["Milestone Practice"]

    for i, unit in enumerate(units):
        col = [col1, col2, col3][i % 3]
        if col.button(unit, key=unit):
            st.session_state.selected_unit = unit
            st.session_state.page = "unit_page"
            st.rerun()

    if st.button("Log out", key="logout", help="Click to log out"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.page = "login"
        st.rerun()

# Unit page placeholder
def unit_page():
    st.markdown(f"<h2 style='text-align:center;'>🧠 {st.session_state.selected_unit} Practice</h2>", unsafe_allow_html=True)
    st.markdown(f"Dr. Fordham knows all, so stay on task!")
    if st.button("⬅ Back to Main Menu"):
        st.session_state.page = "main_menu"
        st.rerun()

# App routing
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    if st.session_state.logged_in:
        main_menu()
    else:
        st.session_state.page = "login"
        st.rerun()
elif st.session_state.page == "unit_page":
    unit_page()