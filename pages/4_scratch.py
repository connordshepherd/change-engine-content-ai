import streamlit as st
from helpers import send_to_openai_with_tools, tools, extract_key_value_pairs

draft_response = """Sure, here are the five different variant drafts for the LinkedIn banner:

-------
Title:
Join Us!
Build Tech
With Us

Hashtag 1: #HiringSoftwareDevs
Suggest Photo/Illustration/Icon: a cartoon illustration
Hashtag 2: #JoinOurTechTeam
-------

-------
Title:
Code Now,
Grow Now
Join Us

Hashtag 1: #HiringSoftwareDevs
Suggest Photo/Illustration/Icon: a cartoon illustration
Hashtag 2: #TechCareersHere
-------

-------
Title:
Dev Team
Needs You!
Apply Now

Hashtag 1: #JoinOurTechTeam
Suggest Photo/Illustration/Icon: a cartoon illustration
Hashtag 2: #SoftwareJobsOpen
-------

-------
Title:
Dream Job,
Code Now,
Succeed

Hashtag 1: #NowHiringDevs
Suggest Photo/Illustration/Icon: a cartoon illustration
Hashtag 2: #TechCareersHere
-------

-------
Title:
Hiring Now!
Developers
Welcome!

Hashtag 1: #TechCareersHere
Suggest Photo/Illustration/Icon: a cartoon illustration
Hashtag 2: #JoinOurTechTeam
-------

Hope these meet your requirements!"""

response = st.text_area(value=draft_response, height=200)

if st.button("Generate")"
    tool_call_prompt = "Please extract relevant entities (Title, Subtitle and any others) from the below text." + "\n\n---------------\n\n" + response
    layout_messages = [{"role": "user", "content": tool_call_prompt}]
    layout_response = send_to_openai_with_tools(layout_messages)
    pairs_json = extract_key_value_pairs(layout_response)
    st.write(pairs_json)
