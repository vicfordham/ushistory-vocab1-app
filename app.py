
import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from datetime import datetime

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load or initialize the student mastery database
def load_database():
    try:
        return pd.read_csv("mastery_data.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["student", "block", "term", "mastered", "timestamp", "last_login"])

def save_database(df):
    df.to_csv("mastery_data.csv", index=False)

@st.cache_data
def load_vocab():
    return pd.read_csv("vocab.csv")

# ---------------- APP START ----------------
st.set_page_config(page_title="Dr. Fordham's History Lab", layout="centered")
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        background-color: #4b6cb7;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: bold;
    }
    .stTextInput>div>input, .stSelectbox>div>div {
        border-radius: 8px;
    }
    .stProgress>div>div>div {
        background-color: #4b6cb7;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📘 Dr. Fordham's U.S. History Lab")
st.markdown("Welcome to your personal mastery-based vocabulary coach. Let's build confidence one word at a time. 💪")

# Sidebar for teacher login
st.sidebar.title("👨‍🏫 Teacher Login")
admin_pw = st.sidebar.text_input("Enter teacher password", type="password")

if admin_pw == "letmein":
    if st.sidebar.button("🚪 Logout"):
        st.rerun()

    st.sidebar.success("Access granted.")
    st.subheader("📊 Teacher Dashboard")
    data = load_database()
    if data.empty:
        st.info("No student data yet.")
    else:
        vocab_total = len(load_vocab())
        mastery_summary = (
            data[data["mastered"] == True]
            .groupby(["student", "block"])
            .agg(Mastered_Terms=("term", "count"), Last_Login=("last_login", "max"))
            .reset_index()
        )
        mastery_summary["Total Terms"] = vocab_total
        mastery_summary["Grade (%)"] = (mastery_summary["Mastered_Terms"] / vocab_total * 100).round(1)
        st.dataframe(mastery_summary)
    st.stop()

# ---------------- STUDENT MODE ----------------
if "student_name" not in st.session_state:
    st.subheader("🔐 Student Login")
    with st.form("name_form"):
        first = st.text_input("First Name")
        last = st.text_input("Last Name")
        block = st.selectbox("Which Block are you in?", ["First", "Second", "Fourth"])
        submitted = st.form_submit_button("Start")
        if submitted and first and last and block:
            full_name = f"{first.strip()} {last.strip()}"
            st.session_state.student_name = full_name
            st.session_state.block = block
            st.session_state.last_login = datetime.now().isoformat()
            st.rerun()
    st.stop()

name = st.session_state.student_name
block = st.session_state.block
last_login = st.session_state.last_login

vocab = load_vocab()
mastery_data = load_database()

# Update last login record for student (only on load)
existing = (mastery_data["student"] == name) & (mastery_data["term"].isnull())
if not mastery_data[existing].empty:
    mastery_data.loc[existing, "last_login"] = last_login
else:
    mastery_data = pd.concat([mastery_data, pd.DataFrame([{
        "student": name,
        "block": block,
        "term": None,
        "mastered": None,
        "timestamp": None,
        "last_login": last_login
    }])], ignore_index=True)
save_database(mastery_data)

# Filter out terms already mastered by this student
mastered_terms = mastery_data[(mastery_data["student"] == name) & (mastery_data["mastered"] == True)]["term"].tolist()
remaining_vocab = vocab[~vocab["term"].isin(mastered_terms)].reset_index(drop=True)
total_vocab = len(vocab)
mastered_count = len(mastered_terms)
progress_pct = (mastered_count / total_vocab) * 100

# Show progress bar
st.sidebar.markdown(f"### 📈 Progress for {name}")
st.sidebar.progress(int(progress_pct))
st.sidebar.markdown(f"**{mastered_count} / {total_vocab}** terms mastered ({int(progress_pct)}%)")
st.sidebar.markdown(f"**Block:** {block}")

if "index" not in st.session_state:
    st.session_state.index = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.index < len(remaining_vocab):
    row = remaining_vocab.iloc[st.session_state.index]
    term = row["term"]
    definition = row["definition"]
    example = row["example_usage"]

    if not st.session_state.messages:
        system_msg = f"Let's talk about the word **{term}**. What do you think it means?"
        st.session_state.messages.append({"role": "assistant", "content": system_msg})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Type your answer...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        messages = [{"role": "system", "content": (
            f"You are a warm, encouraging U.S. History tutor. You're currently helping a student understand the vocabulary term: '{term}'.\n"
            f"The correct definition is: '{definition}'.\n"
            f"An example usage is: '{example}'.\n\n"
            "Respond conversationally and directly to the student. After each student reply, check if they’ve demonstrated clear and correct understanding of the term.\n\n"
            "- ✅ If they have: Affirm them warmly and say 'you got it! Let’s move on.'\n"
            "- 🤔 If their answer is close: Offer encouraging feedback and ask ONE clear follow-up question to deepen understanding.\n"
            "- ❌ If their answer is incorrect or vague: briefly explain the concept again and ask a clarifying question.\n\n"
            "Never ask more than one question at a time, and don’t keep them in a loop if they’ve shown clear understanding."
        )}]
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )

        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

        with st.chat_message("assistant"):
            st.markdown(reply)

        if "you got it" in reply.lower() or "let’s move on" in reply.lower():
            new_row = pd.DataFrame([{
                "student": name,
                "block": block,
                "term": term,
                "mastered": True,
                "timestamp": datetime.now().isoformat(),
                "last_login": last_login
            }])
            mastery_data = pd.concat([mastery_data, new_row], ignore_index=True)
            save_database(mastery_data)
            st.session_state.index += 1
            st.session_state.messages = []
            st.rerun()
else:
    st.success("🎉 You've completed all the vocabulary terms!")
    st.balloons()
