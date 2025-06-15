import re
import argparse

def extract_chinese(input_file, output_file):
    """
    Extract only Chinese characters from input file and save to output file.
    Removes all non-Chinese characters including English, numbers, and punctuation.

    Args:
        input_file (str): Path to input text file
        output_file (str): Path to output file for Chinese characters
    """
    # Unicode ranges for Chinese characters only
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Find all Chinese characters and join them together
        chinese_chars = ''.join(chinese_pattern.findall(text))
        
        # Split into chunks for readability (optional)
        chunk_size = 100
        formatted_text = '\n'.join([chinese_chars[i:i+chunk_size] 
                                  for i in range(0, len(chinese_chars), chunk_size)])
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
            
        print(f"Successfully extracted {len(chinese_chars)} Chinese characters to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract Chinese characters from a text file')
    parser.add_argument('input_file', help='Path to input text file')
    parser.add_argument('output_file', help='Path to output file')
    
    args = parser.parse_args()
    extract_chinese(args.input_file, args.output_file)