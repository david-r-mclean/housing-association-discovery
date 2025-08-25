#!/usr/bin/env python3

import asyncio
import argparse
import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
from agents.regulator_discovery_agent import RegulatorDiscoveryAgent
from agents.enrichment_agent import WebsiteEnrichmentAgent
from database.database_manager import DatabaseManager
from database.duplicate_manager import DuplicateManager
from utils.output_generator import OutputGenerator

async def main():
    parser = argparse.ArgumentParser(description='Production Vertex AI Housing Discovery with Smart Duplicate Detection')
    parser.add_argument('--region', default='scottish', help='Region to discover')
    parser.add_argument('--use-real-ai', action='store_true', help='Use real Vertex AI (requires billing)')
    parser.add_argument('--use-database', action='store_true', help='Save to database')
    parser.add_argument('--comprehensive', action='store_true', help='Full AI analysis')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh of existing data')
    parser.add_argument('--max-age-days', type=int, default=30, help='Max age of data before refresh (days)')
    parser.add_argument('--ai-only', action='store_true', help='Only run AI enhancement on existing data')
    
    args = parser.parse_args()
    
    print("🚀 Production Vertex AI Housing Association Discovery")
    print("🧠 Smart Duplicate Detection Enabled")
    print("=" * 70)
    
    start_time = datetime.now()
    duplicate_manager = DuplicateManager()
    
    try:
        if args.ai_only:
            # Only run AI enhancement on existing associations
            print("\n🧠 AI-Only Mode: Enhancing Existing Associations")
            
            existing_associations = duplicate_manager.get_associations_needing_ai_enhancement(args.region)
            
            if not existing_associations:
                print("✅ All associations are already AI-enhanced!")
                return
            
            print(f"Found {len(existing_associations)} associations needing AI enhancement")
            
            # Convert to format expected by AI agent
            to_enhance = []
            db_manager = DatabaseManager()
            for assoc_info in existing_associations:
                full_assoc = db_manager.get_association_by_company_number(assoc_info['company_number'])
                if full_assoc:
                    assoc_dict = db_manager.association_to_dict(full_assoc)
                    to_enhance.append(assoc_dict)
            
            final_associations = to_enhance
            
        else:
            # Phase 1: Traditional Discovery
            print("\n📡 Phase 1: Traditional Discovery with Duplicate Detection")
            regulator_agent = RegulatorDiscoveryAgent()
            discovered_associations = regulator_agent.discover_all_housing_associations(focus_region=args.region)
            print(f"Discovered {len(discovered_associations)} housing associations")
            
            # Smart duplicate filtering
            filtered_results = duplicate_manager.filter_new_associations(
                discovered_associations,
                region=args.region,
                force_refresh=args.force_refresh,
                max_age_days=args.max_age_days
            )
            
            print(f"\n🔍 Duplicate Analysis Results:")
            print(f"   📊 Total discovered: {filtered_results['summary']['total_discovered']}")
            print(f"   ✨ New associations: {filtered_results['summary']['new_count']}")
            print(f"   ♻️  Stale associations: {filtered_results['summary']['stale_count']}")
            print(f"   ✅ Up-to-date: {filtered_results['summary']['existing_count']}")
            print(f"   🔄 Processing needed: {filtered_results['summary']['processing_needed']}")
            
            # Process only new and stale associations
            to_process = filtered_results['new'] + [item['association'] for item in filtered_results['stale']]
            
            if not to_process:
                print("\n✅ All associations are up-to-date! Use --force-refresh to reprocess.")
                return
            
            print(f"\n🌐 Phase 2: Website Enrichment ({len(to_process)} associations)")
            website_agent = WebsiteEnrichmentAgent()
            enriched_associations = []
            
            for i, association in enumerate(to_process[:10], 1):  # Limit for demo
                print(f"   Enriching ({i}/{min(len(to_process), 10)}): {association.get('name', 'Unknown')}")
                enriched = association.copy()
                website_data = website_agent.enrich_association(association)
                enriched.update(website_data)
                enriched_associations.append(enriched)
            
            final_associations = enriched_associations
        
        # Phase 3: AI Enhancement (if enabled)
        if args.use_real_ai and final_associations:
            print(f"\n🧠 Phase 3: Vertex AI Enhancement ({len(final_associations)} associations)")
            ai_agent = ProductionVertexAIAgent()
            
            ai_enhanced_associations = []
            
            for i, association in enumerate(final_associations, 1):
                print(f"   🤖 AI analyzing ({i}/{len(final_associations)}): {association.get('name', 'Unknown')}")
                
                # Get comprehensive AI analysis
                ai_analysis = await ai_agent.analyze_housing_association_comprehensive(association)
                
                # Merge AI insights with existing data
                association['ai_insights'] = ai_analysis
                association['ai_enhanced'] = True
                association['ai_analysis_timestamp'] = datetime.now().isoformat()
                
                ai_enhanced_associations.append(association)
                
                # Small delay to respect rate limits
                await asyncio.sleep(1)
            
            final_associations = ai_enhanced_associations
            
            # Generate market intelligence
            if args.comprehensive:
                print("\n🌍 Phase 4: Market Intelligence")
                market_intel = await ai_agent.advanced_market_intelligence(args.region, final_associations)
                
                # Generate business insights
                business_insights = await ai_agent.generate_business_insights(
                    [assoc.get('ai_insights', {}) for assoc in final_associations]
                )
                
                # Save market intelligence
                os.makedirs('outputs', exist_ok=True)
                with open(f'outputs/market_intelligence_{args.region}.json', 'w') as f:
                    json.dump(market_intel, f, indent=2)
                
                with open(f'outputs/business_insights_{args.region}.json', 'w') as f:
                    json.dump(business_insights, f, indent=2)
                
                print("📊 Market intelligence and business insights saved")
        
        elif not args.use_real_ai:
            print("\n⚠️ Skipping AI enhancement (use --use-real-ai to enable)")
        
        # Phase 4: Database Storage
        if args.use_database and final_associations:
            print(f"\n💾 Phase 5: Database Storage ({len(final_associations)} associations)")
            db_manager = DatabaseManager()
            saved_count = db_manager.save_housing_associations(final_associations, args.region)
            print(f"Saved {saved_count} associations to database")
            
            # Log the discovery session
            if not args.ai_only:
                duplicate_manager.log_discovery_session(
                    args.region, 
                    filtered_results if 'filtered_results' in locals() else {'summary': {'total_discovered': len(final_associations), 'processing_needed': len(final_associations)}},
                    ai_enhanced=args.use_real_ai
                )
        
        # Phase 5: Output Generation
        if final_associations:
            print(f"\n📄 Phase 6: Output Generation")
            output_gen = OutputGenerator(final_associations)
            output_gen.generate_all_outputs()
        
        # Summary
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Discovery Complete!")
        print(f"   Total associations processed: {len(final_associations) if final_associations else 0}")
        print(f"   AI enhanced: {sum(1 for a in final_associations if a.get('ai_enhanced', False)) if final_associations else 0}")
        print(f"   Execution time: {execution_time:.1f} seconds")
        print(f"   Check outputs/ directory for results")
        
        if args.use_real_ai and final_associations:
            print(f"\n🧠 AI Enhancement Summary:")
            ai_enhanced_count = sum(1 for a in final_associations if a.get('ai_enhanced', False))
            avg_confidence = sum(
                a.get('ai_insights', {}).get('confidence_metrics', {}).get('analysis_confidence', 0) 
                for a in final_associations
            ) / len(final_associations) if final_associations else 0
            print(f"   AI analyses completed: {ai_enhanced_count}")
            print(f"   Average confidence: {avg_confidence:.2f}")
        
    except Exception as e:
        print(f"❌ Error during discovery: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())