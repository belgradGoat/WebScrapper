import sys
import re
import os
from pathlib import Path

# Version 3.3 - Fix: Parse spindle/feedrate from TOOL CALL line itself

if len(sys.argv) != 3:
    print("Usage: script.py <input_file_path> <machine_name>")
    sys.exit(1)

input_file_path1 = sys.argv[1]
mach = sys.argv[2]
file_name, file_extension = os.path.splitext(os.path.basename(input_file_path1))

tool_numbers = []
blk_form_data = []
cutter_comp_info = {}
preset_values = []
cur_time_data = {}
tool_diameters = {}
tool_flutes = {}
tool_params = {}

def is_real_tool_call(line):
    return bool(re.search(r'TOOL CALL (\d+)', line))

with open(input_file_path1, 'r', encoding='utf-8', errors='ignore') as file:
    lines = file.readlines()

for i, line in enumerate(lines):
    if is_real_tool_call(line):
        current_tool_number = re.search(r'TOOL CALL (\d+)', line).group(1)
        tool_numbers.append(current_tool_number)
        spindle_speed = None
        feedrate = None
        cutter_comp_info[current_tool_number] = 'Cutter Comp: Off'

        lines_to_scan = [line] + lines[i+1:]
        for subsequent_line in lines_to_scan:
            if subsequent_line != line and is_real_tool_call(subsequent_line):
                break
            if ' RR' in subsequent_line or ' RL' in subsequent_line:
                cutter_comp_info[current_tool_number] = 'Cutter Comp: On'
            s_match = re.search(r'S(\d+)', subsequent_line)
            f_match = re.search(r'F(\d+\.?\d*)', subsequent_line)
            if s_match and spindle_speed is None:
                spindle_speed = int(s_match.group(1))
            if f_match and feedrate is None:
                try:
                    feedrate = float(f_match.group(1))
                except ValueError:
                    feedrate = None

        tool_params[current_tool_number] = {'spindle': spindle_speed, 'feedrate': feedrate}

    blk_form_match = re.search(r'BLK FORM \d+\.?\d* (?:Z )?X([-+]?\d+\.?\d*) Y([-+]?\d+\.?\d*) Z([-+]?\d+\.?\d*)', line)
    if blk_form_match:
        blk_form_data.append(blk_form_match.groups())

    q339_match = re.search(r'Q339=([-+]?\d+\.?\d*)', line)
    if q339_match:
        preset_values.append(f'Preset - {q339_match.group(1)}')

if len(blk_form_data) == 2:
    x1, y1, z1 = map(float, blk_form_data[0])
    x2, y2, z2 = map(float, blk_form_data[1])
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    depth = abs(z2 - z1)
else:
    width = height = depth = 0

output_file_path1 = os.path.join(os.path.dirname(input_file_path1), file_name + '.scanned.tools')
with open(output_file_path1, 'w', encoding='utf-8') as output_file:
    for number in tool_numbers:
        output_file.write(number + '\n')

desktop_path = Path(os.path.expanduser("~/Desktop"))
input_file_path = desktop_path / "TOOL_P.txt"
numbers = []

with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as file:
    for line in file:
        columns = line.split()
        if len(columns) >= 5:
            numbers.append(columns[1])

output_file_path2 = desktop_path / (file_name + '.filtered.tools')
with open(output_file_path2, 'w', encoding='utf-8') as output_file:
    for number in numbers:
        output_file.write(number + '\n')

tool_t_path = desktop_path / "tool.t"
with open(tool_t_path, 'r', encoding='utf-8', errors='ignore') as tool_t_file:
    lines = tool_t_file.readlines()

    cur_time_column = None
    cur_time_index = None
    for idx, line in enumerate(lines):
        if 'CUR.TIME' in line:
            cur_time_index = idx
            cur_time_column = line.index('CUR.TIME')
            break
        elif 'CUR_TIME' in line:
            cur_time_index = idx
            cur_time_column = line.index('CUR_TIME')
            break

    if cur_time_column is None:
        print("CUR.TIME or CUR_TIME header not found in tool.t")
        sys.exit(1)

    for i, cur_time_line in enumerate(lines[cur_time_index + 2:]):
        parts = cur_time_line.split()
        tool_number = str(i + 1)
        if tool_number in tool_numbers:
            cur_time_value_str = cur_time_line[cur_time_column:].strip().split()[0]
            try:
                cur_time_value = float(cur_time_value_str)
            except ValueError:
                cur_time_value = 0
            cur_time_data[tool_number] = cur_time_value if cur_time_value > 0 else 'N/A'

        if len(parts) >= 2:
            tname = parts[-1]
            d_match = re.search(r'_(\d+\.\d+)', tname)
            f_match = re.search(r'(\d+)$', tname)
            if d_match:
                tool_diameters[tool_number] = float(d_match.group(1))
            if f_match:
                tool_flutes[tool_number] = int(f_match.group(1))

def compare_and_output(file1, file2):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        content1 = f1.read().split()
        content2 = f2.read().split()

    total_numbers = len(content1)
    total_matches = 0
    matched_numbers = []
    feed_issues = False

    matched_numbers.append(f'File: {input_file_path1}')
    matched_numbers.append(f'STOCK DIMENSIONS:')
    matched_numbers.append(f'X{width:.2f} Y{height:.2f} Z{depth:.2f}\n')

    matched_numbers.append('Preset Values:')
    matched_numbers.extend(preset_values)
    matched_numbers.append('\nTools Needed in Sequence Order:')
    matched_numbers.append('---------------------------------')

    for number in content1:
        if number in content2:
            total_matches += 1
            matched_numbers.append(f'T{number}')
            if number in cur_time_data:
                matched_numbers.append(f'CUR.TIME: {cur_time_data[number]} mins')
        else:
            matched_numbers.append(f'T{number} < < < Missing Tool')

        matched_numbers.append(f"{cutter_comp_info.get(number, 'Cutter Comp: Off')}")

        params = tool_params.get(number)
        if params:
            spindle = params.get('spindle')
            feedrate = params.get('feedrate')
            diameter = tool_diameters.get(number)
            flutes = tool_flutes.get(number)

            if spindle is not None and spindle < 1000:
                matched_numbers.append(f'⚠ Warning: Spindle speed unusually low ({spindle} RPM)')
                feed_issues = True

            if spindle and feedrate and diameter and flutes:
                max_feedrate = 0.02 * diameter * spindle * flutes
                if feedrate > max_feedrate:
                    matched_numbers.append(f'⚠ Warning: Feedrate too high (F{feedrate}) for D={diameter}mm, RPM={spindle}, Flutes={flutes}')
                    feed_issues = True

        matched_numbers.append('--------------------')

    match_percentage = (total_matches / total_numbers) * 100 if total_numbers else 0
    matched_numbers.append(f'{int(match_percentage)}% of needed tools are in machine: {mach}')

    if feed_issues:
        matched_numbers.append('\n⚠ Some tools have questionable feeds and speeds.')
    else:
        matched_numbers.append('\n✅ All feeds and speeds look good.')

    output_content = '\n'.join(matched_numbers)
    output_file = os.path.join(os.path.dirname(input_file_path1), file_name + '.TOOL.LIST')

    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(output_content)

    print(f"Results have been written to '{output_file}'")
    open_output_file(output_file)

    if os.path.exists(output_file_path1):
        os.remove(output_file_path1)
    if os.path.exists(output_file_path2):
        os.remove(output_file_path2)

def open_output_file(output_file):
    try:
        os.startfile(output_file)
    except Exception as e:
        print(f"Unable to open the file: {e}")

compare_and_output(output_file_path1, output_file_path2)
