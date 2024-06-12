import streamlit as st
import requests
import re
import json
import pandas as pd
import openai
from typing import List, Dict, Union, Any

# Define the OpenAI model
model = "gpt-4-turbo"
parsing_model = "gpt-4-turbo"

# Define types for readability
ParsedArgument = Dict[str, str]
ResponseArguments = Union[List[ParsedArgument], List[Dict[str, Union[str, List[ParsedArgument]]]]]

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
        type_ = fields.get('fldJg8ITzVFzf8sJx', None)  # Type
        image_prompt = fields.get('fldn0VPsaEnostire', None)  # Image Prompt
        example_prompt = fields.get('fldwAUyVUHPY0pJRV', None)  # Example Prompt
        content_professional = fields.get('fldSC1pBRPq0YhVgd', None)  # Content Professional
        content_casual = fields.get('fld4YQ7TBqU4rgU2L', None)  # Content Casual
        content_direct = fields.get('fldyhq9gi63C3qrTG', None)  # Content Direct
        v1 = fields.get('fld562mr7ro6jODUz', False)  # v1
        designhuddle_link = fields.get('fldhbUkT1QboXcsbG', 'N/A')  # DesignHuddle Link
        content = fields.get('fldbiEIqHlbrdCOhf', 'N/A')  # Content (synced table)
        data.append({
            "Content Type": content_type,
            "Type": type_,
            "Example Prompt": example_prompt,
            "Image Prompt": image_prompt,
            "Content Professional": content_professional,
            "Content Casual": content_casual,
            "Content Direct": content_direct,
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

# Function to send request to OpenAI API
def send_plaintext_to_openai(plaintext):
    messages = []
    messages.append({"role": "user", "content": plaintext})
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Tools object that breaks down a response into parts
tools = [
    {
        "type": "function",
        "function": {
            "name": "fit_to_spec",
            "description": "Fits components of messages to a spec.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The name of the component, like TITLE or SUBTITLE. Match exactly with what you see, eg return HASHTAG 2 instead of HASHTAG if you see HASHTAG 2",
                    },
                    "value": {
                        "type": "string",
                        "description": "The value of the component. Make sure to preserve newlines as \n",
                    },
                },
                "required": ["key", "value"],
            },
        }
    }
]

def evaluate_character_count_and_lines(pairs_json, specs):
    evaluation_result = []

    # Create a dictionary from pairs_json for easier and case-insensitive lookup with spaces removed
    pairs_dict = {pair['key'].replace(' ', '').lower(): pair['value'] for pair in pairs_json}

    for spec_key, spec_str in specs.items():
        key = spec_key.replace('_specs', '').replace(' ', '')
        formatted_key = key.lower()

        try:
            spec = eval(spec_str)  # convert string to dictionary safely
        except Exception as e:
            spec = None
            st.error(f"Error parsing spec: {e}")

        if spec:
            value = pairs_dict.get(formatted_key, None)
            result = {
                "key": key,
                "value": value,
                "meets_line_count": False if value is None else True,
                "meets_character_criteria": False if value is None else True,
            }

            if value:
                value_lines = value.split('\n')
                lines_criteria = spec["LINES"]
                meets_lines_criteria = len(value_lines) == lines_criteria
                
                if not meets_lines_criteria:
                    result["meets_line_count"] = False
                    result["reason_code"] = f"Wrong number of lines - please rewrite this text so it is on {lines_criteria} lines, but keep the meaning the same"
                
                meets_char_criteria = True
                for i in range(lines_criteria):
                    upper_limit = spec[f"LINE_{i+1}_UPPER_LIMIT"]
                    line_length = len(value_lines[i])
                    if line_length > upper_limit:
                        result["meets_character_criteria"] = False
                        result["reason_code"] = f"Too many characters - please rewrite this text to have {line_length - upper_limit} fewer characters, but keep the meaning the same. If there are line breaks, keep them"
                        meets_char_criteria = False
                        break
                        
                    # For Subtitle and Hashtag, also check lower limit
                    if f"LINE_{i+1}_LOWER_LIMIT" in spec:
                        lower_limit = spec[f"LINE_{i+1}_LOWER_LIMIT"]
                        if line_length < lower_limit:
                            result["meets_character_criteria"] = False
                            result["reason_code"] = f"Not enough characters - please rewrite this text to add {lower_limit - line_length} more characters, but keep the meaning the same. If there are line breaks, keep them"
                            meets_char_criteria = False
                            break

                result["meets_line_count"] = meets_lines_criteria
                result["meets_character_criteria"] = meets_char_criteria

            else:
                # If the key is missing in pairs_json, it's automatically false with a reason code
                result["meets_line_count"] = False
                result["meets_character_criteria"] = False
                result["reason_code"] = "The specified key is missing from the generated content"
                
            evaluation_result.append(result)

    return evaluation_result

# Extract the tool responses from OpenAI into key-value pairs
def extract_key_value_pairs(response: Any) -> List[Dict[str, str]]:
    key_value_pairs = []

    # Check if 'choices' exists in response
    if not hasattr(response, 'choices'):
        raise ValueError("Response does not have 'choices' attribute")
    
    choices = response.choices

    for choice in choices:
        # Check if 'choice' has 'message' attribute
        if not hasattr(choice, 'message'):
            continue
        message = choice.message

        # Check if 'message' has 'tool_calls'
        if not hasattr(message, 'tool_calls'):
            continue
        tool_calls = message.tool_calls

        for call in tool_calls:
            # Check if 'call' has 'function' attribute and if 'function' has 'arguments'
            if not hasattr(call, 'function') or not hasattr(call.function, 'arguments'):
                continue
            
            # Parse the arguments from the 'function' attribute of 'call'
            function_arguments = call.function.arguments

            # Ensure function_arguments is a valid JSON string
            try:
                arguments = json.loads(function_arguments)
            except (json.JSONDecodeError, TypeError):
                continue

            if arguments is None:
                continue

            # Check if arguments contains 'tool_uses' or is directly map of key-value pairs
            if isinstance(arguments, dict) and 'tool_uses' in arguments:
                tool_uses = arguments['tool_uses']
                for tool_use in tool_uses:
                    if 'parameters' in tool_use:
                        params = tool_use['parameters']
                        if 'key' in params and 'value' in params:
                            key_value_pairs.append({
                                'key': params['key'],
                                'value': params['value']
                            })
            elif isinstance(arguments, dict):
                # If no tool_uses, try to directly extract key-value pairs from arguments
                if 'key' in arguments and 'value' in arguments:
                    key_value_pairs.append({
                        'key': arguments['key'],
                        'value': arguments['value']
                    })

    return key_value_pairs

# Function to send request to OpenAI API
def send_to_openai_with_tools(messages):
    try:
        response = openai.chat.completions.create(
            model=parsing_model,
            messages=messages,
            tools=tools
        )
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
