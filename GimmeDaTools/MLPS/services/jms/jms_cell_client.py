"""
Client for JMS Cell resources
"""
from typing import Dict, List, Any, Optional
from .jms_base_client import JMSBaseClient


class JMSCellClient(JMSBaseClient):
    """Client for JMS Cell resources"""
    
    def get_all_cells(self) -> List[Dict[str, Any]]:
        """
        Get all cells
        
        Returns:
            List of cell data dictionaries
            
        Raises:
            Exception: If request fails
        """
        return self.get("Cells")
    
    def get_cell(self, cell_id: str) -> Dict[str, Any]:
        """
        Get a specific cell by ID
        
        Args:
            cell_id: ID of the cell to retrieve
            
        Returns:
            Cell data dictionary
            
        Raises:
            Exception: If request fails
        """
        return self.get(f"Cell/{cell_id}")
    
    def get_cell_pallet_types(self, cell_id: str) -> List[str]:
        """
        Get supported pallet types for a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            List of supported pallet types (e.g., MTS, ITS148, UPC)
            
        Raises:
            Exception: If request fails
        """
        cell_data = self.get_cell(cell_id)
        return cell_data.get("supportedPalletTypes", [])
    
    def get_cell_fixture_types(self, cell_id: str) -> List[str]:
        """
        Get defined fixture types for a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            List of defined fixture types
            
        Raises:
            Exception: If request fails
        """
        cell_data = self.get_cell(cell_id)
        return cell_data.get("definedFixtureTypes", [])
    
    def get_cell_resource_groups(self, cell_id: str) -> List[str]:
        """
        Get supported resource groups for a cell
        
        Args:
            cell_id: ID of the cell
            
        Returns:
            List of supported resource groups
            
        Raises:
            Exception: If request fails
        """
        cell_data = self.get_cell(cell_id)
        return cell_data.get("supportedResourceGroups", [])