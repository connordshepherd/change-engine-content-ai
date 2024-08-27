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

prompt_default_value = """You are Employee Experience Manager at a company of about 100 to 5,000 employees. This company is a hybrid work environment. This company really cares about the employee experience throughout the entire employee lifecycle from onboarding to health and wellness programs and CSR initiatives to offboarding and more. The tone should be friendly, supportive, and encouraging and not too serious. Always refer to the HR Team as the People Team instead. Use this structure for the response: group response output by the category of output (where applicable) e.g. Title variation 1, Title variation 2 etc. Then subtitle variation 1, subtitle variation 2 et.c then illustration variation 1, illustration variation 2, illustration variation 3 etc. Never include headers like "Title Variation 10". Ignore any subsequent guidance on output structure in this prompt. Always group by title, subtitle etc. 

You need to create a bunch of summaries and key highlights in a FAQ. This FAQ must answer all of the questions and answers in one page maximum. The policies in the Employee Handbook will cover them in more detail, so these FAQ's don't need to have too much detail. We want these FAQ's to be informative but also engaging and friendly/supportive/helpful in tone. Use the Layouts below to use as a framework for the FAQs. The description of the Layouts outline the character count ranges and other info to produce an FAQ for the topic chosen. Produce an FAQ providing all of the content for the outline. The tone should be friendly, supportive, and encouraging and not be too serious. Always use the outlined character count ranges, # of questions or topics and answers, and everything else outlined in the Layout Descriptions. Never deviate from the Layout Description.
----
The topic is: new contractor onboarding faq. Come up with 2 variations. Never output in code.
----

For each variation include:

**Details for Layout 2**
Title: A title of 28-33 characters
Subtitle: A subtitle of 20-30 characters
Number of Questions and Answers: 5 questions and answers
Suggest Icon/Illustration/Photo: Icon or illustration
Question: A question of 60-75 characters
Answer: An answer of 130-144 characters
image-type: Icon
Description: A description of 120-145 characters






----

Use this structure for the response:
Variation n:
Title
Subtitle
Number of Questions and Answers
Suggest Icon/Illustration/Photo
Question
Answer
image-type
Description"""



# Streamlit UI
st.title("FAQ JSON")
prompt = st.text_area("Prompt", value=prompt_default_value, height=400)
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
                                    "title": {"type": "string"},
                                    "subtitle": {"type": "string"},
                                    "questions_answers": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "question": {"type": "string"},
                                                "answer": {"type": "string"},
                                                "image_type": {
                                                    "type": "string",
                                                    "enum": ["icon", "illustration", "photo"]
                                                },
                                                "image_description": {"type": "string"}
                                            },
                                            "required": ["question", "answer", "image_type", "image_description"]
                                        }
                                    }
                                },
                                "required": ["title", "subtitle", "questions_answers"]
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

# Raw write
st.write("RAW")
st.write(response.status_code)
st.write(response.json)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    result = response.json()
    
    # Extract the generated content
    generated_content = result['choices'][0]['message']['tool_calls'][0]['function']['arguments']
    
    # Parse the JSON string into a Python dictionary
    contractor_onboarding = json.loads(generated_content)
    
    print(json.dumps(contractor_onboarding, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
