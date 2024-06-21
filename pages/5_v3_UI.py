import streamlit as st
import json
import pandas as pd
import requests

from io import BytesIO
from PIL import Image
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array_with_variations, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools
from helpers import send_plaintext_to_openai, get_client_data, prepare_layout_selector_data
from helpers import group_values, fix_problems, update_grouped, evaluate_character_count_and_lines_of_group
import openai
from typing import List, Dict, Union, Any, Tuple


# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

# Session State: Initialize the required session states
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None

# Streamlit UI - Title
st.title("Content Creation AI")

# Retrieve data from Airtable
content_types_data = get_content_types_data()

# Extract and filter content types where v1 is true
v1_true_content_types = [item["Content Type"] for item in content_types_data if item["v1"]]

# Insert default option at the start of the list
options = ["Select a Content Type"] + v1_true_content_types

# Add a selectbox to the Streamlit app
selected_content_type = st.selectbox("Choose a Content Type", options)

# Retrieve client data from Airtable
client_data = get_client_data()

# Create a selectbox for company name
company_name_list = sorted(client_data.keys())

# Determine the default index for the selectbox
default_company_index = 0  # Default to "Select a Company"
if "Global App Testing" in company_name_list:
    default_company_index = company_name_list.index("Global App Testing") + 1  # +1 because of "Select a Company"

selected_company_name = st.selectbox("Company", options=["Select a Company"] + company_name_list, index=default_company_index)

# Display the AI Brand Tone Prompt for the selected company
if selected_company_name and selected_company_name != 'Select a Company':
    company_tone_style = st.text_area("Company Tone and Style Guide", value=client_data[selected_company_name], height=100)
else:
    company_tone_style = st.text_area("Company Tone and Style Guide", value="", height=100)

# Set a number of variations, ie a number of times to run the content loop
variations = st.number_input("Number of Variations", 1, 10, value=5)
