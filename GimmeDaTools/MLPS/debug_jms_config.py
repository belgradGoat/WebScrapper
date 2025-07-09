#!/usr/bin/env python3
"""
Debug script to test JMS configuration update issue
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.jms_service import JMSService
from services.scheduler_service import SchedulerService
from services.machine_service import MachineService

def debug_jms_configuration():
    """Debug the JMS configuration update issue"""
    print("=== Debugging JMS Configuration Update ===")
    
    # Create services
    machine_service = MachineService()
    scheduler_service = SchedulerService(machine_service)
    
    # Create JMS service with default configuration
    print("1. Creating JMS service with default configuration...")
    jms_service = JMSService(scheduler_service)
    print(f"   Initial URL: {jms_service.base_url}")
    print(f"   Initial client URL: {jms_service.client.base_url if jms_service.client else 'No client'}")
    if jms_service.client:
        print(f"   Initial auth client URL: {jms_service.client.auth_client.base_url}")
    
    print("\n2. Updating configuration to http://190.10.10.3:8080...")
    jms_service.update_configuration('http://190.10.10.3:8080', 'testuser', 'testpass')
    print(f"   After update URL: {jms_service.base_url}")
    print(f"   After update client URL: {jms_service.client.base_url if jms_service.client else 'No client'}")
    if jms_service.client:
        print(f"   After update auth client URL: {jms_service.client.auth_client.base_url}")
    
    print("\n3. Testing connection...")
    try:
        result = jms_service.test_connection()
        print(f"   Connection result: {result}")
    except Exception as e:
        print(f"   Connection failed with error: {str(e)}")
    
    print("\n4. Direct auth client test...")
    if jms_service.client:
        try:
            print(f"   Auth client base URL: {jms_service.client.auth_client.base_url}")
            print("   Attempting to get auth header...")
            auth_header = jms_service.client.auth_client.get_auth_header()
            print(f"   Auth header obtained: {auth_header}")
        except Exception as e:
            print(f"   Auth header failed: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_jms_configuration()
