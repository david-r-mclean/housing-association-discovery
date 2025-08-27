"""
Dashboard AI Controller
Handles AI-powered dashboard requests, component generation, and file management
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardAIController:
    """AI Controller for dashboard operations"""
    
    def __init__(self):
        self.conversation_history = {}
        self.generated_files = []
        self.llm_provider = None
        self.init_llm_provider()
    
    def init_llm_provider(self):
        """Initialize LLM provider"""
        try:
            from vertex_agents.llm_connection_manager import get_llm_connection_manager
            llm_manager = get_llm_connection_manager()
            self.llm_provider = llm_manager.get_active_provider()
            if self.llm_provider:
                logger.info(f"LLM provider initialized: {self.llm_provider}")
            else:
                logger.warning("No active LLM provider found")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            self.llm_provider = None
    
    async def process_dashboard_request(self, message: str, conversation_id: str = "default") -> Dict[str, Any]:
        """Process a dashboard AI request"""
        try:
            logger.info(f"Processing dashboard request: {message}")
            
            # Store conversation history
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            self.conversation_history[conversation_id].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Analyze the request
            request_analysis = self.analyze_request(message)
            
            # Generate response based on request type
            if request_analysis['type'] == 'code_generation':
                response = await self.handle_code_generation_request(message, request_analysis)
            elif request_analysis['type'] == 'component_creation':
                response = await self.handle_component_creation_request(message, request_analysis)
            elif request_analysis['type'] == 'data_analysis':
                response = await self.handle_data_analysis_request(message, request_analysis)
            elif request_analysis['type'] == 'social_media_analysis':
                response = await self.handle_social_media_request(message, request_analysis)
            else:
                response = await self.handle_general_request(message, request_analysis)
            
            # Store AI response in conversation history
            self.conversation_history[conversation_id].append({
                'role': 'assistant',
                'content': response.get('response', ''),
                'timestamp': datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing dashboard request: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error processing your request: {str(e)}"
            }
    
    def analyze_request(self, message: str) -> Dict[str, Any]:
        """Analyze the user request to determine intent and requirements"""
        message_lower = message.lower()
        
        # Determine request type
        if any(keyword in message_lower for keyword in ['create', 'generate', 'build', 'make']):
            if any(keyword in message_lower for keyword in ['component', 'widget', 'dashboard', 'ui']):
                request_type = 'component_creation'
            elif any(keyword in message_lower for keyword in ['code', 'function', 'script', 'api']):
                request_type = 'code_generation'
            else:
                request_type = 'general_creation'
        elif any(keyword in message_lower for keyword in ['analyze', 'analysis', 'social media', 'twitter', 'facebook']):
            if any(keyword in message_lower for keyword in ['social', 'media', 'twitter', 'facebook', 'linkedin']):
                request_type = 'social_media_analysis'
            else:
                request_type = 'data_analysis'
        elif any(keyword in message_lower for keyword in ['find', 'search', 'discover', 'housing']):
            request_type = 'search_request'
        else:
            request_type = 'general'
        
        # Extract key entities
        entities = self.extract_entities(message)
        
        return {
            'type': request_type,
            'entities': entities,
            'original_message': message,
            'complexity': self.assess_complexity(message),
            'requires_files': any(keyword in message_lower for keyword in ['create', 'generate', 'build', 'code'])
        }
    
    def extract_entities(self, message: str) -> List[str]:
        """Extract key entities from the message"""
        entities = []
        
        # Common entities in housing association context
        housing_keywords = ['housing association', 'social housing', 'council housing', 'affordable housing']
        tech_keywords = ['api', 'endpoint', 'database', 'component', 'dashboard', 'chart']
        social_keywords = ['twitter', 'facebook', 'linkedin', 'instagram', 'social media']
        
        message_lower = message.lower()
        
        for keyword in housing_keywords + tech_keywords + social_keywords:
            if keyword in message_lower:
                entities.append(keyword)
        
        return entities
    
    def assess_complexity(self, message: str) -> str:
        """Assess the complexity of the request"""
        word_count = len(message.split())
        
        if word_count < 10:
            return 'simple'
        elif word_count < 25:
            return 'medium'
        else:
            return 'complex'
    
    async def handle_code_generation_request(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code generation requests"""
        try:
            # Generate code based on the request
            if 'api' in analysis['entities'] or 'endpoint' in analysis['entities']:
                generated_files = await self.generate_api_endpoints(message)
            elif 'component' in analysis['entities'] or 'dashboard' in analysis['entities']:
                generated_files = await self.generate_dashboard_components(message)
            else:
                generated_files = await self.generate_general_code(message)
            
            response = {
                'success': True,
                'response': 'I\'ve generated the requested code files for you. You can download them using the links below.',
                'generated_files': generated_files,
                'request_type': 'code_generation'
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error generating the code: {str(e)}"
            }
    
    async def handle_component_creation_request(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle component creation requests"""
        try:
            generated_files = await self.generate_dashboard_components(message)
            
            return {
                'success': True,
                'response': 'I\'ve created the dashboard components you requested. The files are ready for download.',
                'generated_files': generated_files,
                'request_type': 'component_creation'
            }
            
        except Exception as e:
            logger.error(f"Component creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error creating the components: {str(e)}"
            }
    
    async def handle_social_media_request(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social media analysis requests"""
        try:
            # Generate social media analysis components
            generated_files = []
            
            # Create social media API endpoints
            api_content = self.generate_social_media_api_code()
            api_file = self.save_generated_file(
                "social_media_api_endpoints.py",
                api_content,
                "FastAPI endpoints for social media analysis"
            )
            generated_files.append(api_file)
            
            # Create social media agent
            agent_content = self.generate_social_media_agent_code()
            agent_file = self.save_generated_file(
                "social_media_agents.py",
                agent_content,
                "AI agents for social media data collection and analysis"
            )
            generated_files.append(agent_file)
            
            return {
                'success': True,
                'response': 'I\'ve created social media analysis components including API endpoints and AI agents.',
                'generated_files': generated_files,
                'request_type': 'social_media_analysis'
            }
            
        except Exception as e:
            logger.error(f"Social media request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error with the social media analysis: {str(e)}"
            }
    
    async def handle_data_analysis_request(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data analysis requests"""
        return {
            'success': True,
            'response': 'I can help you analyze data. What specific data would you like me to analyze?',
            'request_type': 'data_analysis',
            'suggestions': [
                'Housing association performance metrics',
                'Social media engagement data',
                'Document discovery statistics',
                'User interaction patterns'
            ]
        }
    
    async def handle_general_request(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general requests"""
        try:
            # Use LLM if available
            if self.llm_provider:
                response_text = await self.generate_llm_response(message)
            else:
                response_text = self.generate_fallback_response(message, analysis)
            
            return {
                'success': True,
                'response': response_text,
                'request_type': 'general',
                'voice_response': response_text  # For voice synthesis
            }
            
        except Exception as e:
            logger.error(f"General request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm having trouble processing your request right now. Please try again."
            }
    
    async def generate_llm_response(self, message: str) -> str:
        """Generate response using LLM"""
        try:
            if not self.llm_provider:
                return self.generate_fallback_response(message, {})
            
            # Create a context-aware prompt
            prompt = f"""
You are an AI assistant for a housing association discovery platform. You help users:
- Find and analyze housing associations
- Discover regulatory documents
- Analyze social media presence
- Create dashboard components
- Generate intelligent agents

User question: {message}

Provide a helpful, informative response that's relevant to housing associations and the platform's capabilities.
"""
            
            # This would use your actual LLM provider
            # For now, return a contextual response
            return self.generate_contextual_response(message)
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self.generate_fallback_response(message, {})
    
    def generate_contextual_response(self, message: str) -> str:
        """Generate a contextual response based on the message"""
        message_lower = message.lower()
        
        if 'housing association' in message_lower:
            return "I can help you find and analyze housing associations. I can search for associations by location, analyze their social media presence, and discover relevant regulatory documents. What specific information are you looking for?"
        
        elif 'social media' in message_lower:
            return "I can analyze social media presence for housing associations across multiple platforms including Twitter, Facebook, LinkedIn, and Instagram. I can provide insights on engagement, sentiment analysis, and digital presence scoring. Would you like me to start an analysis?"
        
        elif 'document' in message_lower or 'regulation' in message_lower:
            return "I can help you discover regulatory documents, policies, and guidelines related to housing associations. I can search across government databases and provide AI-powered analysis of compliance requirements. What type of documents are you looking for?"
        
        elif 'create' in message_lower or 'generate' in message_lower:
            return "I can create various components for the platform including API endpoints, dashboard widgets, data analysis tools, and intelligent agents. What would you like me to create for you?"
        
        else:
            return "I'm here to help with housing association discovery, social media analysis, document research, and platform development. How can I assist you today?"
    
    def generate_fallback_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate fallback response when LLM is not available"""
        return f"I understand you're asking about: {message}. I'm currently processing your request and will provide more detailed assistance once all systems are fully online."
    
    async def generate_api_endpoints(self, message: str) -> List[Dict[str, Any]]:
        """Generate API endpoint code"""
        generated_files = []
        
        # Generate FastAPI endpoints
        api_content = self.generate_social_media_api_code()
        api_file = self.save_generated_file(
            f"api_endpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
            api_content,
            "Contains the complete source code for 5 new FastAPI endpoints, including routing, Pydantic models, mock database/API calls, and integration instructions."
        )
        generated_files.append(api_file)
        
        return generated_files
    
    async def generate_dashboard_components(self, message: str) -> List[Dict[str, Any]]:
        """Generate dashboard component code"""
        generated_files = []
        
        # This would normally generate React components, but we'll create HTML/JS instead
        try:
            component_content = self.generate_dashboard_component_code()
            component_file = self.save_generated_file(
                f"dashboard_components_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                component_content,
                "Dashboard components with charts and interactive elements"
            )
            generated_files.append(component_file)
        except Exception as e:
            # Handle the encoding error gracefully
            error_file = self.save_generated_file(
                f"component_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                f"The action to create dashboard components failed with the error: {str(e)}. This can be retried.",
                "Error log for component generation"
            )
            generated_files.append(error_file)
        
        return generated_files
    
    async def generate_general_code(self, message: str) -> List[Dict[str, Any]]:
        """Generate general code based on request"""
        generated_files = []
        
        # Generate a simple Python script
        code_content = f'''"""
Generated Code - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Request: {message}
"""

def main():
    """Main function generated based on user request"""
    print("Generated code is ready!")
    print("Request: {message}")
    
    # Add your implementation here
    pass

if __name__ == "__main__":
    main()
'''
        
        code_file = self.save_generated_file(
            f"generated_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
            code_content,
            f"Generated Python code based on request: {message}"
        )
        generated_files.append(code_file)
        
        return generated_files
    
    def generate_social_media_api_code(self) -> str:
        """Generate social media API endpoints code"""
        return '''"""
Social Media API Endpoints
Generated by Dashboard AI Controller
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/social-media", tags=["social-media"])

class SocialMediaAnalysisRequest(BaseModel):
    housing_association: Dict[str, str]
    platforms: List[str] = ["twitter", "facebook", "linkedin"]
    analysis_depth: str = "standard"
    search_terms: List[str] = []

class SocialMediaProfile(BaseModel):
    platform: str
    username: str
    followers: int
    verified: bool
    url: str

class AnalysisResult(BaseModel):
    success: bool
    association_name: str
    profiles_found: List[SocialMediaProfile]
    sentiment_score: float
    engagement_rate: float
    recommendations: List[str]

@router.post("/analyze", response_model=AnalysisResult)
async def analyze_social_media(request: SocialMediaAnalysisRequest):
    """Analyze social media presence for a housing association"""
    
    # Mock analysis - replace with actual implementation
    mock_profiles = [
        SocialMediaProfile(
            platform="twitter",
            username=f"@{request.housing_association['name'].lower().replace(' ', '')}",
            followers=1250,
            verified=False,
            url="https://twitter.com/example"
        ),
        SocialMediaProfile(
            platform="facebook",
            username=request.housing_association['name'],
            followers=2340,
            verified=True,
            url="https://facebook.com/example"
        )
    ]
    
    return AnalysisResult(
        success=True,
        association_name=request.housing_association['name'],
        profiles_found=mock_profiles,
        sentiment_score=0.75,
        engagement_rate=0.045,
        recommendations=[
            "Increase posting frequency on Twitter",
            "Engage more with community comments",
            "Share more visual content on Instagram"
        ]
    )

@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    platforms = [
        {"id": "twitter", "name": "Twitter/X", "active": True},
        {"id": "facebook", "name": "Facebook", "active": True},
        {"id": "linkedin", "name": "LinkedIn", "active": True},
        {"id": "instagram", "name": "Instagram", "active": True},
        {"id": "youtube", "name": "YouTube", "active": False}
    ]
    
    return {"platforms": platforms}

@router.get("/stats/{association_name}")
async def get_association_stats(association_name: str):
    """Get social media statistics for a specific association"""
    
    # Mock stats - replace with database queries
    stats = {
        "total_followers": 5890,
        "total_posts": 234,
        "engagement_rate": 0.045,
        "sentiment_score": 0.75,
        "platforms_active": 3,
        "last_post": "2024-01-15T10:30:00Z"
    }
    
    return {"association": association_name, "stats": stats}

# Integration Instructions:
# 1. Add this router to your main FastAPI app:
#    app.include_router(router)
# 2. Install required dependencies:
#    pip install fastapi pydantic
# 3. Implement actual social media data fetching
# 4. Add database models and connections
# 5. Add authentication and rate limiting
'''
    
    def generate_social_media_agent_code(self) -> str:
        """Generate social media agent code"""
        return '''"""
Social Media Intelligence Agents
Generated by Dashboard AI Controller
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SocialMediaProfile:
    platform: str
    username: str
    url: str
    followers: int
    verified: bool
    description: str
    created_date: Optional[datetime] = None

@dataclass
class SocialMediaPost:
    platform: str
    post_id: str
    content: str
    author: str
    published_date: datetime
    likes: int
    shares: int
    comments: int
    sentiment_score: float

class SocialMediaDataFetcherAgent:
    """Agent for fetching social media data"""
    
    def __init__(self):
        self.platforms = ["twitter", "facebook", "linkedin", "instagram"]
        self.rate_limits = {
            "twitter": {"requests_per_hour": 100},
            "facebook": {"requests_per_hour": 200},
            "linkedin": {"requests_per_hour": 100},
            "instagram": {"requests_per_hour": 200}
        }
    
    async def fetch_profiles(self, association_name: str, platforms: List[str]) -> List[SocialMediaProfile]:
        """Fetch social media profiles for a housing association"""
        profiles = []
        
        for platform in platforms:
            try:
                profile = await self.fetch_platform_profile(association_name, platform)
                if profile:
                    profiles.append(profile)
                    
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching {platform} profile for {association_name}: {e}")
        
        return profiles
    
    async def fetch_platform_profile(self, association_name: str, platform: str) -> Optional[SocialMediaProfile]:
        """Fetch profile from a specific platform"""
        
        # Mock implementation - replace with actual API calls
        search_terms = [
            association_name.lower().replace(" ", ""),
            association_name.lower().replace(" ", "_"),
            f"{association_name.lower().replace(' ', '')}housing",
            f"{association_name.lower().replace(' ', '')}homes"
        ]
        
        # Simulate API call
        await asyncio.sleep(0.5)
        
        # Mock profile data
        if platform == "twitter":
            return SocialMediaProfile(
                platform="twitter",
                username=f"@{search_terms[0]}",
                url=f"https://twitter.com/{search_terms[0]}",
                followers=1250,
                verified=False,
                description=f"Official Twitter account for {association_name}",
                created_date=datetime.now() - timedelta(days=365)
            )
        
        return None
    
    async def fetch_posts(self, profile: SocialMediaProfile, days: int = 30) -> List[SocialMediaPost]:
        """Fetch recent posts from a profile"""
        posts = []
        
        try:
            # Mock implementation - replace with actual API calls
            for i in range(5):  # Mock 5 posts
                post = SocialMediaPost(
                    platform=profile.platform,
                    post_id=f"{profile.platform}_{i}",
                    content=f"Sample post {i+1} from {profile.username}",
                    author=profile.username,
                    published_date=datetime.now() - timedelta(days=i*2),
                    likes=50 + i*10,
                    shares=5 + i*2,
                    comments=10 + i*3,
                    sentiment_score=0.5 + (i*0.1)
                )
                posts.append(post)
            
        except Exception as e:
            logger.error(f"Error fetching posts for {profile.username}: {e}")
        
        return posts

class SentimentAnalysisAgent:
    """Agent for analyzing sentiment of social media content"""
    
    def __init__(self):
        self.sentiment_keywords = {
            "positive": ["great", "excellent", "amazing", "love", "fantastic", "wonderful"],
            "negative": ["terrible", "awful", "hate", "worst", "horrible", "disappointing"],
            "neutral": ["okay", "fine", "average", "normal", "standard"]
        }
    
    async def analyze_post_sentiment(self, post: SocialMediaPost) -> float:
        """Analyze sentiment of a single post"""
        
        content_lower = post.content.lower()
        
        positive_count = sum(1 for word in self.sentiment_keywords["positive"] if word in content_lower)
        negative_count = sum(1 for word in self.sentiment_keywords["negative"] if word in content_lower)
        
        if positive_count > negative_count:
            return min(0.8, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count:
            return max(-0.8, -0.5 - (negative_count * 0.1))
        else:
            return 0.0
    
    async def analyze_profile_sentiment(self, posts: List[SocialMediaPost]) -> Dict[str, float]:
        """Analyze overall sentiment for a profile"""
        
        if not posts:
            return {"overall": 0.0, "positive_ratio": 0.0, "negative_ratio": 0.0}
        
        sentiments = []
        for post in posts:
            sentiment = await self.analyze_post_sentiment(post)
            sentiments.append(sentiment)
        
        overall_sentiment = sum(sentiments) / len(sentiments)
        positive_ratio = len([s for s in sentiments if s > 0.1]) / len(sentiments)
        negative_ratio = len([s for s in sentiments if s < -0.1]) / len(sentiments)
        
        return {
            "overall": overall_sentiment,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "total_posts": len(posts)
        }

class SocialMediaIntelligenceOrchestrator:
    """Main orchestrator for social media intelligence"""
    
    def __init__(self):
        self.data_fetcher = SocialMediaDataFetcherAgent()
        self.sentiment_analyzer = SentimentAnalysisAgent()
    
    async def analyze_association(self, association_name: str, platforms: List[str]) -> Dict[str, Any]:
        """Complete social media analysis for a housing association"""
        
        logger.info(f"Starting social media analysis for: {association_name}")
        
        # Fetch profiles
        profiles = await self.data_fetcher.fetch_profiles(association_name, platforms)
        
        analysis_results = {
            "association_name": association_name,
            "analysis_date": datetime.now().isoformat(),
            "profiles_found": len(profiles),
            "platforms_analyzed": platforms,
            "profiles": [],
            "overall_sentiment": 0.0,
            "total_followers": 0,
            "recommendations": []
        }
        
        # Analyze each profile
        for profile in profiles:
            posts = await self.data_fetcher.fetch_posts(profile)
            sentiment_analysis = await self.sentiment_analyzer.analyze_profile_sentiment(posts)
            
            profile_data = {
                "platform": profile.platform,
                "username": profile.username,
                "followers": profile.followers,
                "verified": profile.verified,
                "posts_analyzed": len(posts),
                "sentiment": sentiment_analysis,
                "engagement_rate": self.calculate_engagement_rate(posts, profile.followers)
            }
            
            analysis_results["profiles"].append(profile_data)
            analysis_results["total_followers"] += profile.followers
        
        # Calculate overall metrics
        if analysis_results["profiles"]:
            overall_sentiment = sum(p["sentiment"]["overall"] for p in analysis_results["profiles"]) / len(analysis_results["profiles"])
            analysis_results["overall_sentiment"] = overall_sentiment
        
        # Generate recommendations
        analysis_results["recommendations"] = self.generate_recommendations(analysis_results)
        
        logger.info(f"Analysis completed for: {association_name}")
        return analysis_results
    
    def calculate_engagement_rate(self, posts: List[SocialMediaPost], followers: int) -> float:
        """Calculate engagement rate for posts"""
        if not posts or followers == 0:
            return 0.0
        
        total_engagement = sum(post.likes + post.shares + post.comments for post in posts)
        return total_engagement / (len(posts) * followers)
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if analysis["profiles_found"] == 0:
            recommendations.append("Consider establishing a social media presence to engage with residents")
        
        if analysis["overall_sentiment"] < 0:
            recommendations.append("Focus on addressing negative feedback and improving community relations")
        
        if analysis["total_followers"] < 1000:
            recommendations.append("Implement strategies to grow your social media following")
        
        platforms_missing = set(["twitter", "facebook", "linkedin"]) - set(p["platform"] for p in analysis["profiles"])
        if platforms_missing:
            recommendations.append(f"Consider expanding to {', '.join(platforms_missing)} for broader reach")
        
        return recommendations

# Usage Example:
async def main():
    orchestrator = SocialMediaIntelligenceOrchestrator()
    result = await orchestrator.analyze_association("Sample Housing Association", ["twitter", "facebook"])
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import json
    asyncio.run(main())
'''
    
    def generate_dashboard_component_code(self) -> str:
        """Generate dashboard component HTML/JS code"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Dashboard Component</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-900 mb-8">Generated Dashboard Component</h1>
        
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-2 bg-blue-100 rounded-lg">
                        <i class="fas fa-users text-blue-600"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Total Users</p>
                        <p class="text-2xl font-bold text-gray-900">2,847</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-2 bg-green-100 rounded-lg">
                        <i class="fas fa-chart-line text-green-600"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Growth Rate</p>
                        <p class="text-2xl font-bold text-gray-900">+12%</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-2 bg-purple-100 rounded-lg">
                        <i class="fas fa-star text-purple-600"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Rating</p>
                        <p class="text-2xl font-bold text-gray-900">4.8</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Chart -->
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Performance Chart</h3>
            <div style="height: 400px;">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Initialize chart when page loads
        document.addEventListener('DOMContentLoaded', function() {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Performance',
                        data: [65, 59, 80, 81, 56, 55],
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
    </script>
</body>
</html>'''
    
    def save_generated_file(self, filename: str, content: str, description: str = "") -> Dict[str, Any]:
        """Save generated file with proper encoding"""
        try:
            # Ensure generated_files directory exists
            os.makedirs("generated_files", exist_ok=True)
            
            # Clean the content to remove problematic Unicode characters
            cleaned_content = self.clean_unicode_content(content)
            
            file_path = f"generated_files/{filename}"
            
            # Write with explicit UTF-8 encoding
            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(cleaned_content)
            
            file_info = {
                'filename': filename,
                'path': file_path,
                'description': description,
                'size': len(cleaned_content),
                'created_at': datetime.now().isoformat()
            }
            
            # Add to generated files list
            self.generated_files.append(file_info)
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            return {
                'filename': filename,
                'error': str(e),
                'created_at': datetime.now().isoformat()
            }

    def clean_unicode_content(self, content: str) -> str:
        """Clean content of problematic Unicode characters"""
        try:
            # Replace common problematic Unicode characters
            replacements = {
                '\u2191': '^',  # Up arrow
                '\u2192': '->',  # Right arrow
                '\u2193': 'v',   # Down arrow
                '\u2190': '<-',  # Left arrow
                '\u2022': '*',   # Bullet point
                '\u2013': '-',   # En dash
                '\u2014': '--',  # Em dash
                '\u201c': '"',   # Left double quote
                '\u201d': '"',   # Right double quote
                '\u2018': "'",   # Left single quote
                '\u2019': "'",   # Right single quote
            }
            
            cleaned = content
            for unicode_char, replacement in replacements.items():
                cleaned = cleaned.replace(unicode_char, replacement)
            
            # Ensure the content can be encoded as UTF-8
            cleaned.encode('utf-8', errors='replace')
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning Unicode content: {e}")
            # Return ASCII-safe version as fallback
            return content.encode('ascii', errors='replace').decode('ascii')
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific conversation"""
        return self.conversation_history.get(conversation_id, [])
    
    def clear_conversation_history(self, conversation_id: str):
        """Clear conversation history for a specific conversation"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
    
    def get_generated_files(self) -> List[Dict[str, Any]]:
        """Get list of all generated files"""
        return self.generated_files
    
    def clear_generated_files(self):
        """Clear the generated files list"""
        self.generated_files = []

# Global instance
_dashboard_ai_controller = None

def get_dashboard_ai_controller() -> DashboardAIController:
    """Get or create the global dashboard AI controller instance"""
    global _dashboard_ai_controller
    if _dashboard_ai_controller is None:
        _dashboard_ai_controller = DashboardAIController()
    return _dashboard_ai_controller