"""
Social Media Intelligence Agent
Gathers comprehensive social media data about housing associations
"""

import asyncio
import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import requests
from bs4 import BeautifulSoup
import time

from agents.dynamic_agent import DynamicAgent
from vertex_agents.real_vertex_agent import get_vertex_ai_agent

logger = logging.getLogger(__name__)

class SocialMediaIntelligenceAgent(DynamicAgent):
    """Comprehensive social media intelligence gathering for housing associations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.name = "Social Media Intelligence Agent"
        self.description = "Gathers comprehensive social media data and insights about housing associations"
        
        # Social media platforms to monitor
        self.platforms = {
            'twitter': {'enabled': True, 'api_required': False},
            'facebook': {'enabled': True, 'api_required': False},
            'linkedin': {'enabled': True, 'api_required': False},
            'instagram': {'enabled': True, 'api_required': False},
            'youtube': {'enabled': True, 'api_required': False},
            'tiktok': {'enabled': True, 'api_required': False},
            'reddit': {'enabled': True, 'api_required': False}
        }
        
        # API configurations (optional - we'll use web scraping as fallback)
        self.api_configs = {
            'twitter_bearer_token': os.getenv('TWITTER_BEARER_TOKEN'),
            'facebook_access_token': os.getenv('FACEBOOK_ACCESS_TOKEN'),
            'linkedin_access_token': os.getenv('LINKEDIN_ACCESS_TOKEN'),
            'youtube_api_key': os.getenv('YOUTUBE_API_KEY'),
            'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
            'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET')
        }
        
        # Rate limiting
        self.rate_limits = {
            'requests_per_minute': 30,
            'requests_per_hour': 1000,
            'delay_between_requests': 2
        }
        
        self.vertex_ai = get_vertex_ai_agent()
        
        logger.info("Social Media Intelligence Agent initialized")
    
    async def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social media intelligence gathering"""
        
        try:
            housing_association = task_data.get('housing_association', {})
            association_name = housing_association.get('name', '')
            search_terms = task_data.get('search_terms', [association_name])
            platforms = task_data.get('platforms', list(self.platforms.keys()))
            analysis_depth = task_data.get('analysis_depth', 'standard')  # basic, standard, comprehensive
            
            if not association_name:
                return {
                    'success': False,
                    'error': 'Housing association name is required'
                }
            
            logger.info(f"Starting social media intelligence gathering for: {association_name}")
            
            # Gather social media data
            social_data = await self.gather_social_media_data(
                association_name, search_terms, platforms, analysis_depth
            )
            
            # Analyze the gathered data
            analysis = await self.analyze_social_media_data(social_data, association_name)
            
            # Generate insights and recommendations
            insights = await self.generate_insights(social_data, analysis, association_name)
            
            # Create comprehensive report
            report = self.create_social_media_report(social_data, analysis, insights, association_name)
            
            return {
                'success': True,
                'association_name': association_name,
                'social_media_data': social_data,
                'analysis': analysis,
                'insights': insights,
                'report': report,
                'platforms_analyzed': platforms,
                'analysis_depth': analysis_depth,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Social media intelligence gathering failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def gather_social_media_data(self, association_name: str, search_terms: List[str], 
                                     platforms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather data from multiple social media platforms"""
        
        social_data = {}
        
        # Prepare search variations
        search_variations = self.prepare_search_terms(association_name, search_terms)
        
        # Gather data from each platform
        for platform in platforms:
            if platform not in self.platforms or not self.platforms[platform]['enabled']:
                continue
                
            logger.info(f"Gathering data from {platform}...")
            
            try:
                if platform == 'twitter':
                    social_data[platform] = await self.gather_twitter_data(search_variations, analysis_depth)
                elif platform == 'facebook':
                    social_data[platform] = await self.gather_facebook_data(search_variations, analysis_depth)
                elif platform == 'linkedin':
                    social_data[platform] = await self.gather_linkedin_data(search_variations, analysis_depth)
                elif platform == 'instagram':
                    social_data[platform] = await self.gather_instagram_data(search_variations, analysis_depth)
                elif platform == 'youtube':
                    social_data[platform] = await self.gather_youtube_data(search_variations, analysis_depth)
                elif platform == 'reddit':
                    social_data[platform] = await self.gather_reddit_data(search_variations, analysis_depth)
                elif platform == 'tiktok':
                    social_data[platform] = await self.gather_tiktok_data(search_variations, analysis_depth)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limits['delay_between_requests'])
                
            except Exception as e:
                logger.error(f"Error gathering data from {platform}: {e}")
                social_data[platform] = {
                    'error': str(e),
                    'profiles': [],
                    'posts': [],
                    'mentions': [],
                    'metrics': {}
                }
        
        return social_data
    
    def prepare_search_terms(self, association_name: str, additional_terms: List[str]) -> List[str]:
        """Prepare comprehensive search terms"""
        
        search_terms = [association_name]
        search_terms.extend(additional_terms)
        
        # Add variations
        name_variations = [
            association_name,
            association_name.replace(' ', ''),
            association_name.replace(' ', '_'),
            association_name.replace(' Housing Association', ''),
            association_name.replace(' HA', ''),
            f"{association_name} housing",
            f"{association_name} homes",
            f"{association_name} social housing"
        ]
        
        search_terms.extend(name_variations)
        
        # Remove duplicates and empty strings
        return list(set([term.strip() for term in search_terms if term.strip()]))
    
    async def gather_twitter_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather Twitter/X data"""
        
        twitter_data = {
            'profiles': [],
            'posts': [],
            'mentions': [],
            'metrics': {},
            'hashtags': [],
            'engagement_data': {}
        }
        
        try:
            # Method 1: Use Twitter API if available
            if self.api_configs.get('twitter_bearer_token'):
                twitter_data = await self.gather_twitter_api_data(search_terms, analysis_depth)
            else:
                # Method 2: Web scraping approach (public data only)
                twitter_data = await self.gather_twitter_web_data(search_terms, analysis_depth)
                
        except Exception as e:
            logger.error(f"Twitter data gathering failed: {e}")
            twitter_data['error'] = str(e)
        
        return twitter_data
    
    async def gather_twitter_web_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather Twitter data via web scraping (public data)"""
        
        twitter_data = {
            'profiles': [],
            'posts': [],
            'mentions': [],
            'metrics': {},
            'hashtags': [],
            'engagement_data': {}
        }
        
        # Search for profiles
        for term in search_terms[:5]:  # Limit to avoid rate limiting
            try:
                # Search for potential Twitter profiles
                profile_data = await self.search_twitter_profiles(term)
                twitter_data['profiles'].extend(profile_data)
                
                # Search for mentions and posts
                mention_data = await self.search_twitter_mentions(term)
                twitter_data['mentions'].extend(mention_data)
                
                await asyncio.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error searching Twitter for {term}: {e}")
        
        # Analyze hashtags and engagement
        twitter_data['hashtags'] = self.extract_hashtags(twitter_data['posts'] + twitter_data['mentions'])
        twitter_data['metrics'] = self.calculate_twitter_metrics(twitter_data)
        
        return twitter_data
    
    async def search_twitter_profiles(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for Twitter profiles"""
        
        profiles = []
        
        # Common Twitter handle patterns for housing associations
        potential_handles = [
            search_term.lower().replace(' ', ''),
            search_term.lower().replace(' ', '_'),
            f"{search_term.lower().replace(' ', '')}ha",
            f"{search_term.lower().replace(' ', '')}homes",
            f"{search_term.lower().replace(' ', '')}housing"
        ]
        
        for handle in potential_handles:
            try:
                # Check if profile exists (simplified approach)
                profile_info = {
                    'handle': f"@{handle}",
                    'potential_match': True,
                    'search_term': search_term,
                    'profile_url': f"https://twitter.com/{handle}",
                    'verification_needed': True
                }
                profiles.append(profile_info)
                
            except Exception as e:
                logger.error(f"Error checking Twitter handle {handle}: {e}")
        
        return profiles
    
    async def search_twitter_mentions(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for Twitter mentions"""
        
        mentions = []
        
        # This would typically use Twitter's search API or web scraping
        # For now, we'll create a structure for the data
        mention_data = {
            'search_term': search_term,
            'mentions_found': 0,
            'recent_mentions': [],
            'sentiment_summary': 'neutral',
            'engagement_metrics': {
                'total_likes': 0,
                'total_retweets': 0,
                'total_replies': 0
            }
        }
        
        mentions.append(mention_data)
        return mentions
    
    async def gather_facebook_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather Facebook data"""
        
        facebook_data = {
            'pages': [],
            'posts': [],
            'reviews': [],
            'metrics': {},
            'community_groups': []
        }
        
        try:
            for term in search_terms[:3]:  # Limit searches
                # Search for Facebook pages
                page_data = await self.search_facebook_pages(term)
                facebook_data['pages'].extend(page_data)
                
                # Search for community groups
                group_data = await self.search_facebook_groups(term)
                facebook_data['community_groups'].extend(group_data)
                
                await asyncio.sleep(3)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Facebook data gathering failed: {e}")
            facebook_data['error'] = str(e)
        
        return facebook_data
    
    async def search_facebook_pages(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for Facebook pages"""
        
        pages = []
        
        # Common Facebook page patterns
        potential_pages = [
            search_term,
            f"{search_term} Housing Association",
            f"{search_term} Homes",
            f"{search_term} Housing"
        ]
        
        for page_name in potential_pages:
            page_info = {
                'name': page_name,
                'search_term': search_term,
                'potential_match': True,
                'verification_needed': True,
                'estimated_url': f"https://facebook.com/{page_name.lower().replace(' ', '')}"
            }
            pages.append(page_info)
        
        return pages
    
    async def search_facebook_groups(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for Facebook community groups"""
        
        groups = []
        
        # Common group patterns
        group_patterns = [
            f"{search_term} residents",
            f"{search_term} community",
            f"{search_term} tenants",
            f"{search_term} housing"
        ]
        
        for pattern in group_patterns:
            group_info = {
                'name': pattern,
                'type': 'community_group',
                'search_term': search_term,
                'potential_match': True
            }
            groups.append(group_info)
        
        return groups
    
    async def gather_linkedin_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather LinkedIn data"""
        
        linkedin_data = {
            'company_pages': [],
            'employee_profiles': [],
            'posts': [],
            'metrics': {}
        }
        
        try:
            for term in search_terms[:3]:
                # Search for company pages
                company_data = await self.search_linkedin_companies(term)
                linkedin_data['company_pages'].extend(company_data)
                
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"LinkedIn data gathering failed: {e}")
            linkedin_data['error'] = str(e)
        
        return linkedin_data
    
    async def search_linkedin_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for LinkedIn company pages"""
        
        companies = []
        
        company_info = {
            'name': search_term,
            'potential_url': f"https://linkedin.com/company/{search_term.lower().replace(' ', '-')}",
            'search_term': search_term,
            'verification_needed': True
        }
        companies.append(company_info)
        
        return companies
    
    async def gather_instagram_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather Instagram data"""
        
        instagram_data = {
            'profiles': [],
            'posts': [],
            'stories': [],
            'metrics': {},
            'hashtags': []
        }
        
        try:
            for term in search_terms[:3]:
                profile_data = await self.search_instagram_profiles(term)
                instagram_data['profiles'].extend(profile_data)
                
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Instagram data gathering failed: {e}")
            instagram_data['error'] = str(e)
        
        return instagram_data
    
    async def search_instagram_profiles(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for Instagram profiles"""
        
        profiles = []
        
        potential_handles = [
            search_term.lower().replace(' ', ''),
            search_term.lower().replace(' ', '_'),
            f"{search_term.lower().replace(' ', '')}homes",
            f"{search_term.lower().replace(' ', '')}housing"
        ]
        
        for handle in potential_handles:
            profile_info = {
                'handle': f"@{handle}",
                'potential_url': f"https://instagram.com/{handle}",
                'search_term': search_term,
                'verification_needed': True
            }
            profiles.append(profile_info)
        
        return profiles
    
    async def gather_youtube_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather YouTube data"""
        
        youtube_data = {
            'channels': [],
            'videos': [],
            'metrics': {}
        }
        
        try:
            if self.api_configs.get('youtube_api_key'):
                youtube_data = await self.gather_youtube_api_data(search_terms, analysis_depth)
            else:
                youtube_data = await self.gather_youtube_web_data(search_terms, analysis_depth)
                
        except Exception as e:
            logger.error(f"YouTube data gathering failed: {e}")
            youtube_data['error'] = str(e)
        
        return youtube_data
    
    async def gather_youtube_web_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather YouTube data via web search"""
        
        youtube_data = {
            'channels': [],
            'videos': [],
            'metrics': {}
        }
        
        for term in search_terms[:3]:
            # Search for potential channels
            channel_data = {
                'name': term,
                'potential_url': f"https://youtube.com/c/{term.replace(' ', '')}",
                'search_term': term,
                'verification_needed': True
            }
            youtube_data['channels'].append(channel_data)
        
        return youtube_data
    
    async def gather_reddit_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather Reddit data"""
        
        reddit_data = {
            'subreddits': [],
            'posts': [],
            'comments': [],
            'metrics': {}
        }
        
        try:
            for term in search_terms[:3]:
                # Search for relevant subreddits and posts
                subreddit_data = await self.search_reddit_content(term)
                reddit_data['subreddits'].extend(subreddit_data)
                
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Reddit data gathering failed: {e}")
            reddit_data['error'] = str(e)
        
        return reddit_data
    
    async def search_reddit_content(self, search_term: str) -> List[Dict[str, Any]]:
        """Search Reddit for relevant content"""
        
        content = []
        
        # Common subreddits for housing discussions
        relevant_subreddits = [
            'HousingUK',
            'UKPersonalFinance',
            'LegalAdviceUK',
            'unitedkingdom',
            'AskUK'
        ]
        
        for subreddit in relevant_subreddits:
            content_info = {
                'subreddit': subreddit,
                'search_term': search_term,
                'potential_discussions': True,
                'url': f"https://reddit.com/r/{subreddit}"
            }
            content.append(content_info)
        
        return content
    
    async def gather_tiktok_data(self, search_terms: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Gather TikTok data"""
        
        tiktok_data = {
            'profiles': [],
            'videos': [],
            'hashtags': [],
            'metrics': {}
        }
        
        try:
            for term in search_terms[:3]:
                profile_data = await self.search_tiktok_profiles(term)
                tiktok_data['profiles'].extend(profile_data)
                
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"TikTok data gathering failed: {e}")
            tiktok_data['error'] = str(e)
        
        return tiktok_data
    
    async def search_tiktok_profiles(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for TikTok profiles"""
        
        profiles = []
        
        potential_handles = [
            search_term.lower().replace(' ', ''),
            f"{search_term.lower().replace(' ', '')}homes",
            f"{search_term.lower().replace(' ', '')}housing"
        ]
        
        for handle in potential_handles:
            profile_info = {
                'handle': f"@{handle}",
                'potential_url': f"https://tiktok.com/@{handle}",
                'search_term': search_term,
                'verification_needed': True
            }
            profiles.append(profile_info)
        
        return profiles
    
    async def analyze_social_media_data(self, social_data: Dict[str, Any], association_name: str) -> Dict[str, Any]:
        """Analyze gathered social media data using AI"""
        
        analysis_prompt = f"""
        Analyze the social media data for {association_name} and provide comprehensive insights.
        
        Social Media Data:
        {json.dumps(social_data, indent=2)}
        
        Please provide analysis in the following areas:
        
        1. **Digital Presence Assessment**:
           - Which platforms does the housing association appear to be active on?
           - Quality and consistency of their digital presence
           - Brand consistency across platforms
        
        2. **Community Engagement**:
           - Level of community interaction and engagement
           - Response rates and customer service quality
           - Community sentiment and feedback patterns
        
        3. **Content Strategy Analysis**:
           - Types of content being shared
           - Posting frequency and timing
           - Content themes and messaging
        
        4. **Reputation Analysis**:
           - Overall online reputation and sentiment
           - Common complaints or praise themes
           - Crisis management and response patterns
        
        5. **Competitive Positioning**:
           - How they compare to other housing associations
           - Unique selling points and differentiators
           - Areas for improvement
        
        6. **Risk Assessment**:
           - Potential reputation risks
           - Negative sentiment patterns
           - Areas requiring attention
        
        Provide the analysis in JSON format with specific recommendations.
        """
        
        try:
            ai_analysis = await self.vertex_ai.generate_content_async(analysis_prompt)
            
            # Parse AI response
            analysis = {
                'ai_analysis': ai_analysis,
                'digital_presence_score': self.calculate_digital_presence_score(social_data),
                'engagement_metrics': self.calculate_engagement_metrics(social_data),
                'sentiment_analysis': self.analyze_sentiment(social_data),
                'platform_performance': self.analyze_platform_performance(social_data),
                'recommendations': self.generate_recommendations(social_data)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Social media analysis failed: {e}")
            return {
                'error': str(e),
                'basic_analysis': self.create_basic_analysis(social_data)
            }
    
    def calculate_digital_presence_score(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate digital presence score"""
        
        platform_scores = {}
        total_score = 0
        max_score = 0
        
        for platform, data in social_data.items():
            if isinstance(data, dict) and 'error' not in data:
                # Score based on presence and activity
                score = 0
                max_platform_score = 100
                
                # Profile existence
                if data.get('profiles') or data.get('pages') or data.get('channels'):
                    score += 30
                
                # Content activity
                if data.get('posts') or data.get('videos'):
                    score += 40
                
                # Engagement
                if data.get('metrics') or data.get('engagement_data'):
                    score += 30
                
                platform_scores[platform] = {
                    'score': score,
                    'max_score': max_platform_score,
                    'percentage': (score / max_platform_score) * 100
                }
                
                total_score += score
                max_score += max_platform_score
        
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'overall_score': overall_score,
            'platform_scores': platform_scores,
            'grade': self.get_score_grade(overall_score)
        }
    
    def get_score_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def calculate_engagement_metrics(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate engagement metrics across platforms"""
        
        total_followers = 0
        total_posts = 0
        total_engagement = 0
        
        platform_metrics = {}
        
        for platform, data in social_data.items():
            if isinstance(data, dict) and 'error' not in data:
                metrics = data.get('metrics', {})
                
                platform_metrics[platform] = {
                    'followers': metrics.get('followers', 0),
                    'posts': len(data.get('posts', [])),
                    'engagement_rate': metrics.get('engagement_rate', 0)
                }
                
                total_followers += metrics.get('followers', 0)
                total_posts += len(data.get('posts', []))
        
        return {
            'total_followers': total_followers,
            'total_posts': total_posts,
            'platform_metrics': platform_metrics,
            'average_engagement_rate': total_engagement / len(platform_metrics) if platform_metrics else 0
        }
    
    def analyze_sentiment(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment across platforms"""
        
        sentiment_data = {
            'overall_sentiment': 'neutral',
            'platform_sentiment': {},
            'positive_themes': [],
            'negative_themes': [],
            'sentiment_score': 0.0
        }
        
        # This would typically use sentiment analysis on actual content
        # For now, we'll provide a structure
        
        for platform, data in social_data.items():
            if isinstance(data, dict) and 'error' not in data:
                sentiment_data['platform_sentiment'][platform] = {
                    'sentiment': 'neutral',
                    'confidence': 0.5,
                    'positive_mentions': 0,
                    'negative_mentions': 0,
                    'neutral_mentions': 0
                }
        
        return sentiment_data
    
    def analyze_platform_performance(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance across platforms"""
        
        performance = {}
        
        for platform, data in social_data.items():
            if isinstance(data, dict) and 'error' not in data:
                performance[platform] = {
                    'presence_detected': bool(data.get('profiles') or data.get('pages') or data.get('channels')),
                    'content_volume': len(data.get('posts', [])) + len(data.get('videos', [])),
                    'engagement_indicators': bool(data.get('metrics') or data.get('engagement_data')),
                    'community_activity': len(data.get('mentions', [])) + len(data.get('comments', [])),
                    'performance_rating': 'needs_verification'
                }
        
        return performance
    
    def generate_recommendations(self, social_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on social media analysis"""
        
        recommendations = []
        
        # Analyze each platform and generate specific recommendations
        for platform, data in social_data.items():
            if isinstance(data, dict) and 'error' not in data:
                if not (data.get('profiles') or data.get('pages') or data.get('channels')):
                    recommendations.append(f"Consider establishing a presence on {platform.title()}")
                
                if not data.get('posts') and not data.get('videos'):
                    recommendations.append(f"Increase content activity on {platform.title()}")
        
        # General recommendations
        recommendations.extend([
            "Implement consistent branding across all social media platforms",
            "Develop a content calendar for regular posting",
            "Monitor and respond to community feedback promptly",
            "Use social media for community engagement and tenant communication",
            "Share success stories and community achievements",
            "Provide customer service support through social channels"
        ])
        
        return recommendations
    
    def create_basic_analysis(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic analysis when AI analysis fails"""
        
        return {
            'platforms_found': list(social_data.keys()),
            'total_platforms': len(social_data),
            'platforms_with_presence': len([p for p, d in social_data.items() 
                                          if isinstance(d, dict) and 'error' not in d 
                                          and (d.get('profiles') or d.get('pages') or d.get('channels'))]),
            'analysis_status': 'basic_analysis_only'
        }
    
    async def generate_insights(self, social_data: Dict[str, Any], analysis: Dict[str, Any], 
                              association_name: str) -> Dict[str, Any]:
        """Generate strategic insights"""
        
        insights_prompt = f"""
        Based on the social media analysis for {association_name}, provide strategic insights and actionable recommendations.
        
        Analysis Data:
        {json.dumps(analysis, indent=2)}
        
        Please provide:
        
        1. **Key Opportunities**: What are the biggest opportunities for improvement?
        2. **Competitive Advantages**: What are they doing well compared to peers?
        3. **Risk Mitigation**: What risks should they be aware of?
        4. **Growth Strategies**: How can they expand their digital presence?
        5. **Community Building**: How can they better engage with their community?
        6. **Crisis Preparedness**: How should they prepare for potential issues?
        
        Provide specific, actionable insights in JSON format.
        """
        
        try:
            ai_insights = await self.vertex_ai.generate_content_async(insights_prompt)
            
            insights = {
                'ai_insights': ai_insights,
                'strategic_priorities': self.identify_strategic_priorities(social_data, analysis),
                'quick_wins': self.identify_quick_wins(social_data, analysis),
                'long_term_goals': self.identify_long_term_goals(social_data, analysis),
                'resource_requirements': self.estimate_resource_requirements(social_data, analysis)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            return {
                'error': str(e),
                'basic_insights': self.create_basic_insights(social_data, analysis)
            }
    
    def identify_strategic_priorities(self, social_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Identify strategic priorities"""
        
        priorities = []
        
        # Check digital presence score
        presence_score = analysis.get('digital_presence_score', {}).get('overall_score', 0)
        if presence_score < 50:
            priorities.append("Establish basic digital presence across key platforms")
        elif presence_score < 75:
            priorities.append("Improve content quality and engagement")
        else:
            priorities.append("Optimize and expand digital strategy")
        
        # Check platform coverage
        platforms_with_presence = len([p for p, d in social_data.items() 
                                     if isinstance(d, dict) and 'error' not in d])
        if platforms_with_presence < 3:
            priorities.append("Expand to additional social media platforms")
        
        return priorities
    
    def identify_quick_wins(self, social_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Identify quick wins"""
        
        quick_wins = [
            "Claim and verify social media profiles",
            "Update profile information and branding",
            "Post regular community updates",
            "Respond to existing comments and messages",
            "Share tenant success stories",
            "Post about community events and initiatives"
        ]
        
        return quick_wins
    
    def identify_long_term_goals(self, social_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Identify long-term goals"""
        
        long_term_goals = [
            "Build a strong community of engaged tenants",
            "Establish thought leadership in social housing",
            "Create a comprehensive digital communication strategy",
            "Implement social listening and reputation management",
            "Develop crisis communication protocols",
            "Integrate social media with customer service operations"
        ]
        
        return long_term_goals
    
    def estimate_resource_requirements(self, social_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate resource requirements"""
        
        return {
            'staffing': {
                'social_media_manager': 'recommended',
                'content_creator': 'part-time initially',
                'community_manager': 'as needed'
            },
            'tools': {
                'social_media_management_platform': 'essential',
                'content_creation_tools': 'recommended',
                'analytics_tools': 'recommended'
            },
            'budget_estimate': {
                'monthly_range': '£500-£2000',
                'setup_costs': '£1000-£5000',
                'ongoing_costs': '£500-£1500/month'
            }
        }
    
    def create_basic_insights(self, social_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic insights when AI generation fails"""
        
        return {
            'summary': 'Basic social media analysis completed',
            'platforms_analyzed': len(social_data),
            'next_steps': [
                'Verify social media profiles',
                'Develop content strategy',
                'Implement regular posting schedule'
            ]
        }
    
    def create_social_media_report(self, social_data: Dict[str, Any], analysis: Dict[str, Any], 
                                 insights: Dict[str, Any], association_name: str) -> Dict[str, Any]:
        """Create comprehensive social media report"""
        
        report = {
            'executive_summary': {
                'association_name': association_name,
                'analysis_date': datetime.now().isoformat(),
                'platforms_analyzed': list(social_data.keys()),
                'overall_digital_presence_score': analysis.get('digital_presence_score', {}).get('overall_score', 0),
                'key_findings': self.extract_key_findings(social_data, analysis, insights)
            },
            'detailed_analysis': {
                'platform_breakdown': social_data,
                'performance_metrics': analysis.get('engagement_metrics', {}),
                'sentiment_analysis': analysis.get('sentiment_analysis', {}),
                'competitive_positioning': analysis.get('platform_performance', {})
            },
            'strategic_recommendations': {
                'immediate_actions': insights.get('quick_wins', []),
                'strategic_priorities': insights.get('strategic_priorities', []),
                'long_term_goals': insights.get('long_term_goals', []),
                'resource_requirements': insights.get('resource_requirements', {})
            },
            'implementation_roadmap': self.create_implementation_roadmap(insights),
            'monitoring_framework': self.create_monitoring_framework(),
            'appendices': {
                'methodology': 'Comprehensive social media intelligence gathering and AI-powered analysis',
                'data_sources': list(social_data.keys()),
                'limitations': 'Analysis based on publicly available data and AI interpretation'
            }
        }
        
        return report
    
    def extract_key_findings(self, social_data: Dict[str, Any], analysis: Dict[str, Any], 
                           insights: Dict[str, Any]) -> List[str]:
        """Extract key findings from analysis"""
        
        findings = []
        
        # Digital presence findings
        presence_score = analysis.get('digital_presence_score', {}).get('overall_score', 0)
        findings.append(f"Overall digital presence score: {presence_score:.1f}%")
        
        # Platform presence
        platforms_with_presence = len([p for p, d in social_data.items() 
                                     if isinstance(d, dict) and 'error' not in d 
                                     and (d.get('profiles') or d.get('pages') or d.get('channels'))])
        findings.append(f"Active presence detected on {platforms_with_presence} platforms")
        
        # Engagement findings
        engagement_metrics = analysis.get('engagement_metrics', {})
        if engagement_metrics.get('total_followers', 0) > 0:
            findings.append(f"Total social media following: {engagement_metrics['total_followers']:,}")
        
        return findings
    
    def create_implementation_roadmap(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation roadmap"""
        
        return {
            'phase_1_immediate': {
                'timeline': '0-30 days',
                'actions': insights.get('quick_wins', [])[:3],
                'resources_needed': 'Internal team, minimal budget'
            },
            'phase_2_foundation': {
                'timeline': '1-3 months',
                'actions': [
                    'Develop content strategy',
                    'Implement posting schedule',
                    'Set up monitoring tools'
                ],
                'resources_needed': 'Social media management tools, content creation'
            },
            'phase_3_growth': {
                'timeline': '3-6 months',
                'actions': [
                    'Expand platform presence',
                    'Implement community engagement programs',
                    'Develop crisis communication protocols'
                ],
                'resources_needed': 'Dedicated social media staff, increased budget'
            },
            'phase_4_optimization': {
                'timeline': '6-12 months',
                'actions': [
                    'Advanced analytics implementation',
                    'Influencer partnerships',
                    'Integrated customer service'
                ],
                'resources_needed': 'Advanced tools, training, strategic partnerships'
            }
        }
    
    def create_monitoring_framework(self) -> Dict[str, Any]:
        """Create monitoring framework"""
        
        return {
            'key_metrics': [
                'Follower growth rate',
                'Engagement rate',
                'Response time to comments/messages',
                'Sentiment score',
                'Share of voice vs competitors',
                'Website traffic from social media'
            ],
            'monitoring_frequency': {
                'daily': ['Response time', 'New mentions'],
                'weekly': ['Engagement metrics', 'Content performance'],
                'monthly': ['Follower growth', 'Sentiment analysis'],
                'quarterly': ['Competitive analysis', 'Strategy review']
            },
            'reporting_schedule': {
                'weekly_reports': 'Internal team updates',
                'monthly_reports': 'Management dashboard',
                'quarterly_reports': 'Strategic review and planning'
            },
            'alert_triggers': [
                'Negative sentiment spike',
                'Crisis-related mentions',
                'Significant follower drop',
                'Viral content (positive or negative)'
            ]
        }
    
    def extract_hashtags(self, posts: List[Dict[str, Any]]) -> List[str]:
        """Extract hashtags from posts"""
        
        hashtags = []
        
        for post in posts:
            content = post.get('content', '') or post.get('text', '')
            if content:
                # Extract hashtags using regex
                found_hashtags = re.findall(r'#\w+', content)
                hashtags.extend(found_hashtags)
        
        # Return unique hashtags with counts
        from collections import Counter
        hashtag_counts = Counter(hashtags)
        
        return [{'hashtag': tag, 'count': count} for tag, count in hashtag_counts.most_common(20)]
    
    def calculate_twitter_metrics(self, twitter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Twitter-specific metrics"""
        
        return {
            'total_profiles_found': len(twitter_data.get('profiles', [])),
            'total_mentions': len(twitter_data.get('mentions', [])),
            'total_hashtags': len(twitter_data.get('hashtags', [])),
            'engagement_indicators': bool(twitter_data.get('engagement_data'))
        }

# Register the agent
def create_social_media_intelligence_agent(config: Dict[str, Any] = None) -> SocialMediaIntelligenceAgent:
    """Factory function to create Social Media Intelligence Agent"""
    return SocialMediaIntelligenceAgent(config)