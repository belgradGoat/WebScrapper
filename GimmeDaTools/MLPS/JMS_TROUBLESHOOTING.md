# JMS Integration Troubleshooting Guide

This guide provides instructions for troubleshooting issues with the JMS API integration in the NC Tool Analyzer application.

## Prerequisites

The JMS integration requires the Python `requests` module. You can install it using pip:

```bash
pip install requests
```

## Diagnosing Issues

If you're experiencing issues with the JMS integration, follow these steps to diagnose the problem:

### 1. Run the Test Script

Run the `test_requests.py` script to check if the requests module is available in your Python environment:

```bash
python test_requests.py
```

This script will:
- Print your Python version and executable path
- Show your Python path (where Python looks for modules)
- Check if the requests module is available
- Try to make a test request to httpbin.org

### 2. Check the Application Log

After running the application, check the `app.log` file for any errors or warnings related to the requests module:

```bash
cat app.log
```

Look for lines containing:
- "Found requests module spec at: ..."
- "Successfully imported requests module from: ..."
- "Error checking for requests module: ..."

### 3. Check Console Output

When running the application, check the console output for debugging messages from the JMS authentication module:

```bash
python main.py
```

Look for lines containing:
- "Python path: ..."
- "Attempting to import requests module..."
- "Successfully imported requests module from: ..."
- "Failed to import requests module: ..."

## Common Issues and Solutions

### 1. Module Not Found

If the requests module is not found, but you've installed it with pip, the issue might be:

- **Multiple Python Installations**: You might have installed requests for a different Python installation than the one running the application.
  - Solution: Use the specific Python executable to install requests: `/path/to/python -m pip install requests`

- **Virtual Environment**: You might be running the application outside of the virtual environment where requests is installed.
  - Solution: Activate the virtual environment before running the application.

- **Path Issues**: Python might not be looking in the right place for the module.
  - Solution: Check the Python path in the debug output and make sure the requests module is installed in one of those directories.

### 2. Force Enable JMS Integration

If you want to test the JMS integration without the requests module, you can use the `force_enable_jms.py` script:

```bash
python force_enable_jms.py
```

This script will:
- Modify the `jms_auth.py` file to force enable JMS integration
- Add a mock requests module that simulates API responses
- Allow you to test the JMS integration UI without actually making API calls

**Note**: This is only for testing purposes and will not actually communicate with the JMS API.

### 3. Python Version Issues

The application has been tested with Python 3.8+. If you're using an older version, you might encounter compatibility issues.

- Solution: Upgrade to Python 3.8 or newer.

## Restoring Original Files

If you've used the force_enable_jms.py script and want to restore the original files, you can:

1. Delete the modified files and restore from version control:
   ```bash
   git checkout -- services/jms/jms_auth.py
   ```

2. Or manually edit the files to remove the mock requests module and restore the original REQUESTS_AVAILABLE check.