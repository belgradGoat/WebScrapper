#!/usr/bin/env python3
# filepath: CleanTags.py

import argparse
import re
import os
from bs4 import BeautifulSoup

def clean_markup(text):
    """
    Remove HTML, CSS, and other markup languages from text
    
    Args:
        text (str): Text containing markup to clean
        
    Returns:
        str: Cleaned plain text
    """
    if not text:
        return ""
        
    # Use BeautifulSoup to remove HTML tags
    try:
        soup = BeautifulSoup(text, "html.parser")
        # Remove script and style elements completely
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text()
        
        # Remove CSS selectors and other common markup patterns
        text = re.sub(r'<[^>]*>', '', text)  # Remove any remaining HTML tags
        text = re.sub(r'\{[^\}]*\}', '', text)  # Remove CSS blocks
        text = re.sub(r'@\w+\s*[^;]*;', '', text)  # Remove CSS at-rules
        
        return text.strip()
    except Exception as e:
        print(f"Error cleaning markup: {e}")
        return text  # Return original if cleaning fails

def clean_file(input_file, output_file=None):
    """
    Clean markup from a file and write the result to a new file
    
    Args:
        input_file (str): Path to the file to clean
        output_file (str, optional): Path to save the cleaned file. If None,
                                     appends '_clean' to the input filename
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set default output filename if not provided
        if not output_file:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_clean{ext}"
        
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean the content
        cleaned_content = clean_markup(content)
        
        # Write the cleaned content to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
            
        print(f"Successfully cleaned {input_file}")
        print(f"Cleaned content saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing file {input_file}: {e}")
        return False

def main():
    """Main function to parse arguments and process the file"""
    parser = argparse.ArgumentParser(
        description="Clean HTML, CSS, and other markup from text files"
    )
    parser.add_argument(
        "filename", 
        help="Path to the file to clean"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output file path (default: adds '_clean' to the input filename)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Process the file
    clean_file(args.filename, args.output)

if __name__ == "__main__":
    main()