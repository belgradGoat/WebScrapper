"""
Client for JMS Order resources
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from .jms_base_client import JMSBaseClient


class JMSOrderClient(JMSBaseClient):
    """Client for JMS Order resources"""
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Get all orders
        
        Returns:
            List of order data dictionaries
            
        Raises:
            Exception: If request fails
        """
        return self.get("Orders")
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get a specific order by ID
        
        Args:
            order_id: ID of the order to retrieve
            
        Returns:
            Order data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get(f"Order/{order_id}")
    
    def create_order(self, name: str, cell: str, product_name: str, 
                    product_version: str, planned_count: int,
                    planned_date: datetime, description: str = "",
                    available_for_cell: bool = False, locked: bool = False) -> Dict[str, Any]:
        """
        Create a new order
        
        Args:
            name: Order name (e.g., "OF-78-856")
            cell: Cell name (e.g., "EMC.0520")
            product_name: Product name
            product_version: Product version
            planned_count: Planned workpiece count
            planned_date: Planned manufacturing date
            description: Order description (optional)
            available_for_cell: Whether to make the order available for the cell (optional)
            locked: Whether the order is locked (optional)
            
        Returns:
            Created order data dictionary with generated ID
            
        Raises:
            Exception: If request fails
        """
        data = {
            "name": name,
            "description": description,
            "plannedManufacturingDate": planned_date.isoformat(),
            "plannedWorkpieceCount": planned_count,
            "availableForCell": available_for_cell,
            "product": {
                "name": product_name,
                "version": product_version
            },
            "cell": cell,
            "locked": locked
        }
        return self.post("Order", data)
    
    def update_order(self, order_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order (full update)
        
        Args:
            order_id: ID of the order to update
            data: Complete order data
            
        Returns:
            Updated order data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.put(f"Order/{order_id}", data)
    
    def patch_order(self, order_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Partially update an order
        
        Args:
            order_id: ID of the order to update
            updates: Partial order data with fields to update
                     (Name, Description, PlannedManufacturingDate, 
                      PlannedWorkpieceCount, Locked)
            
        Returns:
            Updated order data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.patch(f"Order/{order_id}", updates)
    
    def delete_order(self, order_id: str) -> bool:
        """
        Delete an order
        
        Args:
            order_id: ID of the order to delete
            
        Returns:
            True if successful
            
        Raises:
            Exception: If request fails
        """
        return self.delete(f"Order/{order_id}")
    
    def make_available_for_cell(self, order_id: str) -> Dict[str, Any]:
        """
        Make an order available for the cell (request transfer to production)
        
        Args:
            order_id: ID of the order to make available
            
        Returns:
            Updated order data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.patch_order(order_id, {"availableForCell": True})
    
    def lock_order(self, order_id: str) -> Dict[str, Any]:
        """
        Lock an order to prevent changes
        
        Args:
            order_id: ID of the order to lock
            
        Returns:
            Updated order data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.patch_order(order_id, {"locked": True})
    
    def unlock_order(self, order_id: str) -> Dict[str, Any]:
        """
        Unlock an order to allow changes
        
        Args:
            order_id: ID of the order to unlock
            
        Returns:
            Updated order data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.patch_order(order_id, {"locked": False})