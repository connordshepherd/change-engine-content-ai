import streamlit as st
import requests
import json
from collections import defaultdict

def query_airtable_content_table():
    base_id = "appkUZW01q89QDGB9"
    table_name = "content"
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_SECOND_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    params = {
        "cellFormat": "string"  # This will return the string value for linked fields
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()['records']
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

def process_content_table(records):
    if not records:
        return "No data available"

    content_kits = defaultdict(lambda: defaultdict(list))
    
    for record in records:
        fields = record['fields']
        kits = fields.get('Content Kits', ['Uncategorized'])
        # Ensure kits is always a list
        kits = kits if isinstance(kits, list) else [kits]
        kit = ', '.join(kits)
        step = fields.get('Step', 'Uncategorized')
        
        content_kits[kit][step].append(fields)
    
    output = []
    
    for kit, steps in content_kits.items():
        output.append(f"Content Kit: {kit}")
        
        for step, items in steps.items():
            output.append(f"Step: {step}")
            output.append(f"Step Description: {items[0].get('Step Description', 'N/A')}")
            
            for item in items:
                output.append(f"Element Title: {item.get('Content Title', 'N/A')}")
                output.append(f"Element Description: {item.get('Description', 'N/A')}")
                content_type = item.get('Content Type', 'N/A')
                content_type = content_type if isinstance(content_type, str) else ', '.join(content_type)
                output.append(f"Content Type: {content_type}")
                item_type = item.get('Type', 'N/A')
                item_type = item_type if isinstance(item_type, str) else ', '.join(item_type)
                output.append(f"Type: {item_type}")
                output.append("")
            
            output.append("")
        
        output.append("")
    
    return "\n".join(output)

# Streamlit app
st.title("Airtable Content Table")

if st.button("Fetch and Process Data"):
    records = query_airtable_content_table()
    if records:
        processed_data = process_content_table(records)
        st.text_area("Processed Content Table", processed_data, height=300)
