import os
from dotenv import load_dotenv

# Test loading the environment file
load_dotenv('config/api_keys.env')

api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
print(f"API Key loaded: {api_key}")
print(f"API Key length: {len(api_key) if api_key else 'None'}")

if api_key:
    # Test a simple API call
    import requests
    
    url = "https://api.company-information.service.gov.uk/search/companies"
    params = {'q': 'test', 'items_per_page': 1}
    
    response = requests.get(url, params=params, auth=(api_key, ''))
    print(f"API Response Status: {response.status_code}")
    print(f"API Response: {response.text[:200]}...")
else:
    print("No API key found!")