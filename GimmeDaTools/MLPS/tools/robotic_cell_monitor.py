#!/usr/bin/env python3
"""
JMS Robotic Cell Status Monitor
Continuously monitors and displays the status of robots and machines in a cell
"""
import time
import json
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robotic_cell_monitor")

# Check if JMS client is available
try:
    from services.jms.jms_client import JMSClient
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = True
except ImportError:
    JMS_AVAILABLE = False
    logger.error("JMS client modules not found. Please ensure the JMS modules are installed.")
    sys.exit(1)

class RoboticCellMonitor:
    """Monitor for robotic cell status"""
    
    def __init__(self, base_url, cell_id, interval=10):
        """
        Initialize the monitor
        
        Args:
            base_url: JMS API base URL (e.g., "https://10.164.181.100")
            cell_id: ID of the cell to monitor
            interval: Polling interval in seconds
        """
        self.base_url = base_url
        self.cell_id = cell_id
        self.interval = interval
        self.jms_client = None
        
        # Initialize JMS client
        try:
            self.jms_client = JMSClient(base_url)
            logger.info(f"JMS client initialized with URL: {base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize JMS client: {str(e)}")
            sys.exit(1)
    
    def start_monitoring(self):
        """Start monitoring the robotic cell"""
        logger.info(f"Starting robotic cell monitor for cell {self.cell_id}")
        logger.info(f"JMS API URL: {self.base_url}")
        logger.info(f"Polling interval: {self.interval} seconds")
        print("-" * 80)
        
        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n[{timestamp}] Polling cell status...")
                
                # Get cell details
                try:
                    cell = self.jms_client.mdc.get_cell(self.cell_id)
                    print(f"Cell: {cell.get('name', 'Unknown')} (ID: {self.cell_id})")
                    
                    # Get robot status
                    robot_status = self.jms_client.mdc.get_robot_status(self.cell_id)
                    robot_state = self.jms_client.mdc.get_robot_state(self.cell_id)
                    robot_alarms = self.jms_client.mdc.get_robot_alarms(self.cell_id)
                    
                    print("\nROBOT STATUS:")
                    print(f"  State: {robot_state}")
                    print(f"  Alarms: {len(robot_alarms)}")
                    if robot_alarms:
                        for alarm in robot_alarms:
                            print(f"    - {alarm.get('message', 'Unknown alarm')}")
                    
                    # Get machines in cell
                    machines = self.jms_client.mdc.get_cell_machines(self.cell_id)
                    print(f"\nMACHINES ({len(machines)}):")
                    
                    for machine in machines:
                        machine_id = machine.get('id')
                        machine_name = machine.get('name', 'Unknown')
                        
                        # Get machine status
                        machine_state = self.jms_client.mdc.get_machine_state(self.cell_id, machine_id)
                        workpiece_count = self.jms_client.mdc.get_machine_workpiece_count(self.cell_id, machine_id)
                        autonomy = self.jms_client.mdc.get_machine_autonomy(self.cell_id, machine_id)
                        alarms = self.jms_client.mdc.get_machine_alarms(self.cell_id, machine_id)
                        
                        print(f"  Machine: {machine_name} (ID: {machine_id})")
                        print(f"    State: {machine_state}")
                        print(f"    Workpiece Count: {workpiece_count}")
                        print(f"    Autonomy: {autonomy:.1f} minutes")
                        print(f"    Alarms: {len(alarms)}")
                        if alarms:
                            for alarm in alarms:
                                print(f"      - {alarm.get('message', 'Unknown alarm')}")
                    
                except Exception as e:
                    logger.error(f"Error polling cell status: {str(e)}")
                    print(f"Error polling cell status: {str(e)}")
                
                # Wait for next polling interval
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            print("\nMonitoring stopped by user")

def main():
    """Main function"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor a robotic cell via JMS API')
    parser.add_argument('--url', type=str, default="https://10.164.181.100",
                        help='JMS API base URL (default: https://10.164.181.100)')
    parser.add_argument('--cell', type=str, default="EMC.0520",
                        help='Cell ID to monitor (default: EMC.0520)')
    parser.add_argument('--interval', type=int, default=30,
                        help='Polling interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Create and start monitor
    monitor = RoboticCellMonitor(args.url, args.cell, args.interval)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()