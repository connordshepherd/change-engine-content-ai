import streamlit as st
import pandas as pd
import io

def process_csv(df):
    output = ""
    for index, row in df.iterrows():
        output += f"ROW {index + 1}\n"  # Adding row number
        output += f"Content Title: {row['Content Title']}\n"
        output += f"Goals: {row['Goals']}\n"
        output += f"Content Type: {row['Content Type']}\n"
        output += f"Type: {row['Type']}\n"
        output += f"Description: {row['Description']}\n"
        output += f"Timeline Text: {row['Timeline Text']}\n\n"
        output += "-----\n\n"
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
