import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import json
import duckdb
import google.generativeai as genai
from src.utils.config import setup_gemini

# 1. Setup
setup_gemini()
model = genai.GenerativeModel('models/gemini-3.5-flash')

# 2. Get unique values from your DB
con = duckdb.connect('data/airbnb_warehouse.db')
raw_types = [row[0] for row in con.execute('SELECT DISTINCT property_type FROM dim_listings').fetchall()]

# 3. Prompt the LLM for structured JSON
prompt = f"""
You are a data cleaning expert. Map the following Airbnb property types to one of these 4 canonical categories:
['Entire Home', 'Private Room', 'Shared Room', 'Other'].

Return ONLY a valid JSON dictionary where:
- Keys are the original property types.
- Values are the canonical categories.

Property types to map: {raw_types}
"""

response = model.generate_content(prompt)

# 4. Clean and parse the response
json_text = response.text.replace('```json', '').replace('```', '').strip()
mapping = json.loads(json_text)

# 5. Save the mapping to a file for review
with open('data/property_type_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=4)

print("Mapping created and saved to data/property_type_mapping.json")