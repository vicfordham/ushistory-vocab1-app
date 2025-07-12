
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
        return pd.DataFrame(columns=["student", "term", "mastered", "timestamp"])

def save_database(df):
    df.to_csv("mastery_data.csv", index=False)

@st.cache_data
def load_vocab():
    return pd.read_csv("vocab.csv")

# ---------------- APP START ----------------
st.set_page_config(page_title="History Vocab Tutor", layout="centered")
st.title("📘 U.S. History Vocabulary Tutor")

# Sidebar for teacher login
st.sidebar.title("Teacher Login")
admin_pw = st.sidebar.text_input("Enter teacher password", type="password")
if admin_pw == "letmein":
    st.sidebar.success("Access granted.")
    st.subheader("📊 Teacher Dashboard")
    data = load_database()
    if data.empty:
        st.info("No student data yet.")
    else:
        summary = data[data["mastered"] == True].groupby("student")["term"].count().reset_index()
        total_terms = len(load_vocab())
        summary["Total Terms"] = total_terms
        summary["Grade (%)"] = (summary["term"] / total_terms * 100).round(1)
        summary.rename(columns={"term": "Mastered Terms"}, inplace=True)
        st.dataframe(summary)
    st.stop()

# ---------------- STUDENT MODE ----------------
if "student_name" not in st.session_state:
    name = st.text_input("Enter your name to begin:")
    if name:
        st.session_state.student_name = name.strip()
        st.rerun()
    st.stop()

name = st.session_state.student_name
vocab = load_vocab()

if "index" not in st.session_state:
    st.session_state.index = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.index < len(vocab):
    row = vocab.iloc[st.session_state.index]
    term = row["term"]
    definition = row["definition"]
    example = row["example_usage"]

    # Start new term if chat empty
    if not st.session_state.messages:
        system_msg = f"Let's talk about the word **{term}**. What do you think it means?"
        st.session_state.messages.append({"role": "assistant", "content": system_msg})

    # Display chat history using chat UI
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input at bottom
    prompt = st.chat_input("Type your answer...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Compose prompt for OpenAI
        messages = [{"role": "system", "content": (
            "You are a friendly, encouraging U.S. History tutor. Speak directly to the student using 'you'. "
            "Use the student's teacher's name frequently ('Dr. Fordham') to make the conversation more personal. Remind them frequently that Dr. Fordham can see all of their activity and will be giving them a grade for their progress and how serious they take the assignment. Remind them: 'Dr. Fordham knows all!' and frequently make jokes about his omniscience! "
            "Use a conversational tone. The current vocabulary term is: '" + term + "'. "
            "The correct definition is: '" + definition + "'. Example usage: '" + example + "'. "
            "If the student gives an incomplete, vague, or partially correct answer, give feedback and ask a follow-up question. Ask as many follow-up questions as necessary to get the student to a full understanding. "
            "Only say something like 'you got it!' or 'let’s move on' if the student clearly demonstrates full understanding. "
            "Your goal is to help the student fully grasp the term through a natural back-and-forth chat."
        )}]
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )

        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

        with st.chat_message("assistant"):
            st.markdown(reply)

        # Advance if mastered
        if "you got it" in reply.lower() or "let's move on" in reply.lower():
            mastery_data = load_database()
            mastery_data = mastery_data.append({
                "student": name,
                "term": term,
                "mastered": True,
                "timestamp": datetime.now().isoformat()
            }, ignore_index=True)
            save_database(mastery_data)
            st.session_state.index += 1
            st.session_state.messages = []
            st.rerun()
else:
    st.success("🎉 You've completed all the vocabulary terms!")
    st.balloons()
