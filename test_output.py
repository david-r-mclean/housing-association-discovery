import json
from utils.output_generator import OutputGenerator

# Load your existing data
with open('outputs/data/housing_associations_20250823_154627.json', 'r') as f:
    associations = json.load(f)

print(f"Testing output generation with {len(associations)} associations...")

# Test output generation
output_gen = OutputGenerator(associations)
output_gen.generate_all_outputs()

print("Output test complete!")