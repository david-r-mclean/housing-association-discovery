import asyncio
from vertex_agents.llm_connection_manager import get_llm_manager

async def test_vertex_direct():
    print("Testing Vertex AI connection directly...")
    
    # Get the LLM manager
    llm_manager = get_llm_manager()
    
    # Wait for initialization
    await asyncio.sleep(3)
    
    # Check status
    status = llm_manager.get_provider_status()
    print(f"Active provider: {status.get('active_provider', 'None')}")
    print(f"Active provider name: {status.get('active_provider_name', 'None')}")
    
    # Show all provider statuses
    print("\nAll providers:")
    for provider_id, provider_info in status['all_providers'].items():
        print(f"  {provider_info['name']}: {provider_info['status']}")
    
    # Try to generate content
    if status['active_provider']:
        print(f"\nTesting content generation with {status['active_provider_name']}...")
        try:
            response = await llm_manager.generate_content(
                "Hello! Please respond with 'Vertex AI is working perfectly!' to confirm the connection."
            )
            print(f"✅ Success! Response: {response}")
        except Exception as e:
            print(f"❌ Content generation failed: {e}")
    else:
        print("\n❌ No active provider available")
        
        # Try to manually set Vertex AI as active if it's connected
        if llm_manager.providers['vertex_ai']['status'] == 'connected':
            print("🔧 Manually setting Vertex AI as active provider...")
            llm_manager.active_provider = 'vertex_ai'
            
            try:
                response = await llm_manager.generate_content(
                    "Hello! Please respond with 'Vertex AI is working perfectly!' to confirm the connection."
                )
                print(f"✅ Success! Response: {response}")
            except Exception as e:
                print(f"❌ Manual test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_vertex_direct())