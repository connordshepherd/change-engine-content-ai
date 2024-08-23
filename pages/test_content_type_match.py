import streamlit as st
import pandas as pd
import io
import json
import csv

# Hardcoded JSON response
hardcoded_json = [
  {
    "Step": 1,
    "Step Description": "Preparation Before Start Date",
    "Content Title": "New Hire Setup Complete",
    "Description": "Confirm with the manager that the new hire's setup is ready for their first day, including email handle, desk location, etc."
  },
  {
    "Step": 1,
    "Step Description": "Preparation Before Start Date",
    "Content Title": "Upcoming New Hire Notification",
    "Description": "Inform the manager about an upcoming new hire, including their start date and necessary preparation steps."
  },
  {
    "Step": 1,
    "Step Description": "Preparation Before Start Date",
    "Content Title": "New Hire Starts in 2 days!",
    "Description": "Notify the manager that the new hire starts in 2 days, including any final preparations needed."
  },
  {
    "Step": 1,
    "Step Description": "Preparation Before Start Date",
    "Content Title": "Identify Stakeholders",
    "Description": "HR needs to identify all stakeholders involved in the onboarding process, such as IT, Facilities, and immediate team members, to ensure seamless preparation."
  },
  {
    "Step": 1,
    "Step Description": "Preparation Before Start Date",
    "Content Title": "Define Goal",
    "Description": "Define clear objectives for the preparation phase, such as ensuring all logistical and administrative tasks are completed before the new hire starts."
  },
  {
    "Step": 2,
    "Step Description": "Initial Days Onboarding",
    "Content Title": "Welcome New Hire",
    "Description": "Prompt the manager to welcome the new hire on their first day and provide necessary information."
  },
  {
    "Step": 2,
    "Step Description": "Initial Days Onboarding",
    "Content Title": "One-on-One Reminder",
    "Description": "Encourage the manager to schedule and conduct regular one-on-one meetings with the new hire."
  },
  {
    "Step": 2,
    "Step Description": "Initial Days Onboarding",
    "Content Title": "Orientation Reminder",
    "Description": "Remind the manager about the new hire's orientation session and their role in it."
  },
  {
    "Step": 2,
    "Step Description": "Initial Days Onboarding",
    "Content Title": "Top Tip",
    "Description": "Share a top tip with managers on how to create a welcoming environment and make the new hire's first day memorable."
  },
  {
    "Step": 2,
    "Step Description": "Initial Days Onboarding",
    "Content Title": "Quick Win",
    "Description": "Identify a quick win by ensuring the new hire has one meaningful and engaging task to complete in their first few days to boost confidence."
  },
  {
    "Step": 3,
    "Step Description": "Integrating into the Team",
    "Content Title": "New Hire Buddy Reminder",
    "Description": "Encourage managers to assign a buddy to new hires to help them integrate smoothly and feel welcomed."
  },
  {
    "Step": 3,
    "Step Description": "Integrating into the Team",
    "Content Title": "Meet the Team",
    "Description": "Facilitate introductions to team members to promote a sense of inclusion and team spirit."
  },
  {
    "Step": 3,
    "Step Description": "Integrating into the Team",
    "Content Title": "Connection Starters",
    "Description": "Provide prompts or activities that encourage social interaction among team members."
  },
  {
    "Step": 3,
    "Step Description": "Integrating into the Team",
    "Content Title": "Analyze Data",
    "Description": "Gather and analyze data on the effectiveness of buddy programs and team introductions to continually improve the integration process."
  },
  {
    "Step": 3,
    "Step Description": "Integrating into the Team",
    "Content Title": "Identify Stakeholders",
    "Description": "Identify key team members and other stakeholders who will be instrumental in helping the new hire assimilate into the team culture."
  },
  {
    "Step": 4,
    "Step Description": "Tracking Progress and Milestones",
    "Content Title": "Milestone Completion",
    "Description": "Notify the manager when the new hire completes a key milestone and prompt them to acknowledge it."
  },
  {
    "Step": 4,
    "Step Description": "Tracking Progress and Milestones",
    "Content Title": "30/60/90 Day Check-In Guide",
    "Description": "Provide structured timelines for evaluating new hire performance and integration."
  },
  {
    "Step": 4,
    "Step Description": "Tracking Progress and Milestones",
    "Content Title": "Check In Reminder",
    "Description": "Remind the manager to regularly check in with the new hire to address any questions or concerns."
  },
  {
    "Step": 4,
    "Step Description": "Tracking Progress and Milestones",
    "Content Title": "Define Goal",
    "Description": "Set clear goals for tracking the new hire's progress and identify key milestones to be achieved within specific timeframes."
  },
  {
    "Step": 4,
    "Step Description": "Tracking Progress and Milestones",
    "Content Title": "Analyze Data",
    "Description": "Analyze the data from check-ins and milestone completions to identify patterns and areas for improvement in the onboarding process."
  },
  {
    "Step": 5,
    "Step Description": "Continuous Support and Feedback",
    "Content Title": "Manager Guide to Welcoming New Team Members",
    "Description": "Provide best practices and tips for managers on how to effectively welcome and support new hires."
  },
  {
    "Step": 5,
    "Step Description": "Continuous Support and Feedback",
    "Content Title": "Onboarding Success for New Managers",
    "Description": "Deliver guidance on effective onboarding practices specifically for managers new to the role."
  },
  {
    "Step": 5,
    "Step Description": "Continuous Support and Feedback",
    "Content Title": "Master Meetings",
    "Description": "Emphasize the importance of effective meetings to ensure constructive interactions and continuous feedback."
  },
  {
    "Step": 5,
    "Step Description": "Continuous Support and Feedback",
    "Content Title": "Top Tip",
    "Description": "Share tips on how managers can provide ongoing support and constructive feedback to new hires."
  },
  {
    "Step": 5,
    "Step Description": "Continuous Support and Feedback",
    "Content Title": "Quick Win",
    "Description": "Identify quick wins in the continuous support phase that can lead to immediate improvements in the new hire's experience and productivity."
  }
]

def process_csv(df):
    content_map = {}
    for _, row in df.iterrows():
        if pd.notna(row['Content Title']):
            content_map[row['Content Title']] = {
                'Content Type': row['Content Type'] if pd.notna(row['Content Type']) else '',
                'Type': row['Type'] if pd.notna(row['Type']) else ''
            }
    return content_map

def update_json_with_content_info(json_data, content_map):
    special_cases = ["Identify Stakeholders", "Analyze Data", "Quick Win", "Top Tip", "Define Goal"]
    
    for item in json_data:
        content_title = item.get('Content Title')
        if content_title in special_cases:
            item['Content Type'] = "Educational Elements"
            item['Type'] = content_title
        elif content_title in content_map:
            item['Content Type'] = content_map[content_title]['Content Type']
            item['Type'] = content_map[content_title]['Type']
        else:
            # If no match is found, you might want to set default values or leave them empty
            item['Content Type'] = ""
            item['Type'] = ""
    return json_data

st.title("Blueprint Builder - Test Page")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the CSV and generate the content map
    content_map = process_csv(df)

    # Update the hardcoded JSON with Content Type and Type
    updated_json = update_json_with_content_info(hardcoded_json, content_map)

    # Display the updated JSON
    st.json(updated_json)

    # Convert JSON to CSV and offer download
    csv_string = io.StringIO()
    writer = csv.writer(csv_string)
    
    # Write headers
    headers = list(updated_json[0].keys()) if updated_json else []
    writer.writerow(headers)
    
    # Write data
    for item in updated_json:
        writer.writerow(item.values())
    
    st.download_button(
        label="Download CSV",
        data=csv_string.getvalue(),
        file_name="output.csv",
        mime="text/csv"
    )
else:
    st.write("Please upload a CSV file to test the functionality.")
