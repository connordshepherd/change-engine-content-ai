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

    st.write("Running prompt 1 - Steps")
    # Process prompt 1
    messages.append({"role": "user", "content": prompt_1_editable})
    response_1 = call_openai(messages)
    messages.append({"role": "assistant", "content": response_1})
    #st.write("First Response")
    #st.write(response_1)

    st.write("Running prompt 1 - Communications")
    # Process prompt 1 Comms
    messages.append({"role": "user", "content": prompt_1_comms_editable})
    response_1_comms = call_openai(messages)
    messages.append({"role": "assistant", "content": response_1_comms})
    #st.write("Comms Response")
    #st.write(response_1_comms)

    st.write("Running prompt 1 - Designs")
    messages.append({"role": "user", "content": prompt_1a_editable})
    response_1a = call_openai(messages)
    messages.append({"role": "assistant", "content": response_1a})
    #st.write("Designs Response")
    #st.write(response_1a)
    
    st.write("Running prompt 2")
    # Process prompt 2
    messages.append({"role": "user", "content": prompt_2_editable})
    response_2 = call_openai(messages)
    messages.append({"role": "assistant", "content": response_2})
    #st.write(response_2)
    
    st.write("Running prompt 3")
    # Process prompt 3
    messages.append({"role": "user", "content": prompt_3_editable})
    response_3 = call_openai(messages)
    messages.append({"role": "assistant", "content": response_3})
    #st.write(response_3)
    
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
        #st.write("Original JSON")
        #st.json(json_response)

        # Update the JSON response with Content Type and Type
        updated_json = update_json_with_content_info(json_response, content_map)
        #st.write("Updated JSON")
        #st.json(updated_json)
        
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
    # Split the dataframe based on 'Type'
    df_communication = df[df['Type'] == 'Communication']
    df_design = df[df['Type'] == 'Design']
    
    # Process Communication dataframe
    output_communication = ""
    for index, row in df_communication.iterrows():
        output_communication += f"ROW {index + 1}\n"
        if pd.notna(row['Content Title']):
            output_communication += f"Content Title: {row['Content Title']}\n"
        if pd.notna(row['Goals']):
            output_communication += f"Goals: {row['Goals']}\n"
        if pd.notna(row['Description']):
            output_communication += f"Description: {row['Description']}\n"
        if pd.notna(row['Type']):
            output_communication += f"Type: {row['Type']}\n"
        if pd.notna(row['Timeline Text']):
            output_communication += f"Timeline Text: {row['Timeline Text']}\n"
        output_communication += "\n-----\n\n"
    
    # Process Design dataframe
    output_design = ""
    for index, row in df_design.iterrows():
        output_design += f"ROW {index + 1}\n"
        if pd.notna(row['Content Title']):
            output_design += f"Content Title: {row['Content Title']}\n"
        if pd.notna(row['Goals']):
            output_design += f"Goals: {row['Goals']}\n"
        if pd.notna(row['Description']):
            output_design += f"Description: {row['Description']}\n"
        if pd.notna(row['Type']):
            output_design += f"Type: {row['Type']}\n"
        if pd.notna(row['Timeline Text']):
            output_design += f"Timeline Text: {row['Timeline Text']}\n"
        output_design += "\n-----\n\n"
    
    return output_communication, output_design

def normalize_string(s):
    # Convert to lowercase and remove special characters
    return re.sub(r'[^a-z0-9]', '', s.lower())

def create_content_map(df):
    content_map = {}
    for _, row in df.iterrows():
        if pd.notna(row['Content Title']):
            content_title = row['Content Title'].strip()
            normalized_title = normalize_string(content_title)
            content_map[normalized_title] = {
                'Content Title': content_title,  # Keep the original title
                'Content Type': row['Content Type'].strip() if pd.notna(row['Content Type']) else '',
                'Type': row['Type'].strip() if pd.notna(row['Type']) else ''
            }
    return content_map

def update_json_with_content_info(json_data, content_map):
    special_cases = ["Identify Stakeholders", "Analyze Data", "Quick Win", "Top Tip", "Define Goal"]
    updated_data = []
    
    for item in json_data:
        content_title = item.get('Content Title', '').strip()
        normalized_title = normalize_string(content_title)
        
        if content_title in special_cases:
            content_type = content_title
            item_type = "Educational Elements"
        elif normalized_title in content_map:
            content_type = content_map[normalized_title]['Content Type']
            item_type = content_map[normalized_title]['Type']
            # Use the original content title from the map
            content_title = content_map[normalized_title]['Content Title']
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
Description: Implement a system to track the effectiveness of the referral program, including metrics and employee feedback. Regularly review the program’s performance and make necessary adjustments to improve its efficiency and effectiveness.
</EXAMPLE FORMAT>"""

prompt_1a_comms_boilerplate = """Great! Now we're going to begin adding elements to each step, from our database of element options. 

For each step, pick exactly 2 of the options on the below menu of Communications. 
In your output you'll need to repeat the Steps and Step Descriptions exactly from before.
Your full output will have these headers: Step, Step Description, Content Title, Description.\n\n

Here's the menu of Communications options for you to choose from this time. Please only use each option ONCE in your plan - if you use an option in one step you can't use it in other steps.\n\n Here's the list:\n\n"""

prompt_1a_intro_boilerplate = """Awesome. For each step, next please add two of the options on the below menu of Designs. Don't repeat any options - use each only once in your entire plan. You can't use the seme element in different steps, so plan carefully.\n
Just like before, output with the headers: Step, Step Description, Content Title, Description.\n\n"""

full_prompt_2 = """Great! Now, we need to add in "Educational Elements." These are places in the plan where the HR lead needs to gather information, circulate information, or define their goals.
Here's the menu of Educational Elements:
1. Identify Stakeholders
2. Analyze Data
3. Quick Win
4. Top Tip
5. Define Goal
Please add two Educational Elements to each step. You will need to write your own Description."""

full_prompt_3 = """Wonderful. Now please output the full list as a JSON object with the headers: Step, Step Description, Content Title, Description.\n\n

Don't nest anything - just return a JSON object with each entity containing each of those headers."""

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the CSV and generate the output
    output_communication, output_design = process_csv(df)

    # Process the CSV and generate the content map
    content_map = create_content_map(df)

    # Concatenate Full Prompt 1
    full_prompt_1 = prompt_1_intro_boilerplate + user_prompt + prompt_1_outro_boilerplate

    # Concatenate Steps Prompt 1
    full_prompt_1_comms = prompt_1a_comms_boilerplate + output_communication

    # Concatenate Full Prompt 1a
    full_prompt_1a = prompt_1a_intro_boilerplate + output_design
    
    # Display the output in an editable text area
    prompt_1_editable = st.text_area("Prompt 1 Steps (Editable)", value=full_prompt_1, height=200)
    prompt_1_comms_editable = st.text_area("Prompt 1 Communications (Editable)", value=full_prompt_1_comms, height=400)
    prompt_1a_editable = st.text_area("Prompt 1a Designs (Editable)", value=full_prompt_1a, height=400)
    prompt_2_editable = st.text_area("Prompt 2 (Editable)", value=full_prompt_2, height=200)
    prompt_3_editable = st.text_area("Prompt 3 (Editable)", value=full_prompt_3, height=200)

    if st.button("Process"):
        process_prompts()
