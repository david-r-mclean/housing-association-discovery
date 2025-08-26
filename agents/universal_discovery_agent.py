"""
Universal Discovery Agent
Flexible discovery system that works across multiple industries
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import re

from config.industry_configs import IndustryConfigManager, IndustryType, IndustryConfig, DataSource

logger = logging.getLogger(__name__)

class UniversalDiscoveryAgent:
    """Universal agent for discovering organizations across different industries"""
    
    def __init__(self, industry_type: IndustryType = None, custom_config: IndustryConfig = None):
        self.config_manager = IndustryConfigManager()
        
        if custom_config:
            self.config = custom_config
        elif industry_type:
            self.config = self.config_manager.get_config(industry_type)
        else:
            self.config = self.config_manager.get_config(IndustryType.HOUSING_ASSOCIATIONS)  # Default
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"Initialized Universal Discovery Agent for: {self.config.name}")
    
    def discover_organizations(self, 
                             region: str = "all", 
                             limit: Optional[int] = None,
                             custom_keywords: List[str] = None,
                             custom_sources: List[DataSource] = None) -> List[Dict]:
        """
        Discover organizations based on configuration and parameters
        
        Args:
            region: Geographic region to focus on
            limit: Maximum number of organizations to discover
            custom_keywords: Additional search keywords
            custom_sources: Custom data sources to use
        
        Returns:
            List of discovered organizations
        """
        
        logger.info(f"Starting discovery for {self.config.name} in region: {region}")
        
        # Combine keywords
        search_keywords = self.config.search_keywords.copy()
        if custom_keywords:
            search_keywords.extend(custom_keywords)
        
        # Use custom sources or default config sources
        data_sources = custom_sources or self.config.data_sources
        
        all_organizations = []
        
        for source in data_sources:
            try:
                logger.info(f"Discovering from source: {source.name}")
                
                organizations = self._discover_from_source(source, region, search_keywords, limit)
                
                # Add source information to each organization
                for org in organizations:
                    org['discovery_source'] = source.name
                    org['discovery_date'] = datetime.now().isoformat()
                    org['industry_type'] = self.config.industry_type.value
                    org['region'] = region
                
                all_organizations.extend(organizations)
                
                # Respect rate limits
                time.sleep(source.rate_limit)
                
                logger.info(f"Discovered {len(organizations)} organizations from {source.name}")
                
            except Exception as e:
                logger.error(f"Error discovering from {source.name}: {e}")
                continue
        
        # Remove duplicates
        unique_organizations = self._deduplicate_organizations(all_organizations)
        
        # Apply limit if specified
        if limit:
            unique_organizations = unique_organizations[:limit]
        
        logger.info(f"Total unique organizations discovered: {len(unique_organizations)}")
        
        return unique_organizations
    
    def _discover_from_source(self, 
                            source: DataSource, 
                            region: str, 
                            keywords: List[str], 
                            limit: Optional[int]) -> List[Dict]:
        """Discover organizations from a specific data source"""
        
        if source.type == "regulator":
            return self._discover_from_regulator(source, region, keywords, limit)
        elif source.type == "api":
            return self._discover_from_api(source, region, keywords, limit)
        elif source.type == "directory":
            return self._discover_from_directory(source, region, keywords, limit)
        elif source.type == "scrape":
            return self._discover_from_scraping(source, region, keywords, limit)
        else:
            logger.warning(f"Unknown source type: {source.type}")
            return []
    
    def _discover_from_regulator(self, 
                               source: DataSource, 
                               region: str, 
                               keywords: List[str], 
                               limit: Optional[int]) -> List[Dict]:
        """Discover from regulatory websites"""
        organizations = []
        
        try:
            # Build search URL based on source configuration
            search_url = self._build_search_url(source, region, keywords)
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract organizations based on common patterns
            organizations = self._extract_organizations_from_html(soup, source)
            
        except Exception as e:
            logger.error(f"Error discovering from regulator {source.name}: {e}")
        
        return organizations[:limit] if limit else organizations
    
    def _discover_from_api(self, 
                         source: DataSource, 
                         region: str, 
                         keywords: List[str], 
                         limit: Optional[int]) -> List[Dict]:
        """Discover from API endpoints"""
        organizations = []
        
        try:
            # Handle Companies House API
            if "companies-house" in source.url.lower() or "company-information" in source.url.lower():
                organizations = self._discover_from_companies_house(source, region, keywords, limit)
            
            # Handle Charity Commission API
            elif "charity" in source.url.lower():
                organizations = self._discover_from_charity_api(source, region, keywords, limit)
            
            # Handle other APIs
            else:
                organizations = self._discover_from_generic_api(source, region, keywords, limit)
                
        except Exception as e:
            logger.error(f"Error discovering from API {source.name}: {e}")
        
        return organizations
    
    def _discover_from_directory(self, 
                               source: DataSource, 
                               region: str, 
                               keywords: List[str], 
                               limit: Optional[int]) -> List[Dict]:
        """Discover from directory websites"""
        organizations = []
        
        try:
            # Search directory pages
            for keyword in keywords[:3]:  # Limit to avoid overwhelming
                search_url = f"{source.url}/search?q={keyword}&region={region}"
                
                response = self.session.get(search_url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    orgs = self._extract_organizations_from_html(soup, source)
                    organizations.extend(orgs)
                
                time.sleep(1)  # Be respectful
                
        except Exception as e:
            logger.error(f"Error discovering from directory {source.name}: {e}")
        
        return organizations[:limit] if limit else organizations
    
    def _discover_from_scraping(self, 
                              source: DataSource, 
                              region: str, 
                              keywords: List[str], 
                              limit: Optional[int]) -> List[Dict]:
        """Discover through web scraping"""
        organizations = []
        
        try:
            response = self.session.get(source.url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            organizations = self._extract_organizations_from_html(soup, source)
            
        except Exception as e:
            logger.error(f"Error scraping from {source.name}: {e}")
        
        return organizations[:limit] if limit else organizations
    
    def _discover_from_companies_house(self, 
                                     source: DataSource, 
                                     region: str, 
                                     keywords: List[str], 
                                     limit: Optional[int]) -> List[Dict]:
        """Discover from Companies House using search"""
        organizations = []
        
        try:
            # Use the existing Companies House search functionality
            from agents.companies_house_agent import CompaniesHouseAgent
            
            ch_agent = CompaniesHouseAgent()
            
            # Search by SIC codes if specified
            if self.config.sic_codes:
                for sic_code in self.config.sic_codes[:3]:  # Limit searches
                    results = ch_agent.search_companies_by_sic_code(sic_code, limit=50)
                    organizations.extend(results)
            
            # Search by keywords
            for keyword in keywords[:3]:
                results = ch_agent.search_companies(keyword, limit=50)
                organizations.extend(results)
                
        except Exception as e:
            logger.error(f"Error discovering from Companies House: {e}")
        
        return organizations[:limit] if limit else organizations
    
    def _discover_from_charity_api(self, 
                                 source: DataSource, 
                                 region: str, 
                                 keywords: List[str], 
                                 limit: Optional[int]) -> List[Dict]:
        """Discover from charity APIs"""
        organizations = []
        
        try:
            # Implement charity API searches based on region
            if "england" in region.lower() or "wales" in region.lower():
                # England & Wales Charity Commission
                organizations = self._search_charity_commission_ew(keywords, limit)
            elif "scotland" in region.lower():
                # Scottish Charity Regulator (OSCR)
                organizations = self._search_oscr(keywords, limit)
            elif "northern_ireland" in region.lower():
                # Northern Ireland Charity Commission
                organizations = self._search_charity_commission_ni(keywords, limit)
                
        except Exception as e:
            logger.error(f"Error discovering from charity API: {e}")
        
        return organizations
    
    def _discover_from_generic_api(self, 
                                 source: DataSource, 
                                 region: str, 
                                 keywords: List[str], 
                                 limit: Optional[int]) -> List[Dict]:
        """Discover from generic API endpoints"""
        organizations = []
        
        try:
            # Build API request based on source configuration
            api_params = source.search_params.copy()
            api_params.update({
                'region': region,
                'keywords': ','.join(keywords[:3]),
                'limit': limit or 100
            })
            
            response = self.session.get(source.url, params=api_params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                organizations = self._parse_api_response(data, source)
                
        except Exception as e:
            logger.error(f"Error discovering from generic API {source.name}: {e}")
        
        return organizations
    
    def _extract_organizations_from_html(self, soup: BeautifulSoup, source: DataSource) -> List[Dict]:
        """Extract organization data from HTML"""
        organizations = []
        
        try:
            # Look for common patterns in HTML structure
            
            # Try table rows
            for row in soup.find_all('tr')[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    org = self._extract_org_from_table_row(cells, source)
                    if org:
                        organizations.append(org)
            
            # Try list items
            for item in soup.find_all('li'):
                org = self._extract_org_from_list_item(item, source)
                if org:
                    organizations.append(org)
            
            # Try div containers with organization data
            for div in soup.find_all('div', class_=re.compile(r'(organization|company|charity|result)', re.I)):
                org = self._extract_org_from_div(div, source)
                if org:
                    organizations.append(org)
                    
        except Exception as e:
            logger.error(f"Error extracting organizations from HTML: {e}")
        
        return organizations
    
    def _extract_org_from_table_row(self, cells, source: DataSource) -> Optional[Dict]:
        """Extract organization data from table row"""
        try:
            org = {}
            
            # Map cells to data fields based on source configuration
            for i, field in enumerate(source.data_fields):
                if i < len(cells):
                    org[field] = cells[i].get_text(strip=True)
            
            # Ensure we have at least a name
            if org.get('name') or org.get('company_name') or org.get('charity_name'):
                return org
                
        except Exception as e:
            logger.error(f"Error extracting from table row: {e}")
        
        return None
    
    def _extract_org_from_list_item(self, item, source: DataSource) -> Optional[Dict]:
        """Extract organization data from list item"""
        try:
            text = item.get_text(strip=True)
            
            # Look for organization names and details
            if any(keyword.lower() in text.lower() for keyword in self.config.search_keywords):
                org = {
                    'name': text[:100],  # Truncate long names
                    'source_text': text
                }
                
                # Try to extract additional details
                links = item.find_all('a')
                if links:
                    org['website'] = links[0].get('href')
                
                return org
                
        except Exception as e:
            logger.error(f"Error extracting from list item: {e}")
        
        return None
    
    def _extract_org_from_div(self, div, source: DataSource) -> Optional[Dict]:
        """Extract organization data from div container"""
        try:
            org = {}
            
            # Look for name in various elements
            name_elem = div.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
            if name_elem:
                org['name'] = name_elem.get_text(strip=True)
            
            # Look for links
            link_elem = div.find('a')
            if link_elem:
                org['website'] = link_elem.get('href')
            
            # Extract all text for additional processing
            org['source_text'] = div.get_text(strip=True)
            
            if org.get('name'):
                return org
                
        except Exception as e:
            logger.error(f"Error extracting from div: {e}")
        
        return None
    
    def _build_search_url(self, source: DataSource, region: str, keywords: List[str]) -> str:
        """Build search URL for a data source"""
        base_url = source.url
        
        # Add search parameters
        params = []
        
        if keywords:
            params.append(f"q={'+'.join(keywords[:3])}")
        
        if region and region != "all":
            params.append(f"region={region}")
        
        # Add source-specific parameters
        for key, value in source.search_params.items():
            params.append(f"{key}={value}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        
        return base_url
    
    def _parse_api_response(self, data: Dict, source: DataSource) -> List[Dict]:
        """Parse API response data"""
        organizations = []
        
        try:
            # Handle different API response formats
            if isinstance(data, list):
                organizations = data
            elif isinstance(data, dict):
                # Look for common keys that contain the data
                for key in ['results', 'data', 'items', 'organizations', 'companies', 'charities']:
                    if key in data and isinstance(data[key], list):
                        organizations = data[key]
                        break
            
            # Ensure each organization has required fields
            processed_orgs = []
            for org in organizations:
                if isinstance(org, dict):
                    # Map API fields to standard fields
                    processed_org = self._map_api_fields(org, source)
                    if processed_org:
                        processed_orgs.append(processed_org)
            
            return processed_orgs
            
        except Exception as e:
            logger.error(f"Error parsing API response: {e}")
            return []
    
    def _map_api_fields(self, org_data: Dict, source: DataSource) -> Optional[Dict]:
        """Map API fields to standard organization fields"""
        try:
            mapped_org = {}
            
            # Common field mappings
            field_mappings = {
                'name': ['name', 'company_name', 'charity_name', 'organisation_name', 'title'],
                'registration_number': ['registration_number', 'company_number', 'charity_number', 'reg_no'],
                'status': ['status', 'company_status', 'charity_status'],
                'website': ['website', 'url', 'web_address'],
                'address': ['address', 'registered_office_address', 'location'],
                'description': ['description', 'activities', 'purposes', 'objects']
            }
            
            # Map fields
            for standard_field, possible_fields in field_mappings.items():
                for field in possible_fields:
                    if field in org_data:
                        mapped_org[standard_field] = org_data[field]
                        break
            
            # Include all original data
            mapped_org['original_data'] = org_data
            
            # Ensure we have at least a name
            if mapped_org.get('name'):
                return mapped_org
                
        except Exception as e:
            logger.error(f"Error mapping API fields: {e}")
        
        return None
    
    def _deduplicate_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """Remove duplicate organizations"""
        seen = set()
        unique_orgs = []
        
        for org in organizations:
            # Create a key for deduplication
            name = org.get('name', '').lower().strip()
            reg_number = org.get('registration_number', '').strip()
            
            # Use registration number if available, otherwise use name
            key = reg_number if reg_number else name
            
            if key and key not in seen:
                seen.add(key)
                unique_orgs.append(org)
        
        return unique_orgs
    
    def _search_charity_commission_ew(self, keywords: List[str], limit: Optional[int]) -> List[Dict]:
        """Search England & Wales Charity Commission"""
        # Placeholder - implement actual API calls
        return []
    
    def _search_oscr(self, keywords: List[str], limit: Optional[int]) -> List[Dict]:
        """Search Scottish Charity Regulator (OSCR)"""
        # Placeholder - implement actual API calls
        return []
    
    def _search_charity_commission_ni(self, keywords: List[str], limit: Optional[int]) -> List[Dict]:
        """Search Northern Ireland Charity Commission"""
        # Placeholder - implement actual API calls
        return []

# Usage example
if __name__ == "__main__":
    # Discover housing associations
    housing_agent = UniversalDiscoveryAgent(IndustryType.HOUSING_ASSOCIATIONS)
    housing_orgs = housing_agent.discover_organizations(region="scotland", limit=10)
    
    # Discover charities
    charity_agent = UniversalDiscoveryAgent(IndustryType.CHARITIES)
    charities = charity_agent.discover_organizations(region="england", limit=10)
    
    print(f"Found {len(housing_orgs)} housing associations")
    print(f"Found {len(charities)} charities")