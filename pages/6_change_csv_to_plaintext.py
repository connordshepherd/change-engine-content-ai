import streamlit as st
import pandas as pd
import io

def process_csv(df):
    output = ""
    for _, row in df.iterrows():
        output += f"Content Title:\n{row['Content Title']}\n\n"
        output += f"Goals:\n{row['Goals']}\n\n"
        output += f"Content Type:\n{row['Content Type']}\n\n"
        output += f"Type:\n{row['Type']}\n\n"
        output += f"Description:\n{row['Description']}\n\n"
        output += f"Timeline Text:\n{row['Timeline Text']}\n\n"
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

    # Option to download the edited output
    if st.button("Download Edited Output"):
        buffer = io.StringIO()
        buffer.write(edited_output)
        buffer.seek(0)
        st.download_button(
            label="Click here to download",
            data=buffer,
            file_name="processed_output.txt",
            mime="text/plain"
        )
