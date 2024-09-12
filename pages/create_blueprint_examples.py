import streamlit as st
import requests
from collections import defaultdict
import json

from helpers import process_content_table, create_filter_json, get_filter_options, get_unique_content_kits, query_airtable_table

# Streamlit app
st.title("Airtable Content Table")

base_id = "appkUZW01q89QDGB9"

# Fetch data on page load
content_kits_records = query_airtable_table(base_id, "Content Kits")

st.write("Enter your JSON filter object:")
json_input = st.text_area("JSON Input", 
                          '''{
"selected_kits": ["Kit Name 1", "Kit Name 2"],
"filters": {
    "step": ["Step 1", "Step 2"],
    "content_type": ["FAQ", "Handbook"],
    "type": ["Document", "Design"]
}
}''', 
                          height=200)

if st.button("Submit"):
    content_records = query_airtable_table(base_id, "content")
    try:
        filter_json = json.loads(json_input)
        processed_data = process_content_table(content_records, content_kits_records, filter_json)
        st.json(processed_data)
    except json.JSONDecodeError:
        st.error("Invalid JSON input. Please check your JSON format and try again.")
