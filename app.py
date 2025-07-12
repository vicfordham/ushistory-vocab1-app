import streamlit as st
import pandas as pd
import random
import datetime
import os
import openai
from collections import defaultdict

# Set OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai_api_key"]

# Load Vocabulary Data
def load_vocab():
    excel_file = 'vocab.xlsx'
    return {f"Unit {i}": pd.read_excel(excel_file, sheet_name=f"Unit {i}") for i in range(1, 8)}

vocab_data = load_vocab()

# Initialize session state
def init_session():
    if 'user' not in st.session_state:
        st.session_state.user = None
        st.session_state.block = None
        st.session_state.page = "Home"
        st.session_state.chat_progress = defaultdict(lambda: 0)
        st.session_state.unit_chats = defaultdict(list)
        st.session_state.unit_mastery = defaultdict(lambda: defaultdict(bool))
        st.session_state.teacher_logged_in = False
        st.session_state.student_data = {}

init_session()

# Simulate persistent storage
if 'db' not in st.session_state:
    st.session_state.db = {"First": {}, "Second": {}, "Fourth": {}}

# Helper Functions
def save_progress():
    student_key = f"{st.session_state.user['first']} {st.session_state.user['last']}"
    st.session_state.db[st.session_state.block][student_key] = {
        "progress": dict(st.session_state.chat_progress),
        "unit_mastery": dict(st.session_state.unit_mastery),
        "last_login": datetime.datetime.now().strftime("%B %d, %Y - %I:%M %p")
    }

def get_student_key():
    return f"{st.session_state.user['first']} {st.session_state.user['last']}"

def logout():
    st.session_state.user = None
    st.session_state.block = None
    st.session_state.page = "Home"
    st.session_state.teacher_logged_in = False

# Pages

def home_page():
    st.title("Dr. Fordham's History Lab")
    st.subheader("Student Login")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    block = st.selectbox("Block", ["First", "Second", "Fourth"])
    
    if st.button("Student Login"):
        if first and last:
            st.session_state.user = {"first": first, "last": last}
            st.session_state.block = block
            st.session_state.page = "Main Menu"
            save_progress()

    st.subheader("Teacher Login")
    teacher_password = st.text_input("Password", type="password")
    if st.button("Teacher Login") and teacher_password == "letmein":
        st.session_state.teacher_logged_in = True
        st.session_state.page = "Teacher Platform"


def main_menu():
    st.title(f"Welcome, {st.session_state.user['first']} {st.session_state.user['last']}")
    st.write(f"Block: {st.session_state.block}")
    st.progress(sum(st.session_state.chat_progress.values()) / (7 * 100))
    if st.button("Logout"):
        logout()
        return

    for i in range(1, 8):
        if st.button(f"Unit {i} Vocabulary Practice"):
            st.session_state.page = f"Unit {i}"
            return

    if st.button("Milestone Practice"):
        st.session_state.page = "Milestone"
        return

    if st.button("Special Project"):
        st.session_state.page = "Special Project"
        return


def unit_chat(unit):
    st.title(f"{unit} Vocabulary Practice")
    words = vocab_data[unit].to_dict("records")
    mastered = st.session_state.unit_mastery[unit]

    if st.button("Back to Main Menu"):
        st.session_state.page = "Main Menu"
        return

    for word in words:
        if not mastered[word['term']]:
            st.write(f"Define: **{word['term']}**")
            response = st.text_input("Your Response")
            if st.button("Submit"):
                prompt = f"Student's response: '{response}'\nWord: {word['term']}\nDefinition: {word['definition']}\nExample: {word['example']}\nDetermine if the student shows understanding. If partially right, ask a follow-up question to guide them. Otherwise, confirm mastery."
                ai = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
                reply = ai.choices[0].message.content
                st.session_state.unit_chats[unit].append((response, reply))
                st.write(reply)
                if "Correct!" in reply or "Yes," in reply:
                    mastered[word['term']] = True
                    st.session_state.chat_progress[unit] = round((sum(mastered.values()) / len(words)) * 100)
                    save_progress()
            break


def milestone_chat():
    st.title("Milestone Practice")
    words = []
    for unit_df in vocab_data.values():
        words.extend(unit_df.sample(2).to_dict("records"))

    for word in words:
        st.write(f"Define: **{word['term']}**")
        response = st.text_input("Your Response", key=word['term'])
        if st.button(f"Submit {word['term']}"):
            prompt = f"Student's response: '{response}'\nWord: {word['term']}\nDefinition: {word['definition']}\nExample: {word['example']}\nRespond appropriately."
            ai = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
            reply = ai.choices[0].message.content
            st.write(reply)

    if st.button("Back to Main Menu"):
        st.session_state.page = "Main Menu"


def special_project():
    st.title("Special Project - Chat with Benjamin Collins")
    if 'ben_history' not in st.session_state:
        st.session_state.ben_history = []
    st.write("You're now chatting with Ben Collins, a farmer from 1760s Savannah.")
    chat_input = st.text_input("You:")
    if st.button("Send"):
        history = "\n".join(st.session_state.ben_history[-5:])
        prompt = f"You are Benjamin Collins, a 1760s Methodist farmer near Savannah, GA. You are kind, curious, religious, and anti-slavery but don't say so. Chat historically and make up appropriate details about life.\n{history}\nYou: {chat_input}"
        ai = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        reply = ai.choices[0].message.content
        st.session_state.ben_history.append(f"Student: {chat_input}\nBen: {reply}")
        st.write(reply)
    if st.button("Back to Main Menu"):
        st.session_state.page = "Main Menu"


def teacher_platform():
    st.title("Teacher Platform")
    if st.button("Logout"):
        logout()
        return

    st.download_button("Download All Student Data", pd.DataFrame([{
        "Block": blk,
        "Student": name,
        **data["progress"],
        "Last Login": data["last_login"]
    } for blk, students in st.session_state.db.items() for name, data in students.items()]).to_csv(index=False), "all_student_data.csv")

    block = st.selectbox("Select Block", ["First", "Second", "Fourth"])
    students = st.session_state.db[block]
    for name in sorted(students):
        data = students[name]
        st.write(f"**{name}** - Last Login: {data['last_login']}")
        for unit, prog in data["progress"].items():
            new_val = st.slider(f"{unit} Progress", 0, 100, prog)
            students[name]['progress'][unit] = new_val

# Routing
if st.session_state.page == "Home":
    home_page()
elif st.session_state.page == "Main Menu":
    main_menu()
elif st.session_state.page == "Milestone":
    milestone_chat()
elif st.session_state.page == "Special Project":
    special_project()
elif st.session_state.page.startswith("Unit"):
    unit_chat(st.session_state.page)
elif st.session_state.page == "Teacher Platform":
    teacher_platform()
