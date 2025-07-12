
import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Dr. Fordham's US History Lab", layout="wide")

# Title
st.title("📚 Dr. Fordham's US History Lab")

# Inject humor
def dr_fordham_says():
    sayings = [
        "Dr. Fordham knows all, so stay on task!",
        "Don't make Dr. Fordham raise an eyebrow!",
        "Legend has it Dr. Fordham never forgets a wrong answer!",
        "Rumor has it Dr. Fordham can hear your thoughts—define that term!",
        "Dr. Fordham is watching... define wisely!"
    ]
    return random.choice(sayings)

# Load vocabulary from Excel
@st.cache_data
def load_vocab(unit):
    try:
        df = pd.read_excel("vocab.xlsx", sheet_name=unit)
        return df
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit}: {e}")
        return pd.DataFrame()

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "block" not in st.session_state:
    st.session_state.block = ""
if "unit" not in st.session_state:
    st.session_state.unit = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "term_index" not in st.session_state:
    st.session_state.term_index = 0
if "mastered_terms" not in st.session_state:
    st.session_state.mastered_terms = {}

# Progress calculation
def calculate_unit_progress(unit_terms, mastered):
    if not unit_terms:
        return 0
    return int(round((len(mastered) / len(unit_terms)) * 100))

# Login page
def login_page():
    st.subheader("Student Login")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Class Block", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if first and last and block:
            st.session_state.student_name = f"{first.strip().title()} {last.strip().title()}"
            st.session_state.block = block
            st.session_state.page = "main_menu"
            st.rerun()
        else:
            st.warning("Please fill in all fields.")

# Main menu
def main_menu():
    st.markdown(f"### Welcome, {st.session_state.student_name}!")
    total_terms = 0
    total_mastered = 0
    unit_buttons = []

    st.write("#### Select a Unit:")
    cols = st.columns(4)
    for i in range(1, 8):
        unit = f"Unit {i}"
        unit_buttons.append(cols[(i - 1) % 4].button(unit))
    milestone_button = cols[3].button("Milestone Practice")

    # Overall progress bar
    for i in range(1, 8):
        df = load_vocab(f"Unit {i}")
        terms = df["term"].tolist() if not df.empty else []
        mastered = st.session_state.mastered_terms.get(f"Unit {i}", set())
        total_terms += len(terms)
        total_mastered += len(mastered)

    if total_terms:
        overall = int(round((total_mastered / total_terms) * 100))
        st.progress(overall, text=f"Overall Progress: {overall}%")

    for i, clicked in enumerate(unit_buttons, 1):
        if clicked:
            st.session_state.unit = f"Unit {i}"
            st.session_state.page = "unit_chat"
            st.session_state.term_index = 0
            st.session_state.chat_history = []
            st.rerun()

    if milestone_button:
        st.session_state.unit = "Milestone"
        st.session_state.page = "unit_chat"
        st.session_state.term_index = 0
        st.session_state.chat_history = []
        st.rerun()

    if st.button("Log Out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "login"
        st.rerun()

# Chat page
def unit_chat():
    st.button("⬅ Back to Main Menu", on_click=lambda: st.session_state.update({"page": "main_menu"}))
    st.button("🚪 Log Out", on_click=lambda: st.session_state.update({"page": "login"}))

    unit = st.session_state.unit
    df = load_vocab(unit if unit != "Milestone" else f"Unit {random.randint(1,7)}")
    if df.empty:
        st.warning("No vocabulary found.")
        return

    terms = df["term"].tolist()
    defs = df["definition"].tolist()
    mastered = st.session_state.mastered_terms.get(unit, set())
    index = st.session_state.term_index

    # Progress bar
    progress = calculate_unit_progress(terms, mastered)
    st.progress(progress, text=f"Progress for {unit}: {progress}%")

    if index >= len(terms):
        st.success(f"You've completed {unit}!")
        return

    term = terms[index]
    correct_def = defs[index]

    if st.session_state.chat_history:
        for speaker, msg in st.session_state.chat_history:
            with st.chat_message(speaker):
                st.markdown(msg)

    if st.session_state.term_index < len(terms):
        with st.chat_message("assistant"):
            prompt = f"Let's talk about the word **{term}**. What do you think it means?"
            st.markdown(prompt)
            st.session_state.chat_history.append(("assistant", prompt))

        user_input = st.chat_input("Your answer:")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
                st.session_state.chat_history.append(("user", user_input))

            if user_input.lower() in correct_def.lower():
                response = f"✅ That's right! **{term}** means: {correct_def}. Now let's apply it! {dr_fordham_says()}"
                mastered.add(term)
                st.session_state.mastered_terms[unit] = mastered
                st.session_state.term_index += 1
            else:
                response = f"🤔 Not quite. **{term}** means: {correct_def}. Let's dig deeper. {dr_fordham_says()}"

            with st.chat_message("assistant"):
                st.markdown(response)
                st.session_state.chat_history.append(("assistant", response))
            st.rerun()

# Route logic
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_chat":
    unit_chat()
