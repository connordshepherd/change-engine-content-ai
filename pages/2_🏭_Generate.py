import streamlit as st
import json
import pandas as pd
from helpers import get_content_types_data, get_table_data, process_table_data

# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

# Session State: Initialize the required session states
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None

# Streamlit UI - Title
st.title("Content Creation AI - Config")

# Retrieve data from Airtable
content_types_data = get_content_types_data()

# Extract and filter content types where v1 is true
v1_true_content_types = [item["Content Type"] for item in content_types_data if item["v1"]]

# Insert default option at the start of the list
options = ["Select a Content Type"] + v1_true_content_types

# Title for the resulting generation
document_title = st.text_input("Content", "Perks and Benefits FAQ")

# Add a selectbox to the Streamlit app
selected_content_type = st.selectbox("Choose a Content Type", options)

# Text input for layouts (comma-separated integers)
selected_layouts = st.text_input("Select Layouts", "1, 3, 5")

if selected_content_type != "Select a Content Type":
    # Filter data to get the selected content type details
    selected_data = next((item for item in content_types_data if item["Content Type"] == selected_content_type), None)
    
    if selected_data:
        st.subheader("Details for: " f"{selected_content_type}")

        # Display the Image Prompt in a text area for editing
        image_prompt = st.text_area("Image Prompt", value=selected_data["Image Prompt"], height=400)

        # Load data from the table corresponding to the selected content type
        table_data = get_table_data(selected_content_type)
        
        # Process the table data into a DataFrame
        df = process_table_data(table_data)

        # Display the DataFrame
        edited_data = df
        oriented_json = edited_data.to_json(orient='records')
        edited_json = json.loads(oriented_json)

        # Display a JSON object for debugging
        st.subheader("Debug")
        st.write(edited_json)
        
    else:
        st.write("No details available for the selected content type.")
else:
    st.write("Please select a content type to see details.")
