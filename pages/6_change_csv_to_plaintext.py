import streamlit as st
import pandas as pd
import io
import numpy as np
import json
import openai
import csv
import re
from collections import OrderedDict

def call_openai(messages):
    response_raw = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response_raw.choices[0].message.content

def process_prompts():
    messages = []

    st.write("Running prompt 1")
    # Process prompt 1
    messages.append({"role": "user", "content": prompt_1_editable})
    response_1 = call_openai(messages)
    messages.append({"role": "assistant", "content": response_1})
    
    st.write("Running prompt 2")
    # Process prompt 2
    messages.append({"role": "user", "content": prompt_2_editable})
    response_2 = call_openai(messages)
    messages.append({"role": "assistant", "content": response_2})
    
    st.write("Running prompt 3")
    # Process prompt 3
    messages.append({"role": "user", "content": prompt_3_editable})
    response_3 = call_openai(messages)
    messages.append({"role": "assistant", "content": response_3})
    
    # Extract content between triple backticks
    pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(pattern, response_3)

    if match:
        cleaned_response = match.group(1).strip()
    else:
        cleaned_response = response_3.strip()
        st.warning("No content found between triple backticks. Using the entire response.")
    
    # Display final response as JSON
    try:
        json_response = json.loads(cleaned_response)
        st.write("Original JSON")
        st.json(json_response)

        # Update the hardcoded JSON with Content Type and Type
        updated_json = update_json_with_content_info(hardcoded_json, content_map)
        st.write("Updated JSON")
        st.json(updated_json)
        
        # Convert JSON to CSV and offer download
        csv_string = io.StringIO()
        writer = csv.writer(csv_string)
        
        # Write headers
        headers = list(updated_json[0].keys()) if updated_json else []
        writer.writerow(headers)
        
        # Write data
        for item in updated_json:
            writer.writerow(item.values())
        
        st.download_button(
            label="Download CSV",
            data=csv_string.getvalue(),
            file_name="output.csv",
            mime="text/csv"
        )
    except json.JSONDecodeError:
        st.error("The final response is not a valid JSON object.")
        st.text("Cleaned response:")
        st.text(cleaned_response)

def process_csv(df):
    output = ""
    for index, row in df.iterrows():
        output += f"ROW {index + 1}\n"  # Adding row number
        
        # Only include non-null values
        if pd.notna(row['Content Title']):
            output += f"Content Title: {row['Content Title']}\n"
        if pd.notna(row['Goals']):
            output += f"Goals: {row['Goals']}\n"
        if pd.notna(row['Description']):
            output += f"Description: {row['Description']}\n"
        if pd.notna(row['Timeline Text']):
            output += f"Timeline Text: {row['Timeline Text']}\n"
        
        output += "\n-----\n\n"
    return output

def create_content_map(df):
    content_map = {}
    for _, row in df.iterrows():
        if pd.notna(row['Content Title']):
            content_title = row['Content Title'].strip()
            content_map[content_title] = {
                'Content Type': row['Content Type'].strip() if pd.notna(row['Content Type']) else '',
                'Type': row['Type'].strip() if pd.notna(row['Type']) else ''
            }
    return content_map

def update_json_with_content_info(json_data, content_map):
    special_cases = ["Identify Stakeholders", "Analyze Data", "Quick Win", "Top Tip", "Define Goal"]
    updated_data = []
    
    for item in json_data:
        content_title = item.get('Content Title', '').strip()
        if content_title in special_cases:
            content_type = "Educational Elements"
            item_type = content_title
        elif content_title in content_map:
            content_type = content_map[content_title]['Content Type']
            item_type = content_map[content_title]['Type']
        else:
            content_type = ""
            item_type = ""
        
        # Create a new OrderedDict with the specified order
        ordered_item = OrderedDict([
            ("Step", item.get("Step", "")),
            ("Step Description", item.get("Step Description", "")),
            ("Content Title", content_title),
            ("Content Type", content_type),
            ("Type", item_type),
            ("Description", item.get("Description", ""))
        ])
        updated_data.append(ordered_item)
    
    return updated_data

st.title("Blueprint Builder")

user_prompt = st.text_area("What kind of blueprint do you want to make?", value="New Hire Onboarding", height=100)

prompt_1_intro_boilerplate = """Create program/initiative blueprints for an HR/People employee initiative to be executed using the design and communications menu of options provided below. The theme of this initiative is: """

prompt_1_outro_boilerplate = """\n\nAs a first pass, we need to group these menu options into steps.\n
Create 5 Steps in TOTAL to launch the program provided.\n
For each step, pick 3-4 of the options on the menu. First, create the title of the step and write 2 sentences explaining why you are choosing the menu options you pick.\n
Then, output with the headers: Step, Step Description, Content Title, Description. (In later passes, we will flesh out the steps.)\n\n

Here's the menu of options for you to choose from this time:\n\n"""

full_prompt_2 = """Great! Now, we need to add in "Educational Elements." These are places in the plan where the HR lead needs to gather information, circulate information, or define their goals.
Here's the menu of Educational Elements:
1. Identify Stakeholders
2. Analyze Data
3. Quick Win
4. Top Tip
5. Define Goal
Please add one or two Educational Elements to each step. You will need to write your own Description."""

full_prompt_3 = """Wonderful. Now please output the full list as a JSON object with the headers: Step, Step Description, Content Title, Description.\n\n

Don't nest anything - just return a JSON object with each entity containing each of those headers."""

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the CSV and generate the output
    output = process_csv(df)

    # Process the CSV and generate the content map
    content_map = create_content_map(df)

    # Concatenate Full Prompt
    full_prompt_1 = prompt_1_intro_boilerplate + user_prompt + prompt_1_outro_boilerplate + output
    
    # Display the output in an editable text area
    prompt_1_editable = st.text_area("Prompt 1 (Editable)", value=full_prompt_1, height=500)
    prompt_2_editable = st.text_area("Prompt 2 (Editable)", value=full_prompt_2, height=200)
    prompt_3_editable = st.text_area("Prompt 3 (Editable)", value=full_prompt_3, height=200)

    if st.button("Process"):
        process_prompts()
