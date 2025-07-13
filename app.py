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
    c.execute('INSERT OR IGNORE INTO students (first_name, last_name, block, last_login) VALUES (?,?,?,?)',
              (first, last, block, now))
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

# Load vocabulary
vocab = pd.read_excel(VOCAB_PATH, sheet_name=None)
units = [f'Unit {i}' for i in range(1, 8)]

# Session state defaults
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'unit' not in st.session_state:
    st.session_state.unit = None
if 'messages' not in st.session_state or st.session_state.unit is None:
    st.session_state.messages = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# --- Views ---

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
                st.experimental_rerun()
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
            st.experimental_rerun()
    st.markdown('---')
    if st.button('Milestone Practice'):
        st.session_state.unit = 'Milestone'
        st.session_state.messages = []
        st.session_state.current_index = 0
        st.experimental_rerun()
    if st.button('Special Project'):
        st.session_state.unit = 'Special'
        st.session_state.messages = []
        st.session_state.current_index = 0
        st.experimental_rerun()


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
        st.session_state.messages.append({'role': 'assistant', 'content': f"What do you think '{term0}' means?"})

    # Display header and progress
    st.header(unit)
    prog = get_student_progress(user['first'], user['last'], user['block'])
    learned = prog[prog['unit'] == unit]['mastered'].sum() if unit in units else 0
    pct_unit = int(round((learned/len(df_terms))*100)) if df_terms.shape[0] else 0
    st.progress(pct_unit/100)
    st.caption(f'Progress for {unit}: {pct_unit}%')

    # Render chat history
    for msg in st.session_state.messages:
        st.chat_message(msg['role']).write(msg['content'])

    # Accept and process input
    user_input = st.chat_input('Your response...')
    if user_input:
        st.session_state.messages.append({'role': 'user', 'content': user_input})
        term = df_terms.iloc[st.session_state.current_index]['term']
        system = {'role': 'system', 'content': 'You are a patient AI tutor. You may answer questions with hints, never full definitions. Guide student with follow-ups. Respond "correct" on mastery.'}
        payload = [system] + st.session_state.messages
        comp = openai.chat.completions.create(model='gpt-4o-mini', messages=payload)
        reply = comp.choices[0].message.content
        st.session_state.messages.append({'role': 'assistant', 'content': reply})

        # On mastery, record and prepare next
        if 'correct' in reply.lower() and unit in units:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO progress (first_name, last_name, block, unit, term, mastered) VALUES (?,?,?,?,?,1)',
                      (user['first'], user['last'], user['block'], unit, term))
            conn.commit()
            conn.close()
            st.session_state.current_index += 1
            if st.session_state.current_index < len(df_terms):
                nxt = df_terms.iloc[st.session_state.current_index]['term']
                st.session_state.messages.append({'role': 'assistant', 'content': f"Great! What about '{nxt}'?"})
            else:
                st.session_state.messages.append({'role': 'assistant', 'content': f"Congratulations! You've completed {unit}!"})
        st.experimental_rerun()


def teacher_main():
    st.title('Teacher Dashboard')
    st.sidebar.button('Logout', on_click=logout)

    tabs = st.tabs(['First', 'Second', 'Fourth'])
    conn = sqlite3.connect(DB_PATH)
    studs = pd.read_sql_query('SELECT * FROM students', conn)
    prog = pd.read_sql_query('SELECT * FROM progress', conn)
    conn.close()

    for i, b in enumerate(['First', 'Second', 'Fourth']):
        with tabs[i]:
            st.header(f'Block {b} Gradebook')
            blk = studs[studs['block'] == b]
            records = []
            for _, r in blk.iterrows():
                fn, ln = r['first_name'], r['last_name']
                row = {'Last Name': ln, 'First Name': fn, 'Last Login': r['last_login']}
                pr = prog[(prog['first_name'] == fn) & (prog['last_name'] == ln) & (prog['block'] == b)]
                for u in units:
                    row[u] = int(round(pr[pr['unit'] == u]['mastered'].sum() / len(vocab[u]) * 100)) if len(vocab[u]) else 0
                total_terms = sum(len(vocab[u]) for u in units)
                total_mastered = pr['mastered'].sum()
                row['Overall'] = int(round(total_mastered / total_terms * 100)) if total_terms else 0
                records.append(row)
            if records:
                df = pd.DataFrame(records).sort_values('Last Name')
                edited = st.experimental_data_editor(df)
                if st.button(f'Download {b} Data'):
                    writer = pd.ExcelWriter(f'{b}_data.xlsx', engine='xlsxwriter')
                    edited.to_excel(writer, index=False)
                    writer.close()
                    with open(f'{b}_data.xlsx', 'rb') as f:
                        st.download_button('Download Excel', f, file_name=f'{b}_data.xlsx')
            else:
                st.info('No students in this block yet.')


def logout():
    for key in ['user', 'role', 'unit', 'messages', 'current_index']:
        st.session_state[key] = None
    st.experimental_rerun()


def back_to_menu():
    st.session_state.unit = None
    st.session_state.messages = []
    st.session_state.current_index = 0
    st.experimental_rerun()

# App control flow
if st.session_state['role'] is None:
    show_login()
elif st.session_state['role'] == 'student':
    if st.session_state['unit'] is None:
        student_main()
    else:
        chat_session(st.session_state['unit'])
elif st.session_state['role'] == 'teacher':
    teacher_main()
