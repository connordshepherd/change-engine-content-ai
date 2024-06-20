import streamlit as st
import json
import pandas as pd
import requests
import logging

from io import BytesIO
from PIL import Image
from helpers import (
    get_content_types_data,
    get_table_data,
    process_table_data,
    get_selected_layouts_array,
    generate_prompts_array_with_variations,
    send_to_openai,
    add_specs,
    evaluate_character_count_and_lines,
    extract_key_value_pairs,
    send_to_openai_with_tools,
    send_plaintext_to_openai,
    get_client_data,
    prepare_layout_selector_data,
    group_values,
    fix_problems,
    update_grouped,
    evaluate_character_count_and_lines_of_group,
)
import openai

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Streamlit Widescreen Mode
st.set_page_config(layout="wide")

# Title
st.title("Automated Testing for Content Creation AI")

# Retrieve data from Airtable for content types and clients
content_types_data = get_content_types_data()
client_data = get_client_data()

# Extract and filter content types where v1 is true
v1_true_content_types = [item["Content Type"] for item in content_types_data if item["v1"]]

# Insert default options
content_type_options = ["Select a Content Type"] + v1_true_content_types
company_name_list = sorted(client_data.keys())

default_company_index = 0  # Default to "Select a Company"
if "Global App Testing" in company_name_list:
    default_company_index = company_name_list.index("Global App Testing") + 1  # +1 because of "Select a Company"

# Manual input for testing parameters
selected_company_name = st.selectbox("Company", options=["Select a Company"] + company_name_list, index=default_company_index)
selected_content_type = st.selectbox("Content Type", options=content_type_options)
variations = st.number_input("Number of Variations", 1, 10, value=10, step=1)
topic = st.text_area("Prompt", height=100)

if selected_company_name and selected_company_name != "Select a Company":
    company_tone_style = st.text_area("Company Tone and Style Guide", value=client_data[selected_company_name], height=100)
else:
    company_tone_style = st.text_area("Company Tone and Style Guide", value="", height=100)

def get_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

if selected_content_type != "Select a Content Type":
    selected_data = next((item for item in content_types_data if item["Content Type"] == selected_content_type), None)

    if selected_data:
        st.subheader("Details for: " f"{selected_content_type}")

        image_prompt = st.text_area("Image Prompt", value=selected_data["Image Prompt"], height=200)
        content_professional = st.text_area("Content (Professional)", value=selected_data["Content Professional"], height=200)
        content_casual = st.text_area("Content (Casual)", value=selected_data["Content Casual"], height=200)
        content_direct = st.text_area("Content (Direct)", value=selected_data["Content Direct"], height=200)

        if image_prompt:
            # Load data corresponding to the selected content type
            table_data = get_table_data(selected_content_type)
            df = process_table_data(table_data)
            orient_json = df.to_json(orient="records")
            edited_json = json.loads(orient_json)

            # Add specs to the layouts
            edited_json_with_specs = add_specs(edited_json)
            layout_selector_data = prepare_layout_selector_data(table_data)
            column_config = {
                "Layout": st.column_config.Column("Layout", disabled=True),
                "Image": st.column_config.ImageColumn("Preview Image", help="Thumbnail previews from Airtable"),
                "Enabled": st.column_config.CheckboxColumn("Enabled", help="Enable this layout?", default=False),
                "Layout Number": st.column_config.Column("Layout Number", disabled=True),
            }

            # Select each layout one at a time
            layouts_array = get_selected_layouts_array(edited_json_with_specs, list(range(len(layout_selector_data))))

            # Automate testing
            all_results = ""
            for idx, layout in enumerate(layouts_array):
                layout_key = list(layout.keys())[0]
                logging.info(f"Processing layout {layout_key} ({idx + 1}/{len(layouts_array)})")
                prompts_array = generate_prompts_array_with_variations(topic, image_prompt, [layout], variations)
                
                for prompt in prompts_array:
                    for retry in range(3):
                        messages = prompt["message"]
                        specs = prompt["specs"]
                        response = send_to_openai(messages)
                        
                        if not response:
                            logging.warning(f"No response from OpenAI for layout {layout_key}. Retrying {retry + 1}/3...")
                            continue

                        tool_call_prompt = "Please extract relevant entities (Title, Subtitle and any others) from the below text.\n\n---------------\n\n" + response
                        layout_messages = [{"role": "user", "content": response}]
                        layout_response = send_to_openai_with_tools(layout_messages)
                        pairs_json = extract_key_value_pairs(layout_response)

                        iterations = 0
                        missing_key = False
                        max_retries = 3
                        grouped = group_values(pairs_json)

                        while iterations < 5:
                            evaluation = evaluate_character_count_and_lines_of_group(grouped, specs)
                            if not any("reason_code" in value for item in evaluation for value in item["values"].values()):
                                break

                            if any("reason_code" in value and "The specified key is missing" in value["reason_code"] for item in evaluation for value in item["values"].values()):
                                missing_key = True
                                break

                            problems, keys_to_fix, indices_to_fix, line_counts = fix_problems(evaluation)
                            for problem, key, index, line_count in zip(problems, keys_to_fix, indices_to_fix, line_counts):
                                prompt_with_context = f"{problem}\n\nPlease return your new text, on {line_count} lines."
                                fixed_response = send_plaintext_to_openai(prompt_with_context)
                                updated = update_grouped(grouped, key, index, fixed_response)
                                if not updated:
                                    logging.error(f"Could not update value for {key} at index {index} with content {fixed_response}")
                                    continue

                            iterations += 1

                        if missing_key:
                            logging.error(f"Missing key detected for layout {layout_key}. Retrying {retry + 1}/{max_retries}...")
                            continue
                        else:
                            break

                        if retry == max_retries - 1:
                            logging.error(f"Max retries exhausted for layout {layout_key}. Moving on to the next layout.")
                            continue

                    result = f"Generated Response for {layout_key}:\n"
                    for group in grouped:
                        key = group["key"]
                        values = group["values"]
                        for index, value in values.items():
                            result += f"{key} {index}: {value}\n"
                    result += "-" * 30 + "\n"
                    all_results += result

            # Content loop
            other_prompts = [
                ("Content Professional", content_professional),
                ("Content Casual", content_casual),
                ("Content Direct", content_direct),
            ]

            for prompt_name, prompt_content in other_prompts:
                if prompt_content:
                    other_prompt_messages = []
                    other_prompt = company_tone_style + "\n\n--------------\n\n" + topic + "\n\n-----------\n\n" + prompt_content + "\n\nPlease create " + str(variations) + " different variations."
                    other_prompt_messages.append({"role": "user", "content": other_prompt})
                    response = send_to_openai(other_prompt_messages)
                    all_results += f"Generated Response for {prompt_name}:\n{response}\n\n"

            if st.download_button("Download Results as RTF", all_results, file_name="results.rtf", mime="application/rtf"):
                st.write("Download initiated.")

    else:
        st.write("No details available for the selected content type.")
else:
    st.write("Please select a content type to see details.")
