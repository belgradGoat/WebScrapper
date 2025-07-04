#!/usr/bin/env python3
"""
JMS Robotic Cell Integration Test
Tests the complete integration workflow with a robotic cell
"""
import time
import json
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robotic_cell_integration")

# Check if JMS client is available
try:
    from services.jms.jms_client import JMSClient
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = True
except ImportError:
    JMS_AVAILABLE = False
    logger.error("JMS client modules not found. Please ensure the JMS modules are installed.")
    sys.exit(1)

class RoboticCellIntegrationTester:
    """Tests complete integration workflow with a robotic cell"""
    
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
    
    def get_available_cells(self) -> List[Dict[str, Any]]:
        """
        Get all available cells
        
        Returns:
            List of cell dictionaries
        """
        try:
            cells = self.jms_client.cell.get_all_cells()
            logger.info(f"Found {len(cells)} cells")
            return cells
        except Exception as e:
            logger.error(f"Error retrieving cells: {str(e)}")
            return []
    
    def run_integration_test(self, cell_id: str, monitoring_time: int = 60) -> bool:
        """
        Run a complete integration test with a robotic cell
        
        Args:
            cell_id: ID of the cell to test
            monitoring_time: Time to monitor production status (seconds)
            
        Returns:
            True if test was successful, False otherwise
        """
        print(f"\n=== STARTING INTEGRATION TEST FOR CELL: {cell_id} ===")
        logger.info(f"Starting integration test for cell {cell_id}")
        
        # Step 1: Verify cell exists and get details
        print("\nStep 1: Verifying cell exists and getting details...")
        try:
            cell = self.jms_client.cell.get_cell(cell_id)
            print(f"Cell verified: {cell.get('name', 'Unknown')} (ID: {cell_id})")
            logger.info(f"Cell verified: {cell.get('name', 'Unknown')} (ID: {cell_id})")
        except Exception as e:
            error_msg = f"Error: Cell {cell_id} not found - {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            return False
        
        # Step 2: Check cell status (machines and robot)
        print("\nStep 2: Checking cell status...")
        try:
            # Check robot status
            robot_state = self.jms_client.mdc.get_robot_state(cell_id)
            print(f"Robot state: {robot_state}")
            logger.info(f"Robot state: {robot_state}")
            
            # Check machine status
            machines = self.jms_client.mdc.get_cell_machines(cell_id)
            print(f"Found {len(machines)} machines in cell")
            logger.info(f"Found {len(machines)} machines in cell")
            
            for machine in machines:
                machine_id = machine.get('id')
                machine_name = machine.get('name', 'Unknown')
                machine_state = self.jms_client.mdc.get_machine_state(cell_id, machine_id)
                print(f"  Machine {machine_name}: {machine_state}")
                logger.info(f"Machine {machine_name}: {machine_state}")
        except Exception as e:
            error_msg = f"Error checking cell status: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            return False
        
        # Step 3: Create a test order for the cell
        print("\nStep 3: Creating test order...")
        try:
            order_name = f"TEST_ORDER_{int(time.time())}"
            planned_date = datetime.now() + timedelta(days=1)
            
            order_data = self.jms_client.order.create_order(
                name=order_name,
                cell=cell_id,
                product_name="TEST_PRODUCT",
                product_version="1.0",
                planned_count=5,
                planned_date=planned_date,
                description="Test order created by integration test",
                available_for_cell=False,
                locked=False
            )
            
            order_id = order_data.get('id')
            print(f"Test order created: {order_name} (ID: {order_id})")
            logger.info(f"Test order created: {order_name} (ID: {order_id})")
        except Exception as e:
            error_msg = f"Error creating test order: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            return False
        
        # Step 4: Make order available for cell
        print("\nStep 4: Making order available for cell...")
        try:
            self.jms_client.order.make_available_for_cell(order_id)
            print(f"Order {order_id} is now available for cell {cell_id}")
            logger.info(f"Order {order_id} is now available for cell {cell_id}")
        except Exception as e:
            error_msg = f"Error making order available for cell: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            
            # Try to clean up
            try:
                self.jms_client.order.delete_order(order_id)
                logger.info(f"Cleaned up test order {order_id}")
            except:
                pass
                
            return False
        
        # Step 5: Monitor production status
        print("\nStep 5: Monitoring production status...")
        try:
            # Check initial production status
            production_status = self.jms_client.production.get_production_status(order_id)
            state = self.jms_client.production.get_production_state(order_id)
            print(f"Initial production state: {state}")
            logger.info(f"Initial production state: {state}")
            
            # Monitor for a specified period
            print(f"Monitoring production status for {monitoring_time} seconds...")
            start_time = time.time()
            while time.time() - start_time < monitoring_time:
                state = self.jms_client.production.get_production_state(order_id)
                counts = self.jms_client.production.get_workpiece_counts(order_id)
                completion = self.jms_client.production.get_completion_percentage(order_id)
                
                status_msg = (f"[{time.strftime('%H:%M:%S')}] State: {state}, " +
                      f"Finished: {counts.get('finishedGoodWorkpieceCount', 0)}/{counts.get('plannedWorkpieceCount', 0)}, " +
                      f"Completion: {completion:.1f}%")
                print(status_msg)
                logger.info(status_msg)
                
                time.sleep(10)
        except Exception as e:
            error_msg = f"Error monitoring production status: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            # Continue with test
        
        # Step 6: Clean up (delete test order)
        print("\nStep 6: Cleaning up (deleting test order)...")
        try:
            self.jms_client.order.delete_order(order_id)
            print(f"Test order {order_id} deleted")
            logger.info(f"Test order {order_id} deleted")
        except Exception as e:
            error_msg = f"Error deleting test order: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            # Continue with test
        
        print("\n=== INTEGRATION TEST COMPLETED ===")
        logger.info("Integration test completed")
        return True
    
    def run_test_with_first_available_cell(self, monitoring_time: int = 60) -> bool:
        """
        Run integration test with the first available cell
        
        Args:
            monitoring_time: Time to monitor production status (seconds)
            
        Returns:
            True if test was successful, False otherwise
        """
        cells = self.get_available_cells()
        
        if not cells:
            print("No cells found")
            logger.error("No cells found")
            return False
        
        cell_id = cells[0].get('id')
        if not cell_id:
            print("No valid cell ID found")
            logger.error("No valid cell ID found")
            return False
        
        return self.run_integration_test(cell_id, monitoring_time)

def main():
    """Main function"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run integration test with a robotic cell via JMS API')
    parser.add_argument('--url', type=str, default="https://10.164.181.100",
                        help='JMS API base URL (default: https://10.164.181.100)')
    parser.add_argument('--cell', type=str, default=None,
                        help='Cell ID to test (default: first available cell)')
    parser.add_argument('--time', type=int, default=60,
                        help='Time to monitor production status in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Create tester
    tester = RoboticCellIntegrationTester(args.url)
    
    # Run test
    if args.cell:
        tester.run_integration_test(args.cell, args.time)
    else:
        tester.run_test_with_first_available_cell(args.time)

if __name__ == "__main__":
    main()