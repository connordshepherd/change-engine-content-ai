import streamlit as st
import pandas as pd
import io
import numpy as np
import json
import openai
import csv
import re
import requests
from collections import OrderedDict
from helpers import process_content_table, create_filter_json, get_filter_options, get_unique_content_kits, query_airtable_table

# Set the main JSON schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_blueprint",
            "description": "Generate a blueprint for an HR/People employee initiative",
            "parameters": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step_number": {"type": "integer"},
                                "step_title": {"type": "string"},
                                "step_description": {"type": "string"},
                                "elements": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "content_type": {
                                                "type": "string",
                                                "enum": ["Manager One-Pager", "LinkedIn Cover", "FAQ", "Logo", "TV Display", "Certificate", "Zoom Background", "Communication", "Zoom Background", "Poster", "Communication", "Educational Element"]
                                            },
                                            "record_id": {"type": "string"},
                                            "title": {"type": "string"},
                                            "description": {"type": "string"},
                                            "more_context": {"type": "string"},
                                            "image": {"type": "string"}
                                        },
                                        "required": ["content_type"]
                                    }
                                }
                            },
                            "required": ["step_number", "step_title", "step_description"]
                        }
                    }
                },
                "required": ["steps"]
            }
        }
    }
]

# Set the tool for matching to content kits
content_kit_tools = [
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

def call_openai(messages):
    response_raw = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages
    )
    return response_raw.choices[0].message.content

def get_content_kit_names(base_id, content_kits_records):
    if content_kits_records:
        kit_names = [record['fields'].get('Content Kit', 'Unknown') for record in content_kits_records]
        return ", ".join(sorted(set(kit_names)))  # Use set to remove duplicates, then sort and join
    else:
        return "Failed to fetch Content Kit names"

def call_openai_with_tools(messages, tools):
    response_raw = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        tools=tools,
        tool_choice="required"
    )
    tool_call = response_raw.choices[0].message.tool_calls[0]
    json_str = tool_call.function.arguments
    return json_str

def process_prompts(pcc_plaintext):
    messages = []

    st.write("Running prompt 1 - Steps")
    # Process prompt 1
    full_prompt_1 = prompt_1_intro_boilerplate + user_prompt + prompt_1_outro_boilerplate
    messages.append({"role": "user", "content": full_prompt_1})
    response_1 = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_1})
    st.json(response_1)

    st.write("Running prompt 2 - Fill in communications")
    # Process prompt 2
    full_prompt_2 = prompt_2_boilerplate + pcc_plaintext + "As a reminder, the JSON object with the step numbers and descriptions is:" + '\n\n' + str(response_1)
    messages.append({"role": "user", "content": full_prompt_2})
    response_2 = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_2})
    st.json(response_2)

    st.write("Running prompt 2 a - Fill in other elements")
    # Process prompt 2a
    full_prompt_2a = prompt_2a_boilerplate + pcc_plaintext + "As a reminder, the JSON object with the step numbers and descriptions is:" + '\n\n' + str(response_2)
    messages.append({"role": "user", "content": full_prompt_2a})
    response_2a = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_2})
    st.json(response_2a)

    st.write("Running prompt 3 - Adding Educational Elements")
    # Process prompt 3
    full_prompt_3 = prompt_3_boilerplate + '\n\n' + "As a reminder, the JSON object with steps and elements we're adding to is:" + '\n\n' + str(response_2a)
    messages.append({"role": "user", "content": full_prompt_3})
    response_3 = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_3})
    st.json(response_3)

    return response_3

# Set Airtable base ID
base_id = "appkUZW01q89QDGB9"

# Streamlit UI
st.title("Blueprint Builder")

user_prompt = st.text_area("What kind of blueprint do you want to make?", value="New Hire Onboarding", height=100)

prompt_1_intro_boilerplate = """Create program/initiative blueprints for an HR/People employee initiative. The theme of this initiative is: """

prompt_1_outro_boilerplate = """\n\nAs a first pass, we need to create three to five Steps in TOTAL to launch the program provided.\n
Create the title of the step and write one sentence describing what it means. Output with this format:\n\n

<EXAMPLE FORMAT>
Step 1: Raise Awareness & Educate\n
Description: Provide critical information about breast cancer, focusing on prevention, early detection, and available resources. Empower employees with the knowledge they need to spread awareness themselves.\n\n

Step 2: Encourage Participation & Advocacy\n
Foster engagement by organizing events, sharing compelling stories, and raising funds, encouraging active participation and advocacy among employees within and beyond the company.\n\n

Step 3: Celebrate Impact & Sustain Awareness\n
Recognize the collective efforts and accomplishments of employees, while ensuring that breast cancer awareness becomes a long-term commitment.\n
</EXAMPLE FORMAT>\n

You're creating the plan, so the first step shouldn't be anything like "Create a Plan" or "Define the steps." That's what you're doing!"""

prompt_2_boilerplate = """Great! Now we're going to begin adding elements to each step.\n
Here are some previous blueprints you can use as examples. See how the elements nest within the steps?\n
Don't add Educational Elements yet - we'll worry about that later.\n
2 elements of each step should always be Communications. So first, please add 2 Communications per step.\n\n"""

prompt_2a_boilerplate = """Great! Now we're going to add more elements to each step.\n
Here are the previous blueprints you can use as examples again. See how the elements nest within the steps?\n
Please don't add Educational Elements yet - we'll worry about that later.\n
Now, please add other elements to the blueprint - Zoom Backgrounds, Posters, FAQS, and so on. Use the previous blueprints as a reference. Important - please use these ONCE in your plan - if you use an element in one step you can't use it in other steps. For example if you use Zoom Background in one step, you can't use any more Zoom Backgrounds in subsequent steps.\n"""


prompt_3_boilerplate = """Great! Now, we need to add in “Educational Elements.” These are places in the plan where the HR lead needs to gather information, circulate information, or define their goals.\n
Here’s the menu of Educational Elements: \n
1. Identify Stakeholders
2. Analyze Data
3. Quick Win
4. Top Tip
5. Define Goal
Please add two Educational Elements to each step. \n
For 'content_type' on these, return 'Educational Element.' \n
You will need to write your own Description. It should be longer than the others, 4 sentences long at least. Keep the description tone friendly like an upbeat advisor that’s giving you specific advice on the topic. Try not to generalize too much and provide specific tips that could be really useful.  \n
Return the new Educational Elements first within each step, ahead of the other stuff you composed in prior steps."""

if st.button("Process"):
    # Fetch Content Kit data from Airtable
    st.write("Fetching Content Kit names from Airtable to use as examples")
    content_kits_records = query_airtable_table(base_id, "Content Kits")
    names = get_content_kit_names(base_id, content_kits_records)
    matching_prompt = """Here is a list of Content Kits we've created. Each of them contains outlines for an HR initiative:\n\n""" + names + """\n\nPlease return the 5 of these which most closely match this initiative submitted by a user:\n\n""" + user_prompt + """\n\nReturn no more than 5. Don't return any filters."""
    matching_messages = []
    matching_messages.append({"role": "user", "content": matching_prompt})
    matching_response = call_openai_with_tools(matching_messages, content_kit_tools)
    st.write("Found matching Content Kits from Airtable")
    st.json(matching_response)

    # Fetch the matches from Airtable
    st.write("Pulling the full matching content kits from Airtable to use as examples")
    content_records = query_airtable_table(base_id, "content")
    filter_json = json.loads(matching_response)
    processed_data = process_content_table(content_records, content_kits_records, filter_json)
    pcc_plaintext = str(processed_data)
    
    if 'pcc_plaintext' in locals():
        process_prompts(pcc_plaintext)
    else:
        st.error("Please run the Airtable data retrieval first to generate pcc_plaintext.")
