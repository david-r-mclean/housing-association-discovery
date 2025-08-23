import yaml
from typing import List, Dict
from utils.companies_house_api import CompaniesHouseAPI
from tqdm import tqdm
import time

class HousingAssociationDiscovery:
    def __init__(self, config_path: str = 'config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.companies_house = CompaniesHouseAPI()
        self.discovered_associations = []
        
    def run_full_discovery(self) -> List[Dict]:
        """Run complete discovery process"""
        print("Starting housing association discovery...")
        
        # 1. Search Companies House
        print("Searching Companies House...")
        raw_candidates = self.search_multiple_strategies()
        print(f"Found {len(raw_candidates)} initial candidates")
        
        # 2. Validate and filter
        print("Validating candidates...")
        validated = self.validate_housing_associations(raw_candidates)
        print(f"Validated {len(validated)} housing associations")
        
        # 3. Enrich with additional data
        print("Enriching with additional data...")
        enriched = self.enrich_associations(validated)
        
        self.discovered_associations = enriched
        return enriched
    
    def search_multiple_strategies(self) -> List[Dict]:
        """Use multiple search strategies to find housing associations"""
        all_candidates = []
        seen_companies = set()
        
        # Strategy 1: Search by housing terms
        for term in self.config['search']['housing_terms']:
            print(f"Searching for: {term}")
            results = self.companies_house.search_companies(term)
            
            for company in results:
                company_number = company.get('company_number')
                if company_number not in seen_companies:
                    seen_companies.add(company_number)
                    all_candidates.append(company)
            
            time.sleep(2)  # Increased rate limiting
        
        return all_candidates
    
    def validate_housing_associations(self, candidates: List[Dict]) -> List[Dict]:
        """Validate that candidates are actually housing associations"""
        validated = []
        
        for company in tqdm(candidates, desc="Validating companies"):
            if self.is_likely_housing_association(company):
                # Get full company details
                details = self.companies_house.get_company_details(company['company_number'])
                if details and self.validate_company_details(details):
                    validated.append(details)
            
            time.sleep(0.5)  # Increased rate limiting
        
        return validated
    
    def is_likely_housing_association(self, company: Dict) -> bool:
        """Check if company name suggests it's a housing association"""
        name = company.get('title', '').lower()
        
        housing_indicators = [
            'housing association', 'housing society', 'housing trust',
            'community housing', 'social housing', 'registered provider',
            'homes', 'housing group', 'housing company', 'housing co-operative'
        ]
        
        # Must contain housing-related terms
        has_housing_term = any(indicator in name for indicator in housing_indicators)
        
        # Exclude obvious non-housing companies
        exclusions = [
            'construction', 'development', 'property management',
            'estate agent', 'letting agent', 'property investment'
        ]
        has_exclusion = any(exclusion in name for exclusion in exclusions)
        
        return has_housing_term and not has_exclusion
    
    def validate_company_details(self, details: Dict) -> bool:
        """Validate company details to confirm it's a housing association"""
        # Check company status
        if details.get('company_status') != 'active':
            return False
        
        # Check SIC codes if available
        sic_codes = details.get('sic_codes', [])
        target_sics = self.config['search']['sic_codes']
        
        if sic_codes:
            has_relevant_sic = any(sic in target_sics for sic in sic_codes)
            if not has_relevant_sic:
                return False
        
        return True
    
    def enrich_associations(self, associations: List[Dict]) -> List[Dict]:
        """Enrich associations with additional data - SLOW BUT RELIABLE"""
        enriched = []
        
        print(f"Starting enrichment of {len(associations)} associations...")
        print("This will take ~30-45 minutes due to rate limiting, but will be reliable.")
        
        for i, association in enumerate(associations, 1):
            enriched_data = association.copy()
            company_name = association.get('company_name', 'Unknown')
            
            print(f"\n[{i}/{len(associations)}] Processing: {company_name}")
            
            # Get officers information with retry logic
            officers_count = 0
            officers = []
            for attempt in range(3):  # 3 attempts
                try:
                    officers = self.companies_house.get_company_officers(association['company_number'])
                    officers_count = len(officers)
                    break
                except Exception as e:
                    if "429" in str(e):
                        wait_time = 30 * (attempt + 1)  # 30, 60, 90 seconds
                        print(f"  Rate limited on officers, waiting {wait_time}s (attempt {attempt + 1}/3)")
                        time.sleep(wait_time)
                    else:
                        print(f"  Error getting officers: {e}")
                        break
            
            enriched_data['officers_count'] = officers_count
            enriched_data['officers'] = officers[:5]  # Top 5 officers
            
            # Small delay between API calls
            time.sleep(2)
            
            # Get filing history with retry logic
            recent_filings = 0
            last_filing_date = None
            for attempt in range(3):  # 3 attempts
                try:
                    filings = self.companies_house.get_filing_history(association['company_number'])
                    recent_filings = len(filings)
                    last_filing_date = filings[0].get('date') if filings else None
                    break
                except Exception as e:
                    if "429" in str(e):
                        wait_time = 30 * (attempt + 1)  # 30, 60, 90 seconds
                        print(f"  Rate limited on filings, waiting {wait_time}s (attempt {attempt + 1}/3)")
                        time.sleep(wait_time)
                    else:
                        print(f"  Error getting filings: {e}")
                        break
            
            enriched_data['recent_filings'] = recent_filings
            enriched_data['last_filing_date'] = last_filing_date
            
            enriched.append(enriched_data)
            
            # Longer delay between companies
            time.sleep(3)
            
            # Progress update every 10 companies
            if i % 10 == 0:
                print(f"\nCompleted {i}/{len(associations)} associations ({i/len(associations)*100:.1f}%)")
                remaining = len(associations) - i
                estimated_minutes = remaining * 0.3  # ~18 seconds per association
                print(f"Estimated time remaining: {estimated_minutes:.1f} minutes")
        
        return enriched