from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('config/api_keys.env')

Base = declarative_base()

class HousingAssociation(Base):
    __tablename__ = 'housing_associations'
    
    id = Column(Integer, primary_key=True)
    
    # Basic company information
    company_number = Column(String(20), unique=True, index=True)
    company_name = Column(String(500), nullable=False, index=True)
    name = Column(String(500))  # Original discovered name
    company_status = Column(String(50))
    incorporation_date = Column(String(20))
    company_type = Column(String(100))
    
    # Address information
    registered_office_address = Column(JSON)
    
    # Regulator information
    region = Column(String(50), index=True)
    source = Column(String(200))
    regulator_url = Column(Text)
    
    # Company details
    sic_codes = Column(JSON)
    officers_count = Column(Integer)
    recent_filings = Column(Integer)
    last_filing_date = Column(String(20))
    
    # Website and digital presence
    official_website = Column(Text)
    phone_numbers = Column(JSON)
    email_addresses = Column(JSON)
    ceo_name = Column(String(200))
    
    # Social media
    social_media = Column(JSON)
    twitter_followers = Column(Integer)
    facebook_likes = Column(Integer)
    linkedin_followers = Column(Integer)
    social_media_activity_score = Column(Float)
    
    # Website features
    website_has_search = Column(Boolean)
    website_has_tenant_portal = Column(Boolean)
    website_has_online_services = Column(Boolean)
    website_responsive = Column(Boolean)
    
    # Regulatory data
    arc_returns_found = Column(Boolean)
    latest_return_year = Column(String(10))
    total_units = Column(Integer)
    rental_income = Column(Float)
    operating_margin = Column(Float)
    governance_rating = Column(String(10))
    viability_rating = Column(String(10))
    annual_report_available = Column(Boolean)
    annual_report_url = Column(Text)
    
    # Housing units
    housing_units = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_collection_date = Column(DateTime)
    
    def __repr__(self):
        return f"<HousingAssociation(name='{self.company_name}', region='{self.region}')>"

class DiscoveryRun(Base):
    __tablename__ = 'discovery_runs'
    
    id = Column(Integer, primary_key=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    region = Column(String(50))
    total_discovered = Column(Integer)
    total_enriched = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    execution_time_minutes = Column(Float)
    
    def __repr__(self):
        return f"<DiscoveryRun(date='{self.run_date}', region='{self.region}', total='{self.total_discovered}')>"

# Database connection
def get_database_url():
    return os.getenv('DATABASE_URL', 'postgresql://housing_user:housing_pass@localhost:5432/housing_associations')

def create_engine_and_session():
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def create_tables():
    engine, _ = create_engine_and_session()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()