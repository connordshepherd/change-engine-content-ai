import streamlit as st
import json
import pandas as pd
import requests
from st_copy_to_clipboard import st_copy_to_clipboard

from io import BytesIO
from PIL import Image
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array_with_variations, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools
from helpers import send_plaintext_to_openai, get_client_data, prepare_layout_selector_data
from helpers import group_values, fix_problems, update_grouped, evaluate_character_count_and_lines_of_group
from dummy import dummy_prompt
import openai
from typing import List, Dict, Union, Any, Tuple
import webbrowser
from streamlit.components.v1 import html

# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

# Session State: Initialize the required session states
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None

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
    
def get_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

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

        # Create a selectbox for company name
        company_name_list = sorted(client_data.keys())
        
        # Determine the default index for the selectbox
        default_company_index = 0  # Default to "Select a Company"
        if "Global App Testing" in company_name_list:
            default_company_index = company_name_list.index("Global App Testing") + 1  # +1 because of "Select a Company"
        
        selected_company_name = st.selectbox("Company", options=["Select a Company"] + company_name_list, index=default_company_index)
        
        # Display the AI Brand Tone Prompt for the selected company
        if selected_company_name and selected_company_name != 'Select a Company':
            company_tone_style = client_data[selected_company_name]
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

            # Check if more than one layout is selected
            if len(selected_layouts_numbers) > 1:
                st.info("Please select only one layout to continue.")
            else:
                # Assemble the layouts as plaintext
                layouts_array = get_selected_layouts_array(edited_json_with_specs, selected_layouts)
                #st.write(layouts_array)

                st.subheader("Final Prompt with Layout")
                        
                # New section with two columns
                col1, col2 = st.columns([3, 1])  # 25% and 75% width
                
                with col1:
                    # Only assemble and display the prompt if all necessary components are available
                    if selected_company_name != 'Select a Company' and selected_content_type != "Select a Content Type" and selected_data:
                        # Assemble the prompt
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
                    st_copy_to_clipboard(prompt)
                    
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
                    # Your generation logic here
                    pass
