"""
Client for JMS Production resources
"""
from typing import Dict, Any, Optional, List
from .jms_base_client import JMSBaseClient


class JMSProductionClient(JMSBaseClient):
    """Client for JMS Production resources"""
    
    def get_production_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get production status for an order
        
        Args:
            order_id: ID of the order
            
        Returns:
            Production status data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get(f"Order/Production/{order_id}")
    
    def get_production_state(self, order_id: str) -> str:
        """
        Get the production state of an order
        
        Args:
            order_id: ID of the order
            
        Returns:
            Production state string (NotStarted, SetupStarted, ReadyToProduce,
                                    InProcess, Paused, Finished, Error)
            
        Raises:
            Exception: If request fails
        """
        status = self.get_production_status(order_id)
        return status.get("state", "Unknown")
    
    def get_workpiece_counts(self, order_id: str) -> Dict[str, int]:
        """
        Get workpiece counts for an order
        
        Args:
            order_id: ID of the order
            
        Returns:
            Dictionary with workpiece counts:
                - plannedWorkpieceCount: Initial planned quantity
                - setupWorkpieceCount: Workpieces set up by the operator
                - readyLoadedWorkpieceCount: Workpieces ready in the robot magazine
                - readyJobWorkpieceCount: Workpieces with a "ready job" state for machining
                - finishedGoodWorkpieceCount: Number of successfully produced workpieces
                - finishedErrorWorkpieceCount: Number of workpieces finished with an invalid state
            
        Raises:
            Exception: If request fails
        """
        status = self.get_production_status(order_id)
        return {
            "plannedWorkpieceCount": status.get("plannedWorkpieceCount", 0),
            "setupWorkpieceCount": status.get("setupWorkpieceCount", 0),
            "readyLoadedWorkpieceCount": status.get("readyLoadedWorkpieceCount", 0),
            "readyJobWorkpieceCount": status.get("readyJobWorkpieceCount", 0),
            "finishedGoodWorkpieceCount": status.get("finishedGoodWorkpieceCount", 0),
            "finishedErrorWorkpieceCount": status.get("finishedErrorWorkpieceCount", 0)
        }
    
    def get_machining_times(self, order_id: str) -> Dict[str, float]:
        """
        Get machining times for an order
        
        Args:
            order_id: ID of the order
            
        Returns:
            Dictionary with machining times:
                - totalOrderMachiningTime: Cumulative machining time
                - averageWorkpieceMachiningTime: Average time per workpiece
            
        Raises:
            Exception: If request fails
        """
        status = self.get_production_status(order_id)
        return {
            "totalOrderMachiningTime": status.get("totalOrderMachiningTime", 0.0),
            "averageWorkpieceMachiningTime": status.get("averageWorkpieceMachiningTime", 0.0)
        }
    
    def is_order_finished(self, order_id: str) -> bool:
        """
        Check if an order is finished
        
        Args:
            order_id: ID of the order
            
        Returns:
            True if the order is finished, False otherwise
            
        Raises:
            Exception: If request fails
        """
        state = self.get_production_state(order_id)
        return state == "Finished"
    
    def is_order_in_error(self, order_id: str) -> bool:
        """
        Check if an order is in error state
        
        Args:
            order_id: ID of the order
            
        Returns:
            True if the order is in error state, False otherwise
            
        Raises:
            Exception: If request fails
        """
        state = self.get_production_state(order_id)
        return state == "Error"
    
    def get_completion_percentage(self, order_id: str) -> float:
        """
        Calculate the completion percentage of an order
        
        Args:
            order_id: ID of the order
            
        Returns:
            Completion percentage (0-100)
            
        Raises:
            Exception: If request fails
        """
        counts = self.get_workpiece_counts(order_id)
        planned = counts["plannedWorkpieceCount"]
        finished = counts["finishedGoodWorkpieceCount"]
        
        if planned == 0:
            return 0.0
            
        return (finished / planned) * 100.0