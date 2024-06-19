import streamlit as st
from helpers import send_to_openai_with_tools, tools, extract_key_value_pairs
from helpers import evaluate_character_count_and_lines, send_plaintext_to_openai
from typing import List, Dict, Any, Tuple

# Define the fix_problems function
def fix_problems(evaluation: List[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str], List[int]]:
    result = []
    reasons = []
    keys = []
    line_counts = []
    
    for item in evaluation:
        key = item["key"]
        for idx, value in item["values"].items():
            if "reason_code" in value:
                text = value.get("value", "")
                reason_code = value["reason_code"]
                formatted_problem = f"{reason_code}\n\n---------\n\n{text}"
                result.append(formatted_problem)
                reasons.append(key)  # Append the key to track which item we are fixing
                keys.append(idx)  # Append the index within the values dictionary
                line_counts.append(value.get("lines_criteria", "N/A"))  # Append line count criteria
    
    return result, reasons, keys, line_counts

# Updates into the grouped object
def update_grouped(grouped: List[Dict[str, Any]], key: str, index: str, new_value: str) -> bool:
    for item in grouped:
        if item["key"] == key:
            if index in item["values"]:
                item["values"][index] = new_value
                return True
    return False

# Run the character count evaluation on an object with multiple entries
def evaluate_character_count_and_lines_of_group(grouped, specs):
    def evaluate_single_pair(value, spec):
        result = {
            "value": value,
            "meets_line_count": False if value is None else True,
            "meets_character_criteria": False if value is None else True,
        }
    
        if value:
            value_lines = value.split('\n')
            lines_criteria = spec["LINES"]
            meets_lines_criteria = len(value_lines) == lines_criteria
            result.update({"lines_criteria": lines_criteria})
    
            if not meets_lines_criteria:
                result["meets_line_count"] = False
                result["reason_code"] = f"Wrong number of lines - please rewrite this text so it is on {lines_criteria} lines, but keep the general meaning the same:"
            
            meets_char_criteria = True
            for i in range(lines_criteria):
                if i < len(value_lines):
                    upper_limit = spec[f"LINE_{i + 1}_UPPER_LIMIT"]
                    line_length = len(value_lines[i])
                    if line_length > upper_limit:
                        result["meets_character_criteria"] = False
                        result["reason_code"] = f"Say something like this, with only 2 words. You can change the meaning if you need to. If you want to remove a word, do it. This is for a graphic design, so we're just trying to communicate the general theme. It doesn't need to be exact. Return your new text, on {lines_criteria} lines."
                        meets_char_criteria = False
                        break
                        
                    if f"LINE_{i + 1}_LOWER_LIMIT" in spec:
                        lower_limit = spec[f"LINE_{i + 1}_LOWER_LIMIT"]
                        if line_length < lower_limit:
                            result["meets_character_criteria"] = False
                            result["reason_code"] = f"Add 1 word to this text. If there are line breaks, keep them. Return only the adjusted text, on {lines_criteria} lines."
                            meets_char_criteria = False
                            break
                else:
                    # Handle the case where there are fewer lines than required
                    result["meets_character_criteria"] = False
                    result["reason_code"] = f"Insufficient number of lines. The required number of lines is {lines_criteria}, but the value only has {len(value_lines)} lines."
                    meets_char_criteria = False
                    break
    
            result["meets_line_count"] = meets_lines_criteria
            result["meets_character_criteria"] = meets_char_criteria
    
        else:
            result["meets_line_count"] = False
            result["meets_character_criteria"] = False
            result["reason_code"] = f"The specified key is missing from the generated content, which should be formatted with the required number of lines."
            
        return result

    overall_result = []

    for item in grouped:
        key = item["key"]
        formatted_key = key.replace(' ', '').lower()
        spec_key = f"{formatted_key}_specs"

        spec = None
        for spec_key, spec_str in specs.items():
            if formatted_key in spec_key.replace(' ', '').lower():
                try:
                    spec = eval(spec_str)  # Convert string to dictionary safely
                    break
                except Exception as e:
                    print(f"Error parsing spec for key {key}: {e}")

        if spec:
            evaluated_values = {}
            for idx, value in item["values"].items():
                evaluated_values[idx] = evaluate_single_pair(value, spec)
            overall_result.append({"key": key, "values": evaluated_values})
        else:
            print(f"No spec found for key {key}")

    return overall_result


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

grouped = [
  {
    "key": "TITLE",
    "values": {
      "0": "Honor\nAndy",
      "1": "1 Year \nWith Andy",
      "2": "Cheers to \nAndy!"
    }
  },
  {
    "key": "SUBTITLE",
    "values": {
      "0": "Excellence Achieved\nAndy",
      "1": "Cheers\nAndy!",
      "2": "Success with Andy!"
    }
  },
  {
    "key": "ILLUSTRATION",
    "values": {
      "0": "A festive office celebration with balloons and confetti",
      "1": "A team congratulating a colleague with a \"1 Year\" cake",
      "2": "An office party with a \"Happy Work Anniversary\" banner"
    }
  }
]

def group_values(pairs_json):
    grouped = {}
    
    for pair in pairs_json:
        key = pair['key']
        value = pair['value']
        
        if key not in grouped:
            grouped[key] = {'key': key, 'values': {}}
        
        current_index = len(grouped[key]['values'])
        grouped[key]['values'][current_index] = value
    
    return list(grouped.values())

response = st.text_area("Response", value=draft_response, height=200)
st.write("pairs_json", pairs_json)
st.write("Specs", specs)
st.info("You need to adjust the fix_problems function to return the mapping of where in the grouped object you have an issue to fix.")

if st.button("Generate"):
    iterations = 0
    retry = 0
    missing_key = False  # Flag to indicate missing key
    max_retries = 3
    st.write("Grouped", grouped)

    while retry < max_retries:
        while iterations < 5:  # Attempt to fix and ensure criteria max 5 times
            # Evaluate the grouped values based on specifications
            evaluation = evaluate_character_count_and_lines_of_group(grouped, specs)
            st.write("Evaluation", evaluation)

            # Break if all criteria are met and no reason_code is present in the evaluation
            if not any("reason_code" in value for item in evaluation for value in item['values'].values()):
                st.write(f"Completed in {iterations} iterations.")
                break  # Break the fixing loop since all criteria are met

            # Check for missing key issue
            if any("reason_code" in value and "The specified key is missing" in value["reason_code"] for item in evaluation for value in item['values'].values()):
                missing_key = True
                break  # Break the fixing loop to retry with a new generation

            # Fix identified problems systematically
            problems, keys_to_fix, indices_to_fix, line_counts = fix_problems(evaluation)
            st.subheader("Fix Problems")
            for problem, key, index, line_count in zip(problems, keys_to_fix, indices_to_fix, line_counts):
                st.write(f"Fixing problem for {key} at index {index}: {problem}")
                prompt_with_context = f"{problem}\n\nPlease return your new text, on {line_count} lines."
                # Send request to OpenAI for generating fix
                fixed_response = send_plaintext_to_openai(prompt_with_context)
                st.write(f"Fixed response for {key} at index {index}: {fixed_response}")

                # Update the grouped structure with fixed_response
                updated = update_grouped(grouped, key, index, fixed_response)
                st.write("Updated", updated)
                st.write("Updated Grouped", grouped)

                if not updated:
                    st.write(f"Could not update value for {key} at index {index} with content {fixed_response}")

            iterations += 1

        # Retry if a missing key issue was detected
        if missing_key:
            retry += 1
            st.write(f"Missing key detected. Retrying {retry}/{max_retries}...")
            iterations = 0  # Reset the iterations for a fresh start
        else:
            break

    # Final output after processing
    st.write(grouped)
