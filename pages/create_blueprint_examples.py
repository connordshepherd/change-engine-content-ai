import streamlit as st
import requests
from collections import defaultdict
import json
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
                    "selected_kits": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of Content Kit names to include in the search"
                    },
                    "filters": {
                        "type": "object",
                        "properties": {
                            "step": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of step names to filter by"
                            },
                            "content_type": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of content types to filter by"
                            },
                            "type": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of element types to filter by"
                            }
                        }
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

# Streamlit app
st.title("Airtable Content Table")

base_id = "appkUZW01q89QDGB9"

# Fetch data on page load
content_kits_records = query_airtable_table(base_id, "Content Kits")

prompt_template = """Here is a list of Content Kits we've created. Each of them contains outlines for an HR initiative:\n""" + str(content_kits_records)

prompt = st.text_area(value=prompt, height=200)

if st.button("Submit"):
    content_records = query_airtable_table(base_id, "content")
    try:
        filter_json = json.loads(json_input)
        processed_data = process_content_table(content_records, content_kits_records, filter_json)
        st.json(processed_data)
    except json.JSONDecodeError:
        st.error("Invalid JSON input. Please check your JSON format and try again.")
