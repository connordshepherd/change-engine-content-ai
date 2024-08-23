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

st.title("CSV Processor")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the CSV and generate the output
    output = process_csv(df)
    
    # Display the output in an editable text area
    edited_output = st.text_area("Processed Output (Editable)", value=output, height=500)
