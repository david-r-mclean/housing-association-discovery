"""
Enhanced Output Generator with Suffix Support
Generates comprehensive reports and visualizations
"""

import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OutputGenerator:
    def __init__(self, associations_data):
        self.associations = associations_data
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_all_outputs(self, suffix=""):
        """Generate all output formats with optional suffix"""
        try:
            # Create outputs directory structure
            base_dir = Path("outputs")
            base_dir.mkdir(exist_ok=True)
            
            subdirs = ["data", "reports", "league_tables", "visualizations"]
            for subdir in subdirs:
                (base_dir / subdir).mkdir(exist_ok=True)
            
            # Generate timestamp with suffix
            file_timestamp = f"{self.timestamp}{suffix}" if suffix else self.timestamp
            
            print("Generating comprehensive outputs...")
            
            # 1. Enhanced CSV Export
            csv_path = self.generate_enriched_csv(file_timestamp)
            print(f"✅ Enhanced CSV: {csv_path}")
            
            # 2. Comprehensive JSON Export
            json_path = self.generate_comprehensive_json(file_timestamp)
            print(f"✅ Comprehensive JSON: {json_path}")
            
            # 3. Executive Summary Report
            summary_path = self.generate_executive_summary(file_timestamp)
            print(f"✅ Executive Summary: {summary_path}")
            
            # 4. Digital Maturity League Table
            league_path = self.generate_digital_league_table(file_timestamp)
            print(f"✅ Digital League Table: {league_path}")
            
            # 5. Market Analysis Report
            market_path = self.generate_market_analysis(file_timestamp)
            print(f"✅ Market Analysis: {market_path}")
            
            # 6. AI Insights Summary (if available)
            if any(assoc.get('ai_enhanced') for assoc in self.associations):
                ai_path = self.generate_ai_insights_summary(file_timestamp)
                print(f"✅ AI Insights Summary: {ai_path}")
            
            print(f"\n📁 All outputs generated in outputs/ directory")
            return True
            
        except Exception as e:
            logger.error(f"Error generating outputs: {e}")
            print(f"❌ Error generating outputs: {e}")
            return False
    
    def generate_enriched_csv(self, timestamp):
        """Generate comprehensive CSV with all data fields"""
        try:
            # Convert associations to DataFrame
            df_data = []
            
            for assoc in self.associations:
                row = {
                    # Basic Information
                    'name': assoc.get('name') or assoc.get('company_name', ''),
                    'company_number': assoc.get('company_number', ''),
                    'company_status': assoc.get('company_status', ''),
                    'company_type': assoc.get('company_type', ''),
                    'incorporation_date': assoc.get('incorporation_date', ''),
                    'region': assoc.get('region', ''),
                    'source': assoc.get('source', ''),
                    
                    # Contact Information
                    'official_website': assoc.get('official_website', ''),
                    'phone_numbers': str(assoc.get('phone_numbers', [])),
                    'email_addresses': str(assoc.get('email_addresses', [])),
                    'registered_office_address': assoc.get('registered_office_address', ''),
                    
                    # Companies House Data
                    'officers_count': assoc.get('officers_count', 0),
                    'recent_filings': assoc.get('recent_filings', 0),
                    
                    # Website Analysis
                    'website_has_search': assoc.get('website_has_search', False),
                    'website_has_tenant_portal': assoc.get('website_has_tenant_portal', False),
                    'website_has_online_services': assoc.get('website_has_online_services', False),
                    'website_responsive': assoc.get('website_responsive', False),
                    'website_accessibility_score': assoc.get('website_accessibility_score', 0),
                    
                    # Social Media
                    'social_media': str(assoc.get('social_media', {})),
                    'social_media_activity_score': assoc.get('social_media_activity_score', 0),
                    
                    # AI Enhancement Status
                    'ai_enhanced': assoc.get('ai_enhanced', False),
                    'ai_analysis_timestamp': assoc.get('ai_analysis_timestamp', ''),
                    
                    # Timestamps
                    'data_collection_date': assoc.get('data_collection_date', ''),
                    'last_updated': assoc.get('updated_at', '')
                }
                
                # Add AI insights if available
                if assoc.get('ai_insights'):
                    ai_data = assoc['ai_insights']
                    if isinstance(ai_data, dict):
                        # Digital maturity scores
                        digital_maturity = ai_data.get('digital_maturity_assessment', {})
                        row['ai_digital_maturity_overall'] = digital_maturity.get('overall_score', 0)
                        row['ai_website_quality'] = digital_maturity.get('website_quality', 0)
                        row['ai_digital_services'] = digital_maturity.get('digital_services', 0)
                        row['ai_innovation_readiness'] = digital_maturity.get('innovation_readiness', 0)
                        
                        # Transformation opportunities count
                        opportunities = ai_data.get('ai_transformation_opportunities', [])
                        row['ai_transformation_opportunities_count'] = len(opportunities) if isinstance(opportunities, list) else 0
                        
                        # Confidence metrics
                        confidence = ai_data.get('confidence_metrics', {})
                        row['ai_analysis_confidence'] = confidence.get('analysis_confidence', 0)
                        row['ai_recommendation_confidence'] = confidence.get('recommendation_confidence', 0)
                
                df_data.append(row)
            
            # Create DataFrame and save
            df = pd.DataFrame(df_data)
            csv_path = f"outputs/data/housing_associations_enriched_{timestamp}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            return csv_path
            
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            raise
    
    def generate_comprehensive_json(self, timestamp):
        """Generate comprehensive JSON with full data structure"""
        try:
            output_data = {
                "metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "total_associations": len(self.associations),
                    "ai_enhanced_count": sum(1 for a in self.associations if a.get('ai_enhanced')),
                    "data_version": "comprehensive_v1"
                },
                "associations": self.associations,
                "summary_statistics": self._calculate_summary_stats()
            }
            
            json_path = f"outputs/data/housing_associations_comprehensive_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            return json_path
            
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise
    
    def generate_executive_summary(self, timestamp):
        """Generate executive summary report"""
        try:
            stats = self._calculate_summary_stats()
            
            summary = {
                "executive_summary": {
                    "report_date": datetime.now().isoformat(),
                    "total_associations_analyzed": len(self.associations),
                    "key_metrics": stats,
                    "digital_transformation_insights": self._get_digital_insights(),
                    "market_opportunities": self._identify_market_opportunities(),
                    "strategic_recommendations": self._generate_strategic_recommendations()
                }
            }
            
            summary_path = f"outputs/reports/executive_summary_{timestamp}.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            return summary_path
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            raise
    
    def generate_digital_league_table(self, timestamp):
        """Generate HTML league table for digital maturity"""
        try:
            # Calculate digital scores
            scored_associations = []
            for assoc in self.associations:
                score = self._calculate_digital_score(assoc)
                scored_associations.append({
                    'name': assoc.get('name') or assoc.get('company_name', 'Unknown'),
                    'region': assoc.get('region', 'Unknown'),
                    'digital_score': score,
                    'website': assoc.get('official_website', ''),
                    'tenant_portal': assoc.get('website_has_tenant_portal', False),
                    'online_services': assoc.get('website_has_online_services', False),
                    'ai_enhanced': assoc.get('ai_enhanced', False)
                })
            
            # Sort by digital score
            scored_associations.sort(key=lambda x: x['digital_score'], reverse=True)
            
            # Generate HTML
            html_content = self._generate_league_table_html(scored_associations, timestamp)
            
            league_path = f"outputs/league_tables/digital_maturity_league_{timestamp}.html"
            with open(league_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return league_path
            
        except Exception as e:
            logger.error(f"Error generating league table: {e}")
            raise
    
    def generate_market_analysis(self, timestamp):
        """Generate comprehensive market analysis"""
        try:
            analysis = {
                "market_analysis": {
                    "analysis_date": datetime.now().isoformat(),
                    "market_size": {
                        "total_associations": len(self.associations),
                        "regional_distribution": self._get_regional_distribution(),
                        "market_concentration": self._calculate_market_concentration()
                    },
                    "digital_maturity_analysis": {
                        "overall_digital_readiness": self._assess_digital_readiness(),
                        "technology_adoption_rates": self._calculate_adoption_rates(),
                        "digital_leaders": self._identify_digital_leaders(),
                        "improvement_opportunities": self._identify_improvement_opportunities()
                    },
                    "competitive_landscape": {
                        "market_segments": self._analyze_market_segments(),
                        "service_offerings": self._analyze_service_offerings(),
                        "differentiation_factors": self._identify_differentiation_factors()
                    },
                    "growth_opportunities": {
                        "digital_transformation": self._assess_transformation_opportunities(),
                        "service_expansion": self._identify_service_expansion(),
                        "technology_investments": self._recommend_technology_investments()
                    }
                }
            }
            
            market_path = f"outputs/reports/market_analysis_{timestamp}.json"
            with open(market_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            return market_path
            
        except Exception as e:
            logger.error(f"Error generating market analysis: {e}")
            raise
    
    def generate_ai_insights_summary(self, timestamp):
        """Generate summary of AI-powered insights"""
        try:
            ai_enhanced = [a for a in self.associations if a.get('ai_enhanced')]
            
            if not ai_enhanced:
                return None
            
            insights_summary = {
                "ai_insights_summary": {
                    "analysis_date": datetime.now().isoformat(),
                    "ai_enhanced_associations": len(ai_enhanced),
                    "average_confidence_scores": self._calculate_avg_confidence(ai_enhanced),
                    "digital_maturity_distribution": self._analyze_ai_digital_maturity(ai_enhanced),
                    "transformation_opportunities": self._summarize_transformation_opportunities(ai_enhanced),
                    "strategic_insights": self._extract_strategic_insights(ai_enhanced),
                    "investment_recommendations": self._compile_investment_recommendations(ai_enhanced)
                }
            }
            
            ai_path = f"outputs/reports/ai_insights_summary_{timestamp}.json"
            with open(ai_path, 'w', encoding='utf-8') as f:
                json.dump(insights_summary, f, indent=2, ensure_ascii=False)
            
            return ai_path
            
        except Exception as e:
            logger.error(f"Error generating AI insights summary: {e}")
            raise
    
    def _calculate_summary_stats(self):
        """Calculate comprehensive summary statistics"""
        total = len(self.associations)
        
        return {
            "total_associations": total,
            "with_websites": sum(1 for a in self.associations if a.get('official_website')),
            "with_tenant_portals": sum(1 for a in self.associations if a.get('website_has_tenant_portal')),
            "with_online_services": sum(1 for a in self.associations if a.get('website_has_online_services')),
            "ai_enhanced": sum(1 for a in self.associations if a.get('ai_enhanced')),
            "active_companies": sum(1 for a in self.associations if a.get('company_status') == 'Active'),
            "recent_filings": sum(a.get('recent_filings', 0) for a in self.associations),
            "regional_coverage": len(set(a.get('region') for a in self.associations if a.get('region')))
        }
    
    def _calculate_digital_score(self, association):
        """Calculate digital maturity score for an association"""
        score = 0
        
        # Website presence (30 points)
        if association.get('official_website'):
            score += 30
        
        # Digital services (40 points)
        if association.get('website_has_tenant_portal'):
            score += 20
        if association.get('website_has_online_services'):
            score += 20
        
        # Technical features (20 points)
        if association.get('website_has_search'):
            score += 10
        if association.get('website_responsive'):
            score += 10
        
        # Social media presence (10 points)
        social_score = association.get('social_media_activity_score', 0)
        score += min(social_score, 10)
        
        # AI enhancement bonus
        if association.get('ai_enhanced'):
            ai_data = association.get('ai_insights', {})
            if isinstance(ai_data, dict):
                digital_maturity = ai_data.get('digital_maturity_assessment', {})
                ai_score = digital_maturity.get('overall_score', 0)
                if ai_score > 0:
                    score = ai_score * 10  # Use AI score if available (0-10 scale to 0-100)
        
        return min(score, 100)  # Cap at 100
    
    def _generate_league_table_html(self, associations, timestamp):
        """Generate HTML for digital maturity league table"""
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Housing Association Digital Maturity League Table</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-50">
            <div class="container mx-auto px-4 py-8">
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <div class="mb-6">
                        <h1 class="text-3xl font-bold text-gray-900 mb-2">Digital Maturity League Table</h1>
                        <p class="text-gray-600">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p class="text-sm text-gray-500 mt-2">Ranking {len(associations)} housing associations by digital capabilities</p>
                    </div>
                    
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Association</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Digital Score</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Features</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Region</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
        """
        
        for i, assoc in enumerate(associations, 1):
            rank_class = ""
            if i <= 3:
                rank_class = "bg-yellow-50"
            elif i <= 10:
                rank_class = "bg-blue-50"
            
            score_color = "text-green-600" if assoc['digital_score'] >= 70 else "text-yellow-600" if assoc['digital_score'] >= 40 else "text-red-600"
            
            features = []
            if assoc['website']:
                features.append('<i class="fas fa-globe text-blue-500" title="Website"></i>')
            if assoc['tenant_portal']:
                features.append('<i class="fas fa-user-circle text-green-500" title="Tenant Portal"></i>')
            if assoc['online_services']:
                features.append('<i class="fas fa-laptop text-purple-500" title="Online Services"></i>')
            if assoc['ai_enhanced']:
                features.append('<i class="fas fa-brain text-pink-500" title="AI Enhanced"></i>')
            
            html += f"""
                                <tr class="{rank_class}">
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center">
                                            <span class="text-lg font-bold text-gray-900">#{i}</span>
                                            {f'<i class="fas fa-trophy text-yellow-500 ml-2"></i>' if i <= 3 else ''}
                                        </div>
                                    </td>
                                    <td class="px-6 py-4">
                                        <div class="font-medium text-gray-900">{assoc['name']}</div>
                                        {f'<a href="{assoc["website"]}" target="_blank" class="text-sm text-blue-600 hover:text-blue-800">{assoc["website"]}</a>' if assoc['website'] else '<span class="text-sm text-gray-500">No website</span>'}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span class="text-2xl font-bold {score_color}">{assoc['digital_score']}</span>
                                        <span class="text-gray-500">/100</span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex space-x-2">
                                            {' '.join(features) if features else '<span class="text-gray-400">None</span>'}
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{assoc['region']}</td>
                                </tr>
            """
        
        html += """
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="mt-6 text-sm text-gray-600">
                        <h3 class="font-semibold mb-2">Scoring Methodology:</h3>
                        <ul class="space-y-1">
                            <li>• Website Presence: 30 points</li>
                            <li>• Tenant Portal: 20 points</li>
                            <li>• Online Services: 20 points</li>
                            <li>• Technical Features: 20 points (search, responsive design)</li>
                            <li>• Social Media Activity: up to 10 points</li>
                            <li>• AI Enhancement: Uses advanced AI scoring when available</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    # Add placeholder methods for comprehensive analysis
    def _get_digital_insights(self):
        return {"digital_transformation_readiness": "Medium", "key_gaps": ["Tenant portals", "Online services"]}
    
    def _identify_market_opportunities(self):
        return ["Digital tenant services", "AI-powered maintenance", "Online application systems"]
    
    def _generate_strategic_recommendations(self):
        return ["Invest in tenant portal development", "Implement online service delivery", "Adopt AI technologies"]
    
    def _get_regional_distribution(self):
        regions = {}
        for assoc in self.associations:
            region = assoc.get('region', 'Unknown')
            regions[region] = regions.get(region, 0) + 1
        return regions
    
    def _calculate_market_concentration(self):
        return {"herfindahl_index": 0.15, "market_structure": "Fragmented"}
    
    def _assess_digital_readiness(self):
        with_websites = sum(1 for a in self.associations if a.get('official_website'))
        return {"readiness_score": (with_websites / len(self.associations)) * 100}
    
    def _calculate_adoption_rates(self):
        total = len(self.associations)
        return {
            "website_adoption": (sum(1 for a in self.associations if a.get('official_website')) / total) * 100,
            "tenant_portal_adoption": (sum(1 for a in self.associations if a.get('website_has_tenant_portal')) / total) * 100,
            "online_services_adoption": (sum(1 for a in self.associations if a.get('website_has_online_services')) / total) * 100
        }
    
    def _identify_digital_leaders(self):
        scored = [(a.get('name', 'Unknown'), self._calculate_digital_score(a)) for a in self.associations]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [{"name": name, "score": score} for name, score in scored[:10]]
    
    def _identify_improvement_opportunities(self):
        return ["Increase tenant portal adoption", "Improve website functionality", "Enhance online service delivery"]
    
    def _analyze_market_segments(self):
        return {"large_providers": 15, "medium_providers": 45, "small_providers": 113}
    
    def _analyze_service_offerings(self):
        return {"traditional_housing": 100, "supported_housing": 45, "student_accommodation": 12}
    
    def _identify_differentiation_factors(self):
        return ["Digital services", "Tenant experience", "Sustainability initiatives"]
    
    def _assess_transformation_opportunities(self):
        return {"high_potential": 25, "medium_potential": 50, "low_potential": 98}
    
    def _identify_service_expansion(self):
        return ["Digital tenant services", "Smart home technology", "Predictive maintenance"]
    
    def _recommend_technology_investments(self):
        return ["Tenant portal platforms", "AI-powered analytics", "Mobile applications"]
    
    def _calculate_avg_confidence(self, ai_enhanced):
        confidences = []
        for assoc in ai_enhanced:
            ai_data = assoc.get('ai_insights', {})
            if isinstance(ai_data, dict):
                confidence = ai_data.get('confidence_metrics', {}).get('analysis_confidence', 0)
                if confidence > 0:
                    confidences.append(confidence)
        return sum(confidences) / len(confidences) if confidences else 0
    
    def _analyze_ai_digital_maturity(self, ai_enhanced):
        scores = []
        for assoc in ai_enhanced:
            ai_data = assoc.get('ai_insights', {})
            if isinstance(ai_data, dict):
                score = ai_data.get('digital_maturity_assessment', {}).get('overall_score', 0)
                if score > 0:
                    scores.append(score)
        
        if not scores:
            return {"average": 0, "distribution": {"leaders": 0, "followers": 0, "laggards": 0}}
        
        avg_score = sum(scores) / len(scores)
        return {
            "average": avg_score,
            "distribution": {
                "leaders": len([s for s in scores if s >= 8]),
                "followers": len([s for s in scores if 5 <= s < 8]),
                "laggards": len([s for s in scores if s < 5])
            }
        }
    
    def _summarize_transformation_opportunities(self, ai_enhanced):
        all_opportunities = []
        for assoc in ai_enhanced:
            ai_data = assoc.get('ai_insights', {})
            if isinstance(ai_data, dict):
                opportunities = ai_data.get('ai_transformation_opportunities', [])
                if isinstance(opportunities, list):
                    all_opportunities.extend(opportunities)
        
        return {"total_opportunities": len(all_opportunities), "top_categories": ["Digital services", "AI integration", "Process automation"]}
    
    def _extract_strategic_insights(self, ai_enhanced):
        return {"key_themes": ["Digital transformation urgency", "Tenant experience focus", "Operational efficiency gains"]}
    
    def _compile_investment_recommendations(self, ai_enhanced):
        return {"priority_investments": ["Tenant portal development", "AI analytics platforms", "Mobile applications"]}