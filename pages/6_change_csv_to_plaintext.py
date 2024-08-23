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

prompt_1_intro_boilerplate = """Create program/initiative blueprints for an HR/People employee initiative to be executed using the design and communications menu of options provided below. The theme of this initiative is """""
prompt_1_outro_boilerplate = """As a first pass, we need to group these menu options into steps.\n
Create 5 Steps in TOTAL to launch the program provided.\n
For each step, pick 3-4 of the options on the menu. First, create the title of the step and write 2 sentences explaining why you are choosing the menu options you pick.\n
Then, output with the headers: Step, Step Description, Content Title, Content Type, Type, Description. (In later passes, we will flesh out the steps.)\n
Here's the menu of options:\n\n"""

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the CSV and generate the output
    output = process_csv(df)

    # Concatenate Full Prompt
    full_prompt_1 = prompt_1_intro_boilerplate + user_prompt + prompt_1_outro_boilerplate + output
    
    # Display the output in an editable text area
    edited_output = st.text_area("Processed Output (Editable)", value=full_prompt_1, height=500)
