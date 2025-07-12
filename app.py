
import streamlit as st
import pandas as pd
from datetime import datetime

# Custom CSS for youthful styling
st.markdown("""
    <style>
        .main {
            background-color: #f0f4f8;
        }
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

st.markdown("<div class='title'>📚 Dr. Fordham's U.S. History Lab</div>", unsafe_allow_html=True)
st.markdown("---")

# Session state for login
if "student_name" not in st.session_state:
    st.session_state.student_name = None

# Login Page
if not st.session_state.student_name:
    st.subheader("📝 Student Login")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    block = st.selectbox("Select Your Block", ["First", "Second", "Fourth"])
    if st.button("Enter"):
        if first_name and last_name:
            st.session_state.student_name = f"{first_name.strip().title()} {last_name.strip().title()}"
            st.session_state.block = block
            st.session_state.login_time = datetime.now().isoformat()
        else:
            st.warning("Please enter both first and last names.")
    st.stop()

# Unit Selection Page
st.success(f"Welcome, {st.session_state.student_name} ({st.session_state.block} Block)!")
st.subheader("📘 Choose a Vocabulary Unit to Begin")

cols = st.columns(4)
units = [f"Unit {i}" for i in range(1, 8)]
unit_selected = None

for i, unit in enumerate(units):
    if cols[i % 4].button(unit):
        st.session_state.unit_selected = unit

# Quiz Button
if st.button("🎯 Final Quiz (50 Random Words)"):
    st.info("Quiz mode coming soon!")


# Route to unit page if selected
if "unit_selected" in st.session_state and st.session_state.unit_selected:
    if st.button("🔙 Back to Unit Menu"):
        del st.session_state.unit_selected
        st.experimental_rerun()

    if st.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

    unit = st.session_state.unit_selected
    st.markdown(f"### ✏️ {unit} Vocabulary")
    if unit == "Unit 1":

if unit_selected == "Unit 1":
    st.markdown("### ✏️ Unit 1 Vocabulary")

    # Load vocab for Unit 1
    vocab_df = pd.read_csv("vocab.csv")
    vocab_list = vocab_df["term"].tolist()
    if "current_term_index" not in st.session_state:
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []

    if st.session_state.current_term_index < len(vocab_list):
        term = vocab_list[st.session_state.current_term_index]
        st.markdown(f"**🗣 Let's talk about the word: `{term}`**")

        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(msg)

        user_input = st.chat_input("What do you think it means?")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.chat_history.append(("user", user_input))

            # AI Evaluation (simple rule-based for now)
            correct_def = vocab_df[vocab_df["term"] == term]["definition"].values[0]
            if user_input.lower() in correct_def.lower():
                response = f"✅ That's correct! '{term}' means: {correct_def}"
                st.session_state.current_term_index += 1
                st.session_state.chat_history.append(("assistant", response))
                with st.chat_message("assistant"):
                    st.markdown(response)
            else:
                response = f"🤔 Not quite. '{term}' actually means: {correct_def}. Let's talk more—can you explain how this applies to history?"
                st.session_state.chat_history.append(("assistant", response))
                with st.chat_message("assistant"):
                    st.markdown(response)
    else:
        st.balloons()
        st.success("🎉 You've finished all Unit 1 vocabulary!")

