import streamlit as st
import json
import pandas as pd
import requests

from io import BytesIO
from PIL import Image
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools
from helpers import send_plaintext_to_openai, get_client_data, prepare_layout_selector_data
import openai
from typing import List, Dict, Union, Any, Tuple


#------ v2 HELPERS ---------

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

#------ v2 HELPERS ---------




# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

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

# Retrieve client data from Airtable
client_data = get_client_data()

# Create a selectbox for company name
company_name_list = sorted(client_data.keys())
selected_company_name = st.selectbox("Company", options=["Select a Company"] + company_name_list)

# Display the AI Brand Tone Prompt for the selected company
if selected_company_name and selected_company_name != 'Select a Company':
    company_tone_style = st.text_area("Company Tone and Style Guide", value=client_data[selected_company_name], height=100)
else:
    company_tone_style = st.text_area("Company Tone and Style Guide", value="", height=100)

# Set a number of variations, ie a number of times to run the content loop
variations = st.number_input("Number of Variations", 1, 10)

def get_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

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

            # Prepare layout selector data using the helper function
            layout_selector_data = prepare_layout_selector_data(table_data)

            # Define column configurations
            column_config = {
                "Layout": st.column_config.Column("Layout", disabled=True),
                "Image": st.column_config.ImageColumn("Preview Image", help="Thumbnail previews from Airtable"),
                "Enabled": st.column_config.CheckboxColumn("Enabled", help="Enable this layout?", default=False),
                "Layout Number": st.column_config.Column("Layout Number", disabled=True)
            }

            image_selector_df = st.data_editor(data=layout_selector_data, column_config=column_config, hide_index=True)
            selected_images = image_selector_df[image_selector_df["Enabled"]]
            selected_layouts_numbers = selected_images['Layout Number'].tolist()
            selected_layouts = ", ".join(map(str, selected_layouts_numbers))
            st.write(f"Selected Layouts: {selected_layouts}")

            # Assemble the layouts as plaintext
            layouts_array = get_selected_layouts_array(edited_json_with_specs, selected_layouts)
            # st.write(layouts_array)


        # This button starts the generation loop.
        if st.button("Generate"):
            all_results = ""  # Initialize a single string to hold all results

            for _ in range(variations):
                results = []  # Initialize a list to hold the results

                # This starts the IMAGE SUBLOOP. Images are complicated because they have stringent character length requirements. 
                # Only FAQ images are exempt - they are actually too complex to map here.
                if image_prompt:

                    # Generate prompts array for image_prompt
                    prompts_array = generate_prompts_array(topic, image_prompt, layouts_array)

                    # Go to OpenAI for each one
                    for prompt, layout in zip(prompts_array, layouts_array):
                        layout_key = list(layout.keys())[0]  # Extract the layout key (e.g., "Layout 1")

                        # Check if content type is 'FAQ'
                        if selected_content_type == "FAQ":
                            # Generate response and add directly to results
                            messages = prompt['message']
                            response = send_to_openai(messages)
                            all_results += f"Generated Response for {layout_key}:\n{response}\n\n"
                            st.text(all_results)
                            continue  # Skip rest of the iteration
                        
                        for retry in range(3):  # Retry up to 3 times
                            # st.subheader(f"Images - Generated Response for {layout_key}")
                            messages = prompt['message']
                            specs = prompt['specs']
                            response = send_to_openai(messages)
                            # st.write(response)
                            if not response:
                                # st.write(f"Failed to get a response. Retrying {retry + 1}/3...")
                                continue  # Retry without incrementing n

                            tool_call_prompt = "Please extract relevant entities (Title, Subtitle and any others) from the below text." + "\n\n---------------\n\n" + response
                            layout_messages = [{"role": "user", "content": response}]
                            layout_response = send_to_openai_with_tools(layout_messages)
                            pairs_json = extract_key_value_pairs(layout_response)

                            iterations = 0
                            retry = 0
                            missing_key = False  # Flag to indicate missing key
                            max_retries = 3
                            grouped = group_values(pairs_json)
                            st.write("Grouped", grouped)
                            st.write("Specs", specs)
                            
                            while retry < max_retries:
                                while iterations < 5:  # Attempt to fix and ensure criteria max 5 times
                                    # Evaluate the grouped values based on specifications
                                    evaluation = evaluate_character_count_and_lines_of_group(grouped, specs)
                                    st.write("Evaluation", evaluation)
                            
                                    # Break if all criteria are met and no reason_code is present in the evaluation
                                    if not any("reason_code" in value for item in evaluation for value in item['values'].values()):
                                        st.write(f"Completed in {iterations} iterations.")
                                        break  # Break the fixing loop since all criteria are met
                            
                                    # Check for missing key issue
                                    if any("reason_code" in value and "The specified key is missing" in value["reason_code"] for item in evaluation for value in item['values'].values()):
                                        missing_key = True
                                        break  # Break the fixing loop to retry with a new generation
                            
                                    # Fix identified problems systematically
                                    problems, keys_to_fix, indices_to_fix, line_counts = fix_problems(evaluation)
                                    st.subheader("Fix Problems")
                                    for problem, key, index, line_count in zip(problems, keys_to_fix, indices_to_fix, line_counts):
                                        st.write(f"Fixing problem for {key} at index {index}: {problem}")
                                        prompt_with_context = f"{problem}\n\nPlease return your new text, on {line_count} lines."
                                        # Send request to OpenAI for generating fix
                                        fixed_response = send_plaintext_to_openai(prompt_with_context)
                                        st.write(f"Fixed response for {key} at index {index}: {fixed_response}")
                            
                                        # Update the grouped structure with fixed_response
                                        updated = update_grouped(grouped, key, index, fixed_response)
                                        st.write("Updated", updated)
                                        st.write("Updated Grouped", grouped)
                            
                                        if not updated:
                                            st.write(f"Could not update value for {key} at index {index} with content {fixed_response}")
                            
                                    iterations += 1
                            
                                # Retry if a missing key issue was detected
                                if missing_key:
                                    retry += 1
                                    st.write(f"Missing key detected. Retrying {retry}/{max_retries}...")
                                    iterations = 0  # Reset the iterations for a fresh start
                                else:
                                    break
                            
                            # Final output after processing
                            st.write("Final grouped", grouped)

                        # Collect and format the final output
                        result = f"Generated Response for {layout_key}:\n"

                        # Iterate over each group and format the key-value pairs correctly
                        for group in grouped:
                            key = group['key']
                            values = group['values']
                            for index, value in values.items():
                                result += f"{key} {index}: {value}\n"
                        
                        result += "-" * 30 + "\n"
                        results.append(result)  # Append the formatted result to the list

                # Append all accumulated results to the main results string
                for result in results:
                    all_results += result
                    st.text(all_results)

                # ------ The above is the end of the IMAGE SUBLOOP.

                # Now we do the CONTENT SUBLOOP. We work through other prompts (content_professional, content_casual, content_direct) and apply different logic.
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
                        all_results += f"Generated Response for {prompt_name}:\n{response}\n\n"

            # Display a JSON object for debugging
            st.subheader("Debug")
            st.write(prompts_array)

            # This ends the CONTENT SUBLOOP.

            # Button to download the results as RTF
            if st.download_button("Download Results as RTF", all_results, file_name="results.rtf", mime="application/rtf"):
                st.write("Download initiated.")
    else:
        st.write("No details available for the selected content type.")
else:
    st.write("Please select a content type to see details.")
