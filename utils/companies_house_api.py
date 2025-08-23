import requests
import time
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv('config/api_keys.env')

class CompaniesHouseAPI:
    def __init__(self):
        self.api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
        self.base_url = "https://api.company-information.service.gov.uk"
        self.session = requests.Session()
        self.session.auth = (self.api_key, '')
        
    def search_companies(self, query: str, items_per_page: int = 100) -> List[Dict]:
        """Search for companies by name or other criteria"""
        url = f"{self.base_url}/search/companies"
        params = {
            'q': query,
            'items_per_page': items_per_page
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except requests.RequestException as e:
            print(f"Error searching companies: {e}")
            return []
    
    def get_company_details(self, company_number: str) -> Optional[Dict]:
        """Get detailed information about a specific company"""
        url = f"{self.base_url}/company/{company_number}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting company details for {company_number}: {e}")
            return None
    
    def get_company_officers(self, company_number: str) -> List[Dict]:
        """Get officers (directors) of a company"""
        url = f"{self.base_url}/company/{company_number}/officers"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except requests.RequestException as e:
            print(f"Error getting officers for {company_number}: {e}")
            return []
    
    def get_filing_history(self, company_number: str, items_per_page: int = 20) -> List[Dict]:
        """Get filing history for a company"""
        url = f"{self.base_url}/company/{company_number}/filing-history"
        params = {'items_per_page': items_per_page}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except requests.RequestException as e:
            print(f"Error getting filing history for {company_number}: {e}")
            return []