"""
Conversational AI Intent Engine
Understands user requests and creates specialized agents dynamically
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
from config.industry_configs import IndustryType, IndustryConfigManager

logger = logging.getLogger(__name__)

class IntentType(Enum):
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    MONITORING = "monitoring"
    RESEARCH = "research"
    REPORTING = "reporting"
    PREDICTION = "prediction"
    OPTIMIZATION = "optimization"
    REGULATORY_DISCOVERY = "regulatory_discovery"  # NEW
    COMPLIANCE_ANALYSIS = "compliance_analysis"    # NEW
    DOCUMENT_SEARCH = "document_search"            # NEW

@dataclass
class UserIntent:
    intent_type: IntentType
    industry: Optional[str] = None
    region: Optional[str] = None
    specific_organizations: List[str] = None
    analysis_focus: List[str] = None
    time_frame: Optional[str] = None
    output_format: Optional[str] = None
    urgency: str = "normal"  # low, normal, high, critical
    custom_criteria: Dict[str, Any] = None
    confidence_score: float = 0.0

@dataclass
class AgentRecommendation:
    agent_type: str
    agent_config: Dict[str, Any]
    priority: int
    estimated_time: str
    description: str
    dependencies: List[str] = None

class ConversationalIntentEngine:
    """AI-powered intent understanding and agent recommendation system"""
    
    def __init__(self):
        self.vertex_ai = ProductionVertexAIAgent()
        self.config_manager = IndustryConfigManager()
        self.conversation_history: List[Dict] = []
        
        # Intent patterns for quick classification
        self.intent_patterns = {
            IntentType.DISCOVERY: [
                r"find|discover|search|locate|identify",
                r"who are|what are|list|show me",
                r"organizations|companies|associations|providers"
            ],
            IntentType.ANALYSIS: [
                r"analyze|analyse|assess|evaluate|examine",
                r"performance|quality|effectiveness|impact",
                r"how well|how good|strengths|weaknesses"
            ],
            IntentType.COMPARISON: [
                r"compare|versus|vs|against|benchmark",
                r"better|worse|best|worst|rank|ranking",
                r"differences|similarities|contrast"
            ],
            IntentType.MONITORING: [
                r"monitor|track|watch|observe|follow",
                r"changes|updates|progress|trends",
                r"real.?time|continuous|ongoing"
            ],
            IntentType.RESEARCH: [
                r"research|investigate|study|explore",
                r"market|sector|industry|trends",
                r"insights|intelligence|data|information"
            ],
            IntentType.REPORTING: [
                r"report|summary|overview|dashboard",
                r"export|download|generate|create",
                r"pdf|csv|excel|presentation"
            ],
            IntentType.PREDICTION: [
                r"predict|forecast|future|trends",
                r"will|might|could|expect|anticipate",
                r"growth|decline|changes|outlook"
            ],
            IntentType.REGULATORY_DISCOVERY: [
                r"regulatory|regulation|compliance|government|policy",
                r"find.*documents|discover.*documents|search.*documents",
                r"legislation|guidance|standards|requirements",
                r"authority|regulator|ministry|department"
            ],
            IntentType.COMPLIANCE_ANALYSIS: [
                r"compliance|comply|compliant|non.?compliant",
                r"requirements|obligations|duties|responsibilities",
                r"assess.*compliance|check.*compliance|review.*compliance",
                r"audit|inspection|evaluation"
            ],
            IntentType.DOCUMENT_SEARCH: [
                r"search.*document|find.*document|look.*document",
                r"policy.*document|guidance.*document|regulation.*document",
                r"specific.*document|particular.*document|certain.*document"
            ]
            IntentType.OPTIMIZATION: [
                r"optimize|improve|enhance|maximize",
                r"efficiency|performance|results",
                r"recommendations|suggestions|advice"
            ]
        }
        
        logger.info("Conversational Intent Engine initialized")

   async def _recommend_regulatory_discovery_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
    """Recommend regulatory discovery agents"""
    
    agents = []
    
    # Regulatory Document Discovery Agent
    agents.append(AgentRecommendation(
        agent_type="RegulatoryDocumentAgent",
        agent_config={
            'industry': intent.industry or 'general',
            'document_types': intent.analysis_focus or ['legislation', 'guidance', 'policy', 'standards'],
            'regions': [intent.region] if intent.region else ['uk'],
            'download_documents': intent.urgency in ['high', 'critical'],
            'download_limit': 100 if intent.urgency == 'critical' else 50,
            'keywords': intent.specific_organizations or []
        },
        priority=95,
        estimated_time="15-45 minutes",
        description="Discover and analyze regulatory documents from government sources"
    ))
    
    # Compliance Analysis Agent
    agents.append(AgentRecommendation(
        agent_type="ComplianceAnalysisAgent",
        agent_config={
            'analysis_depth': 'comprehensive' if intent.urgency == 'high' else 'standard',
            'focus_areas': intent.analysis_focus or ['mandatory_requirements', 'deadlines', 'penalties'],
            'industry_context': intent.industry
        },
        priority=85,
        estimated_time="20-60 minutes",
        description="Analyze compliance requirements and create action plans",
        dependencies=["RegulatoryDocumentAgent"]
    ))
    
    # Document Classification Agent
    agents.append(AgentRecommendation(
        agent_type="DocumentClassificationAgent",
        agent_config={
            'classification_types': ['urgency', 'compliance_impact', 'document_type'],
            'ai_enhanced': True
        },
        priority=75,
        estimated_time="10-30 minutes",
        description="Classify and prioritize regulatory documents",
        dependencies=["RegulatoryDocumentAgent"]
    ))
    
    return agents

async def _recommend_compliance_analysis_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
    """Recommend compliance analysis agents"""
    
    agents = []
    
    # Compliance Gap Analysis Agent
    agents.append(AgentRecommendation(
        agent_type="ComplianceGapAnalysisAgent",
        agent_config={
            'analysis_scope': intent.analysis_focus or ['current_state', 'required_state', 'gaps'],
            'industry': intent.industry,
            'urgency_level': intent.urgency
        },
        priority=90,
        estimated_time="30-90 minutes",
        description="Identify compliance gaps and create remediation plans"
    ))
    
    # Risk Assessment Agent
    agents.append(AgentRecommendation(
        agent_type="RiskAssessmentAgent",
        agent_config={
            'risk_types': ['compliance_risk', 'operational_risk', 'reputational_risk'],
            'assessment_depth': 'detailed' if intent.urgency == 'high' else 'standard'
        },
        priority=80,
        estimated_time="20-45 minutes",
        description="Assess compliance risks and impact"
    ))
    
    return agents

async def _recommend_document_search_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
    """Recommend document search agents"""
    
    agents = []
    
    # Document Search Agent
    agents.append(AgentRecommendation(
        agent_type="DocumentSearchAgent",
        agent_config={
            'search_terms': intent.specific_organizations or intent.analysis_focus,
            'search_scope': 'regulatory_database',
            'result_limit': 100,
            'include_content': True
        },
        priority=85,
        estimated_time="5-15 minutes",
        description="Search regulatory document database for specific documents"
    ))
    
    # Content Analysis Agent
    agents.append(AgentRecommendation(
        agent_type="ContentAnalysisAgent",
        agent_config={
            'analysis_type': 'regulatory_content',
            'extract_requirements': True,
            'identify_deadlines': True
        },
        priority=75,
        estimated_time="10-25 minutes",
        description="Analyze document content for key requirements and deadlines",
        dependencies=["DocumentSearchAgent"]
    ))
    
    return agents

# Update the recommend_agents method to include new intent types
async def recommend_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
    """
    Recommend specialized agents based on user intent
    """
    
    logger.info(f"Recommending agents for intent: {intent.intent_type.value}")
    
    recommendations = []
    
    # Existing recommendations...
    if intent.intent_type in [IntentType.DISCOVERY, IntentType.RESEARCH]:
        recommendations.extend(await self._recommend_discovery_agents(intent))
    
    if intent.intent_type in [IntentType.ANALYSIS, IntentType.COMPARISON]:
        recommendations.extend(await self._recommend_analysis_agents(intent))
    
    # ... other existing recommendations ...
    
    # NEW: Regulatory document recommendations
    if intent.intent_type == IntentType.REGULATORY_DISCOVERY:
        recommendations.extend(await self._recommend_regulatory_discovery_agents(intent))
    
    if intent.intent_type == IntentType.COMPLIANCE_ANALYSIS:
        recommendations.extend(await self._recommend_compliance_analysis_agents(intent))
    
    if intent.intent_type == IntentType.DOCUMENT_SEARCH:
        recommendations.extend(await self._recommend_document_search_agents(intent))
    
    # Sort by priority
    recommendations.sort(key=lambda x: x.priority, reverse=True)
    
    logger.info(f"Generated {len(recommendations)} agent recommendations")
    
    return recommendations

    async def understand_user_request(self, user_message: str, context: Dict = None) -> UserIntent:
        """
        Understand user intent from natural language message
        """
        
        logger.info(f"Processing user request: {user_message[:100]}...")
        
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'context': context or {}
        })
        
        # Quick pattern-based classification
        quick_intent = self._quick_intent_classification(user_message)
        
        # Use Vertex AI for detailed intent analysis
        detailed_intent = await self._ai_intent_analysis(user_message, context, quick_intent)
        
        logger.info(f"Identified intent: {detailed_intent.intent_type.value} (confidence: {detailed_intent.confidence_score:.2f})")
        
        return detailed_intent
    
    def _quick_intent_classification(self, message: str) -> Optional[IntentType]:
        """Quick pattern-based intent classification"""
        
        message_lower = message.lower()
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            
            if score > 0:
                intent_scores[intent_type] = score
        
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    async def _ai_intent_analysis(self, message: str, context: Dict, quick_intent: Optional[IntentType]) -> UserIntent:
        """Use Vertex AI for detailed intent analysis"""
        
        try:
            # Build context for AI analysis
            analysis_context = {
                'user_message': message,
                'quick_classification': quick_intent.value if quick_intent else None,
                'conversation_history': self.conversation_history[-5:],  # Last 5 messages
                'available_industries': [config.name for config in self.config_manager.get_all_configs().values()],
                'context': context or {}
            }
            
            # AI prompt for intent analysis
            prompt = f"""
            You are an expert AI assistant that understands user requests for business intelligence and data analysis.
            
            Analyze this user request and extract the following information:
            
            User Message: "{message}"
            
            Context: {json.dumps(analysis_context, indent=2)}
            
            Please provide a detailed analysis in JSON format with these fields:
            
            {{
                "intent_type": "one of: discovery, analysis, comparison, monitoring, research, reporting, prediction, optimization",
                "industry": "specific industry mentioned or null",
                "region": "geographic region mentioned or null", 
                "specific_organizations": ["list of specific organization names mentioned"],
                "analysis_focus": ["list of specific aspects to analyze"],
                "time_frame": "time period mentioned or null",
                "output_format": "preferred output format or null",
                "urgency": "low, normal, high, or critical",
                "custom_criteria": {{"any specific criteria or filters mentioned"}},
                "confidence_score": 0.95,
                "reasoning": "explanation of your analysis",
                "clarifying_questions": ["questions to ask user for more clarity"],
                "suggested_approach": "recommended approach to fulfill this request"
            }}
            
            Be thorough but concise. If something is unclear, include clarifying questions.
            """
            
            # Get AI analysis
            ai_response = await self.vertex_ai.generate_content_async(prompt)
            
            # Parse AI response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    ai_analysis = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in AI response")
                
                # Create UserIntent object
                intent = UserIntent(
                    intent_type=IntentType(ai_analysis.get('intent_type', 'discovery')),
                    industry=ai_analysis.get('industry'),
                    region=ai_analysis.get('region'),
                    specific_organizations=ai_analysis.get('specific_organizations', []),
                    analysis_focus=ai_analysis.get('analysis_focus', []),
                    time_frame=ai_analysis.get('time_frame'),
                    output_format=ai_analysis.get('output_format'),
                    urgency=ai_analysis.get('urgency', 'normal'),
                    custom_criteria=ai_analysis.get('custom_criteria', {}),
                    confidence_score=ai_analysis.get('confidence_score', 0.7)
                )
                
                # Store additional AI insights
                intent.ai_reasoning = ai_analysis.get('reasoning', '')
                intent.clarifying_questions = ai_analysis.get('clarifying_questions', [])
                intent.suggested_approach = ai_analysis.get('suggested_approach', '')
                
                return intent
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse AI intent analysis: {e}")
                # Fallback to quick classification
                return self._create_fallback_intent(message, quick_intent)
        
        except Exception as e:
            logger.error(f"AI intent analysis failed: {e}")
            return self._create_fallback_intent(message, quick_intent)
    
    def _create_fallback_intent(self, message: str, quick_intent: Optional[IntentType]) -> UserIntent:
        """Create fallback intent when AI analysis fails"""
        
        return UserIntent(
            intent_type=quick_intent or IntentType.DISCOVERY,
            confidence_score=0.5,
            custom_criteria={'original_message': message}
        )
    
    async def recommend_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """
        Recommend specialized agents based on user intent
        """
        
        logger.info(f"Recommending agents for intent: {intent.intent_type.value}")
        
        recommendations = []
        
        # Base agents for all intents
        if intent.intent_type in [IntentType.DISCOVERY, IntentType.RESEARCH]:
            recommendations.extend(await self._recommend_discovery_agents(intent))
        
        if intent.intent_type in [IntentType.ANALYSIS, IntentType.COMPARISON]:
            recommendations.extend(await self._recommend_analysis_agents(intent))
        
        if intent.intent_type == IntentType.MONITORING:
            recommendations.extend(await self._recommend_monitoring_agents(intent))
        
        if intent.intent_type == IntentType.REPORTING:
            recommendations.extend(await self._recommend_reporting_agents(intent))
        
        if intent.intent_type == IntentType.PREDICTION:
            recommendations.extend(await self._recommend_prediction_agents(intent))
        
        if intent.intent_type == IntentType.OPTIMIZATION:
            recommendations.extend(await self._recommend_optimization_agents(intent))
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Generated {len(recommendations)} agent recommendations")
        
        return recommendations
    
    async def _recommend_discovery_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """Recommend discovery agents"""
        
        agents = []
        
        # Universal Discovery Agent
        agents.append(AgentRecommendation(
            agent_type="UniversalDiscoveryAgent",
            agent_config={
                'industry_type': intent.industry,
                'region': intent.region or 'all',
                'custom_keywords': intent.analysis_focus,
                'limit': 500 if intent.urgency == 'high' else 1000
            },
            priority=90,
            estimated_time="5-15 minutes",
            description="Discover organizations across multiple data sources"
        ))
        
        # Companies House Agent (if UK focus)
        if not intent.region or 'uk' in intent.region.lower() or any(uk_region in (intent.region or '').lower() 
                                                                    for uk_region in ['england', 'scotland', 'wales', 'northern ireland']):
            agents.append(AgentRecommendation(
                agent_type="CompaniesHouseAgent",
                agent_config={
                    'search_terms': intent.specific_organizations or intent.analysis_focus,
                    'company_types': self._get_relevant_company_types(intent.industry)
                },
                priority=80,
                estimated_time="3-10 minutes",
                description="Search UK Companies House for detailed company information"
            ))
        
        # Industry-specific regulatory agents
        if intent.industry:
            regulatory_agent = self._get_regulatory_agent(intent.industry)
            if regulatory_agent:
                agents.append(regulatory_agent)
        
        return agents
    
    async def _recommend_analysis_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """Recommend analysis agents"""
        
        agents = []
        
        # AI Analysis Agent
        agents.append(AgentRecommendation(
            agent_type="AIAnalysisAgent",
            agent_config={
                'analysis_type': 'comprehensive',
                'focus_areas': intent.analysis_focus,
                'industry_context': intent.industry,
                'comparison_mode': intent.intent_type == IntentType.COMPARISON
            },
            priority=95,
            estimated_time="10-30 minutes",
            description="AI-powered comprehensive analysis and insights",
            dependencies=["UniversalDiscoveryAgent"]
        ))
        
        # Website Analysis Agent
        agents.append(AgentRecommendation(
            agent_type="WebsiteAnalysisAgent",
            agent_config={
                'deep_analysis': intent.urgency in ['high', 'critical'],
                'focus_areas': ['digital_maturity', 'user_experience', 'accessibility']
            },
            priority=70,
            estimated_time="15-45 minutes",
            description="Analyze websites for digital capabilities and user experience",
            dependencies=["UniversalDiscoveryAgent"]
        ))
        
        # Financial Analysis Agent (if relevant)
        if any(keyword in (intent.analysis_focus or []) for keyword in ['financial', 'revenue', 'income', 'funding']):
            agents.append(AgentRecommendation(
                agent_type="FinancialAnalysisAgent",
                agent_config={
                    'analysis_depth': 'detailed' if intent.urgency == 'high' else 'standard',
                    'metrics': ['revenue', 'growth', 'efficiency', 'sustainability']
                },
                priority=85,
                estimated_time="20-60 minutes",
                description="Analyze financial performance and sustainability",
                dependencies=["CompaniesHouseAgent"]
            ))
        
        return agents
    
    async def _recommend_monitoring_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """Recommend monitoring agents"""
        
        agents = []
        
        # Real-time Monitoring Agent
        agents.append(AgentRecommendation(
            agent_type="MonitoringAgent",
            agent_config={
                'monitoring_frequency': self._get_monitoring_frequency(intent.urgency),
                'alert_thresholds': intent.custom_criteria.get('thresholds', {}),
                'focus_areas': intent.analysis_focus
            },
            priority=90,
            estimated_time="Continuous",
            description="Real-time monitoring with alerts and notifications"
        ))
        
        # Change Detection Agent
        agents.append(AgentRecommendation(
            agent_type="ChangeDetectionAgent",
            agent_config={
                'sensitivity': 'high' if intent.urgency == 'critical' else 'medium',
                'change_types': ['status', 'performance', 'structure', 'digital_presence']
            },
            priority=75,
            estimated_time="Continuous",
            description="Detect and analyze changes in organizations"
        ))
        
        return agents
    
    async def _recommend_reporting_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """Recommend reporting agents"""
        
        agents = []
        
        # Report Generation Agent
        agents.append(AgentRecommendation(
            agent_type="ReportGenerationAgent",
            agent_config={
                'output_formats': [intent.output_format] if intent.output_format else ['pdf', 'html', 'csv'],
                'report_type': 'executive' if intent.urgency == 'high' else 'comprehensive',
                'include_visualizations': True
            },
            priority=85,
            estimated_time="5-15 minutes",
            description="Generate comprehensive reports and visualizations",
            dependencies=["AIAnalysisAgent"]
        ))
        
        # Dashboard Agent
        agents.append(AgentRecommendation(
            agent_type="DashboardAgent",
            agent_config={
                'dashboard_type': 'interactive',
                'update_frequency': 'real-time' if intent.intent_type == IntentType.MONITORING else 'daily'
            },
            priority=70,
            estimated_time="10-20 minutes",
            description="Create interactive dashboards and visualizations"
        ))
        
        return agents
    
    async def _recommend_prediction_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """Recommend prediction agents"""
        
        agents = []
        
        # Predictive Analytics Agent
        agents.append(AgentRecommendation(
            agent_type="PredictiveAnalyticsAgent",
            agent_config={
                'prediction_horizon': intent.time_frame or '12_months',
                'prediction_types': ['growth', 'performance', 'risk', 'opportunities'],
                'confidence_level': 0.95
            },
            priority=90,
            estimated_time="30-90 minutes",
            description="AI-powered predictive analytics and forecasting",
            dependencies=["AIAnalysisAgent"]
        ))
        
        # Trend Analysis Agent
        agents.append(AgentRecommendation(
            agent_type="TrendAnalysisAgent",
            agent_config={
                'trend_types': ['market', 'technology', 'regulatory', 'competitive'],
                'analysis_depth': 'deep' if intent.urgency == 'high' else 'standard'
            },
            priority=80,
            estimated_time="20-45 minutes",
            description="Identify and analyze market and industry trends"
        ))
        
        return agents
    
    async def _recommend_optimization_agents(self, intent: UserIntent) -> List[AgentRecommendation]:
        """Recommend optimization agents"""
        
        agents = []
        
        # Optimization Recommendation Agent
        agents.append(AgentRecommendation(
            agent_type="OptimizationAgent",
            agent_config={
                'optimization_areas': intent.analysis_focus or ['performance', 'efficiency', 'digital_maturity'],
                'recommendation_depth': 'detailed',
                'implementation_roadmap': True
            },
            priority=95,
            estimated_time="45-120 minutes",
            description="Generate optimization recommendations and implementation roadmaps",
            dependencies=["AIAnalysisAgent"]
        ))
        
        # Benchmarking Agent
        agents.append(AgentRecommendation(
            agent_type="BenchmarkingAgent",
            agent_config={
                'benchmark_type': 'industry_best_practice',
                'comparison_metrics': intent.analysis_focus or ['all']
            },
            priority=80,
            estimated_time="30-60 minutes",
            description="Benchmark against industry best practices and peers"
        ))
        
        return agents
    
    def _get_relevant_company_types(self, industry: str) -> List[str]:
        """Get relevant company types for an industry"""
        
        if not industry:
            return []
        
        # Get industry config
        config = self.config_manager.get_config_by_name(industry)
        if config:
            return config.company_types
        
        return []
    
    def _get_regulatory_agent(self, industry: str) -> Optional[AgentRecommendation]:
        """Get industry-specific regulatory agent"""
        
        regulatory_agents = {
            'housing_associations': AgentRecommendation(
                agent_type="HousingRegulatorAgent",
                agent_config={'regions': ['scotland', 'england']},
                priority=85,
                estimated_time="10-20 minutes",
                description="Extract data from housing regulators"
            ),
            'charities': AgentRecommendation(
                agent_type="CharityCommissionAgent",
                agent_config={'regions': ['england_wales', 'scotland', 'northern_ireland']},
                priority=85,
                estimated_time="10-20 minutes",
                description="Extract data from charity regulators"
            ),
            'care_homes': AgentRecommendation(
                agent_type="CareQualityAgent",
                agent_config={'include_ratings': True},
                priority=85,
                estimated_time="15-30 minutes",
                description="Extract care quality ratings and inspection data"
            )
        }
        
        return regulatory_agents.get(industry.lower().replace(' ', '_'))
    
    def _get_monitoring_frequency(self, urgency: str) -> str:
        """Get monitoring frequency based on urgency"""
        
        frequency_map = {
            'low': 'weekly',
            'normal': 'daily',
            'high': 'hourly',
            'critical': 'real_time'
        }
        
        return frequency_map.get(urgency, 'daily')
    
    async def generate_clarifying_questions(self, intent: UserIntent) -> List[str]:
        """Generate clarifying questions to better understand user needs"""
        
        questions = []
        
        # Industry clarification
        if not intent.industry:
            questions.append("Which industry or sector are you interested in? (e.g., housing associations, charities, healthcare)")
        
        # Region clarification
        if not intent.region:
            questions.append("Which geographic region should I focus on? (e.g., Scotland, England, specific cities)")
        
        # Scope clarification
        if not intent.analysis_focus:
            if intent.intent_type == IntentType.ANALYSIS:
                questions.append("What specific aspects would you like me to analyze? (e.g., digital maturity, financial performance, service quality)")
            elif intent.intent_type == IntentType.COMPARISON:
                questions.append("What criteria should I use for comparison? (e.g., size, performance, location)")
        
        # Output format clarification
        if intent.intent_type == IntentType.REPORTING and not intent.output_format:
            questions.append("What format would you prefer for the results? (e.g., PDF report, Excel spreadsheet, interactive dashboard)")
        
        # Time frame clarification
        if intent.intent_type in [IntentType.MONITORING, IntentType.PREDICTION] and not intent.time_frame:
            questions.append("What time frame are you interested in? (e.g., next 6 months, 1 year, ongoing monitoring)")
        
        # Use AI to generate additional contextual questions
        if hasattr(intent, 'clarifying_questions'):
            questions.extend(intent.clarifying_questions)
        
        return questions[:5]  # Limit to 5 questions to avoid overwhelming
    
    async def create_conversation_response(self, intent: UserIntent, recommendations: List[AgentRecommendation]) -> Dict[str, Any]:
        """Create a comprehensive response for the user"""
        
        # Generate clarifying questions
        clarifying_questions = await self.generate_clarifying_questions(intent)
        
        # Create response
        response = {
            'understood_intent': {
                'type': intent.intent_type.value,
                'industry': intent.industry,
                'region': intent.region,
                'confidence': intent.confidence_score,
                'summary': self._create_intent_summary(intent)
            },
            'recommended_approach': {
                'agents': [
                    {
                        'type': rec.agent_type,
                        'description': rec.description,
                        'estimated_time': rec.estimated_time,
                        'priority': rec.priority
                    } for rec in recommendations[:5]  # Top 5 recommendations
                ],
                'total_estimated_time': self._calculate_total_time(recommendations),
                'execution_order': self._determine_execution_order(recommendations)
            },
            'clarifying_questions': clarifying_questions,
            'next_steps': self._generate_next_steps(intent, recommendations),
            'can_proceed': len(clarifying_questions) <= 2  # Can proceed if minimal clarification needed
        }
        
        return response
    
    def _create_intent_summary(self, intent: UserIntent) -> str:
        """Create a human-readable summary of the understood intent"""
        
        summary_parts = []
        
        # Intent type
        intent_descriptions = {
            IntentType.DISCOVERY: "find and discover organizations",
            IntentType.ANALYSIS: "analyze and assess organizations",
            IntentType.COMPARISON: "compare organizations",
            IntentType.MONITORING: "monitor organizations over time",
            IntentType.RESEARCH: "research market and industry insights",
            IntentType.REPORTING: "generate reports and summaries",
            IntentType.PREDICTION: "predict future trends and outcomes",
            IntentType.OPTIMIZATION: "optimize and improve performance"
        }
        
        summary_parts.append(f"You want to {intent_descriptions.get(intent.intent_type, 'analyze')}")
        
        # Industry
        if intent.industry:
            summary_parts.append(f"in the {intent.industry} sector")
        
        # Region
        if intent.region:
            summary_parts.append(f"in {intent.region}")
        
        # Specific focus
        if intent.analysis_focus:
            focus_str = ", ".join(intent.analysis_focus[:3])
            summary_parts.append(f"focusing on {focus_str}")
        
        # Urgency
        if intent.urgency in ['high', 'critical']:
            summary_parts.append(f"with {intent.urgency} priority")
        
        return " ".join(summary_parts) + "."
    
    def _calculate_total_time(self, recommendations: List[AgentRecommendation]) -> str:
        """Calculate total estimated execution time"""
        
        # Simple estimation - this could be more sophisticated
        if len(recommendations) <= 2:
            return "15-45 minutes"
        elif len(recommendations) <= 4:
            return "45-90 minutes"
        else:
            return "1.5-3 hours"
    
    def _determine_execution_order(self, recommendations: List[AgentRecommendation]) -> List[str]:
        """Determine optimal execution order for agents"""
        
        # Sort by dependencies and priority
        ordered = []
        remaining = recommendations.copy()
        
        while remaining:
            # Find agents with no unmet dependencies
            ready = []
            for rec in remaining:
                if not rec.dependencies or all(dep in [r.agent_type for r in ordered] for dep in rec.dependencies):
                    ready.append(rec)
            
            if not ready:
                # Break circular dependencies by taking highest priority
                ready = [max(remaining, key=lambda x: x.priority)]
            
            # Sort ready agents by priority
            ready.sort(key=lambda x: x.priority, reverse=True)
            
            # Add to ordered list
            ordered.extend(ready)
            
            # Remove from remaining
            for rec in ready:
                remaining.remove(rec)
        
        return [rec.agent_type for rec in ordered]
    
    def _generate_next_steps(self, intent: UserIntent, recommendations: List[AgentRecommendation]) -> List[str]:
        """Generate next steps for the user"""
        
        steps = []
        
        if hasattr(intent, 'clarifying_questions') and intent.clarifying_questions:
            steps.append("Answer the clarifying questions to refine the analysis")
        
        steps.append("Review and approve the recommended approach")
        
        if intent.urgency in ['high', 'critical']:
            steps.append("Execute high-priority agents first for quick insights")
        else:
            steps.append("Execute the full agent pipeline for comprehensive results")
        
        steps.append("Review results and request additional analysis if needed")
        
        return steps

# Global intent engine instance
intent_engine = None

def get_intent_engine() -> ConversationalIntentEngine:
    """Get the global intent engine instance"""
    global intent_engine
    if intent_engine is None:
        intent_engine = ConversationalIntentEngine()
    return intent_engine