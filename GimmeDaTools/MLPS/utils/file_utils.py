"""
File utilities for NC Tool Analyzer
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


def ensure_directory_exists(file_path: str) -> None:
    """
    Ensure that the directory for a file exists
    
    Args:
        file_path: Path to the file
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(file_path: str, default: Any = None) -> Any:
    """
    Load data from a JSON file
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if the file doesn't exist or can't be parsed
        
    Returns:
        Data from the JSON file or the default value
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
    
    return default


def save_json_file(file_path: str, data: Any, indent: int = 2) -> bool:
    """
    Save data to a JSON file
    
    Args:
        file_path: Path to the JSON file
        data: Data to save
        indent: Indentation level for the JSON file
        
    Returns:
        True if the file was saved successfully, False otherwise
    """
    try:
        ensure_directory_exists(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False


def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (lowercase, without the dot)
    """
    return os.path.splitext(file_path)[1].lower().lstrip('.')


def is_nc_file(file_path: str) -> bool:
    """
    Check if a file is an NC file based on its extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is an NC file, False otherwise
    """
    nc_extensions = ['nc', 'txt', 'cnc', 'prg', 'h']
    return get_file_extension(file_path) in nc_extensions


def get_temp_file_path(prefix: str, suffix: str) -> str:
    """
    Generate a temporary file path
    
    Args:
        prefix: Prefix for the temporary file
        suffix: Suffix for the temporary file (including extension)
        
    Returns:
        Path to the temporary file
    """
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


def read_text_file(file_path: str, encoding: str = 'utf-8', errors: str = 'ignore') -> Optional[str]:
    """
    Read text from a file
    
    Args:
        file_path: Path to the file
        encoding: File encoding
        errors: How to handle encoding errors
        
    Returns:
        File contents or None if the file couldn't be read
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write text to a file
    
    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding
        
    Returns:
        True if the file was written successfully, False otherwise
    """
    try:
        ensure_directory_exists(file_path)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False