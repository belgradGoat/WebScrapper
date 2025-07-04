"""
Client for JMS Machine Data Collection (MDC) Interface
"""
from typing import Dict, List, Any, Optional
from .jms_base_client import JMSBaseClient


class JMSMDCClient(JMSBaseClient):
    """Client for JMS Machine Data Collection Interface"""
    
    def __init__(self, base_url: str, auth_client=None):
        """
        Initialize the JMS MDC client
        
        Args:
            base_url: Base URL of the JMS API
            auth_client: JMSAuthClient instance (created if not provided)
        """
        super().__init__(base_url, auth_client)
        # MDC interface has a different base path
        self.api_base = f"{base_url}/mdc"
    
    def get_root(self) -> Dict[str, Any]:
        """
        Get the root resource
        
        Returns:
            Root resource data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get("")
    
    def get_all_cells(self) -> List[Dict[str, Any]]:
        """
        Get all cells
        
        Returns:
            List of cell data dictionaries
            
        Raises:
            Exception: If request fails
        """
        root = self.get_root()
        return root.get("cells", [])
    
    def get_cell(self, cell_id: str) -> Dict[str, Any]:
        """
        Get status for a specific cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            Cell data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get(f"Cell/{cell_id}")
    
    def get_cell_machines(self, cell_id: str) -> List[Dict[str, Any]]:
        """
        Get all machines in a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            List of machine data dictionaries
            
        Raises:
            Exception: If request fails
        """
        cell = self.get_cell(cell_id)
        return cell.get("machines", [])
    
    def get_machine_status(self, cell_id: str, machine_id: str) -> Dict[str, Any]:
        """
        Get status for a specific machine
        
        Args:
            cell_id: ID of the cell
            machine_id: ID of the machine
            
        Returns:
            Machine state data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get(f"Cell/{cell_id}/Machine/{machine_id}/MachineState")
    
    def get_machine_state(self, cell_id: str, machine_id: str) -> str:
        """
        Get the current state of a machine
        
        Args:
            cell_id: ID of the cell
            machine_id: ID of the machine
            
        Returns:
            Machine state string (Running, Stopped, Ready, NotReady, OutOfJob, Error)
            
        Raises:
            Exception: If request fails
        """
        status = self.get_machine_status(cell_id, machine_id)
        return status.get("currentMachineState", "Unknown")
    
    def get_machine_workpiece_count(self, cell_id: str, machine_id: str) -> int:
        """
        Get the absolute workpiece count for a machine
        
        Args:
            cell_id: ID of the cell
            machine_id: ID of the machine
            
        Returns:
            Total produced workpieces
            
        Raises:
            Exception: If request fails
        """
        status = self.get_machine_status(cell_id, machine_id)
        return status.get("absoluteMachineWorkpieceCount", 0)
    
    def get_machine_autonomy(self, cell_id: str, machine_id: str) -> float:
        """
        Get the autonomy duration for a machine
        
        Args:
            cell_id: ID of the cell
            machine_id: ID of the machine
            
        Returns:
            Estimated production time based on pending orders (in minutes)
            
        Raises:
            Exception: If request fails
        """
        status = self.get_machine_status(cell_id, machine_id)
        return status.get("autonomyDuration", 0.0)
    
    def get_machine_alarms(self, cell_id: str, machine_id: str) -> List[Dict[str, Any]]:
        """
        Get current pending alarms for a machine
        
        Args:
            cell_id: ID of the cell
            machine_id: ID of the machine
            
        Returns:
            List of alarm data dictionaries
            
        Raises:
            Exception: If request fails
        """
        status = self.get_machine_status(cell_id, machine_id)
        return status.get("alarms", [])
    
    def get_robot_status(self, cell_id: str) -> Dict[str, Any]:
        """
        Get status for the robot in a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            Robot state data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get(f"Cell/{cell_id}/Robot/RobotState")
    
    def get_robot_state(self, cell_id: str) -> str:
        """
        Get the current state of the robot in a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            Robot state string (Running, Ready, NotReady, Error, Disconnected)
            
        Raises:
            Exception: If request fails
        """
        status = self.get_robot_status(cell_id)
        return status.get("currentRobotState", "Unknown")
    
    def get_robot_alarms(self, cell_id: str) -> List[Dict[str, Any]]:
        """
        Get current pending alarms for the robot in a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            List of alarm data dictionaries
            
        Raises:
            Exception: If request fails
        """
        status = self.get_robot_status(cell_id)
        return status.get("alarms", [])