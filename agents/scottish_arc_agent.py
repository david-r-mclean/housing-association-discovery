"""
Scottish Housing Regulator ARC Returns Agent
Extracts Annual Return to Communities data from Scottish Housing Regulator
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ScottishARCAgent:
    """Agent to extract ARC returns data from Scottish Housing Regulator"""
    
    def __init__(self):
        self.base_url = "https://www.housingregulator.gov.scot"
        self.statistical_url = "https://www.housingregulator.gov.scot/landlord-performance/statistical-information"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def discover_arc_data_sources(self) -> List[Dict]:
        """Discover available ARC data sources from the statistical information page"""
        try:
            logger.info(f"Discovering ARC data sources from {self.statistical_url}")
            
            response = self.session.get(self.statistical_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data_sources = []
            
            # Look for downloadable files (Excel, CSV, PDF)
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                # Check for ARC-related files
                if any(keyword in text.lower() for keyword in ['arc', 'annual return', 'statistical', 'performance', 'landlord']):
                    if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.csv', '.pdf']):
                        full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                        
                        data_sources.append({
                            'title': text,
                            'url': full_url,
                            'type': self._get_file_type(href),
                            'year': self._extract_year(text),
                            'description': self._get_link_context(link)
                        })
            
            # Look for embedded data tables
            tables = soup.find_all('table')
            for i, table in enumerate(tables):
                if self._is_arc_table(table):
                    data_sources.append({
                        'title': f'ARC Data Table {i+1}',
                        'url': self.statistical_url,
                        'type': 'table',
                        'year': datetime.now().year,
                        'description': 'Embedded data table',
                        'table_index': i
                    })
            
            logger.info(f"Found {len(data_sources)} ARC data sources")
            return data_sources
            
        except Exception as e:
            logger.error(f"Error discovering ARC data sources: {e}")
            return []
    
    def extract_arc_returns_data(self) -> Dict:
        """Extract comprehensive ARC returns data"""
        try:
            logger.info("Extracting ARC returns data from Scottish Housing Regulator")
            
            # Discover available data sources
            data_sources = self.discover_arc_data_sources()
            
            arc_data = {
                'extraction_date': datetime.now().isoformat(),
                'source': 'Scottish Housing Regulator',
                'data_sources': data_sources,
                'associations': [],
                'summary_statistics': {},
                'performance_indicators': {}
            }
            
            # Extract data from each source
            for source in data_sources:
                try:
                    if source['type'] in ['xlsx', 'xls', 'csv']:
                        associations_data = self._extract_from_file(source)
                        if associations_data:
                            arc_data['associations'].extend(associations_data)
                    
                    elif source['type'] == 'table':
                        table_data = self._extract_from_table(source)
                        if table_data:
                            arc_data['associations'].extend(table_data)
                
                except Exception as e:
                    logger.warning(f"Failed to extract from {source['title']}: {e}")
                    continue
            
            # Generate summary statistics
            arc_data['summary_statistics'] = self._generate_summary_stats(arc_data['associations'])
            
            # Extract performance indicators
            arc_data['performance_indicators'] = self._extract_performance_indicators()
            
            logger.info(f"Extracted ARC data for {len(arc_data['associations'])} associations")
            return arc_data
            
        except Exception as e:
            logger.error(f"Error extracting ARC returns data: {e}")
            return {'error': str(e)}
    
    def _extract_from_file(self, source: Dict) -> List[Dict]:
        """Extract data from downloadable files"""
        try:
            logger.info(f"Extracting data from file: {source['title']}")
            
            response = self.session.get(source['url'], timeout=60)
            response.raise_for_status()
            
            if source['type'] == 'csv':
                # Handle CSV files
                df = pd.read_csv(io.StringIO(response.text))
                return self._process_dataframe(df, source)
            
            elif source['type'] in ['xlsx', 'xls']:
                # Handle Excel files
                df = pd.read_excel(io.BytesIO(response.content))
                return self._process_dataframe(df, source)
            
        except Exception as e:
            logger.error(f"Error extracting from file {source['url']}: {e}")
            return []
    
    def _extract_from_table(self, source: Dict) -> List[Dict]:
        """Extract data from HTML tables"""
        try:
            response = self.session.get(source['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')
            
            if source.get('table_index', 0) < len(tables):
                table = tables[source['table_index']]
                return self._process_html_table(table, source)
            
        except Exception as e:
            logger.error(f"Error extracting from table: {e}")
            return []
    
    def _process_dataframe(self, df: pd.DataFrame, source: Dict) -> List[Dict]:
        """Process pandas DataFrame into association records"""
        associations = []
        
        # Common column mappings
        column_mappings = {
            'name': ['name', 'association', 'landlord', 'organisation', 'rsl'],
            'registration_number': ['reg_no', 'registration', 'number', 'rsl_no'],
            'stock_units': ['units', 'stock', 'homes', 'properties'],
            'rent_collected': ['rent', 'income', 'rental_income'],
            'satisfaction_score': ['satisfaction', 'tenant_satisfaction', 'customer_satisfaction'],
            'complaints': ['complaints', 'complaint_numbers'],
            'repairs_completed': ['repairs', 'maintenance', 'responsive_repairs']
        }
        
        # Normalize column names
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        for _, row in df.iterrows():
            association = {
                'data_source': source['title'],
                'year': source.get('year', datetime.now().year)
            }
            
            # Map columns to standard fields
            for field, possible_cols in column_mappings.items():
                for col in possible_cols:
                    if col in df.columns:
                        association[field] = row[col]
                        break
            
            # Add all other columns as additional data
            for col in df.columns:
                if col not in [mapped_col for cols in column_mappings.values() for mapped_col in cols]:
                    association[f'additional_{col}'] = row[col]
            
            if association.get('name'):  # Only add if we have a name
                associations.append(association)
        
        return associations
    
    def _process_html_table(self, table, source: Dict) -> List[Dict]:
        """Process HTML table into association records"""
        associations = []
        
        try:
            # Extract headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True).lower().replace(' ', '_'))
            
            # Extract data rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= len(headers):
                    association = {
                        'data_source': source['title'],
                        'year': source.get('year', datetime.now().year)
                    }
                    
                    for i, cell in enumerate(cells[:len(headers)]):
                        if i < len(headers):
                            association[headers[i]] = cell.get_text(strip=True)
                    
                    if association.get('name') or association.get('association'):
                        associations.append(association)
            
        except Exception as e:
            logger.error(f"Error processing HTML table: {e}")
        
        return associations
    
    def _extract_performance_indicators(self) -> Dict:
        """Extract sector-wide performance indicators"""
        try:
            response = self.session.get(self.statistical_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            indicators = {}
            
            # Look for key statistics in the page
            for element in soup.find_all(['p', 'div', 'span']):
                text = element.get_text(strip=True)
                
                # Extract numerical indicators
                if any(keyword in text.lower() for keyword in ['satisfaction', 'complaints', 'repairs', 'rent']):
                    numbers = re.findall(r'(\d+(?:\.\d+)?%?)', text)
                    if numbers:
                        indicators[text[:50]] = numbers[0]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error extracting performance indicators: {e}")
            return {}
    
    def _generate_summary_stats(self, associations: List[Dict]) -> Dict:
        """Generate summary statistics from associations data"""
        if not associations:
            return {}
        
        stats = {
            'total_associations': len(associations),
            'data_years': list(set(a.get('year') for a in associations if a.get('year'))),
            'associations_with_stock_data': sum(1 for a in associations if a.get('stock_units')),
            'associations_with_satisfaction_data': sum(1 for a in associations if a.get('satisfaction_score')),
            'total_stock_units': sum(int(str(a.get('stock_units', 0)).replace(',', '')) for a in associations if a.get('stock_units') and str(a.get('stock_units')).replace(',', '').isdigit())
        }
        
        return stats
    
    def _get_file_type(self, url: str) -> str:
        """Get file type from URL"""
        if '.xlsx' in url.lower():
            return 'xlsx'
        elif '.xls' in url.lower():
            return 'xls'
        elif '.csv' in url.lower():
            return 'csv'
        elif '.pdf' in url.lower():
            return 'pdf'
        else:
            return 'unknown'
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        years = re.findall(r'20\d{2}', text)
        return int(years[-1]) if years else None
    
    def _get_link_context(self, link) -> str:
        """Get context around a link for better description"""
        parent = link.parent
        if parent:
            return parent.get_text(strip=True)[:100]
        return ""
    
    def _is_arc_table(self, table) -> bool:
        """Check if a table contains ARC-related data"""
        table_text = table.get_text().lower()
        return any(keyword in table_text for keyword in ['association', 'landlord', 'performance', 'satisfaction', 'complaints'])

# Usage example
if __name__ == "__main__":
    import io
    
    agent = ScottishARCAgent()
    arc_data = agent.extract_arc_returns_data()
    
    print(f"Extracted ARC data: {json.dumps(arc_data, indent=2, default=str)}")