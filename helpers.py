import streamlit as st
import requests
import re
import json
import pandas as pd
import openai
from typing import List, Dict, Union, Any, Tuple
from io import BytesIO
from PIL import Image

# Define the OpenAI model
model = "gpt-4-turbo"
parsing_model = "gpt-4o"

# Define types for readability
ParsedArgument = Dict[str, str]
ResponseArguments = Union[List[ParsedArgument], List[Dict[str, Union[str, List[ParsedArgument]]]]]

fewshot_prompt = """The layout will have keys: return the keys in your response, separated from the values by a colon.

You will likely make a few versions: here's how I'd like you to return a response.

For example, let's say you were asked to write some text welcoming Connor as CFO, and asked to create 3 variations, and given this example layout:

**Details for Layout 2** # EXAMPLE layout
Title: 3 lines to put on the zoom background, every line is maximum 10 characters each (10/10/10) Hashtag 1: A hashtag of between 15-21 characters 
Hashtag 2: A hashtag of between 15-21 characters

In that case, you'd return something like:

Title: Welcome 
New CFO
Connor!
Title: Our 
New 
CFO
Title: New 
CFO 
Connor

Hashtag 1: #WelcomeToTheTeam
Hashtag 1: #FinanceWizard
Hashtag 1: #NewWorldofFinance

Hashtag 2: #StrongerTogether
Hashtag 2: #FinanceTeam
Hashtag 2: #MoneyMoves

As you can see, we return the response with keys separated from values by a colon. The keys are grouped together. No values are shared.

Now that we've finished the example, let's move on to the actual request. Here's the actual layout I'd like you to use:"""

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

# Function to get all client names and their associated tone prompts from Airtable
def get_client_data():
    """
    Fetch client names and their associated tone prompts from Airtable.
    """
    url = "https://api.airtable.com/v0/appbJ9Bt0YNuBafT4/Client%20AI%20+%20Automation"
    airtable_token = st.secrets.AIRTABLE_PERSONAL_TOKEN
    headers = {
        "Authorization": f"Bearer {airtable_token}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        records = response.json()['records']
        client_data = {}
        for record in records:
            fields = record['fields']
            if 'Customer Name' in fields and 'AI Brand Tone Prompt' in fields:
                client_data[fields['Customer Name']] = fields['AI Brand Tone Prompt']
        return client_data
    else:
        return {}

# Function to get all the Layout table data from Airtable when the user selects a table
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

# Function to make the little image selection table on the page
def prepare_layout_selector_data(table_data):
    layout_selector_data = []
    for record in table_data:
        layout = record["fields"]["Layout"]
        image_url = record["fields"]["Preview Image"][0]["thumbnails"]["large"]["url"]
        layout_selector_data.append({"Layout": layout, "Image": image_url, "Enabled": False})

    layout_selector_df = pd.DataFrame(layout_selector_data)
    layout_selector_df['Layout Number'] = layout_selector_df['Layout'].str.extract('(\d+)').astype(int)
    layout_selector_df = layout_selector_df.sort_values(by='Layout Number')

    return layout_selector_df

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

# Creates the array of prompts to send to OpenAI
def generate_prompts_array_with_variations(topic, image_prompt, layouts_array, variations):
    prompts_array = []

    for layout in layouts_array:
        for layout_key, layout_details in layout.items():
            prompt_messages = []
            layout_messages = []

            # Combine image_prompt, layout 'Text' and 'Specs'
            full_prompt = f"{image_prompt}\n\n{fewshot_prompt}\n\n---------\n\n{layout_details['Text']}\n\n---------\n\nHere's the topic:\n\n{topic}\n\nPlease make {variations} full variations. Each one should have all the keys you see in the layout description above."
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
            lines_criteria = spec["LINES"]
            result = {
                "key": key,
                "value": value,
                "meets_line_count": False if value is None else True,
                "meets_character_criteria": False if value is None else True,
                "lines_criteria": lines_criteria  # add this information to the result
            }

            if value:
                value_lines = value.split('\n')
                meets_lines_criteria = len(value_lines) == lines_criteria

                if not meets_lines_criteria:
                    result["meets_line_count"] = False
                    result["reason_code"] = f"Wrong number of lines - please rewrite this text so it is on {lines_criteria} lines, but keep the general meaning the same:"
                
                meets_char_criteria = True
                for i in range(lines_criteria):
                    upper_limit = spec[f"LINE_{i+1}_UPPER_LIMIT"]
                    line_length = len(value_lines[i])
                    if line_length > upper_limit:
                        result["meets_character_criteria"] = False
                        result["reason_code"] = f"Say something like this, with only 2 words. You can change the meaning if you need to. If you want to remove a word, do it. This is for a graphic design, so we're just trying to communicate the general theme. It doesn't need to be exact. Return your new text, on {lines_criteria} lines."
                        meets_char_criteria = False
                        break
                        
                    # For Subtitle and Hashtag, also check lower limit
                    if f"LINE_{i+1}_LOWER_LIMIT" in spec:
                        lower_limit = spec[f"LINE_{i+1}_LOWER_LIMIT"]
                        if line_length < lower_limit:
                            result["meets_character_criteria"] = False
                            result["reason_code"] = f"Add 1 word to this text. If there are line breaks, keep them. Return only the adjusted text, on {lines_criteria} lines."
                            meets_char_criteria = False
                            break

                result["meets_line_count"] = meets_lines_criteria
                result["meets_character_criteria"] = meets_char_criteria

            else:
                # If the key is missing in pairs_json, it's automatically false with a reason code
                result["meets_line_count"] = False
                result["meets_character_criteria"] = False
                result["reason_code"] = f"The specified key is missing from the generated content, which should be formatted with {lines_criteria} lines."
                
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

# Define the fix_problems function
def fix_problems(evaluation: List[Dict[str, Any]]) -> List[Tuple[str, str, int]]:
    result = []
    reasons = []
    line_counts = []
    for item in evaluation:
        if "reason_code" in item:
            text = item.get("value", "")
            reason_code = item["reason_code"]
            formatted_problem = f"{reason_code}\n\n---------\n\n{text}"
            result.append(formatted_problem)
            reasons.append(item["key"])  # Append the key to track which item we are fixing
            line_counts.append(item.get("lines_criteria", "N/A"))  # Append line count criteria
    return result, reasons, line_counts

def group_values(pairs_json):
    grouped = {}
    
    for pair in pairs_json:
        key = pair['key']
        value = pair['value']
        
        if key not in grouped:
            grouped[key] = {'key': key, 'values': {}}
        
        current_index = len(grouped[key]['values'])
        grouped[key]['values'][current_index] = value
    
    return list(grouped.values())

# Define the fix_problems function
def fix_problems(evaluation: List[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str], List[int]]:
    result = []
    reasons = []
    keys = []
    line_counts = []
    
    for item in evaluation:
        key = item["key"]
        for idx, value in item["values"].items():
            if "reason_code" in value:
                text = value.get("value", "")
                reason_code = value["reason_code"]
                formatted_problem = f"{reason_code}\n\n---------\n\n{text}"
                result.append(formatted_problem)
                reasons.append(key)  # Append the key to track which item we are fixing
                keys.append(idx)  # Append the index within the values dictionary
                line_counts.append(value.get("lines_criteria", "N/A"))  # Append line count criteria
    
    return result, reasons, keys, line_counts

# Updates into the grouped object
def update_grouped(grouped: List[Dict[str, Any]], key: str, index: str, new_value: str) -> bool:
    for item in grouped:
        if item["key"] == key:
            if index in item["values"]:
                item["values"][index] = new_value
                return True
    return False

# Run the character count evaluation on an object with multiple entries
# Run the character count evaluation on an object with multiple entries
def evaluate_character_count_and_lines_of_group(grouped, specs):
    def evaluate_single_pair(value, spec):
        result = {
            "value": value,
            "meets_line_count": False if value is None else True,
            "meets_character_criteria": False if value is None else True,
        }
    
        if value:
            value_lines = value.split('\n')
            lines_criteria = spec["LINES"]
            meets_lines_criteria = len(value_lines) == lines_criteria
            result.update({"lines_criteria": lines_criteria})
    
            if not meets_lines_criteria:
                result["meets_line_count"] = False
                result["reason_code"] = f"Wrong number of lines - please rewrite this text so it is on {lines_criteria} lines, but keep the general meaning the same:"
            
            meets_char_criteria = True
            for i in range(lines_criteria):
                if i < len(value_lines):
                    upper_limit = spec[f"LINE_{i + 1}_UPPER_LIMIT"]
                    line_length = len(value_lines[i])
                    if line_length > upper_limit:
                        result["meets_character_criteria"] = False
                        result["reason_code"] = f"Say something like this, with only 2 words. You can change the meaning if you need to. If you want to remove a word, do it. This is for a graphic design, so we're just trying to communicate the general theme. It doesn't need to be exact. Return your new text, on {lines_criteria} lines."
                        meets_char_criteria = False
                        break
                        
                    if f"LINE_{i + 1}_LOWER_LIMIT" in spec:
                        lower_limit = spec[f"LINE_{i + 1}_LOWER_LIMIT"]
                        if line_length < lower_limit:
                            result["meets_character_criteria"] = False
                            result["reason_code"] = f"Add 1 word to this text. If there are line breaks, keep them. Return only the adjusted text, on {lines_criteria} lines."
                            meets_char_criteria = False
                            break
                else:
                    # Handle the case where there are fewer lines than required
                    result["meets_character_criteria"] = False
                    result["reason_code"] = f"Insufficient number of lines. The required number of lines is {lines_criteria}, but the value only has {len(value_lines)} lines."
                    meets_char_criteria = False
                    break
    
            result["meets_line_count"] = meets_lines_criteria
            result["meets_character_criteria"] = meets_char_criteria
    
        else:
            result["meets_line_count"] = False
            result["meets_character_criteria"] = False
            result["reason_code"] = f"The specified key is missing from the generated content, which should be formatted with the required number of lines."
            
        return result

    overall_result = []

    for item in grouped:
        key = item["key"]
        formatted_key = key.replace(' ', '').lower()
        spec_key = f"{formatted_key}_specs"

        spec = None
        for spec_key, spec_str in specs.items():
            if formatted_key in spec_key.replace(' ', '').lower():
                try:
                    spec = eval(spec_str)  # Convert string to dictionary safely
                    break
                except Exception as e:
                    print(f"Error parsing spec for key {key}: {e}")

        if spec:
            evaluated_values = {}
            for idx, value in item["values"].items():
                evaluated_values[idx] = evaluate_single_pair(value, spec)
            overall_result.append({"key": key, "values": evaluated_values})
        else:
            print(f"No spec found for key {key}")

    return overall_result

def open_page(url):
    open_script = """
    <script type="text/javascript">
        window.open('%s', '_blank').focus();
    </script>
    """ % url
    html(open_script)

def assemble_prompt(company_tone_style, image_prompt, topic, variations, layouts_array, content_professional=None, content_casual=None, content_direct=None):
    layouts_text = ""
    response_structure = "Use this structure for the response:\nVariation n:\n"
    
    for layout in layouts_array:
        for layout_name, layout_details in layout.items():
            layouts_text += f"{layout_details['Text']}\n"
            layouts_text += "\n"
            
            # Extract field names for the response structure
            field_names = [line.split(":")[0].strip() for line in layout_details['Text'].split("\n") if ":" in line]
            response_structure += "\n".join(field_names) + "\n"
    
    # Concatenating content fields with newlines
    content_parts = []
    if content_professional:
        content_parts.append(content_professional)
    if content_casual:
        content_parts.append(content_casual)
    if content_direct:
        content_parts.append(content_direct)
    
    concatenated_content = "\n\n".join(content_parts)

    prompt = f"""{company_tone_style}

{image_prompt}
----
The topic is: {topic}. Come up with {variations} variations. Never output in code.
----

For each variation include:

{layouts_text}

{concatenated_content}

----

{response_structure}"""

    return prompt

def get_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))
