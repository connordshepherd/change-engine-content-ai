import streamlit as st
import requests
import re
import json
import pandas as pd

# Function to get data from the "Content Types" table using field IDs
def get_content_types_data():
    base_id = 'appbJ9Bt0YNuBafT4'
    table_name = "Content Types"
    airtable_token = st.secrets.AIRTABLE_PERSONAL_TOKEN
    headers = {
        "Authorization": f"Bearer {airtable_token}"
    }

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}?returnFieldsByFieldId=true"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.error(f"Failed to retrieve data from table {table_name}: {response.text}")
        return []

    records = response.json().get('records', [])
    
    data = []

    for record in records:
        fields = record.get('fields', {})
        content_type = fields.get('fldaCnCA1wmlTY1HR', 'N/A')  # Content Type
        type_ = fields.get('fldJg8ITzVFzf8sJx', 'N/A')  # Type
        image_prompt = fields.get('fldn0VPsaEnostire', 'N/A')  # Image Prompt
        v1 = fields.get('fld562mr7ro6jODUz', False)  # v1
        designhuddle_link = fields.get('fldhbUkT1QboXcsbG', 'N/A')  # DesignHuddle Link
        content = fields.get('fldbiEIqHlbrdCOhf', 'N/A')  # Content (synced table)
        data.append({
            "Content Type": content_type,
            "Type": type_,
            "Image Prompt": image_prompt,
            "v1": v1,
            "DesignHuddle Link": designhuddle_link,
            "Content": content
        })

    return data

# Function to get all the table data from Airtable when the user selects a table
def get_table_data(table_name):
    """
    Fetch table data from Airtable based on the given table name.
    """
    url = f"https://api.airtable.com/v0/appbJ9Bt0YNuBafT4/{table_name}"
    airtable_token = st.secrets.AIRTABLE_PERSONAL_TOKEN
    headers = {
        "Authorization": f"Bearer {airtable_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['records']
    else:
        return []

import pandas as pd

# Function to process all the data from get_table_data into a nice DataFrame
def process_table_data(table_data):
    """
    Process the table data into a DataFrame with the desired structure and sorting.
    """
    # Prepare a list of dictionaries with flattened 'fields' and additional metadata
    processed_data = []
    for record in table_data:
        fields = record.get('fields', {})
        fields['id'] = record.get('id', '')
        fields['createdTime'] = record.get('createdTime', '')
        processed_data.append(fields)
    
    # Convert the processed data to a DataFrame
    df = pd.DataFrame(processed_data)

    # Extract numerical part from 'Layout' for sorting
    df['Layout Number'] = df['Layout'].str.extract('(\d+)').astype(int)
    
    # Define desired order of columns
    desired_columns = [
        'Layout',
        'AI',
        'Title',
        'Subtitle',
        'Description (character count)',
        'Number of Questions and Answers',
        'Question (character count)',
        'Answer (character count)',
        'Topics and Answers',
        'Topic',
        'Footer (character count)',
        'Suggest Icon/Illustration/Photo',
        'Layout Number',
        'DH Layout Description',
        'id',
        'createdTime'
    ]
    
    # Compute the final columns list:
    # - Include desired columns that are present in the DataFrame
    # - Add any remaining columns that were not in the desired_columns to the end of the list
    final_columns = [col for col in desired_columns if col in df.columns] + \
                    [col for col in df.columns if col not in desired_columns]
    
    # Reorder the DataFrame columns according to the computed list
    df = df[final_columns]
    
    # Sort by 'Layout Number'
    df = df.sort_values(by='Layout Number')
    
    return df

# Loops through the Airtable data looking for character counts, either 2 integers separated with a hypen, or integers separated by slashes in parentheses
def add_specs(json_data):
    pattern_hyphen = re.compile(r'\b\d{1,2}-\d{1,2}\b')
    pattern_slash = re.compile(r'\(\d+(?:/\d+)*\)')

    # Iterate over each dictionary in the list
    for item in json_data:
        additions = {}
        # Iterate over key, value pairs
        for key, value in item.items():
            if isinstance(value, str):
                specs = None
                if pattern_hyphen.search(value):
                    specs = pattern_hyphen.findall(value)
                elif pattern_slash.search(value):
                    specs = pattern_slash.findall(value)

                if specs:
                    additions[f"{key}_specs"] = specs[0]

        # Update the item with new specs
        item.update(additions)

    return json_data
