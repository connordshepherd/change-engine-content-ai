import streamlit as st
import requests
from collections import defaultdict
import json

def query_airtable_table(base_id, table_name):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_SECOND_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    all_records = []
    params = {}

    while True:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            all_records.extend(data['records'])
            
            if 'offset' in data:
                params['offset'] = data['offset']
            else:
                break
        else:
            st.error(f"Error fetching data from {table_name}: {response.status_code}")
            return None

    return all_records

def get_unique_content_kits(content_kits_records):
    return sorted(set(record['fields'].get('Content Kit', 'Unknown') for record in content_kits_records))

def process_content_table(content_records, content_kits_records, selected_kits):
    if not content_records or not content_kits_records:
        return {}

    content_kits_lookup = {record['id']: record['fields'].get('Content Kit', 'Unknown') for record in content_kits_records}

    content_kits = defaultdict(lambda: defaultdict(list))
    
    for record in content_records:
        fields = record['fields']
        kit_ids = fields.get('Content Kits', ['Uncategorized'])
        kits = [content_kits_lookup.get(kit_id, kit_id) for kit_id in kit_ids]
        kit = ', '.join(kits)
        
        if kit in selected_kits:
            step = fields.get('Step', 'Uncategorized')
            
            if step != 'Uncategorized':
                content_kits[kit][step].append(fields)
    
    json_output = {}
    
    for kit, steps in content_kits.items():
        json_output[kit] = []
        
        sorted_steps = sorted(steps.items(), key=lambda x: int(x[0].split(':')[0].split()[-1]) if x[0].startswith('Step') else float('inf'))
        
        for step, items in sorted_steps:
            step_data = {
                "name": step,
                "description": items[0].get('Step Description', 'N/A'),
                "elements": []
            }
            
            for item in items:
                content_type = item.get('Content Type (from Content Type)', item.get('Content Type', 'N/A'))
                content_type = content_type if isinstance(content_type, str) else ', '.join(content_type)
                item_type = item.get('Type', 'N/A')
                item_type = item_type if isinstance(item_type, str) else ', '.join(item_type)
                
                element = {
                    "title": item.get('Content Title', 'N/A'),
                    "description": item.get('Description', 'N/A'),
                    "content_type": content_type,
                    "type": item_type
                }
                step_data["elements"].append(element)
            
            json_output[kit].append(step_data)
    
    return json_output

# Streamlit app
st.title("Airtable Content Table")

base_id = "appkUZW01q89QDGB9"

# Fetch data on page load
content_records = query_airtable_table(base_id, "content")
content_kits_records = query_airtable_table(base_id, "Content Kits")

if content_records and content_kits_records:
    unique_kits = get_unique_content_kits(content_kits_records)
    st.write("Available Content Kits:")
    st.write(", ".join(unique_kits))

    selected_kits_input = st.text_input("Enter comma-separated Content Kit names to filter:")
    selected_kits = [kit.strip() for kit in selected_kits_input.split(',')] if selected_kits_input else []

    if st.button("Submit"):
        if selected_kits:
            processed_data = process_content_table(content_records, content_kits_records, selected_kits)
            st.json(processed_data)
        else:
            st.warning("Please enter at least one Content Kit name.")
else:
    st.error("Failed to fetch data from Airtable. Please try again later.")
