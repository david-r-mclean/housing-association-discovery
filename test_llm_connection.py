"""
Test LLM Connection
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_llm_connections():
    """Test all LLM connections"""
    
    print("🔍 Testing LLM Connections...")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("\n1. Environment Variables:")
    google_project = os.getenv('GOOGLE_CLOUD_PROJECT')
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    print(f"   GOOGLE_CLOUD_PROJECT: {google_project}")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
    
    if google_creds and os.path.exists(google_creds):
        print("   ✅ Credentials file exists")
    else:
        print("   ❌ Credentials file not found")
    
    # Test 2: Try importing Vertex AI
    print("\n2. Vertex AI Import:")
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        print("   ✅ Vertex AI imports successful")
        
        # Test 3: Initialize Vertex AI
        print("\n3. Vertex AI Initialization:")
        try:
            vertexai.init(project=google_project, location="us-central1")
            model = GenerativeModel("gemini-1.5-flash")
            print("   ✅ Vertex AI initialized successfully")
            
            # Test 4: Simple generation test
            print("\n4. Simple Generation Test:")
            try:
                response = model.generate_content("Say 'Hello, I am working!'")
                print(f"   ✅ Response: {response.text}")
                return True
                
            except Exception as e:
                print(f"   ❌ Generation failed: {e}")
                return False
                
        except Exception as e:
            print(f"   ❌ Vertex AI initialization failed: {e}")
            return False
            
    except ImportError as e:
        print(f"   ❌ Vertex AI import failed: {e}")
        return False
    
    # Test 5: Try LLM Connection Manager
    print("\n5. LLM Connection Manager:")
    try:
        from vertex_agents.llm_connection_manager import get_llm_connection_manager
        
        llm_manager = get_llm_connection_manager()
        print("   ✅ LLM Connection Manager imported")
        
        # Test connection
        active_provider = llm_manager.get_active_provider()
        print(f"   Active Provider: {active_provider}")
        
        if active_provider:
            print("   ✅ LLM Connection Manager working")
            return True
        else:
            print("   ❌ No active provider found")
            return False
            
    except Exception as e:
        print(f"   ❌ LLM Connection Manager failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_llm_connections())
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 LLM Connection Test: PASSED")
    else:
        print("❌ LLM Connection Test: FAILED")
        print("\n🔧 Troubleshooting Steps:")
        print("1. Check your .env file has correct GOOGLE_CLOUD_PROJECT")
        print("2. Verify GOOGLE_APPLICATION_CREDENTIALS path is correct")
        print("3. Ensure the service account has Vertex AI permissions")
        print("4. Try running: gcloud auth application-default login")