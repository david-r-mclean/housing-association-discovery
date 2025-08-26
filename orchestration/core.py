"""
Enterprise Orchestration Layer
Manages complex workflows, parallel processing, and task coordination
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path
import traceback
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import redis
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pickle

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"

class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

@dataclass
class Task:
    id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: Priority = Priority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class Workflow:
    id: str
    name: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    max_parallel_tasks: int = 5
    failure_strategy: str = "stop"  # "stop", "continue", "retry"

class OrchestrationEngine:
    """Main orchestration engine for managing workflows and tasks"""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 db_url: str = "sqlite:///orchestration.db",
                 max_workers: int = 10,
                 enable_persistence: bool = True):
        
        self.workflows: Dict[str, Workflow] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_queue = asyncio.Queue()
        self.max_workers = max_workers
        self.enable_persistence = enable_persistence
        
        # Initialize Redis for distributed coordination
        try:
            self.redis_client = redis.from_url(redis_url) if redis_url else None
            if self.redis_client:
                self.redis_client.ping()
                logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis_client = None
        
        # Initialize database for persistence
        if enable_persistence:
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
            self._create_tables()
        
        # Thread pools for different types of work
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers // 2)
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Metrics
        self.metrics = {
            'workflows_created': 0,
            'workflows_completed': 0,
            'workflows_failed': 0,
            'tasks_executed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        
        logger.info(f"Orchestration Engine initialized with {max_workers} workers")
    
    def _create_tables(self):
        """Create database tables for persistence"""
        Base = declarative_base()
        
        class WorkflowRecord(Base):
            __tablename__ = 'workflows'
            id = Column(String, primary_key=True)
            name = Column(String)
            description = Column(Text)
            status = Column(String)
            created_at = Column(DateTime)
            started_at = Column(DateTime)
            completed_at = Column(DateTime)
            metadata = Column(Text)
            workflow_data = Column(Text)
        
        class TaskRecord(Base):
            __tablename__ = 'tasks'
            id = Column(String, primary_key=True)
            workflow_id = Column(String)
            name = Column(String)
            status = Column(String)
            created_at = Column(DateTime)
            completed_at = Column(DateTime)
            execution_time = Column(Float)
            result_data = Column(Text)
            error_message = Column(Text)
            metadata = Column(Text)
        
        Base.metadata.create_all(self.engine)
        self.WorkflowRecord = WorkflowRecord
        self.TaskRecord = TaskRecord
    
    async def create_workflow(self, 
                            name: str, 
                            description: str = "",
                            max_parallel_tasks: int = 5,
                            failure_strategy: str = "stop",
                            metadata: Dict = None) -> str:
        """Create a new workflow"""
        
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            max_parallel_tasks=max_parallel_tasks,
            failure_strategy=failure_strategy,
            metadata=metadata or {}
        )
        
        self.workflows[workflow_id] = workflow
        self.metrics['workflows_created'] += 1
        
        # Persist to database
        if self.enable_persistence:
            await self._persist_workflow(workflow)
        
        # Publish event
        await self._publish_event('workflow_created', {
            'workflow_id': workflow_id,
            'name': name,
            'description': description
        })
        
        logger.info(f"Created workflow: {name} ({workflow_id})")
        return workflow_id
    
    async def add_task(self, 
                      workflow_id: str,
                      name: str,
                      function: Callable,
                      args: tuple = (),
                      kwargs: Dict = None,
                      dependencies: List[str] = None,
                      priority: Priority = Priority.NORMAL,
                      max_retries: int = 3,
                      timeout: Optional[float] = None,
                      scheduled_at: Optional[datetime] = None,
                      metadata: Dict = None) -> str:
        """Add a task to a workflow"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            function=function,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or [],
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        
        self.workflows[workflow_id].tasks.append(task)
        
        logger.info(f"Added task '{name}' to workflow {workflow_id}")
        return task_id
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """Start executing a workflow"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.CREATED:
            raise ValueError(f"Workflow {workflow_id} is not in CREATED status")
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        # Start workflow execution
        asyncio.create_task(self._execute_workflow(workflow))
        
        await self._publish_event('workflow_started', {
            'workflow_id': workflow_id,
            'name': workflow.name
        })
        
        logger.info(f"Started workflow: {workflow.name} ({workflow_id})")
        return True
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute a workflow with all its tasks"""
        
        try:
            logger.info(f"Executing workflow: {workflow.name}")
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow.tasks)
            
            # Execute tasks in dependency order
            completed_tasks = set()
            running_tasks = {}
            
            while len(completed_tasks) < len(workflow.tasks):
                # Find tasks ready to run
                ready_tasks = []
                for task in workflow.tasks:
                    if (task.id not in completed_tasks and 
                        task.id not in running_tasks and
                        all(dep in completed_tasks for dep in task.dependencies) and
                        (task.scheduled_at is None or task.scheduled_at <= datetime.now())):
                        ready_tasks.append(task)
                
                # Sort by priority
                ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                
                # Start tasks up to parallel limit
                while (ready_tasks and 
                       len(running_tasks) < workflow.max_parallel_tasks):
                    task = ready_tasks.pop(0)
                    task_coroutine = self._execute_task(task, workflow)
                    running_tasks[task.id] = asyncio.create_task(task_coroutine)
                    logger.info(f"Started task: {task.name}")
                
                # Wait for at least one task to complete
                if running_tasks:
                    done, pending = await asyncio.wait(
                        running_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed tasks
                    for task_future in done:
                        task_id = None
                        for tid, future in running_tasks.items():
                            if future == task_future:
                                task_id = tid
                                break
                        
                        if task_id:
                            completed_tasks.add(task_id)
                            del running_tasks[task_id]
                            
                            # Check if task failed and handle according to strategy
                            task = next(t for t in workflow.tasks if t.id == task_id)
                            if task.status == TaskStatus.FAILED:
                                if workflow.failure_strategy == "stop":
                                    # Cancel remaining tasks
                                    for future in running_tasks.values():
                                        future.cancel()
                                    workflow.status = WorkflowStatus.FAILED
                                    await self._publish_event('workflow_failed', {
                                        'workflow_id': workflow.id,
                                        'failed_task': task.name
                                    })
                                    return
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
            
            # All tasks completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            self.metrics['workflows_completed'] += 1
            
            await self._publish_event('workflow_completed', {
                'workflow_id': workflow.id,
                'name': workflow.name,
                'execution_time': (workflow.completed_at - workflow.started_at).total_seconds()
            })
            
            logger.info(f"Workflow completed: {workflow.name}")
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            self.metrics['workflows_failed'] += 1
            
            logger.error(f"Workflow failed: {workflow.name} - {e}")
            await self._publish_event('workflow_failed', {
                'workflow_id': workflow.id,
                'error': str(e)
            })
    
    async def _execute_task(self, task: Task, workflow: Workflow) -> TaskResult:
        """Execute a single task"""
        
        start_time = datetime.now()
        task.status = TaskStatus.RUNNING
        
        await self._publish_event('task_started', {
            'task_id': task.id,
            'workflow_id': workflow.id,
            'task_name': task.name
        })
        
        retries = 0
        while retries <= task.max_retries:
            try:
                # Execute the task function
                if asyncio.iscoroutinefunction(task.function):
                    if task.timeout:
                        result = await asyncio.wait_for(
                            task.function(*task.args, **task.kwargs),
                            timeout=task.timeout
                        )
                    else:
                        result = await task.function(*task.args, **task.kwargs)
                else:
                    # Run in thread pool for sync functions
                    if task.timeout:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                self.thread_executor,
                                lambda: task.function(*task.args, **task.kwargs)
                            ),
                            timeout=task.timeout
                        )
                    else:
                        result = await asyncio.get_event_loop().run_in_executor(
                            self.thread_executor,
                            lambda: task.function(*task.args, **task.kwargs)
                        )
                
                # Task succeeded
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                task_result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    execution_time=execution_time,
                    completed_at=end_time
                )
                
                task.status = TaskStatus.COMPLETED
                task.result = task_result
                
                self.metrics['tasks_executed'] += 1
                self.metrics['total_execution_time'] += execution_time
                
                await self._publish_event('task_completed', {
                    'task_id': task.id,
                    'workflow_id': workflow.id,
                    'task_name': task.name,
                    'execution_time': execution_time
                })
                
                logger.info(f"Task completed: {task.name} ({execution_time:.2f}s)")
                return task_result
                
            except Exception as e:
                retries += 1
                error_msg = str(e)
                
                if retries <= task.max_retries:
                    task.status = TaskStatus.RETRYING
                    logger.warning(f"Task {task.name} failed (attempt {retries}), retrying: {error_msg}")
                    await asyncio.sleep(task.retry_delay * retries)  # Exponential backoff
                else:
                    # Task failed permanently
                    end_time = datetime.now()
                    execution_time = (end_time - start_time).total_seconds()
                    
                    task_result = TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILED,
                        error=error_msg,
                        execution_time=execution_time,
                        completed_at=end_time
                    )
                    
                    task.status = TaskStatus.FAILED
                    task.result = task_result
                    
                    self.metrics['tasks_failed'] += 1
                    
                    await self._publish_event('task_failed', {
                        'task_id': task.id,
                        'workflow_id': workflow.id,
                        'task_name': task.name,
                        'error': error_msg,
                        'retries': retries - 1
                    })
                    
                    logger.error(f"Task failed permanently: {task.name} - {error_msg}")
                    return task_result
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Build a dependency graph for tasks"""
        graph = {}
        for task in tasks:
            graph[task.id] = task.dependencies.copy()
        return graph
    
    async def _publish_event(self, event_type: str, data: Dict):
        """Publish events to handlers and Redis"""
        
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Call local event handlers
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
        
        # Publish to Redis
        if self.redis_client:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.publish('orchestration_events', json.dumps(event, default=str))
                )
            except Exception as e:
                logger.error(f"Redis publish error: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _persist_workflow(self, workflow: Workflow):
        """Persist workflow to database"""
        if not self.enable_persistence:
            return
        
        try:
            session = self.Session()
            
            workflow_record = self.WorkflowRecord(
                id=workflow.id,
                name=workflow.name,
                description=workflow.description,
                status=workflow.status.value,
                created_at=workflow.created_at,
                started_at=workflow.started_at,
                completed_at=workflow.completed_at,
                metadata=json.dumps(workflow.metadata, default=str),
                workflow_data=pickle.dumps(workflow).hex()
            )
            
            session.merge(workflow_record)
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error persisting workflow: {e}")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get detailed workflow status"""
        
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        task_statuses = {}
        for task in workflow.tasks:
            task_statuses[task.id] = {
                'name': task.name,
                'status': task.status.value,
                'created_at': task.created_at.isoformat(),
                'execution_time': task.result.execution_time if task.result else 0,
                'error': task.result.error if task.result else None
            }
        
        return {
            'workflow_id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'total_tasks': len(workflow.tasks),
            'completed_tasks': sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED),
            'failed_tasks': sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED),
            'running_tasks': sum(1 for t in workflow.tasks if t.status == TaskStatus.RUNNING),
            'tasks': task_statuses,
            'metadata': workflow.metadata
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.CANCELLED
        
        # Cancel running tasks
        for task in workflow.tasks:
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
        
        await self._publish_event('workflow_cancelled', {
            'workflow_id': workflow_id,
            'name': workflow.name
        })
        
        logger.info(f"Cancelled workflow: {workflow.name}")
        return True
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.PAUSED
        
        await self._publish_event('workflow_paused', {
            'workflow_id': workflow_id,
            'name': workflow.name
        })
        
        logger.info(f"Paused workflow: {workflow.name}")
        return True
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        if workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.RUNNING
            asyncio.create_task(self._execute_workflow(workflow))
            
            await self._publish_event('workflow_resumed', {
                'workflow_id': workflow_id,
                'name': workflow.name
            })
            
            logger.info(f"Resumed workflow: {workflow.name}")
            return True
        
        return False
    
    def get_metrics(self) -> Dict:
        """Get orchestration metrics"""
        return self.metrics.copy()
    
    async def cleanup(self):
        """Cleanup resources"""
        
        # Cancel all running tasks
        for workflow in self.workflows.values():
            if workflow.status == WorkflowStatus.RUNNING:
                await self.cancel_workflow(workflow.id)
        
        # Shutdown executors
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        
        # Close Redis connection
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Orchestration engine cleaned up")

# Global orchestration engine instance
orchestration_engine = None

def get_orchestration_engine() -> OrchestrationEngine:
    """Get the global orchestration engine instance"""
    global orchestration_engine
    if orchestration_engine is None:
        orchestration_engine = OrchestrationEngine()
    return orchestration_engine