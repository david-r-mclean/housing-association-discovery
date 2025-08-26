import os
import asyncio
from vertex_agents.llm_connection_manager import get_llm_manager

async def test_vertex_connection():
    print("Testing Vertex AI connection...")
    
    # Get the LLM manager
    llm_manager = get_llm_manager()
    
    # Wait a moment for initialization
    await asyncio.sleep(2)
    
    # Check provider status
    status = llm_manager.get_provider_status()
    print(f"Active provider: {status.get('active_provider_name', 'None')}")
    
    # Test all providers
    print("\nProvider Status:")
    for provider_id, provider_info in status['all_providers'].items():
        print(f"  {provider_info['name']}: {provider_info['status']}")
    
    # Test content generation
    if status['active_provider']:
        print(f"\nTesting content generation with {status['active_provider_name']}...")
        try:
            response = await llm_manager.generate_content(
                "Hello! Please respond with 'Vertex AI connection successful' to confirm everything is working."
            )
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\nNo active provider available for testing.")

if __name__ == "__main__":
    asyncio.run(test_vertex_connection())