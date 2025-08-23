import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from typing import List, Dict, Optional
import json
from urllib.parse import urljoin, urlparse

class RegulatorDiscoveryAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.regulator_urls = {
            'scottish': {
                'main': 'https://www.housingregulator.gov.scot',
                'landlord_list': 'https://www.housingregulator.gov.scot/for-tenants/landlord-performance',
                'data_downloads': 'https://www.housingregulator.gov.scot/about-us/what-we-do/research-and-findings',
                'register': 'https://www.housingregulator.gov.scot/for-landlords/registered-social-landlords'
            },
            'english': {
                'main': 'https://www.gov.uk/government/organisations/regulator-of-social-housing',
                'statistical_releases': 'https://www.gov.uk/government/collections/statistical-data-returns-statistical-releases',
                'provider_list': 'https://www.gov.uk/government/publications/current-registered-providers-of-social-housing',
                'global_accounts': 'https://www.gov.uk/government/collections/global-accounts-of-housing-providers'
            }
        }
    
    def discover_all_housing_associations(self, focus_region: str = 'scottish') -> List[Dict]:
        """Discover housing associations from official regulator sources"""
        print(f"Discovering {focus_region} housing associations from official regulators...")
        
        all_associations = []
        
        if focus_region == 'scottish' or focus_region == 'all':
            print("Getting Scottish housing associations...")
            scottish_associations = self._get_scottish_associations()
            all_associations.extend(scottish_associations)
            print(f"Found {len(scottish_associations)} Scottish associations")
        
        if focus_region == 'english' or focus_region == 'all':
            print("Getting English housing associations...")
            english_associations = self._get_english_associations()
            all_associations.extend(english_associations)
            print(f"Found {len(english_associations)} English associations")
        
        # Remove duplicates
        unique_associations = self._remove_duplicates(all_associations)
        print(f"Total unique associations: {len(unique_associations)}")
        
        # Enrich with Companies House data
        print("Enriching with Companies House data...")
        enriched_associations = self._enrich_with_companies_house(unique_associations)
        
        return enriched_associations
    
    def _get_scottish_associations(self) -> List[Dict]:
        """Get Scottish housing associations from Scottish Housing Regulator"""
        associations = []
        
        try:
            # Method 1: Get comprehensive Scottish list
            comprehensive_list = self._get_comprehensive_scottish_list()
            associations.extend(comprehensive_list)
            
            # Method 2: Try to find downloadable register/data
            data_sources = self._find_scottish_data_downloads()
            
            for source in data_sources:
                associations_from_source = self._extract_from_data_source(source)
                associations.extend(associations_from_source)
            
            # Method 3: Scrape landlord performance pages
            scraped_associations = self._scrape_scottish_landlord_list()
            associations.extend(scraped_associations)
                
        except Exception as e:
            print(f"Error getting Scottish associations: {e}")
        
        return associations
    
    def _get_comprehensive_scottish_list(self) -> List[Dict]:
        """Get comprehensive list of Scottish housing associations from multiple sources"""
        all_associations = []
        
        # Method 1: Known major Scottish housing associations
        known_scottish = [
            "Glasgow Housing Association", "Wheatley Group", "Sanctuary Scotland Housing Association",
            "Places for People Scotland", "Cairn Housing Association", "Fife Housing Association",
            "Trust Housing Association", "West Lothian Housing Partnership", "Clyde Valley Housing Association",
            "Dunedin Canmore Housing", "Link Housing Association", "Riverside Scotland",
            "Albyn Housing Society", "Blackwood Homes and Care", "Bield Housing & Care",
            "Hanover (Scotland) Housing Association", "Orkney Islands Council", "Shetland Islands Council",
            "Western Isles Council", "Highland Council", "Argyll Community Housing Association",
            "Ayrshire Housing", "Berwickshire Housing Association", "Borders Housing Association",
            "Castle Rock Edinvar Housing Association", "Clydebank Housing Association",
            "Cumnock & Doon Valley Housing Association", "East Lothian Housing Association",
            "Eildon Housing Association", "Falkirk Council", "Glasgow City Council",
            "Grampian Housing Association", "Horizon Housing Association", "Irvine Housing Association",
            "Kingdom Housing Association", "Langstane Housing Association", "Linthouse Housing Association",
            "Loreburn Housing Association", "Manor Estates Housing Association", "Melville Housing Association",
            "New Gorbals Housing Association", "North Lanarkshire Council", "Orkney Housing Association",
            "Paragon Housing Association", "Pentland Housing Association", "Queens Cross Housing Association",
            "Rural Stirling Housing Association", "Scottish Borders Housing Association",
            "South of Scotland Community Housing", "Southside Housing Association", "Stirling Council",
            "Thenue Housing Association", "Viewpoint Housing Association", "West Highland Housing Association",
            "Weslo Housing Management", "Wishaw & District Housing Association", "Yoker Housing Association",
            "Cordale Housing Association", "Cube Housing Association", "Dumfries and Galloway Housing Partnership",
            "East Ayrshire Council", "East Dunbartonshire Council", "East Renfrewshire Council",
            "Inverclyde Council", "Midlothian Council", "Moray Council", "North Ayrshire Council",
            "Perth and Kinross Council", "Renfrewshire Council", "South Ayrshire Council",
            "South Lanarkshire Council", "West Dunbartonshire Council", "Aberdeen City Council",
            "Aberdeenshire Council", "Angus Council", "Argyll and Bute Council", "City of Edinburgh Council",
            "Clackmannanshire Council", "Dundee City Council", "Comhairle nan Eilean Siar"
        ]
        
        for name in known_scottish:
            all_associations.append({
                'name': name,
                'region': 'Scotland',
                'source': 'Known Scottish Housing Association'
            })
        
        # Method 2: Search Scottish Housing Regulator data
        regulator_associations = self._scrape_scottish_regulator_comprehensive()
        all_associations.extend(regulator_associations)
        
        # Method 3: Search local authority housing departments
        council_housing = self._get_scottish_council_housing()
        all_associations.extend(council_housing)
        
        return all_associations

    def _scrape_scottish_regulator_comprehensive(self) -> List[Dict]:
        """Comprehensive scraping of Scottish Housing Regulator"""
        associations = []
        
        try:
            # Try multiple regulator pages
            regulator_pages = [
                "https://www.housingregulator.gov.scot/for-landlords/registered-social-landlords",
                "https://www.housingregulator.gov.scot/for-tenants/landlord-performance",
                "https://www.housingregulator.gov.scot/about-us/what-we-do/regulation",
                "https://www.housingregulator.gov.scot/landlord-performance"
            ]
            
            for page_url in regulator_pages:
                try:
                    print(f"Checking: {page_url}")
                    response = self.session.get(page_url, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for any links or text mentioning housing associations
                    text = soup.get_text().lower()
                    
                    # Extract potential housing association names from text
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if len(line) > 10 and 'housing' in line.lower():
                            # Clean up the line
                            cleaned = re.sub(r'[^\w\s&-]', '', line).strip()
                            if self._looks_like_housing_association(cleaned):
                                associations.append({
                                    'name': cleaned.title(),
                                    'region': 'Scotland',
                                    'source': f'Scottish Regulator - {page_url}'
                                })
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error checking {page_url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in comprehensive regulator scraping: {e}")
        
        return associations

    def _get_scottish_council_housing(self) -> List[Dict]:
        """Get Scottish council housing departments"""
        scottish_councils = [
            "Aberdeen City Council", "Aberdeenshire Council", "Angus Council",
            "Argyll and Bute Council", "City of Edinburgh Council", "Clackmannanshire Council",
            "Dumfries and Galloway Council", "Dundee City Council", "East Ayrshire Council",
            "East Dunbartonshire Council", "East Lothian Council", "East Renfrewshire Council",
            "Falkirk Council", "Fife Council", "Glasgow City Council",
            "Highland Council", "Inverclyde Council", "Midlothian Council",
            "Moray Council", "North Ayrshire Council", "North Lanarkshire Council",
            "Orkney Islands Council", "Perth and Kinross Council", "Renfrewshire Council",
            "Scottish Borders Council", "Shetland Islands Council", "South Ayrshire Council",
            "South Lanarkshire Council", "Stirling Council", "West Dunbartonshire Council",
            "West Lothian Council", "Western Isles Council"
        ]
        
        council_housing = []
        for council in scottish_councils:
            council_housing.append({
                'name': f"{council} Housing",
                'region': 'Scotland',
                'source': 'Scottish Local Authority Housing'
            })
        
        return council_housing
    
    def _find_scottish_data_downloads(self) -> List[Dict]:
        """Find downloadable data files from Scottish Housing Regulator"""
        data_sources = []
        
        try:
            # Check main data/research pages
            urls_to_check = [
                self.regulator_urls['scottish']['data_downloads'],
                self.regulator_urls['scottish']['register'],
                f"{self.regulator_urls['scottish']['main']}/publications"
            ]
            
            for url in urls_to_check:
                try:
                    response = self.session.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for downloadable files (CSV, Excel, PDF)
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        text = link.get_text().lower()
                        
                        if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', '.pdf']):
                            if any(keyword in text for keyword in ['landlord', 'provider', 'register', 'list']):
                                data_sources.append({
                                    'url': urljoin(url, href),
                                    'type': self._get_file_type(href),
                                    'description': text.strip()
                                })
                                
                except Exception as e:
                    print(f"Error checking {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error finding Scottish data downloads: {e}")
        
        return data_sources
    
    def _scrape_scottish_landlord_list(self) -> List[Dict]:
        """Scrape Scottish landlord performance pages"""
        associations = []
        
        try:
            # Try landlord performance page
            response = self.session.get(self.regulator_urls['scottish']['landlord_list'], timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for landlord names and links
            for link in soup.find_all('a', href=True):
                text = link.get_text().strip()
                
                # Filter for housing association names
                if self._looks_like_housing_association(text):
                    associations.append({
                        'name': text,
                        'regulator_url': urljoin(self.regulator_urls['scottish']['main'], link['href']),
                        'region': 'Scotland',
                        'source': 'Scottish Housing Regulator'
                    })
            
            # Also check for any tables or lists
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        text = cells[0].get_text().strip()
                        if self._looks_like_housing_association(text):
                            associations.append({
                                'name': text,
                                'region': 'Scotland',
                                'source': 'Scottish Housing Regulator Table'
                            })
                            
        except Exception as e:
            print(f"Error scraping Scottish landlord list: {e}")
        
        return associations
    
    def _get_english_associations(self) -> List[Dict]:
        """Get English housing associations from Regulator of Social Housing"""
        associations = []
        
        try:
            # Method 1: Look for official provider register
            register_data = self._find_english_provider_register()
            associations.extend(register_data)
            
            # Method 2: Statistical data releases
            if not associations:
                statistical_data = self._get_english_statistical_data()
                associations.extend(statistical_data)
            
            # Method 3: Known major English housing associations
            if not associations:
                known_english = self._get_known_english_associations()
                associations.extend(known_english)
                
        except Exception as e:
            print(f"Error getting English associations: {e}")
        
        return associations
    
    def _find_english_provider_register(self) -> List[Dict]:
        """Find English registered provider list"""
        associations = []
        
        try:
            # Check provider list page
            response = self.session.get(self.regulator_urls['english']['provider_list'], timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for downloadable register
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower()
                
                if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls']):
                    if 'provider' in text or 'register' in text:
                        # Found downloadable register
                        register_url = urljoin(self.regulator_urls['english']['provider_list'], href)
                        associations = self._extract_from_data_source({
                            'url': register_url,
                            'type': self._get_file_type(href),
                            'description': text
                        })
                        break
                        
        except Exception as e:
            print(f"Error finding English provider register: {e}")
        
        return associations
    
    def _get_known_english_associations(self) -> List[Dict]:
        """Get known major English housing associations"""
        known_english = [
            "Clarion Housing Group", "L&Q", "Peabody", "Sanctuary Housing Association",
            "Places for People", "Notting Hill Genesis", "Riverside", "A2Dominion",
            "Hyde Housing Association", "Metropolitan Thames Valley Housing",
            "Guinness Partnership", "Orbit Group", "Bromford", "Accent Group",
            "Aster Group", "Cross Keys Homes", "Flagship Housing Group",
            "Great Places Housing Group", "Halton Housing Trust", "Homes England",
            "Housing & Care 21", "Incommunities", "Karbon Homes", "LiveWest",
            "Magna Housing Group", "Midland Heart", "Onward Homes", "Platform Housing Group",
            "Progress Housing Group", "Raven Housing Trust", "Red Kite Community Housing",
            "Rooftop Housing Group", "Sage Housing", "Sovereign Housing Association",
            "Stonewater", "The Guinness Partnership", "Together Housing Group",
            "Torus", "Vivid Housing", "Watford Community Housing", "WM Housing Group",
            "Yorkshire Housing", "Your Housing Group"
        ]
        
        associations = []
        for name in known_english:
            associations.append({
                'name': name,
                'region': 'England',
                'source': 'Known English Housing Association'
            })
        
        return associations
    
    def _extract_from_data_source(self, source: Dict) -> List[Dict]:
        """Extract housing association data from downloadable source"""
        associations = []
        
        try:
            print(f"Downloading: {source['description']}")
            response = self.session.get(source['url'], timeout=30)
            
            if source['type'] == 'csv':
                # Handle CSV files
                try:
                    import io
                    df = pd.read_csv(io.StringIO(response.text))
                    associations = self._extract_from_dataframe(df)
                except Exception as e:
                    print(f"Error reading CSV: {e}")
                    
            elif source['type'] in ['xlsx', 'xls']:
                # Handle Excel files
                try:
                    df = pd.read_excel(response.content)
                    associations = self._extract_from_dataframe(df)
                except Exception as e:
                    print(f"Error reading Excel: {e}")
                    
            elif source['type'] == 'pdf':
                # For PDF, we'd need additional libraries
                print(f"PDF extraction not implemented yet: {source['url']}")
                
        except Exception as e:
            print(f"Error extracting from data source: {e}")
        
        return associations
    
    def _extract_from_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        """Extract housing associations from pandas DataFrame"""
        associations = []
        
        try:
            # Look for columns that might contain housing association names
            name_columns = []
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['name', 'landlord', 'provider', 'organisation', 'company']):
                    name_columns.append(col)
            
            if not name_columns:
                # Use first column as default
                name_columns = [df.columns[0]]
            
            for _, row in df.iterrows():
                for col in name_columns:
                    name = str(row[col]).strip()
                    if name and name != 'nan' and self._looks_like_housing_association(name):
                        association = {
                            'name': name,
                            'source': 'Regulator Data File'
                        }
                        
                        # Try to extract additional data from other columns
                        for other_col in df.columns:
                            if other_col != col:
                                col_lower = str(other_col).lower()
                                value = row[other_col]
                                
                                if 'region' in col_lower or 'area' in col_lower:
                                    association['region'] = str(value)
                                elif 'number' in col_lower and 'company' in col_lower:
                                    association['company_number'] = str(value)
                                elif 'units' in col_lower or 'homes' in col_lower:
                                    association['housing_units'] = value
                        
                        associations.append(association)
                        break  # Only take first valid name per row
                        
        except Exception as e:
            print(f"Error extracting from DataFrame: {e}")
        
        return associations
    
    def _looks_like_housing_association(self, text: str) -> bool:
        """Check if text looks like a housing association name"""
        if not text or len(text) < 5:
            return False
            
        text_lower = text.lower()
        
        # Must contain housing-related terms
        housing_terms = [
            'housing', 'homes', 'residential', 'accommodation',
            'landlord', 'provider', 'society', 'trust'
        ]
        
        has_housing_term = any(term in text_lower for term in housing_terms)
        
        # Exclude obvious non-housing entities
        exclusions = [
            'council', 'authority', 'department', 'ministry',
            'government', 'regulator', 'total', 'average'
        ]
        
        has_exclusion = any(exclusion in text_lower for exclusion in exclusions)
        
        return has_housing_term and not has_exclusion
    
    def _remove_duplicates(self, associations: List[Dict]) -> List[Dict]:
        """Remove duplicate associations based on name similarity"""
        unique_associations = []
        seen_names = set()
        
        for association in associations:
            name = association.get('name', '').lower().strip()
            
            # Clean name for comparison
            clean_name = re.sub(r'\b(limited|ltd|association|society|group|homes|housing)\b', '', name).strip()
            clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
            
            if clean_name and clean_name not in seen_names:
                seen_names.add(clean_name)
                unique_associations.append(association)
        
        return unique_associations
    
    def _enrich_with_companies_house(self, associations: List[Dict]) -> List[Dict]:
        """Enrich regulator data with Companies House information"""
        from utils.companies_house_api import CompaniesHouseAPI
        
        enriched = []
        companies_house = CompaniesHouseAPI()
        
        print(f"Enriching {len(associations)} associations with Companies House data...")
        
        for i, association in enumerate(associations, 1):
            enriched_assoc = association.copy()
            name = association.get('name', '')
            
            if i % 10 == 0:
                print(f"Processed {i}/{len(associations)} associations")
            
            try:
                # Search Companies House for this association
                search_results = companies_house.search_companies(name)
                
                # Find best match
                best_match = self._find_best_companies_house_match(name, search_results)
                
                if best_match:
                    # Get detailed company information
                    company_details = companies_house.get_company_details(best_match['company_number'])
                    
                    if company_details:
                        # Merge Companies House data
                        enriched_assoc.update({
                            'company_number': company_details.get('company_number'),
                            'company_name': company_details.get('company_name'),
                            'company_status': company_details.get('company_status'),
                            'incorporation_date': company_details.get('date_of_creation'),
                            'company_type': company_details.get('type'),
                            'registered_office_address': company_details.get('registered_office_address'),
                            'sic_codes': company_details.get('sic_codes', [])
                        })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error enriching {name}: {e}")
                time.sleep(1)  # Extra delay on error
            
            enriched.append(enriched_assoc)
        
        return enriched
    
    def _find_best_companies_house_match(self, target_name: str, search_results: List[Dict]) -> Optional[Dict]:
        """Find best matching company from search results"""
        if not search_results:
            return None
        
        target_lower = target_name.lower()
        
        # Look for exact or very close matches
        for result in search_results:
            result_name = result.get('title', '').lower()
            
            # Exact match
            if target_lower == result_name:
                return result
            
            # Close match (remove common suffixes)
            target_clean = re.sub(r'\b(limited|ltd|association|society|group|homes|housing)\b', '', target_lower).strip()
            result_clean = re.sub(r'\b(limited|ltd|association|society|group|homes|housing)\b', '', result_name).strip()
            
            if target_clean and result_clean and target_clean in result_clean:
                return result
        
        # Return first result if no close match
        return search_results[0] if search_results else None
    
    def _get_file_type(self, url: str) -> str:
        """Get file type from URL"""
        if '.csv' in url.lower():
            return 'csv'
        elif '.xlsx' in url.lower():
            return 'xlsx'
        elif '.xls' in url.lower():
            return 'xls'
        elif '.pdf' in url.lower():
            return 'pdf'
        else:
            return 'unknown'
    
    def _get_english_statistical_data(self) -> List[Dict]:
        """Get English housing associations from statistical releases"""
        # This would involve parsing statistical data releases
        # For now, return empty list - can be implemented later
        return []