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

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                 first_name TEXT,
                 last_name TEXT,
                 block TEXT,
                 last_login TEXT,
                 PRIMARY KEY(first_name, last_name, block)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS progress (
                 first_name TEXT,
                 last_name TEXT,
                 block TEXT,
                 unit TEXT,
                 term TEXT,
                 mastered INTEGER,
                 PRIMARY KEY(first_name, last_name, block, unit, term)
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
    c.execute('UPDATE students SET last_login=? WHERE first_name=? AND last_name=? AND block=?', (now, first, last, block))
    conn.commit()
    conn.close()

def get_student_progress(first, last, block):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        'SELECT unit, term, mastered FROM progress WHERE first_name=? AND last_name=? AND block=?',
        conn, params=(first, last, block))
    conn.close()
    return df

# Load vocabulary and define units
vocab = pd.read_excel(VOCAB_PATH, sheet_name=None)
units = list(vocab.keys())

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
        if st.button('Login') and first and last:
            st.session_state.user = {'first': first, 'last': last, 'block': block}
            st.session_state.role = 'student'
            record_login(first, last, block)
            return
    else:
        pwd = st.text_input('Password', type='password')
        if st.button('Login') and pwd == 'letmein':
            st.session_state.role = 'teacher'
            return
        elif st.button('Login'):
            st.error('Incorrect password')

def student_main():
    user = st.session_state.user
    st.sidebar.button('Logout', on_click=logout)
    st.title(f"Welcome, {user['first']} {user['last']} (Block {user['block']})")
    progress = get_student_progress(user['first'], user['last'], user['block'])
    total_terms = sum(len(vocab[u]) for u in units)
    mastered = progress['mastered'].sum()
    overall_pct = int(round(mastered / total_terms * 100)) if total_terms else 0
    st.progress(overall_pct / 100)
    st.caption(f'Overall Progress: {overall_pct}%')

    cols = st.columns(4)
    for i, u in enumerate(units):
        if cols[i % 4].button(u):
            st.session_state.unit = u
            st.session_state.messages = []
            st.session_state.current_index = 0
            return

    st.markdown('---')
    if st.button('Milestone Practice'):
        st.session_state.unit = 'Milestone'
        st.session_state.messages = []
        st.session_state.current_index = 0
        return
    if st.button('Special Project'):
        st.session_state.unit = 'Special'
        st.session_state.messages = []
        st.session_state.current_index = 0
        return

def chat_session():
    unit = st.session_state.unit
    user = st.session_state.user
    st.sidebar.button('Back to Menu', on_click=back_to_menu)

    # Select terms
    if unit in units:
        terms_df = vocab[unit]
    elif unit == 'Milestone':
        recs = []
        for u in units:
            recs += vocab[u].sample(2).to_dict('records')
        terms_df = pd.DataFrame(recs)
    else:
        st.header('Special Project')
        st.info('Benjamin Collins simulation coming soon.')
        return

    # Initialize first question
    if not st.session_state.messages:
        first_term = terms_df.iloc[0]['term']
        st.session_state.messages = [{'role': 'assistant', 'content': f"What do you think '{first_term}' means?"}]
        st.session_state.current_index = 0

    # Display header and progress
    st.header(unit)
    prog = get_student_progress(user['first'], user['last'], user['block'])
    learned = prog[prog['unit'] == unit]['mastered'].sum() if unit in units else 0
    pct = int(round(learned / len(terms_df) * 100)) if len(terms_df) else 0
    st.progress(pct / 100)
    st.caption(f'Progress: {pct}%')

    # Show conversation
    for msg in st.session_state.messages:
        st.chat_message(msg['role']).write(msg['content'])

    # Get user input
    user_response = st.chat_input('Your response...')
    if user_response:
        st.session_state.messages.append({'role': 'user', 'content': user_response})
        current_term = terms_df.iloc[st.session_state.current_index]['term']
        system_msg = {'role': 'system', 'content': 'You are a patient tutor. Provide hints, never full definitions. Guide with follow-ups. Reply "correct" on mastery.'}
        conversation = [system_msg] + st.session_state.messages
        resp = openai.chat.completions.create(model='gpt-4o-mini', messages=conversation)
        reply = resp.choices[0].message.content
        st.session_state.messages.append({'role': 'assistant', 'content': reply})

        if 'correct' in reply.lower() and unit in units:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO progress VALUES (?,?,?,?,?,1)',
                      (user['first'], user['last'], user['block'], unit, current_term))
            conn.commit()
            conn.close()
            st.session_state.current_index += 1
            if st.session_state.current_index < len(terms_df):
                next_term = terms_df.iloc[st.session_state.current_index]['term']
                st.session_state.messages.append({'role': 'assistant', 'content': f"Great! What about '{next_term}'?"})
        return

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
            st.header(f'Block {b}')
            block_students = studs[studs['block'] == b]
            records = []
            for _, r in block_students.iterrows():
                fn, ln = r['first_name'], r['last_name']
                row = {'Last Name': ln, 'First Name': fn, 'Last Login': r['last_login']}
                pr = prog[(prog['first_name'] == fn) & (prog['last_name'] == ln) & (prog['block'] == b)]
                for u in units:
                    row[u] = int(round(pr[pr['unit'] == u]['mastered'].sum() / len(vocab[u]) * 100)) if len(vocab[u]) else 0
                total = sum(len(vocab[u]) for u in units)
                mastered_all = pr['mastered'].sum()
                row['Overall'] = int(round(mastered_all / total * 100)) if total else 0
                records.append(row)
            if records:
                df = pd.DataFrame(records).sort_values('Last Name')
                edited = st.experimental_data_editor(df)
                if st.button(f'Download {b} Data'):
                    writer = pd.ExcelWriter(f'{b}.xlsx', engine='xlsxwriter')
                    edited.to_excel(writer, index=False)
                    writer.close()
                    with open(f'{b}.xlsx', 'rb') as f:
                        st.download_button('Download Excel', f, file_name=f'{b}.xlsx')
            else:
                st.info('No students in this block.')

# Navigation

def logout():
    for k in ['user', 'role', 'unit', 'messages', 'current_index']:
        st.session_state[k] = None


def back_to_menu():
    st.session_state.unit = None
    st.session_state.messages = []
    st.session_state.current_index = 0

# App flow
if st.session_state['role'] is None:
    show_login()
elif st.session_state['role'] == 'student':
    if st.session_state['unit'] is None:
        student_main()
    else:
        chat_session()
elif st.session_state['role'] == 'teacher':
    teacher_main()
