import streamlit as st
import json
import pandas as pd
import requests
from st_copy_to_clipboard import st_copy_to_clipboard

from io import BytesIO
from PIL import Image
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array_with_variations, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools
from helpers import send_plaintext_to_openai, get_client_data, prepare_layout_selector_data, assemble_prompt, get_image_from_url
from helpers import group_values, fix_problems, update_grouped, evaluate_character_count_and_lines_of_group
from dummy import dummy_prompt
import openai
from typing import List, Dict, Union, Any, Tuple
import webbrowser
from streamlit.components.v1 import html

def open_page(url):
    open_script = """
    <script type="text/javascript">
        window.open('%s', '_blank').focus();
    </script>
    """ % url
    html(open_script)

# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

# Streamlit UI - Title
st.title("Content Creation AI")

# Display all the prompts from Content Types
topic = st.text_area("Prompt", height=100)

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

if selected_content_type != "Select a Content Type":
    # Filter data to get the selected content type details
    selected_data = next((item for item in content_types_data if item["Content Type"] == selected_content_type), None)

    if selected_data:
        
        # Show an example prompt for the selected content type
        example_value = selected_data["Example Prompt"]
        st.write(f"Example Prompts: {example_value}")

        # Set number of variations from 'Variation Default' column
        default_variations = selected_data.get("Variation Default", 5)  # Default to 5 if not specified
        variations = st.number_input("Number of Variations", 1, 1000, value=int(default_variations))
        
        # Add "Group By" selectbox
        group_by = st.selectbox("Group By", options=["Layout", "Key"])

        # Fetch Tone table data from Airtable
        tone_data = get_table_data('Tone')
        
        # Extract 'Tone' and 'Tone Description' columns
        tone_list = [record['fields']['Tone'] for record in tone_data if 'Tone' in record['fields']]
        tone_description_dict = {record['fields']['Tone']: record['fields']['Tone Description'] for record in tone_data if 'Tone' in record['fields'] and 'Tone Description' in record['fields']}
        
        # Create a selectbox for Tone values
        selected_tone = st.selectbox("Select Tone", options=["Select a Tone"] + tone_list)
        
        # Display the corresponding Tone Description for the selected Tone
        if selected_tone and selected_tone != 'Select a Tone':
            company_tone_style = tone_description_dict[selected_tone]
        else:
            company_tone_style = ""

        if selected_data.get("Image Prompt"):
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

            # New section with two columns
            col3, col4 = st.columns([3, 1])  # 25% and 75% width

            with col3:
                image_selector_df = st.data_editor(data=layout_selector_data, column_config=column_config, hide_index=True, use_container_width=True)

            with col4:
                # URLs for GPT and Adobe (as examples, use actual URLs)
                design_url = "https://changeEngine.designhuddle.com"
                
                # Buttons with on_click to open a new tab
                if st.button("Open DH Layouts"):
                    open_page(design_url)
                    
            selected_images = image_selector_df[image_selector_df["Enabled"]]
            selected_layouts_numbers = selected_images['Layout Number'].tolist()
            selected_layouts = ", ".join(map(str, selected_layouts_numbers))

            # Assemble the layouts as plaintext
            layouts_array = get_selected_layouts_array(edited_json_with_specs, selected_layouts)
            #st.write(layouts_array)

            st.subheader("Final Prompt with Layout")
                    
            # New section with two columns
            col1, col2 = st.columns([3, 1])  # 25% and 75% width
            
            with col1:
                # Only assemble and display the prompt if all necessary components are available
                if selected_content_type != "Select a Content Type" and selected_data:
                    # Assemble the prompt for display
                    prompt = assemble_prompt(
                        company_tone_style,
                        selected_data.get("Image Prompt", ""),
                        topic,  # You need to define this variable based on user input or selection
                        variations,
                        layouts_array,
                        content_professional=selected_data.get("Content Professional"),
                        content_casual=selected_data.get("Content Casual"),
                        content_direct=selected_data.get("Content Direct")
                    )
                    prompt_display = st.text_area("Prompt", value=prompt, height=400)
                else:
                    st.write("Please select a company and content type to generate the prompt.")
                
            with col2:
                st.write("Copy to Clipboard")
                st_copy_to_clipboard(prompt_display)
                
                # URLs for GPT and Adobe (as examples, use actual URLs)
                gpt_url = "https://chatgpt.com/"
                adobe_url = "https://new.express.adobe.com/?category=generative-ai"
                
                # Buttons with on_click to open a new tab
                if st.button("Open GPT"):
                    open_page(gpt_url)
                if st.button("Open Adobe"):
                    open_page(adobe_url)

            # Generate button
            if st.button("Generate"):
                st.write("---")
                # Set the prompt values
                image_prompt = selected_data.get("Image Prompt")
                content_professional = selected_data.get("Content Professional")
                content_casual = selected_data.get("Content Casual")
                content_direct = selected_data.get("Content Direct")
                
                # Start generating
                all_results = ""  # Initialize a single string to hold all results
                # Variation loop I took out
                results = []  # Initialize a list to hold the results
    
                # This starts the IMAGE SUBLOOP. Images are complicated because they have stringent character length requirements. 
                # Only FAQ images are exempt - they are actually too complex to map here.
                if image_prompt:

                    st.subheader("Image Results: Text for Selected Layout")
                    # Generate prompts array for image_prompt
                    prompts_array = generate_prompts_array_with_variations(topic, image_prompt, layouts_array, variations)
                    #st.write("Prompts array", prompts_array)
                
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
                            #st.write("OpenAI response", response)
                            if not response:
                                # st.write(f"Failed to get a response. Retrying {retry + 1}/3...")
                                continue  # Retry without incrementing n
                
                            tool_call_prompt = "Please extract relevant entities (Title, Subtitle and any others) from the below text." + "\n\n---------------\n\n" + response
                            layout_messages = [{"role": "user", "content": response}]
                            layout_response = send_to_openai_with_tools(layout_messages)
                            pairs_json = extract_key_value_pairs(layout_response)
                            #st.write("Pairs JSON initial", pairs_json)
                
                            iterations = 0
                            missing_key = False  # Flag to indicate missing key
                            max_retries = 3
                            grouped = group_values(pairs_json)
                            #st.write("Grouped", grouped)
                            #st.write("Specs", specs)
                            
                            while iterations < 5:
                                # Evaluate the grouped values based on specifications
                                evaluation = evaluate_character_count_and_lines_of_group(grouped, specs)
                                #st.write("Evaluation", evaluation)
                
                                # Break if all criteria are met and no reason_code is present in the evaluation
                                if not any("reason_code" in value for item in evaluation for value in item['values'].values()):
                                    #st.info(f"Completed in {iterations} iterations.")
                                    break  # Break the fixing loop since all criteria are met
                
                                # Check for missing key issue
                                if any("reason_code" in value and "The specified key is missing" in value["reason_code"] for item in evaluation for value in item['values'].values()):
                                    missing_key = True
                                    break  # Break the fixing loop to retry with a new generation
                
                                # Fix identified problems systematically
                                problems, keys_to_fix, indices_to_fix, line_counts = fix_problems(evaluation)
                                #st.subheader("Fix Problems")
                                for problem, key, index, line_count in zip(problems, keys_to_fix, indices_to_fix, line_counts):
                                    #st.write(f"Fixing problem for {key} at index {index}: {problem}")
                                    prompt_with_context = f"{problem}\n\nPlease return your new text, on {line_count} lines."
                                    # Send request to OpenAI for generating fix
                                    fixed_response = send_plaintext_to_openai(prompt_with_context)
                                    #st.write(f"Fixed response for {key} at index {index}: {fixed_response}")
                
                                    # Update the grouped structure with fixed_response
                                    updated = update_grouped(grouped, key, index, fixed_response)
                                    #st.write("Updated", updated)
                                    #st.write("Updated Grouped", grouped)
                
                                    if not updated:
                                        st.write(f"Could not update value for {key} at index {index} with content {fixed_response}")
                
                                iterations += 1
                
                            if missing_key:
                                st.write(f"Missing key detected. Retrying {retry + 1}/{max_retries}...")
                            else:
                                break
                
                            if retry == max_retries - 1:  # If we've exhausted retries
                                st.write("Max retries exhausted. Moving on to the next layout.")
                            
                            #st.write("Final grouped", grouped)
                
                        # Collect and format the final output
                        result = f"Generated Response for {layout_key}:\n"
                
                        # Iterate over each group and format the key-value pairs correctly
                        if group_by == "Key":
                            # Grouping by Key, keep current logic
                            result = ""
                            for group in grouped:
                                key = group['key']
                                values = group['values']
                                for index, value in values.items():
                                    result += f"{key} {index}: {value}\n"
                                result += "-" * 30 + "\n"
                            results.append(result)
                        
                        elif group_by == "Layout":
                            # Grouping by Layout, new logic
                            indices = set()
                            for group in grouped:
                                indices.update(group['values'].keys())
                            
                            result = ""
                            for index in sorted(indices):
                                for group in grouped:
                                    key = group['key']
                                    value = group['values'].get(index, "")  # Use .get() to avoid KeyError
                                    result += f"{key} {index}: {value}\n"
                                result += "-" * 30 + "\n"
                            results.append(result)
                    
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
                            st.subheader(f"Generated Results for {prompt_name}")
                            other_prompt_messages = []
                            other_prompt = company_tone_style + "\n\n--------------\n\n" + topic + "\n\n-----------\n\n" + prompt_content + "\n\nPlease create " + str(variations) + "different variations."
                            other_prompt_messages.append({"role": "user", "content": other_prompt})
                            response = send_to_openai(other_prompt_messages)
                            st.write(response)
                            all_results += f"Generated Response for {prompt_name}:\n{response}\n\n"
    
                # Display a JSON object for debugging
                #st.subheader("Debug")
                #st.write(prompts_array)
    
                # This ends the CONTENT SUBLOOP.
    
                # Button to download the results as RTF
                if st.download_button("Download Results as RTF", all_results, file_name="results.rtf", mime="application/rtf"):
                    st.write("Download initiated.")
