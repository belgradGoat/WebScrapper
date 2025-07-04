#!/usr/bin/env python3
"""
JMS Robotic Cell Operations Test
Tests various operations related to robotic cells via JMS API
"""
import json
import sys
import os
import logging
from typing import List, Dict, Any, Optional

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robotic_cell_tester")

# Check if JMS client is available
try:
    from services.jms.jms_client import JMSClient
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = True
except ImportError:
    JMS_AVAILABLE = False
    logger.error("JMS client modules not found. Please ensure the JMS modules are installed.")
    sys.exit(1)

class RoboticCellTester:
    """Tests robotic cell operations via JMS API"""
    
    def __init__(self, base_url: str):
        """
        Initialize the tester
        
        Args:
            base_url: JMS API base URL (e.g., "https://10.164.181.100")
        """
        self.base_url = base_url
        self.jms_client = None
        
        try:
            self.jms_client = JMSClient(base_url)
            logger.info(f"Initialized JMS client with URL: {base_url}")
            
            # Test connection
            if not self.jms_client.test_connection():
                logger.error("Failed to connect to JMS API")
                sys.exit(1)
            logger.info("Successfully connected to JMS API")
        except Exception as e:
            logger.error(f"Failed to initialize JMS client: {str(e)}")
            sys.exit(1)
    
    def list_cells(self) -> List[Dict[str, Any]]:
        """
        List all available cells
        
        Returns:
            List of cell dictionaries
        """
        print("\n=== AVAILABLE CELLS ===")
        
        # Get cells from MDC interface
        try:
            mdc_cells = self.jms_client.mdc.get_all_cells()
            print(f"Found {len(mdc_cells)} cells in MDC interface:")
            for cell in mdc_cells:
                print(f"  - {cell.get('name', 'Unknown')} (ID: {cell.get('id', 'Unknown')})")
        except Exception as e:
            logger.error(f"Error retrieving MDC cells: {str(e)}")
            print(f"Error retrieving MDC cells: {str(e)}")
            mdc_cells = []
        
        # Get cells from Cell interface
        try:
            cells = self.jms_client.cell.get_all_cells()
            print(f"\nFound {len(cells)} cells in Cell interface:")
            for cell in cells:
                print(f"  - {cell.get('name', 'Unknown')} (ID: {cell.get('id', 'Unknown')})")
        except Exception as e:
            logger.error(f"Error retrieving cells: {str(e)}")
            print(f"Error retrieving cells: {str(e)}")
            cells = []
            
        return cells
    
    def test_cell_details(self, cell_id: str) -> None:
        """
        Test retrieving cell details
        
        Args:
            cell_id: ID of the cell to test
        """
        print(f"\n=== CELL DETAILS: {cell_id} ===")
        
        try:
            # Get cell details
            cell = self.jms_client.cell.get_cell(cell_id)
            print(f"Name: {cell.get('name', 'Unknown')}")
            print(f"Description: {cell.get('description', 'N/A')}")
            
            # Get pallet types
            try:
                pallet_types = self.jms_client.cell.get_cell_pallet_types(cell_id)
                print(f"Supported pallet types: {', '.join(pallet_types) if pallet_types else 'None'}")
            except Exception as e:
                logger.error(f"Error retrieving pallet types: {str(e)}")
                print(f"Error retrieving pallet types: {str(e)}")
            
            # Get fixture types
            try:
                fixture_types = self.jms_client.cell.get_cell_fixture_types(cell_id)
                print(f"Defined fixture types: {', '.join(fixture_types) if fixture_types else 'None'}")
            except Exception as e:
                logger.error(f"Error retrieving fixture types: {str(e)}")
                print(f"Error retrieving fixture types: {str(e)}")
            
            # Get resource groups
            try:
                resource_groups = self.jms_client.cell.get_cell_resource_groups(cell_id)
                print(f"Supported resource groups: {', '.join(resource_groups) if resource_groups else 'None'}")
            except Exception as e:
                logger.error(f"Error retrieving resource groups: {str(e)}")
                print(f"Error retrieving resource groups: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error retrieving cell details: {str(e)}")
            print(f"Error retrieving cell details: {str(e)}")
    
    def test_robot_status(self, cell_id: str) -> None:
        """
        Test retrieving robot status
        
        Args:
            cell_id: ID of the cell containing the robot
        """
        print(f"\n=== ROBOT STATUS: {cell_id} ===")
        
        try:
            # Get robot status
            robot_status = self.jms_client.mdc.get_robot_status(cell_id)
            robot_state = self.jms_client.mdc.get_robot_state(cell_id)
            robot_alarms = self.jms_client.mdc.get_robot_alarms(cell_id)
            
            print(f"Current state: {robot_state}")
            print(f"Alarms: {len(robot_alarms)}")
            if robot_alarms:
                for alarm in robot_alarms:
                    print(f"  - {alarm.get('message', 'Unknown alarm')}")
            
            # Print full status (formatted)
            print("\nFull status:")
            print(json.dumps(robot_status, indent=2))
            
        except Exception as e:
            logger.error(f"Error retrieving robot status: {str(e)}")
            print(f"Error retrieving robot status: {str(e)}")
    
    def test_machine_status(self, cell_id: str) -> None:
        """
        Test retrieving machine status for all machines in a cell
        
        Args:
            cell_id: ID of the cell containing the machines
        """
        print(f"\n=== MACHINE STATUS: {cell_id} ===")
        
        try:
            # Get machines in cell
            machines = self.jms_client.mdc.get_cell_machines(cell_id)
            print(f"Found {len(machines)} machines in cell")
            
            for machine in machines:
                machine_id = machine.get('id')
                machine_name = machine.get('name', 'Unknown')
                
                print(f"\nMachine: {machine_name} (ID: {machine_id})")
                
                try:
                    # Get machine status
                    status = self.jms_client.mdc.get_machine_status(cell_id, machine_id)
                    state = self.jms_client.mdc.get_machine_state(cell_id, machine_id)
                    
                    print(f"Current state: {state}")
                    print(f"Current program: {status.get('runningNCProgram', 'N/A')}")
                    print(f"Workpiece count: {status.get('absoluteMachineWorkpieceCount', 0)}")
                    print(f"Autonomy: {status.get('autonomyDuration', 0):.1f} minutes")
                    
                    # Get alarms
                    alarms = self.jms_client.mdc.get_machine_alarms(cell_id, machine_id)
                    print(f"Alarms: {len(alarms)}")
                    if alarms:
                        for alarm in alarms:
                            print(f"  - {alarm.get('message', 'Unknown alarm')}")
                except Exception as e:
                    logger.error(f"Error retrieving status for machine {machine_id}: {str(e)}")
                    print(f"Error retrieving status for machine {machine_id}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error retrieving machine status: {str(e)}")
            print(f"Error retrieving machine status: {str(e)}")
    
    def test_orders_for_cell(self, cell_id: str) -> None:
        """
        Test retrieving orders for a specific cell
        
        Args:
            cell_id: ID of the cell
        """
        print(f"\n=== ORDERS FOR CELL: {cell_id} ===")
        
        try:
            # Get all orders
            all_orders = self.jms_client.order.get_all_orders()
            
            # Filter orders for this cell
            cell_orders = [order for order in all_orders if order.get('cell') == cell_id]
            
            print(f"Found {len(cell_orders)} orders for cell {cell_id}")
            
            for order in cell_orders:
                order_id = order.get('id')
                order_name = order.get('name', 'Unknown')
                
                print(f"\nOrder: {order_name} (ID: {order_id})")
                print(f"Description: {order.get('description', 'N/A')}")
                print(f"Planned date: {order.get('plannedManufacturingDate', 'N/A')}")
                print(f"Planned count: {order.get('plannedWorkpieceCount', 0)}")
                print(f"Available for cell: {order.get('availableForCell', False)}")
                print(f"Locked: {order.get('locked', False)}")
                
                # Get production status if available
                try:
                    production_status = self.jms_client.production.get_production_status(order_id)
                    state = production_status.get('state', 'Unknown')
                    counts = self.jms_client.production.get_workpiece_counts(order_id)
                    completion = self.jms_client.production.get_completion_percentage(order_id)
                    
                    print(f"Production state: {state}")
                    print(f"Finished good: {counts.get('finishedGoodWorkpieceCount', 0)}")
                    print(f"Finished error: {counts.get('finishedErrorWorkpieceCount', 0)}")
                    print(f"Ready loaded: {counts.get('readyLoadedWorkpieceCount', 0)}")
                    print(f"Ready job: {counts.get('readyJobWorkpieceCount', 0)}")
                    print(f"Completion: {completion:.1f}%")
                except Exception as e:
                    logger.error(f"Error retrieving production status for order {order_id}: {str(e)}")
                    print(f"Error retrieving production status for order {order_id}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error retrieving orders: {str(e)}")
            print(f"Error retrieving orders: {str(e)}")
    
    def run_all_tests(self, cell_id: Optional[str] = None) -> None:
        """
        Run all tests for a cell
        
        Args:
            cell_id: ID of the cell to test (if None, will use the first available cell)
        """
        # List all cells
        cells = self.list_cells()
        
        if not cells:
            print("No cells found")
            return
        
        # Use provided cell ID or first available cell
        test_cell_id = cell_id if cell_id else cells[0].get('id')
        
        if not test_cell_id:
            print("No valid cell ID found")
            return
        
        print(f"\nRunning all tests for cell: {test_cell_id}")
        
        # Run tests
        self.test_cell_details(test_cell_id)
        self.test_robot_status(test_cell_id)
        self.test_machine_status(test_cell_id)
        self.test_orders_for_cell(test_cell_id)
        
        print("\nAll tests completed")

def main():
    """Main function"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test robotic cell operations via JMS API')
    parser.add_argument('--url', type=str, default="https://10.164.181.100",
                        help='JMS API base URL (default: https://10.164.181.100)')
    parser.add_argument('--cell', type=str, default=None,
                        help='Cell ID to test (default: first available cell)')
    parser.add_argument('--test', type=str, choices=['all', 'cells', 'details', 'robot', 'machines', 'orders'],
                        default='all', help='Test to run (default: all)')
    
    args = parser.parse_args()
    
    # Create tester
    tester = RoboticCellTester(args.url)
    
    # Run selected test
    if args.test == 'all':
        tester.run_all_tests(args.cell)
    elif args.test == 'cells':
        tester.list_cells()
    elif args.cell:
        if args.test == 'details':
            tester.test_cell_details(args.cell)
        elif args.test == 'robot':
            tester.test_robot_status(args.cell)
        elif args.test == 'machines':
            tester.test_machine_status(args.cell)
        elif args.test == 'orders':
            tester.test_orders_for_cell(args.cell)
    else:
        print("Cell ID is required for specific tests")
        parser.print_help()

if __name__ == "__main__":
    main()