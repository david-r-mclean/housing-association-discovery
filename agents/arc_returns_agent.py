import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import json

class ARCReturnsAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.regulator_urls = {
            'rsh': 'https://www.gov.uk/government/organisations/regulator-of-social-housing',
            'statistical_data': 'https://www.gov.uk/government/statistical-data-sets/live-tables-on-social-housing-sales'
        }
    
    def get_arc_data(self, association: Dict) -> Dict:
        """Get ARC returns data for housing association"""
        company_name = association.get('company_name', '')
        company_number = association.get('company_number', '')
        
        print(f"Fetching ARC data for: {company_name}")
        
        arc_data = {
            'arc_returns_found': False,
            'latest_return_year': None,
            'total_units': None,
            'rental_income': None,
            'operating_margin': None,
            'development_completions': None,
            'regulatory_rating': None,
            'governance_rating': None,
            'viability_rating': None
        }
        
        # Try multiple sources for ARC data
        arc_data.update(self._search_rsh_data(company_name))
        arc_data.update(self._search_statistical_releases(company_name))
        arc_data.update(self._search_annual_reports(company_name, association.get('official_website')))
        
        time.sleep(1)  # Rate limiting
        return arc_data
    
    def _search_rsh_data(self, company_name: str) -> Dict:
        """Search Regulator of Social Housing data"""
        data = {}
        
        try:
            # Search for regulatory judgments
            search_url = f"https://www.gov.uk/search/all?keywords={company_name} housing association regulatory"
            response = self.session.get(search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for regulatory judgment links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text().lower()
                
                if 'regulatory' in text and 'judgment' in text:
                    judgment_data = self._extract_regulatory_judgment(href)
                    data.update(judgment_data)
                    break
                    
        except Exception as e:
            print(f"Error searching RSH data for {company_name}: {e}")
        
        return data
    
    def _extract_regulatory_judgment(self, judgment_url: str) -> Dict:
        """Extract data from regulatory judgment page"""
        data = {}
        
        try:
            if not judgment_url.startswith('http'):
                judgment_url = 'https://www.gov.uk' + judgment_url
                
            response = self.session.get(judgment_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for governance and viability ratings
            governance_pattern = r'Governance:\s*([A-Z]\d?)'
            viability_pattern = r'Viability:\s*([A-Z]\d?)'
            
            governance_match = re.search(governance_pattern, text)
            if governance_match:
                data['governance_rating'] = governance_match.group(1)
            
            viability_match = re.search(viability_pattern, text)
            if viability_match:
                data['viability_rating'] = viability_match.group(1)
                
            if governance_match or viability_match:
                data['arc_returns_found'] = True
                
        except Exception as e:
            print(f"Error extracting regulatory judgment: {e}")
        
        return data
    
    def _search_statistical_releases(self, company_name: str) -> Dict:
        """Search statistical data releases"""
        data = {}
        
        try:
            # Search for statistical releases mentioning the association
            search_terms = [
                f"{company_name} statistical data release",
                f"{company_name} social housing statistics"
            ]
            
            for term in search_terms:
                search_url = f"https://www.gov.uk/search/all?keywords={term}"
                response = self.session.get(search_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for statistical data links
                for link in soup.find_all('a', href=True):
                    text = link.get_text().lower()
                    if 'statistical' in text and ('housing' in text or 'data' in text):
                        stats_data = self._extract_statistical_data(link['href'])
                        if stats_data:
                            data.update(stats_data)
                            break
                
                if data:
                    break
                    
        except Exception as e:
            print(f"Error searching statistical releases for {company_name}: {e}")
        
        return data
    
    def _extract_statistical_data(self, stats_url: str) -> Dict:
        """Extract statistical data from government releases"""
        data = {}
        
        try:
            if not stats_url.startswith('http'):
                stats_url = 'https://www.gov.uk' + stats_url
                
            response = self.session.get(stats_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for downloadable data files (CSV, Excel)
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls']):
                    # Found data file - could contain housing association data
                    data['statistical_data_available'] = True
                    break
                    
        except Exception as e:
            print(f"Error extracting statistical data: {e}")
        
        return data
    
    def _search_annual_reports(self, company_name: str, website_url: Optional[str]) -> Dict:
        """Search for annual reports and financial data"""
        data = {}
        
        if not website_url:
            return data
        
        try:
            # Common annual report page URLs
            report_urls = [
                f"{website_url}/annual-report",
                f"{website_url}/reports",
                f"{website_url}/financial-information",
                f"{website_url}/about/reports",
                f"{website_url}/corporate/annual-report"
            ]
            
            for url in report_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for PDF links to annual reports
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            text = link.get_text().lower()
                            
                            if '.pdf' in href and any(keyword in text for keyword in ['annual', 'report', 'financial']):
                                # Found annual report
                                report_data = self._extract_annual_report_data(href, website_url)
                                data.update(report_data)
                                break
                        
                        if data:
                            break
                            
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error searching annual reports for {company_name}: {e}")
        
        return data
    
    def _extract_annual_report_data(self, report_url: str, base_url: str) -> Dict:
        """Extract key metrics from annual report (basic text extraction)"""
        data = {}
        
        try:
            if not report_url.startswith('http'):
                from urllib.parse import urljoin
                report_url = urljoin(base_url, report_url)
            
            # For now, just mark that we found a report
            # Full PDF text extraction would require additional libraries
            data['annual_report_available'] = True
            data['annual_report_url'] = report_url
            
            # Could add PDF text extraction here with PyPDF2 or similar
            # to extract financial metrics like:
            # - Total rental income
            # - Operating margin
            # - Number of units
            # - Development completions
            
        except Exception as e:
            print(f"Error extracting annual report data: {e}")
        
        return data

class SocialMediaMetricsAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_social_media_metrics(self, association: Dict) -> Dict:
        """Get basic social media metrics (public data only)"""
        social_media = association.get('social_media', {})
        company_name = association.get('company_name', '')
        
        metrics = {
            'twitter_followers': None,
            'twitter_following': None,
            'twitter_posts_count': None,
            'facebook_likes': None,
            'linkedin_followers': None,
            'social_media_activity_score': 0
        }
        
        print(f"Getting social media metrics for: {company_name}")
        
        # Get Twitter metrics (if available)
        if social_media.get('twitter'):
            twitter_metrics = self._get_twitter_metrics(social_media['twitter'])
            metrics.update(twitter_metrics)
        
        # Get Facebook metrics (if available)
        if social_media.get('facebook'):
            facebook_metrics = self._get_facebook_metrics(social_media['facebook'])
            metrics.update(facebook_metrics)
        
        # Get LinkedIn metrics (if available)
        if social_media.get('linkedin'):
            linkedin_metrics = self._get_linkedin_metrics(social_media['linkedin'])
            metrics.update(linkedin_metrics)
        
        # Calculate activity score
        metrics['social_media_activity_score'] = self._calculate_activity_score(metrics, social_media)
        
        time.sleep(1)  # Rate limiting
        return metrics
    
    def _get_twitter_metrics(self, twitter_url: str) -> Dict:
        """Get basic Twitter metrics from public profile"""
        metrics = {}
        
        try:
            response = self.session.get(twitter_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for follower counts (this is basic scraping - Twitter's structure changes frequently)
            follower_patterns = [
                r'(\d+(?:,\d+)*)\s*Followers',
                r'(\d+(?:\.\d+)?[KM]?)\s*Followers'
            ]
            
            for pattern in follower_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    followers_text = match.group(1)
                    metrics['twitter_followers'] = self._parse_social_count(followers_text)
                    break
            
        except Exception as e:
            print(f"Error getting Twitter metrics: {e}")
        
        return metrics
    
    def _get_facebook_metrics(self, facebook_url: str) -> Dict:
        """Get basic Facebook metrics from public page"""
        metrics = {}
        
        try:
            response = self.session.get(facebook_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for like counts
            like_patterns = [
                r'(\d+(?:,\d+)*)\s*likes',
                r'(\d+(?:\.\d+)?[KM]?)\s*likes'
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    likes_text = match.group(1)
                    metrics['facebook_likes'] = self._parse_social_count(likes_text)
                    break
            
        except Exception as e:
            print(f"Error getting Facebook metrics: {e}")
        
        return metrics
    
    def _get_linkedin_metrics(self, linkedin_url: str) -> Dict:
        """Get basic LinkedIn metrics from public page"""
        metrics = {}
        
        try:
            response = self.session.get(linkedin_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for follower counts
            follower_patterns = [
                r'(\d+(?:,\d+)*)\s*followers',
                r'(\d+(?:\.\d+)?[KM]?)\s*followers'
            ]
            
            for pattern in follower_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    followers_text = match.group(1)
                    metrics['linkedin_followers'] = self._parse_social_count(followers_text)
                    break
            
        except Exception as e:
            print(f"Error getting LinkedIn metrics: {e}")
        
        return metrics
    
    def _parse_social_count(self, count_text: str) -> Optional[int]:
        """Parse social media count text (e.g., '1.2K', '15,000') to integer"""
        try:
            count_text = count_text.replace(',', '')
            
            if 'K' in count_text.upper():
                return int(float(count_text.upper().replace('K', '')) * 1000)
            elif 'M' in count_text.upper():
                return int(float(count_text.upper().replace('M', '')) * 1000000)
            else:
                return int(count_text)
                
        except Exception:
            return None
    
    def _calculate_activity_score(self, metrics: Dict, social_media: Dict) -> int:
        """Calculate a simple social media activity score (0-100)"""
        score = 0
        
        # Points for having accounts
        for platform in ['twitter', 'facebook', 'linkedin', 'instagram', 'youtube']:
            if social_media.get(platform):
                score += 10
        
        # Points for follower counts
        if metrics.get('twitter_followers'):
            if metrics['twitter_followers'] > 1000:
                score += 15
            elif metrics['twitter_followers'] > 100:
                score += 10
            else:
                score += 5
        
        if metrics.get('facebook_likes'):
            if metrics['facebook_likes'] > 1000:
                score += 15
            elif metrics['facebook_likes'] > 100:
                score += 10
            else:
                score += 5
        
        if metrics.get('linkedin_followers'):
            if metrics['linkedin_followers'] > 500:
                score += 15
            elif metrics['linkedin_followers'] > 50:
                score += 10
            else:
                score += 5
        
        return min(score, 100)  # Cap at 100