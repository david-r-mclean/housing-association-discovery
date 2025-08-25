# Housing Association Discovery System

Automated discovery and analysis system for UK housing associations, designed for digital transformation SaaS targeting.

## Features

- **Official Regulator Discovery**: Pulls data from Scottish Housing Regulator and Regulator of Social Housing
- **Companies House Integration**: Complete company profiles with filing history
- **Website Analysis**: Digital maturity assessment and feature detection
- **Social Media Metrics**: Multi-platform presence and engagement analysis
- **Comprehensive Data Storage**: Organized storage with PostgreSQL backend
- **Multiple Output Formats**: CSV, JSON, HTML league tables

## Current Coverage

- ✅ **173 Scottish Housing Associations** (Production Ready)
- 🟡 **English Housing Associations** (Framework Ready)
- 🔴 **Welsh/NI Housing Associations** (Planned)

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
2. Configure API Keys:

cp config/api_keys.env.example config/api_keys.env
# Edit with your actual API keys
3. Setup Database:

python setup_database.py
4. Run Discovery:

# Scottish housing associations
python run_discovery.py --full-discovery --region scottish

# With comprehensive data collection
python run_discovery.py --full-discovery --region scottish --comprehensive-data
Architecture
undefined

## API Keys Required

- **Companies House API**: https://developer.company-information.service.gov.uk/
- **Google Custom Search API**: https://developers.google.com/custom-search/v1/introduction

## Database Setup

The system supports both file-based storage (development) and PostgreSQL (production):

- **Development**: Automatic file-based storage in `storage/` directory
- **Production**: PostgreSQL with automatic schema creation

## Production Deployment

See `deployment/` directory for:
- Docker configuration
- AWS/Azure deployment scripts
- Environment setup guides

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Private - Lumberworks Ltd"# housing-association-discovery" 
