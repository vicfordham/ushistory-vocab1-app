
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

if st.session_state.index < len(vocab):
    row = vocab.iloc[st.session_state.index]
    term = row["term"]
    correct_definition = row["definition"]
    example = row["example_usage"]

    st.header(f"Term: {term}")
    answer = st.text_input("What does this mean?", key="answer")

    if st.button("Submit"):
        if answer.lower() in correct_definition.lower():
            st.success("✅ Correct!")
            st.session_state.mastered.add(term)
            st.session_state.index += 1
            st.experimental_rerun()
        else:
            st.error("❌ Not quite.")
            st.markdown(f"**Correct Definition:** {correct_definition}")
            st.markdown(f"**Example:** {example}")

            with st.spinner("Explaining with AI..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You're a U.S. History tutor for middle and high school students."},
                        {"role": "user", "content": f"Explain the term '{term}' clearly, since the student got it wrong. Use examples and simple language."}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                explanation = response.choices[0].message.content
                st.info(f"💡 AI Explanation: {explanation}")
else:
    st.balloons()
    st.success("🎉 You've completed the vocabulary list!")
