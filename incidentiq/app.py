import streamlit as st

st.set_page_config(page_title="IncidentIQ — New Incident", page_icon="🚨")
st.title("IncidentIQ — New Incident")

uploaded_file = st.file_uploader("Upload an incident log", type=None)

if uploaded_file is not None:
    st.write(f"{uploaded_file.name} — {len(uploaded_file.getvalue())} bytes")
