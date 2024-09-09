import streamlit as st
import requests
import pandas as pd
import json

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

if response.status_code == 200:
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
        first_paragraph = context.split('\n')[0] if context else ''
        
        # Extract the first sentence
        first_sentence = context.split('.')[0] + '.' if context else ''

        extracted_record = {
            'Airtable Record ID': record['id'],
            'Moment Title': record['fields'].get('Moment Title', ''),
            'What': record['fields'].get('What', ''),
            'Context': context,
            'Preview Image Final': image_url,
            'Subject Line': record['fields'].get('Subject Line', ''),
            'context_first_sentence': first_sentence
        }
        extracted_data.append(extracted_record)

        # Add to pcc_plaintext
        pcc_plaintext += f"Record ID: {record['id']}\n"
        pcc_plaintext += f"Title: {extracted_record['Moment Title']}\n"
        pcc_plaintext += f"Description_short: {extracted_record['What']}\n"
        pcc_plaintext += f"More Context: {first_paragraph}\n"
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

    # Display the JSON object
    st.json(airtable_pcc)

else:
    st.error(f"Error: Unable to fetch data from Airtable. Status code: {response.status_code}")
