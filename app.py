
import streamlit as st
import pandas as pd
from openai import OpenAI
import os

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use updated cache syntax
@st.cache_data
def load_vocab():
    return pd.read_csv("vocab.csv")

vocab = load_vocab()

st.title("📘 U.S. History Vocab Mastery Tool")

if "index" not in st.session_state:
    st.session_state.index = 0
if "mastered" not in st.session_state:
    st.session_state.mastered = set()
if "awaiting_retry" not in st.session_state:
    st.session_state.awaiting_retry = False

if st.session_state.index < len(vocab):
    row = vocab.iloc[st.session_state.index]
    term = row["term"]
    correct_definition = row["definition"]
    example = row["example_usage"]

    st.header(f"Term: {term}")

    if not st.session_state.awaiting_retry:
        answer = st.text_input("What does this mean?", key=f"answer_{st.session_state.index}")

        if st.button("Submit"):
            with st.spinner("Evaluating your response..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You're a U.S. History teacher evaluating student vocabulary answers."},
                        {"role": "user", "content": f"The student was asked to define '{term}'.

Student answer: '{answer}'

Correct definition: '{correct_definition}'

Evaluate their answer. Is it correct, close, or incorrect? Give brief feedback. If it’s close, ask a follow-up question to deepen their understanding. If it's fully correct, say so and tell them they can move on."}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )

                feedback = response.choices[0].message.content
                st.session_state.last_feedback = feedback

                if "fully correct" in feedback.lower() or "you can move on" in feedback.lower():
                    st.success("✅ Great job! Moving on...")
                    st.session_state.mastered.add(term)
                    st.session_state.index += 1
                    st.session_state.awaiting_retry = False
                    st.experimental_rerun()
                else:
                    st.info(f"💬 {feedback}")
                    st.session_state.awaiting_retry = True
    else:
        retry_input = st.text_input("Your follow-up answer:", key=f"retry_{st.session_state.index}")

        if st.button("Try Again"):
            with st.spinner("Re-evaluating your follow-up..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You're a U.S. History teacher evaluating student vocabulary answers."},
                        {"role": "user", "content": f"The student was asked to define '{term}'.

Their revised answer is: '{retry_input}'

Correct definition: '{correct_definition}'

Evaluate their revised answer. If correct, tell them they got it and can move on. If still not fully correct, explain clearly and ask one final clarifying question."}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                feedback = response.choices[0].message.content
                st.info(f"💬 {feedback}")

                if "fully correct" in feedback.lower() or "you can move on" in feedback.lower():
                    st.success("✅ Got it! Moving on...")
                    st.session_state.mastered.add(term)
                    st.session_state.index += 1
                    st.session_state.awaiting_retry = False
                    st.experimental_rerun()
else:
    st.balloons()
    st.success("🎉 You've completed the vocabulary list!")
