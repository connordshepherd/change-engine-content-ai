import streamlit as st
import pandas as pd
import io
import numpy as np

def process_csv(df):
    output = ""
    for index, row in df.iterrows():
        output += f"ROW {index + 1}\n"  # Adding row number
        
        # Only include non-null values
        if pd.notna(row['Content Title']):
            output += f"Content Title: {row['Content Title']}\n"
        if pd.notna(row['Goals']):
            output += f"Goals: {row['Goals']}\n"
        if pd.notna(row['Content Type']):
            output += f"Content Family: {row['Content Type']}\n"
        if pd.notna(row['Type']):
            output += f"Content Type: {row['Type']}\n"
        if pd.notna(row['Description']):
            output += f"Description: {row['Description']}\n"
        if pd.notna(row['Timeline Text']):
            output += f"Timeline Text: {row['Timeline Text']}\n"
        
        output += "\n-----\n\n"
    return output

st.title("Blueprint Builder")

user_prompt = st.text_area("What kind of blueprint do you want to make?", value="New Hire Onboarding", height=100)

prompt_1_intro_boilerplate = """Create program/initiative blueprints for an HR/People employee initiative to be executed using the design and communications menu of options provided below. The theme of this initiative is: """

prompt_1_outro_boilerplate = """\n\nAs a first pass, we need to group these menu options into steps.\n
Create 5 Steps in TOTAL to launch the program provided.\n
For each step, pick 3-4 of the options on the menu. First, create the title of the step and write 2 sentences explaining why you are choosing the menu options you pick.\n
Then, output with the headers: Step, Step Description, Content Title, Content Family, Content Type, Description. (In later passes, we will flesh out the steps.)\n
Here's the menu of options:\n\n"""

prompt_2_boilerplate = """Great! Now, we need to add in "Educational Elements." These are places in the plan where the HR lead needs to gather information, circulate information, or define their goals.
Here's the menu of Educational Elements:
1. Identify Stakeholders
2. Analyze Data
3. Quick Win
4. Top Tip
5. Define Goal
Please add one or two Educational Elements to each step. Keep in mind that the Educational Element, in the data structure, is a Content Type. The name of the Educational Element you choose will be a Content Title. You will need to write your own Description."""

full_prompt_3 = """Wonderful. Now please output the full list as a JSON object with the headers: Step, Step Description, Content Title, Content Family, Content Type, Description."""

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the CSV and generate the output
    output = process_csv(df)

    # Concatenate Full Prompt
    full_prompt_1 = prompt_1_intro_boilerplate + user_prompt + prompt_1_outro_boilerplate + output
    
    # Display the output in an editable text area
    prompt_1_editable = st.text_area("Prompt 1 (Editable)", value=full_prompt_1, height=500)
    prompt_2_editable = st.text_area("Prompt 2 (Editable)", value=full_prompt_2, height=200)
    prompt_3_editable = st.text_area("Prompt 3 (Editable)", value=full_prompt_3, height=200)
