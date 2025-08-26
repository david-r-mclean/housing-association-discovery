"""
Updated Production Vertex AI Agent with enhanced connection management
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the new connection manager
from vertex_agents.llm_connection_manager import get_llm_manager

logger = logging.getLogger(__name__)

class ProductionVertexAIAgent:
    """Production-ready Vertex AI agent with multiple LLM provider support"""
    
    def __init__(self):
        self.llm_manager = get_llm_manager()
        self.conversation_history = []
        
        logger.info("Production Vertex AI Agent initialized with enhanced connection management")
    
    async def generate_content_async(self, prompt: str, **kwargs) -> str:
        """Generate content using the best available LLM provider"""
        
        try:
            # Add to conversation history
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'kwargs': kwargs
            })
            
            # Generate content using connection manager
            response = await self.llm_manager.generate_content(prompt, **kwargs)
            
            # Add response to history
            self.conversation_history[-1]['response'] = response
            self.conversation_history[-1]['provider'] = self.llm_manager.active_provider
            
            logger.info(f"Content generated successfully using {self.llm_manager.providers[self.llm_manager.active_provider]['name']}")
            
            return response
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            
            # Add error to history
            if self.conversation_history:
                self.conversation_history[-1]['error'] = str(e)
            
            # Return a helpful error message
            return f"I apologize, but I'm having trouble connecting to the AI service. Error: {str(e)}. Please check your LLM provider configuration."
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """Synchronous wrapper for generate_content_async"""
        
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                task = asyncio.create_task(self.generate_content_async(prompt, **kwargs))
                return asyncio.run_coroutine_threadsafe(task, loop).result(timeout=30)
            else:
                # If no loop is running, run directly
                return asyncio.run(self.generate_content_async(prompt, **kwargs))
        except Exception as e:
            # Fallback for synchronous execution
            logger.warning(f"Async execution failed, trying sync fallback: {e}")
            return asyncio.run(self.generate_content_async(prompt, **kwargs))
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers"""
        return self.llm_manager.get_provider_status()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the current LLM connection"""
        
        try:
            test_prompt = "Hello! Please respond with 'Connection test successful' to confirm the LLM is working."
            response = await self.generate_content_async(test_prompt)
            
            return {
                'success': True,
                'response': response,
                'provider': self.llm_manager.active_provider,
                'provider_name': self.llm_manager.providers[self.llm_manager.active_provider]['name'] if self.llm_manager.active_provider else 'None'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': self.llm_manager.active_provider
            }

# Global instance for backward compatibility
vertex_ai_agent = None

def get_vertex_ai_agent() -> ProductionVertexAIAgent:
    """Get global vertex AI agent instance"""
    global vertex_ai_agent
    if vertex_ai_agent is None:
        vertex_ai_agent = ProductionVertexAIAgent()
    return vertex_ai_agent