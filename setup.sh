#!/bin/bash

echo "Setting up Housing Association Discovery System..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create config from example
if [ ! -f config/api_keys.env ]; then
    cp config/api_keys.env.example config/api_keys.env
    echo "Created config/api_keys.env - please add your API keys"
fi

# Create outputs directory structure
mkdir -p outputs/reports
mkdir -p outputs/data
mkdir -p outputs/league_tables

echo "Setup complete!"
echo "1. Add your API keys to config/api_keys.env"
echo "2. Run: python run_discovery.py --full-discovery"