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
    st.json(response_1)

    st.write("Running prompt 2 - Fill in steps")
    # Process prompt 2
    full_prompt_2 = prompt_2_boilerplate + pcc_plaintext + "As a reminder, the JSON object with the step numbers and descriptions is:" + '\n\n' + str(response_1)
    messages.append({"role": "user", "content": full_prompt_2})
    response_2 = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_2})
    st.json(response_2)

    st.write("Running prompt 3 - Adding Educational Elements")
    # Process prompt 3
    full_prompt_3 = prompt_3_boilerplate + '\n\n' + "As a reminder, the JSON object with steps and elements we're adding to is:" + '\n\n' + str(response_2)
    messages.append({"role": "user", "content": full_prompt_3})
    response_3 = call_openai_with_tools(messages, tools)
    messages.append({"role": "assistant", "content": response_3})
    st.json(response_3)

    return response_3

# Get the PCC
from dummy import dummy_json
pcc_plaintext = str(dummy_json)

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

prompt_2_boilerplate_old = """Great! Now we're going to begin adding elements to each step, from our database of element options. \n
For each step, pick exactly 4 of the options on the below menu of Elements. \n
For 'type' on these, return 'pcc'.
Very important - please only use each element ONCE in your plan - if you use an element in one step you can't use it in other steps.\n
Here's the list of element options:\n\n"""

prompt_2_boilerplate = """Great! Now we're going to begin adding elements to each step.\n
Here are some previous blueprints you can use as examples. See how the elements nest within the steps? Every step should have at least 4 elements.\n
Don't add Educational Elements yet - we'll worry about that later.\n
Very important - please only use each element ONCE in your plan - if you use an element in one step you can't use it in other steps.\n"""

prompt_3_boilerplate = """Great! Now, we need to add in "Educational Elements." These are places in the plan where the HR lead needs to gather information, circulate information, or define their goals.\n
Here's the menu of Educational Elements: \n
1. Identify Stakeholders
2. Analyze Data
3. Quick Win
4. Top Tip
5. Define Goal
Please add two Educational Elements to each step. \n
For 'content_type' on these, return 'educational.' \n
You will need to write your own Description."""

if st.button("Process"):
    if 'pcc_plaintext' in locals():
        process_prompts(pcc_plaintext)
    else:
        st.error("Please run the Airtable data retrieval first to generate pcc_plaintext.")
