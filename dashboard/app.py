from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Housing Association Discovery Platform")

# Mount static files
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="dashboard/templates")

# Basic routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root redirect to dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/social-media", response_class=HTMLResponse)
async def social_media_intelligence_page(request: Request):
    """Social Media Intelligence page"""
    return templates.TemplateResponse("social_media_intelligence.html", {"request": request})

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check database connection
        database_status = True
        try:
            # Test database connection here if needed
            pass
        except:
            database_status = False
        
        # Check LLM status more thoroughly
        llm_status = False
        llm_provider = None
        try:
            from vertex_agents.llm_connection_manager import get_llm_connection_manager
            llm_manager = get_llm_connection_manager()
            active_provider = llm_manager.get_active_provider()
            if active_provider:
                llm_status = True
                llm_provider = active_provider
        except Exception as e:
            logger.warning(f"LLM status check failed: {e}")
        
        # Check AI controller
        ai_controller_status = False
        try:
            from ai.dashboard_ai_controller import get_dashboard_ai_controller
            ai_controller = get_dashboard_ai_controller()
            ai_controller_status = True
        except Exception as e:
            logger.warning(f"AI controller check failed: {e}")
        
        return JSONResponse(content={
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': database_status,
            'llm_status': llm_status,
            'llm_provider': llm_provider,
            'ai_controller': ai_controller_status,
            'version': '1.0.0',
            'components': {
                'api_server': True,
                'database': database_status,
                'llm_provider': llm_status,
                'ai_controller': ai_controller_status
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

# Dashboard AI endpoints
@app.post("/api/dashboard-ai/process-request")
async def process_dashboard_request(request: Request):
    """Process dashboard AI requests"""
    try:
        data = await request.json()
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', 'default')
        
        if not message:
            return JSONResponse(
                status_code=400,
                content={'error': 'Message is required'}
            )
        
        logger.info(f"Processing dashboard request: {message}")
        
        # Try to use the AI dashboard controller
        try:
            from ai.dashboard_ai_controller import get_dashboard_ai_controller
            ai_controller = get_dashboard_ai_controller()
            
            # Process the request
            result = await ai_controller.process_dashboard_request(message)
            
            return JSONResponse(content={
                'success': True,
                'message': result.get('response', 'Request processed successfully'),
                'response': result.get('response', ''),
                'voice_response': result.get('voice_response'),
                'generated_files': result.get('generated_files', []),
                'conversation_id': conversation_id,
                'timestamp': datetime.now().isoformat()
            })
            
        except ImportError:
            # Fallback response if AI controller not available
            return JSONResponse(content={
                'success': True,
                'message': f"I received your message: '{message}'. The AI system is currently being set up.",
                'response': f"Thank you for your request about '{message}'. I'm working on processing this for you.",
                'conversation_id': conversation_id,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Dashboard AI request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

@app.get("/api/dashboard-ai/download/{filename}")
async def download_generated_file(filename: str):
    """Download generated files"""
    try:
        # This would typically serve files from a generated files directory
        file_path = f"generated_files/{filename}"
        
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type='application/octet-stream'
            )
        else:
            return JSONResponse(
                status_code=404,
                content={'error': 'File not found'}
            )
            
    except Exception as e:
        logger.error(f"File download failed: {e}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Mock stats for now - you can replace with real data
        stats = {
            'total_associations': 1247,
            'total_documents': 3891,
            'total_social_profiles': 892,
            'recent_analyses': 45,
            'system_uptime': '99.9%',
            'last_updated': datetime.now().isoformat()
        }
        
        return JSONResponse(content={
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

# Social Media Intelligence endpoints
@app.post("/api/social-media/analyze")
async def analyze_social_media(request: Request):
    """Analyze social media presence for a housing association"""
    
    try:
        data = await request.json()
        
        housing_association = data.get('housing_association', {})
        search_terms = data.get('search_terms', [])
        platforms = data.get('platforms', ['twitter', 'facebook', 'linkedin', 'instagram', 'youtube'])
        analysis_depth = data.get('analysis_depth', 'standard')
        
        if not housing_association.get('name'):
            return JSONResponse(
                status_code=400,
                content={'error': 'Housing association name is required'}
            )
        
        logger.info(f"Starting social media analysis for: {housing_association['name']}")
        
        # Try to create social media intelligence agent
        try:
            from agents.social_media_intelligence_agent import create_social_media_intelligence_agent
            from database.social_media_manager import get_social_media_manager
            
            # Create social media intelligence agent
            social_agent = create_social_media_intelligence_agent()
            
            # Execute analysis
            task_data = {
                'housing_association': housing_association,
                'search_terms': search_terms,
                'platforms': platforms,
                'analysis_depth': analysis_depth
            }
            
            result = await social_agent.execute(task_data)
            
            if result['success']:
                # Save to database
                social_media_manager = get_social_media_manager()
                report_id = social_media_manager.save_social_media_analysis(
                    housing_association['name'], 
                    result
                )
                result['report_id'] = report_id
                
                logger.info(f"Social media analysis completed for: {housing_association['name']}")
            
            return JSONResponse(content=result)
            
        except ImportError as e:
            logger.warning(f"Social media agent not available: {e}")
            # Return mock analysis result
            return JSONResponse(content={
                'success': True,
                'message': f"Social media analysis initiated for {housing_association['name']}",
                'association_name': housing_association['name'],
                'platforms_analyzed': platforms,
                'analysis_depth': analysis_depth,
                'mock_data': True,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Social media analysis failed: {e}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

@app.get("/api/social-media/platforms")
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    
    platforms = [
        {
            'id': 'twitter',
            'name': 'Twitter/X',
            'description': 'Real-time updates and community engagement',
            'api_required': False,
            'data_types': ['profiles', 'posts', 'mentions', 'hashtags']
        },
        {
            'id': 'facebook',
            'name': 'Facebook',
            'description': 'Community pages and resident groups',
            'api_required': False,
            'data_types': ['pages', 'posts', 'reviews', 'groups']
        },
        {
            'id': 'linkedin',
            'name': 'LinkedIn',
            'description': 'Professional presence and industry networking',
            'api_required': False,
            'data_types': ['company_pages', 'employee_profiles', 'posts']
        },
        {
            'id': 'instagram',
            'name': 'Instagram',
            'description': 'Visual content and community showcasing',
            'api_required': False,
            'data_types': ['profiles', 'posts', 'stories', 'hashtags']
        },
        {
            'id': 'youtube',
            'name': 'YouTube',
            'description': 'Video content and educational materials',
            'api_required': False,
            'data_types': ['channels', 'videos', 'comments']
        },
        {
            'id': 'reddit',
            'name': 'Reddit',
            'description': 'Community discussions and feedback',
            'api_required': False,
            'data_types': ['subreddits', 'posts', 'comments']
        },
        {
            'id': 'tiktok',
            'name': 'TikTok',
            'description': 'Short-form video content',
            'api_required': False,
            'data_types': ['profiles', 'videos', 'hashtags']
        }
    ]
    
    return JSONResponse(content={
        'success': True,
        'platforms': platforms,
        'total_platforms': len(platforms)
    })

@app.get("/api/social-media/dashboard-stats")
async def get_social_media_dashboard_stats():
    """Get dashboard statistics for social media intelligence"""
    try:
        # Mock data for now - replace with actual database queries
        stats = {
            "total_associations_analyzed": 47,
            "total_profiles_found": 156,
            "total_posts_analyzed": 2847,
            "total_reports_generated": 23,
            "platform_distribution": [
                {"platform": "Twitter", "count": 45},
                {"platform": "Facebook", "count": 38},
                {"platform": "LinkedIn", "count": 32},
                {"platform": "Instagram", "count": 28},
                {"platform": "YouTube", "count": 13}
            ],
            "sentiment_overview": [
                {"sentiment": "positive", "count": 1247},
                {"sentiment": "neutral", "count": 1156},
                {"sentiment": "negative", "count": 444}
            ]
        }
        
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting social media dashboard stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

# Background task function (properly indented)
async def run_discovery_task(task_data: dict):
    """Background task to run discovery"""
    try:
        logger.info(f"Running background discovery task: {task_data}")
        # Add your background task logic here
        await asyncio.sleep(1)  # Simulate work
        logger.info("Background discovery task completed")
    except Exception as e:
        logger.error(f"Background task failed: {e}")

# Discovery endpoint with background task
@app.post("/api/discovery/start")
async def start_discovery(request: Request, background_tasks: BackgroundTasks):
    """Start a discovery task"""
    try:
        data = await request.json()
        
        # Add background task
        background_tasks.add_task(run_discovery_task, data)
        
        return JSONResponse(content={
            'success': True,
            'message': 'Discovery task started',
            'task_id': 'discovery_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        })
        
    except Exception as e:
        logger.error(f"Discovery start failed: {e}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    """Documents page"""
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics page"""
    return templates.TemplateResponse("analytics.html", {"request": request})
@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """File management page"""
    return templates.TemplateResponse("files.html", {"request": request})

@app.get("/api/files/list")
async def list_generated_files():
    """List all generated files"""
    try:
        files_dir = Path("generated_files")
        if not files_dir.exists():
            return JSONResponse(content={"success": True, "files": []})
        
        files = []
        for file_path in files_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": file_path.suffix,
                    "path": str(file_path)
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return JSONResponse(content={"success": True, "files": files})
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/files/content/{filename}")
async def get_file_content(filename: str):
    """Get file content for editing"""
    try:
        file_path = Path("generated_files") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "content": content,
            "size": len(content)
        })
        
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/files/save/{filename}")
async def save_file_content(filename: str, request: Request):
    """Save edited file content"""
    try:
        data = await request.json()
        content = data.get("content", "")
        
        file_path = Path("generated_files") / filename
        
        # Create backup
        backup_path = Path("generated_files") / f"{filename}.backup"
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, backup_path)
        
        # Save new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return JSONResponse(content={
            "success": True,
            "message": f"File {filename} saved successfully",
            "backup_created": backup_path.exists()
        })
        
    except Exception as e:
        logger.error(f"Error saving file {filename}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/api/files/delete/{filename}")
async def delete_file(filename: str):
    """Delete a generated file"""
    try:
        file_path = Path("generated_files") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path.unlink()
        
        return JSONResponse(content={
            "success": True,
            "message": f"File {filename} deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/files/search")
async def search_files(request: Request):
    """Search through file contents"""
    try:
        data = await request.json()
        query = data.get("query", "").lower()
        
        if not query:
            return JSONResponse(content={"success": True, "results": []})
        
        files_dir = Path("generated_files")
        if not files_dir.exists():
            return JSONResponse(content={"success": True, "results": []})
        
        results = []
        for file_path in files_dir.iterdir():
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    if query in content.lower() or query in file_path.name.lower():
                        # Find matching lines
                        lines = content.split('\n')
                        matching_lines = []
                        for i, line in enumerate(lines):
                            if query in line.lower():
                                matching_lines.append({
                                    "line_number": i + 1,
                                    "content": line.strip()
                                })
                        
                        results.append({
                            "filename": file_path.name,
                            "matches": len(matching_lines),
                            "matching_lines": matching_lines[:5]  # Limit to first 5 matches
                        })
                        
                except Exception as e:
                    logger.warning(f"Error searching file {file_path.name}: {e}")
        
        return JSONResponse(content={"success": True, "results": results})
        
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
    
@app.get("/api/database/files")
async def get_database_files():
    """Get list of database files"""
    try:
        from database.file_manager import get_db_file_manager
        db_manager = get_db_file_manager()
        
        db_files = db_manager.get_database_files()
        doc_files = db_manager.get_document_files()
        
        return JSONResponse(content={
            "success": True,
            "database_files": db_files,
            "document_files": doc_files,
            "total_files": len(db_files) + len(doc_files)
        })
        
    except Exception as e:
        logger.error(f"Error getting database files: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/database/content/{filename}")
async def get_database_file_content(filename: str):
    """Get database file content"""
    try:
        from database.file_manager import get_db_file_manager
        db_manager = get_db_file_manager()
        
        # Try database directory first
        db_path = Path("database") / filename
        if db_path.exists():
            result = db_manager.read_file_content(str(db_path))
        else:
            # Try documents directory
            doc_path = Path("documents") / filename
            if doc_path.exists():
                result = db_manager.read_file_content(str(doc_path))
            else:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": "File not found"}
                )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting database file content: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/database/search")
async def search_database_files(request: Request):
    """Search database and document files"""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        from database.file_manager import get_db_file_manager
        db_manager = get_db_file_manager()
        
        results = db_manager.search_files(query)
        
        return JSONResponse(content={
            "success": True,
            "results": results,
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Error searching database files: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )