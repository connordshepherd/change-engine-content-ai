# These are all the old imports - you probably don't need all this
import streamlit as st
import json
import pandas as pd
import requests
from st_copy_to_clipboard import st_copy_to_clipboard
from io import BytesIO
from PIL import Image
from helpers import get_content_types_data, get_table_data, process_table_data, get_selected_layouts_array, generate_prompts_array_with_variations, send_to_openai
from helpers import add_specs, evaluate_character_count_and_lines, extract_key_value_pairs, send_to_openai_with_tools, tools
from helpers import send_plaintext_to_openai, get_client_data, prepare_layout_selector_data, assemble_prompt, get_image_from_url
from helpers import group_values, fix_problems, update_grouped, evaluate_character_count_and_lines_of_group
from dummy import dummy_prompt
import openai
from typing import List, Dict, Union, Any, Tuple
import webbrowser
from streamlit.components.v1 import html

# NEW import
from pydantic import BaseModel
from enum import Enum

class ImageType(str, Enum):
    icon = "icon"
    illustration = "illustration"
    photo = "photo"

class QuestionAnswer(BaseModel):
    question: str
    answer: str
    image_type: ImageType
    image_description: str

class Variation(BaseModel):
    title: str
    subtitle: str
    questions_answers: List[QuestionAnswer]

class ContractorOnboarding(BaseModel):
    variations: List[Variation]

# This is the main response model
class Response(BaseModel):
    contractor_onboarding: ContractorOnboarding    

prompt_default_value = """You are Employee Experience Manager at a company of about 100 to 5,000 employees. This company is a hybrid work environment. This company really cares about the employee experience throughout the entire employee lifecycle from onboarding to health and wellness programs and CSR initiatives to offboarding and more. The tone should be friendly, supportive, and encouraging and not too serious. Always refer to the HR Team as the People Team instead. Use this structure for the response: group response output by the category of output (where applicable) e.g. Title variation 1, Title variation 2 etc. Then subtitle variation 1, subtitle variation 2 et.c then illustration variation 1, illustration variation 2, illustration variation 3 etc. Never include headers like "Title Variation 10". Ignore any subsequent guidance on output structure in this prompt. Always group by title, subtitle etc. 

You need to create a bunch of summaries and key highlights in a FAQ. This FAQ must answer all of the questions and answers in one page maximum. The policies in the Employee Handbook will cover them in more detail, so these FAQ's don't need to have too much detail. We want these FAQ's to be informative but also engaging and friendly/supportive/helpful in tone. Use the Layouts below to use as a framework for the FAQs. The description of the Layouts outline the character count ranges and other info to produce an FAQ for the topic chosen. Produce an FAQ providing all of the content for the outline. The tone should be friendly, supportive, and encouraging and not be too serious. Always use the outlined character count ranges, # of questions or topics and answers, and everything else outlined in the Layout Descriptions. Never deviate from the Layout Description.
----
The topic is: new contractor onboarding faq. Come up with 2 variations. Never output in code.
----

For each variation include:

**Details for Layout 2**
Title: A title of 28-33 characters
Subtitle: A subtitle of 20-30 characters
Number of Questions and Answers: 5 questions and answers
Suggest Icon/Illustration/Photo: Icon or illustration
Question: A question of 60-75 characters
Answer: An answer of 130-144 characters
image-type: Icon
Description: A description of 120-145 characters






----

Use this structure for the response:
Variation n:
Title
Subtitle
Number of Questions and Answers
Suggest Icon/Illustration/Photo
Question
Answer
image-type
Description"""



# Streamlit UI
st.title("FAQ JSON")
client = OpenAI()
prompt = st.text_area("Prompt", value=prompt_default_value, height=400)
messages = [{"role": "user", "content": prompt}]


# Use the model
completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",  # Make sure to use an available model
    messages=messages,
    response_format=Response,
)

result = completion.choices[0].message.parsed
st.write("Response")
st.write(result)

