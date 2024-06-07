import streamlit as st
import requests
import re
import json
import pandas as pd
import openai

model = "gpt-4o"

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
    pattern_hyphen = re.compile(r'\b(\d{1,2})-(\d{1,2})\b')
    pattern_slash = re.compile(r'\((\d+(?:/\d+)*)\)')

    for item in json_data:
        additions = {}
        for key, value in item.items():
            if isinstance(value, str):
                specs = None
                if (match := pattern_hyphen.search(value)) is not None:
                    lower, upper = match.groups()
                    specs = {
                        "LINES": 1,
                        "LINE_1_LOWER_LIMIT": int(lower),
                        "LINE_1_UPPER_LIMIT": int(upper)
                    }
                elif (match := pattern_slash.search(value)) is not None:
                    numbers = list(map(int, match.group(1).split('/')))
                    specs = {"LINES": len(numbers)}
                    for i, num in enumerate(numbers, 1):
                        specs[f"LINE_{i}_UPPER_LIMIT"] = num

                if specs:
                    additions[f"{key}_specs"] = json.dumps(specs)  # Store as json

        item.update(additions)

    return json_data

# Grabs the user-selected layouts from the main array
def get_selected_layouts_array(edited_json, selected_layouts):
    # Read and clean the selected_layouts
    cleaned_layouts = [int(x.strip()) for x in selected_layouts.split(',') if x.strip().isdigit()]

    layouts_array = []

    # Loop through the response object
    for entry in edited_json:
        if entry["Layout Number"] in cleaned_layouts:
            text_content = f"**Details for Layout {entry['Layout Number']}**\n"
            specs_content = {}

            for key, value in entry.items():
                if key not in ["AI", "Layout", "Preview Image", "Layout Number", "DH Layout Description", "id", "createdTime"]:
                    if value is not None:
                        if "_specs" in key:
                            specs_content[key] = value
                        else:
                            text_content += f"{key}: {value}\n"
                            
            # Add the assembled dictionary to the layouts_array with the layout key
            layouts_array.append({
                f"Layout {entry['Layout Number']}": {
                    "Text": text_content,
                    "Specs": specs_content
                }
            })

    return layouts_array

# Creates the array of prompts to send to OpenAI
def generate_prompts_array(topic, image_prompt, layouts_array):
    prompts_array = []
    
    for layout in layouts_array:
        for layout_key, layout_details in layout.items():
            prompt_messages = []
            layout_messages = []
            
            # Combine image_prompt, layout 'Text' and 'Specs'
            full_prompt = f"{image_prompt}\n\n---------\n\n{layout_details['Text']}\n\n---------\n\nHere's the topic:\n\n{topic}"
            prompt_messages.append({"role": "user", "content": full_prompt})
            
            layout_messages.append({"role": "user", "content": layout_details['Text']})
            
            specs = layout_details.get('Specs', {})
            
            prompts_array.append({"message": prompt_messages, "layout": layout_messages, "specs": specs})
    
    return prompts_array

# Function to send request to OpenAI API
def send_to_openai(messages):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
