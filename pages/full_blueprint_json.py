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
                                "step_description": {"type": "string"},
                                "elements": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": ["pcc", "educational"]
                                            },
                                            "record_id": {"type": "string"},
                                            "title": {"type": "string"},
                                            "description": {"type": "string"},
                                            "more_context": {"type": "string"},
                                            "image": {"type": "string"}
                                        },
                                        "required": ["type"]
                                    }
                                }
                            },
                            "required": ["step_number", "step_description"]
                        }
                    }
                },
                "required": ["steps"]
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

def call_openai_with_tools(messages, tools):
    response_raw = openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        tools=tools
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
    st.write(response_1)

    st.write("Running prompt 2 - Fill in steps")
    # Process prompt 2
    full_prompt_2 = f"Here's a list of content from our database:\n\n{pcc_plaintext}\n\nUsing this content, please fill in the steps you created with appropriate content. For each step, choose 2-3 pieces of content that fit well. Output in the same format as before, but include the content title and a brief description of how it fits into the step."
    messages.append({"role": "user", "content": full_prompt_2})
    response_2 = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_2})
    st.write(response_2)

    # You can add more steps here if needed

    return response_2

# Airtable API endpoint
base_id = "appkUZW01q89QDGB9"
table_name = "PCC"
url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

# Get the API token from Streamlit secrets
api_token = st.secrets["AIRTABLE_SECOND_TOKEN"]

# Set up the headers for the API request
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Make the API request
response = requests.get(url, headers=headers)

# Parse the JSON response
data = response.json()

# Extract the records
records = data['records']

# Create a list to store the extracted data
extracted_data = []

# Create the pcc_plaintext
pcc_plaintext = ""

# Extract the desired fields from each record
for record in records:
    # Handle the "Preview Image Final" field
    preview_image = record['fields'].get('Preview Image Final')
    image_url = preview_image[0]['url'] if preview_image else None

    # Handle the "Context" field
    context = record['fields'].get('Context', '')
    
    # Extract the first two sentences
    sentences = re.split(r'(?<=[.!?])\s+', context)
    first_two_sentences = ' '.join(sentences[:2]) if len(sentences) >= 2 else context

    extracted_record = {
        'Airtable Record ID': record['id'],
        'Moment Title': record['fields'].get('Moment Title', ''),
        'What': record['fields'].get('What', ''),
        'Context': context,
        'Preview Image Final': image_url,
        'Subject Line': record['fields'].get('Subject Line', ''),
        'context_first_two_sentences': first_two_sentences
    }
    extracted_data.append(extracted_record)

    # Add to pcc_plaintext
    pcc_plaintext += f"Record ID: {record['id']}\n"
    pcc_plaintext += f"Title: {extracted_record['Moment Title']}\n"
    pcc_plaintext += f"Description_short: {extracted_record['What']}\n"
    pcc_plaintext += f"More Context: {first_two_sentences}\n"
    pcc_plaintext += f"Has Image: {'Yes' if image_url else 'No'}\n"
    pcc_plaintext += f"Has Communication: {'Yes' if extracted_record['Subject Line'] else 'No'}\n\n"

# Create a DataFrame from the extracted data
df = pd.DataFrame(extracted_data)

# Display the dataframe
display_data = st.data_editor(df)

# Display the pcc_plaintext in a text area
st.text_area("PCC Plaintext", pcc_plaintext, height=400)

# Create JSON object from DataFrame
airtable_pcc = df.to_json(orient='records')

# Streamlit UI
st.title("Blueprint Builder")

user_prompt = st.text_area("What kind of blueprint do you want to make?", value="New Hire Onboarding", height=100)

prompt_1_intro_boilerplate = """Create program/initiative blueprints for an HR/People employee initiative. The theme of this initiative is: """

prompt_1_outro_boilerplate = """\n\nAs a first pass, we need to create 5 Steps in TOTAL to launch the program provided.\n
Create the title of the step and write one sentence describing what it means. Output with this format:\n\n

<EXAMPLE FORMAT>
Step 1: Program Design & Objectives\n
Description: Define the goals and structure of the Employee Referral Program, including setting clear objectives such as increasing quality hires, reducing time-to-hire, and promoting a positive company culture.\n\n

Step 2: Policy Development & Guidelines\n
Description: Establish the rules and guidelines for the referral program, including eligibility, reward structures, and processes.\n\n

Step 3: Communication & Promotion Plan\n
Description: Develop a comprehensive communication plan to introduce the Employee Referral Program to all employees. Utilize various channels such as emails, intranet, and team meetings to ensure maximum awareness and engagement.\n\n

Step 4: Training & Resources\n
Description: Provide training sessions and resources to help employees understand how to effectively refer candidates. This could include workshops, online tutorials, and informational brochures outlining best practices for making referrals.\n\n

Step 5: Monitoring, Feedback & Improvement\n
Description: Implement a system to track the effectiveness of the referral program, including metrics and employee feedback. Regularly review the program's performance and make necessary adjustments to improve its efficiency and effectiveness.
</EXAMPLE FORMAT>"""

if st.button("Process"):
    if 'pcc_plaintext' in locals():
        process_prompts(pcc_plaintext)
    else:
        st.error("Please run the Airtable data retrieval first to generate pcc_plaintext.")
