#!/usr/bin/env python3
"""
Full Scale Housing Association Discovery - Process ALL Associations
No limits, comprehensive analysis of entire dataset
"""

import asyncio
import argparse
import sys
import os
import json
from datetime import datetime
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
from agents.regulator_discovery_agent import RegulatorDiscoveryAgent
from agents.enrichment_agent import WebsiteEnrichmentAgent
from database.database_manager import DatabaseManager
from database.duplicate_manager import DuplicateManager
from utils.output_generator import OutputGenerator

async def main():
    parser = argparse.ArgumentParser(description='Full Scale Housing Discovery - Process ALL Associations')
    parser.add_argument('--region', default='scottish', help='Region to discover')
    parser.add_argument('--use-real-ai', action='store_true', help='Use real Vertex AI (requires billing)')
    parser.add_argument('--use-database', action='store_true', help='Save to database')
    parser.add_argument('--comprehensive', action='store_true', help='Full AI analysis')
    parser.add_argument('--batch-size', type=int, default=50, help='Process in batches of N associations')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    
    args = parser.parse_args()
    
    print("🚀 FULL SCALE Housing Association Discovery")
    print("🔥 NO LIMITS - Processing ALL Associations")
    print("=" * 70)
    
    start_time = datetime.now()
    duplicate_manager = DuplicateManager()
    
    try:
        # Phase 1: Traditional Discovery
        print("\n📡 Phase 1: Complete Discovery (No Limits)")
        regulator_agent = RegulatorDiscoveryAgent()
        discovered_associations = regulator_agent.discover_all_housing_associations(focus_region=args.region)
        print(f"Discovered {len(discovered_associations)} housing associations")
        
        # Smart duplicate filtering
        filtered_results = duplicate_manager.filter_new_associations(
            discovered_associations,
            region=args.region,
            max_age_days=7  # Shorter refresh cycle for full processing
        )
        
        print(f"\n🔍 Processing Strategy:")
        print(f"   📊 Total discovered: {filtered_results['summary']['total_discovered']}")
        print(f"   ✨ New associations: {filtered_results['summary']['new_count']}")
        print(f"   ♻️  Stale associations: {filtered_results['summary']['stale_count']}")
        print(f"   ✅ Up-to-date: {filtered_results['summary']['existing_count']}")
        print(f"   🔄 PROCESSING ALL: {filtered_results['summary']['processing_needed']}")
        
        # Process ALL new and stale associations
        to_process = filtered_results['new'] + [item['association'] for item in filtered_results['stale']]
        
        if not to_process:
            print("\n✅ All associations are up-to-date!")
            # Still process existing for AI enhancement if requested
            if args.use_real_ai:
                print("🧠 Checking for AI enhancement opportunities...")
                existing_for_ai = duplicate_manager.get_associations_needing_ai_enhancement(args.region)
                if existing_for_ai:
                    print(f"Found {len(existing_for_ai)} associations needing AI enhancement")
                    # Convert to processing format
                    db_manager = DatabaseManager()
                    to_process = []
                    for assoc_info in existing_for_ai:
                        full_assoc = db_manager.get_association_by_company_number(assoc_info['company_number'])
                        if full_assoc:
                            assoc_dict = db_manager.association_to_dict(full_assoc)
                            to_process.append(assoc_dict)
        
        if not to_process:
            print("✅ No processing needed!")
            return
        
        print(f"\n🌐 Phase 2: Website Enrichment - ALL {len(to_process)} Associations")
        website_agent = WebsiteEnrichmentAgent()
        enriched_associations = []
        
        # Process in batches for better progress tracking
        batch_size = args.batch_size
        total_batches = (len(to_process) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(to_process))
            batch = to_process[start_idx:end_idx]
            
            print(f"\n📦 Processing Batch {batch_num + 1}/{total_batches} ({len(batch)} associations)")
            
            for i, association in enumerate(batch, 1):
                global_idx = start_idx + i
                print(f"   Enriching ({global_idx}/{len(to_process)}): {association.get('name', 'Unknown')}")
                
                enriched = association.copy()
                website_data = website_agent.enrich_association(association)
                enriched.update(website_data)
                enriched_associations.append(enriched)
                
                # Respectful delay
                time.sleep(args.delay)
            
            print(f"   ✅ Batch {batch_num + 1} completed ({len(enriched_associations)}/{len(to_process)} total)")
            
            # Save progress after each batch
            if args.use_database and enriched_associations:
                db_manager = DatabaseManager()
                saved_count = db_manager.save_housing_associations(enriched_associations[-len(batch):], args.region)
                print(f"   💾 Saved batch to database ({saved_count} associations)")
        
        print(f"\n✅ Website enrichment completed: {len(enriched_associations)} associations processed")
        
        # Phase 3: AI Enhancement (if enabled)
        if args.use_real_ai and enriched_associations:
            print(f"\n🧠 Phase 3: AI Enhancement - ALL {len(enriched_associations)} Associations")
            ai_agent = ProductionVertexAIAgent()
            
            ai_enhanced_associations = []
            
            for i, association in enumerate(enriched_associations, 1):
                print(f"   🤖 AI analyzing ({i}/{len(enriched_associations)}): {association.get('name', 'Unknown')}")
                
                # Get comprehensive AI analysis
                ai_analysis = await ai_agent.analyze_housing_association_comprehensive(association)
                
                # Merge AI insights with existing data
                association['ai_insights'] = ai_analysis
                association['ai_enhanced'] = True
                association['ai_analysis_timestamp'] = datetime.now().isoformat()
                
                ai_enhanced_associations.append(association)
                
                # Progress updates
                if i % 10 == 0:
                    print(f"   📊 AI Progress: {i}/{len(enriched_associations)} completed")
                
                # Respectful delay for AI API
                await asyncio.sleep(args.delay)
            
            enriched_associations = ai_enhanced_associations
            
            # Generate comprehensive market intelligence
            if args.comprehensive:
                print("\n🌍 Phase 4: Comprehensive Market Intelligence")
                market_intel = await ai_agent.advanced_market_intelligence(args.region, enriched_associations)
                
                # Generate business insights
                business_insights = await ai_agent.generate_business_insights(
                    [assoc.get('ai_insights', {}) for assoc in enriched_associations]
                )
                
                # Save market intelligence
                os.makedirs('outputs', exist_ok=True)
                with open(f'outputs/market_intelligence_{args.region}_full.json', 'w') as f:
                    json.dump(market_intel, f, indent=2)
                
                with open(f'outputs/business_insights_{args.region}_full.json', 'w') as f:
                    json.dump(business_insights, f, indent=2)
                
                print("📊 Comprehensive market intelligence saved")
        
        # Phase 4/5: Database Storage
        if args.use_database and enriched_associations:
            print(f"\n💾 Phase 5: Final Database Storage")
            db_manager = DatabaseManager()
            saved_count = db_manager.save_housing_associations(enriched_associations, args.region)
            print(f"Final save: {saved_count} associations to database")
            
            # Log the discovery session
            duplicate_manager.log_discovery_session(
                args.region, 
                filtered_results,
                ai_enhanced=args.use_real_ai
            )
        
        # Phase 5/6: Output Generation
        if enriched_associations:
            print(f"\n📄 Phase 6: Comprehensive Output Generation")
            output_gen = OutputGenerator(enriched_associations)
            output_gen.generate_all_outputs(suffix="_full_scale")
            print("📁 All outputs generated with '_full_scale' suffix")
        
        # Final Summary
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n🎉 FULL SCALE DISCOVERY COMPLETE!")
        print(f"=" * 50)
        print(f"   📊 Total associations processed: {len(enriched_associations)}")
        print(f"   🧠 AI enhanced: {sum(1 for a in enriched_associations if a.get('ai_enhanced', False))}")
        print(f"   ⏱️  Total execution time: {execution_time/60:.1f} minutes")
        print(f"   📁 Check outputs/ directory for comprehensive results")
        
        if args.use_real_ai and enriched_associations:
            print(f"\n🧠 AI Enhancement Summary:")
            ai_enhanced_count = sum(1 for a in enriched_associations if a.get('ai_enhanced', False))
            avg_confidence = sum(
                a.get('ai_insights', {}).get('confidence_metrics', {}).get('analysis_confidence', 0) 
                for a in enriched_associations
            ) / len(enriched_associations) if enriched_associations else 0
            print(f"   🎯 AI analyses completed: {ai_enhanced_count}")
            print(f"   📈 Average confidence: {avg_confidence:.2f}")
            print(f"   💰 Estimated market value analyzed: £{len(enriched_associations) * 2.5:.1f}M+")
        
    except Exception as e:
        print(f"❌ Error during full scale discovery: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())