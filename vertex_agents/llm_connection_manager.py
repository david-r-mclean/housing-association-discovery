"""
Enhanced LLM Connection Manager
Supports multiple LLM providers with fallback options
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import requests

logger = logging.getLogger(__name__)

class LLMConnectionManager:
    """Manages connections to multiple LLM providers"""
    
    def __init__(self):
        self.providers = {}
        self.active_provider = None
        self.fallback_providers = []
        
        # Initialize all available providers
        self.init_providers()
        
        # Test connections and set active provider
        asyncio.create_task(self.test_all_connections())
    
    def init_providers(self):
        """Initialize all LLM provider configurations"""
        
        # Load environment variables first
        from dotenv import load_dotenv
        load_dotenv()
        
        # Google Vertex AI
        self.providers['vertex_ai'] = {
            'name': 'Google Vertex AI',
            'class': VertexAIProvider,
            'config': {
                'project_id': os.getenv('GOOGLE_CLOUD_PROJECT', 'housing-ai-platform-470118'),
                'location': os.getenv('VERTEX_AI_LOCATION', 'us-central1'),
                'model_name': os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-pro'),
                'credentials_path': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            },
            'priority': 1,
            'status': 'unknown'
        }
        
        # OpenAI GPT
        self.providers['openai'] = {
            'name': 'OpenAI GPT',
            'class': OpenAIProvider,
            'config': {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model_name': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
            },
            'priority': 2,
            'status': 'unknown'
        }
        
        # Mock Provider for testing
        self.providers['mock'] = {
            'name': 'Mock Provider (Testing)',
            'class': MockProvider,
            'config': {},
            'priority': 999,
            'status': 'unknown'
        }
    
    async def test_all_connections(self):
        """Test all provider connections and set active provider"""
        
        logger.info("Testing LLM provider connections...")
        
        working_providers = []
        
        # Sort providers by priority
        sorted_providers = sorted(self.providers.items(), key=lambda x: x[1]['priority'])
        
        for provider_id, provider_config in sorted_providers:
            try:
                logger.info(f"Testing {provider_config['name']}...")
                
                # Create provider instance
                provider_class = provider_config['class']
                provider = provider_class(provider_config['config'])
                
                # Test connection
                test_result = await provider.test_connection()
                
                if test_result['success']:
                    provider_config['status'] = 'connected'
                    provider_config['instance'] = provider
                    working_providers.append((provider_id, provider_config))
                    logger.info(f"✅ {provider_config['name']} connected successfully")
                else:
                    provider_config['status'] = 'failed'
                    logger.warning(f"❌ {provider_config['name']} connection failed: {test_result.get('error', 'Unknown error')}")
                
            except Exception as e:
                provider_config['status'] = 'error'
                logger.error(f"❌ {provider_config['name']} error: {e}")
        
        # Set active provider (first working one)
        if working_providers:
            self.active_provider = working_providers[0][0]
            self.fallback_providers = [p[0] for p in working_providers[1:]]
            
            logger.info(f"🎯 Active LLM provider: {self.providers[self.active_provider]['name']}")
            if self.fallback_providers:
                fallback_names = [self.providers[p]['name'] for p in self.fallback_providers]
                logger.info(f"🔄 Fallback providers: {', '.join(fallback_names)}")
        else:
            logger.error("❌ No LLM providers are available!")
            # Create a mock provider for testing
            self.create_mock_provider()
    
    def create_mock_provider(self):
        """Create a mock provider for testing when no real providers are available"""
        
        logger.warning("Creating mock LLM provider for testing...")
        
        self.providers['mock']['status'] = 'connected'
        self.providers['mock']['instance'] = MockProvider({})
        
        self.active_provider = 'mock'
        self.fallback_providers = []
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content using the active provider with fallback"""
        
        if not self.active_provider:
            # Try to find a connected provider
            for provider_id, provider_config in self.providers.items():
                if provider_config.get('status') == 'connected' and provider_config.get('instance'):
                    self.active_provider = provider_id
                    break
            
            if not self.active_provider:
                raise Exception("No LLM provider available")
        
        # Try active provider first
        providers_to_try = [self.active_provider] + self.fallback_providers
        
        for provider_id in providers_to_try:
            try:
                provider_config = self.providers.get(provider_id)
                if not provider_config or not provider_config.get('instance'):
                    continue
                    
                provider = provider_config['instance']
                result = await provider.generate_content(prompt, **kwargs)
                
                logger.info(f"✅ Content generated using {provider_config['name']}")
                return result
                
            except Exception as e:
                logger.warning(f"❌ {self.providers[provider_id]['name']} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed to generate content")
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        
        return {
            'active_provider': self.active_provider,
            'active_provider_name': self.providers[self.active_provider]['name'] if self.active_provider else None,
            'fallback_providers': self.fallback_providers,
            'all_providers': {
                provider_id: {
                    'name': config['name'],
                    'status': config['status'],
                    'priority': config['priority']
                }
                for provider_id, config in self.providers.items()
            }
        }

# Base Provider Class
class BaseLLMProvider:
    """Base class for all LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = "Base Provider"
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the provider"""
        raise NotImplementedError
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content using the provider"""
        raise NotImplementedError

# Google Vertex AI Provider
class VertexAIProvider(BaseLLMProvider):
    """Google Vertex AI provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "Google Vertex AI"
        self.client = None
        
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Get project ID from config first, then environment
            project_id = config.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT', 'housing-ai-platform-470118')
            location = config.get('location') or os.getenv('VERTEX_AI_LOCATION', 'us-central1')
            model_name = config.get('model_name') or os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-pro')
            
            print(f"Initializing Vertex AI with project: {project_id}, location: {location}, model: {model_name}")
            
            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            
            self.model = GenerativeModel(model_name)
            
        except ImportError:
            logger.error("Vertex AI SDK not installed. Run: pip install google-cloud-aiplatform")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Vertex AI connection"""
        try:
            # Simple test prompt
            response = self.model.generate_content("Hello, this is a test. Please respond with 'Connection successful'.")
            
            if response and response.text:
                return {'success': True, 'response': response.text}
            else:
                return {'success': False, 'error': 'No response received'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content using Vertex AI"""
        try:
            response = self.model.generate_content(prompt)
            return response.text if response else "No response generated"
            
        except Exception as e:
            logger.error(f"Vertex AI generation failed: {e}")
            raise

# OpenAI Provider
class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "OpenAI GPT"
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=config.get('api_key'),
                base_url=config.get('base_url', 'https://api.openai.com/v1')
            )
            self.model_name = config.get('model_name', 'gpt-3.5-turbo')
            
        except ImportError:
            logger.error("OpenAI SDK not installed. Run: pip install openai")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection"""
        try:
            if not self.client.api_key:
                return {'success': False, 'error': 'No API key provided'}
                
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello, this is a test. Please respond with 'Connection successful'."}],
                max_tokens=50
            )
            
            if response.choices and response.choices[0].message:
                return {'success': True, 'response': response.choices[0].message.content}
            else:
                return {'success': False, 'error': 'No response received'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_tokens', 2000),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            return response.choices[0].message.content if response.choices else "No response generated"
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

# Mock Provider for Testing
class MockProvider(BaseLLMProvider):
    """Mock provider for testing when no real providers are available"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "Mock Provider (Testing)"
    
    async def test_connection(self) -> Dict[str, Any]:
        """Mock test connection"""
        return {'success': True, 'response': 'Mock connection successful'}
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate mock content"""
        
        # Simple mock responses based on prompt content
        prompt_lower = prompt.lower()
        
        if 'create' in prompt_lower and 'component' in prompt_lower:
            return """
            {
                "message": "I understand you want to create a new component. Here's what I would do:",
                "components": [
                    {
                        "name": "MockComponent",
                        "description": "A mock component for testing",
                        "html": "<div class='mock-component'>Mock Component</div>",
                        "javascript": "console.log('Mock component loaded');",
                        "integration_instructions": "This is a mock response for testing"
                    }
                ],
                "success": true,
                "voice_response": "I've created a mock component for testing purposes."
            }
            """
        
        elif 'regulatory' in prompt_lower or 'document' in prompt_lower:
            return """
            I understand you're looking for regulatory documents. In a real implementation, I would:
            
            1. Search government databases for relevant regulations
            2. Analyze document compliance requirements
            3. Create a comprehensive compliance report
            4. Set up monitoring for regulatory changes
            
            This is a mock response since no real LLM is connected. Please configure a real LLM provider for full functionality.
            """
        
        else:
            return f"""
            This is a mock response to your query: "{prompt[:100]}..."
            
            I'm a mock LLM provider used for testing when no real LLM is available.
            
            To get real AI responses, please configure one of these providers:
            - Google Vertex AI (recommended)
            - OpenAI GPT
            
            Check the console logs for connection status and configuration instructions.
            """

# Global instance
llm_manager = None

def get_llm_manager() -> LLMConnectionManager:
    """Get global LLM connection manager instance"""
    global llm_manager
    if llm_manager is None:
        llm_manager = LLMConnectionManager()
    return llm_manager