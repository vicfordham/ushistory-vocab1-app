
import streamlit as st
import pandas as pd
from datetime import datetime

# Custom CSS for youthful styling
st.markdown("""
    <style>
        .main {
            background-color: #f0f4f8;
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
        .title {
            font-size: 2em;
            font-weight: 700;
            color: #2c3e50;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>📚 Dr. Fordham's U.S. History Lab</div>", unsafe_allow_html=True)
st.markdown("---")

# Session state for login
if "student_name" not in st.session_state:
    st.session_state.student_name = None

# Login Page
if not st.session_state.student_name:
    st.subheader("📝 Student Login")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    block = st.selectbox("Select Your Block", ["First", "Second", "Fourth"])
    if st.button("Enter"):
        if first_name and last_name:
            st.session_state.student_name = f"{first_name} {last_name}"
            st.session_state.block = block
            st.session_state.login_time = datetime.now().isoformat()
        else:
            st.warning("Please enter both first and last names.")
    st.stop()

# Unit Selection Page
st.success(f"Welcome, {st.session_state.student_name} ({st.session_state.block} Block)!")
st.subheader("📘 Choose a Vocabulary Unit to Begin")

cols = st.columns(4)
units = [f"Unit {i}" for i in range(1, 8)]
unit_selected = None

for i, unit in enumerate(units):
    if cols[i % 4].button(unit):
        unit_selected = unit

# Quiz Button
if st.button("🎯 Final Quiz (50 Random Words)"):
    st.info("Quiz mode coming soon!")

# Simulate Unit 1 session
if unit_selected == "Unit 1":
    st.markdown("### ✏️ Unit 1 Vocabulary")
    st.info("Interactive vocabulary session for Unit 1 will go here.")
