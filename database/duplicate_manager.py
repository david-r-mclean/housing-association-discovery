"""
Smart Duplicate Detection and Management
Prevents re-processing of previously analyzed associations
"""

from sqlalchemy.orm import Session
from database.models import HousingAssociation, DiscoveryRun
from database.database_manager import DatabaseManager
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DuplicateManager:
    """Manages duplicate detection and incremental updates"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def get_existing_associations(self, region: str = None) -> Dict[str, Dict]:
        """Get all existing associations from database"""
        session = self.db_manager.get_session()
        
        try:
            query = session.query(HousingAssociation)
            if region:
                query = query.filter(HousingAssociation.region.ilike(f'%{region}%'))
            
            existing = query.all()
            
            # Create lookup dictionary by company_number and name
            existing_dict = {}
            for assoc in existing:
                if assoc.company_number:
                    existing_dict[assoc.company_number] = {
                        'id': assoc.id,
                        'name': assoc.name or assoc.company_name,
                        'last_updated': assoc.updated_at,
                        'data_collection_date': assoc.data_collection_date,
                        'ai_enhanced': hasattr(assoc, 'ai_insights') and assoc.ai_insights is not None
                    }
                
                # Also index by name for associations without company numbers
                if assoc.name:
                    name_key = self._normalize_name(assoc.name)
                    if name_key not in existing_dict:
                        existing_dict[name_key] = {
                            'id': assoc.id,
                            'name': assoc.name,
                            'last_updated': assoc.updated_at,
                            'data_collection_date': assoc.data_collection_date,
                            'ai_enhanced': hasattr(assoc, 'ai_insights') and assoc.ai_insights is not None
                        }
            
            logger.info(f"Found {len(existing_dict)} existing associations in database")
            return existing_dict
            
        finally:
            session.close()
    
    def filter_new_associations(self, discovered_associations: List[Dict], 
                              region: str = None, 
                              force_refresh: bool = False,
                              max_age_days: int = 30) -> Dict:
        """Filter out associations that don't need processing"""
        
        existing = self.get_existing_associations(region)
        
        new_associations = []
        existing_associations = []
        stale_associations = []
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for assoc in discovered_associations:
            company_number = assoc.get('company_number')
            name = assoc.get('name', assoc.get('company_name'))
            name_key = self._normalize_name(name) if name else None
            
            # Check if exists by company number or name
            existing_record = None
            if company_number and company_number in existing:
                existing_record = existing[company_number]
            elif name_key and name_key in existing:
                existing_record = existing[name_key]
            
            if existing_record:
                # Check if data is stale
                last_updated = existing_record.get('last_updated')
                if force_refresh or (last_updated and last_updated < cutoff_date):
                    stale_associations.append({
                        'association': assoc,
                        'existing_id': existing_record['id'],
                        'last_updated': last_updated,
                        'reason': 'force_refresh' if force_refresh else 'stale_data'
                    })
                else:
                    existing_associations.append({
                        'association': assoc,
                        'existing_id': existing_record['id'],
                        'last_updated': last_updated,
                        'ai_enhanced': existing_record.get('ai_enhanced', False)
                    })
            else:
                new_associations.append(assoc)
        
        result = {
            'new': new_associations,
            'existing': existing_associations,
            'stale': stale_associations,
            'summary': {
                'total_discovered': len(discovered_associations),
                'new_count': len(new_associations),
                'existing_count': len(existing_associations),
                'stale_count': len(stale_associations),
                'processing_needed': len(new_associations) + len(stale_associations)
            }
        }
        
        logger.info(f"Duplicate analysis: {result['summary']}")
        return result
    
    def get_associations_needing_ai_enhancement(self, region: str = None) -> List[Dict]:
        """Get associations that haven't been AI-enhanced yet"""
        session = self.db_manager.get_session()
        
        try:
            query = session.query(HousingAssociation)
            if region:
                query = query.filter(HousingAssociation.region.ilike(f'%{region}%'))
            
            # Filter for associations without AI insights
            # This would need to be adapted based on how you store AI insights
            associations = query.all()
            
            needs_ai = []
            for assoc in associations:
                # Check if AI insights are missing or old
                needs_enhancement = True
                
                # You might store AI insights in a JSON field or separate table
                # For now, we'll assume they need enhancement if no recent AI analysis
                if hasattr(assoc, 'ai_analysis_timestamp'):
                    ai_date = getattr(assoc, 'ai_analysis_timestamp')
                    if ai_date and ai_date > datetime.now() - timedelta(days=7):
                        needs_enhancement = False
                
                if needs_enhancement:
                    needs_ai.append({
                        'id': assoc.id,
                        'company_number': assoc.company_number,
                        'name': assoc.name or assoc.company_name,
                        'official_website': assoc.official_website,
                        'last_updated': assoc.updated_at
                    })
            
            logger.info(f"Found {len(needs_ai)} associations needing AI enhancement")
            return needs_ai
            
        finally:
            session.close()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize association name for comparison"""
        if not name:
            return ""
        
        # Remove common suffixes and normalize
        normalized = name.upper()
        suffixes = [
            'LIMITED', 'LTD', 'LTD.', 'HOUSING ASSOCIATION', 
            'HOUSING ASSOCIATION LIMITED', 'ASSOCIATION', 'GROUP'
        ]
        
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Remove special characters
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        return normalized.strip()
    
    def log_discovery_session(self, region: str, results: Dict, ai_enhanced: bool = False):
        """Log the discovery session results"""
        session = self.db_manager.get_session()
        
        try:
            run = DiscoveryRun(
                region=region,
                total_discovered=results['summary']['total_discovered'],
                total_enriched=results['summary']['processing_needed'],
                success=True,
                ai_enhanced=ai_enhanced,
                new_associations=results['summary']['new_count'],
                updated_associations=results['summary']['stale_count'],
                execution_time_minutes=0  # You can track this
            )
            session.add(run)
            session.commit()
            
            logger.info(f"Discovery session logged for {region}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log discovery session: {e}")
        finally:
            session.close()

# Usage example
async def smart_discovery_example():
    """Example of using smart duplicate detection"""
    
    duplicate_manager = DuplicateManager()
    
    # Get discovered associations (your existing discovery logic)
    discovered = [
        {'company_number': 'SP12345', 'name': 'Test Housing Association'},
        {'company_number': 'SP67890', 'name': 'Another Housing Association'}
    ]
    
    # Filter for processing
    filtered = duplicate_manager.filter_new_associations(
        discovered, 
        region='scottish',
        max_age_days=30
    )
    
    print(f"Processing needed for {filtered['summary']['processing_needed']} associations")
    print(f"Skipping {filtered['summary']['existing_count']} up-to-date associations")
    
    # Process only new and stale associations
    to_process = filtered['new'] + [item['association'] for item in filtered['stale']]
    
    return to_process

if __name__ == "__main__":
    import asyncio
    asyncio.run(smart_discovery_example())