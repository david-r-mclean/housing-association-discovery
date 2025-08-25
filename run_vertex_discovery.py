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
from utils.output_generator import OutputGenerator

async def main():
    parser = argparse.ArgumentParser(description='Production Vertex AI Housing Discovery')
    parser.add_argument('--region', default='scottish', help='Region to discover')
    parser.add_argument('--use-real-ai', action='store_true', help='Use real Vertex AI (requires billing)')
    parser.add_argument('--use-database', action='store_true', help='Save to database')
    parser.add_argument('--comprehensive', action='store_true', help='Full AI analysis')
    
    args = parser.parse_args()
    
    print("🚀 Production Vertex AI Housing Association Discovery")
    print("=" * 70)
    
    start_time = datetime.now()
    
    try:
        # Phase 1: Traditional Discovery
        print("\n📡 Phase 1: Traditional Discovery")
        regulator_agent = RegulatorDiscoveryAgent()
        associations = regulator_agent.discover_all_housing_associations(focus_region=args.region)
        print(f"Found {len(associations)} housing associations")
        
        # Phase 2: Website Enrichment
        print("\n🌐 Phase 2: Website Enrichment")
        website_agent = WebsiteEnrichmentAgent()
        enriched_associations = []
        
        for association in associations[:10]:  # Limit for testing
            enriched = association.copy()
            website_data = website_agent.enrich_association(association)
            enriched.update(website_data)
            enriched_associations.append(enriched)
        
        print(f"Enriched {len(enriched_associations)} associations")
        
        # Phase 3: AI Enhancement (if enabled)
        if args.use_real_ai:
            print("\n🧠 Phase 3: Vertex AI Enhancement")
            ai_agent = ProductionVertexAIAgent()
            
            ai_enhanced_associations = []
            
            for association in enriched_associations:
                print(f"   🤖 AI analyzing: {association.get('name', 'Unknown')}")
                
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
                with open(f'outputs/market_intelligence_{args.region}.json', 'w') as f:
                    json.dump(market_intel, f, indent=2)
                
                with open(f'outputs/business_insights_{args.region}.json', 'w') as f:
                    json.dump(business_insights, f, indent=2)
                
                print("📊 Market intelligence and business insights saved")
        
        else:
            final_associations = enriched_associations
            print("\n⚠️ Skipping AI enhancement (use --use-real-ai to enable)")
        
        # Phase 4: Database Storage
        if args.use_database:
            print("\n💾 Phase 5: Database Storage")
            db_manager = DatabaseManager()
            saved_count = db_manager.save_housing_associations(final_associations, args.region)
            print(f"Saved {saved_count} associations to database")
        
        # Phase 5: Output Generation
        print("\n📄 Phase 6: Output Generation")
        output_gen = OutputGenerator(final_associations)
        output_gen.generate_all_outputs()
        
        # Summary
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Discovery Complete!")
        print(f"   Total associations: {len(final_associations)}")
        print(f"   AI enhanced: {sum(1 for a in final_associations if a.get('ai_enhanced', False))}")
        print(f"   Execution time: {execution_time:.1f} seconds")
        print(f"   Check outputs/ directory for results")
        
        if args.use_real_ai:
            print(f"\n🧠 AI Enhancement Summary:")
            ai_enhanced_count = sum(1 for a in final_associations if a.get('ai_enhanced', False))
            print(f"   AI analyses completed: {ai_enhanced_count}")
            print(f"   Average confidence: {sum(a.get('ai_insights', {}).get('confidence_scores', {}).get('analysis_reliability', 0) for a in final_associations) / len(final_associations):.2f}")
        
    except Exception as e:
        print(f"❌ Error during discovery: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())