import streamlit as st
import pandas as pd
import sqlite3
import os
import random
from datetime import datetime
import openai

# Configuration
st.set_page_config(page_title="Dr. Fordham's History Lab", layout='wide')
openai.api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", ""))
DB_PATH = 'student_progress.db'
VOCAB_PATH = 'vocab.xlsx'

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    first_name TEXT,
                    last_name TEXT,
                    block TEXT,
                    last_login TEXT,
                    PRIMARY KEY (first_name, last_name, block)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS progress (
                    first_name TEXT,
                    last_name TEXT,
                    block TEXT,
                    unit TEXT,
                    term TEXT,
                    mastered INTEGER,
                    PRIMARY KEY (first_name, last_name, block, unit, term)
                )''')
    conn.commit()
    conn.close()
init_db()

# Helpers

def record_login(first, last, block):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%B %d, %Y - %I:%M %p')
    c.execute('INSERT OR IGNORE INTO students VALUES (?,?,?,?)', (first, last, block, now))
    c.execute('UPDATE students SET last_login=? WHERE first_name=? AND last_name=? AND block=?',
              (now, first, last, block))
    conn.commit()
    conn.close()

def get_student_progress(first, last, block):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        'SELECT unit, term, mastered FROM progress WHERE first_name=? AND last_name=? AND block=?',
        conn, params=(first, last, block))
    conn.close()
    return df

# Load vocab
vocab = pd.read_excel(VOCAB_PATH, sheet_name=None)
units = [f'Unit {i}' for i in range(1, 8)]

# Initialize session state
for key, default in {'user': None, 'role': None, 'unit': None, 'messages': [], 'current_index': 0}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Views

def show_login():
    st.title("Dr. Fordham's History Lab")
    role = st.radio("Login as", ['Student', 'Teacher'], horizontal=True)
    if role == 'Student':
        first = st.text_input('First Name')
        last = st.text_input('Last Name')
        block = st.selectbox('Block', ['First', 'Second', 'Fourth'])
        if st.button('Login as Student') and first and last:
            st.session_state.user = {'first': first, 'last': last, 'block': block}
            st.session_state.role = 'student'
            record_login(first, last, block)
    else:
        pwd = st.text_input('Password', type='password')
        if st.button('Login as Teacher'):
            if pwd == 'letmein':
                st.session_state.role = 'teacher'
            else:
                st.error('Incorrect password')


def student_main():
    user = st.session_state.user
    st.sidebar.button('Logout', on_click=logout)
    st.title(f"Welcome, {user['first']} {user['last']} (Block {user['block']})")

    prog = get_student_progress(user['first'], user['last'], user['block'])
    total = sum(vocab[u].shape[0] for u in units)
    mastered = prog['mastered'].sum()
    pct = int(round((mastered/total)*100)) if total else 0
    st.progress(pct/100)
    st.caption(f'Overall Progress: {pct}%')

    cols = st.columns(4)
    for i, u in enumerate(units):
        if cols[i % 4].button(u):
            st.session_state.unit = u
            st.session_state.messages = []
            st.session_state.current_index = 0
    st.markdown('---')
    if st.button('Milestone Practice'):
        st.session_state.unit = 'Milestone'
        st.session_state.messages = []
        st.session_state.current_index = 0
    if st.button('Special Project'):
        st.session_state.unit = 'Special'
        st.session_state.messages = []
        st.session_state.current_index = 0


def chat_session(unit):
    user = st.session_state.user
    st.sidebar.button('Back to Menu', on_click=back_to_menu)

    # Prepare term list
    if unit in units:
        df_terms = vocab[unit]
    elif unit == 'Milestone':
        recs = []
        for u in units:
            recs += vocab[u].sample(2).to_dict('records')
        df_terms = pd.DataFrame(recs)
    else:
        st.header('Special Project')
        st.info('Benjamin Collins simulation coming soon.')
        return

    # Initialize first question
    if not st.session_state.messages:
        term0 = df_terms.iloc[0]['term']
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"What do you think '{term0}' means?"
        })

    # Display header and progress
    st.header(unit)
    prog = get_student_progress(user['first'], user['last'], user['block'])
    learned = prog[prog['unit'] == unit]['mastered'].sum() if unit in units else 0
    pct_unit = int(round((learned/len(df_terms))*100)) if df_terms.shape[0] else 0
    st.progress(pct_unit/100)
    st.caption(f'Progress for {unit}: {pct_unit}%')

    # Render chat
    for msg in st.session_state.messages:
        st.chat_message(msg['role']).write(msg['content'])

    # Accept and process input
    user_input = st.chat_input('Your response...')
    if user_input:
        st.session_state.messages.append({'role': 'user', 'content': user_input})
        term = df_terms.iloc[st.session_state.current_index]['term']
        system = {'role': 'system', 'content': 'You are a patient AI tutor. You may answer student questions with hints or clarifications, but never provide the full definition outright. Guide the student with follow-up questions toward understanding. Recognize partial correctness and, when the student clearly demonstrates mastery, respond exactly with "correct" to move on.'}
        payload = [system] + st.session_state.messages
        comp = openai.chat.completions.create(model='gpt-4o-mini', messages=payload)
        reply = comp.choices[0].message.content
        st.session_state.messages.append({'role': 'assistant', 'content': reply})

        # On mastery, record and queue next
        if 'correct' in reply.lower() and unit in units:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO progress VALUES (?,?,?,?,?,1)',
                      (user['first'], user['last'], user['block'], unit, term))
            conn.commit()
            conn.close()
            st.session_state.current_index += 1
            if st.session_state.current_index < len(df_terms):
                nxt = df_terms.iloc[st.session_state.current_index]['term']
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': f"Great! What about '{nxt}'?"
                })
            else:
                st.session_state.messages.append({'role': 'assistant', 'content': f"Congratulations! You've completed {unit}!"})
        # Force re-render so the assistant's reply appears immediately
        st.experimental_rerun()
