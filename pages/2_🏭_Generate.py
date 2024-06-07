import streamlit as st
import json
import pandas as pd
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array, send_to_openai
import openai
from typing import List, Dict, Union

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

# Extract the tool responses from OpenAI into key-value pairs
def extract_key_value_pairs(response: Dict) -> List[Dict[str, str]]:
    key_value_pairs = []
    
    # Navigate to tool_calls in choices[0].message.tool_calls
    tool_calls = response['choices'][0]['message']['tool_calls']
    
    for call in tool_calls:
        # Parse the arguments JSON string
        arguments = json.loads(call['function']['arguments'])
        
        # Extract 'key' and 'value' if available
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

        # Assemble the layouts as plaintext
        layouts_array = get_selected_layouts_array(edited_json, selected_layouts)

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
                response = send_to_openai(messages)
                layout_messages = []
                layout_messages.append({"role": "user", "content": response})
                layout_response = send_to_openai_with_tools(layout_messages)
                #pairs_json = extract_key_value_pairs(layout_response)
                
                if response:
                    st.write(f"{response}\n\n----\n\n")
                    st.write(layout_response)
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
