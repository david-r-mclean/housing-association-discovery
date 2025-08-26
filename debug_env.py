import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=== Environment Variables ===")
print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
print(f"VERTEX_AI_LOCATION: {os.getenv('VERTEX_AI_LOCATION', 'NOT SET')}")
print(f"VERTEX_AI_MODEL: {os.getenv('VERTEX_AI_MODEL', 'NOT SET')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')}")

print("\n=== All Environment Variables Starting with GOOGLE or VERTEX ===")
for key, value in os.environ.items():
    if key.startswith(('GOOGLE', 'VERTEX')):
        print(f"{key}: {value}")