
import streamlit as st
import pandas as pd
import random
from datetime import datetime

# App title
st.set_page_config(page_title="Dr. Fordham's U.S. History Lab", layout="wide")

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False
if "unit" not in st.session_state:
    st.session_state.unit = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0

# Load vocab data
def load_vocab(unit):
    try:
        df = pd.read_excel("vocab.xlsx", sheet_name=unit)
        return df
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit}: {e}")
        return None

# Playful reminder
def playful_reminder():
    reminders = [
        "Dr. Fordham knows all, so stay on task!",
        "Even Dr. Fordham would expect you to get this one!",
        "Keep going—Dr. Fordham is watching!",
        "Focus up, scholar! Dr. Fordham believes in you!",
        "Dr. Fordham says, 'Mastery takes practice!'"
    ]
    return random.choice(reminders)

# Homepage
def home():
    st.markdown("<h1 style='text-align: center;'>Welcome to Dr. Fordham's U.S. History Lab</h1>", unsafe_allow_html=True)
    st.subheader("Student Login")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    block = st.selectbox("Class Block", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if first_name and last_name:
            st.session_state.student_name = f"{last_name.strip().title()}, {first_name.strip().title()}"
            st.session_state.block = block
            st.session_state.logged_in = True
            st.session_state.page = "main_menu"
            st.experimental_rerun()

    st.subheader("Teacher Login")
    teacher_pw = st.text_input("Enter Password", type="password")
    if st.button("Login as Teacher"):
        if teacher_pw == "drfordham123":  # Example password
            st.session_state.teacher_logged_in = True
            st.session_state.page = "teacher_dashboard"
            st.experimental_rerun()

# Main menu
def main_menu():
    st.markdown(f"### Welcome, {st.session_state.student_name}")
    overall_progress = random.randint(50, 100)  # Placeholder
    st.progress(overall_progress / 100, text=f"Overall Progress: {overall_progress}%")

    col1, col2, col3 = st.columns(3)
    for i in range(1, 8):
        with [col1, col2, col3][(i - 1) % 3]:
            if st.button(f"Unit {i} Vocabulary"):
                st.session_state.unit = f"Unit {i}"
                st.session_state.page = "unit_page"
                st.experimental_rerun()

    if st.button("Milestone Practice"):
        st.session_state.unit = "Milestone"
        st.session_state.page = "unit_page"
        st.experimental_rerun()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "home"
        st.experimental_rerun()

# Unit page
def unit_page():
    st.markdown(f"## {st.session_state.unit} Vocabulary Practice")
    vocab_df = load_vocab(st.session_state.unit)
    if vocab_df is None or vocab_df.empty:
        st.warning("No vocabulary found.")
        return

    terms = vocab_df.to_dict("records")
    if st.session_state.current_term_index >= len(terms):
        st.success("🎉 You've completed this unit!")
        if st.button("Back to Menu"):
            st.session_state.page = "main_menu"
            st.experimental_rerun()
        return

    term = terms[st.session_state.current_term_index]
    st.info(f"{playful_reminder()} Try this: How do you think '{term['term']}' affected history?")

    user_input = st.chat_input("Your answer:")
    if user_input:
        correct_def = term["definition"]
        if user_input.lower() in correct_def.lower():
            response = f"✅ That's right! '{term['term']}' means: {correct_def}. Great job!"
            st.session_state.current_term_index += 1
        else:
            response = f"🤔 Not quite. '{term['term']}' means: {correct_def}. Let's try to break it down more. What part confused you?"

        with st.chat_message("assistant"):
            st.markdown(response)

    st.button("Back to Menu", on_click=lambda: st.session_state.update({"page": "main_menu"}))
    st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "page": "home"}))

# Teacher dashboard
def teacher_dashboard():
    st.title("📊 Teacher Dashboard: Dr. Fordham")
    st.info("Gradebook and tracking tools coming soon.")
    if st.button("Logout"):
        st.session_state.teacher_logged_in = False
        st.session_state.page = "home"
        st.experimental_rerun()

# Page router
if st.session_state.page == "home":
    home()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
elif st.session_state.page == "teacher_dashboard":
    teacher_dashboard()
