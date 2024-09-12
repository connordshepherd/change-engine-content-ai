import streamlit as st
import requests
from collections import defaultdict

def query_airtable_table(base_id, table_name):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_SECOND_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()['records']
    else:
        st.error(f"Error fetching data from {table_name}: {response.status_code}")
        return None

def process_content_table(content_records, content_kits_records):
    if not content_records or not content_kits_records:
        return "No data available"

    # Create a lookup dictionary for Content Kits
    content_kits_lookup = {record['id']: record['fields'].get('Content Kit', 'Unknown') for record in content_kits_records}

    content_kits = defaultdict(lambda: defaultdict(list))
    
    for record in content_records:
        fields = record['fields']
        kit_ids = fields.get('Content Kits', ['Uncategorized'])
        kits = [content_kits_lookup.get(kit_id, kit_id) for kit_id in kit_ids]
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
                content_type = item.get('Content Type (from Content Type)', item.get('Content Type', 'N/A'))
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
    base_id = "appkUZW01q89QDGB9"
    content_records = query_airtable_table(base_id, "content")
    content_kits_records = query_airtable_table(base_id, "Content Kits")
    
    if content_records and content_kits_records:
        processed_data = process_content_table(content_records, content_kits_records)
        st.text_area("Processed Content Table", processed_data, height=300)
