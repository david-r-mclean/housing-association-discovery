#!/usr/bin/env python3

import argparse
import time
from datetime import datetime
from agents.regulator_discovery_agent import RegulatorDiscoveryAgent
from agents.enrichment_agent import WebsiteEnrichmentAgent
from agents.comprehensive_data_agent import ComprehensiveDataAgent
from utils.output_generator import OutputGenerator
from utils.data_storage import DataStorage
from database.database_manager import DatabaseManager
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description='Housing Association Discovery System')
    parser.add_argument('--full-discovery', action='store_true', 
                       help='Run full discovery process')
    parser.add_argument('--region', choices=['scottish', 'english', 'all'], 
                       default='scottish', help='Focus region for discovery')
    parser.add_argument('--comprehensive-data', action='store_true',
                       help='Collect comprehensive public data including ARC returns')
    parser.add_argument('--use-database', action='store_true',
                       help='Save results to PostgreSQL database')
    
    args = parser.parse_args()
    
    start_time = time.time()
    storage = DataStorage()
    db_manager = DatabaseManager() if args.use_database else None
    
    if args.full_discovery:
        try:
            # Run complete discovery and enrichment using regulators
            print("=== PHASE 1: REGULATOR DISCOVERY ===")
            regulator_agent = RegulatorDiscoveryAgent()
            associations = regulator_agent.discover_all_housing_associations(focus_region=args.region)
            
            # Save raw discovery data
            storage.save_raw_discovery_data(associations, f"{args.region}_regulator_discovery")
            
            print(f"\n=== PHASE 2: WEBSITE ENRICHMENT ===")
            website_enriched = run_website_enrichment(associations)
            
            if args.comprehensive_data:
                print(f"\n=== PHASE 3: COMPREHENSIVE DATA COLLECTION ===")
                fully_enriched = run_comprehensive_data_collection(website_enriched)
            else:
                fully_enriched = website_enriched
            
            # Save to database if requested
            if db_manager:
                print(f"\n=== PHASE 4: DATABASE STORAGE ===")
                saved_count = db_manager.save_housing_associations(fully_enriched, args.region)
                print(f"Saved {saved_count} associations to database")
            
            # Save processed dataset to files
            storage.save_processed_dataset(fully_enriched, f"{args.region}_housing_associations")
            
            # Generate outputs
            print(f"\n=== PHASE 5: OUTPUT GENERATION ===")
            if db_manager:
                # Use database data for outputs
                output_data = db_manager.export_to_dict(args.region)
            else:
                output_data = fully_enriched
            
            output_gen = OutputGenerator(output_data)
            output_gen.generate_all_outputs()
            
            # Log discovery run
            execution_time = (time.time() - start_time) / 60  # Convert to minutes
            if db_manager:
                db_manager.log_discovery_run(
                    region=args.region,
                    total_discovered=len(associations),
                    total_enriched=len(fully_enriched),
                    success=True,
                    execution_time=execution_time
                )
            
            # Print storage summary
            print(f"\n=== SUMMARY ===")
            if db_manager:
                print(f"Database: {len(fully_enriched)} associations saved")
            
            summary = storage.get_storage_summary()
            for directory, count in summary.items():
                print(f"Files - {directory}: {count} files")
            
            print(f"\nComplete! Found and enriched {len(fully_enriched)} housing associations")
            print(f"Execution time: {execution_time:.1f} minutes")
            print(f"Check outputs/ and storage/ directories for results")
            
        except Exception as e:
            execution_time = (time.time() - start_time) / 60
            if db_manager:
                db_manager.log_discovery_run(
                    region=args.region,
                    total_discovered=0,
                    total_enriched=0,
                    success=False,
                    error_message=str(e),
                    execution_time=execution_time
                )
            raise
    
    else:
        print("Use --full-discovery to run the discovery process")
        print("Options: --region scottish|english|all --comprehensive-data --use-database")

def run_website_enrichment(associations):
    """Run website enrichment"""
    website_agent = WebsiteEnrichmentAgent()
    enriched_associations = []
    
    for association in tqdm(associations, desc="Website enrichment"):
        enriched = association.copy()
        website_data = website_agent.enrich_association(association)
        enriched.update(website_data)
        enriched_associations.append(enriched)
    
    return enriched_associations

def run_comprehensive_data_collection(associations):
    """Run comprehensive public data collection"""
    comprehensive_agent = ComprehensiveDataAgent()
    enriched_associations = []
    
    for association in tqdm(associations, desc="Comprehensive data collection"):
        enriched = association.copy()
        comprehensive_data = comprehensive_agent.get_comprehensive_public_data(association)
        enriched.update(comprehensive_data)
        enriched_associations.append(enriched)
    
    return enriched_associations

if __name__ == "__main__":
    main()