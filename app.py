
# Dr. Fordham's U.S. History Lab - Streamlit App

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os

st.set_page_config(page_title="Dr. Fordham's US History Lab", layout="wide")

# --- Constants ---
UNITS = [f"Unit {i}" for i in range(1, 8)]
MILESTONE = "Milestone Practice"
ALL_UNITS = UNITS + [MILESTONE]

# --- Helper Functions ---
def load_vocab_data():
    try:
        return pd.read_excel("vocab.xlsx", sheet_name=None)
    except Exception as e:
        st.error(f"Could not load vocabulary data: {e}")
        return {}

def get_current_time():
    return datetime.now().strftime("%B %d, %Y - %I:%M %p")

def evaluate_response(user_input, correct_def):
    if user_input and correct_def:
        user_input = user_input.lower()
        correct_def = correct_def.lower()
        if user_input in correct_def or any(word in correct_def for word in user_input.split()):
            return True
    return False

def playful_reminder():
    return random.choice([
        "Don't slack off... Dr. Fordham is watching! 👀",
        "You're doing great, but Dr. Fordham demands excellence! 💪",
        "Dr. Fordham says: ‘Keep pushing, scholar!’ 🧠",
        "Uh oh… Dr. Fordham smells laziness. Prove him wrong! 😂",
        "Stay sharp! Dr. Fordham knows all! 🧐"
    ])

def update_mastery(student_id, unit, is_correct):
    if "mastery" not in st.session_state:
        st.session_state.mastery = {}
    if student_id not in st.session_state.mastery:
        st.session_state.mastery[student_id] = {}
    if unit not in st.session_state.mastery[student_id]:
        st.session_state.mastery[student_id][unit] = []

    if is_correct and len(st.session_state.mastery[student_id][unit]) < len(st.session_state.vocab[unit]):
        st.session_state.mastery[student_id][unit].append(st.session_state.current_term)

def calculate_progress(student_id, unit):
    total = len(st.session_state.vocab.get(unit, []))
    correct = len(st.session_state.mastery.get(student_id, {}).get(unit, []))
    percent = (correct / total * 100) if total else 0
    return int(percent) if percent % 1 < 0.5 else int(percent) + 1

# --- App Pages ---
def login():
    st.title("Dr. Fordham's US History Lab")

    col1, col2 = st.columns(2)
    with col1:
        first = st.text_input("First Name")
    with col2:
        last = st.text_input("Last Name")

    block = st.selectbox("Select Your Block", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if first and last:
            student = f"{last.strip().title()}, {first.strip().title()}"
            st.session_state.student = student
            st.session_state.block = block
            st.session_state.last_login = get_current_time()
            st.session_state.page = "menu"
            st.experimental_rerun()

def student_menu():
    st.markdown(f"### Welcome, **{st.session_state.student}**")
    st.markdown(f"**Block:** {st.session_state.block} | **Last Login:** {st.session_state.last_login}")

    total_units = len(UNITS)
    total_words = sum(len(st.session_state.vocab.get(unit, [])) for unit in UNITS)
    total_correct = sum(len(st.session_state.mastery.get(st.session_state.student, {}).get(unit, [])) for unit in UNITS)
    overall_progress = (total_correct / total_words * 100) if total_words else 0
    if overall_progress % 1 >= 0.5:
        overall_progress = int(overall_progress) + 1
    else:
        overall_progress = int(overall_progress)

    st.markdown(f"#### Overall Progress: **{overall_progress}%**")
    st.progress(overall_progress / 100)

    col1, col2, col3 = st.columns(3)
    for i, unit in enumerate(ALL_UNITS):
        col = [col1, col2, col3][i % 3]
        with col:
            if st.button(unit):
                st.session_state.unit = unit
                st.session_state.current_term_index = 0
                st.session_state.page = "chat"
                st.experimental_rerun()

    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

def chat_page():
    unit = st.session_state.unit
    student = st.session_state.student
    vocab_terms = st.session_state.vocab.get(unit, [])

    if st.button("Back to Main Menu"):
        st.session_state.page = "menu"
        st.experimental_rerun()

    st.markdown(f"### {unit} Vocabulary Practice")
    unit_progress = calculate_progress(student, unit)
    st.markdown(f"Progress: **{unit_progress}%**")
    st.progress(unit_progress / 100)

    if st.session_state.current_term_index >= len(vocab_terms):
        st.success("🎉 You've completed this unit!")
        return

    term = vocab_terms[st.session_state.current_term_index]
    st.markdown(f"**🗣 Let's talk about the word: `{term['term']}`**")
    user_input = st.text_input("What do you think it means?", key=term['term'])

    if st.button("Submit"):
        correct_def = term['definition']
        if evaluate_response(user_input, correct_def):
            update_mastery(student, unit, True)
            st.success(f"✅ That's right! '{term['term']}' means: {correct_def}")
        else:
            st.warning(f"🤔 Not quite. '{term['term']}' actually means: {correct_def}")
            st.info(f"{playful_reminder()}
Try this: How do you think '{term['term']}' affected history?")

        st.session_state.current_term_index += 1
        st.experimental_rerun()

# --- Load Vocabulary ---
vocab_raw = load_vocab_data()
if "vocab" not in st.session_state:
    st.session_state.vocab = {}
    for unit in ALL_UNITS:
        if unit == MILESTONE:
            combined = []
            for u in UNITS:
                combined += vocab_raw.get(u, pd.DataFrame()).sample(n=min(3, len(vocab_raw.get(u, []))), random_state=42).to_dict(orient="records")
            st.session_state.vocab[unit] = combined
        else:
            st.session_state.vocab[unit] = vocab_raw.get(unit, pd.DataFrame()).to_dict(orient="records")

# --- Page Routing ---
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login()
elif st.session_state.page == "menu":
    student_menu()
elif st.session_state.page == "chat":
    chat_page()
