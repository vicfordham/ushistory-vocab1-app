
import streamlit as st

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "teacher_password" not in st.session_state:
    st.session_state.teacher_password = ""

def home_page():
    st.markdown("<h1 style='text-align: center;'>Welcome to Dr. Fordham's U.S. History Lab</h1>", unsafe_allow_html=True)
    st.subheader("Student Login")
    st.text_input("First Name", key="first_name")
    st.text_input("Last Name", key="last_name")
    st.selectbox("Class Block", ["First", "Second", "Fourth"], key="block")
    if st.button("Login as Student"):
        st.session_state.page = "main_menu"
        st.experimental_rerun()

    st.subheader("Teacher Login")
    st.text_input("Enter Teacher Password", type="password", key="teacher_password")
    if st.button("Login as Teacher"):
        if st.session_state.teacher_password == "letmein":
            st.session_state.page = "teacher_dashboard"
            st.experimental_rerun()
        else:
            st.error("Incorrect password. Please try again.")

def teacher_dashboard():
    st.title("📊 Teacher Dashboard")
    st.write("This is where the teacher dashboard will be displayed.")
    if st.button("Logout"):
        st.session_state.page = "home"
        st.experimental_rerun()

# Main app logic
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "teacher_dashboard":
    teacher_dashboard()
else:
    st.write("Unknown page state. Returning home.")
    st.session_state.page = "home"
    st.experimental_rerun()
