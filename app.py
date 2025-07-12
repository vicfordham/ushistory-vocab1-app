
# --- app.py (fixed login rerun issue) ---
import streamlit as st
import pandas as pd
import datetime
import os

# Styling
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
    .title { font-size: 2em; font-weight: 700; color: #2c3e50; }
    </style>
""", unsafe_allow_html=True)

st.title("📘 U.S. History Vocab Mastery Tool")

# --- Helper functions ---
def load_vocab(unit_csv='vocabulary.csv'):
    return pd.read_csv(unit_csv)

def record_login(name, block):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    data = pd.DataFrame([[name, block, timestamp]], columns=["student", "block", "last_login"])
    if os.path.exists("student_logins.csv"):
        existing = pd.read_csv("student_logins.csv")
        existing = existing[existing.student != name]  # remove duplicates
        full = pd.concat([existing, data])
    else:
        full = data
    full.to_csv("student_logins.csv", index=False)

# --- Session setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Login Page ---
if not st.session_state.logged_in:
    st.subheader("Log In")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Class Period (Block):", ["First", "Second", "Fourth"])

    if st.button("Log In"):
        name = f"{first.strip().title()} {last.strip().title()}"
        if name and block:
            st.session_state.student_name = name
            st.session_state.block = block
            st.session_state.logged_in = True
            record_login(name, block)
            st.success("✅ Logged in! Redirecting...")
            st.stop()
    st.stop()

# --- Main Menu ---
st.subheader(f"Welcome, {st.session_state.student_name}!")
st.markdown("**Choose a Unit to Begin:**")

units = [f"Unit {i}" for i in range(1, 8)] + ["Review Quiz"]
unit = st.selectbox("Select a Unit:", units)

if unit == "Unit 1":
    vocab_df = load_vocab()
    vocab_list = vocab_df["term"].tolist()
    def_dict = dict(zip(vocab_df.term, vocab_df.definition))

    if "current_term_index" not in st.session_state:
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []

    term = vocab_list[st.session_state.current_term_index]
    correct_def = def_dict[term]

    st.markdown(f"**🗣 Let's talk about the word: `{term}`**")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input("What does this mean?")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        if user_input and correct_def and user_input.lower() in correct_def.lower():
            response = f"✅ Great job! '{term}' is correct. Let's move to the next word."
            st.session_state.current_term_index += 1
            st.session_state.chat_history = []
        else:
            response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append(("assistant", response))

        if st.session_state.current_term_index >= len(vocab_list):
            st.success("🎉 You've completed all words in this Unit!")
            st.session_state.current_term_index = 0
            st.session_state.chat_history = []

# --- Logout ---
if st.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.student_name = ""
    st.session_state.block = ""
    st.session_state.current_term_index = 0
    st.session_state.chat_history = []
    st.rerun()
