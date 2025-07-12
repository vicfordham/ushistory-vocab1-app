import streamlit as st

# Dummy functions and variables for example
def playful_reminder():
    return "Dr. Fordham knows all, so stay on task!"

term = {'term': 'Manifest Destiny'}

# The corrected line
st.info(f"{playful_reminder()} Try this: How do you think \"{term['term']}\" affected history?")