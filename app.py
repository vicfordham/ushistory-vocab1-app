
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="U.S. History Vocab Mastery", layout="wide")

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "unit_selected" not in st.session_state:
    st.session_state.unit_selected = None
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load vocabulary data
def load_vocab(unit_tab):
    try:
        df = pd.read_excel("vocab.xlsx", sheet_name=unit_tab)
        return df
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit_tab}: {e}")
        return pd.DataFrame()

# Login page
def login_page():
    st.title("📚 U.S. History Vocab Mastery - Login")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    if st.button("Log in"):
        if first_name and last_name:
            st.session_state.student_name = f"{first_name.strip().title()} {last_name.strip().title()}"
            st.session_state.logged_in = True
            st.experimental_rerun()

# Main menu with Unit buttons
def main_menu():
    st.title(f"Welcome, {st.session_state.student_name} 👋")
    st.subheader("📖 Choose a Unit")
    col1, col2, col3, col4 = st.columns(4)
    units = [f"Unit {i}" for i in range(1, 8)]
    with col1:
        for i in range(0, 2):
            if st.button(units[i]):
                st.session_state.unit_selected = units[i]
                st.experimental_rerun()
    with col2:
        for i in range(2, 4):
            if st.button(units[i]):
                st.session_state.unit_selected = units[i]
                st.experimental_rerun()
    with col3:
        for i in range(4, 6):
            if st.button(units[i]):
                st.session_state.unit_selected = units[i]
                st.experimental_rerun()
    with col4:
        for i in range(6, 7):
            if st.button(units[i]):
                st.session_state.unit_selected = units[i]
                st.experimental_rerun()
    st.markdown("---")
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.student_name = ""
        st.session_state.unit_selected = None
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []
        st.experimental_rerun()

# Unit page with vocab interaction
def unit_page():
    unit = st.session_state.unit_selected
    st.title(f"{unit} Vocabulary")
    if st.button("⬅ Back to Main Menu"):
        st.session_state.unit_selected = None
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []
        st.experimental_rerun()
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.student_name = ""
        st.session_state.unit_selected = None
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []
        st.experimental_rerun()

    vocab_df = load_vocab(unit)
    if vocab_df.empty:
        return

    vocab_list = vocab_df.to_dict("records")
    if st.session_state.current_term_index >= len(vocab_list):
        st.success("🎉 You've completed all terms in this unit!")
        return

    term_data = vocab_list[st.session_state.current_term_index]
    term = term_data["term"]
    correct_def = term_data["definition"]

    st.markdown(f"**🗣 Let's talk about the word: `{term}`**")

    for speaker, message in st.session_state.chat_history:
        with st.chat_message(speaker):
            st.markdown(message)

    user_input = st.chat_input("Type your response...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        if user_input.lower() in correct_def.lower():
            response = f"✅ That's right! '{term}' means: {correct_def}. Great work!"
            st.session_state.current_term_index += 1
            st.session_state.chat_history = []
        else:
            response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append(("assistant", response))

# App logic
if not st.session_state.logged_in:
    login_page()
elif st.session_state.unit_selected:
    unit_page()
else:
    main_menu()
