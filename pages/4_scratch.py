import streamlit as st
from helpers import send_to_openai_with_tools, tools, extract_key_value_pairs

specs = {
  "Title_specs": "{\"LINES\": 3, \"LINE_1_UPPER_LIMIT\": 10, \"LINE_2_UPPER_LIMIT\": 10, \"LINE_3_UPPER_LIMIT\": 10}",
  "Hashtag 1_specs": "{\"LINES\": 1, \"LINE_1_LOWER_LIMIT\": 15, \"LINE_1_UPPER_LIMIT\": 21}",
  "Hashtag 2_specs": "{\"LINES\": 1, \"LINE_1_LOWER_LIMIT\": 15, \"LINE_1_UPPER_LIMIT\": 21}"
}

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

    # Process and evaluate the response
    iterations = 0
    missing_key = False  # Flag to indicate missing key

    while iterations < 5:  # Attempt to fix and ensure criteria max 5 times
        evaluation = evaluate_character_count_and_lines(pairs_json, specs)
        st.write(evaluation)

        if not any("reason_code" in item for item in evaluation):
            st.write(f"Completed in {iterations} iterations.")
            break  # Break the fixing loop since all criteria are met

        if any("reason_code" in item and "The specified key is missing" in item["reason_code"] for item in evaluation):
            missing_key = True
            break  # Break the fixing loop to retry with a new generation

        problems, keys_to_fix, line_counts = fix_problems(evaluation)
        st.subheader("Fix Problems")
        for problem, key, line_count in zip(problems, keys_to_fix, line_counts):
            st.write(f"Fixing problem for {key}: {problem}")
            prompt_with_context = f"{problem}\n\nPlease return your new text, on {line_count} lines."
            fixed_response = send_plaintext_to_openai(prompt_with_context)
            st.write(fixed_response)

            for pair in pairs_json:
                if pair["key"].upper() == key.upper():
                    pair["value"] = fixed_response

        iterations += 1

    if missing_key:
        st.write(f"Missing key detected. Retrying {retry + 1}/3...")
    else:
        st.write(pairs_json)
