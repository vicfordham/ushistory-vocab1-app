
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os

st.set_page_config(page_title="Dr. Fordham's US History Lab", layout="wide")

# Load vocabulary Excel with multiple sheets
VOCAB_FILE = "vocab.xlsx"

def load_vocab(unit_name):
    try:
        df = pd.read_excel(VOCAB_FILE, sheet_name=unit_name, engine="openpyxl")
        if "term" in df.columns and "definition" in df.columns:
            return df[["term", "definition"]]
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit_name}: {e}")
    return pd.DataFrame(columns=["term", "definition"])

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = "login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "unit" not in st.session_state:
    st.session_state.unit = None
if "user" not in st.session_state:
    st.session_state.user = None
if "block" not in st.session_state:
    st.session_state.block = None

# Reminder for fun
def playful_reminder():
    return random.choice([
        "Dr. Fordham knows all, so stay on task!",
        "You don't want Dr. Fordham seeing you slack off!",
        "Stay focused — Dr. Fordham is watching!",
        "Remember, Dr. Fordham says: Mastery is the mission!",
    ])

# Save and load student data
def get_student_file():
    return f"students/{st.session_state.user.lower().replace(' ', '_')}.csv"

def save_student_progress(unit, term, score):
    os.makedirs("students", exist_ok=True)
    file = get_student_file()
    now = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    entry = pd.DataFrame([{
        "unit": unit,
        "term": term,
        "score": score,
        "last_login": now,
        "block": st.session_state.block,
        "student": st.session_state.user
    }])
    if os.path.exists(file):
        df = pd.read_csv(file)
        df = df[df.term != term]
        df = pd.concat([df, entry])
    else:
        df = entry
    df.to_csv(file, index=False)

def load_student_progress(unit):
    file = get_student_file()
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df[df.unit == unit]
    return pd.DataFrame(columns=["unit", "term", "score", "last_login", "block", "student"])

def get_mastery_score(unit, vocab_df):
    progress = load_student_progress(unit)
    mastered = progress[progress.score == 1]["term"].nunique()
    total = vocab_df["term"].nunique()
    return int((mastered / total) * 100 + 0.5) if total else 0

# Login page
def login_page():
    st.title("Dr. Fordham's US History Lab")
    st.subheader("Student Login")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Class Block", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if first and last:
            full_name = f"{last.strip().title()}, {first.strip().title()}"
            st.session_state.user = full_name
            st.session_state.block = block
            st.session_state.page = "main_menu"
            st.rerun()

# Main menu
def main_menu():
    st.title("Welcome to Dr. Fordham's US History Lab")
    st.subheader(f"Hello, {st.session_state.user}!")
    unit_names = [f"Unit {i}" for i in range(1, 8)] + ["Milestone Practice"]

    total_score = 0
    total_terms = 0
    for unit in unit_names[:-1]:  # exclude Milestone for overall progress
        vocab = load_vocab(unit)
        total_terms += len(vocab)
        progress = load_student_progress(unit)
        total_score += len(progress[progress.score == 1])
    if total_terms > 0:
        percent = int((total_score / total_terms) * 100 + 0.5)
    else:
        percent = 0
    st.progress(percent, text=f"Overall Progress: {percent}%")

    cols = st.columns(4)
    for i, unit in enumerate(unit_names):
        if cols[i % 4].button(unit):
            st.session_state.unit = unit
            st.session_state.page = "unit_page"
            st.rerun()

    st.button("Logout", on_click=lambda: st.session_state.clear())

# Unit interaction
def unit_page():
    unit = st.session_state.unit
    st.title(unit)
    st.button("⬅️ Back", on_click=lambda: set_page("main_menu"))
    st.button("Logout", on_click=lambda: st.session_state.clear())

    vocab = load_vocab(unit)
    if vocab.empty:
        st.warning("No vocabulary found.")
        return

    mastered = load_student_progress(unit)
    mastered_terms = mastered[mastered.score == 1]["term"].tolist()

    unmastered = vocab[~vocab.term.isin(mastered_terms)]
    if unmastered.empty:
        st.success("🎉 You've mastered all terms in this unit!")
        return

    term_row = unmastered.sample(1).iloc[0]
    term, correct_def = term_row["term"], term_row["definition"]
    st.markdown(f"**🗣 Let's talk about the word: `{term}`**")
    st.info(playful_reminder())

    user_input = st.text_input("What do you think it means?")
    if st.button("Submit"):
        if user_input:
            if user_input.lower() in correct_def.lower():
                st.success(f"✅ That's right! '{term}' means: {correct_def}")
                save_student_progress(unit, term, 1)
            else:
                st.error(f"🤔 Not quite. '{term}' means: {correct_def}")
                st.info(f"{playful_reminder()} Try this: How do you think "{term}" affected history?")
                save_student_progress(unit, term, 0)
            st.rerun()

def set_page(name):
    st.session_state.page = name
    st.rerun()

# Page routing
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
