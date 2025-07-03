"""
Service for integrating JMS API with the scheduler
"""
import threading
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from models.job import Job
from models.part import Part
from utils.event_system import event_system
from utils.file_utils import load_json_file, save_json_file
from services.jms.jms_client import JMSClient


class JMSService:
    """Service for integrating JMS API with the scheduler"""
    
    def __init__(
        self, 
        scheduler_service,
        base_url: str = "http://localhost:8080",
        polling_interval: int = 30,
        mapping_file: str = "jms_mapping.json"
    ):
        """
        Initialize the JMS service
        
        Args:
            scheduler_service: SchedulerService instance
            base_url: Base URL of the JMS API
            polling_interval: Interval for polling production updates (seconds)
            mapping_file: Path to the file storing job-order mappings
        """
        self.scheduler_service = scheduler_service
        self.client = JMSClient(base_url)
        self.polling_interval = polling_interval
        self.mapping_file = mapping_file
        
        # Thread for background polling
        self.polling_thread = None
        self.stop_polling_flag = threading.Event()
        
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
        if self.polling_thread and self.polling_thread.is_alive():
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
    
    def sync_job_to_jms(self, job: Job) -> str:
        """
        Synchronize a job to JMS as an order
        
        Args:
            job: Job to synchronize
            
        Returns:
            JMS order ID
            
        Raises:
            Exception: If synchronization fails
        """
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
                self.client.order.patch_order(order_id, updates)
            else:
                # Create new order
                order_data = self.client.order.create_order(
                    name=job.name,
                    cell=machine.name,  # Use machine name as cell
                    product_name=f"Product_{job.job_id}",
                    product_version="1.0",
                    planned_count=job.total_parts,
                    planned_date=start_date,
                    description=f"Job created from NC Tool Analyzer",
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
        try:
            return self.client.test_connection()
        except Exception:
            return False