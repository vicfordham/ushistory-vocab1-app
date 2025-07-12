
import streamlit as st
import pandas as pd
import random
from datetime import datetime

# ------------------- Setup -------------------

st.set_page_config(page_title="U.S. History Vocab Mastery", layout="wide")

@st.cache_data
def load_vocab():
    try:
        return pd.read_excel("vocab.xlsx", sheet_name=None)
    except Exception as e:
        st.error(f"Could not load vocabulary file: {e}")
        return {}

@st.cache_data
def load_teacher_password():
    return "teacher123"

# ------------------- Session State Init -------------------

if "page" not in st.session_state:
    st.session_state.page = "login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_term_index" not in st.session_state:
    st.session_state.current_term_index = 0
if "unit" not in st.session_state:
    st.session_state.unit = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "block" not in st.session_state:
    st.session_state.block = ""
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False

# ------------------- Utility Functions -------------------

def format_last_login(dt):
    return dt.strftime("%B %d, %Y - %I:%M %p")

def get_student_progress(name, block, unit, scores_df):
    row = scores_df[(scores_df["Name"] == name) & (scores_df["Block"] == block)]
    if row.empty:
        return 0
    return int(round(row[unit].values[0]))

def update_student_score(name, block, unit, score, scores_df):
    if not ((scores_df["Name"] == name) & (scores_df["Block"] == block)).any():
        new_row = {"Name": name, "Block": block, unit: score, "Last Login": datetime.now()}
        scores_df.loc[len(scores_df)] = new_row
    else:
        idx = scores_df[(scores_df["Name"] == name) & (scores_df["Block"] == block)].index[0]
        scores_df.at[idx, unit] = score
        scores_df.at[idx, "Last Login"] = datetime.now()
    return scores_df

def save_scores(scores_dict):
    with pd.ExcelWriter("scores.xlsx", engine="openpyxl", mode="w") as writer:
        for block, df in scores_dict.items():
            df.sort_values(by="Name", inplace=True)
            df.to_excel(writer, sheet_name=block, index=False)

def load_scores():
    try:
        excel_file = pd.ExcelFile("scores.xlsx")
        return {sheet: excel_file.parse(sheet) for sheet in excel_file.sheet_names}
    except:
        return {
            "First Block": pd.DataFrame(columns=["Name", "Block", "Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6", "Unit 7", "Milestone Practice", "Last Login"]),
            "Second Block": pd.DataFrame(columns=["Name", "Block", "Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6", "Unit 7", "Milestone Practice", "Last Login"]),
            "Fourth Block": pd.DataFrame(columns=["Name", "Block", "Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6", "Unit 7", "Milestone Practice", "Last Login"]),
        }

# ------------------- Pages -------------------

def login_page():
    st.title("Welcome to Dr. Fordham's U.S. History Vocab Mastery")
    st.subheader("Student Login")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        first = st.text_input("First Name")
    with col2:
        last = st.text_input("Last Name")
    with col3:
        block = st.selectbox("Block", ["First Block", "Second Block", "Fourth Block"])
    if st.button("Login"):
        if first and last:
            full_name = f"{last.strip().title()}, {first.strip().title()}"
            st.session_state.student_name = full_name
            st.session_state.block = block
            st.session_state.page = "main"
            st.rerun()

    st.divider()
    st.subheader("Teacher Login")
    password = st.text_input("Enter Teacher Password", type="password")
    if st.button("Login as Teacher"):
        if password == load_teacher_password():
            st.session_state.teacher_logged_in = True
            st.session_state.page = "teacher"
            st.rerun()
        else:
            st.error("Incorrect password.")

def main_menu():
    st.title(f"Welcome, {st.session_state.student_name}!")
    vocab_data = load_vocab()
    scores_dict = load_scores()
    units = [f"Unit {i}" for i in range(1,8)] + ["Milestone Practice"]
    unit_buttons = []

    total_score = 0
    for unit in units:
        score = get_student_progress(st.session_state.student_name, st.session_state.block, unit, scores_dict[st.session_state.block])
        total_score += score
    overall = int(round(total_score / (len(units) * 100) * 100))
    st.progress(overall, text=f"Overall Progress: {overall}%")

    for i in range(0, len(units), 4):
        cols = st.columns(4)
        for j, unit in enumerate(units[i:i+4]):
            with cols[j]:
                if st.button(unit):
                    st.session_state.unit = unit
                    st.session_state.page = "chat"
                    st.rerun()

    if st.button("Log Out"):
        st.session_state.page = "login"
        st.rerun()

def chat_page():
    st.title(f"{st.session_state.unit} Vocabulary")
    st.button("⬅️ Back to Menu", on_click=lambda: st.session_state.update({"page": "main"}))
    st.button("Logout", on_click=lambda: st.session_state.update({"page": "login"}))
    st.divider()

    vocab_data = load_vocab()
    scores_dict = load_scores()
    unit_tab = st.session_state.unit if st.session_state.unit != "Milestone Practice" else random.choice(list(vocab_data.keys()))
    words = vocab_data.get(unit_tab, pd.DataFrame(columns=["term", "definition"]))
    word_list = words.to_dict("records")

    if st.session_state.unit == "Milestone Practice":
        word_list = random.sample(word_list, min(10, len(word_list)))

    if "current_term_index" not in st.session_state or st.session_state.unit != st.session_state.get("last_unit"):
        st.session_state.current_term_index = 0
        st.session_state.chat_history = []
        st.session_state.last_unit = st.session_state.unit

    index = st.session_state.current_term_index
    if index < len(word_list):
        term_data = word_list[index]
        st.markdown(f"**🗣 Let's talk about the word: `{term_data['term']}`**")
        user_input = st.text_input("What does this mean?", key=f"input_{index}")
        if st.button("Submit", key=f"submit_{index}"):
            correct = term_data["definition"].lower()
            if user_input and user_input.lower() in correct:
                response = f"✅ That's right! '{term_data['term']}' means: {term_data['definition']}"
            else:
                response = f"🤔 Not quite. '{term_data['term']}' means: {term_data['definition']}"

            st.session_state.chat_history.append((term_data['term'], user_input, response))
            st.session_state.current_term_index += 1
            st.rerun()
    else:
        st.success("🎉 You’ve completed this unit!")
        score = int(round(len(st.session_state.chat_history) / len(word_list) * 100))
        scores_dict[st.session_state.block] = update_student_score(
            st.session_state.student_name,
            st.session_state.block,
            st.session_state.unit,
            score,
            scores_dict[st.session_state.block]
        )
        save_scores(scores_dict)

    for term, answer, reply in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(f"**{term}**: {answer}")
        with st.chat_message("assistant"):
            st.markdown(reply)

def teacher_page():
    st.title("📊 Teacher Dashboard")
    st.button("Logout", on_click=lambda: st.session_state.update({"teacher_logged_in": False, "page": "login"}))
    scores_dict = load_scores()
    tabs = st.tabs(["First Block", "Second Block", "Fourth Block"])
    for i, block in enumerate(["First Block", "Second Block", "Fourth Block"]):
        with tabs[i]:
            df = scores_dict[block].copy()
            if not df.empty:
                df["Last Login"] = pd.to_datetime(df["Last Login"], errors="coerce").dt.strftime("%B %d, %Y - %I:%M %p")
                unit_cols = [col for col in df.columns if "Unit" in col or "Milestone" in col]
                df["Overall"] = df[unit_cols].mean(axis=1).round().astype("Int64").astype(str) + "%"
                df = df[["Name"] + unit_cols + ["Overall", "Last Login"]]
                df = df.sort_values("Name")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No student data available.")

# ------------------- Routing -------------------

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "main":
    main_menu()
elif st.session_state.page == "chat":
    chat_page()
elif st.session_state.page == "teacher":
    teacher_page()
