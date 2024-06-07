import streamlit as st
import json
import pandas as pd
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array, send_to_openai, add_specs
import openai
from typing import List, Dict, Union, Any

# Define the OpenAI model
model = "gpt-4-turbo"
parsing_model = "gpt-4-turbo"

# Define types for readability
ParsedArgument = Dict[str, str]
ResponseArguments = Union[List[ParsedArgument], List[Dict[str, Union[str, List[ParsedArgument]]]]]

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
                        "description": "The name of the component, like TITLE or SUBTITLE. Match exactly with what you see, eg return HASHTAG_2 instead of HASHTAG if you see HASHTAG_2",
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
    
    for pair in pairs_json:
        key = pair['key']
        value = pair['value']
        value_lines = value.split('\n')
        
        if key.upper() + "_specs" in specs:
            spec = eval(specs[key.upper() + "_specs"])  # convert string to dictionary
            lines_criteria = spec["LINES"]
            meets_lines_criteria = len(value_lines) == lines_criteria
            
            meets_char_criteria = True
            for i in range(lines_criteria):
                upper_limit = spec[f"LINE_{i+1}_UPPER_LIMIT"]
                meets_char_criteria = meets_char_criteria and len(value_lines[i]) <= upper_limit
                
                # For Subtitle and Hashtag, also check lower limit
                if f"LINE_{i+1}_LOWER_LIMIT" in spec:
                    lower_limit = spec[f"LINE_{i+1}_LOWER_LIMIT"]
                    meets_char_criteria = meets_char_criteria and len(value_lines[i]) >= lower_limit
            
            evaluation_result.append({
                "key": key,
                "value": value,
                "meets_line_count": meets_lines_criteria,
                "meets_character_criteria": meets_char_criteria
            })
        else:
            evaluation_result.append({
                "key": key,
                "value": value,
                "meets_line_count": "SPEC NOT FOUND",
                "meets_character_criteria": "SPEC NOT FOUND"
            })
    
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

            # Check if arguments is a dictionary and contains both 'key' and 'value'
            if isinstance(arguments, dict) and 'key' in arguments and 'value' in arguments:
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

# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

# Session State: Initialize the required session states
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None

# Streamlit UI - Title
st.title("Content Creation AI - Config")

# Retrieve data from Airtable
content_types_data = get_content_types_data()

# Extract and filter content types where v1 is true
v1_true_content_types = [item["Content Type"] for item in content_types_data if item["v1"]]

# Insert default option at the start of the list
options = ["Select a Content Type"] + v1_true_content_types

# Title for the resulting generation
topic = st.text_input("Content", "Zoom yoga session tomorrow Friday June 7")

# Add a selectbox to the Streamlit app
selected_content_type = st.selectbox("Choose a Content Type", options)

# Text input for layouts (comma-separated integers)
selected_layouts = st.text_input("Select Layouts", "1, 3")

if selected_content_type != "Select a Content Type":
    # Filter data to get the selected content type details
    selected_data = next((item for item in content_types_data if item["Content Type"] == selected_content_type), None)
    
    if selected_data:
        st.subheader("Details for: " f"{selected_content_type}")

        # Display the Image Prompt in a text area for editing
        image_prompt = st.text_area("Image Prompt", value=selected_data["Image Prompt"], height=400)

        # Load data from the table corresponding to the selected content type
        table_data = get_table_data(selected_content_type)
        
        # Process the table data into a DataFrame
        df = process_table_data(table_data)

        # Turn it into JSON
        edited_data = df
        oriented_json = edited_data.to_json(orient='records')
        edited_json = json.loads(oriented_json)

        # Add specs to the layouts data
        edited_json_with_specs = add_specs(edited_json)

        # Assemble the layouts as plaintext
        layouts_array = get_selected_layouts_array(edited_json_with_specs, selected_layouts)

        # Put the Generate button on the screen and start the logic for generating prompts and posting them to OpenAI
        if st.button("Generate"):
            # Generate prompts array
            prompts_array = generate_prompts_array(topic, image_prompt, layouts_array)
            st.write(prompts_array)

            # Go to OpenAI for each one
            n = 1
            for prompt in prompts_array:
                st.subheader(f"Generated Response {n}")
                messages = prompt['message']
                specs = prompt['specs']
                response = send_to_openai(messages)
                layout_messages = []
                layout_messages.append({"role": "user", "content": response})
                layout_response = send_to_openai_with_tools(layout_messages)
                pairs_json = extract_key_value_pairs(layout_response)
                
                if response:
                    st.write(f"{response}\n\n----\n\n")
                    st.write(pairs_json)
                    # Evaluate the character count and lines
                    evaluation = evaluate_character_count_and_lines(pairs_json, specs)
                    st.write(evaluation)
                else:
                    st.write("Failed to get a response.\n\n----\n\n")
                n = n + 1

            # Display a JSON object for debugging
            st.subheader("Debug")
            st.write("Prompts Array")
            st.write(prompts_array)
            st.write("Airtable JSON")
            st.write(edited_json)
        
    else:
        st.write("No details available for the selected content type.")
else:
    st.write("Please select a content type to see details.")
