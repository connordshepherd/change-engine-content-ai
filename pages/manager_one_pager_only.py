# These are all the old imports - you probably don't need all this
import streamlit as st
import json
import pandas as pd
import requests
from st_copy_to_clipboard import st_copy_to_clipboard
from io import BytesIO
from PIL import Image
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array_with_variations, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools
from helpers import send_plaintext_to_openai, get_client_data, prepare_layout_selector_data, assemble_prompt, get_image_from_url
from helpers import group_values, fix_problems, update_grouped, evaluate_character_count_and_lines_of_group
from dummy import dummy_prompt
import openai
from typing import List, Dict, Union, Any, Tuple
import webbrowser
from streamlit.components.v1 import html

prompt_default_value = """You need to create a manager one pager to educate managers. This one-pager must give managers tips and tricks in one page maximum. The manager coaching guide will cover them in more detail, so these manager one-pagers don't need to have too much detail. We want these one-pagers to be informative but also engaging and friendly/supportive/helpful in tone. Use the Layouts to use as a framework for the manager one pager . The description of the Layouts outline the character count ranges and other info to produce a one pager for the topic chosen. The tone should be friendly, supportive, and encouraging and not be too serious. Always use the outlined character count ranges, # of questions or topics and answers, and everything else outlined in the Layout Descriptions. Never deviate from the Layout Description.
----
The topic is: Program Evaluation Report towards company goal of increasing employee referral rates from 15% to 25% in 3 months. Come up with 2 variations. Never output in code.
----

For each variation include:

**Details for Layout 8**
subheader: a subheader between 25- 38 characters
subheader-1: a subheader #1 of between 60-74
subheader-3: a subheader #3 of between 60-74 characters
section-4: a section #4 of between 400-504 characters
section-2: a section #2 of between 300-504 characters
subheader-2: a subheader #2 of between 60-74 characters
section-3: a section #3 of between 400-504 characters
header: a header of 2 lines, every line is a maximum of 27 characters each (27/27)
subheader-4: subheader #4 of between 60-74 characters
section-1: a section #1 of 4 lines, every line is maximum 126 characters (126/126/126/126) Write a bulletpoint or numbered list
section-5: a section #5 of between 600-672 characters
subheader-5: a subheader #5 of between 60-74 characters
description: a description between 500-608 characters"""



# Streamlit UI
st.title("Manager One-Pager JSON")
prompt = st.text_area("Prompt", value=prompt_default_value, height=400)

if st.button("Submit"):
        messages = [{"role": "user", "content": prompt}]
        
        # Your OpenAI API key
        api_key = st.secrets.OPENAI_API_KEY
        
        # The API endpoint
        url = "https://api.openai.com/v1/chat/completions"
        
        # The headers for the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # The request payload
        payload = {
            "model": "gpt-4o-2024-08-06",  # Use an available model
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI that generates contractor onboarding information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "generate_contractor_onboarding",
                        "description": "Generate contractor onboarding information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "variations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "reasoning": {
                                                "type": "string",
                                                "description": "To get started, write 3 sentences describing the manager one-pager you're about to compose. Give some thought to how many sections you'll need and what you want to put in each one."
                                            },
                                            "header": {"type": "string"},
                                            "subheader": {"type": "string"},
                                            "description": {"type": "string"},
                                            "sections": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "section_subheader": {"type": "string"},
                                                        "section_content": {"type": "string"},
                                                        "image_type": {
                                                            "type": "string",
                                                            "enum": ["icon", "illustration", "photo"]
                                                        },
                                                        "image_description": {"type": "string"}
                                                    },
                                                    "required": ["section_subheader", "section_content", "image_type", "image_description"]
                                                }
                                            }
                                        },
                                        "required": ["header", "subheader", "sections"]
                                    }
                                }
                            },
                            "required": ["variations"]
                        }
                    }
                }
            ]
        }
        
        # Make the API call
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            
            # Extract the generated content
            generated_content = result['choices'][0]['message']['tool_calls'][0]['function']['arguments']
            
            # Parse the JSON string into a Python dictionary
            contractor_onboarding = json.loads(generated_content)
            
            #st.write(json.dumps(contractor_onboarding, indent=2))
            st.write(contractor_onboarding)
        else:
            st.write(f"Error: {response.status_code}")
            st.write(response.text)
