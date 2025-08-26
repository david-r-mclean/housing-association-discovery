"""
Pre-built Workflow Templates for Common Operations
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .core import OrchestrationEngine, Priority, get_orchestration_engine
from config.industry_configs import IndustryType, IndustryConfigManager

logger = logging.getLogger(__name__)

class WorkflowTemplates:
    """Pre-built workflow templates for common discovery operations"""
    
    def __init__(self, orchestration_engine: OrchestrationEngine = None):
        self.engine = orchestration_engine or get_orchestration_engine()
        self.config_manager = IndustryConfigManager()
    
    async def create_comprehensive_discovery_workflow(self,
                                                    industry_type: IndustryType,
                                                    region: str = "all",
                                                    use_ai: bool = True,
                                                    parallel_enrichment: int = 5,
                                                    enable_monitoring: bool = True) -> str:
        """
        Create a comprehensive discovery workflow with all stages
        """
        
        workflow_id = await self.engine.create_workflow(
            name=f"Comprehensive Discovery - {industry_type.value}",
            description=f"Full discovery pipeline for {industry_type.value} in {region}",
            max_parallel_tasks=parallel_enrichment,
            failure_strategy="continue",
            metadata={
                'industry_type': industry_type.value,
                'region': region,
                'use_ai': use_ai,
                'created_by': 'workflow_template'
            }
        )
        
        # Stage 1: Initial Discovery
        discovery_task_id = await self.engine.add_task(
            workflow_id=workflow_id,
            name="Initial Discovery",
            function=self._discovery_task,
            args=(industry_type, region),
            priority=Priority.HIGH,
            timeout=300.0,  # 5 minutes
            metadata={'stage': 'discovery'}
        )
        
        # Stage 2: Data Validation and Cleaning
        validation_task_id = await self.engine.add_task(
            workflow_id=workflow_id,
            name="Data Validation",
            function=self._validation_task,
            dependencies=[discovery_task_id],
            priority=Priority.HIGH,
            metadata={'stage': 'validation'}
        )
        
        # Stage 3: Parallel Website Enrichment
        enrichment_tasks = []
        for i in range(parallel_enrichment):
            task_id = await self.engine.add_task(
                workflow_id=workflow_id,
                name=f"Website Enrichment {i+1}",
                function=self._enrichment_task,
                args=(i, parallel_enrichment),
                dependencies=[validation_task_id],
                priority=Priority.NORMAL,
                timeout=600.0,  # 10 minutes
                metadata={'stage': 'enrichment', 'batch': i}
            )
            enrichment_tasks.append(task_id)
        
        # Stage 4: AI Analysis (if enabled)
        ai_tasks = []
        if use_ai:
            for i in range(parallel_enrichment):
                task_id = await self.engine.add_task(
                    workflow_id=workflow_id,
                    name=f"AI Analysis {i+1}",
                    function=self._ai_analysis_task,
                    args=(industry_type, i, parallel_enrichment),
                    dependencies=enrichment_tasks,
                    priority=Priority.NORMAL,
                    timeout=1800.0,  # 30 minutes
                    metadata={'stage': 'ai_analysis', 'batch': i}
                )
                ai_tasks.append(task_id)
        
        # Stage 5: Data Consolidation
        consolidation_deps = ai_tasks if ai_tasks else enrichment_tasks
        consolidation_task_id = await self.engine.add_task(
            workflow_id=workflow_id,
            name="Data Consolidation",
            function=self._consolidation_task,
            dependencies=consolidation_deps,
            priority=Priority.HIGH,
            metadata={'stage': 'consolidation'}
        )
        
        # Stage 6: Database Storage
        storage_task_id = await self.engine.add_task(
            workflow_id=workflow_id,
            name="Database Storage",
            function=self._storage_task,
            args=(industry_type, region),
            dependencies=[consolidation_task_id],
            priority=Priority.HIGH,
            metadata={'stage': 'storage'}
        )
        
        # Stage 7: Report Generation
        report_task_id = await self.engine.add_task(
            workflow_id=workflow_id,
            name="Report Generation",
            function=self._report_generation_task,
            args=(industry_type, region),
            dependencies=[storage_task_id],
            priority=Priority.NORMAL,
            metadata={'stage': 'reporting'}
        )
        
        # Stage 8: Market Intelligence (if AI enabled)
        if use_ai:
            intelligence_task_id = await self.engine.add_task(
                workflow_id=workflow_id,
                name="Market Intelligence",
                function=self._market_intelligence_task,
                args=(industry_type, region),
                dependencies=[report_task_id],
                priority=Priority.NORMAL,
                timeout=900.0,  # 15 minutes
                metadata={'stage': 'intelligence'}
            )
        
        # Stage 9: Notification and Cleanup
        notification_deps = [report_task_id]
        if use_ai:
            notification_deps.append(intelligence_task_id)
        
        await self.engine.add_task(
            workflow_id=workflow_id,
            name="Notification and Cleanup",
            function=self._notification_task,
            args=(workflow_id,),
            dependencies=notification_deps,
            priority=Priority.LOW,
            metadata={'stage': 'notification'}
        )
        
        logger.info(f"Created comprehensive discovery workflow: {workflow_id}")
        return workflow_id
    
    async def create_monitoring_workflow(self, 
                                       target_workflow_id: str,
                                       check_interval: int = 30) -> str:
        """Create a monitoring workflow for another workflow"""
        
        workflow_id = await self.engine.create_workflow(
            name=f"Monitor Workflow {target_workflow_id}",
            description=f"Real-time monitoring for workflow {target_workflow_id}",
            max_parallel_tasks=1,
            metadata={
                'target_workflow': target_workflow_id,
                'monitoring': True
            }
        )
        
        # Continuous monitoring task
        await self.engine.add_task(
            workflow_id=workflow_id,
            name="Continuous Monitor",
            function=self._monitoring_task,
            args=(target_workflow_id, check_interval),
            priority=Priority.LOW,
            metadata={'stage': 'monitoring'}
        )
        
        return workflow_id
    
    async def create_data_pipeline_workflow(self,
                                          source_configs: List[Dict],
                                          transformations: List[Dict],
                                          destinations: List[Dict]) -> str:
        """Create a data pipeline workflow"""
        
        workflow_id = await self.engine.create_workflow(
            name="Data Pipeline",
            description="Extract, Transform, Load data pipeline",
            max_parallel_tasks=3,
            metadata={
                'pipeline': True,
                'sources': len(source_configs),
                'transformations': len(transformations),
                'destinations': len(destinations)
            }
        )
        
        # Extract tasks
        extract_tasks = []
        for i, source_config in enumerate(source_configs):
            task_id = await self.engine.add_task(
                workflow_id=workflow_id,
                name=f"Extract from {source_config['name']}",
                function=self._extract_task,
                args=(source_config,),
                priority=Priority.HIGH,
                metadata={'stage': 'extract', 'source': source_config['name']}
            )
            extract_tasks.append(task_id)
        
        # Transform tasks
        transform_tasks = []
        for i, transform_config in enumerate(transformations):
            task_id = await self.engine.add_task(
                workflow_id=workflow_id,
                name=f"Transform {transform_config['name']}",
                function=self._transform_task,
                args=(transform_config,),
                dependencies=extract_tasks,
                priority=Priority.NORMAL,
                metadata={'stage': 'transform', 'transformation': transform_config['name']}
            )
            transform_tasks.append(task_id)
        
        # Load tasks
        for i, dest_config in enumerate(destinations):
            await self.engine.add_task(
                workflow_id=workflow_id,
                name=f"Load to {dest_config['name']}",
                function=self._load_task,
                args=(dest_config,),
                dependencies=transform_tasks,
                priority=Priority.HIGH,
                metadata={'stage': 'load', 'destination': dest_config['name']}
            )
        
        return workflow_id
    
    async def create_scheduled_workflow(self,
                                      base_workflow_id: str,
                                      schedule_cron: str,
                                      max_instances: int = 1) -> str:
        """Create a scheduled workflow that runs periodically"""
        
        workflow_id = await self.engine.create_workflow(
            name=f"Scheduled Workflow - {schedule_cron}",
            description=f"Scheduled execution of workflow {base_workflow_id}",
            max_parallel_tasks=max_instances,
            metadata={
                'scheduled': True,
                'base_workflow': base_workflow_id,
                'cron': schedule_cron,
                'max_instances': max_instances
            }
        )
        
        # Scheduler task
        await self.engine.add_task(
            workflow_id=workflow_id,
            name="Scheduler",
            function=self._scheduler_task,
            args=(base_workflow_id, schedule_cron, max_instances),
            priority=Priority.LOW,
            metadata={'stage': 'scheduling'}
        )
        
        return workflow_id
    
    # Task Implementation Methods
    
    async def _discovery_task(self, industry_type: IndustryType, region: str) -> Dict:
        """Initial discovery task"""
        logger.info(f"Starting discovery for {industry_type.value} in {region}")
        
        try:
            from agents.universal_discovery_agent import UniversalDiscoveryAgent
            
            agent = UniversalDiscoveryAgent(industry_type)
            organizations = agent.discover_organizations(region=region)
            
            # Store results in workflow context
            result = {
                'organizations': organizations,
                'count': len(organizations),
                'industry_type': industry_type.value,
                'region': region,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Discovery completed: {len(organizations)} organizations found")
            return result
            
        except Exception as e:
            logger.error(f"Discovery task failed: {e}")
            raise
    
    async def _validation_task(self, discovery_result: Dict) -> Dict:
        """Data validation and cleaning task"""
        logger.info("Starting data validation")
        
        try:
            organizations = discovery_result['organizations']
            
            # Validation logic
            valid_organizations = []
            validation_errors = []
            
            for org in organizations:
                # Basic validation
                if not org.get('name'):
                    validation_errors.append(f"Missing name for organization: {org}")
                    continue
                
                # Clean and normalize data
                cleaned_org = self._clean_organization_data(org)
                valid_organizations.append(cleaned_org)
            
            result = {
                'organizations': valid_organizations,
                'valid_count': len(valid_organizations),
                'error_count': len(validation_errors),
                'errors': validation_errors,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Validation completed: {len(valid_organizations)} valid organizations")
            return result
            
        except Exception as e:
            logger.error(f"Validation task failed: {e}")
            raise
    
    async def _enrichment_task(self, batch_index: int, total_batches: int, validation_result: Dict) -> Dict:
        """Website enrichment task for a batch of organizations"""
        logger.info(f"Starting enrichment batch {batch_index + 1}/{total_batches}")
        
        try:
            from agents.enrichment_agent import WebsiteEnrichmentAgent
            
            organizations = validation_result['organizations']
            batch_size = len(organizations) // total_batches
            start_idx = batch_index * batch_size
            end_idx = start_idx + batch_size if batch_index < total_batches - 1 else len(organizations)
            
            batch_orgs = organizations[start_idx:end_idx]
            
            agent = WebsiteEnrichmentAgent()
            enriched_organizations = []
            
            for org in batch_orgs:
                enriched_data = agent.enrich_association(org)
                org.update(enriched_data)
                enriched_organizations.append(org)
                
                # Small delay to be respectful
                await asyncio.sleep(0.5)
            
            result = {
                'organizations': enriched_organizations,
                'batch_index': batch_index,
                'batch_size': len(enriched_organizations),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Enrichment batch {batch_index + 1} completed: {len(enriched_organizations)} organizations")
            return result
            
        except Exception as e:
            logger.error(f"Enrichment task failed: {e}")
            raise
    
    async def _ai_analysis_task(self, industry_type: IndustryType, batch_index: int, total_batches: int, enrichment_results: List[Dict]) -> Dict:
        """AI analysis task for a batch of organizations"""
        logger.info(f"Starting AI analysis batch {batch_index + 1}/{total_batches}")
        
        try:
            from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
            
            # Combine all enrichment results
            all_organizations = []
            for result in enrichment_results:
                all_organizations.extend(result['organizations'])
            
            batch_size = len(all_organizations) // total_batches
            start_idx = batch_index * batch_size
            end_idx = start_idx + batch_size if batch_index < total_batches - 1 else len(all_organizations)
            
            batch_orgs = all_organizations[start_idx:end_idx]
            
            ai_agent = ProductionVertexAIAgent()
            config = self.config_manager.get_config(industry_type)
            
            analyzed_organizations = []
            
            for org in batch_orgs:
                ai_analysis = await ai_agent.analyze_organization_universal(org, config)
                org['ai_insights'] = ai_analysis
                org['ai_enhanced'] = True
                org['ai_analysis_timestamp'] = datetime.now().isoformat()
                analyzed_organizations.append(org)
                
                # Respectful delay for AI API
                await asyncio.sleep(1.0)
            
            result = {
                'organizations': analyzed_organizations,
                'batch_index': batch_index,
                'batch_size': len(analyzed_organizations),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"AI analysis batch {batch_index + 1} completed: {len(analyzed_organizations)} organizations")
            return result
            
        except Exception as e:
            logger.error(f"AI analysis task failed: {e}")
            raise
    
    async def _consolidation_task(self, batch_results: List[Dict]) -> Dict:
        """Consolidate results from all batches"""
        logger.info("Starting data consolidation")
        
        try:
            all_organizations = []
            total_processed = 0
            
            for result in batch_results:
                all_organizations.extend(result['organizations'])
                total_processed += result['batch_size']
            
            # Remove duplicates
            unique_organizations = self._deduplicate_organizations(all_organizations)
            
            result = {
                'organizations': unique_organizations,
                'total_count': len(unique_organizations),
                'processed_count': total_processed,
                'duplicates_removed': total_processed - len(unique_organizations),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Consolidation completed: {len(unique_organizations)} unique organizations")
            return result
            
        except Exception as e:
            logger.error(f"Consolidation task failed: {e}")
            raise
    
    async def _storage_task(self, industry_type: IndustryType, region: str, consolidation_result: Dict) -> Dict:
        """Store results in database"""
        logger.info("Starting database storage")
        
        try:
            from database.database_manager import DatabaseManager
            
            organizations = consolidation_result['organizations']
            db_manager = DatabaseManager()
            
            saved_count = db_manager.save_organizations_universal(
                organizations, 
                industry_type.value, 
                region
            )
            
            result = {
                'saved_count': saved_count,
                'total_organizations': len(organizations),
                'industry_type': industry_type.value,
                'region': region,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Storage completed: {saved_count} organizations saved")
            return result
            
        except Exception as e:
            logger.error(f"Storage task failed: {e}")
            raise
    
    async def _report_generation_task(self, industry_type: IndustryType, region: str, storage_result: Dict) -> Dict:
        """Generate comprehensive reports"""
        logger.info("Starting report generation")
        
        try:
            from utils.output_generator import OutputGenerator
            from database.database_manager import DatabaseManager
            
            # Get organizations from database
            db_manager = DatabaseManager()
            organizations = db_manager.get_organizations_by_industry(industry_type.value, region)
            
            # Convert to dict format for output generator
            org_dicts = [db_manager.association_to_dict(org) for org in organizations]
            
            # Generate reports
            output_gen = OutputGenerator(org_dicts)
            success = output_gen.generate_all_outputs(suffix=f"_{industry_type.value}_{region}_orchestrated")
            
            result = {
                'reports_generated': success,
                'organization_count': len(org_dicts),
                'industry_type': industry_type.value,
                'region': region,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Report generation completed: {success}")
            return result
            
        except Exception as e:
            logger.error(f"Report generation task failed: {e}")
            raise
    
    async def _market_intelligence_task(self, industry_type: IndustryType, region: str, report_result: Dict) -> Dict:
        """Generate market intelligence"""
        logger.info("Starting market intelligence generation")
        
        try:
            from vertex_agents.real_vertex_agent import ProductionVertexAIAgent
            from database.database_manager import DatabaseManager
            
            # Get AI-enhanced organizations
            db_manager = DatabaseManager()
            organizations = db_manager.get_organizations_by_industry(industry_type.value, region)
            org_dicts = [db_manager.association_to_dict(org) for org in organizations if org.ai_enhanced]
            
            if not org_dicts:
                logger.warning("No AI-enhanced organizations found for market intelligence")
                return {'market_intelligence': None, 'message': 'No AI data available'}
            
            ai_agent = ProductionVertexAIAgent()
            market_intel = await ai_agent.advanced_market_intelligence(region, org_dicts)
            
            # Save market intelligence
            import json
            import os
            os.makedirs('outputs', exist_ok=True)
            with open(f'outputs/market_intelligence_{industry_type.value}_{region}_orchestrated.json', 'w') as f:
                json.dump(market_intel, f, indent=2, default=str)
            
            result = {
                'market_intelligence': market_intel,
                'organizations_analyzed': len(org_dicts),
                'industry_type': industry_type.value,
                'region': region,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Market intelligence generation completed")
            return result
            
        except Exception as e:
            logger.error(f"Market intelligence task failed: {e}")
            raise
    
    async def _notification_task(self, workflow_id: str, *results) -> Dict:
        """Send notifications and cleanup"""
        logger.info("Starting notification and cleanup")
        
        try:
            # Send completion notification
            workflow_status = await self.engine.get_workflow_status(workflow_id)
            
            # Here you could send emails, Slack messages, etc.
            logger.info(f"Workflow {workflow_id} completed successfully")
            
            result = {
                'notifications_sent': True,
                'workflow_id': workflow_id,
                'completion_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Notification task failed: {e}")
            raise
    
    async def _monitoring_task(self, target_workflow_id: str, check_interval: int) -> Dict:
        """Continuous monitoring task"""
        logger.info(f"Starting monitoring for workflow {target_workflow_id}")
        
        try:
            while True:
                status = await self.engine.get_workflow_status(target_workflow_id)
                
                if status.get('status') in ['completed', 'failed', 'cancelled']:
                    logger.info(f"Target workflow {target_workflow_id} finished with status: {status.get('status')}")
                    break
                
                # Log progress
                completed = status.get('completed_tasks', 0)
                total = status.get('total_tasks', 0)
                if total > 0:
                    progress = (completed / total) * 100
                    logger.info(f"Workflow {target_workflow_id} progress: {progress:.1f}% ({completed}/{total})")
                
                await asyncio.sleep(check_interval)
            
            return {'monitoring_completed': True, 'final_status': status.get('status')}
            
        except Exception as e:
            logger.error(f"Monitoring task failed: {e}")
            raise
    
    # Helper methods
    
    def _clean_organization_data(self, org: Dict) -> Dict:
        """Clean and normalize organization data"""
        cleaned = org.copy()
        
        # Normalize name
        if cleaned.get('name'):
            cleaned['name'] = cleaned['name'].strip()
        
        # Normalize website URL
        if cleaned.get('website'):
            website = cleaned['website'].strip()
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            cleaned['website'] = website
        
        # Add data quality score
        quality_score = 0
        if cleaned.get('name'): quality_score += 25
        if cleaned.get('website'): quality_score += 25
        if cleaned.get('registration_number'): quality_score += 25
        if cleaned.get('address'): quality_score += 25
        
        cleaned['data_quality_score'] = quality_score
        
        return cleaned
    
    def _deduplicate_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """Remove duplicate organizations"""
        seen = set()
        unique_orgs = []
        
        for org in organizations:
            # Create deduplication key
            name = org.get('name', '').lower().strip()
            reg_number = org.get('registration_number', '').strip()
            
            key = reg_number if reg_number else name
            
            if key and key not in seen:
                seen.add(key)
                unique_orgs.append(org)
        
        return unique_orgs
    
    # Placeholder task methods for data pipeline
    async def _extract_task(self, source_config: Dict) -> Dict:
        """Extract data from source"""
        # Implement data extraction logic
        return {'extracted_data': [], 'source': source_config['name']}
    
    async def _transform_task(self, transform_config: Dict, extract_results: List[Dict]) -> Dict:
        """Transform extracted data"""
        # Implement data transformation logic
        return {'transformed_data': [], 'transformation': transform_config['name']}
    
    async def _load_task(self, dest_config: Dict, transform_results: List[Dict]) -> Dict:
        """Load data to destination"""
        # Implement data loading logic
        return {'loaded_count': 0, 'destination': dest_config['name']}
    
    async def _scheduler_task(self, base_workflow_id: str, cron: str, max_instances: int) -> Dict:
        """Scheduler task for periodic execution"""
        # Implement scheduling logic
        return {'scheduled': True, 'cron': cron}