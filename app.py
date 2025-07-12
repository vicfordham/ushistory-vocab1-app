import streamlit as st
import pandas as pd
import sqlite3
import os
import random
from datetime import datetime
import openai

# --- Configuration ---
st.set_page_config(page_title="Dr. Fordham's History Lab", layout='wide')
openai.api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", ""))
DB_PATH = 'student_progress.db'
VOCAB_PATH = 'vocab.xlsx'

# --- Database Setup ---
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

# --- Helper Functions ---
def record_login(first, last, block):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%B %d, %Y - %I:%M %p')
    c.execute('INSERT OR IGNORE INTO students (first_name, last_name, block, last_login) VALUES (?, ?, ?, ?)',
              (first, last, block, now))
    c.execute('UPDATE students SET last_login = ? WHERE first_name = ? AND last_name = ? AND block = ?',
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

# --- Session State ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None

# --- Authentication ---
def show_login():
    st.title("Dr. Fordham's History Lab")
    role = st.radio("Login as", ['Student', 'Teacher'], horizontal=True)
    if role == 'Student':
        first = st.text_input('First Name')
        last = st.text_input('Last Name')
        block = st.selectbox('Block', ['First', 'Second', 'Fourth'])
        if st.button('Login as Student'):
            if first and last:
                st.session_state.user = {'first': first, 'last': last, 'block': block}
                st.session_state.role = 'student'
                record_login(first, last, block)
                st.experimental_rerun()
    else:
        pwd = st.text_input('Password', type='password')
        if st.button('Login as Teacher'):
            if pwd == 'letmein':
                st.session_state.role = 'teacher'
                st.experimental_rerun()
            else:
                st.error('Incorrect password')

# --- Student View ---
def student_main():
    user = st.session_state.user
    st.sidebar.button('Logout', on_click=logout)
    st.title(f"Welcome, {user['first']} {user['last']} (Block {user['block']})")

    prog_df = get_student_progress(user['first'], user['last'], user['block'])
    total = sum(vocab[unit].shape[0] for unit in units)
    mastered = prog_df['mastered'].sum()
    overall_pct = int(round((mastered/total)*100)) if total>0 else 0
    st.progress(overall_pct / 100)
    st.caption(f'Overall Progress: {overall_pct}%')

    cols = st.columns(4)
    for idx, unit in enumerate(units):
        if cols[idx%4].button(unit):
            st.session_state.unit = unit
            st.experimental_rerun()

    st.markdown('---')
    if st.button('Milestone Practice'):
        st.session_state.unit = 'Milestone'
        st.experimental_rerun()
    if st.button('Special Project'):
        st.session_state.unit = 'Special'
        st.experimental_rerun()

# --- Chat Sessions ---
def chat_session(unit):
    user = st.session_state.user
    st.sidebar.button('Back to Menu', on_click=back_to_menu)

    if unit in units:
        df = vocab[unit]
    elif unit == 'Milestone':
        samples = []
        for u in units:
            dfu = vocab[u]
            samples += dfu.sample(2).to_dict('records')
        df = pd.DataFrame(samples)

    st.header(unit)
    prog_df = get_student_progress(user['first'], user['last'], user['block'])
    term_list = df['term'].tolist()
    mastered_terms = prog_df[prog_df['unit']==unit]['term'].tolist() if unit in units else []
    pct = int(round(len(mastered_terms)/len(term_list)*100)) if term_list else 0
    st.progress(pct/100)
    st.caption(f'Progress for {unit}: {pct}%')

    if 'messages' not in st.session_state:
        st.session_state.messages = []
        st.session_state.current_index = 0

    for msg in st.session_state.messages:
        st.chat_message(msg['role']).write(msg['content'])

    user_input = st.chat_input('Your response...')
    if user_input:
        st.session_state.messages.append({'role':'user','content':user_input})
        term = df.iloc[st.session_state.current_index]
        prompt = (
            f"Term: {term['term']}\nDefinition: {term['definition']}\nExample: {term['example']}\n"
            f"Student says: {user_input}\nEvaluate correctness, ask follow-up if needed."
        )
        # Use new OpenAI v2 API endpoint
        messages_payload = [{'role': 'system', 'content': 'You are a helpful tutor.'}]
        messages_payload += [{'role': m['role'], 'content': m['content']} for m in st.session_state.messages]
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_payload
        )
        reply = completion.choices[0].message.content
        st.session_state.messages.append({'role':'assistant','content':reply})

        if 'correct' in reply.lower() and unit in units:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                'INSERT OR REPLACE INTO progress (first_name,last_name,block,unit,term,mastered) VALUES (?,?,?,?,?,1)',
                (user['first'], user['last'], user['block'], unit, term['term'])
            )
            conn.commit()
            conn.close()
            st.session_state.current_index += 1
            if st.session_state.current_index >= len(term_list):
                st.success(f'{unit} completed!')

        st.experimental_rerun()

# --- Teacher View ---
def teacher_main():
    st.title('Teacher Dashboard')
    st.sidebar.button('Logout', on_click=logout)

    tabs = st.tabs(['First','Second','Fourth'])
    conn = sqlite3.connect(DB_PATH)
    students_df = pd.read_sql_query('SELECT * FROM students', conn)
    prog_df = pd.read_sql_query('SELECT * FROM progress', conn)
    conn.close()

    for idx, block in enumerate(['First','Second','Fourth']):
        with tabs[idx]:
            st.header(f'Block {block} Gradebook')
            blk_students = students_df[students_df['block']==block]
            records = []
            for _,r in blk_students.iterrows():
                fname, lname = r['first_name'], r['last_name']
                row = {'Last Name': lname, 'First Name': fname, 'Last Login': r['last_login']}
                pr = prog_df[(prog_df['first_name']==fname)&(prog_df['last_name']==lname)&(prog_df['block']==block)]
                for unit in units:
                    pct = int(round(pr[pr['unit']==unit]['mastered'].sum()/len(vocab[unit])*100)) if len(vocab[unit])>0 else 0
                    row[unit] = pct
                total_terms = sum(len(vocab[unit]) for unit in units)
                total_mastered = pr['mastered'].sum()
                row['Overall'] = int(round(total_mastered/total_terms*100)) if total_terms>0 else 0
                records.append(row)
            if not records:
                st.info('No students found in this block.')
            else:
                df = pd.DataFrame(records).sort_values('Last Name')
                edited = st.experimental_data_editor(df, num_rows='dynamic')
                if st.button(f'Download {block} Data'):
                    towrite = pd.ExcelWriter(f'block_{block}.xlsx', engine='xlsxwriter')
                    edited.to_excel(towrite, index=False, sheet_name=f'Block_{block}')
                    towrite.close()
                    with open(f'block_{block}.xlsx','rb') as f:
                        st.download_button('Download Excel', f, file_name=f'block_{block}.xlsx')

# --- Navigation ---
def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()

def back_to_menu():
    st.session_state.pop('unit', None)
    st.session_state.pop('messages', None)
    st.session_state.pop('current_index', None)
    st.experimental_rerun()

# --- App Control Flow ---
if st.session_state.role is None:
    show_login()
elif st.session_state.role == 'student':
    if 'unit' not in st.session_state:
        student_main()
    elif st.session_state.unit in units or st.session_state.unit == 'Milestone':
        chat_session(st.session_state.unit)
    else:
        st.header('Special Project: Chat with Ben')
        st.info('Benjamin Collins simulation coming soon.')
        if st.button('Back to Menu'):
            back_to_menu()
elif st.session_state.role == 'teacher':
    teacher_main()
