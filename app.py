
import streamlit as st
import pandas as pd
import datetime
import os

# ---- Styling ----
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

# ---- Helper Functions ----
def load_vocab(unit_name):
    xls = pd.ExcelFile("vocab.csv")
    return xls.parse(unit_name)

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

# ---- Session Setup ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "unit_selected" not in st.session_state:
    st.session_state.unit_selected = None

# ---- Login Page ----
if not st.session_state.logged_in:
    st.title("📘 U.S. History Vocab Mastery Tool")
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
            st.session_state.unit_selected = None
            st.experimental_rerun()
    st.stop()

# ---- Logout Button ----
if st.button("Log Out"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

# ---- Main Menu ----
if not st.session_state.unit_selected:
    st.title(f"Welcome, {st.session_state.student_name}!")
    st.markdown("### Choose a Unit to Begin:")

    cols = st.columns(4)
    for i in range(1, 8):
        with cols[(i - 1) % 4]:
            if st.button(f"Unit {i}"):
                st.session_state.unit_selected = f"Unit {i}"
                st.experimental_rerun()
    with st.container():
        if st.button("Review Quiz"):
            st.session_state.unit_selected = "Review Quiz"
            st.experimental_rerun()
    st.stop()

# ---- Load Vocab ----
unit = st.session_state.unit_selected
try:
    df = load_vocab(unit)
except Exception as e:
    st.error(f"Could not load vocabulary for {unit}: {e}")
    st.stop()

vocab_list = df["term"].tolist()
def_dict = dict(zip(df.term, df.definition))

if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
    st.session_state.chat_history = []

term = vocab_list[st.session_state.current_term_index]
correct_def = def_dict[term]

# ---- Header for Assignment Page ----
st.markdown(f"### {unit} Vocabulary Practice")
st.button("🔙 Back to Menu", on_click=lambda: st.session_state.update({"unit_selected": None, "current_term_index": 0, "chat_history": []}))
st.progress((st.session_state.current_term_index / len(vocab_list)))

# ---- Chat Display ----
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

user_input = st.chat_input(f"What does '{term}' mean?")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    if user_input.lower() in correct_def.lower():
        response = f"✅ Great job! '{term}' is correct. Moving to the next word."
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
