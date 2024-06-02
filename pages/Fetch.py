import streamlit as st
import requests

# Function to get field names and IDs from the "Content Types" table
def get_field_names_and_ids():
    base_id = 'appbJ9Bt0YNuBafT4'
    table_id = 'Content Types'  # This could be the table name or ID
    airtable_token = st.secrets.AIRTABLE_PERSONAL_TOKEN
    headers = {
        "Authorization": f"Bearer {airtable_token}"
    }

    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.error(f"Failed to retrieve table metadata: {response.text}")
        return []

    tables = response.json().get('tables', [])

    table_fields = {}
    for table in tables:
        if table['name'] == table_id or table['id'] == table_id:
            table_fields = table['fields']
            break

    field_ids = {}
    for field in table_fields:
        field_ids[field['name']] = field['id']

    return field_ids

# Streamlit UI
st.title("Airtable Content Types Field IDs Fetcher")

field_ids = get_field_names_and_ids()

if field_ids:
    st.write("Field Names and IDs:")
    for name, id_ in field_ids.items():
        st.write(f"Name: {name}, ID: {id_}")
else:
    st.write("No fields found.")
