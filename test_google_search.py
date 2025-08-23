import os
import requests
from dotenv import load_dotenv

load_dotenv('config/api_keys.env')

api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

print(f"API Key: {api_key[:20]}..." if api_key else "No API key")
print(f"Search Engine ID: {search_engine_id}")

if api_key and search_engine_id:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': 'test search',
        'num': 1
    }
    
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Google Search API working!")
    else:
        print(f"❌ Error: {response.text}")