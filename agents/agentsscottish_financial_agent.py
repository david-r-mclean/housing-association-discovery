import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import json
from urllib.parse import urljoin

class ScottishFinancialAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.scottish_regulator_urls = {
            'main': 'https://www.housingregulator.gov.scot',
            'landlord_list': 'https://www.housingregulator.gov.scot/for-tenants/landlord-performance',
            'annual_statements': 'https://www.housingregulator.gov.scot/for-landlords/statutory-guidance/annual-assurance-statements'
        }
        
        self.companies_house_filing_types = [
            'AA',    # Annual accounts
            'AR01',  # Annual return
            'CS01',  # Confirmation statement
            'PSC01', # People with significant control
            'CH01',  # Change of registered office
            'TM01',  # Termination of appointment
            'AP01'   # Appointment of director/secretary
        ]
    
    def get_comprehensive_financial_data(self, association: Dict) -> Dict:
        """Get comprehensive financial and regulatory data"""
        company_name = association.get('company_name', '')
        company_number = association.get('company_number', '')
        
        print(f"Getting comprehensive data for: {company_name}")
        
        financial_data = {
            # Scottish regulator data
            'scottish_regulator_listed': False,
            'regulator_performance_rating': None,
            'annual_assurance_statement': None,
            'regulatory_notices': [],
            
            # Companies House detailed filings
            'annual_accounts_filed': False,
            'latest_accounts_date': None,
            'accounts_overdue': False,
            'confirmation_statements_filed': False,
            'latest_confirmation_date': None,
            'director_changes_last_year': 0,
            'registered_office_changes': 0,
            'filing_compliance_score': 0,
            
            # Financial metrics (from accounts if available)
            'turnover': None,
            'total_assets': None,
            'net_assets': None,
            'creditors': None,
            'housing_stock_units': None,
            'rental_income': None
        }
        
        # Get Scottish regulator data
        regulator_data = self._get_scottish_regulator_data(company_name)
        financial_data.update(regulator_data)
        
        # Get detailed Companies House filings
        filing_data = self._get_detailed_filings(company_number)
        financial_data.update(filing_data)
        
        # Try to get financial metrics from latest accounts
        accounts_data = self._extract_financial_metrics(company_number)
        financial_data.update(accounts_data)
        
        time.sleep(2)  # Rate limiting
        return financial_data
    
    def _get_scottish_regulator_data(self, company_name: str) -> Dict:
        """Get data from Scottish Housing Regulator"""
        data = {
            'scottish_regulator_listed': False,
            'regulator_performance_rating': None,
            'annual_assurance_statement': None,
            'regulatory_notices': []
        }
        
        try:
            # Search Scottish Housing Regulator website
            search_terms = [
                company_name,
                company_name.replace('LIMITED', '').replace('LTD', '').strip(),
                company_name.split()[0] + ' housing'  # First word + housing
            ]
            
            for term in search_terms:
                regulator_results = self._search_scottish_regulator(term)
                if regulator_results:
                    data.update(regulator_results)
                    break
                    
        except Exception as e:
            print(f"Error getting Scottish regulator data: {e}")
        
        return data
    
    def _search_scottish_regulator(self, search_term: str) -> Dict:
        """Search Scottish Housing Regulator website"""
        data = {}
        
        try:
            # Try landlord performance page
            performance_url = f"{self.scottish_regulator_urls['main']}/search?q={search_term}"
            response = self.session.get(performance_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for landlord listings
                for link in soup.find_all('a', href=True):
                    link_text = link.get_text().lower()
                    if search_term.lower() in link_text and 'housing' in link_text:
                        data['scottish_regulator_listed'] = True
                        
                        # Try to extract performance info
                        performance_info = self._extract_performance_data(link['href'])
                        data.update(performance_info)
                        break
                        
        except Exception as e:
            print(f"Error searching Scottish regulator: {e}")
        
        return data
    
    def _extract_performance_data(self, performance_url: str) -> Dict:
        """Extract performance data from regulator page"""
        data = {}
        
        try:
            if not performance_url.startswith('http'):
                performance_url = urljoin(self.scottish_regulator_urls['main'], performance_url)
            
            response = self.session.get(performance_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for performance ratings
            rating_patterns = [
                r'Performance:\s*([A-Z]+)',
                r'Rating:\s*([A-Z]+)',
                r'Grade:\s*([A-Z]+)'
            ]
            
            for pattern in rating_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data['regulator_performance_rating'] = match.group(1)
                    break
            
            # Look for regulatory notices
            if 'regulatory notice' in text.lower() or 'enforcement' in text.lower():
                data['regulatory_notices'].append('Regulatory notice found')
                
        except Exception as e:
            print(f"Error extracting performance data: {e}")
        
        return data
    
    def _get_detailed_filings(self, company_number: str) -> Dict:
        """Get detailed filing information from Companies House"""
        from utils.companies_house_api import CompaniesHouseAPI
        
        data = {
            'annual_accounts_filed': False,
            'latest_accounts_date': None,
            'accounts_overdue': False,
            'confirmation_statements_filed': False,
            'latest_confirmation_date': None,
            'director_changes_last_year': 0,
            'registered_office_changes': 0,
            'filing_compliance_score': 0
        }
        
        try:
            companies_house = CompaniesHouseAPI()
            
            # Get more detailed filing history
            filings = companies_house.get_filing_history(company_number, items_per_page=50)
            
            if not filings:
                return data
            
            # Analyze filings
            accounts_filings = []
            confirmation_filings = []
            director_changes = []
            office_changes = []
            
            for filing in filings:
                filing_type = filing.get('category', '')
                filing_date = filing.get('date', '')
                description = filing.get('description', '').lower()
                
                # Categorize filings
                if 'accounts' in description or filing_type == 'accounts':
                    accounts_filings.append(filing)
                elif 'confirmation' in description or filing_type == 'confirmation-statement':
                    confirmation_filings.append(filing)
                elif 'director' in description or 'appointment' in description or 'resignation' in description:
                    director_changes.append(filing)
                elif 'registered office' in description or 'change of address' in description:
                    office_changes.append(filing)
            
            # Process accounts
            if accounts_filings:
                data['annual_accounts_filed'] = True
                data['latest_accounts_date'] = accounts_filings[0].get('date')
                
                # Check if accounts are overdue (basic check)
                from datetime import datetime, timedelta
                try:
                    latest_date = datetime.strptime(accounts_filings[0].get('date'), '%Y-%m-%d')
                    if datetime.now() - latest_date > timedelta(days=400):  # Rough overdue check
                        data['accounts_overdue'] = True
                except:
                    pass
            
            # Process confirmation statements
            if confirmation_filings:
                data['confirmation_statements_filed'] = True
                data['latest_confirmation_date'] = confirmation_filings[0].get('date')
            
            # Count recent changes
            data['director_changes_last_year'] = len([f for f in director_changes if self._is_recent_filing(f.get('date'))])
            data['registered_office_changes'] = len(office_changes)
            
            # Calculate compliance score
            data['filing_compliance_score'] = self._calculate_compliance_score(data, len(filings))
            
        except Exception as e:
            print(f"Error getting detailed filings for {company_number}: {e}")
        
        return data
    
    def _extract_financial_metrics(self, company_number: str) -> Dict:
        """Try to extract financial metrics from latest accounts"""
        data = {
            'turnover': None,
            'total_assets': None,
            'net_assets': None,
            'creditors': None,
            'housing_stock_units': None,
            'rental_income': None
        }
        
        try:
            from utils.companies_house_api import CompaniesHouseAPI
            companies_house = CompaniesHouseAPI()
            
            # Get filing history to find latest accounts
            filings = companies_house.get_filing_history(company_number, items_per_page=20)
            
            for filing in filings:
                if 'accounts' in filing.get('description', '').lower():
                    # Try to get document details (this would require document API access)
                    # For now, we'll mark that accounts are available
                    data['accounts_available'] = True
                    break
                    
        except Exception as e:
            print(f"Error extracting financial metrics: {e}")
        
        return data
    
    def _is_recent_filing(self, filing_date: str) -> bool:
        """Check if filing is within last year"""
        try:
            from datetime import datetime, timedelta
            filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
            return datetime.now() - filing_dt <= timedelta(days=365)
        except:
            return False
    
    def _calculate_compliance_score(self, filing_data: Dict, total_filings: int) -> int:
        """Calculate filing compliance score (0-100)"""
        score = 0
        
        # Points for having accounts
        if filing_data.get('annual_accounts_filed'):
            score += 30
            if not filing_data.get('accounts_overdue'):
                score += 20
        
        # Points for confirmation statements
        if filing_data.get('confirmation_statements_filed'):
            score += 20
        
        # Points for regular filing activity
        if total_filings > 10:
            score += 15
        elif total_filings > 5:
            score += 10
        
        # Deduct points for too many director changes (instability)
        director_changes = filing_data.get('director_changes_last_year', 0)
        if director_changes > 3:
            score -= 10
        
        # Deduct points for multiple office changes (instability)
        office_changes = filing_data.get('registered_office_changes', 0)
        if office_changes > 2:
            score -= 5
        
        return max(0, min(100, score))  # Keep between 0-100