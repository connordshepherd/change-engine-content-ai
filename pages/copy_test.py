import streamlit as st
from st_copy_to_clipboard import st_copy_to_clipboard

st.title("Copy to Clipboard Test")
st_copy_to_clipboard("Test text to copy")
