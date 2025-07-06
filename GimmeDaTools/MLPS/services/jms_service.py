"""
Service for integrating JMS API with the scheduler
"""
import threading
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from models.job import Job
from models.part import Part
from models.workpiece_priority import WorkpiecePriority
from utils.event_system import event_system
from utils.file_utils import load_json_file, save_json_file

# Check if JMS client is available
try:
    from services.jms.jms_client import JMSClient
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = True  # Module is available even if requests is not
except ImportError:
    JMS_AVAILABLE = False
    event_system.publish("error", "JMS client modules not found. JMS integration will not be available.")


class JMSService:
    """Service for integrating JMS API with the scheduler"""
    
    def __init__(
        self,
        scheduler_service,
        base_url: str = "http://localhost:8080",
        polling_interval: int = 30,
        mapping_file: str = "jms_mapping.json",
        username: str = None,
        password: str = None,
        client_id: str = "EsbusciClient",
        client_secret: str = "DefaultEsbusciClientSecret"
    ):
        """
        Initialize the JMS service
        
        Args:
            scheduler_service: SchedulerService instance
            base_url: Base URL of the JMS API
            polling_interval: Interval for polling production updates (seconds)
            mapping_file: Path to the file storing job-order mappings
            username: Username for authentication (optional)
            password: Password for authentication (optional)
            client_id: OAuth2 client ID (default: EsbusciClient)
            client_secret: OAuth2 client secret (default: DefaultEsbusciClientSecret)
        """
        self.scheduler_service = scheduler_service
        self.polling_interval = polling_interval
        self.mapping_file = mapping_file
        self.base_url = base_url
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Thread for background polling
        self.polling_thread = None
        self.stop_polling_flag = threading.Event()
        
        # Initialize client if available
        self.client = None
        if JMS_AVAILABLE:
            try:
                print(f"Initializing JMS client with URL: {base_url}")
                if username and password:
                    print(f"Using username authentication for JMS client")
                    self.client = JMSClient(base_url, client_id, client_secret, username, password)
                else:
                    print(f"Using client credentials authentication for JMS client")
                    self.client = JMSClient(base_url, client_id, client_secret)
            except Exception as e:
                error_msg = f"Failed to initialize JMS client: {str(e)}"
                print(error_msg)
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                event_system.publish("error", error_msg)
        
        # Load job-order mappings
        self.job_order_mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, str]:
        """
        Load job-order mappings from file
        
        Returns:
            Dictionary mapping job IDs to order IDs
        """
        mappings = load_json_file(self.mapping_file, default={})
        return mappings
    
    def _save_mappings(self) -> None:
        """Save job-order mappings to file"""
        save_json_file(self.mapping_file, self.job_order_mappings)
    
    def start_polling(self) -> None:
        """Start background polling for production updates"""
        if not JMS_AVAILABLE or not self.client:
            event_system.publish("error", "Cannot start polling: JMS client not available")
            return
            
        if self.polling_thread and self.polling_thread.is_alive():
            return
            
        # If requests is not available, just simulate polling
        if not REQUESTS_AVAILABLE:
            event_system.publish("jms_polling_started", "Started mock polling for JMS updates")
            return
            
        self.stop_polling_flag.clear()
        self.polling_thread = threading.Thread(target=self._polling_worker)
        self.polling_thread.daemon = True
        self.polling_thread.start()
        
        event_system.publish("jms_polling_started", "Started polling JMS for production updates")
    
    def stop_polling(self) -> None:
        """Stop background polling"""
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_polling_flag.set()
            self.polling_thread.join(timeout=5.0)
            
            event_system.publish("jms_polling_stopped", "Stopped polling JMS for production updates")
    
    def _polling_worker(self) -> None:
        """Worker function for background polling"""
        while not self.stop_polling_flag.is_set():
            try:
                self._update_production_status()
            except Exception as e:
                event_system.publish("error", f"JMS polling error: {str(e)}")
            
            # Sleep for the polling interval
            self.stop_polling_flag.wait(self.polling_interval)
    
    def _update_production_status(self) -> None:
        """Update production status from JMS"""
        # Get all jobs with JMS order IDs
        for job_id, order_id in self.job_order_mappings.items():
            try:
                # Get job from scheduler
                job = self.scheduler_service.get_job(job_id)
                if not job:
                    continue
                
                # Get production status from JMS
                production_status = self.client.production.get_production_status(order_id)
                
                # Update job parts based on production status
                self._update_job_parts(job, production_status)
                
            except Exception as e:
                event_system.publish("error", f"Failed to update production status for job {job_id}: {str(e)}")
    
    def _update_job_parts(self, job: Job, production_status: Dict[str, Any]) -> None:
        """
        Update job parts based on production status
        
        Args:
            job: Job to update
            production_status: Production status from JMS
        """
        # Get current state
        state = production_status.get("state", "Unknown")
        
        # Get workpiece counts
        finished_count = production_status.get("finishedGoodWorkpieceCount", 0)
        error_count = production_status.get("finishedErrorWorkpieceCount", 0)
        in_progress_count = production_status.get("readyJobWorkpieceCount", 0)
        
        # Get job parts
        job_parts = self.scheduler_service.get_job_parts(job.job_id)
        
        # Update part statuses based on counts
        for i, part in enumerate(job_parts):
            if i < finished_count:
                if part.status != 'completed':
                    part.status = 'completed'
                    part.estimate = False
                    self.scheduler_service.update_part(part)
            elif i < finished_count + in_progress_count:
                if part.status != 'in-progress':
                    part.status = 'in-progress'
                    part.estimate = False
                    self.scheduler_service.update_part(part)
    
    def sync_job_to_jms(self, job: Job, priority: WorkpiecePriority = None) -> str:
        """
        Synchronize a job to JMS as an order with priority support
        
        Args:
            job: Job to synchronize
            priority: Optional workpiece priority information
            
        Returns:
            JMS order ID
            
        Raises:
            Exception: If synchronization fails
        """
        if not JMS_AVAILABLE or not self.client:
            error_msg = "Cannot synchronize job: JMS client not available"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
            
        # Check if job is already mapped to an order
        order_id = self.job_order_mappings.get(job.job_id)
        
        try:
            # Get job parts
            job_parts = self.scheduler_service.get_job_parts(job.job_id)
            if not job_parts:
                raise Exception("Job has no parts")
            
            # Get machine ID from first part
            machine_id = job_parts[0].machine_id
            if not machine_id:
                raise Exception("Job has no assigned machine")
            
            # Get machine from machine service
            machine = self.scheduler_service.machine_service.get_machine(machine_id)
            if not machine:
                raise Exception(f"Machine {machine_id} not found")
            
            # Get start date from first part
            start_date = datetime.fromtimestamp(job_parts[0].start_time / 1000)
            
            if order_id:
                # Update existing order
                updates = {
                    "name": job.name,
                    "plannedWorkpieceCount": job.total_parts,
                    "plannedManufacturingDate": start_date.isoformat()
                }
                
                # Add priority information if available
                if priority:
                    updates["priority"] = priority.get_effective_priority_score()
                    updates["rushOrder"] = priority.rush_order
                    if priority.due_date:
                        updates["dueDate"] = datetime.fromtimestamp(priority.due_date / 1000).isoformat()
                
                self.client.order.patch_order(order_id, updates)
            else:
                # Prepare order description with priority info
                description = f"Job created from NC Tool Analyzer"
                if priority:
                    description += f" - Priority: {priority.priority_level.upper()}"
                    if priority.rush_order:
                        description += " (RUSH ORDER)"
                
                # Create new order with priority
                order_data = self.client.order.create_order(
                    name=job.name,
                    cell=machine.name,  # Use machine name as cell
                    product_name=f"Product_{job.job_id}",
                    product_version="1.0",
                    planned_count=job.total_parts,
                    planned_date=start_date,
                    description=description,
                    available_for_cell=False,
                    locked=False
                )
                
                # Get order ID
                order_id = order_data.get("id")
                if not order_id:
                    raise Exception("Failed to get order ID from JMS response")
                
                # Save mapping
                self.job_order_mappings[job.job_id] = order_id
                self._save_mappings()
            
            return order_id
            
        except Exception as e:
            error_msg = f"Failed to synchronize job {job.job_id} to JMS: {str(e)}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def sync_jms_to_job(self, order_id: str) -> Job:
        """
        Synchronize a JMS order to a local job
        
        Args:
            order_id: JMS order ID
            
        Returns:
            Synchronized job
            
        Raises:
            Exception: If synchronization fails
        """
        if not JMS_AVAILABLE or not self.client:
            error_msg = "Cannot synchronize order: JMS client not available"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
            
        try:
            # Get order from JMS
            order_data = self.client.order.get_order(order_id)
            
            # Check if order is already mapped to a job
            job_id = None
            for j_id, o_id in self.job_order_mappings.items():
                if o_id == order_id:
                    job_id = j_id
                    break
            
            if job_id:
                # Update existing job
                job = self.scheduler_service.get_job(job_id)
                if not job:
                    raise Exception(f"Job {job_id} not found")
                
                # Update job properties
                job.name = order_data.get("name", job.name)
                job.total_parts = order_data.get("plannedWorkpieceCount", job.total_parts)
                
                # Update job in scheduler
                self.scheduler_service.update_job(job)
            else:
                # Create new job
                job = Job(
                    name=order_data.get("name", "JMS Order"),
                    total_parts=order_data.get("plannedWorkpieceCount", 1),
                    cycle_time=30.0  # Default cycle time (minutes)
                )
                
                # Add job to scheduler
                self.scheduler_service.add_job(job)
                
                # Get cell name
                cell_name = order_data.get("cell")
                
                # Find matching machine by name
                machine_id = None
                machines = self.scheduler_service.machine_service.get_all_machines()
                for m_id, machine in machines.items():
                    if machine.name == cell_name:
                        machine_id = m_id
                        break
                
                # Get planned date
                planned_date_str = order_data.get("plannedManufacturingDate")
                if planned_date_str:
                    planned_date = datetime.fromisoformat(planned_date_str.replace("Z", "+00:00"))
                    start_time = int(planned_date.timestamp() * 1000)
                else:
                    start_time = int(datetime.now().timestamp() * 1000)
                
                # Create parts
                for i in range(job.total_parts):
                    part = Part(
                        job_id=job.job_id,
                        part_number=i + 1,
                        machine_id=machine_id,
                        start_time=start_time + (i * int(job.cycle_time * 60 * 1000)),
                        estimate=True,
                        status='scheduled'
                    )
                    self.scheduler_service.add_part(part)
                
                # Save mapping
                self.job_order_mappings[job.job_id] = order_id
                self._save_mappings()
            
            return job
            
        except Exception as e:
            error_msg = f"Failed to synchronize JMS order {order_id} to job: {str(e)}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def get_machine_status(self, machine_id: str) -> Dict[str, Any]:
        """
        Get machine status from JMS
        
        Args:
            machine_id: Machine ID
            
        Returns:
            Machine status dictionary
            
        Raises:
            Exception: If request fails
        """
        if not JMS_AVAILABLE or not self.client:
            error_msg = "Cannot get machine status: JMS client not available"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
            
        try:
            # Get machine from machine service
            machine = self.scheduler_service.machine_service.get_machine(machine_id)
            if not machine:
                raise Exception(f"Machine {machine_id} not found")
            
            # Use machine name as cell and machine ID
            cell_id = machine.name
            jms_machine_id = machine.machine_id
            
            # Get machine status from JMS
            return self.client.mdc.get_machine_status(cell_id, jms_machine_id)
        except Exception as e:
            error_msg = f"Failed to get machine status for {machine_id}: {str(e)}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def test_connection(self) -> bool:
        """
        Test the connection to the JMS API
        
        Returns:
            True if connection is successful, False otherwise
        """
        if not JMS_AVAILABLE or not self.client:
            print("JMS client not available for connection test")
            return False
            
        # If requests is not available, return True for mock functionality
        if not REQUESTS_AVAILABLE:
            print("Using mock connection test")
            return True
            
        try:
            print(f"Testing connection to JMS API at {self.base_url}")
            result = self.client.test_connection()
            if result:
                print("Connection test successful")
            else:
                print("Connection test failed")
            return result
        except Exception as e:
            print(f"Connection test failed with exception: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    # Enhanced Priority Management Methods
    def sync_job_with_priority(self, job: Job, priority: WorkpiecePriority) -> str:
        """
        Synchronize job with priority information to JMS
        
        Args:
            job: Job to synchronize
            priority: Priority information
            
        Returns:
            JMS order ID
        """
        return self.sync_job_to_jms(job, priority)
    
    def update_workpiece_priority(self, order_id: str, priority_score: int) -> bool:
        """
        Update workpiece priority in JMS
        
        Args:
            order_id: JMS order ID
            priority_score: New priority score (1-100)
            
        Returns:
            True if successful
        """
        if not JMS_AVAILABLE or not self.client:
            return False
        
        try:
            updates = {"priority": priority_score}
            self.client.order.patch_order(order_id, updates)
            return True
        except Exception as e:
            event_system.publish("error", f"Failed to update JMS priority: {str(e)}")
            return False
    
    def get_real_time_status(self, order_ids: List[str]) -> Dict[str, Any]:
        """
        Get real-time status for multiple orders
        
        Args:
            order_ids: List of JMS order IDs
            
        Returns:
            Dictionary mapping order_id to status information
        """
        if not JMS_AVAILABLE or not self.client:
            return {}
        
        status_map = {}
        for order_id in order_ids:
            try:
                status = self.client.production.get_production_status(order_id)
                status_map[order_id] = status
            except Exception as e:
                event_system.publish("error", f"Failed to get status for order {order_id}: {str(e)}")
                status_map[order_id] = {"error": str(e)}
        
        return status_map
    
    def configure_polling_interval(self, minutes: int) -> None:
        """
        Configure the polling interval for real-time updates
        
        Args:
            minutes: Polling interval in minutes
        """
        if minutes < 1:
            minutes = 1  # Minimum 1 minute
        
        self.polling_interval = minutes * 60  # Convert to seconds
        
        # Restart polling with new interval if currently running
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_polling()
            time.sleep(1)  # Brief pause
            self.start_polling()
        
        event_system.publish("jms_polling_interval_changed", minutes)
    
    def get_connection_health(self) -> Dict[str, Any]:
        """
        Get JMS connection health information
        
        Returns:
            Dictionary with connection health details
        """
        health = {
            "available": JMS_AVAILABLE,
            "requests_available": REQUESTS_AVAILABLE if JMS_AVAILABLE else False,
            "client_initialized": self.client is not None,
            "polling_active": self.polling_thread and self.polling_thread.is_alive(),
            "polling_interval_seconds": self.polling_interval,
            "base_url": self.base_url,
            "job_mappings_count": len(self.job_order_mappings)
        }
        
        # Test connection if client is available
        if self.client and REQUESTS_AVAILABLE:
            try:
                health["connection_test"] = self.test_connection()
                health["last_test_time"] = datetime.now().isoformat()
            except Exception as e:
                health["connection_test"] = False
                health["connection_error"] = str(e)
        
        return health
    
    def get_enhanced_production_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get enhanced production status including priority and scheduling info
        
        Args:
            job_id: Local job ID
            
        Returns:
            Enhanced status information
        """
        order_id = self.job_order_mappings.get(job_id)
        if not order_id:
            return {"error": "Job not synced to JMS"}
        
        try:
            # Get basic production status
            status = self.client.production.get_production_status(order_id)
            
            # Get order details for priority info
            order_details = self.client.order.get_order(order_id)
            
            # Combine information
            enhanced_status = {
                **status,
                "order_details": order_details,
                "priority": order_details.get("priority", 50),
                "rush_order": order_details.get("rushOrder", False),
                "due_date": order_details.get("dueDate"),
                "jms_order_id": order_id,
                "local_job_id": job_id,
                "sync_timestamp": int(datetime.now().timestamp() * 1000)
            }
            
            return enhanced_status
            
        except Exception as e:
            return {
                "error": str(e),
                "jms_order_id": order_id,
                "local_job_id": job_id
            }
    
    def bulk_sync_jobs(self, jobs_with_priorities: List[Tuple[Job, WorkpiecePriority]]) -> Dict[str, Any]:
        """
        Synchronize multiple jobs to JMS in bulk
        
        Args:
            jobs_with_priorities: List of (job, priority) tuples
            
        Returns:
            Dictionary with sync results
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(jobs_with_priorities)
        }
        
        for job, priority in jobs_with_priorities:
            try:
                order_id = self.sync_job_with_priority(job, priority)
                results["successful"].append({
                    "job_id": job.job_id,
                    "job_name": job.name,
                    "order_id": order_id
                })
            except Exception as e:
                results["failed"].append({
                    "job_id": job.job_id,
                    "job_name": job.name,
                    "error": str(e)
                })
        
        event_system.publish("jms_bulk_sync_completed", results)
        return results
    
    def get_jms_statistics(self) -> Dict[str, Any]:
        """
        Get JMS integration statistics
        
        Returns:
            Dictionary with JMS statistics
        """
        stats = {
            "synced_jobs": len(self.job_order_mappings),
            "connection_health": self.get_connection_health(),
            "polling_status": {
                "active": self.polling_thread and self.polling_thread.is_alive(),
                "interval_minutes": self.polling_interval / 60
            }
        }
        
        # Add error counts if available
        try:
            # This would track errors over time - placeholder for now
            stats["error_counts"] = {
                "connection_errors": 0,
                "sync_errors": 0,
                "polling_errors": 0
            }
        except:
            pass
        
        return stats