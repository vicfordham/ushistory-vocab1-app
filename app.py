
import streamlit as st
import pandas as pd
import random
import datetime

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "unit" not in st.session_state:
    st.session_state.unit = ""
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
if "mastered_terms" not in st.session_state:
    st.session_state.mastered_terms = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load vocabulary from Excel with openpyxl engine
def load_vocab(unit_name):
    try:
        df = pd.read_excel("vocab.xlsx", sheet_name=unit_name, engine="openpyxl")
        return df.to_dict("records")
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit_name}: {e}")
        return []

# Login Page
def login_page():
    st.title("U.S. History Vocabulary Mastery")
    st.subheader("Login")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    if st.button("Login"):
        if first and last:
            st.session_state.student_name = f"{first.strip().title()} {last.strip().title()}"
            st.session_state.page = "main_menu"
            st.rerun()
        else:
            st.warning("Please enter both first and last name.")

# Main Menu Page
def main_menu():
    st.title(f"Welcome, {st.session_state.student_name} 👋")
    st.subheader("Choose a Unit")
    col1, col2, col3 = st.columns(3)
    units = ["Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6", "Unit 7"]
    for i, unit in enumerate(units):
        if i % 3 == 0:
            col = col1
        elif i % 3 == 1:
            col = col2
        else:
            col = col3
        if col.button(unit):
            st.session_state.unit = unit
            st.session_state.page = "unit_page"
            st.session_state.current_term_index = 0
            st.session_state.mastered_terms = []
            st.session_state.chat_history = []
            st.rerun()

    if st.button("Logout"):
        st.session_state.page = "login"
        st.session_state.student_name = ""
        st.rerun()

# Unit Page (Chat-Based Learning)
def unit_page():
    unit = st.session_state.unit
    vocab_list = load_vocab(unit)

    if not vocab_list:
        st.error("No vocabulary loaded.")
        return

    total_terms = len(vocab_list)
    mastered = len(st.session_state.mastered_terms)
    progress = mastered / total_terms if total_terms > 0 else 0
    st.progress(progress, text=f"Mastery: {mastered}/{total_terms}")

    if st.button("⬅️ Back to Menu"):
        st.session_state.page = "main_menu"
        st.rerun()
    if st.button("Logout"):
        st.session_state.page = "login"
        st.session_state.student_name = ""
        st.rerun()

    if st.session_state.current_term_index >= total_terms:
        st.success("🎉 You've completed this unit!")
        return

    term_data = vocab_list[st.session_state.current_term_index]
    term = term_data["term"]
    correct_def = term_data["definition"]
    example = term_data["example"]

    st.markdown(f"### 🧠 Let's talk about the word: **{term}**")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input("What do you think it means?")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        if user_input.lower() in correct_def.lower():
            response = f"✅ That's right! '{term}' means: {correct_def}

Example: {example}"
            st.session_state.chat_history.append(("assistant", response))
            st.session_state.mastered_terms.append(term)
            st.session_state.current_term_index += 1
            st.rerun()
        else:
            response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"
            st.session_state.chat_history.append(("assistant", response))
            st.rerun()

# Page Router
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
