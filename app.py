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
    c.execute('INSERT OR IGNORE INTO students (first_name, last_name, block, last_login) VALUES (?,?,?,?)',
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
        if st.button('Login as Student') and first and last:
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
    total_terms = sum(vocab[u].shape[0] for u in units)
    mastered = prog_df['mastered'].sum()
    overall_pct = int(round((mastered/total_terms)*100)) if total_terms else 0
    st.progress(overall_pct/100)
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

    # Select term list
    if unit in units:
        df_terms = vocab[unit]
    elif unit == 'Milestone':
        samples = []
        for u in units:
            samples += vocab[u].sample(2).to_dict('records')
        df_terms = pd.DataFrame(samples)
    else:
        st.header('Special Project')
        st.info('Coming soon.')
        return

    # Initialize state
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Start by asking student without giving definition
    if not st.session_state.messages:
        term0 = df_terms.iloc[0]
        init_q = f"What do you think the word '{term0['term']}' means?"
        st.session_state.messages.append({'role':'assistant','content':init_q})

    # Display progress header
    st.header(unit)
    prog_df = get_student_progress(user['first'], user['last'], user['block'])
    total = len(df_terms)
    mastered = prog_df[prog_df['unit']==unit]['mastered'].sum() if unit in units else 0
    pct = int(round(mastered/total*100)) if total else 0
    st.progress(pct/100)
    st.caption(f'Progress for {unit}: {pct}%')

    # Render chat history
    for msg in st.session_state.messages:
        st.chat_message(msg['role']).write(msg['content'])

    # Accept user reply
    user_input = st.chat_input('Your response...')
    if user_input:
        st.session_state.messages.append({'role':'user','content':user_input})
        term = df_terms.iloc[st.session_state.current_index]
        # Build conversation for model
        system_msg = {'role':'system','content':'You are a helpful history vocabulary tutor. Ask follow-up questions as needed, and recognize partial correctness.'}
        payload = [system_msg] + st.session_state.messages
        completion = openai.chat.completions.create(model="gpt-4o-mini", messages=payload)
        reply = completion.choices[0].message.content
        st.session_state.messages.append({'role':'assistant','content':reply})

        # If student shows mastery, record and move to next term
        if 'correct' in reply.lower() and unit in units:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO progress (first_name,last_name,block,unit,term,mastered) VALUES (?,?,?,?,?,1)',
                      (user['first'], user['last'], user['block'], unit, term['term']))
            conn.commit()
            conn.close()
            st.session_state.current_index += 1
            if st.session_state.current_index < len(df_terms):
                next_term = df_terms.iloc[st.session_state.current_index]
                next_q = f"Great! Now, what do you think '{next_term['term']}' means?"
                st.session_state.messages.append({'role':'assistant','content':next_q})
            else:
                st.session_state.messages.append({'role':'assistant','content':f"Congratulations! You've completed {unit}!"})
        st.experimental_rerun()

# --- Teacher View ---
def teacher_main():
    st.title('Teacher Dashboard')
    st.sidebar.button('Logout', on_click=logout)
    tabs = st.tabs(['First','Second','Fourth'])
    conn = sqlite3.connect(DB_PATH)
    students_df = pd.read_sql('SELECT * FROM students', conn)
    prog_df = pd.read_sql('SELECT * FROM progress', conn)
    conn.close()

    for i, block in enumerate(['First','Second','Fourth']):
        with tabs[i]:
            st.header(f'Block {block} Gradebook')
            blk = students_df[students_df['block']==block]
            records = []
            for _, r in blk.iterrows():
                fname, lname = r['first_name'], r['last_name']
                row = {'Last Name': lname, 'First Name': fname, 'Last Login': r['last_login']}
                pr = prog_df[(prog_df['first_name']==fname)&(prog_df['last_name']==lname)&(prog_df['block']==block)]
                for u in units:
                    pct = int(round(pr[pr['unit']==u]['mastered'].sum()/len(vocab[u])*100)) if len(vocab[u])>0 else 0
                    row[u] = pct
                total = sum(len(vocab[u]) for u in units)
                mastered = pr['mastered'].sum()
                row['Overall'] = int(round(mastered/total*100)) if total else 0
                records.append(row)
            if records:
                df = pd.DataFrame(records).sort_values('Last Name')
                edited = st.experimental_data_editor(df)
                if st.button(f'Download {block} Data'):
                    towrite = pd.ExcelWriter(f'{block}_data.xlsx', engine='xlsxwriter')
                    edited.to_excel(towrite, index=False, sheet_name=block)
                    towrite.close()
                    with open(f'{block}_data.xlsx','rb') as f:
                        st.download_button('Download Excel', f, file_name=f'{block}_data.xlsx')
            else:
                st.info('No students in this block.')

# --- Navigation Helpers ---
def logout():
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.experimental_rerun()

def back_to_menu():
    for k in ['unit','current_index','messages']: st.session_state.pop(k, None)
    st.experimental_rerun()

# --- App Flow ---
if st.session_state.role is None:
    show_login()
elif st.session_state.role=='student':
    if 'unit' not in st.session_state:
        student_main()
    else:
        chat_session(st.session_state.unit)
elif st.session_state.role=='teacher':
    teacher_main()
