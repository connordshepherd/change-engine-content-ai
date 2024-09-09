import streamlit as st
import requests
import pandas as pd

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
    
    # Extract the desired fields from each record
    for record in records:
        extracted_record = {
            'Airtable Record ID': record['id'],
            'Moment Title': record['fields'].get('Moment Title', ''),
            'What': record['fields'].get('What', ''),
            'Context': record['fields'].get('Context', '')
        }
        extracted_data.append(extracted_record)
    
    # Create a DataFrame from the extracted data
    df = pd.DataFrame(extracted_data)
    
    # Display the DataFrame in Streamlit
    st.dataframe(df)
else:
    st.error(f"Error: Unable to fetch data from Airtable. Status code: {response.status_code}")
