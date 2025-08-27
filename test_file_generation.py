"""
Test File Generation
"""

import asyncio
import json
from datetime import datetime

async def test_file_generation():
    """Test the file generation system"""
    
    print("🔍 Testing File Generation...")
    print("=" * 50)
    
    try:
        # Test 1: Import the AI controller
        print("\n1. Importing AI Controller:")
        from ai.dashboard_ai_controller import get_dashboard_ai_controller
        
        ai_controller = get_dashboard_ai_controller()
        print("   ✅ AI Controller imported successfully")
        
        # Test 2: Test file saving with Unicode content
        print("\n2. Testing File Saving:")
        test_content = """
# Test File with Unicode Characters
This is a test file with various Unicode characters:
- Arrow up: ↑
- Arrow right: →
- Bullet point: •
- Em dash: —
- Quotes: "Hello" and 'World'

def test_function():
    return "This works!"
        """
        
        result = ai_controller.save_generated_file(
            filename="test_unicode.py",
            content=test_content,
            description="Test file with Unicode characters"
        )
        
        if 'error' not in result:
            print("   ✅ File saved successfully")
            print(f"   📁 File: {result['filename']}")
            print(f"   📏 Size: {result['size']} bytes")
        else:
            print(f"   ❌ File save failed: {result['error']}")
            return False
        
        # Test 3: Test reading the file back
        print("\n3. Testing File Reading:")
        try:
            with open(result['path'], 'r', encoding='utf-8') as f:
                read_content = f.read()
            print("   ✅ File read successfully")
            print(f"   📄 Content length: {len(read_content)} characters")
        except Exception as e:
            print(f"   ❌ File read failed: {e}")
            return False
        
        # Test 4: Test the dashboard AI request
        print("\n4. Testing Dashboard AI Request:")
        try:
            test_request = "Create a simple Python function to calculate fibonacci numbers"
            result = await ai_controller.process_dashboard_request(test_request)
            
            if result.get('success', False):
                print("   ✅ Dashboard AI request processed")
                if result.get('generated_files'):
                    print(f"   📁 Generated {len(result['generated_files'])} files")
                else:
                    print("   ℹ️  No files generated (this is normal)")
            else:
                print(f"   ❌ Dashboard AI request failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Dashboard AI request failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_file_generation())
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 File Generation Test: PASSED")
    else:
        print("❌ File Generation Test: FAILED")