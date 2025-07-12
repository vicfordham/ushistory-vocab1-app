
import streamlit as st
import pandas as pd
import datetime
import os

# Set page config
st.set_page_config(page_title="U.S. History Vocabulary Mastery", layout="wide")

# Session state defaults
if "page" not in st.session_state:
    st.session_state.page = "login"
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "block" not in st.session_state:
    st.session_state.block = ""
if "unit" not in st.session_state:
    st.session_state.unit = ""
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load vocabulary from Excel
def load_vocab(unit_sheet):
    try:
        df = pd.read_excel("vocab.xlsx", sheet_name=unit_sheet, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Could not load vocabulary for {unit_sheet}: {e}")
        return None

# Save student progress
def save_progress(student_name, block, unit, index):
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    progress_path = "student_progress.csv"
    if os.path.exists(progress_path):
        df = pd.read_csv(progress_path)
    else:
        df = pd.DataFrame(columns=["student_name", "block", "unit", "term_index", "last_login"])
    df = df[df["student_name"].str.lower() != student_name.lower()]
    df.loc[len(df.index)] = [student_name, block, unit, index, today]
    df.to_csv(progress_path, index=False)

# Main menu page
def main_menu():
    st.title(f"Welcome, {st.session_state.student_name} 👋")
    st.subheader("Select a Vocabulary Assignment:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Unit 1 Vocabulary"):
            st.session_state.unit = "Unit 1"
            st.session_state.page = "unit_page"
            st.experimental_rerun()
    with col2:
        if st.button("Unit 2 Vocabulary"):
            st.session_state.unit = "Unit 2"
            st.session_state.page = "unit_page"
            st.experimental_rerun()
    with col3:
        if st.button("Unit 3 Vocabulary"):
            st.session_state.unit = "Unit 3"
            st.session_state.page = "unit_page"
            st.experimental_rerun()
    st.button("Log out", on_click=logout)

# Logout function
def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.page = "login"
    st.experimental_rerun()

# Unit interaction page
def unit_page():
    unit = st.session_state.unit
    df = load_vocab(unit)
    if df is None or df.empty:
        st.warning("No vocabulary found.")
        return

    vocab_list = df.to_dict("records")
    index = st.session_state.current_term_index
    if index >= len(vocab_list):
        st.success("🎉 You've completed this unit!")
        if st.button("Back to Menu"):
            st.session_state.page = "main_menu"
            st.experimental_rerun()
        return

    term = vocab_list[index]["term"]
    correct_def = vocab_list[index]["definition"]

    st.markdown(f"### 📘 Let's talk about: `{term}`")

    for speaker, msg in st.session_state.chat_history:
        with st.chat_message(speaker):
            st.markdown(msg)

    user_input = st.chat_input("What does this word mean?")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        if user_input.lower() in correct_def.lower():
            response = f"✅ That's right! '{term}' means: {correct_def}"
            st.session_state.current_term_index += 1
            save_progress(st.session_state.student_name, st.session_state.block, unit, st.session_state.current_term_index)
        else:
            response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's keep going and talk more—can you explain why this matters in U.S. History?"

        st.session_state.chat_history.append(("assistant", response))
        st.experimental_rerun()

    st.button("⬅️ Back to Menu", on_click=lambda: go_to_menu())
    st.button("🚪 Log out", on_click=logout)

def go_to_menu():
    st.session_state.page = "main_menu"
    st.session_state.current_term_index = 0
    st.session_state.chat_history = []
    st.experimental_rerun()

# Login page
def login_page():
    st.title("🔑 Student Login")
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    block = st.selectbox("Class Block", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if fname and lname and block:
            full_name = f"{fname.strip().title()} {lname.strip().title()}"
            st.session_state.student_name = full_name
            st.session_state.block = block
            st.session_state.page = "main_menu"
            st.experimental_rerun()
        else:
            st.warning("Please fill in all fields.")

# Page router
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
