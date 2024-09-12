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

def get_filter_options(content_records):
    steps = set()
    content_types = set()
    types = set()
    
    for record in content_records:
        fields = record['fields']
        steps.add(fields.get('Step', 'Uncategorized'))
        content_type = fields.get('Content Type (from Content Type)', fields.get('Content Type', 'N/A'))
        if isinstance(content_type, list):
            content_types.update(content_type)
        else:
            content_types.add(content_type)
        item_type = fields.get('Type', 'N/A')
        if isinstance(item_type, list):
            types.update(item_type)
        else:
            types.add(item_type)
    
    return {
        "steps": sorted(steps),
        "content_types": sorted(content_types),
        "types": sorted(types)
    }

def create_filter_json(selected_kits, selected_steps, selected_content_types, selected_types):
    return {
        "selected_kits": selected_kits,
        "filters": {
            "step": selected_steps,
            "content_type": selected_content_types,
            "type": selected_types
        }
    }

def process_content_table(content_records, content_kits_records, filter_json):
    if not content_records or not content_kits_records:
        return {}

    content_kits_lookup = {record['id']: record['fields'].get('Content Kit', 'Unknown') for record in content_kits_records}

    content_kits = defaultdict(lambda: defaultdict(list))
    
    selected_kits = filter_json['selected_kits']
    filters = filter_json['filters']
    
    for record in content_records:
        fields = record['fields']
        kit_ids = fields.get('Content Kits', ['Uncategorized'])
        kits = [content_kits_lookup.get(kit_id, kit_id) for kit_id in kit_ids]
        kit = ', '.join(kits)
        
        if kit in selected_kits:
            step = fields.get('Step', 'Uncategorized')
            content_type = fields.get('Content Type (from Content Type)', fields.get('Content Type', 'N/A'))
            item_type = fields.get('Type', 'N/A')
            
            if (step in filters['step'] or not filters['step']) and \
               (content_type in filters['content_type'] or not filters['content_type']) and \
               (item_type in filters['type'] or not filters['type']):
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
    st.write("Enter your JSON filter object:")
    json_input = st.text_area("JSON Input", 
                              '''{
    "selected_kits": ["Kit Name 1", "Kit Name 2"],
    "filters": {
        "step": ["Step 1", "Step 2"],
        "content_type": ["FAQ", "Handbook"],
        "type": ["Document", "Design"]
    }
}''', 
                              height=200)

    if st.button("Submit"):
        try:
            filter_json = json.loads(json_input)
            processed_data = process_content_table(content_records, content_kits_records, filter_json)
            st.json(processed_data)
        except json.JSONDecodeError:
            st.error("Invalid JSON input. Please check your JSON format and try again.")
else:
    st.error("Failed to fetch data from Airtable. Please try again later.")
