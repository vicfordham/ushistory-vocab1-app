
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os

st.set_page_config(page_title="Dr. Fordham's US History Lab", layout="wide")

# --- Utilities ---
def playful_reminder():
    phrases = [
        "Dr. Fordham knows all, so stay on task!",
        "Remember what Dr. Fordham says: History matters!",
        "Don’t make Dr. Fordham come over there!",
        "This one's for you, Dr. Fordham!",
        "You're making Dr. Fordham proud... maybe."
    ]
    return random.choice(phrases)

# --- Session State Initialization ---
if "page" not in st.session_state:
    st.session_state.page = "login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "block" not in st.session_state:
    st.session_state.block = ""
if "unit" not in st.session_state:
    st.session_state.unit = ""
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
if "vocab_data" not in st.session_state:
    st.session_state.vocab_data = {}

# --- Load Vocabulary File ---
@st.cache_data
def load_vocab_data():
    xls = pd.ExcelFile("vocab.xlsx")
    return {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}

st.session_state.vocab_data = load_vocab_data()

# --- Progress Tracking ---
def get_student_progress(name):
    progress_file = "student_progress.csv"
    if not os.path.exists(progress_file):
        return {}
    df = pd.read_csv(progress_file)
    student_data = df[df["name"].str.lower() == name.lower()]
    if student_data.empty:
        return {}
    return student_data.iloc[0].to_dict()

def update_progress(name, block, unit, score):
    progress_file = "student_progress.csv"
    now = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    if os.path.exists(progress_file):
        df = pd.read_csv(progress_file)
    else:
        df = pd.DataFrame(columns=["name", "block", "last_login"] + [f"Unit {i}" for i in range(1, 8)] + ["Milestone", "Overall Progress"])

    mask = df["name"].str.lower() == name.lower()
    if mask.any():
        df.loc[mask, unit] = score
        df.loc[mask, "last_login"] = now
    else:
        new_row = {
            "name": name,
            "block": block,
            "last_login": now,
            unit: score
        }
        for col in df.columns:
            if col not in new_row:
                new_row[col] = 0
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    unit_cols = [f"Unit {i}" for i in range(1, 8)]
    df["Overall Progress"] = (df[unit_cols].mean(axis=1) * 100).round().clip(upper=100)
    df.to_csv(progress_file, index=False)

# --- Main Pages ---
def login_page():
    st.title("Dr. Fordham's US History Lab")
    st.subheader("Student Login")
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    block = st.selectbox("Class Block", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if fname and lname:
            name = f"{lname.strip().title()}, {fname.strip().title()}"
            st.session_state.student_name = name
            st.session_state.block = block
            st.session_state.page = "main_menu"
            update_progress(name, block, None, None)
            st.rerun()

def main_menu():
    st.title("Main Menu")
    st.markdown(f"Welcome, **{st.session_state.student_name}**!")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.page = "login"
            st.rerun()
    progress = get_student_progress(st.session_state.student_name)
    overall = progress.get("Overall Progress", 0)
    st.progress(int(overall), text=f"Overall Progress: {int(overall)}%")

    for i in range(1, 8):
        if st.button(f"Unit {i} Vocabulary"):
            st.session_state.unit = f"Unit {i}"
            st.session_state.page = "unit_page"
            st.session_state.current_term_index = 0
            st.session_state.chat_history = []
            st.rerun()

    if st.button("Milestone Practice"):
        st.session_state.unit = "Milestone"
        st.session_state.page = "unit_page"
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []
        st.rerun()

def unit_page():
    unit = st.session_state.unit
    st.title(f"{unit} - Vocabulary Practice")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("⬅ Back"):
            st.session_state.page = "main_menu"
            st.rerun()
    with col2:
        if st.button("Logout"):
            st.session_state.page = "login"
            st.rerun()

    df = st.session_state.vocab_data.get(unit)
    if df is None or df.empty:
        st.error(f"No vocabulary found for {unit}")
        return

    vocab_list = df.to_dict(orient="records")
    index = st.session_state.current_term_index
    if index >= len(vocab_list):
        st.success("🎉 You've finished this unit!")
        update_progress(st.session_state.student_name, st.session_state.block, unit, 100)
        return

    mastered = int((index / len(vocab_list)) * 100)
    st.progress(mastered, text=f"{mastered}% Mastered")

    term = vocab_list[index]
    st.markdown(f"**🗣 Let's talk about the word: `{term['term']}`**")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input("What do you think it means?")
    if user_input:
        correct_def = term["definition"]
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        if user_input.lower() in correct_def.lower():
            response = f"✅ That's right! '{term['term']}' means: {correct_def}"
            st.session_state.current_term_index += 1
        else:
            response = f"🤔 Not quite. '{term['term']}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"
            st.info(f"{playful_reminder()} Try this: How do you think '{term['term']}' affected history?")

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append(("assistant", response))

# --- App Controller ---
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
