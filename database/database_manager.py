from sqlalchemy.orm import Session
from database.models import HousingAssociation, DiscoveryRun, create_engine_and_session
from typing import List, Dict, Optional
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self):
        self.engine, self.SessionLocal = create_engine_and_session()
    
    def get_session(self):
        return self.SessionLocal()
    
    def save_housing_associations(self, associations: List[Dict], region: str) -> int:
        """Save housing associations to database"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for assoc_data in associations:
                # Check if association already exists
                existing = session.query(HousingAssociation).filter_by(
                    company_number=assoc_data.get('company_number')
                ).first()
                
                if existing:
                    # Update existing record
                    self._update_association(existing, assoc_data)
                    print(f"Updated: {assoc_data.get('company_name', assoc_data.get('name'))}")
                else:
                    # Create new record
                    association = self._create_association(assoc_data)
                    session.add(association)
                    print(f"Added: {assoc_data.get('company_name', assoc_data.get('name'))}")
                
                saved_count += 1
            
            session.commit()
            print(f"Successfully saved {saved_count} housing associations to database")
            
        except Exception as e:
            session.rollback()
            print(f"Error saving to database: {e}")
            raise
        finally:
            session.close()
        
        return saved_count
    
    def _create_association(self, data: Dict) -> HousingAssociation:
        """Create HousingAssociation object from data dictionary"""
        return HousingAssociation(
            company_number=data.get('company_number'),
            company_name=data.get('company_name', data.get('name')),
            name=data.get('name'),
            company_status=data.get('company_status'),
            incorporation_date=data.get('incorporation_date', data.get('date_of_creation')),
            company_type=data.get('company_type', data.get('type')),
            registered_office_address=data.get('registered_office_address'),
            region=data.get('region'),
            source=data.get('source'),
            regulator_url=data.get('regulator_url'),
            sic_codes=data.get('sic_codes', []),
            officers_count=data.get('officers_count', 0),
            recent_filings=data.get('recent_filings', 0),
            last_filing_date=data.get('last_filing_date'),
            official_website=data.get('official_website'),
            phone_numbers=data.get('phone_numbers', []),
            email_addresses=data.get('email_addresses', []),
            ceo_name=data.get('ceo_name'),
            social_media=data.get('social_media', {}),
            twitter_followers=data.get('twitter_followers'),
            facebook_likes=data.get('facebook_likes'),
            linkedin_followers=data.get('linkedin_followers'),
            social_media_activity_score=data.get('social_media_activity_score', 0),
            website_has_search=data.get('website_has_search', False),
            website_has_tenant_portal=data.get('website_has_tenant_portal', False),
            website_has_online_services=data.get('website_has_online_services', False),
            website_responsive=data.get('website_responsive', False),
            arc_returns_found=data.get('arc_returns_found', False),
            latest_return_year=data.get('latest_return_year'),
            total_units=data.get('total_units'),
            rental_income=data.get('rental_income'),
            operating_margin=data.get('operating_margin'),
            governance_rating=data.get('governance_rating'),
            viability_rating=data.get('viability_rating'),
            annual_report_available=data.get('annual_report_available', False),
            annual_report_url=data.get('annual_report_url'),
            housing_units=data.get('housing_units'),
            data_collection_date=datetime.now()
        )
    
    def _update_association(self, existing: HousingAssociation, data: Dict):
        """Update existing association with new data"""
        # Update all fields with new data
        for key, value in data.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        
        existing.updated_at = datetime.now()
        existing.data_collection_date = datetime.now()
    
    def get_all_associations(self, region: Optional[str] = None) -> List[HousingAssociation]:
        """Get all housing associations, optionally filtered by region"""
        session = self.get_session()
        
        try:
            query = session.query(HousingAssociation)
            if region:
                query = query.filter(HousingAssociation.region == region)
            
            return query.all()
        finally:
            session.close()
    
    def get_association_by_company_number(self, company_number: str) -> Optional[HousingAssociation]:
        """Get association by company number"""
        session = self.get_session()
        
        try:
            return session.query(HousingAssociation).filter_by(company_number=company_number).first()
        finally:
            session.close()
    
    def log_discovery_run(self, region: str, total_discovered: int, total_enriched: int, 
                         success: bool, error_message: str = None, execution_time: float = None):
        """Log discovery run statistics"""
        session = self.get_session()
        
        try:
            run = DiscoveryRun(
                region=region,
                total_discovered=total_discovered,
                total_enriched=total_enriched,
                success=success,
                error_message=error_message,
                execution_time_minutes=execution_time
            )
            session.add(run)
            session.commit()
            print(f"Discovery run logged: {total_discovered} discovered, {total_enriched} enriched")
        except Exception as e:
            session.rollback()
            print(f"Error logging discovery run: {e}")
        finally:
            session.close()
    
    def export_to_dict(self, region: Optional[str] = None) -> List[Dict]:
        """Export associations to dictionary format for compatibility"""
        associations = self.get_all_associations(region)
        
        result = []
        for assoc in associations:
            data = {
                'company_number': assoc.company_number,
                'company_name': assoc.company_name,
                'name': assoc.name,
                'company_status': assoc.company_status,
                'incorporation_date': assoc.incorporation_date,
                'company_type': assoc.company_type,
                'registered_office_address': assoc.registered_office_address,
                'region': assoc.region,
                'source': assoc.source,
                'regulator_url': assoc.regulator_url,
                'sic_codes': assoc.sic_codes,
                'officers_count': assoc.officers_count,
                'recent_filings': assoc.recent_filings,
                'last_filing_date': assoc.last_filing_date,
                'official_website': assoc.official_website,
                'phone_numbers': assoc.phone_numbers,
                'email_addresses': assoc.email_addresses,
                'ceo_name': assoc.ceo_name,
                'social_media': assoc.social_media,
                'twitter_followers': assoc.twitter_followers,
                'facebook_likes': assoc.facebook_likes,
                'linkedin_followers': assoc.linkedin_followers,
                'social_media_activity_score': assoc.social_media_activity_score,
                'website_has_search': assoc.website_has_search,
                'website_has_tenant_portal': assoc.website_has_tenant_portal,
                'website_has_online_services': assoc.website_has_online_services,
                'website_responsive': assoc.website_responsive,
                'arc_returns_found': assoc.arc_returns_found,
                'latest_return_year': assoc.latest_return_year,
                'total_units': assoc.total_units,
                'rental_income': assoc.rental_income,
                'operating_margin': assoc.operating_margin,
                'governance_rating': assoc.governance_rating,
                'viability_rating': assoc.viability_rating,
                'annual_report_available': assoc.annual_report_available,
                'annual_report_url': assoc.annual_report_url,
                'housing_units': assoc.housing_units,
                'created_at': assoc.created_at.isoformat() if assoc.created_at else None,
                'updated_at': assoc.updated_at.isoformat() if assoc.updated_at else None,
                'data_collection_date': assoc.data_collection_date.isoformat() if assoc.data_collection_date else None
            }
            result.append(data)
        
        return result