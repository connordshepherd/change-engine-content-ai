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

pairs_json = [
  {
    "key": "TITLE",
    "value": "Join Us\nIn Our\nMission"
  },
  {
    "key": "HASHTAG 1",
    "value": "#SoftwarePlusSolutions"
  },
  {
    "key": "HASHTAG 2",
    "value": "#DevelopWithUsNow"
  },
  {
    "key": "TITLE",
    "value": "Code It\nWith Us\nToday!"
  },
  {
    "key": "HASHTAG 1",
    "value": "#TechJobsAvailableNow"
  },
  {
    "key": "HASHTAG 2",
    "value": "#SoftwareCareersOpen"
  },
  {
    "key": "TITLE",
    "value": "Join Our\nDev Team\nNow!"
  },
  {
    "key": "HASHTAG 1",
    "value": "#InnovateWithCode"
  },
  {
    "key": "HASHTAG 2",
    "value": "#JoinOurDevTeam"
  },
  {
    "key": "TITLE",
    "value": "We Are\nHiring\nNow!"
  },
  {
    "key": "HASHTAG 1",
    "value": "#DevelopAtBestPlace"
  },
  {
    "key": "HASHTAG 2",
    "value": "#JoinOurTalentedTeam"
  },
  {
    "key": "TITLE",
    "value": "Your New\nCareer\nStarts"
  },
  {
    "key": "HASHTAG 1",
    "value": "#CodeYourFuture"
  },
  {
    "key": "HASHTAG 2",
    "value": "#DevelopCareersHere"
  }
]

response = st.text_area("Response", value=draft_response, height=200)

if st.button("Generate"):
    # Assemble pairs_json unless you already have it
    # tool_call_prompt = "Please extract relevant entities (Title, Subtitle and any others) from the below text." + "\n\n---------------\n\n" + response
    #layout_messages = [{"role": "user", "content": tool_call_prompt}]
    #layout_response = send_to_openai_with_tools(layout_messages)
    #pairs_json = extract_key_value_pairs(layout_response)
    #st.write(pairs_json)
