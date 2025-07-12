
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="U.S. History Vocab", layout="wide")

# Custom CSS
st.markdown("""
<style>
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

# Load vocab data
@st.cache_data
def load_vocab_data():
    try:
        df = pd.read_excel("vocab.xlsx", sheet_name=None)
        return df
    except Exception as e:
        st.error(f"Error loading vocab.xlsx: {e}")
        return {}

vocab_data = load_vocab_data()
units = list(vocab_data.keys())

# Initialize session state
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "unit_selected" not in st.session_state:
    st.session_state.unit_selected = None
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Login page
def login_page():
    st.title("🧠 U.S. History Vocabulary Tool")
    st.subheader("Please log in to get started.")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    if st.button("Login"):
        if first and last:
            st.session_state.student_name = f"{first.strip().title()} {last.strip().title()}"
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.warning("Please enter both first and last name.")

# Main menu
def main_menu():
    st.title(f"Welcome, {st.session_state.student_name}!")
    st.subheader("Select a Unit to Begin:")
    cols = st.columns(4)
    for i, unit in enumerate(units):
        if cols[i % 4].button(unit):
            st.session_state.unit_selected = unit
            st.session_state.current_term_index = 0
            st.session_state.chat_history = []
            st.experimental_rerun()
    st.button("Log out", on_click=logout)

# Logout
def logout():
    st.session_state.logged_in = False
    st.session_state.student_name = ""
    st.session_state.unit_selected = None
    st.session_state.current_term_index = 0
    st.session_state.chat_history = []
    st.experimental_rerun()

# Unit page
def unit_page(unit_name):
    st.markdown(f"### Unit: {unit_name}")
    st.button("⬅️ Back to Menu", on_click=go_back)
    st.button("🚪 Log out", on_click=logout)
    
    vocab_df = vocab_data.get(unit_name)
    if vocab_df is None:
        st.error(f"Could not load vocabulary for {unit_name}.")
        return

    vocab_list = vocab_df["term"].tolist()
    definitions = dict(zip(vocab_df["term"], vocab_df["definition"]))

    # Progress bar
    progress = (st.session_state.current_term_index) / len(vocab_list)
    st.progress(progress)

    # Current term
    if st.session_state.current_term_index < len(vocab_list):
        term = vocab_list[st.session_state.current_term_index]
        correct_def = definitions[term]

        st.markdown(f"**🗣 Let's talk about the word: `{term}`**")

        # Chat history
        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(msg)

        user_input = st.chat_input("What do you think it means?")
        if user_input:
            if user_input.lower() in correct_def.lower():
                response = f"✅ That's right! '{term}' means: {correct_def}."
                st.session_state.current_term_index += 1
            else:
                response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"

            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("assistant", response))
            st.experimental_rerun()
    else:
        st.success("🎉 You've completed this unit!")

def go_back():
    st.session_state.unit_selected = None
    st.session_state.chat_history = []
    st.session_state.current_term_index = 0
    st.experimental_rerun()

# App control flow
if not st.session_state.logged_in:
    login_page()
elif st.session_state.unit_selected:
    unit_page(st.session_state.unit_selected)
else:
    main_menu()

