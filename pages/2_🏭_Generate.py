import streamlit as st
import json
import pandas as pd
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools, send_plaintext_to_openai
import openai
from typing import List, Dict, Union, Any, Tuple

# Define the OpenAI model
model = "gpt-4o"
parsing_model = "gpt-4-turbo"

# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

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

# Session State: Initialize the required session states
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None

# Streamlit UI - Title
st.title("Content Creation AI")

# Retrieve data from Airtable
content_types_data = get_content_types_data()

# Extract and filter content types where v1 is true
v1_true_content_types = [item["Content Type"] for item in content_types_data if item["v1"]]

# Insert default option at the start of the list
options = ["Select a Content Type"] + v1_true_content_types

# Add a selectbox to the Streamlit app
selected_content_type = st.selectbox("Choose a Content Type", options)

# Text input for layouts (comma-separated integers)
selected_layouts = st.text_input("Select Layouts", "1, 3")

# Create an input box for company name
company_name = st.text_input("Company", "Global App Testing")
# TODO make this a dropdown

# Create an input box for company description
test_description = "You are Employee Experience Manager at an unnamed nonprofit company, of about 100 to 5,000 employees. This company is a hybrid work environment. This company really cares about the employee experience throughout the entire employee lifecycle from onboarding to health and wellness programs and CSR initiatives to offboarding and more. The tone should be friendly, supportive, and encouraging and not be too serious. Always refer to the HR Team as the People Team instead."
company_tone_style = st.text_area("Company Tone and Style Guide", value=test_description, height=100)

if selected_content_type != "Select a Content Type":
    # Filter data to get the selected content type details
    selected_data = next((item for item in content_types_data if item["Content Type"] == selected_content_type), None)
    
    if selected_data:
        st.subheader("Details for: " f"{selected_content_type}")

        # Display all the prompts from Content Types
        topic = st.text_area("Prompt", height=100)
        example_value = selected_data["Example Prompt"]
        st.write(f"Example Prompts: {example_value}")
        image_prompt = st.text_area("Image Prompt", value=selected_data["Image Prompt"], height=200)
        content_professional = st.text_area("Content (Professional)", value=selected_data["Content Professional"], height=200)
        content_casual = st.text_area("Content (Casual)", value=selected_data["Content Casual"], height=200)
        content_direct = st.text_area("Content (Direct)", value=selected_data["Content Direct"], height=200)

        # Put the Generate button on the screen and start the logic for generating prompts and posting them to OpenAI
        if st.button("Generate"):
            results = []  # Initialize a list to hold the results
        
            # First check and process image_prompt if not null
            if image_prompt:
        
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
                # st.write(layouts_array)
        
                # Generate prompts array for image_prompt
                prompts_array = generate_prompts_array(topic, image_prompt, layouts_array)
        
                # Go to OpenAI for each one
                for prompt, layout in zip(prompts_array, layouts_array):
                    layout_key = list(layout.keys())[0]  # Extract the layout key (e.g., "Layout 1")
                    
                    for retry in range(3):  # Retry up to 3 times
                        #st.subheader(f"Images - Generated Response for {layout_key}")
                        messages = prompt['message']
                        specs = prompt['specs']
                        response = send_to_openai(messages)
                        if not response:
                            # st.write(f"Failed to get a response. Retrying {retry + 1}/3...")
                            continue  # Retry without incrementing n
        
                        tool_call_prompt = "Please extract relevant entities (Title, Subtitle and any others) from the below text." + "\n\n---------------\n\n" + response
                        layout_messages = [{"role": "user", "content": response}]
                        layout_response = send_to_openai_with_tools(layout_messages)
                        pairs_json = extract_key_value_pairs(layout_response)
                    
                        # Process and evaluate the response
                        iterations = 0
                        missing_key = False  # Flag to indicate missing key
                    
                        while iterations < 5:  # Attempt to fix and ensure criteria max 5 times
                            evaluation = evaluate_character_count_and_lines(pairs_json, specs)
                            # st.write(evaluation)
                    
                            if not any("reason_code" in item for item in evaluation):
                                # st.write(f"Completed in {iterations} iterations.")
                                break  # Break the fixing loop since all criteria are met
                    
                            if any("reason_code" in item and "The specified key is missing" in item["reason_code"] for item in evaluation):
                                missing_key = True
                                break  # Break the fixing loop to retry with a new generation
        
                            problems, keys_to_fix, line_counts = fix_problems(evaluation)
                            #st.subheader("Fix Problems")
                            for problem, key, line_count in zip(problems, keys_to_fix, line_counts):
                                # st.write(f"Fixing problem for {key}: {problem}")
                                prompt_with_context = f"{problem}\n\nPlease return your new text, on {line_count} lines."
                                fixed_response = send_plaintext_to_openai(prompt_with_context)
                                # st.write(fixed_response)
                    
                                for pair in pairs_json:
                                    if pair["key"].upper() == key.upper():
                                        pair["value"] = fixed_response
        
                                #st.write(pairs_json)
                    
                            iterations += 1
                    
                        if missing_key:
                            st.write(f"Missing key detected. Retrying {retry + 1}/3...")
                        else:
                            break  # Successfully completed, no need to retry
                    else:
                        st.write(f"Failed to process prompt for {layout_key} after 3 retries.")
        
                    # Collect and format the final output
                    result = f"Generated Response for {layout_key}:\n"
                    for pair in pairs_json:
                        result += f"{pair['key']}: {pair['value']}\n"
                    result += "-" * 30 + "\n"
                    results.append(result)  # Append the formatted result to the list
        
            # Now loop through other prompts (content_professional, content_casual, content_direct) and apply different logic
            other_prompts = [
                ("Content Professional", content_professional),
                ("Content Casual", content_casual),
                ("Content Direct", content_direct)
            ]
            
            for prompt_name, prompt_content in other_prompts:
                if prompt_content:
                    st.subheader(f"Generated Response for {prompt_name}")
                    other_prompt_messages = []
                    other_prompt = company_tone_style + "\n\n--------------\n\n" + topic + "\n\n-----------\n\n" + prompt_content
                    other_prompt_messages.append({"role": "user", "content": other_prompt})
                    response = send_to_openai(other_prompt_messages)
                    st.write(response)
        
            # Display all accumulated results
            st.subheader("All Generated Responses")
            for result in results:
                st.text(result)
        
            # Display a JSON object for debugging
            st.subheader("Debug")
        
    else:
        st.write("No details available for the selected content type.")
else:
    st.write("Please select a content type to see details.")
