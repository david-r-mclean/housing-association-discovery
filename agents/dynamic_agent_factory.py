"""
Dynamic Agent Factory
Creates and configures specialized agents based on user intent
"""

import asyncio
import importlib
from typing import Dict, List, Any, Optional, Type
from datetime import datetime
import logging

from ai.intent_engine import AgentRecommendation, UserIntent
from vertex_agents.real_vertex_agent import ProductionVertexAIAgent

logger = logging.getLogger(__name__)

class RegulatoryDocumentAgent(DynamicAgent):
    """Regulatory document discovery agent"""
    
    async def _execute_specific(self) -> Dict[str, Any]:
        """Execute regulatory document discovery"""
        
        industry = self.config.get('industry', 'general')
        document_types = self.config.get('document_types', ['legislation', 'guidance', 'policy'])
        regions = self.config.get('regions', ['uk'])
        download_documents = self.config.get('download_documents', False)
        download_limit = self.config.get('download_limit', 50)
        keywords = self.config.get('keywords', [])
        
        logger.info(f"Starting regulatory document discovery for {industry}")
        
        try:
            # Import and use the regulatory agent
            from agents.regulatory_document_agent import get_regulatory_agent
            
            regulatory_agent = get_regulatory_agent()
            
            # Discover documents
            documents = await regulatory_agent.discover_regulatory_documents(
                industry=industry,
                document_types=document_types,
                regions=regions,
                keywords=keywords
            )
            
            # Download and process if requested
            processed_documents = documents
            if download_documents and documents:
                processed_documents = await regulatory_agent.download_and_process_documents(
                    documents, download_limit
                )
            
            # Save to database
            from database.regulatory_document_manager import get_regulatory_doc_manager
            doc_manager = get_regulatory_doc_manager()
            
            saved_count = 0
            for doc in processed_documents:
                try:
                    doc_manager.save_document(doc)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save document {doc.get('title', 'Unknown')}: {e}")
            
            # Generate summary
            summary = {
                'total_discovered': len(documents),
                'total_processed': len(processed_documents),
                'total_saved': saved_count,
                'by_document_type': {},
                'by_urgency': {},
                'high_priority_documents': []
            }
            
            # Analyze results
            for doc in processed_documents:
                doc_type = doc.get('document_type', 'unknown')
                summary['by_document_type'][doc_type] = summary['by_document_type'].get(doc_type, 0) + 1
                
                urgency = doc.get('urgency_level', 'medium')
                summary['by_urgency'][urgency] = summary['by_urgency'].get(urgency, 0) + 1
                
                if urgency == 'high' or doc.get('compliance_impact') == 'mandatory':
                    summary['high_priority_documents'].append({
                        'title': doc.get('title'),
                        'url': doc.get('url'),
                        'urgency_level': urgency,
                        'compliance_impact': doc.get('compliance_impact'),
                        'regulatory_authority': doc.get('regulatory_authority')
                    })
            
            return {
                'industry': industry,
                'discovery_summary': summary,
                'documents': processed_documents[:20],  # Return first 20 for display
                'total_documents': len(processed_documents),
                'execution_status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Regulatory document discovery failed: {e}")
            return {
                'industry': industry,
                'error': str(e),
                'execution_status': 'failed'
            }

class ComplianceAnalysisAgent(DynamicAgent):
    """Compliance analysis agent"""
    
    async def _execute_specific(self) -> Dict[str, Any]:
        """Execute compliance analysis"""
        
        analysis_depth = self.config.get('analysis_depth', 'standard')
        focus_areas = self.config.get('focus_areas', ['mandatory_requirements', 'deadlines'])
        industry_context = self.config.get('industry_context', 'general')
        
        logger.info(f"Starting compliance analysis for {industry_context}")
        
        try:
            # Get regulatory documents from database
            from database.regulatory_document_manager import get_regulatory_doc_manager
            doc_manager = get_regulatory_doc_manager()
            
            # Get high-priority and mandatory documents
            mandatory_docs = doc_manager.get_documents(compliance_impact='mandatory', limit=100)
            high_priority_docs = doc_manager.get_documents(urgency_level='high', limit=100)
            
            all_docs = mandatory_docs + high_priority_docs
            
            if not all_docs:
                return {
                    'error': 'No regulatory documents found for compliance analysis',
                    'recommendation': 'Run regulatory document discovery first'
                }
            
            # Analyze compliance requirements
            compliance_analysis = await self._analyze_compliance_requirements(all_docs, focus_areas, industry_context)
            
            # Generate compliance action plan
            action_plan = await self._generate_compliance_action_plan(compliance_analysis, analysis_depth)
            
            # Create compliance dashboard data
            dashboard_data = self._create_compliance_dashboard_data(all_docs, compliance_analysis)
            
            return {
                'industry_context': industry_context,
                'analysis_depth': analysis_depth,
                'documents_analyzed': len(all_docs),
                'compliance_analysis': compliance_analysis,
                'action_plan': action_plan,
                'dashboard_data': dashboard_data,
                'execution_status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return {
                'error': str(e),
                'execution_status': 'failed'
            }
    
    async def _analyze_compliance_requirements(self, documents: List[Dict], focus_areas: List[str], industry_context: str) -> Dict[str, Any]:
        """Analyze compliance requirements from documents"""
        
        # Create AI prompt for compliance analysis
        doc_summaries = []
        for doc in documents[:20]:  # Limit for AI processing
            doc_summaries.append({
                'title': doc.get('title', ''),
                'regulatory_authority': doc.get('regulatory_authority', ''),
                'compliance_impact': doc.get('compliance_impact', ''),
                'urgency_level': doc.get('urgency_level', ''),
                'ai_analysis': doc.get('ai_analysis', {})
            })
        
        analysis_prompt = f"""
        You are a compliance expert. Analyze these regulatory documents and provide comprehensive compliance insights.
        
        Industry Context: {industry_context}
        Focus Areas: {', '.join(focus_areas)}
        Documents to Analyze: {len(doc_summaries)}
        
        Document Summaries:
        {json.dumps(doc_summaries, indent=2)}
        
        Provide analysis in JSON format:
        
        {{
            "compliance_overview": {{
                "total_requirements": 25,
                "mandatory_requirements": 15,
                "recommended_requirements": 10,
                "immediate_action_required": 5,
                "compliance_complexity": "high|medium|low"
            }},
            "key_requirements": [
                {{
                    "requirement": "Description of requirement",
                    "source_document": "Document title",
                    "regulatory_authority": "Authority name",
                    "compliance_deadline": "Date or null",
                    "priority": "high|medium|low",
                    "implementation_effort": "high|medium|low",
                    "penalties": "Description of penalties"
                }}
            ],
            "compliance_themes": [
                {{
                    "theme": "Data Protection",
                    "requirement_count": 8,
                    "urgency": "high",
                    "description": "Requirements related to data protection"
                }}
            ],
            "regulatory_authorities": [
                {{
                    "authority": "Authority name",
                    "requirement_count": 12,
                    "key_focus_areas": ["area1", "area2"],
                    "contact_info": "Contact information if available"
                }}
            ],
            "compliance_timeline": [
                {{
                    "deadline": "2024-12-31",
                    "requirements": ["requirement1", "requirement2"],
                    "preparation_time": "3 months"
                }}
            ],
            "risk_assessment": {{
                "high_risk_areas": ["area1", "area2"],
                "compliance_gaps": ["gap1", "gap2"],
                "potential_penalties": ["penalty1", "penalty2"],
                "overall_risk_level": "high|medium|low"
            }}
        }}
        
        Focus on actionable insights and practical compliance steps.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(analysis_prompt)
            
            # Parse AI response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'raw_analysis': ai_response, 'parsing_error': 'Could not extract JSON'}
                
        except Exception as e:
            logger.error(f"Failed to analyze compliance requirements: {e}")
            return {'error': str(e)}
    
    async def _generate_compliance_action_plan(self, compliance_analysis: Dict, analysis_depth: str) -> Dict[str, Any]:
        """Generate compliance action plan"""
        
        action_plan_prompt = f"""
        Based on this compliance analysis, create a detailed action plan for implementation.
        
        Compliance Analysis:
        {json.dumps(compliance_analysis, indent=2)}
        
        Analysis Depth: {analysis_depth}
        
        Create an action plan in JSON format:
        
        {{
            "immediate_actions": [
                {{
                    "action": "Action description",
                    "priority": "critical|high|medium|low",
                    "deadline": "Date",
                    "responsible_party": "Who should do this",
                    "resources_required": ["resource1", "resource2"],
                    "estimated_effort": "hours or days",
                    "dependencies": ["dependency1", "dependency2"]
                }}
            ],
            "short_term_actions": [
                {{
                    "action": "Action description",
                    "timeline": "1-3 months",
                    "priority": "high|medium|low",
                    "success_criteria": "How to measure success"
                }}
            ],
            "long_term_actions": [
                {{
                    "action": "Action description",
                    "timeline": "3-12 months",
                    "strategic_importance": "high|medium|low",
                    "expected_outcome": "Expected result"
                }}
            ],
            "resource_requirements": {{
                "budget_estimate": "Estimated cost",
                "personnel_needed": ["role1", "role2"],
                "external_support": ["consultant", "legal advice"],
                "technology_requirements": ["system1", "system2"]
            }},
            "implementation_roadmap": [
                {{
                    "phase": "Phase 1: Assessment",
                    "duration": "2 weeks",
                    "activities": ["activity1", "activity2"],
                    "deliverables": ["deliverable1", "deliverable2"]
                }}
            ],
            "monitoring_plan": {{
                "key_metrics": ["metric1", "metric2"],
                "review_frequency": "monthly|quarterly",
                "reporting_requirements": ["report1", "report2"],
                "escalation_procedures": "When and how to escalate issues"
            }}
        }}
        
        Make the action plan specific, measurable, and achievable.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(action_plan_prompt)
            
            import json
            import re
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'raw_plan': ai_response, 'parsing_error': 'Could not extract JSON'}
                
        except Exception as e:
            logger.error(f"Failed to generate action plan: {e}")
            return {'error': str(e)}
    
    def _create_compliance_dashboard_data(self, documents: List[Dict], compliance_analysis: Dict) -> Dict[str, Any]:
        """Create data for compliance dashboard"""
        
        dashboard_data = {
            'summary_stats': {
                'total_documents': len(documents),
                'mandatory_documents': len([d for d in documents if d.get('compliance_impact') == 'mandatory']),
                'high_priority_documents': len([d for d in documents if d.get('urgency_level') == 'high']),
                'unique_authorities': len(set(d.get('regulatory_authority') for d in documents if d.get('regulatory_authority')))
            },
            'document_distribution': {
                'by_type': {},
                'by_authority': {},
                'by_urgency': {}
            },
            'compliance_status': {
                'compliant': 0,
                'partially_compliant': 0,
                'non_compliant': 0,
                'unknown': len(documents)  # Default all to unknown
            },
            'upcoming_deadlines': [],
            'high_risk_items': []
        }
        
        # Analyze document distribution
        for doc in documents:
            doc_type = doc.get('document_type', 'unknown')
            dashboard_data['document_distribution']['by_type'][doc_type] = \
                dashboard_data['document_distribution']['by_type'].get(doc_type, 0) + 1
            
            authority = doc.get('regulatory_authority', 'unknown')
            dashboard_data['document_distribution']['by_authority'][authority] = \
                dashboard_data['document_distribution']['by_authority'].get(authority, 0) + 1
            
            urgency = doc.get('urgency_level', 'medium')
            dashboard_data['document_distribution']['by_urgency'][urgency] = \
                dashboard_data['document_distribution']['by_urgency'].get(urgency, 0) + 1
        
        # Extract high-risk items from compliance analysis
        if 'risk_assessment' in compliance_analysis:
            risk_assessment = compliance_analysis['risk_assessment']
            dashboard_data['high_risk_items'] = risk_assessment.get('high_risk_areas', [])
        
        return dashboard_data

class DocumentSearchAgent(DynamicAgent):
    """Document search agent"""
    
    async def _execute_specific(self) -> Dict[str, Any]:
        """Execute document search"""
        
        search_terms = self.config.get('search_terms', [])
        search_scope = self.config.get('search_scope', 'regulatory_database')
        result_limit = self.config.get('result_limit', 50)
        include_content = self.config.get('include_content', False)
        
        if not search_terms:
            return {'error': 'No search terms provided'}
        
        logger.info(f"Searching for documents with terms: {search_terms}")
        
        try:
            from database.regulatory_document_manager import get_regulatory_doc_manager
            doc_manager = get_regulatory_doc_manager()
            
            all_results = []
            
            # Search for each term
            for term in search_terms:
                results = doc_manager.search_documents(term, result_limit)
                all_results.extend(results)
            
            # Remove duplicates
            unique_results = []
            seen_urls = set()
            
            for result in all_results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    
                    # Add full content if requested
                    if include_content:
                        content = doc_manager.get_document_content(result.get('id'))
                        if content:
                            result['text_content'] = content
                    
                    unique_results.append(result)
            
            # Sort by relevance and importance
            unique_results.sort(
                key=lambda x: (x.get('importance_score', 0), x.get('relevance_score', 0)), 
                reverse=True
            )
            
            # Limit results
            final_results = unique_results[:result_limit]
            
            return {
                'search_terms': search_terms,
                'total_results': len(final_results),
                'results': final_results,
                'search_summary': {
                    'by_document_type': {},
                    'by_authority': {},
                    'by_urgency': {}
                }
            }
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return {
                'error': str(e),
                'search_terms': search_terms
            }

# Update the DynamicAgentFactory to include new agent classes
def __init__(self):
    self.vertex_ai = ProductionVertexAIAgent()
    self.agent_classes = {
        'AIAnalysisAgent': AIAnalysisAgent,
        'WebsiteAnalysisAgent': WebsiteAnalysisAgent,
        'RegulatoryDocumentAgent': RegulatoryDocumentAgent,        # NEW
        'ComplianceAnalysisAgent': ComplianceAnalysisAgent,        # NEW
        'DocumentSearchAgent': DocumentSearchAgent,               # NEW
        # Add more agent classes as needed
    }
    
    logger.info("Dynamic Agent Factory initialized")

class DynamicAgent:
    """Base class for dynamically created agents"""
    
    def __init__(self, agent_type: str, config: Dict[str, Any], vertex_ai: ProductionVertexAIAgent):
        self.agent_type = agent_type
        self.config = config
        self.vertex_ai = vertex_ai
        self.results: Dict[str, Any] = {}
        self.status = "initialized"
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        logger.info(f"Created dynamic agent: {agent_type}")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the agent's main functionality"""
        
        self.status = "running"
        self.started_at = datetime.now()
        
        try:
            logger.info(f"Executing {self.agent_type} agent")
            
            # Call the specific agent implementation
            results = await self._execute_specific()
            
            self.results = results
            self.status = "completed"
            self.completed_at = datetime.now()
            
            execution_time = (self.completed_at - self.started_at).total_seconds()
            logger.info(f"{self.agent_type} completed in {execution_time:.2f} seconds")
            
            return {
                'agent_type': self.agent_type,
                'status': self.status,
                'results': results,
                'execution_time': execution_time,
                'metadata': {
                    'created_at': self.created_at.isoformat(),
                    'started_at': self.started_at.isoformat(),
                    'completed_at': self.completed_at.isoformat()
                }
            }
            
        except Exception as e:
            self.status = "failed"
            self.completed_at = datetime.now()
            
            logger.error(f"{self.agent_type} failed: {e}")
            
            return {
                'agent_type': self.agent_type,
                'status': self.status,
                'error': str(e),
                'metadata': {
                    'created_at': self.created_at.isoformat(),
                    'started_at': self.started_at.isoformat() if self.started_at else None,
                    'completed_at': self.completed_at.isoformat()
                }
            }
    
    async def _execute_specific(self) -> Dict[str, Any]:
        """Override this method in specific agent implementations"""
        raise NotImplementedError("Subclasses must implement _execute_specific")

class AIAnalysisAgent(DynamicAgent):
    """AI-powered analysis agent"""
    
    async def _execute_specific(self) -> Dict[str, Any]:
        """Execute AI analysis"""
        
        analysis_type = self.config.get('analysis_type', 'comprehensive')
        focus_areas = self.config.get('focus_areas', [])
        industry_context = self.config.get('industry_context')
        comparison_mode = self.config.get('comparison_mode', False)
        
        # Get organizations to analyze (from previous agents or database)
        organizations = await self._get_organizations_for_analysis()
        
        if not organizations:
            return {'error': 'No organizations found for analysis'}
        
        logger.info(f"Analyzing {len(organizations)} organizations with AI")
        
        analyzed_organizations = []
        
        for org in organizations:
            try:
                # Create analysis prompt based on configuration
                analysis_prompt = self._create_analysis_prompt(org, analysis_type, focus_areas, industry_context, comparison_mode)
                
                # Get AI analysis
                ai_response = await self.vertex_ai.generate_content_async(analysis_prompt)
                
                # Parse and structure the response
                structured_analysis = await self._parse_ai_analysis(ai_response, focus_areas)
                
                # Add to organization data
                org['ai_analysis'] = structured_analysis
                org['ai_analysis_timestamp'] = datetime.now().isoformat()
                org['analysis_type'] = analysis_type
                
                analyzed_organizations.append(org)
                
                # Respectful delay
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Failed to analyze organization {org.get('name', 'Unknown')}: {e}")
                continue
        
        # Generate summary insights
        summary_insights = await self._generate_summary_insights(analyzed_organizations, focus_areas, comparison_mode)
        
        return {
            'analyzed_organizations': analyzed_organizations,
            'total_analyzed': len(analyzed_organizations),
            'analysis_type': analysis_type,
            'focus_areas': focus_areas,
            'summary_insights': summary_insights,
            'comparison_mode': comparison_mode
        }
    
    def _create_analysis_prompt(self, org: Dict, analysis_type: str, focus_areas: List[str], industry_context: str, comparison_mode: bool) -> str:
        """Create AI analysis prompt"""
        
        base_prompt = f"""
        You are an expert business analyst specializing in {industry_context or 'organizational'} analysis.
        
        Analyze this organization comprehensively:
        
        Organization Data:
        {json.dumps(org, indent=2, default=str)}
        
        Analysis Requirements:
        - Analysis Type: {analysis_type}
        - Focus Areas: {', '.join(focus_areas) if focus_areas else 'All aspects'}
        - Industry Context: {industry_context or 'General'}
        - Comparison Mode: {'Yes' if comparison_mode else 'No'}
        
        Please provide a detailed analysis in JSON format with these sections:
        
        {{
            "organization_overview": {{
                "name": "organization name",
                "key_characteristics": ["list of key characteristics"],
                "primary_strengths": ["list of strengths"],
                "areas_for_improvement": ["list of improvement areas"]
            }},
            "performance_analysis": {{
                "overall_score": 0.85,
                "performance_indicators": {{
                    "digital_maturity": 0.75,
                    "operational_efficiency": 0.80,
                    "service_quality": 0.90,
                    "innovation_readiness": 0.70
                }},
                "benchmarking": {{
                    "industry_percentile": 75,
                    "peer_comparison": "above_average"
                }}
            }},
            "strategic_insights": {{
                "competitive_advantages": ["list of advantages"],
                "market_position": "description of market position",
                "growth_opportunities": ["list of opportunities"],
                "risk_factors": ["list of risks"]
            }},
            "recommendations": {{
                "immediate_actions": ["list of immediate recommendations"],
                "medium_term_goals": ["list of medium-term recommendations"],
                "long_term_strategy": ["list of long-term recommendations"],
                "investment_priorities": ["list of investment priorities"]
            }},
            "confidence_metrics": {{
                "analysis_confidence": 0.90,
                "data_quality_score": 0.85,
                "recommendation_confidence": 0.80
            }}
        }}
        
        Focus particularly on: {', '.join(focus_areas) if focus_areas else 'comprehensive analysis across all dimensions'}.
        
        Be specific, actionable, and evidence-based in your analysis.
        """
        
        return base_prompt
    
    async def _parse_ai_analysis(self, ai_response: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Parse and structure AI analysis response"""
        
        try:
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {
                    'raw_analysis': ai_response,
                    'focus_areas': focus_areas,
                    'parsing_error': 'Could not extract structured JSON'
                }
                
        except Exception as e:
            logger.error(f"Failed to parse AI analysis: {e}")
            return {
                'raw_analysis': ai_response,
                'parsing_error': str(e)
            }
    
    async def _get_organizations_for_analysis(self) -> List[Dict]:
        """Get organizations for analysis from various sources"""
        
        # Try to get from database first
        try:
            from database.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Get recent organizations
            associations = db_manager.get_recent_associations(limit=100)
            
            if associations:
                return [db_manager.association_to_dict(assoc) for assoc in associations]
            
        except Exception as e:
            logger.warning(f"Could not get organizations from database: {e}")
        
        # Fallback to sample data or empty list
        return []
    
    async def _generate_summary_insights(self, organizations: List[Dict], focus_areas: List[str], comparison_mode: bool) -> Dict[str, Any]:
        """Generate summary insights across all analyzed organizations"""
        
        if not organizations:
            return {}
        
        try:
            # Create summary prompt
            summary_prompt = f"""
            You are an expert market analyst. Analyze these {len(organizations)} organizations and provide market-level insights.
            
            Organizations analyzed: {len(organizations)}
            Focus areas: {', '.join(focus_areas) if focus_areas else 'All aspects'}
            Comparison mode: {'Yes' if comparison_mode else 'No'}
            
            Based on the individual analyses, provide market-level insights in JSON format:
            
            {{
                "market_overview": {{
                    "total_organizations": {len(organizations)},
                    "market_maturity": "emerging/developing/mature",
                    "competitive_landscape": "description",
                    "key_trends": ["list of trends"]
                }},
                "performance_benchmarks": {{
                    "average_digital_maturity": 0.75,
                    "top_performers": ["list of top performers"],
                    "improvement_needed": ["list of organizations needing improvement"],
                    "industry_leaders": ["list of leaders"]
                }},
                "strategic_recommendations": {{
                    "market_opportunities": ["list of opportunities"],
                    "investment_areas": ["list of investment areas"],
                    "collaboration_potential": ["list of collaboration opportunities"],
                    "policy_recommendations": ["list of policy recommendations"]
                }},
                "future_outlook": {{
                    "growth_potential": "high/medium/low",
                    "key_challenges": ["list of challenges"],
                    "success_factors": ["list of success factors"],
                    "timeline_for_change": "description"
                }}
            }}
            """
            
            # Get AI summary
            summary_response = await self.vertex_ai.generate_content_async(summary_prompt)
            
            # Parse summary
            import json
            import re
            
            json_match = re.search(r'\{.*\}', summary_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'raw_summary': summary_response}
                
        except Exception as e:
            logger.error(f"Failed to generate summary insights: {e}")
            return {'error': str(e)}

class WebsiteAnalysisAgent(DynamicAgent):
    """Website analysis agent"""
    
    async def _execute_specific(self) -> Dict[str, Any]:
        """Execute website analysis"""
        
        deep_analysis = self.config.get('deep_analysis', False)
        focus_areas = self.config.get('focus_areas', ['digital_maturity', 'user_experience'])
        
        # Get organizations with websites
        organizations = await self._get_organizations_with_websites()
        
        if not organizations:
            return {'error': 'No organizations with websites found'}
        
        logger.info(f"Analyzing websites for {len(organizations)} organizations")
        
        analyzed_websites = []
        
        for org in organizations:
            try:
                website_url = org.get('website') or org.get('official_website')
                if not website_url:
                    continue
                
                # Analyze website with AI
                website_analysis = await self._analyze_website_with_ai(website_url, org, focus_areas, deep_analysis)
                
                org['website_analysis'] = website_analysis
                org['website_analysis_timestamp'] = datetime.now().isoformat()
                
                analyzed_websites.append(org)
                
                # Respectful delay
                await asyncio.sleep(2.0)
                
            except Exception as e:
                logger.error(f"Failed to analyze website for {org.get('name', 'Unknown')}: {e}")
                continue
        
        return {
            'analyzed_websites': analyzed_websites,
            'total_analyzed': len(analyzed_websites),
            'focus_areas': focus_areas,
            'deep_analysis': deep_analysis
        }
    
    async def _analyze_website_with_ai(self, website_url: str, org: Dict, focus_areas: List[str], deep_analysis: bool) -> Dict[str, Any]:
        """Analyze website using AI"""
        
        # First, get basic website data
        try:
            from agents.enrichment_agent import WebsiteEnrichmentAgent
            
            enrichment_agent = WebsiteEnrichmentAgent()
            website_data = enrichment_agent.analyze_website(website_url)
            
        except Exception as e:
            logger.warning(f"Could not get basic website data: {e}")
            website_data = {'url': website_url, 'error': str(e)}
        
        # Create AI analysis prompt
        analysis_prompt = f"""
        You are a digital experience expert. Analyze this website comprehensively.
        
        Website URL: {website_url}
        Organization: {org.get('name', 'Unknown')}
        Industry: {org.get('industry_type', 'Unknown')}
        
        Basic Website Data:
        {json.dumps(website_data, indent=2, default=str)}
        
        Analysis Focus: {', '.join(focus_areas)}
        Deep Analysis: {'Yes' if deep_analysis else 'No'}
        
        Provide a comprehensive website analysis in JSON format:
        
        {{
            "digital_maturity": {{
                "overall_score": 0.85,
                "modern_design": 0.80,
                "mobile_responsiveness": 0.90,
                "loading_speed": 0.75,
                "accessibility": 0.70,
                "seo_optimization": 0.80
            }},
            "user_experience": {{
                "navigation_quality": 0.85,
                "content_quality": 0.80,
                "visual_appeal": 0.75,
                "functionality": 0.90,
                "user_journey": 0.80
            }},
            "digital_services": {{
                "online_services": ["list of services"],
                "digital_tools": ["list of tools"],
                "integration_level": 0.70,
                "service_completeness": 0.75
            }},
            "content_analysis": {{
                "content_freshness": 0.80,
                "information_completeness": 0.85,
                "engagement_features": ["list of features"],
                "communication_effectiveness": 0.75
            }},
            "technical_assessment": {{
                "security_features": ["list of security features"],
                "performance_metrics": {{"load_time": "2.3s", "mobile_score": 85}},
                "technology_stack": ["list of technologies"],
                "maintenance_quality": 0.80
            }},
            "competitive_analysis": {{
                "industry_comparison": "above_average",
                "unique_features": ["list of unique features"],
                "improvement_opportunities": ["list of opportunities"]
            }},
            "recommendations": {{
                "immediate_improvements": ["list of immediate improvements"],
                "strategic_enhancements": ["list of strategic enhancements"],
                "investment_priorities": ["list of priorities"]
            }}
        }}
        
        Be specific and actionable in your recommendations.
        """
        
        try:
            # Get AI analysis
            ai_response = await self.vertex_ai.generate_content_async(analysis_prompt)
            
            # Parse response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                analysis['basic_data'] = website_data
                return analysis
            else:
                return {
                    'basic_data': website_data,
                    'ai_analysis': ai_response,
                    'parsing_error': 'Could not extract structured analysis'
                }
                
        except Exception as e:
            logger.error(f"AI website analysis failed: {e}")
            return {
                'basic_data': website_data,
                'error': str(e)
            }
    
    async def _get_organizations_with_websites(self) -> List[Dict]:
        """Get organizations that have websites"""
        
        try:
            from database.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            associations = db_manager.get_recent_associations(limit=50)
            
            # Filter for organizations with websites
            with_websites = []
            for assoc in associations:
                assoc_dict = db_manager.association_to_dict(assoc)
                if assoc_dict.get('website') or assoc_dict.get('official_website'):
                    with_websites.append(assoc_dict)
            
            return with_websites
            
        except Exception as e:
            logger.error(f"Could not get organizations with websites: {e}")
            return []

class DynamicAgentFactory:
    """Factory for creating and managing dynamic agents"""
    
    def __init__(self):
        self.vertex_ai = ProductionVertexAIAgent()
        self.agent_classes = {
            'AIAnalysisAgent': AIAnalysisAgent,
            'WebsiteAnalysisAgent': WebsiteAnalysisAgent,
            # Add more agent classes as needed
        }
        
        logger.info("Dynamic Agent Factory initialized")
    
    async def create_agent(self, recommendation: AgentRecommendation) -> DynamicAgent:
        """Create an agent based on recommendation"""
        
        agent_type = recommendation.agent_type
        
        # Get agent class
        agent_class = self.agent_classes.get(agent_type)
        
        if not agent_class:
            # Create generic agent for unknown types
            agent_class = self._create_generic_agent_class(agent_type)
        
        # Create agent instance
        agent = agent_class(agent_type, recommendation.agent_config, self.vertex_ai)
        
        logger.info(f"Created agent: {agent_type}")
        
        return agent
    
    def _create_generic_agent_class(self, agent_type: str) -> Type[DynamicAgent]:
        """Create a generic agent class for unknown agent types"""
        
        class GenericAgent(DynamicAgent):
            async def _execute_specific(self) -> Dict[str, Any]:
                """Generic agent execution"""
                
                logger.info(f"Executing generic agent: {self.agent_type}")
                
                # Create AI prompt for generic analysis
                prompt = f"""
                You are a specialized {agent_type} agent. Based on the configuration provided, 
                perform the requested analysis or task.
                
                Agent Type: {self.agent_type}
                Configuration: {json.dumps(self.config, indent=2)}
                
                Please provide results in JSON format with relevant insights and recommendations.
                """
                
                try:
                    # Get AI response
                    ai_response = await self.vertex_ai.generate_content_async(prompt)
                    
                    return {
                        'agent_type': self.agent_type,
                        'ai_response': ai_response,
                        'config_used': self.config,
                        'execution_method': 'generic_ai_analysis'
                    }
                    
                except Exception as e:
                    return {
                        'agent_type': self.agent_type,
                        'error': str(e),
                        'config_used': self.config
                    }
        
        return GenericAgent
    
    async def execute_agent_pipeline(self, recommendations: List[AgentRecommendation], execution_order: List[str]) -> Dict[str, Any]:
        """Execute a pipeline of agents in the specified order"""
        
        logger.info(f"Executing agent pipeline with {len(recommendations)} agents")
        
        results = {}
        execution_log = []
        
        # Create agents
        agents = {}
        for rec in recommendations:
            agent = await self.create_agent(rec)
            agents[rec.agent_type] = agent
        
        # Execute in order
        for agent_type in execution_order:
            if agent_type in agents:
                try:
                    logger.info(f"Executing agent: {agent_type}")
                    
                    start_time = datetime.now()
                    result = await agents[agent_type].execute()
                    end_time = datetime.now()
                    
                    results[agent_type] = result
                    execution_log.append({
                        'agent_type': agent_type,
                        'status': result.get('status'),
                        'execution_time': (end_time - start_time).total_seconds(),
                        'timestamp': end_time.isoformat()
                    })
                    
                    logger.info(f"Agent {agent_type} completed with status: {result.get('status')}")
                    
                except Exception as e:
                    logger.error(f"Agent {agent_type} failed: {e}")
                    
                    results[agent_type] = {
                        'agent_type': agent_type,
                        'status': 'failed',
                        'error': str(e)
                    }
                    
                    execution_log.append({
                        'agent_type': agent_type,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Generate pipeline summary
        pipeline_summary = {
            'total_agents': len(recommendations),
            'executed_agents': len(execution_log),
            'successful_agents': len([log for log in execution_log if log.get('status') == 'completed']),
            'failed_agents': len([log for log in execution_log if log.get('status') == 'failed']),
            'total_execution_time': sum(log.get('execution_time', 0) for log in execution_log),
            'execution_order': execution_order,
            'execution_log': execution_log
        }
        
        return {
            'pipeline_summary': pipeline_summary,
            'agent_results': results,
            'execution_timestamp': datetime.now().isoformat()
        }

# Global factory instance
agent_factory = None

def get_agent_factory() -> DynamicAgentFactory:
    """Get the global agent factory instance"""
    global agent_factory
    if agent_factory is None:
        agent_factory = DynamicAgentFactory()
    return agent_factory

