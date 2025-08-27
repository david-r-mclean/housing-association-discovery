# Housing Association Discovery Platform

An AI-powered platform for discovering, analyzing, and managing housing associations with advanced social media intelligence, voice interface, and dynamic component generation capabilities.

## 🚀 Features

### Core Capabilities
- **AI-Powered Dashboard**: Conversational AI assistant with natural language processing
- **Social Media Intelligence**: Multi-platform analysis across Twitter, Facebook, LinkedIn, Instagram
- **Voice Interface**: Speech recognition and synthesis with "Hey Dashboard" wake word
- **File Management**: Advanced code editor with syntax highlighting and search
- **Database Integration**: SQLite database management with schema viewing
- **Dynamic Components**: AI-generated dashboard components and API endpoints

### Technical Features
- **Multi-LLM Support**: Google Vertex AI, OpenAI, Claude, Azure OpenAI integration
- **Real-time Analytics**: Live charts and performance monitoring
- **Document Discovery**: Regulatory document search and analysis
- **Health Monitoring**: System status and component health checks
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **Charts**: Chart.js for data visualization
- **Database**: SQLite with custom managers
- **AI/ML**: Google Vertex AI, Gemini models
- **Voice**: Web Speech API
- **Code Editor**: CodeMirror

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud Project with Vertex AI enabled
- Service account credentials for Google Cloud

## 🚀 Quick Start

### 1. Clone the Repository
```bash

git clone https://github.com/YOUR_USERNAME/housing-association-discovery.git

cd housing-association-discovery
2. Set Up Virtual Environment

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install Dependencies

pip install fastapi uvicorn python-multipart jinja2 python-dotenv google-cloud-aiplatform
4. Configure Environment
Create a .env file:


GOOGLE_CLOUD_PROJECT=your-project-id

GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json
5. Run the Application

python -m uvicorn dashboard.app:app --reload --host 0.0.0.0 --port 8000
6. Access the Platform
Open your browser and navigate to: http://localhost:8000

📁 Project Structure

housing-association-discovery/

├── ai/                          # AI controllers and processors

│   └── dashboard_ai_controller.py

├── dashboard/                   # Main web application

│   ├── app.py                  # FastAPI application

│   ├── templates/              # HTML templates

│   └── static/                 # CSS, JS, assets

├── vertex_agents/              # LLM connection management

├── database/                   # Database managers and schemas

├── agents/                     # Specialized AI agents

├── generated_files/            # AI-generated code files

└── documents/                  # Document storage
🎯 Usage Examples
AI Assistant Commands
"Analyze social media presence for housing associations"
"Create API endpoints for data analysis"
"Generate dashboard components"
"Find regulatory documents"
"Help me with housing association search"
Voice Commands
"Hey Dashboard, find housing associations in London"
"Hey Dashboard, analyze social media data"
"Hey Dashboard, show me the latest reports"
🔧 API Endpoints
Core APIs
GET /api/health - System health check
POST /api/dashboard-ai/process-request - AI request processing
GET /api/files/list - List generated files
Social Media APIs
POST /api/social-media/analyze - Start social media analysis
GET /api/social-media/platforms - Get supported platforms
GET /api/social-media/dashboard-stats - Get analytics data
Database APIs
GET /api/database/files - List database files
GET /api/database/content/{filename} - Get file content
POST /api/database/search - Search files
🧪 Testing
Test LLM Connection

python test_llm_connection.py
Test File Generation

python test_file_generation.py
Fix File Encoding Issues

python fix_generated_files.py
🔒 Security Notes
Keep your .env file secure and never commit it
Rotate your Google Cloud service account keys regularly
Use environment variables for all sensitive configuration
Implement proper authentication for production use
🤝 Contributing
Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Google Cloud Vertex AI for LLM capabilities
FastAPI for the excellent web framework
Chart.js for beautiful data visualizations
Tailwind CSS for responsive design
CodeMirror for the code editor functionality
📞 Support
For support, please open an issue on GitHub or contact [your-email@example.com]

Built with ❤️ for the housing association community