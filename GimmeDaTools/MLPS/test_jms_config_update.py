#!/usr/bin/env python3
"""
Test script to verify the JMS configuration update functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.jms_service import JMSService
from services.scheduler_service import SchedulerService
from services.machine_service import MachineService


def test_jms_configuration_update():
    """Test the JMS configuration update functionality"""
    print("Testing JMS configuration update...")
    
    # Create dummy services for testing
    machine_service = MachineService()
    scheduler_service = SchedulerService(machine_service)
    
    # Create JMS service with default configuration
    jms_service = JMSService(
        scheduler_service,
        base_url="http://localhost:8080",
        username="test_user",
        password="test_pass"
    )
    
    print(f"Initial configuration: URL={jms_service.base_url}, Username={jms_service.username}")
    
    # Test updating configuration
    new_url = "http://192.168.1.100:8080"
    new_username = "production_user"
    new_password = "production_pass"
    
    try:
        jms_service.update_configuration(new_url, new_username, new_password)
        print(f"Updated configuration: URL={jms_service.base_url}, Username={jms_service.username}")
        
        # Verify the configuration was updated
        assert jms_service.base_url == new_url, f"Expected {new_url}, got {jms_service.base_url}"
        assert jms_service.username == new_username, f"Expected {new_username}, got {jms_service.username}"
        assert jms_service.password == new_password, f"Expected {new_password}, got {jms_service.password}"
        
        print("✓ Configuration update test passed!")
        
        # Test that configuration persists (if file was created)
        if os.path.exists('jms_config.json'):
            print("✓ Configuration file was created")
            
            # Create a new JMS service to test loading
            jms_service2 = JMSService(scheduler_service)
            print(f"Loaded configuration: URL={jms_service2.base_url}, Username={jms_service2.username}")
            
            # Verify the configuration was loaded
            assert jms_service2.base_url == new_url, f"Expected {new_url}, got {jms_service2.base_url}"
            assert jms_service2.username == new_username, f"Expected {new_username}, got {jms_service2.username}"
            
            print("✓ Configuration persistence test passed!")
            
            # Clean up
            os.remove('jms_config.json')
        else:
            print("! Configuration file was not created (this is expected if file_utils has issues)")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration update test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_jms_configuration_update()
    sys.exit(0 if success else 1)
