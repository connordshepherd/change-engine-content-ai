import streamlit as st
import requests
from collections import defaultdict
import json
import openai
from helpers import process_content_table, create_filter_json, get_filter_options, get_unique_content_kits, query_airtable_table

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_search_object",
            "description": "Create a search object to filter Airtable content for HR/People employee initiatives",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "A two-sentence explanation of why you're selecting the 5 Selected Kits you've chosen"
                    },
                    "selected_kits": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of Content Kit names to include in the search"
                    }
                },
                "required": ["selected_kits"]
            }
        }
    }
]

def call_openai_with_tools(messages, tools):
    response_raw = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        tools=tools
    )
    tool_call = response_raw.choices[0].message.tool_calls[0]
    json_str = tool_call.function.arguments
    return json_str

def get_content_kit_names(base_id):
    content_kits_records = query_airtable_table(base_id, "Content Kits")
    if content_kits_records:
        kit_names = [record['fields'].get('Content Kit', 'Unknown') for record in content_kits_records]
        return ", ".join(sorted(set(kit_names)))  # Use set to remove duplicates, then sort and join
    else:
        return "Failed to fetch Content Kit names"

# Streamlit app
st.title("Airtable Content Table")

base_id = "appkUZW01q89QDGB9"

# Fetch data on page load
names = get_content_kit_names(base_id)
user_input = st.text_input("What blueprint do you want to make?")

if st.button("Run Prompt"):

    prompt_template = """Here is a list of Content Kits we've created. Each of them contains outlines for an HR initiative:\n\n""" + names + """\n\nPlease return the 5 of these which most closely match this initiative submitted by a user:\n\n""" + user_input + """\n\nReturn no more than 5. Don't return any filters."""
    prompt = st.text_area(label="Prompt", value=prompt_template, height=200)
    messages = []
    messages.append({"role": "user", "content": prompt})
    response = call_openai_with_tools(messages, tools)
    st.json(response)
    
    if st.button("Submit"):
        content_records = query_airtable_table(base_id, "content")
        try:
            filter_json = json.loads(response)
            processed_data = process_content_table(content_records, content_kits_records, filter_json)
            st.json(processed_data)
        except json.JSONDecodeError:
            st.error("Invalid JSON input. Please check your JSON format and try again.")
