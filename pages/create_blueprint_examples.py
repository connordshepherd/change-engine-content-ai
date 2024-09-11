import streamlit as st
import requests
from collections import defaultdict

def query_airtable_content_table():
    base_id = "appkUZW01q89QDGB9"
    table_name = "content"
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    
    headers = {
        "Authorization": f"Bearer {st.secrets['AIRTABLE_SECOND_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        records = response.json()['records']
        
        # Fetch field information
        fields_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_name}/fields"
        fields_response = requests.get(fields_url, headers=headers)
        
        if fields_response.status_code == 200:
            fields_info = {field['id']: field for field in fields_response.json()['fields']}
            return records, fields_info
        else:
            st.error(f"Error fetching field information: {fields_response.status_code}")
            return None, None
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None, None

def get_linked_field_value(field_id, record_id, fields_info):
    if field_id in fields_info and fields_info[field_id]['type'] == 'multipleSelects':
        options = fields_info[field_id]['options']['choices']
        return next((option['name'] for option in options if option['id'] == record_id), record_id)
    return record_id

def process_content_table(records, fields_info):
    if not records:
        return "No data available"

    content_kits = defaultdict(lambda: defaultdict(list))
    
    for record in records:
        fields = record['fields']
        kits = fields.get('Content Kits', ['Uncategorized'])
        kits = [get_linked_field_value('Content Kits', kit, fields_info) for kit in kits] if isinstance(kits, list) else [kits]
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
                content_type = [get_linked_field_value('Content Type', ct, fields_info) for ct in content_type] if isinstance(content_type, list) else [content_type]
                output.append(f"Content Type: {', '.join(content_type)}")
                item_type = item.get('Type', 'N/A')
                item_type = [get_linked_field_value('Type', t, fields_info) for t in item_type] if isinstance(item_type, list) else [item_type]
                output.append(f"Type: {', '.join(item_type)}")
                output.append("")
            
            output.append("")
        
        output.append("")
    
    return "\n".join(output)

# Streamlit app
st.title("Airtable Content Table")

if st.button("Fetch and Process Data"):
    records, fields_info = query_airtable_content_table()
    if records and fields_info:
        processed_data = process_content_table(records, fields_info)
        st.text_area("Processed Content Table", processed_data, height=300)
