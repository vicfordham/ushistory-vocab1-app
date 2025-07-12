
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os

# Constants
UNITS = [f"Unit {i}" for i in range(1, 8)]
FINAL_UNIT = "Milestone Practice"
ALL_UNITS = UNITS + [FINAL_UNIT]
VOCAB_FILE = "vocab.xlsx"
TEACHER_PASSWORD = "fordhamsecure"

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "student" not in st.session_state:
    st.session_state.student = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0

# Helper Functions
def load_vocab(unit):
    try:
        if unit == FINAL_UNIT:
            dfs = [pd.read_excel(VOCAB_FILE, sheet_name=f"Unit {i}") for i in range(1, 8)]
            combined = pd.concat(dfs)
            return combined.sample(n=50, replace=True).reset_index(drop=True)
        else:
            return pd.read_excel(VOCAB_FILE, sheet_name=unit)
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit}: {e}")
        return pd.DataFrame()

def update_gradebook(student, unit, correct, total):
    block = student["block"]
    file = f"gradebook_block_{block}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
    else:
        df = pd.DataFrame()

    full_name = f"{student['last']}, {student['first']}"
    progress = round((correct / total) * 100 + 0.5)  # round up if >= .5
    last_login = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    if full_name in df["name"].values:
        df.loc[df["name"] == full_name, unit] = progress
        df.loc[df["name"] == full_name, "Last Login"] = last_login
    else:
        row = {
            "name": full_name,
            unit: progress,
            "Last Login": last_login
        }
        for u in UNITS:
            if u != unit:
                row[u] = ""
        row["Milestone Practice"] = "" if unit != FINAL_UNIT else progress
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    df.to_csv(file, index=False)

# Pages
def home_page():
    st.title("📘 U.S. History Vocab Mastery Tool")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Student Login")
        first = st.text_input("First Name")
        last = st.text_input("Last Name")
        block = st.selectbox("Block", ["First", "Second", "Fourth"])
        if st.button("Login"):
            if first and last:
                st.session_state.student = {
                    "first": first.strip().title(),
                    "last": last.strip().title(),
                    "block": block.lower()
                }
                st.session_state.page = "menu"
    with col2:
        st.subheader("Teacher Login")
        pw = st.text_input("Password", type="password")
        if st.button("Enter Teacher Dashboard"):
            if pw == TEACHER_PASSWORD:
                st.session_state.page = "teacher"

def student_menu():
    st.title(f"Welcome, {st.session_state.student['first']} {st.session_state.student['last']} 👋")
    st.subheader("Select a Unit to Begin:")
    cols = st.columns(4)
    for i, unit in enumerate(ALL_UNITS):
        with cols[i % 4]:
            if st.button(unit):
                st.session_state.selected_unit = unit
                st.session_state.page = "unit"
                st.session_state.current_term_index = 0
                st.session_state.chat_history = []

    # Show overall progress
    block = st.session_state.student["block"]
    full_name = f"{st.session_state.student['last']}, {st.session_state.student['first']}"
    file = f"gradebook_block_{block}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        row = df[df["name"] == full_name]
        if not row.empty:
            scores = row[UNITS].fillna(0).astype(float)
            total = scores.sum(axis=1).values[0]
            progress = round(total / (len(UNITS) * 100) * 100 + 0.5)
            st.progress(progress / 100, text=f"Overall Progress: {progress}%")

    if st.button("Logout"):
        st.session_state.page = "home"
        st.session_state.student = {}

def unit_page():
    unit = st.session_state.selected_unit
    df = load_vocab(unit)
    if df.empty:
        return
    vocab_list = df.to_dict("records")

    st.button("⬅️ Back to Menu", on_click=lambda: st.session_state.update({"page": "menu"}))
    st.button("Logout", on_click=lambda: st.session_state.update({"page": "home", "student": {}}))

    total = len(vocab_list)
    correct = st.session_state.get("correct", 0)

    st.progress(correct / total, text=f"{correct} of {total} Mastered")

    if st.session_state.current_term_index < total:
        current = vocab_list[st.session_state.current_term_index]
        term = current["term"]
        correct_def = current["definition"]

        if st.session_state.chat_history:
            for role, msg in st.session_state.chat_history:
                with st.chat_message(role):
                    st.markdown(msg)

        with st.chat_message("assistant"):
            st.markdown(f"**🗣 Let's talk about the word: `{term}`**")

        user_input = st.chat_input("What do you think it means?")
        if user_input:
            st.session_state.chat_history.append(("user", user_input))
            if user_input.lower().strip() in correct_def.lower():
                response = f"✅ That's right! '{term}' means: {correct_def}"
                st.session_state.correct = st.session_state.get("correct", 0) + 1
                st.session_state.current_term_index += 1
            else:
                response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"

            st.session_state.chat_history.append(("assistant", response))
            with st.chat_message("assistant"):
                st.markdown(response)
    else:
        st.success("🎉 You've completed this unit!")
        update_gradebook(st.session_state.student, unit, st.session_state.get("correct", 0), total)

def teacher_dashboard():
    st.title("📊 Teacher Dashboard")
    tabs = st.tabs(["First Block", "Second Block", "Fourth Block"])
    for i, blk in enumerate(["first", "second", "fourth"]):
        file = f"gradebook_block_{blk}.csv"
        if os.path.exists(file):
            df = pd.read_csv(file)
            cols = ["name"] + UNITS + [FINAL_UNIT, "Last Login"]
            df = df[cols]
            df = df.sort_values(by="name")
            tabs[i].dataframe(df)
            tabs[i].download_button("Download", df.to_csv(index=False), file_name=f"{blk}_block_gradebook.csv")
        else:
            tabs[i].warning("No data available yet.")

    if st.button("Logout"):
        st.session_state.page = "home"

# Page Router
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "menu":
    student_menu()
elif st.session_state.page == "unit":
    unit_page()
elif st.session_state.page == "teacher":
    teacher_dashboard()
