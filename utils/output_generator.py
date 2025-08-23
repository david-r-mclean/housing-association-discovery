import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
import os

class OutputGenerator:
    def __init__(self, associations: List[Dict]):
        self.associations = associations
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_all_outputs(self):
        """Generate all output formats"""
        print("Generating outputs...")
        
        # Ensure output directories exist
        os.makedirs('outputs/data', exist_ok=True)
        os.makedirs('outputs/reports', exist_ok=True)
        os.makedirs('outputs/league_tables', exist_ok=True)
        
        # Generate different formats
        self.export_csv()
        self.export_json()
        self.generate_summary_report()
        self.generate_league_table_html()
        
        print(f"Outputs generated in outputs/ directory")
    
    def export_csv(self):
        """Export to CSV format with enriched data"""
        flattened_data = []
        
        for assoc in self.associations:
            row = {
                # Basic company data
                'company_number': assoc.get('company_number', ''),
                'company_name': assoc.get('company_name', assoc.get('name', '')),
                'company_status': assoc.get('company_status', ''),
                'incorporation_date': assoc.get('date_of_creation', assoc.get('incorporation_date', '')),
                'company_type': assoc.get('type', ''),
                'registered_office_address': self._format_address(assoc.get('registered_office_address')),
                'sic_codes': ', '.join(assoc.get('sic_codes', [])),
                'officers_count': assoc.get('officers_count', 0),
                'recent_filings': assoc.get('recent_filings', 0),
                'last_filing_date': assoc.get('last_filing_date', ''),
                
                # Regulator data
                'region': assoc.get('region', ''),
                'source': assoc.get('source', ''),
                'regulator_url': assoc.get('regulator_url', ''),
                'housing_units': assoc.get('housing_units', ''),
                
                # Website and contact data
                'official_website': assoc.get('official_website', ''),
                'phone_numbers': ', '.join(assoc.get('phone_numbers', [])),
                'email_addresses': ', '.join(assoc.get('email_addresses', [])),
                'ceo_name': assoc.get('ceo_name', ''),
                
                # Social media
                'twitter_url': assoc.get('social_media', {}).get('twitter', ''),
                'facebook_url': assoc.get('social_media', {}).get('facebook', ''),
                'linkedin_url': assoc.get('social_media', {}).get('linkedin', ''),
                'instagram_url': assoc.get('social_media', {}).get('instagram', ''),
                'youtube_url': assoc.get('social_media', {}).get('youtube', ''),
                'twitter_followers': assoc.get('twitter_followers', ''),
                'facebook_likes': assoc.get('facebook_likes', ''),
                'linkedin_followers': assoc.get('linkedin_followers', ''),
                'social_media_activity_score': assoc.get('social_media_activity_score', 0),
                
                # Website features
                'website_has_search': assoc.get('website_has_search', False),
                'website_has_tenant_portal': assoc.get('website_has_tenant_portal', False),
                'website_has_online_services': assoc.get('website_has_online_services', False),
                'website_responsive': assoc.get('website_responsive', False),
                
                # ARC/Regulatory data
                'arc_returns_found': assoc.get('arc_returns_found', False),
                'latest_return_year': assoc.get('latest_return_year', ''),
                'total_units': assoc.get('total_units', ''),
                'rental_income': assoc.get('rental_income', ''),
                'operating_margin': assoc.get('operating_margin', ''),
                'governance_rating': assoc.get('governance_rating', ''),
                'viability_rating': assoc.get('viability_rating', ''),
                'annual_report_available': assoc.get('annual_report_available', False),
                'annual_report_url': assoc.get('annual_report_url', ''),
            }
            flattened_data.append(row)
        
        df = pd.DataFrame(flattened_data)
        filename = f'outputs/data/housing_associations_enriched_{self.timestamp}.csv'
        df.to_csv(filename, index=False)
        print(f"Enriched CSV exported: {filename}")
    
    def export_json(self):
        """Export to JSON format"""
        filename = f'outputs/data/housing_associations_{self.timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(self.associations, f, indent=2, default=str)
        print(f"JSON exported: {filename}")
    
    def generate_summary_report(self):
        """Generate summary statistics"""
        total_associations = len(self.associations)
        
        # Company types breakdown
        type_counts = {}
        status_counts = {}
        region_counts = {}
        social_media_stats = {
            'has_website': 0,
            'has_twitter': 0,
            'has_facebook': 0,
            'has_linkedin': 0,
            'has_tenant_portal': 0,
            'has_online_services': 0,
            'has_arc_data': 0
        }
        
        for assoc in self.associations:
            # Company type counts
            company_type = assoc.get('type', assoc.get('company_type', 'Unknown'))
            type_counts[company_type] = type_counts.get(company_type, 0) + 1
            
            # Status counts
            status = assoc.get('company_status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Region counts
            region = assoc.get('region', 'Unknown')
            region_counts[region] = region_counts.get(region, 0) + 1
            
            # Digital presence stats
            if assoc.get('official_website'):
                social_media_stats['has_website'] += 1
            
            social_media = assoc.get('social_media', {})
            if social_media.get('twitter'):
                social_media_stats['has_twitter'] += 1
            if social_media.get('facebook'):
                social_media_stats['has_facebook'] += 1
            if social_media.get('linkedin'):
                social_media_stats['has_linkedin'] += 1
            
            if assoc.get('website_has_tenant_portal'):
                social_media_stats['has_tenant_portal'] += 1
            if assoc.get('website_has_online_services'):
                social_media_stats['has_online_services'] += 1
            if assoc.get('arc_returns_found'):
                social_media_stats['has_arc_data'] += 1
        
        # Calculate percentages
        digital_percentages = {}
        for key, count in social_media_stats.items():
            digital_percentages[key] = round((count / total_associations) * 100, 1) if total_associations > 0 else 0
        
        summary = {
            'discovery_date': datetime.now().isoformat(),
            'total_housing_associations': total_associations,
            'company_types': type_counts,
            'company_statuses': status_counts,
            'regions': region_counts,
            'digital_presence_stats': social_media_stats,
            'digital_presence_percentages': digital_percentages,
            'top_10_by_name': [assoc.get('company_name', assoc.get('name', 'Unknown')) for assoc in self.associations[:10]],
            'top_social_media_performers': self._get_top_social_performers()
        }
        
        filename = f'outputs/reports/summary_report_{self.timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary report: {filename}")
    
    def _get_top_social_performers(self):
        """Get top social media performers"""
        # Sort by social media activity score
        sorted_by_social = sorted(
            [assoc for assoc in self.associations if assoc.get('social_media_activity_score', 0) > 0],
            key=lambda x: x.get('social_media_activity_score', 0),
            reverse=True
        )
        
        return [
            {
                'name': assoc.get('company_name', assoc.get('name', 'Unknown')),
                'activity_score': assoc.get('social_media_activity_score'),
                'twitter_followers': assoc.get('twitter_followers'),
                'facebook_likes': assoc.get('facebook_likes')
            }
            for assoc in sorted_by_social[:10]
        ]
    
    def generate_league_table_html(self):
        """Generate HTML league table"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Housing Associations League Table</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .header {{ margin-bottom: 20px; }}
                .metric {{ text-align: center; }}
                .website-link {{ color: #0066cc; }}
                .social-score {{ font-weight: bold; }}
                .high-score {{ color: #008000; }}
                .medium-score {{ color: #ff8c00; }}
                .low-score {{ color: #dc143c; }}
                .yes {{ color: #008000; font-weight: bold; }}
                .no {{ color: #dc143c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Housing Associations League Table</h1>
                <p>Generated: {timestamp}</p>
                <p>Total Associations: {total_count}</p>
                <p>Ranked by Digital Maturity Score (combination of social media activity, website features, and data availability)</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Company Name</th>
                        <th>Region</th>
                        <th>Website</th>
                        <th>Social Media Score</th>
                        <th>Twitter Followers</th>
                        <th>Facebook Likes</th>
                        <th>Tenant Portal</th>
                        <th>Online Services</th>
                        <th>ARC Data</th>
                        <th>Officers</th>
                        <th>Company Number</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div style="margin-top: 30px;">
                <h3>Scoring Methodology</h3>
                <ul>
                    <li><strong>Social Media Score:</strong> Based on number of platforms and follower counts</li>
                    <li><strong>Digital Features:</strong> Tenant portal, online services, mobile responsiveness</li>
                    <li><strong>Data Availability:</strong> ARC returns, annual reports, regulatory data</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Calculate digital maturity score for ranking
        scored_associations = []
        for assoc in self.associations:
            score = self._calculate_digital_maturity_score(assoc)
            scored_associations.append((assoc, score))
        
        # Sort by digital maturity score
        scored_associations.sort(key=lambda x: x[1], reverse=True)
        
        table_rows = ""
        for i, (assoc, score) in enumerate(scored_associations, 1):
            social_score = assoc.get('social_media_activity_score', 0)
            social_class = self._get_score_class(social_score)
            
            website_cell = ""
            if assoc.get('official_website'):
                website_cell = f'<a href="{assoc["official_website"]}" class="website-link" target="_blank">Visit</a>'
            else:
                website_cell = "No website"
            
            # Use text instead of Unicode symbols
            tenant_portal = '<span class="yes">YES</span>' if assoc.get('website_has_tenant_portal') else '<span class="no">NO</span>'
            online_services = '<span class="yes">YES</span>' if assoc.get('website_has_online_services') else '<span class="no">NO</span>'
            arc_data = '<span class="yes">YES</span>' if assoc.get('arc_returns_found') else '<span class="no">NO</span>'
            
            company_name = assoc.get('company_name', assoc.get('name', 'N/A'))
            region = assoc.get('region', 'Unknown')
            company_number = assoc.get('company_number', 'N/A')
            
            table_rows += f"""
                <tr>
                    <td class="metric">{i}</td>
                    <td>{company_name}</td>
                    <td>{region}</td>
                    <td>{website_cell}</td>
                    <td class="metric social-score {social_class}">{social_score}</td>
                    <td class="metric">{assoc.get('twitter_followers') or '-'}</td>
                    <td class="metric">{assoc.get('facebook_likes') or '-'}</td>
                    <td class="metric">{tenant_portal}</td>
                    <td class="metric">{online_services}</td>
                    <td class="metric">{arc_data}</td>
                    <td class="metric">{assoc.get('officers_count', 0)}</td>
                    <td class="metric">{company_number}</td>
                </tr>
            """
        
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_count=len(self.associations),
            table_rows=table_rows
        )
        
        filename = f'outputs/league_tables/league_table_{self.timestamp}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"League table HTML: {filename}")
    
    def _calculate_digital_maturity_score(self, assoc: Dict) -> int:
        """Calculate overall digital maturity score"""
        score = 0
        
        # Social media activity score (0-100)
        score += assoc.get('social_media_activity_score', 0)
        
        # Website features (0-30)
        if assoc.get('official_website'):
            score += 10
        if assoc.get('website_has_tenant_portal'):
            score += 10
        if assoc.get('website_has_online_services'):
            score += 10
        
        # Data availability (0-20)
        if assoc.get('arc_returns_found'):
            score += 10
        if assoc.get('annual_report_available'):
            score += 10
        
        # Contact information (0-10)
        if assoc.get('email_addresses'):
            score += 5
        if assoc.get('phone_numbers'):
            score += 5
        
        return min(score, 150)  # Cap at 150
    
    def _get_score_class(self, score: int) -> str:
        """Get CSS class for score color coding"""
        if score >= 70:
            return 'high-score'
        elif score >= 40:
            return 'medium-score'
        else:
            return 'low-score'
    
    def _format_address(self, address) -> str:
        """Format address dictionary into string"""
        if not address or not isinstance(address, dict):
            return ''
        
        parts = []
        for key in ['address_line_1', 'address_line_2', 'locality', 'postal_code']:
            if address.get(key):
                parts.append(str(address[key]))
        return ', '.join(parts)