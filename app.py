
import streamlit as st
import pandas as pd
import datetime

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "name" not in st.session_state:
    st.session_state.name = ""
if "block" not in st.session_state:
    st.session_state.block = ""
if "unit" not in st.session_state:
    st.session_state.unit = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0

# Define pages
def login_page():
    st.title("Welcome to U.S. History Vocab Mastery")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Class Period", ["First", "Second", "Fourth"])
    if st.button("Login"):
        if first and last:
            st.session_state.name = f"{first.strip().title()} {last.strip().title()}"
            st.session_state.block = block
            st.session_state.page = "main_menu"
            st.rerun()

def main_menu():
    st.title(f"Welcome, {st.session_state.name}!")
    st.subheader("Choose a Vocabulary Assignment:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Unit 1 Vocabulary"):
            st.session_state.unit = "Unit 1"
            st.session_state.page = "unit_page"
            st.rerun()
    with col2:
        if st.button("Unit 2 Vocabulary"):
            st.session_state.unit = "Unit 2"
            st.session_state.page = "unit_page"
            st.rerun()
    with col3:
        if st.button("Unit 3 Vocabulary"):
            st.session_state.unit = "Unit 3"
            st.session_state.page = "unit_page"
            st.rerun()
    if st.button("Logout"):
        st.session_state.page = "login"
        st.rerun()

def unit_page():
    st.button("⬅ Back", on_click=go_back)
    st.button("🚪 Logout", on_click=logout)
    st.title(f"{st.session_state.unit} Vocabulary")
    try:
        vocab_df = pd.read_excel("vocab.xlsx", sheet_name=st.session_state.unit)
        vocab_list = vocab_df["term"].tolist()
        definitions = dict(zip(vocab_df["term"], vocab_df["definition"]))
    except Exception as e:
        st.error(f"Could not load vocabulary for {st.session_state.unit}: {e}")
        return

    if st.session_state.current_term_index >= len(vocab_list):
        st.success("🎉 You've finished this unit!")
        return

    term = vocab_list[st.session_state.current_term_index]
    correct_def = definitions[term]
    st.markdown(f"**🗣 Let's talk about the word: `{term}`**")
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input("What do you think this word means?")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        if user_input.lower() in correct_def.lower():
            response = f"✅ That's right! '{term}' means: {correct_def}. Great job!"
            st.session_state.current_term_index += 1
            st.session_state.chat_history = []
        else:
            response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"
        st.session_state.chat_history.append(("assistant", response))
        st.rerun()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def go_back():
    st.session_state.page = "main_menu"
    st.rerun()

# Route to correct page
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "unit_page":
    unit_page()
