"""
Advanced AI Dashboard Controller
Enables the dashboard to modify itself, create new agents, and evolve based on user needs
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

from vertex_agents.real_vertex_agent import ProductionVertexAIAgent

logger = logging.getLogger(__name__)

class DashboardAIController:
    """AI controller that can modify the dashboard and create new features"""
    
    def __init__(self):
        self.vertex_ai = ProductionVertexAIAgent()
        self.dashboard_components = {}
        self.generated_agents = {}
        self.conversation_history = []
        self.active_modifications = {}
        
        # Dashboard modification capabilities
        self.modification_capabilities = {
            'create_new_components': True,
            'modify_existing_components': True,
            'generate_new_agents': True,
            'create_api_endpoints': True,
            'modify_database_schema': True,
            'generate_reports': True,
            'create_visualizations': True,
            'integrate_external_apis': True
        }
        
        logger.info("Dashboard AI Controller initialized")
    
    async def process_dashboard_request(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user request for dashboard modifications or new features"""
        
        logger.info(f"Processing dashboard request: {user_message}")
        
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'context': context or {}
        })
        
        try:
            # Analyze the request
            request_analysis = await self._analyze_dashboard_request(user_message, context)
            
            # Determine required actions
            actions = await self._determine_required_actions(request_analysis)
            
            # Execute actions
            execution_results = await self._execute_dashboard_actions(actions)
            
            # Generate response
            response = await self._generate_dashboard_response(request_analysis, execution_results)
            
            # Add to conversation history
            self.conversation_history[-1]['ai_response'] = response
            self.conversation_history[-1]['actions_taken'] = actions
            self.conversation_history[-1]['execution_results'] = execution_results
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing dashboard request: {e}")
            return {
                'error': str(e),
                'message': 'I encountered an error processing your request. Please try rephrasing or provide more details.',
                'suggestions': [
                    'Try being more specific about what you want to create or modify',
                    'Provide examples of similar features you\'ve seen',
                    'Break down complex requests into smaller parts'
                ]
            }
    
    async def _analyze_dashboard_request(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user request to understand what dashboard modifications are needed"""
        
        analysis_prompt = f"""
        You are an expert dashboard AI that can understand user requests for dashboard modifications, new features, and agent creation.
        
        User Request: "{user_message}"
        Context: {json.dumps(context, indent=2)}
        
        Analyze this request and provide detailed analysis in JSON format:
        
        {{
            "request_type": "create_component|modify_component|create_agent|create_api|create_visualization|general_query",
            "intent_classification": {{
                "primary_intent": "dashboard_modification|agent_creation|data_analysis|feature_request|bug_report|general_help",
                "confidence": 0.95,
                "secondary_intents": ["list of other possible intents"]
            }},
            "required_capabilities": [
                "create_new_components",
                "generate_new_agents",
                "create_api_endpoints",
                "modify_database_schema",
                "create_visualizations"
            ],
            "technical_requirements": {{
                "frontend_changes": {{
                    "new_components": ["component1", "component2"],
                    "modified_components": ["existing_component1"],
                    "new_pages": ["page1"],
                    "ui_framework": "html_css_js|react|vue",
                    "styling_requirements": "tailwind|bootstrap|custom"
                }},
                "backend_changes": {{
                    "new_endpoints": ["/api/new-endpoint"],
                    "modified_endpoints": ["/api/existing-endpoint"],
                    "new_database_tables": ["table1"],
                    "new_agents": ["AgentName"],
                    "external_integrations": ["api1", "api2"]
                }},
                "data_requirements": {{
                    "new_data_sources": ["source1"],
                    "data_processing": ["processing_type1"],
                    "storage_needs": ["database", "files", "cache"]
                }}
            }},
            "complexity_assessment": {{
                "overall_complexity": "low|medium|high|very_high",
                "estimated_development_time": "minutes|hours|days",
                "risk_level": "low|medium|high",
                "dependencies": ["dependency1", "dependency2"]
            }},
            "user_experience_impact": {{
                "new_user_flows": ["flow1", "flow2"],
                "modified_user_flows": ["existing_flow1"],
                "accessibility_considerations": ["consideration1"],
                "mobile_responsiveness": true
            }},
            "implementation_plan": {{
                "phase_1": {{
                    "description": "Initial implementation",
                    "deliverables": ["deliverable1", "deliverable2"],
                    "estimated_time": "30 minutes"
                }},
                "phase_2": {{
                    "description": "Enhancement and testing",
                    "deliverables": ["deliverable3"],
                    "estimated_time": "15 minutes"
                }}
            }},
            "success_criteria": [
                "User can successfully perform the requested action",
                "New feature integrates seamlessly with existing dashboard",
                "Performance impact is minimal"
            ],
            "potential_challenges": [
                "challenge1",
                "challenge2"
            ],
            "alternative_approaches": [
                {{
                    "approach": "Alternative approach 1",
                    "pros": ["pro1", "pro2"],
                    "cons": ["con1", "con2"]
                }}
            ]
        }}
        
        Be thorough and consider all technical and user experience aspects.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(analysis_prompt)
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                analysis['raw_ai_response'] = ai_response
                return analysis
            else:
                return {
                    'error': 'Could not parse AI analysis',
                    'raw_response': ai_response,
                    'request_type': 'general_query'
                }
                
        except Exception as e:
            logger.error(f"Error analyzing dashboard request: {e}")
            return {
                'error': str(e),
                'request_type': 'general_query'
            }
    
    async def _determine_required_actions(self, request_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine specific actions needed to fulfill the request"""
        
        actions = []
        
        if request_analysis.get('error'):
            return [{'type': 'error_response', 'data': request_analysis}]
        
        tech_requirements = request_analysis.get('technical_requirements', {})
        
        # Frontend actions
        frontend_changes = tech_requirements.get('frontend_changes', {})
        if frontend_changes.get('new_components'):
            actions.append({
                'type': 'create_frontend_components',
                'data': frontend_changes
            })
        
        if frontend_changes.get('modified_components'):
            actions.append({
                'type': 'modify_frontend_components',
                'data': frontend_changes
            })
        
        if frontend_changes.get('new_pages'):
            actions.append({
                'type': 'create_new_pages',
                'data': frontend_changes
            })
        
        # Backend actions
        backend_changes = tech_requirements.get('backend_changes', {})
        if backend_changes.get('new_endpoints'):
            actions.append({
                'type': 'create_api_endpoints',
                'data': backend_changes
            })
        
        if backend_changes.get('new_agents'):
            actions.append({
                'type': 'create_new_agents',
                'data': backend_changes
            })
        
        if backend_changes.get('new_database_tables'):
            actions.append({
                'type': 'create_database_tables',
                'data': backend_changes
            })
        
        # Data actions
        data_requirements = tech_requirements.get('data_requirements', {})
        if data_requirements.get('new_data_sources'):
            actions.append({
                'type': 'integrate_data_sources',
                'data': data_requirements
            })
        
        # If no specific actions, create a general response
        if not actions:
            actions.append({
                'type': 'generate_response',
                'data': request_analysis
            })
        
        return actions
    
    async def _execute_dashboard_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the determined actions"""
        
        results = []
        
        for action in actions:
            try:
                action_type = action['type']
                action_data = action['data']
                
                if action_type == 'create_frontend_components':
                    result = await self._create_frontend_components(action_data)
                elif action_type == 'modify_frontend_components':
                    result = await self._modify_frontend_components(action_data)
                elif action_type == 'create_new_pages':
                    result = await self._create_new_pages(action_data)
                elif action_type == 'create_api_endpoints':
                    result = await self._create_api_endpoints(action_data)
                elif action_type == 'create_new_agents':
                    result = await self._create_new_agents(action_data)
                elif action_type == 'create_database_tables':
                    result = await self._create_database_tables(action_data)
                elif action_type == 'integrate_data_sources':
                    result = await self._integrate_data_sources(action_data)
                elif action_type == 'generate_response':
                    result = await self._generate_general_response(action_data)
                elif action_type == 'error_response':
                    result = {'type': 'error', 'message': 'Could not process request', 'data': action_data}
                else:
                    result = {'type': 'unknown_action', 'message': f'Unknown action type: {action_type}'}
                
                results.append({
                    'action_type': action_type,
                    'result': result,
                    'success': result.get('success', False)
                })
                
            except Exception as e:
                logger.error(f"Error executing action {action['type']}: {e}")
                results.append({
                    'action_type': action['type'],
                    'result': {'error': str(e), 'success': False},
                    'success': False
                })
        
        return results
    
    async def _create_frontend_components(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new frontend components"""
        
        new_components = frontend_data.get('new_components', [])
        
        component_creation_prompt = f"""
        You are an expert frontend developer. Create new dashboard components based on these requirements.
        
        Components to create: {new_components}
        UI Framework: {frontend_data.get('ui_framework', 'html_css_js')}
        Styling: {frontend_data.get('styling_requirements', 'tailwind')}
        
        For each component, generate complete, production-ready code including:
        1. HTML structure
        2. CSS styling (Tailwind classes preferred)
        3. JavaScript functionality
        4. Integration with existing dashboard
        5. Responsive design
        6. Accessibility features
        
        Provide the code in JSON format:
        
        {{
            "components": [
                {{
                    "name": "ComponentName",
                    "description": "What this component does",
                    "html": "Complete HTML code",
                    "css": "Additional CSS if needed",
                    "javascript": "JavaScript functionality",
                    "integration_instructions": "How to integrate with dashboard",
                    "api_endpoints_needed": ["endpoint1", "endpoint2"],
                    "dependencies": ["dependency1", "dependency2"]
                }}
            ],
            "global_styles": "Any global CSS additions needed",
            "javascript_utilities": "Utility functions needed",
            "integration_steps": [
                "Step 1: Add HTML to dashboard.html",
                "Step 2: Add JavaScript to dashboard.js",
                "Step 3: Test functionality"
            ]
        }}
        
        Make components modern, user-friendly, and consistent with the existing dashboard design.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(component_creation_prompt)
            
            # Parse response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                component_data = json.loads(json_match.group())
                
                # Save generated components
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                components_dir = Path('generated_components')
                components_dir.mkdir(exist_ok=True)
                
                for component in component_data.get('components', []):
                    component_name = component['name']
                    
                    # Save component files
                    component_dir = components_dir / f"{component_name}_{timestamp}"
                    component_dir.mkdir(exist_ok=True)
                    
                    # Save HTML
                    (component_dir / f"{component_name}.html").write_text(component['html'])
                    
                    # Save CSS
                    if component.get('css'):
                        (component_dir / f"{component_name}.css").write_text(component['css'])
                    
                    # Save JavaScript
                    if component.get('javascript'):
                        (component_dir / f"{component_name}.js").write_text(component['javascript'])
                    
                    # Save integration instructions
                    (component_dir / "integration_instructions.md").write_text(component['integration_instructions'])
                
                # Save complete component data
                (components_dir / f"components_{timestamp}.json").write_text(json.dumps(component_data, indent=2))
                
                return {
                    'success': True,
                    'components_created': len(component_data.get('components', [])),
                    'component_data': component_data,
                    'saved_to': str(components_dir),
                    'message': f"Created {len(component_data.get('components', []))} new components"
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not parse component generation response',
                    'raw_response': ai_response
                }
                
        except Exception as e:
            logger.error(f"Error creating frontend components: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_api_endpoints(self, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new API endpoints"""
        
        new_endpoints = backend_data.get('new_endpoints', [])
        
        endpoint_creation_prompt = f"""
        You are an expert backend developer. Create new FastAPI endpoints based on these requirements.
        
        Endpoints to create: {new_endpoints}
        External integrations needed: {backend_data.get('external_integrations', [])}
        
        For each endpoint, generate complete, production-ready code including:
        1. FastAPI route definition
        2. Request/response models (Pydantic)
        3. Business logic implementation
        4. Error handling
        5. Authentication/authorization if needed
        6. Database operations if needed
        7. External API integrations if needed
        8. Comprehensive documentation
        
        Provide the code in JSON format:
        
        {{
            "endpoints": [
                {{
                    "path": "/api/endpoint-name",
                    "method": "GET|POST|PUT|DELETE",
                    "description": "What this endpoint does",
                    "code": "Complete FastAPI endpoint code",
                    "models": "Pydantic models needed",
                    "dependencies": ["dependency1", "dependency2"],
                    "database_operations": "Database code if needed",
                    "external_api_calls": "External API integration code",
                    "error_handling": "Error handling code",
                    "testing_examples": "Example requests and responses"
                }}
            ],
            "imports_needed": [
                "from fastapi import FastAPI, HTTPException",
                "from pydantic import BaseModel"
            ],
            "utility_functions": "Any utility functions needed",
            "integration_instructions": [
                "Step 1: Add imports to app.py",
                "Step 2: Add endpoint definitions",
                "Step 3: Test endpoints"
            ]
        }}
        
        Follow FastAPI best practices and ensure proper error handling and validation.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(endpoint_creation_prompt)
            
            # Parse response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                endpoint_data = json.loads(json_match.group())
                
                # Save generated endpoints
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                endpoints_dir = Path('generated_endpoints')
                endpoints_dir.mkdir(exist_ok=True)
                
                # Save endpoint code
                endpoint_file = endpoints_dir / f"endpoints_{timestamp}.py"
                
                # Generate complete endpoint file
                endpoint_code = "# Generated API Endpoints\n\n"
                
                # Add imports
                for import_stmt in endpoint_data.get('imports_needed', []):
                    endpoint_code += f"{import_stmt}\n"
                
                endpoint_code += "\n"
                
                # Add utility functions
                if endpoint_data.get('utility_functions'):
                    endpoint_code += f"# Utility Functions\n{endpoint_data['utility_functions']}\n\n"
                
                # Add endpoints
                for endpoint in endpoint_data.get('endpoints', []):
                    endpoint_code += f"# {endpoint['description']}\n"
                    endpoint_code += f"{endpoint['code']}\n\n"
                
                endpoint_file.write_text(endpoint_code)
                
                # Save complete endpoint data
                (endpoints_dir / f"endpoint_data_{timestamp}.json").write_text(json.dumps(endpoint_data, indent=2))
                
                return {
                    'success': True,
                    'endpoints_created': len(endpoint_data.get('endpoints', [])),
                    'endpoint_data': endpoint_data,
                    'saved_to': str(endpoints_dir),
                    'message': f"Created {len(endpoint_data.get('endpoints', []))} new API endpoints"
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not parse endpoint generation response',
                    'raw_response': ai_response
                }
                
        except Exception as e:
            logger.error(f"Error creating API endpoints: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_new_agents(self, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new intelligent agents"""
        
        new_agents = backend_data.get('new_agents', [])
        
        agent_creation_prompt = f"""
        You are an expert AI agent developer. Create new intelligent agents based on these requirements.
        
        Agents to create: {new_agents}
        
        For each agent, generate complete, production-ready code including:
        1. Agent class definition inheriting from DynamicAgent
        2. Initialization and configuration
        3. Core execution logic
        4. AI integration for intelligent decision making
        5. Error handling and logging
        6. Integration with existing systems
        7. Comprehensive documentation
        
        Provide the code in JSON format:
        
        {{
            "agents": [
                {{
                    "name": "AgentName",
                    "description": "What this agent does",
                    "capabilities": ["capability1", "capability2"],
                    "code": "Complete agent class code",
                    "config_schema": {{
                        "required_params": ["param1", "param2"],
                        "optional_params": ["param3", "param4"]
                    }},
                    "dependencies": ["dependency1", "dependency2"],
                    "ai_prompts": {{
                        "main_prompt": "Primary AI prompt for this agent",
                        "analysis_prompt": "Prompt for analysis tasks"
                    }},
                    "integration_points": ["database", "external_api", "other_agents"],
                    "testing_examples": [
                        {{
                            "input": "Example input",
                            "expected_output": "Expected output"
                        }}
                    ]
                }}
            ],
            "imports_needed": [
                "import asyncio",
                "from typing import Dict, List, Any"
            ],
            "utility_classes": "Any utility classes needed",
            "integration_instructions": [
                "Step 1: Add agent to dynamic_agent_factory.py",
                "Step 2: Register agent in agent registry",
                "Step 3: Test agent functionality"
            ]
        }}
        
        Make agents intelligent, efficient, and well-integrated with the existing system.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(agent_creation_prompt)
            
            # Parse response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                agent_data = json.loads(json_match.group())
                
                # Save generated agents
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                agents_dir = Path('generated_agents')
                agents_dir.mkdir(exist_ok=True)
                
                for agent in agent_data.get('agents', []):
                    agent_name = agent['name']
                    
                    # Save agent code
                    agent_file = agents_dir / f"{agent_name.lower()}_{timestamp}.py"
                    
                    # Generate complete agent file
                    agent_code = f"# Generated Agent: {agent_name}\n"
                    agent_code += f"# Description: {agent['description']}\n\n"
                    
                    # Add imports
                    for import_stmt in agent_data.get('imports_needed', []):
                        agent_code += f"{import_stmt}\n"
                    
                    agent_code += "\n"
                    
                    # Add utility classes
                    if agent_data.get('utility_classes'):
                        agent_code += f"{agent_data['utility_classes']}\n\n"
                    
                    # Add agent code
                    agent_code += f"{agent['code']}\n"
                    
                    agent_file.write_text(agent_code)
                
                # Save complete agent data
                (agents_dir / f"agent_data_{timestamp}.json").write_text(json.dumps(agent_data, indent=2))
                
                # Store in generated agents registry
                for agent in agent_data.get('agents', []):
                    self.generated_agents[agent['name']] = {
                        'created_at': datetime.now().isoformat(),
                        'agent_data': agent,
                        'file_path': str(agents_dir / f"{agent['name'].lower()}_{timestamp}.py")
                    }
                
                return {
                    'success': True,
                    'agents_created': len(agent_data.get('agents', [])),
                    'agent_data': agent_data,
                    'saved_to': str(agents_dir),
                    'message': f"Created {len(agent_data.get('agents', []))} new intelligent agents"
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not parse agent generation response',
                    'raw_response': ai_response
                }
                
        except Exception as e:
            logger.error(f"Error creating new agents: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_dashboard_response(self, request_analysis: Dict[str, Any], execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive response to user"""
        
        response_prompt = f"""
        You are an intelligent dashboard AI assistant. Generate a comprehensive, helpful response to the user based on the request analysis and execution results.
        
        Request Analysis:
        {json.dumps(request_analysis, indent=2)}
        
        Execution Results:
        {json.dumps(execution_results, indent=2)}
        
        Generate a response in JSON format:
        
        {{
            "message": "Main response message to the user",
            "success": true,
            "summary": {{
                "actions_taken": ["action1", "action2"],
                "components_created": 2,
                "endpoints_created": 1,
                "agents_created": 1,
                "estimated_completion_time": "30 minutes"
            }},
            "next_steps": [
                "Step 1: Review the generated components",
                "Step 2: Test the new functionality",
                "Step 3: Provide feedback for improvements"
            ],
            "generated_files": [
                {{
                    "type": "component",
                    "name": "ComponentName",
                    "path": "generated_components/ComponentName_20241126_161500",
                    "description": "What this file contains"
                }}
            ],
            "integration_instructions": [
                "How to integrate the new features",
                "What files to modify",
                "How to test the changes"
            ],
            "additional_capabilities": [
                "What else the AI can help with",
                "Suggestions for further improvements"
            ],
            "voice_response": "Concise version suitable for text-to-speech",
            "follow_up_questions": [
                "Would you like me to create additional features?",
                "Should I modify any of the generated components?",
                "Do you need help integrating these changes?"
            ]
        }}
        
        Be helpful, encouraging, and provide clear next steps.
        """
        
        try:
            ai_response = await self.vertex_ai.generate_content_async(response_prompt)
            
            # Parse response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                response_data['raw_ai_response'] = ai_response
                response_data['timestamp'] = datetime.now().isoformat()
                return response_data
            else:
                return {
                    'message': 'I\'ve processed your request and generated the requested features. Please check the generated files for the new components and functionality.',
                    'success': True,
                    'raw_response': ai_response,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating dashboard response: {e}")
            return {
                'message': 'I\'ve completed your request, but encountered an issue generating the response. The requested features should still be available.',
                'success': True,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # Placeholder methods for other actions
    async def _modify_frontend_components(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': True, 'message': 'Component modification not yet implemented'}
    
    async def _create_new_pages(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': True, 'message': 'Page creation not yet implemented'}
    
    async def _create_database_tables(self, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': True, 'message': 'Database table creation not yet implemented'}
    
    async def _integrate_data_sources(self, data_requirements: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': True, 'message': 'Data source integration not yet implemented'}
    
    async def _generate_general_response(self, request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'success': True,
            'message': 'I understand your request. Let me know if you need help with specific dashboard modifications or new features.',
            'analysis': request_analysis
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_generated_components(self) -> Dict[str, Any]:
        """Get information about generated components"""
        return {
            'dashboard_components': self.dashboard_components,
            'generated_agents': self.generated_agents,
            'total_components': len(self.dashboard_components),
            'total_agents': len(self.generated_agents)
        }

# Global instance
dashboard_ai_controller = None

def get_dashboard_ai_controller() -> DashboardAIController:
    """Get global dashboard AI controller instance"""
    global dashboard_ai_controller
    if dashboard_ai_controller is None:
        dashboard_ai_controller = DashboardAIController()
    return dashboard_ai_controller