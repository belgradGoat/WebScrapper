import sys
import re
import os
from pathlib import Path

# Version 2.1 4/21/2024 B.Sihler- added Stock Dimensions from BLK FORM.
# Version 2.2 4/21/2024 B.Sihler- CUTTER COMP reading.
# Version 2.3 8/2/2024 B.Sihler- Added Preset Values, Saved Tool List File With The NC Program.
# Version 2.4 10/16/2024 - Added F value check for values exceeding 80000.
# Version 2.5 10/16/2024 - Removed F_ERRORS file, using console output and exit codes instead.

# Get the input file name from command line arguments
if len(sys.argv) != 3:
    print("Wrong Number of Arguments")
    sys.exit(1)

input_file_path1 = sys.argv[1]
mach = sys.argv[2]

# Extracting the filename without extension
file_name, file_extension = os.path.splitext(os.path.basename(input_file_path1))

tool_numbers = []
blk_form_data = []
cutter_comp_info = {}
preset_values = []
current_tool_number = None
f_value_errors = []  # List to store F value errors

# Function to check if a tool call is real
def is_real_tool_call(line):
    return bool(re.search(r'TOOL CALL (\d+)', line))

# Function to check F values
def check_f_value(line, line_number):
    f_matches = re.findall(r'F(\d+(?:\.\d*)?)', line)
    for f_value_str in f_matches:
        try:
            f_value = float(f_value_str)
            if f_value > 80000:
                return f"Line {line_number}: F value {f_value} exceeds maximum allowed (80000)"
        except ValueError:
            pass
    return None

# Read the input file for TOOL CALL, BLK FORM lines, cutter comp indicators, and F values
with open(input_file_path1, 'r', encoding='utf-8', errors='ignore') as file:
    lines = file.readlines()

# Process lines to capture TOOL CALLs, cutter comp indicators, Q339 values, and check F values
for i, line in enumerate(lines, 1):
    if is_real_tool_call(line):
        current_tool_number = re.search(r'TOOL CALL (\d+)', line).group(1)
        tool_numbers.append(current_tool_number)
        
        # Initialize cutter comp as off
        cutter_comp_info[current_tool_number] = 'Cutter Comp: Off'
        
        # Search for RR and RL between the current and next real TOOL CALL
        for subsequent_line in lines[i:]:
            if is_real_tool_call(subsequent_line):
                break
            if ' RR' in subsequent_line or ' RL' in subsequent_line:
                cutter_comp_info[current_tool_number] = 'Cutter Comp: On'
        
    blk_form_match = re.search(r'BLK FORM \d+\.?\d* (?:Z )?X([-+]?\d+\.?\d*) Y([-+]?\d+\.?\d*) Z([-+]?\d+\.?\d*)', line)
    if blk_form_match:
        blk_form_data.append(blk_form_match.groups())
    
    # Capture Q339 values
    q339_match = re.search(r'Q339=([-+]?\d+\.?\d*)', line)
    if q339_match:
        preset_values.append(f'Preset - {q339_match.group(1)}')
    
    # Check F values
    f_error = check_f_value(line, i)
    if f_error:
        f_value_errors.append(f_error)

# Assuming we always get two BLK FORM lines, calculate the rectangle dimensions
if len(blk_form_data) == 2:
    x1, y1, z1 = float(blk_form_data[0][0]), float(blk_form_data[0][1]), float(blk_form_data[0][2])
    x2, y2, z2 = float(blk_form_data[1][0]), float(blk_form_data[1][1]), float(blk_form_data[1][2])
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    depth = abs(z2 - z1)
    dimensions = f"Width: {width}, Height: {height}, Depth: {depth}"
else:
    dimensions = "Insufficient data for dimensions calculation"

# Output file path
output_file_path1 = os.path.join(os.path.dirname(input_file_path1), file_name + '.scanned.tools')

# Write TOOL CALL numbers to the output file
with open(output_file_path1, 'w', encoding='utf-8') as output_file:
    for number in tool_numbers:
        output_file.write(number + '\n')

print(f"Numbers have been written to '{output_file_path1}'")

# Get the desktop path
desktop_path = Path(os.path.expanduser("~/Desktop"))

# Specify the input file name
input_file_name = "TOOL_P.txt"

# Construct the full path to the input file
input_file_path = desktop_path / input_file_name

numbers = []

with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as file:
    for line in file:
        # Split the line into columns
        columns = line.split()
        # Check if there are at least 5 columns
        if len(columns) >= 5:
            # Extract the number to the right of the 9th column
            number = columns[1]
            numbers.append(number)

# Constructing the output file path with the same name but different extension
output_file_path2 = desktop_path / (file_name + '.filtered.tools')

# Writing the numbers to the output file
with open(output_file_path2, 'w', encoding='utf-8') as output_file:
    for number in numbers:
        output_file.write(number + '\n')

print(f"TOOL CALL and BLK FORM numbers have been written to '{output_file_path1}'")

def compare_and_output(file1, file2):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        content1 = f1.read().split()
        content2 = f2.read().split()

    total_numbers = len(content1)
    total_matches = 0
    matched_numbers = []

    matched_numbers.append(f'File: {input_file_path1}')
    matched_numbers.append(f'STOCK DIMENSIONS:')
    matched_numbers.append(f'X{width:.2f} Y{height:.2f} Z{depth:.2f}')
    matched_numbers.append('')
    
    # Add preset values to the output
    matched_numbers.append('Preset Values:')
    matched_numbers.extend(preset_values)
    matched_numbers.append('')
    
    matched_numbers.append(f'Tools Needed in Sequence Order:')
    matched_numbers.append(f'---------------------------------')

    for number in content1:
        if number in content2:
            total_matches += 1
            matched_numbers.append(f'T{number}')
        else:
            matched_numbers.append(f'T{number} < < < Missing Tool')

        if number in cutter_comp_info:
            matched_numbers.append(f'{cutter_comp_info[number]}')
            matched_numbers.append('--------------------')  # Add a line of 20 dashes after cutter comp info

    match_percentage = (total_matches / total_numbers) * 100 if total_numbers else 0
    matched_numbers.append(f'{int(match_percentage)}% of needed tools are in machine: {mach}')

    output_content = '\n'.join(matched_numbers)

    # Construct the output file path with the same name as input_file_path1 but with .TOOL.LIST extension
    output_file = os.path.join(os.path.dirname(input_file_path1), file_name + '.TOOL.LIST')

    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(output_content)

    print(f"Results have been written to '{output_file}'")

    # Print F value errors to console
    if f_value_errors:
        print("F Value Errors detected:")
        for error in f_value_errors:
            print(error)
    else:
        print("No F value errors detected.")

    # Open the output file using the default text editor
    open_output_file(output_file)

    # Delete the .scanned.tools file
    if os.path.exists(output_file_path1):
        os.remove(output_file_path1)
        print(f"{output_file_path1} has been deleted.")
    
    # Delete the .filtered.tools file from the desktop
    if os.path.exists(output_file_path2):
        os.remove(output_file_path2)
        print(f"{output_file_path2} has been deleted.")

    # Return True if there were F value errors, False otherwise
    return bool(f_value_errors)

def open_output_file(output_file):
    try:
        # Use os.startfile to open the file with the default associated program (Windows only)
        os.startfile(output_file)
    except Exception as e:
        print(f"Unable to open the file: {e}")

# Main execution
if __name__ == "__main__":
    has_errors = compare_and_output(output_file_path1, output_file_path2)
    sys.exit(1 if has_errors else 0)