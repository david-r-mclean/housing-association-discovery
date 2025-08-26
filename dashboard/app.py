"""
Real-time Housing Association Intelligence Dashboard
FastAPI backend with WebSocket support for live updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path
import sys
import zipfile
import io
from fastapi.responses import FileResponse, StreamingResponse
import glob
import csv
from orchestration.core import get_orchestration_engine, Priority
from orchestration.workflows import WorkflowTemplates
from config.industry_configs import IndustryType
from ai.intent_engine import get_intent_engine
from agents.dynamic_agent_factory import get_agent_factory
from datetime import datetime
from agents.regulatory_document_agent import get_regulatory_agent
from database.regulatory_document_manager import get_regulatory_doc_manager
from ai.dashboard_ai_controller import get_dashboard_ai_controller
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.database_manager import DatabaseManager
from database.duplicate_manager import DuplicateManager
from vertex_agents.real_vertex_agent import ProductionVertexAIAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Housing Association Intelligence Dashboard",
    description="Real-time AI-powered housing association analytics",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")

# Global state for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Initialize database managers
db_manager = DatabaseManager()
duplicate_manager = DuplicateManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        # Get all associations
        all_associations = db_manager.get_all_associations()
        
        # Calculate statistics
        total_associations = len(all_associations)
        ai_enhanced = sum(1 for a in all_associations if hasattr(a, 'ai_insights') and a.ai_insights)
        
        # Digital maturity distribution
        digital_scores = []
        for assoc in all_associations:
            if hasattr(assoc, 'ai_insights') and assoc.ai_insights:
                try:
                    ai_data = json.loads(assoc.ai_insights) if isinstance(assoc.ai_insights, str) else assoc.ai_insights
                    score = ai_data.get('digital_maturity_assessment', {}).get('overall_score', 0)
                    if score > 0:
                        digital_scores.append(score)
                except:
                    pass
        
        avg_digital_maturity = sum(digital_scores) / len(digital_scores) if digital_scores else 0
        
        # Regional distribution
        regions = {}
        for assoc in all_associations:
            region = assoc.region or 'Unknown'
            regions[region] = regions.get(region, 0) + 1
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_updates = sum(1 for a in all_associations if a.updated_at and a.updated_at > week_ago)
        
        stats = {
            "total_associations": total_associations,
            "ai_enhanced": ai_enhanced,
            "ai_enhancement_rate": round((ai_enhanced / total_associations * 100) if total_associations > 0 else 0, 1),
            "avg_digital_maturity": round(avg_digital_maturity, 1),
            "regions": regions,
            "recent_updates": recent_updates,
            "digital_maturity_distribution": {
                "leaders": len([s for s in digital_scores if s >= 8]),
                "followers": len([s for s in digital_scores if 5 <= s < 8]),
                "laggards": len([s for s in digital_scores if s < 5])
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {"error": str(e)}

@app.get("/api/associations")
async def get_associations(region: Optional[str] = None, limit: int = 200):
    """Get associations with optional filtering"""
    try:
        associations = db_manager.get_all_associations(region)
        
        # Convert to dict format and limit results
        result = []
        for assoc in associations[:limit]:
            assoc_data = {
                "id": assoc.id,
                "name": assoc.name or assoc.company_name,
                "company_number": assoc.company_number,
                "region": assoc.region,
                "official_website": assoc.official_website,
                "company_status": assoc.company_status,
                "officers_count": assoc.officers_count,
                "recent_filings": assoc.recent_filings,
                "website_has_tenant_portal": assoc.website_has_tenant_portal,
                "website_has_online_services": assoc.website_has_online_services,
                "social_media_activity_score": assoc.social_media_activity_score,
                "updated_at": assoc.updated_at.isoformat() if assoc.updated_at else None,
                "ai_enhanced": hasattr(assoc, 'ai_insights') and assoc.ai_insights is not None
            }
            
            # Add AI insights if available
            if hasattr(assoc, 'ai_insights') and assoc.ai_insights:
                try:
                    ai_data = json.loads(assoc.ai_insights) if isinstance(assoc.ai_insights, str) else assoc.ai_insights
                    assoc_data["digital_maturity_score"] = ai_data.get('digital_maturity_assessment', {}).get('overall_score', 0)
                    assoc_data["ai_transformation_opportunities"] = len(ai_data.get('ai_transformation_opportunities', []))
                    assoc_data["confidence_score"] = ai_data.get('confidence_metrics', {}).get('analysis_confidence', 0)
                except:
                    pass
            
            result.append(assoc_data)
        
        return {
            "associations": result,
            "total": len(associations),
            "returned": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting associations: {e}")
        return {"error": str(e)}

@app.get("/api/association/{association_id}")
async def get_association_detail(association_id: int):
    """Get detailed information for a specific association"""
    try:
        session = db_manager.get_session()
        association = session.query(db_manager.HousingAssociation).filter_by(id=association_id).first()
        
        if not association:
            return {"error": "Association not found"}
        
        # Convert to detailed dict
        detail = {
            "id": association.id,
            "name": association.name or association.company_name,
            "company_number": association.company_number,
            "company_status": association.company_status,
            "incorporation_date": association.incorporation_date.isoformat() if association.incorporation_date else None,
            "company_type": association.company_type,
            "registered_office_address": association.registered_office_address,
            "region": association.region,
            "source": association.source,
            "official_website": association.official_website,
            "phone_numbers": association.phone_numbers,
            "email_addresses": association.email_addresses,
            "officers_count": association.officers_count,
            "recent_filings": association.recent_filings,
            "website_features": {
                "has_search": association.website_has_search,
                "has_tenant_portal": association.website_has_tenant_portal,
                "has_online_services": association.website_has_online_services,
                "responsive": association.website_responsive
            },
            "social_media": association.social_media,
            "social_media_activity_score": association.social_media_activity_score,
            "created_at": association.created_at.isoformat() if association.created_at else None,
            "updated_at": association.updated_at.isoformat() if association.updated_at else None
        }
        
        # Add AI insights if available
        if hasattr(association, 'ai_insights') and association.ai_insights:
            try:
                ai_data = json.loads(association.ai_insights) if isinstance(association.ai_insights, str) else association.ai_insights
                detail["ai_insights"] = ai_data
            except:
                pass
        
        session.close()
        return detail
        
    except Exception as e:
        logger.error(f"Error getting association detail: {e}")
        return {"error": str(e)}

@app.post("/api/discover")
async def trigger_discovery(background_tasks: BackgroundTasks, region: str = "scottish"):
    """Trigger a new discovery process"""
    
    async def run_discovery():
    """Background task to run discovery"""
    try:
        # Broadcast start message
        await manager.broadcast({
            "type": "discovery_started",
            "region": region,
            "timestamp": datetime.now().isoformat()
        })
        
        # Import discovery modules
        from agents.regulator_discovery_agent import RegulatorDiscoveryAgent
        from agents.enrichment_agent import WebsiteEnrichmentAgent
        
        # Phase 1: Discovery
        await manager.broadcast({
            "type": "discovery_progress",
            "phase": "discovery",
            "message": f"Discovering {region} housing associations..."
        })
        
        regulator_agent = RegulatorDiscoveryAgent()
        discovered = regulator_agent.discover_all_housing_associations(focus_region=region)
        
        await manager.broadcast({
            "type": "discovery_progress",
            "phase": "discovery",
            "message": f"Found {len(discovered)} associations",
            "count": len(discovered)
        })
        
        # Phase 2: Duplicate filtering
        if duplicate_manager:
            filtered_results = duplicate_manager.filter_new_associations(discovered, region=region)
            to_process = filtered_results['new'] + [item['association'] for item in filtered_results['stale']]
        else:
            # REMOVE THE [:10] LIMIT HERE TOO
            to_process = discovered  # Changed from discovered[:10]
        
        await manager.broadcast({
            "type": "discovery_progress",
            "phase": "filtering",
            "message": f"Processing {len(to_process)} associations",
            "count": len(to_process)
        })
        
        # Phase 3: Enrichment - PROCESS ALL ASSOCIATIONS
        website_agent = WebsiteEnrichmentAgent()
        enriched = []
        
        for i, assoc in enumerate(to_process, 1):  # Process ALL associations
            await manager.broadcast({
                "type": "discovery_progress",
                "phase": "enrichment",
                "message": f"Enriching {assoc.get('name', 'Unknown')} ({i}/{len(to_process)})",
                "progress": (i / len(to_process)) * 100
            })
            
            enriched_assoc = assoc.copy()
            website_data = website_agent.enrich_association(assoc)
            enriched_assoc.update(website_data)
            enriched.append(enriched_assoc)
            
            # Small delay to prevent overwhelming servers
            await asyncio.sleep(0.5)  # Increased delay for politeness
            
            # Progress updates every 10 associations
            if i % 10 == 0:
                await manager.broadcast({
                    "type": "discovery_progress",
                    "phase": "enrichment",
                    "message": f"Completed {i}/{len(to_process)} associations",
                    "progress": (i / len(to_process)) * 100
                })
        
        # Phase 4: Save to database
        if db_manager:
            saved_count = db_manager.save_housing_associations(enriched, region)
        else:
            saved_count = 0
        
        await manager.broadcast({
            "type": "discovery_completed",
            "region": region,
            "total_processed": len(enriched),
            "saved_count": saved_count,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        await manager.broadcast({
            "type": "discovery_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    background_tasks.add_task(run_discovery)
    
    return {
        "status": "started",
        "region": region,
        "message": "Discovery process started in background"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/market-intelligence")
async def get_market_intelligence():
    """Get latest market intelligence data"""
    try:
        # Try to load from file
        intelligence_file = Path("outputs/market_intelligence_scottish.json")
        if intelligence_file.exists():
            with open(intelligence_file, 'r') as f:
                return json.load(f)
        else:
            return {"message": "No market intelligence data available. Run comprehensive analysis first."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/business-insights")
async def get_business_insights():
    """Get latest business insights"""
    try:
        insights_file = Path("outputs/business_insights_scottish.json")
        if insights_file.exists():
            with open(insights_file, 'r') as f:
                return json.load(f)
        else:
            return {"message": "No business insights available. Run comprehensive analysis first."}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    @app.get("/api/reports")
async def get_available_reports():
    """Get list of available reports and outputs"""
    try:
        outputs_dir = parent_dir / "outputs"
        reports = {
            "data_files": [],
            "reports": [],
            "league_tables": [],
            "market_intelligence": [],
            "business_insights": []
        }
        
        if outputs_dir.exists():
            # Data files (CSV, JSON)
            for pattern in ["*.csv", "*.json"]:
                for file_path in outputs_dir.glob(f"**/{pattern}"):
                    file_info = {
                        "name": file_path.name,
                        "path": str(file_path.relative_to(parent_dir)),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "type": file_path.suffix[1:].upper()
                    }
                    
                    if "enriched" in file_path.name or "associations" in file_path.name:
                        reports["data_files"].append(file_info)
                    elif "market_intelligence" in file_path.name:
                        reports["market_intelligence"].append(file_info)
                    elif "business_insights" in file_path.name:
                        reports["business_insights"].append(file_info)
                    elif "summary_report" in file_path.name:
                        reports["reports"].append(file_info)
            
            # HTML league tables
            for file_path in outputs_dir.glob("**/*.html"):
                reports["league_tables"].append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(parent_dir)),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "type": "HTML"
                })
        
        return reports
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return {"error": str(e)}

@app.get("/api/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    """Download a specific report file"""
    try:
        file_path = parent_dir / "outputs" / file_type / filename
        
        # Also check root outputs directory
        if not file_path.exists():
            file_path = parent_dir / "outputs" / filename
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return {"error": str(e)}

@app.get("/api/download-all")
async def download_all_reports():
    """Download all reports as a ZIP file"""
    try:
        outputs_dir = parent_dir / "outputs"
        
        if not outputs_dir.exists():
            return {"error": "No reports available"}
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in outputs_dir.rglob("*"):
                if file_path.is_file():
                    # Add file to ZIP with relative path
                    arcname = str(file_path.relative_to(outputs_dir))
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=housing_association_reports.zip"}
        )
        
    except Exception as e:
        logger.error(f"Error creating ZIP: {e}")
        return {"error": str(e)}

@app.get("/api/view-report/{filename}")
async def view_report_content(filename: str):
    """View report content (JSON/CSV preview)"""
    try:
        file_path = parent_dir / "outputs" / filename
        
        # Also check subdirectories
        if not file_path.exists():
            for subdir in ["data", "reports", "league_tables"]:
                alt_path = parent_dir / "outputs" / subdir / filename
                if alt_path.exists():
                    file_path = alt_path
                    break
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return {"type": "json", "content": content, "filename": filename}
        
        elif file_ext == '.csv':
            # Read CSV and return first 100 rows for preview
            rows = []
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                headers = csv_reader.fieldnames
                for i, row in enumerate(csv_reader):
                    if i >= 100:  # Limit preview
                        break
                    rows.append(row)
            
            return {
                "type": "csv",
                "headers": headers,
                "rows": rows,
                "total_rows": len(rows),
                "filename": filename,
                "preview_limit": 100
            }
        
        elif file_ext == '.html':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"type": "html", "content": content, "filename": filename}
        
        else:
            return {"error": "Unsupported file type"}
        
    except Exception as e:
        logger.error(f"Error viewing report: {e}")
        return {"error": str(e)}

@app.get("/api/arc-returns")
async def get_arc_returns():
    """Get ARC (Annual Return to Communities) data from Scottish Housing Regulator"""
    try:
        # Import the Scottish ARC agent
        from agents.scottish_arc_agent import ScottishARCAgent
        
        logger.info("Fetching ARC returns from Scottish Housing Regulator")
        
        arc_agent = ScottishARCAgent()
        arc_data = arc_agent.extract_arc_returns_data()
        
        if 'error' in arc_data:
            return {"error": arc_data['error']}
        
        # Process the data for dashboard display
        processed_data = {
            "arc_returns": [],
            "total_associations": len(arc_data.get('associations', [])),
            "total_data_sources": len(arc_data.get('data_sources', [])),
            "data_years": arc_data.get('summary_statistics', {}).get('data_years', []),
            "last_updated": arc_data.get('extraction_date'),
            "source": "Scottish Housing Regulator",
            "performance_indicators": arc_data.get('performance_indicators', {}),
            "summary_statistics": arc_data.get('summary_statistics', {})
        }
        
        # Format associations for table display
        for assoc in arc_data.get('associations', []):
            processed_assoc = {
                "name": assoc.get('name', 'Unknown'),
                "registration_number": assoc.get('registration_number', 'N/A'),
                "stock_units": assoc.get('stock_units', 0),
                "satisfaction_score": assoc.get('satisfaction_score', 'N/A'),
                "complaints": assoc.get('complaints', 'N/A'),
                "year": assoc.get('year', 'N/A'),
                "data_source": assoc.get('data_source', 'Unknown'),
                "rent_collected": assoc.get('rent_collected', 'N/A'),
                "repairs_completed": assoc.get('repairs_completed', 'N/A')
            }
            processed_data["arc_returns"].append(processed_assoc)
        
        # Sort by stock units (largest first)
        processed_data["arc_returns"].sort(
            key=lambda x: int(str(x.get('stock_units', 0)).replace(',', '')) if str(x.get('stock_units', 0)).replace(',', '').isdigit() else 0, 
            reverse=True
        )
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error getting ARC returns: {e}")
        return {"error": str(e)}

@app.get("/api/industry-configs")
async def get_industry_configs():
    """Get available industry configurations"""
    try:
        from config.industry_configs import IndustryConfigManager
        
        config_manager = IndustryConfigManager()
        configs = config_manager.get_all_configs()
        
        industry_list = []
        for industry_type, config in configs.items():
            industry_info = {
                "type": industry_type.value,
                "name": config.name,
                "description": config.description,
                "search_keywords": config.search_keywords,
                "data_sources": [
                    {
                        "name": source.name,
                        "type": source.type,
                        "url": source.url
                    } for source in config.data_sources
                ],
                "output_fields": config.output_fields,
                "company_types": config.company_types,
                "sic_codes": config.sic_codes
            }
            industry_list.append(industry_info)
        
        return {"industries": industry_list}
        
    except Exception as e:
        logger.error(f"Error getting industry configs: {e}")
        return {"error": str(e)}

@app.post("/api/discover-universal")
async def trigger_universal_discovery(background_tasks: BackgroundTasks, request: Request):
    """Trigger universal discovery with custom parameters"""
    
    try:
        body = await request.json()
        
        industry_type = body.get('industry_type', 'housing_associations')
        region = body.get('region', 'all')
        limit = body.get('limit')
        custom_keywords = body.get('custom_keywords', [])
        use_ai = body.get('use_ai', False)
        save_to_db = body.get('save_to_database', True)
        comprehensive = body.get('comprehensive_analysis', False)
        
        async def run_universal_discovery():
            """Background task for universal discovery"""
            try:
                await manager.broadcast({
                    "type": "discovery_started",
                    "industry": industry_type,
                    "region": region,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Import universal discovery agent
                from agents.universal_discovery_agent import UniversalDiscoveryAgent
                from config.industry_configs import IndustryType
                
                # Convert string to enum
                industry_enum = IndustryType(industry_type)
                
                # Initialize agent
                agent = UniversalDiscoveryAgent(industry_enum)
                
                await manager.broadcast({
                    "type": "discovery_progress",
                    "phase": "initialization",
                    "message": f"Initialized discovery for {agent.config.name}"
                })
                
                # Discover organizations
                discovered = agent.discover_organizations(
                    region=region,
                    limit=int(limit) if limit else None,
                    custom_keywords=custom_keywords
                )
                
                await manager.broadcast({
                    "type": "discovery_progress",
                    "phase": "discovery",
                    "message": f"Discovered {len(discovered)} organizations",
                    "count": len(discovered)
                })
                
                # Enrich with website data if needed
                if discovered:
                    from agents.enrichment_agent import WebsiteEnrichmentAgent
                    
                    website_agent = WebsiteEnrichmentAgent()
                    enriched = []
                    
                    for i, org in enumerate(discovered, 1):
                        await manager.broadcast({
                            "type": "discovery_progress",
                            "phase": "enrichment",
                            "message": f"Enriching {org.get('name', 'Unknown')} ({i}/{len(discovered)})",
                            "progress": (i / len(discovered)) * 100
                        })
                        
                        enriched_org = org.copy()
                        website_data = website_agent.enrich_association(org)
                        enriched_org.update(website_data)
                        enriched.append(enriched_org)
                        
                        await asyncio.sleep(0.5)
                    
                    discovered = enriched
                
                # AI Analysis if requested
                if use_ai and discovered:
                    from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
                    
                    ai_agent = ProductionVertexAIAgent()
                    
                    for i, org in enumerate(discovered, 1):
                        await manager.broadcast({
                            "type": "discovery_progress",
                            "phase": "ai_analysis",
                            "message": f"AI analyzing {org.get('name', 'Unknown')} ({i}/{len(discovered)})",
                            "progress": (i / len(discovered)) * 100
                        })
                        
                        # Use industry-specific AI prompts
                        ai_analysis = await ai_agent.analyze_organization_universal(org, agent.config)
                        org['ai_insights'] = ai_analysis
                        org['ai_enhanced'] = True
                        
                        await asyncio.sleep(1.0)
                
                # Save to database if requested
                saved_count = 0
                if save_to_db and discovered:
                    if db_manager:
                        saved_count = db_manager.save_organizations_universal(discovered, industry_type, region)
                
                # Generate outputs
                if discovered:
                    from utils.output_generator import OutputGenerator
                    output_gen = OutputGenerator(discovered)
                    output_gen.generate_all_outputs(suffix=f"_{industry_type}_{region}")
                
                await manager.broadcast({
                    "type": "discovery_completed",
                    "industry": industry_type,
                    "region": region,
                    "total_processed": len(discovered),
                    "saved_count": saved_count,
                    "ai_enhanced": sum(1 for org in discovered if org.get('ai_enhanced')),
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Universal discovery error: {e}")
                await manager.broadcast({
                    "type": "discovery_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        background_tasks.add_task(run_universal_discovery)
        
        return {
            "status": "started",
            "industry": industry_type,
            "region": region,
            "message": "Universal discovery process started"
        }
        
    except Exception as e:
        logger.error(f"Error starting universal discovery: {e}")
        return {"error": str(e)}

@app.get("/api/download-arc-returns")
async def download_arc_returns():
    """Download ARC returns data as CSV"""
    try:
        arc_response = await get_arc_returns()
        
        if "error" in arc_response:
            return arc_response
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'name', 'registration_number', 'stock_units', 'satisfaction_score',
            'complaints', 'year', 'data_source', 'rent_collected', 'repairs_completed'
        ])
        
        writer.writeheader()
        writer.writerows(arc_response["arc_returns"])
        
        # Convert to bytes
        csv_content = output.getvalue().encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=scottish_arc_returns.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error downloading ARC returns: {e}")
        return {"error": str(e)}

@app.get("/api/insights-summary")
async def get_insights_summary():
    """Get comprehensive insights summary from all available data"""
    try:
        # Load business insights if available
        insights_file = parent_dir / "outputs" / "business_insights_scottish.json"
        market_file = parent_dir / "outputs" / "market_intelligence_scottish.json"
        
        summary = {
            "business_insights": None,
            "market_intelligence": None,
            "database_stats": None,
            "recommendations": []
        }
        
        # Load business insights
        if insights_file.exists():
            with open(insights_file, 'r') as f:
                summary["business_insights"] = json.load(f)
        
        # Load market intelligence
        if market_file.exists():
            with open(market_file, 'r') as f:
                summary["market_intelligence"] = json.load(f)
        
        # Get database statistics
        if db_manager:
            associations = db_manager.get_all_associations()
            summary["database_stats"] = {
                "total_associations": len(associations),
                "with_websites": sum(1 for a in associations if a.official_website),
                "with_tenant_portals": sum(1 for a in associations if a.website_has_tenant_portal),
                "with_online_services": sum(1 for a in associations if a.website_has_online_services),
                "active_filings": sum(1 for a in associations if a.recent_filings and a.recent_filings > 0),
                "regions": len(set(a.region for a in associations if a.region))
            }
        
        # Generate recommendations based on data
        if summary["database_stats"]:
            stats = summary["database_stats"]
            recommendations = []
            
            if stats["with_tenant_portals"] / stats["total_associations"] < 0.5:
                recommendations.append({
                    "priority": "high",
                    "category": "Digital Services",
                    "recommendation": "50%+ of associations lack tenant portals - major digitization opportunity",
                    "impact": "High tenant satisfaction and operational efficiency gains"
                })
            
            if stats["with_online_services"] / stats["total_associations"] < 0.7:
                recommendations.append({
                    "priority": "medium",
                    "category": "Online Services",
                    "recommendation": "Expand online service offerings across the sector",
                    "impact": "Reduced administrative burden and improved accessibility"
                })
            
            summary["recommendations"] = recommendations
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting insights summary: {e}")
        return {"error": str(e)}
    
@app.get("/api/orchestration/workflows")
async def get_workflows():
    """Get all workflows"""
    try:
        engine = get_orchestration_engine()
        workflows = []
        
        for workflow_id, workflow in engine.workflows.items():
            status = await engine.get_workflow_status(workflow_id)
            workflows.append(status)
        
        return {"workflows": workflows}
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        return {"error": str(e)}

@app.post("/api/orchestration/create-workflow")
async def create_orchestrated_workflow(request: Request):
    """Create a new orchestrated workflow"""
    try:
        body = await request.json()
        
        industry_type = IndustryType(body.get('industry_type', 'housing_associations'))
        region = body.get('region', 'all')
        use_ai = body.get('use_ai', True)
        parallel_tasks = body.get('parallel_tasks', 5)
        
        templates = WorkflowTemplates()
        workflow_id = await templates.create_comprehensive_discovery_workflow(
            industry_type=industry_type,
            region=region,
            use_ai=use_ai,
            parallel_enrichment=parallel_tasks
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "created",
            "message": "Orchestrated workflow created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating orchestrated workflow: {e}")
        return {"error": str(e)}

@app.post("/api/orchestration/start-workflow/{workflow_id}")
async def start_orchestrated_workflow(workflow_id: str):
    """Start an orchestrated workflow"""
    try:
        engine = get_orchestration_engine()
        success = await engine.start_workflow(workflow_id)
        
        if success:
            return {"status": "started", "workflow_id": workflow_id}
        else:
            return {"error": "Failed to start workflow"}
            
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        return {"error": str(e)}

@app.get("/api/orchestration/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get detailed workflow status"""
    try:
        engine = get_orchestration_engine()
        status = await engine.get_workflow_status(workflow_id)
        return status
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        return {"error": str(e)}

@app.post("/api/orchestration/workflow/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow"""
    try:
        engine = get_orchestration_engine()
        success = await engine.cancel_workflow(workflow_id)
        
        return {"cancelled": success, "workflow_id": workflow_id}
        
    except Exception as e:
        logger.error(f"Error cancelling workflow: {e}")
        return {"error": str(e)}

@app.post("/api/orchestration/workflow/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause a running workflow"""
    try:
        engine = get_orchestration_engine()
        success = await engine.pause_workflow(workflow_id)
        
        return {"paused": success, "workflow_id": workflow_id}
        
    except Exception as e:
        logger.error(f"Error pausing workflow: {e}")
        return {"error": str(e)}

@app.post("/api/orchestration/workflow/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """Resume a paused workflow"""
    try:
        engine = get_orchestration_engine()
        success = await engine.resume_workflow(workflow_id)
        
        return {"resumed": success, "workflow_id": workflow_id}
        
    except Exception as e:
        logger.error(f"Error resuming workflow: {e}")
        return {"error": str(e)}

@app.get("/api/orchestration/metrics")
async def get_orchestration_metrics():
    """Get orchestration engine metrics"""
    try:
        engine = get_orchestration_engine()
        metrics = engine.get_metrics()
        
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}

# WebSocket endpoint for real-time orchestration updates
@app.websocket("/ws/orchestration")
async def orchestration_websocket(websocket: WebSocket):
    """WebSocket for real-time orchestration updates"""
    await websocket.accept()
    
    try:
        engine = get_orchestration_engine()
        
        # Add event handler for this WebSocket
        async def send_update(event):
            try:
                await websocket.send_json(event)
            except:
                pass  # Connection closed
        
        # Subscribe to all orchestration events
        for event_type in ['workflow_created', 'workflow_started', 'workflow_completed', 
                          'workflow_failed', 'task_started', 'task_completed', 'task_failed']:
            engine.add_event_handler(event_type, send_update)
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back for heartbeat
                await websocket.send_json({
                    "type": "heartbeat", 
                    "timestamp": datetime.now().isoformat()
                })
            except:
                break
                
    except Exception as e:
        logger.error(f"Orchestration WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
# Add conversational AI endpoints

@app.post("/api/ai/understand-request")
async def understand_user_request(request: Request):
    """Understand user intent from natural language"""
    try:
        body = await request.json()
        user_message = body.get('message', '')
        context = body.get('context', {})
        
        if not user_message:
            return {"error": "No message provided"}
        
        intent_engine = get_intent_engine()
        
        # Understand intent
        intent = await intent_engine.understand_user_request(user_message, context)
        
        # Get agent recommendations
        recommendations = await intent_engine.recommend_agents(intent)
        
        # Create conversation response
        response = await intent_engine.create_conversation_response(intent, recommendations)
        
        return response
        
    except Exception as e:
        logger.error(f"Error understanding user request: {e}")
        return {"error": str(e)}

@app.post("/api/ai/execute-intent")
async def execute_user_intent(request: Request, background_tasks: BackgroundTasks):
    """Execute user intent with recommended agents"""
    try:
        body = await request.json()
        
        intent_data = body.get('intent')
        recommendations_data = body.get('recommendations')
        execution_order = body.get('execution_order', [])
        user_confirmations = body.get('confirmations', {})
        
        if not intent_data or not recommendations_data:
            return {"error": "Intent and recommendations required"}
        
        # Create agent recommendations from data
        from ai.intent_engine import AgentRecommendation
        
        recommendations = []
        for rec_data in recommendations_data:
            rec = AgentRecommendation(
                agent_type=rec_data['type'],
                agent_config=rec_data.get('config', {}),
                priority=rec_data.get('priority', 50),
                estimated_time=rec_data.get('estimated_time', 'Unknown'),
                description=rec_data.get('description', ''),
                dependencies=rec_data.get('dependencies', [])
            )
            recommendations.append(rec)
        
        async def execute_intent_pipeline():
            """Background task for intent execution"""
            try:
                # Broadcast start
                await manager.broadcast({
                    "type": "intent_execution_started",
                    "intent_type": intent_data.get('type'),
                    "agents_count": len(recommendations),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Execute agent pipeline
                agent_factory = get_agent_factory()
                results = await agent_factory.execute_agent_pipeline(recommendations, execution_order)
                
                # Broadcast completion
                await manager.broadcast({
                    "type": "intent_execution_completed",
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info("Intent execution pipeline completed")
                
            except Exception as e:
                logger.error(f"Intent execution failed: {e}")
                await manager.broadcast({
                    "type": "intent_execution_failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Start background execution
        background_tasks.add_task(execute_intent_pipeline)
        
        return {
            "status": "started",
            "message": "Intent execution started",
            "agents_count": len(recommendations),
            "estimated_time": "15-60 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error executing user intent: {e}")
        return {"error": str(e)}

@app.get("/api/ai/conversation-history")
async def get_conversation_history():
    """Get conversation history"""
    try:
        intent_engine = get_intent_engine()
        
        return {
            "conversation_history": intent_engine.conversation_history[-10:],  # Last 10 messages
            "total_messages": len(intent_engine.conversation_history)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return {"error": str(e)}

@app.post("/api/ai/clarify-intent")
async def clarify_user_intent(request: Request):
    """Handle clarifying questions and refine intent"""
    try:
        body = await request.json()
        
        original_intent = body.get('original_intent')
        clarifications = body.get('clarifications', {})
        
        if not original_intent:
            return {"error": "Original intent required"}
        
        # Update intent with clarifications
        # This would involve re-analyzing with additional context
        intent_engine = get_intent_engine()
        
        # Create updated message with clarifications
        updated_message = f"Original request with clarifications: {json.dumps(clarifications)}"
        
        # Re-understand with additional context
        refined_intent = await intent_engine.understand_user_request(
            updated_message, 
            {'original_intent': original_intent, 'clarifications': clarifications}
        )
        
        # Get updated recommendations
        updated_recommendations = await intent_engine.recommend_agents(refined_intent)
        
        # Create updated response
        response = await intent_engine.create_conversation_response(refined_intent, updated_recommendations)
        
        return response
        
    except Exception as e:
        logger.error(f"Error clarifying intent: {e}")
        return {"error": str(e)}
    

# Add these endpoints to your existing dashboard/app.py

@app.get("/api/stats")
async def get_stats():
    """Get basic statistics"""
    try:
        # Try to get from database
        try:
            from database.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # Get basic counts
            associations = db_manager.get_recent_associations(limit=1000)
            total_associations = len(associations)
            
            ai_enhanced = len([a for a in associations if db_manager.association_to_dict(a).get('ai_enhanced')])
            with_websites = len([a for a in associations if db_manager.association_to_dict(a).get('official_website')])
            
            # Get recent discoveries (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_discoveries = len([a for a in associations if a.updated_at and a.updated_at > week_ago])
            
            return {
                "total_associations": total_associations,
                "ai_enhanced": ai_enhanced,
                "with_websites": with_websites,
                "recent_discoveries": recent_discoveries,
                "active_workflows": 0,  # Will be updated when orchestration is active
                "tasks_executed": 0,
                "avg_execution_time": 0,
                "success_rate": 100
            }
            
        except Exception as db_error:
            logger.warning(f"Database not available for stats: {db_error}")
            
            # Return default stats
            return {
                "total_associations": 0,
                "ai_enhanced": 0,
                "with_websites": 0,
                "recent_discoveries": 0,
                "active_workflows": 0,
                "tasks_executed": 0,
                "avg_execution_time": 0,
                "success_rate": 0
            }
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e)}

@app.get("/api/associations")
async def get_associations(limit: int = 10):
    """Get associations list"""
    try:
        from database.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        associations = db_manager.get_recent_associations(limit=limit)
        
        associations_data = []
        for assoc in associations:
            assoc_dict = db_manager.association_to_dict(assoc)
            associations_data.append(assoc_dict)
        
        return {
            "associations": associations_data,
            "total": len(associations_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting associations: {e}")
        return {
            "associations": [],
            "total": 0,
            "error": str(e)
        }

@app.get("/api/industry-configs")
async def get_industry_configs():
    """Get all industry configurations"""
    try:
        from config.industry_configs import IndustryConfigManager
        
        config_manager = IndustryConfigManager()
        configs = config_manager.get_all_configs()
        
        industries = []
        for industry_type, config in configs.items():
            industries.append({
                "type": industry_type,
                "name": config.name,
                "description": config.description,
                "data_sources": [{"name": ds.name, "type": ds.source_type} for ds in config.data_sources],
                "search_keywords": config.search_keywords,
                "output_fields": config.output_fields,
                "company_types": getattr(config, 'company_types', [])
            })
        
        return {
            "industries": industries,
            "total": len(industries)
        }
        
    except Exception as e:
        logger.error(f"Error getting industry configs: {e}")
        return {"error": str(e)}

@app.get("/api/market-intelligence")
async def get_market_intelligence():
    """Get market intelligence data"""
    try:
        # Try to load from recent reports or database
        import os
        import json
        
        # Look for market intelligence files
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if "market_intelligence" in filename.lower() and filename.endswith('.json'):
                    filepath = os.path.join(reports_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            return {"market_intelligence": data}
                    except Exception as e:
                        continue
        
        # Return placeholder data
        return {
            "market_intelligence": {
                "market_overview": "Market intelligence will be available after running discovery analysis.",
                "key_insights": [
                    "Run discovery to generate market insights",
                    "AI analysis will provide competitive intelligence",
                    "Comprehensive reports will include strategic recommendations"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting market intelligence: {e}")
        return {"error": str(e)}

@app.get("/api/comprehensive-insights")
async def get_comprehensive_insights():
    """Get comprehensive insights"""
    try:
        # Try to load from recent analysis
        import os
        import json
        
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if "comprehensive" in filename.lower() and filename.endswith('.json'):
                    filepath = os.path.join(reports_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            return {"insights": data}
                    except Exception as e:
                        continue
        
        # Return placeholder
        return {
            "insights": {
                "digital_maturity": "Comprehensive insights will be available after running AI analysis.",
                "market_opportunities": "Discovery analysis will identify market opportunities and trends.",
                "strategic_recommendations": "AI-powered recommendations will be generated from your data analysis."
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting comprehensive insights: {e}")
        return {"error": str(e)}

@app.get("/api/arc-returns")
async def get_arc_returns():
    """Get ARC returns data"""
    try:
        # Try to get from database or files
        from database.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        associations = db_manager.get_recent_associations(limit=100)
        
        # Filter for Scottish associations with ARC data
        arc_returns = []
        for assoc in associations:
            assoc_dict = db_manager.association_to_dict(assoc)
            if assoc_dict.get('region', '').lower() in ['scotland', 'scottish']:
                arc_returns.append({
                    "name": assoc_dict.get('name', 'Unknown'),
                    "registration_number": assoc_dict.get('registration_number', 'N/A'),
                    "data_source": assoc_dict.get('data_source', 'Database'),
                    "stock_units": assoc_dict.get('stock_units', 0),
                    "satisfaction_score": assoc_dict.get('satisfaction_score', 'N/A'),
                    "year": assoc_dict.get('year', '2024')
                })
        
        return {
            "arc_returns": arc_returns,
            "total_associations": len(arc_returns),
            "total_data_sources": len(set(arc['data_source'] for arc in arc_returns)),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting ARC returns: {e}")
        return {
            "arc_returns": [],
            "total_associations": 0,
            "total_data_sources": 0,
            "last_updated": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/api/download-arc-returns")
async def download_arc_returns():
    """Download ARC returns as CSV"""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv
        
        # Get ARC data
        arc_response = await get_arc_returns()
        arc_returns = arc_response.get('arc_returns', [])
        
        if not arc_returns:
            return {"error": "No ARC returns data available"}
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['name', 'registration_number', 'data_source', 'stock_units', 'satisfaction_score', 'year'])
        writer.writeheader()
        writer.writerows(arc_returns)
        
        # Return as download
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=scottish_arc_returns.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error downloading ARC returns: {e}")
        return {"error": str(e)}
    

# Add this endpoint anywhere in your app.py file (I recommend near the top after your existing endpoints)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check database
        try:
            from database.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            associations = db_manager.get_recent_associations(limit=1)
            health_status["components"]["database"] = "available"
        except Exception as e:
            health_status["components"]["database"] = f"unavailable: {str(e)}"
        
        # Check Vertex AI
        try:
            from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
            vertex_ai = ProductionVertexAIAgent()
            health_status["components"]["vertex_ai"] = "available"
        except Exception as e:
            health_status["components"]["vertex_ai"] = f"unavailable: {str(e)}"
        
        # Check industry configs
        try:
            from config.industry_configs import IndustryConfigManager
            config_manager = IndustryConfigManager()
            configs = config_manager.get_all_configs()
            health_status["components"]["industry_configs"] = f"available ({len(configs)} industries)"
        except Exception as e:
            health_status["components"]["industry_configs"] = f"unavailable: {str(e)}"
        
        # Check reports directory
        import os
        if os.path.exists("reports"):
            report_count = len([f for f in os.listdir("reports") if f.endswith(('.csv', '.json', '.html'))])
            health_status["components"]["reports"] = f"available ({report_count} files)"
        else:
            health_status["components"]["reports"] = "directory not found"
        
        # Check orchestration system
        try:
            from orchestration.core import OrchestrationEngine
            health_status["components"]["orchestration"] = "available"
        except Exception as e:
            health_status["components"]["orchestration"] = f"unavailable: {str(e)}"
        
        # Check AI intent engine
        try:
            from ai.intent_engine import get_intent_engine
            intent_engine = get_intent_engine()
            health_status["components"]["ai_intent_engine"] = "available"
        except Exception as e:
            health_status["components"]["ai_intent_engine"] = f"unavailable: {str(e)}"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
@app.post("/api/discover-regulatory-documents")
async def discover_regulatory_documents(request: Request, background_tasks: BackgroundTasks):
    """Discover regulatory documents for an industry"""
    try:
        body = await request.json()
        
        industry = body.get('industry', '')
        document_types = body.get('document_types', ['legislation', 'guidance', 'policy', 'standards', 'reports'])
        regions = body.get('regions', ['uk'])
        keywords = body.get('keywords', [])
        download_documents = body.get('download_documents', False)
        download_limit = body.get('download_limit', 50)
        save_to_database = body.get('save_to_database', True)
        
        if not industry:
            return {"error": "Industry is required"}
        
        async def discover_documents_task():
            """Background task for document discovery"""
            try:
                # Broadcast start
                await manager.broadcast({
                    "type": "regulatory_discovery_started",
                    "industry": industry,
                    "document_types": document_types,
                    "regions": regions,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Get regulatory agent
                regulatory_agent = get_regulatory_agent()
                
                # Discover documents
                logger.info(f"Starting regulatory document discovery for {industry}")
                documents = await regulatory_agent.discover_regulatory_documents(
                    industry=industry,
                    document_types=document_types,
                    regions=regions,
                    keywords=keywords
                )
                
                # Broadcast progress
                await manager.broadcast({
                    "type": "regulatory_discovery_progress",
                    "message": f"Discovered {len(documents)} documents",
                    "documents_found": len(documents),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Download and process documents if requested
                processed_documents = documents
                if download_documents and documents:
                    logger.info(f"Downloading and processing up to {download_limit} documents")
                    processed_documents = await regulatory_agent.download_and_process_documents(
                        documents, download_limit
                    )
                    
                    await manager.broadcast({
                        "type": "regulatory_discovery_progress",
                        "message": f"Downloaded and processed {len(processed_documents)} documents",
                        "documents_processed": len(processed_documents),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Save to database if requested
                if save_to_database and processed_documents:
                    doc_manager = get_regulatory_doc_manager()
                    for doc in processed_documents:
                        doc_manager.save_document(doc)
                    
                    await manager.broadcast({
                        "type": "regulatory_discovery_progress",
                        "message": f"Saved {len(processed_documents)} documents to database",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Generate discovery report
                report = regulatory_agent.generate_discovery_report(processed_documents, industry)
                
                # Save report
                report_filename = f"regulatory_discovery_{industry}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                os.makedirs("reports", exist_ok=True)
                with open(f"reports/{report_filename}", 'w') as f:
                    json.dump(report, f, indent=2)
                
                # Broadcast completion
                await manager.broadcast({
                    "type": "regulatory_discovery_completed",
                    "industry": industry,
                    "total_documents": len(processed_documents),
                    "report_filename": report_filename,
                    "high_priority_count": len([d for d in processed_documents if d.get('urgency_level') == 'high']),
                    "mandatory_count": len([d for d in processed_documents if d.get('compliance_impact') == 'mandatory']),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Regulatory document discovery completed for {industry}")
                
            except Exception as e:
                logger.error(f"Regulatory document discovery failed: {e}")
                await manager.broadcast({
                    "type": "regulatory_discovery_failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Start background task
        background_tasks.add_task(discover_documents_task)
        
        return {
            "status": "started",
            "message": f"Regulatory document discovery started for {industry}",
            "industry": industry,
            "document_types": document_types,
            "regions": regions,
            "download_documents": download_documents
        }
        
    except Exception as e:
        logger.error(f"Error starting regulatory document discovery: {e}")
        return {"error": str(e)}

@app.get("/api/regulatory-documents")
async def get_regulatory_documents(
    document_type: str = None,
    regulatory_authority: str = None,
    jurisdiction: str = None,
    urgency_level: str = None,
    compliance_impact: str = None,
    industry_relevance: str = None,
    limit: int = 100
):
    """Get regulatory documents with filtering"""
    try:
        doc_manager = get_regulatory_doc_manager()
        
        documents = doc_manager.get_documents(
            document_type=document_type,
            regulatory_authority=regulatory_authority,
            jurisdiction=jurisdiction,
            urgency_level=urgency_level,
            compliance_impact=compliance_impact,
            industry_relevance=industry_relevance,
            limit=limit
        )
        
        return {
            "documents": documents,
            "total": len(documents),
            "filters_applied": {
                "document_type": document_type,
                "regulatory_authority": regulatory_authority,
                "jurisdiction": jurisdiction,
                "urgency_level": urgency_level,
                "compliance_impact": compliance_impact,
                "industry_relevance": industry_relevance
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting regulatory documents: {e}")
        return {"error": str(e)}

@app.get("/api/regulatory-documents/search")
async def search_regulatory_documents(q: str, limit: int = 50):
    """Search regulatory documents"""
    try:
        if not q:
            return {"error": "Search query is required"}
        
        doc_manager = get_regulatory_doc_manager()
        documents = doc_manager.search_documents(q, limit)
        
        return {
            "documents": documents,
            "total": len(documents),
            "search_query": q
        }
        
    except Exception as e:
        logger.error(f"Error searching regulatory documents: {e}")
        return {"error": str(e)}

@app.get("/api/regulatory-documents/{document_id}")
async def get_regulatory_document(document_id: int):
    """Get a specific regulatory document with full content"""
    try:
        doc_manager = get_regulatory_doc_manager()
        
        # Get document metadata
        documents = doc_manager.get_documents(limit=1)
        document = None
        for doc in documents:
            if doc['id'] == document_id:
                document = doc
                break
        
        if not document:
            return {"error": "Document not found"}
        
        # Get full text content
        text_content = doc_manager.get_document_content(document_id)
        if text_content:
            document['text_content'] = text_content
        
        return {
            "document": document
        }
        
    except Exception as e:
        logger.error(f"Error getting regulatory document {document_id}: {e}")
        return {"error": str(e)}

@app.get("/api/regulatory-documents/compliance-summary")
async def get_compliance_summary():
    """Get compliance summary statistics"""
    try:
        doc_manager = get_regulatory_doc_manager()
        summary = doc_manager.get_compliance_summary()
        
        return {
            "compliance_summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}")
        return {"error": str(e)}

@app.get("/api/regulatory-documents/export")
async def export_regulatory_documents():
    """Export regulatory documents to CSV"""
    try:
        from fastapi.responses import FileResponse
        
        doc_manager = get_regulatory_doc_manager()
        filename = doc_manager.export_documents_to_csv()
        
        return FileResponse(
            filename,
            media_type="text/csv",
            filename=f"regulatory_documents_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
    except Exception as e:
        logger.error(f"Error exporting regulatory documents: {e}")
        return {"error": str(e)}

@app.post("/api/regulatory-documents/{document_id}/compliance-tracking")
async def add_compliance_tracking(document_id: int, request: Request):
    """Add compliance tracking for a document"""
    try:
        body = await request.json()
        
        organization_id = body.get('organization_id')
        compliance_status = body.get('compliance_status', 'pending')
        due_date = body.get('due_date')
        notes = body.get('notes', '')
        
        if not organization_id:
            return {"error": "Organization ID is required"}
        
        doc_manager = get_regulatory_doc_manager()
        tracking_id = doc_manager.add_compliance_tracking(
            document_id, organization_id, compliance_status, due_date, notes
        )
        
        return {
            "tracking_id": tracking_id,
            "message": "Compliance tracking added successfully"
        }
        
    except Exception as e:
        logger.error(f"Error adding compliance tracking: {e}")
        return {"error": str(e)}

@app.get("/api/regulatory-authorities")
async def get_regulatory_authorities():
    """Get list of regulatory authorities"""
    try:
        doc_manager = get_regulatory_doc_manager()
        
        # Get unique regulatory authorities from database
        with sqlite3.connect(doc_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT regulatory_authority, COUNT(*) as document_count
                FROM regulatory_documents 
                WHERE regulatory_authority IS NOT NULL AND regulatory_authority != ''
                GROUP BY regulatory_authority
                ORDER BY document_count DESC
            ''')
            
            authorities = [
                {"name": row[0], "document_count": row[1]} 
                for row in cursor.fetchall()
            ]
        
        return {
            "regulatory_authorities": authorities,
            "total": len(authorities)
        }
        
    except Exception as e:
        logger.error(f"Error getting regulatory authorities: {e}")
        return {"error": str(e)}

@app.get("/api/document-types")
async def get_document_types():
    """Get available document types"""
    try:
        doc_manager = get_regulatory_doc_manager()
        
        # Get unique document types from database
        with sqlite3.connect(doc_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT document_type, COUNT(*) as document_count
                FROM regulatory_documents 
                WHERE document_type IS NOT NULL AND document_type != ''
                GROUP BY document_type
                ORDER BY document_count DESC
            ''')
            
            doc_types = [
                {"type": row[0], "document_count": row[1]} 
                for row in cursor.fetchall()
            ]
        
        return {
            "document_types": doc_types,
            "total": len(doc_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting document types: {e}")
        return {"error": str(e)}
    
@app.post("/api/dashboard-ai/process-request")
async def process_dashboard_ai_request(request: Request, background_tasks: BackgroundTasks):
    """Process AI dashboard modification requests"""
    try:
        body = await request.json()
        
        user_message = body.get('message', '')
        context = body.get('context', {})
        
        if not user_message:
            return {"error": "Message is required"}
        
        # Get dashboard AI controller
        ai_controller = get_dashboard_ai_controller()
        
        # Process request
        response = await ai_controller.process_dashboard_request(user_message, context)
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "dashboard_ai_response",
            "user_message": user_message,
            "ai_response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing dashboard AI request: {e}")
        return {"error": str(e)}

@app.get("/api/dashboard-ai/conversation-history")
async def get_dashboard_ai_conversation_history():
    """Get AI conversation history"""
    try:
        ai_controller = get_dashboard_ai_controller()
        history = ai_controller.get_conversation_history()
        
        return {
            "conversation_history": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return {"error": str(e)}

@app.delete("/api/dashboard-ai/conversation-history")
async def clear_dashboard_ai_conversation_history():
    """Clear AI conversation history"""
    try:
        ai_controller = get_dashboard_ai_controller()
        ai_controller.clear_conversation_history()
        
        return {"message": "Conversation history cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        return {"error": str(e)}

@app.get("/api/dashboard-ai/generated-components")
async def get_generated_components():
    """Get information about AI-generated components"""
    try:
        ai_controller = get_dashboard_ai_controller()
        components = ai_controller.get_generated_components()
        
        return components
        
    except Exception as e:
        logger.error(f"Error getting generated components: {e}")
        return {"error": str(e)}

@app.post("/api/dashboard-ai/create-component")
async def create_dashboard_component(request: Request, background_tasks: BackgroundTasks):
    """Create a new dashboard component using AI"""
    try:
        body = await request.json()
        
        component_description = body.get('description', '')
        component_type = body.get('type', 'general')
        requirements = body.get('requirements', {})
        
        if not component_description:
            return {"error": "Component description is required"}
        
        async def create_component_task():
            try:
                ai_controller = get_dashboard_ai_controller()
                
                # Create AI request for component creation
                ai_request = f"Create a new dashboard component: {component_description}. Type: {component_type}. Requirements: {json.dumps(requirements)}"
                
                response = await ai_controller.process_dashboard_request(ai_request, {
                    'component_creation': True,
                    'component_type': component_type,
                    'requirements': requirements
                })
                
                await manager.broadcast({
                    "type": "component_created",
                    "component_description": component_description,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Component creation failed: {e}")
                await manager.broadcast({
                    "type": "component_creation_failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        background_tasks.add_task(create_component_task)
        
        return {
            "status": "started",
            "message": "Component creation started",
            "description": component_description
        }
        
    except Exception as e:
        logger.error(f"Error starting component creation: {e}")
        return {"error": str(e)}

@app.post("/api/dashboard-ai/create-agent")
async def create_dashboard_agent(request: Request, background_tasks: BackgroundTasks):
    """Create a new intelligent agent using AI"""
    try:
        body = await request.json()
        
        agent_description = body.get('description', '')
        agent_capabilities = body.get('capabilities', [])
        agent_config = body.get('config', {})
        
        if not agent_description:
            return {"error": "Agent description is required"}
        
        async def create_agent_task():
            try:
                ai_controller = get_dashboard_ai_controller()
                
                # Create AI request for agent creation
                ai_request = f"Create a new intelligent agent: {agent_description}. Capabilities: {', '.join(agent_capabilities)}. Configuration: {json.dumps(agent_config)}"
                
                response = await ai_controller.process_dashboard_request(ai_request, {
                    'agent_creation': True,
                    'agent_capabilities': agent_capabilities,
                    'agent_config': agent_config
                })
                
                await manager.broadcast({
                    "type": "agent_created",
                    "agent_description": agent_description,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Agent creation failed: {e}")
                await manager.broadcast({
                    "type": "agent_creation_failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        background_tasks.add_task(create_agent_task)
        
        return {
            "status": "started",
            "message": "Agent creation started",
            "description": agent_description
        }
        
    except Exception as e:
        logger.error(f"Error starting agent creation: {e}")
        return {"error": str(e)}

@app.post("/api/dashboard-ai/modify-dashboard")
async def modify_dashboard(request: Request, background_tasks: BackgroundTasks):
    """Modify dashboard based on AI analysis"""
    try:
        body = await request.json()
        
        modification_request = body.get('request', '')
        target_components = body.get('components', [])
        modification_type = body.get('type', 'enhancement')
        
        if not modification_request:
            return {"error": "Modification request is required"}
        
        async def modify_dashboard_task():
            try:
                ai_controller = get_dashboard_ai_controller()
                
                response = await ai_controller.process_dashboard_request(modification_request, {
                    'dashboard_modification': True,
                    'target_components': target_components,
                    'modification_type': modification_type
                })
                
                await manager.broadcast({
                    "type": "dashboard_modified",
                    "modification_request": modification_request,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Dashboard modification failed: {e}")
                await manager.broadcast({
                    "type": "dashboard_modification_failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        background_tasks.add_task(modify_dashboard_task)
        
        return {
            "status": "started",
            "message": "Dashboard modification started",
            "request": modification_request
        }
        
    except Exception as e:
        logger.error(f"Error starting dashboard modification: {e}")
        return {"error": str(e)}

@app.get("/api/voice/capabilities")
async def get_voice_capabilities():
    """Get voice interface capabilities"""
    try:
        return {
            "voice_supported": True,
            "features": {
                "speech_recognition": True,
                "speech_synthesis": True,
                "continuous_listening": True,
                "wake_word_detection": True,
                "voice_commands": True,
                "multi_language": True,
                "voice_settings": True
            },
            "supported_languages": [
                "en-US", "en-GB", "en-AU", "en-CA",
                "es-ES", "es-MX", "fr-FR", "de-DE",
                "it-IT", "pt-BR", "ja-JP", "ko-KR",
                "zh-CN", "zh-TW", "ru-RU", "ar-SA"
            ],
            "voice_commands": [
                "hey dashboard",
                "stop listening",
                "start listening",
                "clear conversation",
                "refresh dashboard",
                "speak slower",
                "speak faster",
                "show help"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting voice capabilities: {e}")
        return {"error": str(e)}

@app.post("/api/voice/settings")
async def update_voice_settings(request: Request):
    """Update voice interface settings"""
    try:
        body = await request.json()
        
        # Voice settings would typically be stored per user
        # For now, we'll just return success
        
        return {
            "message": "Voice settings updated",
            "settings": body
        }
        
    except Exception as e:
        logger.error(f"Error updating voice settings: {e}")
        return {"error": str(e)}

@app.get("/api/voice/settings")
async def get_voice_settings():
    """Get voice interface settings"""
    try:
        # Return default settings
        return {
            "settings": {
                "language": "en-US",
                "voiceSpeed": 1.0,
                "voicePitch": 1.0,
                "voiceVolume": 1.0,
                "autoSpeak": True,
                "wakeWord": "hey dashboard",
                "continuousListening": False,
                "noiseReduction": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting voice settings: {e}")
        return {"error": str(e)}