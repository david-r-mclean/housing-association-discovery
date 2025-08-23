import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import os
from dotenv import load_dotenv

load_dotenv('config/api_keys.env')

class WebsiteEnrichmentAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    def enrich_association(self, association: Dict) -> Dict:
        """Enrich a single housing association with web data"""
        enriched = association.copy()
        company_name = association.get('company_name', '')
        
        print(f"Enriching: {company_name}")
        
        # 1. Find official website
        website = self.find_official_website(company_name)
        enriched['official_website'] = website
        
        if website:
            # 2. Extract contact information
            contact_info = self.extract_contact_info(website)
            enriched.update(contact_info)
            
            # 3. Find social media accounts
            social_media = self.find_social_media_accounts(website, company_name)
            enriched['social_media'] = social_media
            
            # 4. Extract key metrics from website
            website_metrics = self.extract_website_metrics(website)
            enriched.update(website_metrics)
        
        time.sleep(1)  # Rate limiting
        return enriched
    
    def find_official_website(self, company_name: str) -> Optional[str]:
        """Find the official website using Google Search API or web scraping"""
        if self.google_api_key:
            return self._google_search_website(company_name)
        else:
            return self._scrape_search_website(company_name)
    
    def _google_search_website(self, company_name: str) -> Optional[str]:
        """Use Google Custom Search API to find website"""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_search_engine_id,
            'q': f'"{company_name}" housing association official website',
            'num': 5
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                url = item['link']
                if self._is_likely_official_website(url, company_name):
                    return url
                    
        except Exception as e:
            print(f"Google search error for {company_name}: {e}")
        
        return None
    
    def _scrape_search_website(self, company_name: str) -> Optional[str]:
        """Fallback: scrape DuckDuckGo search results"""
        search_url = f"https://duckduckgo.com/html/?q={company_name} housing association official website"
        
        try:
            response = self.session.get(search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search result links
            for link in soup.find_all('a', class_='result__a'):
                url = link.get('href')
                if url and self._is_likely_official_website(url, company_name):
                    return url
                    
        except Exception as e:
            print(f"Search scraping error for {company_name}: {e}")
        
        return None
    
    def _is_likely_official_website(self, url: str, company_name: str) -> bool:
        """Check if URL is likely the official website"""
        domain = urlparse(url).netloc.lower()
        name_parts = company_name.lower().split()
        
        # Check if domain contains company name parts
        name_in_domain = any(part in domain for part in name_parts if len(part) > 3)
        
        # Exclude obvious non-official sites
        excluded_domains = ['wikipedia', 'companies-house', 'gov.uk', 'facebook', 'twitter', 'linkedin']
        is_excluded = any(excluded in domain for excluded in excluded_domains)
        
        return name_in_domain and not is_excluded
    
    def extract_contact_info(self, website_url: str) -> Dict:
        """Extract contact information from website"""
        contact_info = {
            'phone_numbers': [],
            'email_addresses': [],
            'ceo_name': None,
            'head_office_address': None
        }
        
        try:
            # Try common contact page URLs
            contact_urls = [
                website_url,
                urljoin(website_url, '/contact'),
                urljoin(website_url, '/contact-us'),
                urljoin(website_url, '/about'),
                urljoin(website_url, '/about-us')
            ]
            
            for url in contact_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text = soup.get_text()
                    
                    # Extract phone numbers
                    phone_pattern = r'(?:\+44|0)[\d\s\-\(\)]{10,}'
                    phones = re.findall(phone_pattern, text)
                    contact_info['phone_numbers'].extend(phones[:3])  # Max 3
                    
                    # Extract email addresses
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, text)
                    contact_info['email_addresses'].extend(emails[:3])  # Max 3
                    
                    # Look for CEO/Chief Executive
                    ceo_pattern = r'(?:CEO|Chief Executive|Managing Director)[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)'
                    ceo_match = re.search(ceo_pattern, text, re.IGNORECASE)
                    if ceo_match and not contact_info['ceo_name']:
                        contact_info['ceo_name'] = ceo_match.group(1)
                    
                    if contact_info['phone_numbers'] or contact_info['email_addresses']:
                        break  # Found contact info, no need to check more pages
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error extracting contact info from {website_url}: {e}")
        
        # Remove duplicates
        contact_info['phone_numbers'] = list(set(contact_info['phone_numbers']))
        contact_info['email_addresses'] = list(set(contact_info['email_addresses']))
        
        return contact_info
    
    def find_social_media_accounts(self, website_url: str, company_name: str) -> Dict:
        """Find social media accounts from website and search"""
        social_media = {
            'twitter': None,
            'facebook': None,
            'linkedin': None,
            'instagram': None,
            'youtube': None
        }
        
        try:
            # 1. Check website for social media links
            response = self.session.get(website_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find social media links
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                
                if 'twitter.com' in href or 'x.com' in href:
                    social_media['twitter'] = link['href']
                elif 'facebook.com' in href:
                    social_media['facebook'] = link['href']
                elif 'linkedin.com' in href:
                    social_media['linkedin'] = link['href']
                elif 'instagram.com' in href:
                    social_media['instagram'] = link['href']
                elif 'youtube.com' in href:
                    social_media['youtube'] = link['href']
            
            # 2. Search for social media accounts if not found on website
            for platform in social_media:
                if not social_media[platform]:
                    account = self._search_social_media_account(company_name, platform)
                    social_media[platform] = account
                    
        except Exception as e:
            print(f"Error finding social media for {company_name}: {e}")
        
        return social_media
    
    def _search_social_media_account(self, company_name: str, platform: str) -> Optional[str]:
        """Search for social media account on specific platform"""
        platform_domains = {
            'twitter': 'twitter.com',
            'facebook': 'facebook.com',
            'linkedin': 'linkedin.com',
            'instagram': 'instagram.com',
            'youtube': 'youtube.com'
        }
        
        domain = platform_domains.get(platform)
        if not domain:
            return None
        
        search_query = f'site:{domain} "{company_name}" housing association'
        
        try:
            if self.google_api_key:
                # Use Google Custom Search
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_search_engine_id,
                    'q': search_query,
                    'num': 3
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                for item in data.get('items', []):
                    if domain in item['link']:
                        return item['link']
            
        except Exception as e:
            print(f"Error searching {platform} for {company_name}: {e}")
        
        return None
    
    def extract_website_metrics(self, website_url: str) -> Dict:
        """Extract basic metrics from website"""
        metrics = {
            'website_has_search': False,
            'website_has_tenant_portal': False,
            'website_has_online_services': False,
            'website_responsive': False,
            'last_updated': None
        }
        
        try:
            response = self.session.get(website_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text().lower()
            
            # Check for search functionality
            search_indicators = ['search', 'find', 'lookup']
            metrics['website_has_search'] = any(
                soup.find('input', {'type': 'search'}) or 
                soup.find('input', {'name': name}) for name in search_indicators
            )
            
            # Check for tenant portal
            portal_keywords = ['tenant portal', 'resident portal', 'my account', 'login', 'sign in']
            metrics['website_has_tenant_portal'] = any(keyword in text for keyword in portal_keywords)
            
            # Check for online services
            service_keywords = ['online services', 'report repair', 'pay rent', 'book appointment']
            metrics['website_has_online_services'] = any(keyword in text for keyword in service_keywords)
            
            # Check if responsive (basic check)
            viewport_meta = soup.find('meta', {'name': 'viewport'})
            metrics['website_responsive'] = viewport_meta is not None
            
        except Exception as e:
            print(f"Error extracting website metrics from {website_url}: {e}")
        
        return metrics