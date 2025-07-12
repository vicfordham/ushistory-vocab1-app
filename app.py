# app.py — Clean, Stable Rebuild for Dr. Fordham's U.S. History Vocab Mastery App

import streamlit as st
import pandas as pd
import os
import datetime

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="U.S. History Vocab Mastery", layout="centered")

# -------------------- STYLE --------------------
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

# -------------------- SESSION STATE INIT --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student_name = ""
    st.session_state.block = ""
    st.session_state.unit_selected = ""
    st.session_state.current_term_index = 0
    st.session_state.vocab_list = []
    st.session_state.chat_history = []

# -------------------- FUNCTIONS --------------------
def load_vocab(unit_file):
    return pd.read_csv(unit_file)

def record_login(name, block):
    now = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    df = pd.DataFrame([[name, block, now]], columns=["student", "block", "last_login"])
    if os.path.exists("student_logins.csv"):
        old = pd.read_csv("student_logins.csv")
        old = old[old["student"] != name]  # remove duplicates
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv("student_logins.csv", index=False)

def show_main_menu():
    st.markdown("<div class='title'>📚 Welcome to U.S. History Vocab Mastery</div>", unsafe_allow_html=True)
    st.markdown(f"### Hello, {st.session_state.student_name}! (Block {st.session_state.block})")
    st.markdown("Choose a Unit to Begin:")

    cols = st.columns(4)
    for i in range(1, 8):
        with cols[i % 4]:
            if st.button(f"Unit {i}"):
                st.session_state.unit_selected = "vocabulary.csv"
                st.experimental_rerun()

    st.markdown("---")
    if st.button("📝 Take the 50-Word Quiz"):
        st.session_state.unit_selected = "quiz.csv"
        st.experimental_rerun()
    st.button("🚪 Log Out", on_click=logout)

def logout():
    st.session_state.logged_in = False
    st.session_state.student_name = ""
    st.session_state.block = ""
    st.session_state.unit_selected = ""
    st.session_state.chat_history = []
    st.session_state.current_term_index = 0
    st.experimental_rerun()

def show_vocab_conversation():
    if not st.session_state.vocab_list:
        vocab_df = load_vocab(st.session_state.unit_selected)
        st.session_state.vocab_list = vocab_df.to_dict(orient="records")
        st.session_state.current_term_index = 0

    vocab = st.session_state.vocab_list
    idx = st.session_state.current_term_index

    if idx >= len(vocab):
        st.success("✅ You've completed this unit! Great job.")
        if st.button("⬅ Back to Main Menu"):
            st.session_state.unit_selected = ""
            st.experimental_rerun()
        return

    term_data = vocab[idx]
    term = term_data["term"]
    correct_def = term_data["definition"]

    st.markdown(f"**🗣 Let's talk about the word: `{term}`**")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input("What do you think it means?")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)

        # Simulate feedback (basic logic, can be replaced by GPT)
        if user_input.lower() in correct_def.lower():
            response = f"✅ That’s right! '{term}' means: {correct_def}"
            st.session_state.current_term_index += 1
            st.session_state.chat_history = []
        else:
            response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Want to try another example?"

        st.session_state.chat_history.append(("assistant", response))
        with st.chat_message("assistant"):
            st.markdown(response)

# -------------------- APP --------------------
st.title("Dr. Fordham's Vocab Mastery App")

if not st.session_state.logged_in:
    st.subheader("Student Login")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Class Period (Block)", ["First", "Second", "Fourth"])
    if st.button("Log In"):
        name = f"{first.strip().title()} {last.strip().title()}"
        st.session_state.student_name = name
        st.session_state.block = block
        st.session_state.logged_in = True
        record_login(name, block)
        st.experimental_rerun()
else:
    if st.session_state.unit_selected:
        show_vocab_conversation()
    else:
        show_main_menu()
