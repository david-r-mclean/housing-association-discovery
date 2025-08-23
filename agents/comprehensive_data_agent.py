import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import json
from urllib.parse import urljoin
from utils.data_storage import DataStorage

class ComprehensiveDataAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.storage = DataStorage()
        
        self.data_sources = {
            'companies_house_filings': 'https://find-and-update.company-information.service.gov.uk/company/{}/filing-history',
            'scottish_regulator': 'https://www.housingregulator.gov.scot',
            'english_regulator': 'https://www.gov.uk/government/organisations/regulator-of-social-housing',
            'charity_commission': 'https://register-of-charities.charitycommission.gov.uk/charity-search',
            'oscr_scotland': 'https://www.oscr.org.uk/about-charities/search-the-register'
        }
    
    def get_comprehensive_public_data(self, association: Dict) -> Dict:
        """Get all available public data for housing association"""
        company_name = association.get('company_name', association.get('name', ''))
        company_number = association.get('company_number', '')
        
        print(f"Getting comprehensive public data for: {company_name}")
        
        comprehensive_data = {
            'data_collection_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'company_name': company_name,
            'company_number': company_number
        }
        
        # 1. Enhanced Companies House data
        if company_number:
            ch_data = self._get_enhanced_companies_house_data(company_number)
            comprehensive_data.update(ch_data)
            
            # Save individual Companies House data
            self.storage.save_companies_house_data(company_number, ch_data)
        
        # 2. ARC Returns and regulatory data
        regulatory_data = self._get_regulatory_data(company_name, company_number)
        comprehensive_data.update(regulatory_data)
        
        if regulatory_data:
            self.storage.save_regulatory_data(company_number or company_name.replace(' ', '_'), 'housing_regulator', regulatory_data)
        
        # 3. Charity Commission data (many housing associations are charities)
        charity_data = self._get_charity_data(company_name)
        comprehensive_data.update(charity_data)
        
        # 4. Annual reports and financial documents
        financial_docs = self._get_financial_documents(company_name, association.get('official_website'))
        comprehensive_data.update(financial_docs)
        
        # 5. Performance and inspection reports
        performance_data = self._get_performance_reports(company_name)
        comprehensive_data.update(performance_data)
        
        time.sleep(2)  # Rate limiting
        return comprehensive_data
    
    def _get_enhanced_companies_house_data(self, company_number: str) -> Dict:
        """Get comprehensive Companies House data including all filings"""
        from utils.companies_house_api import CompaniesHouseAPI
        
        data = {}
        
        try:
            companies_house = CompaniesHouseAPI()
            
            # Get detailed filing history (more items)
            filings = companies_house.get_filing_history(company_number, items_per_page=100)
            
            if filings:
                # Categorize all filings
                filing_categories = {
                    'annual_accounts': [],
                    'confirmation_statements': [],
                    'director_appointments': [],
                    'director_resignations': [],
                    'registered_office_changes': [],
                    'mortgage_charges': [],
                    'other_filings': []
                }
                
                for filing in filings:
                    category = filing.get('category', '').lower()
                    description = filing.get('description', '').lower()
                    
                    if 'accounts' in description or category == 'accounts':
                        filing_categories['annual_accounts'].append(filing)
                    elif 'confirmation' in description:
                        filing_categories['confirmation_statements'].append(filing)
                    elif 'appointment' in description and 'director' in description:
                        filing_categories['director_appointments'].append(filing)
                    elif 'resignation' in description or 'termination' in description:
                        filing_categories['director_resignations'].append(filing)
                    elif 'registered office' in description:
                        filing_categories['registered_office_changes'].append(filing)
                    elif 'charge' in description or 'mortgage' in description:
                        filing_categories['mortgage_charges'].append(filing)
                    else:
                        filing_categories['other_filings'].append(filing)
                
                data['filing_categories'] = filing_categories
                data['total_filings'] = len(filings)
                
                # Extract key metrics
                data['latest_accounts_date'] = filing_categories['annual_accounts'][0].get('date') if filing_categories['annual_accounts'] else None
                data['accounts_filing_frequency'] = len(filing_categories['annual_accounts'])
                data['director_turnover'] = len(filing_categories['director_appointments']) + len(filing_categories['director_resignations'])
                data['office_stability'] = len(filing_categories['registered_office_changes'])
                data['has_charges'] = len(filing_categories['mortgage_charges']) > 0
            
            # Get current officers with more detail
            officers = companies_house.get_company_officers(company_number)
            if officers:
                data['current_officers'] = officers
                data['officer_analysis'] = self._analyze_officers(officers)
            
        except Exception as e:
            print(f"Error getting enhanced Companies House data: {e}")
        
        return data
    
    def _get_regulatory_data(self, company_name: str, company_number: str) -> Dict:
        """Get housing regulator data and ARC returns"""
        data = {}
        
        try:
            # Scottish Housing Regulator
            if 'scotland' in company_name.lower() or any(term in company_name.lower() for term in ['glasgow', 'edinburgh', 'dundee', 'aberdeen']):
                scottish_data = self._get_scottish_regulator_data(company_name)
                data.update(scottish_data)
            
            # English Regulator of Social Housing
            else:
                english_data = self._get_english_regulator_data(company_name)
                data.update(english_data)
            
            # Try to find ARC returns or equivalent
            arc_data = self._search_arc_returns(company_name, company_number)
            data.update(arc_data)
            
        except Exception as e:
            print(f"Error getting regulatory data: {e}")
        
        return data
    
    def _get_charity_data(self, company_name: str) -> Dict:
        """Check if housing association is registered charity"""
        data = {}
        
        try:
            # Search Charity Commission (England & Wales)
            charity_search_url = f"https://register-of-charities.charitycommission.gov.uk/charity-search?p_p_id=uk_gov_ccew_onereg_charitydetailsportlet_CharityDetailsPortlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&_uk_gov_ccew_onereg_charitydetailsportlet_CharityDetailsPortlet_javax.portlet.action=searchCharities&_uk_gov_ccew_onereg_charitydetailsportlet_CharityDetailsPortlet_keywords={company_name}"
            
            response = self.session.get(charity_search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for charity registration
                if 'charity' in soup.get_text().lower():
                    data['registered_charity'] = True
                    
                    # Try to extract charity number
                    charity_number_pattern = r'Charity number:\s*(\d+)'
                    match = re.search(charity_number_pattern, soup.get_text())
                    if match:
                        data['charity_number'] = match.group(1)
            
            # Search OSCR (Scotland)
            if not data.get('registered_charity'):
                oscr_data = self._search_oscr_scotland(company_name)
                data.update(oscr_data)
                
        except Exception as e:
            print(f"Error getting charity data: {e}")
        
        return data
    
    def _get_financial_documents(self, company_name: str, website_url: Optional[str]) -> Dict:
        """Find and download annual reports and financial documents"""
        data = {
            'annual_reports_found': [],
            'financial_statements_found': [],
            'impact_reports_found': []
        }
        
        try:
            if website_url:
                # Search website for financial documents
                doc_urls = self._find_financial_documents_on_website(website_url)
                
                for doc_url in doc_urls:
                    doc_type = self._classify_document_type(doc_url)
                    
                    if doc_type == 'annual_report':
                        data['annual_reports_found'].append(doc_url)
                    elif doc_type == 'financial_statement':
                        data['financial_statements_found'].append(doc_url)
                    elif doc_type == 'impact_report':
                        data['impact_reports_found'].append(doc_url)
                    
                    # Try to download and save key documents
                    if doc_type in ['annual_report', 'financial_statement']:
                        self._download_and_save_document(doc_url, company_name, doc_type)
            
        except Exception as e:
            print(f"Error getting financial documents: {e}")
        
        return data
    
    def _find_financial_documents_on_website(self, website_url: str) -> List[str]:
        """Find financial documents on housing association website"""
        doc_urls = []
        
        try:
            # Common pages that might have financial documents
            pages_to_check = [
                website_url,
                urljoin(website_url, '/about'),
                urljoin(website_url, '/reports'),
                urljoin(website_url, '/annual-report'),
                urljoin(website_url, '/financial-information'),
                urljoin(website_url, '/governance'),
                urljoin(website_url, '/corporate-information')
            ]
            
            for page_url in pages_to_check:
                try:
                    response = self.session.get(page_url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for PDF links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        text = link.get_text().lower()
                        
                        if '.pdf' in href and any(keyword in text for keyword in ['annual', 'report', 'financial', 'accounts', 'impact']):
                            full_url = urljoin(page_url, href)
                            doc_urls.append(full_url)
                            
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error finding financial documents: {e}")
        
        return doc_urls
    
    def _download_and_save_document(self, doc_url: str, company_name: str, doc_type: str):
        """Download and save financial document"""
        try:
            response = self.session.get(doc_url, timeout=30)
            if response.status_code == 200:
                company_safe_name = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
                filename = f"{company_safe_name}_{doc_type}.pdf"
                
                if doc_type == 'annual_report':
                    filepath = os.path.join(self.storage.base_path, 'annual_reports', filename)
                else:
                    filepath = os.path.join(self.storage.base_path, 'regulatory_data', filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Downloaded: {filename}")
                
        except Exception as e:
            print(f"Error downloading document: {e}")
    
    def _analyze_officers(self, officers: List[Dict]) -> Dict:
        """Analyze company officers for insights"""
        analysis = {
            'total_officers': len(officers),
            'active_officers': 0,
            'director_types': {},
            'appointment_dates': []
        }
        
        for officer in officers:
            if officer.get('resigned_on') is None:
                analysis['active_officers'] += 1
            
            officer_role = officer.get('officer_role', 'Unknown')
            analysis['director_types'][officer_role] = analysis['director_types'].get(officer_role, 0) + 1
            
            if officer.get('appointed_on'):
                analysis['appointment_dates'].append(officer['appointed_on'])
        
        return analysis
    
    # Additional helper methods would go here...
    def _classify_document_type(self, url: str) -> str:
        """Classify document type from URL"""
        url_lower = url.lower()
        if 'annual' in url_lower and 'report' in url_lower:
            return 'annual_report'
        elif 'financial' in url_lower or 'accounts' in url_lower:
            return 'financial_statement'
        elif 'impact' in url_lower:
            return 'impact_report'
        else:
            return 'other'