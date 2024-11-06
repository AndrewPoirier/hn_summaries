import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load settings from settings.json
with open('openai_settings.json', 'r') as f:
    settings = json.load(f)

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

def summarize(url):
    # Use the OpenAI API to summarize the text
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # You can use "gpt-4" if available
        messages=[
            {"role": "system", "content": settings['prompt']},
            {"role": "user", "content": f"Summarize the following website: {url}"}
        ],
        max_tokens=150  # Limit the summary length
    )
    
    summary_obj = completion.choices[0].message
    return summary_obj.content