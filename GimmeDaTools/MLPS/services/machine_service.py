"""
Machine Service for NC Tool Analyzer
Handles machine management and communication
"""
import os
import subprocess
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from models.machine import Machine
from utils.event_system import event_system
from utils.file_utils import load_json_file, save_json_file


class MachineService:
    """
    Service for managing machines and communicating with them
    """
    def __init__(self, database_path: str = "machine_database.json"):
        """
        Initialize the machine service
        
        Args:
            database_path: Path to the machine database JSON file
        """
        self.database_path = database_path
        self.machines: Dict[str, Machine] = {}
        self.load_database()
        
    def load_database(self) -> None:
        """
        Load the machine database from the JSON file
        """
        data = load_json_file(self.database_path, default={})
        
        # Convert dictionary to Machine objects
        self.machines = {}
        for machine_id, machine_data in data.items():
            self.machines[machine_id] = Machine.from_dict(machine_data)
            
        # Notify listeners that machines were loaded
        event_system.publish("machines_loaded", self.machines)
            
    def save_database(self) -> None:
        """
        Save the machine database to the JSON file
        """
        # Convert Machine objects to dictionaries
        data = {}
        for machine_id, machine in self.machines.items():
            data[machine_id] = machine.to_dict()
            
        if save_json_file(self.database_path, data):
            # Notify listeners that machines were saved
            event_system.publish("machines_saved", self.machines)
        else:
            event_system.publish("error", f"Failed to save machine database")
            
    def get_all_machines(self) -> Dict[str, Machine]:
        """
        Get all machines in the database
        
        Returns:
            Dictionary of machine_id to Machine objects
        """
        return self.machines
    
    def get_machine(self, machine_id: str) -> Optional[Machine]:
        """
        Get a specific machine by ID
        
        Args:
            machine_id: ID of the machine to get
            
        Returns:
            Machine object or None if not found
        """
        return self.machines.get(machine_id)
    
    def add_machine(self, machine: Machine) -> None:
        """
        Add or update a machine in the database
        
        Args:
            machine: Machine object to add or update
        """
        self.machines[machine.machine_id] = machine
        self.save_database()
        event_system.publish("machine_added", machine)
        
    def delete_machine(self, machine_id: str) -> bool:
        """
        Delete a machine from the database
        
        Args:
            machine_id: ID of the machine to delete
            
        Returns:
            True if the machine was deleted, False if not found
        """
        if machine_id in self.machines:
            machine = self.machines.pop(machine_id)
            self.save_database()
            event_system.publish("machine_deleted", machine_id)
            return True
        return False
    
    def download_from_machine(self, machine_id: str) -> Tuple[bool, str]:
        """
        Download tool data from a specific machine
        
        Args:
            machine_id: ID of the machine to download from
            
        Returns:
            Tuple of (success, message)
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return False, "Machine not found"
        
        ip_address = machine.ip_address
        temp_file = f"temp_{machine_id}_TOOL_P.TXT"
        
        try:
            # Step 1: Download TOOL_P.TCH for tool availability
            cmd = [
                r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                f"-I{ip_address}",
                "Get",
                r"TNC:\TABLE\TOOL_P.TCH",
                temp_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_file):
                # Parse the downloaded file for tool availability
                available_tools, locked_tools, _ = self._parse_tool_p_file(temp_file)
                os.remove(temp_file)  # Clean up temp file
                
                # Step 2: Download tool.t for tool life data
                tool_t_file = f"temp_{machine_id}_tool.t"
                cmd_tool_t = [
                    r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                    f"-I{ip_address}",
                    "Get",
                    r"TNC:\TABLE\tool.t",
                    tool_t_file
                ]
                
                result_tool_t = subprocess.run(cmd_tool_t, capture_output=True, text=True, timeout=30)
                tool_life_data = {}
                
                if result_tool_t.returncode == 0 and os.path.exists(tool_t_file):
                    # Parse tool.t for tool life data
                    tool_life_data = self._parse_tool_t_file(tool_t_file, available_tools)
                    os.remove(tool_t_file)  # Clean up temp file
                
                # Update machine data
                machine.update_tools(available_tools, locked_tools, tool_life_data)
                self.save_database()
                
                message = f"Available: {len(available_tools)} tools"
                if locked_tools:
                    message += f", Locked/Broken: {len(locked_tools)} tools"
                if tool_life_data:
                    message += f", Life data: {len(tool_life_data)} tools"
                
                event_system.publish("machine_updated", machine)
                return True, message
            else:
                return False, f"TNCCMD failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def send_file_to_machine(self, machine_id: str, file_path: str) -> Tuple[bool, str]:
        """
        Send an NC file to a machine
        
        Args:
            machine_id: ID of the machine to send to
            file_path: Path to the NC file to send
            
        Returns:
            Tuple of (success, message)
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return False, "Machine not found"
        
        if not os.path.exists(file_path):
            return False, "File not found"
        
        ip_address = machine.ip_address
        tnc_folder = machine.tnc_folder
        filename = os.path.basename(file_path)
        
        try:
            # Construct remote path
            remote_path = f"TNC:\\{tnc_folder}\\{filename}" if tnc_folder else f"TNC:\\{filename}"
            
            # TNCCMD Put command
            cmd = [
                r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                f"-I{ip_address}",
                "Put",
                file_path,
                remote_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                event_system.publish("file_sent", machine_id, filename)
                return True, f"File '{filename}' successfully sent to {machine.name}"
            else:
                error_message = result.stderr or "Unknown error"
                return False, error_message
                
        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _parse_tool_p_file(self, filename: str) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """
        Parse TOOL_P.TXT file - extract tool availability
        
        Args:
            filename: Path to the TOOL_P.TXT file
            
        Returns:
            Tuple of (available_tools, locked_tools, empty_dict)
        """
        available_tools = []
        locked_tools = []
        
        try:
            print(f"\n=== Parsing TOOL_P.TXT file: {filename} ===")
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = 0
                for line in f:
                    line_count += 1
                    columns = line.split()
                    
                    # Debug output for first 10 lines
                    if line_count <= 10:
                        print(f"Line {line_count}: {len(columns)} columns: {columns}")
                    
                    # Same logic as original script - just check for 5+ columns and take tool number
                    if len(columns) >= 5:
                        tool_number = columns[1]  # Tool number from column[1]
                        
                        # Very conservative lock detection - only check for obvious text indicators
                        is_locked = self._check_tool_status_conservative(columns, line)
                        
                        if is_locked:
                            locked_tools.append(tool_number)
                            if line_count <= 10:
                                print(f"  -> Locked tool: {tool_number} ({is_locked})")
                        else:
                            available_tools.append(tool_number)
                            if line_count <= 10:
                                print(f"  -> Available tool: {tool_number}")
            
            print(f"Total lines processed: {line_count}")
            print(f"Available tools: {len(available_tools)}")
            print(f"Locked/Broken tools: {len(locked_tools)}")
            
            # Remove duplicates and sort tools
            unique_available = list(set(available_tools))
            sorted_available = sorted(unique_available, key=lambda x: int(x) if x.isdigit() else 999999)
            
            unique_locked = list(set(locked_tools))
            sorted_locked = sorted(unique_locked, key=lambda x: int(x) if x.isdigit() else 999999)
            
            print(f"Final available tools ({len(sorted_available)}): {sorted_available[:20]}...")
            if sorted_locked:
                print(f"Final locked tools ({len(sorted_locked)}): {sorted_locked[:10]}...")
            print("=== TOOL_P.TXT parsing complete ===\n")
            
            return sorted_available, sorted_locked, {}  # Empty dict for compatibility
            
        except Exception as e:
            print(f"ERROR parsing {filename}: {e}")
            return [], [], {}
    
    def _parse_tool_t_file(self, filename: str, available_tools: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Parse tool.t file for tool life data
        
        Args:
            filename: Path to the tool.t file
            available_tools: List of available tool numbers
            
        Returns:
            Dictionary of tool life data
        """
        tool_life_data = {}
        
        try:
            print(f"\n=== Parsing tool.t file: {filename} ===")
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Find CUR.TIME or CUR_TIME header
            cur_time_column = None
            cur_time_index = None
            
            for idx, line in enumerate(lines):
                if 'CUR.TIME' in line:
                    cur_time_index = idx
                    cur_time_column = line.index('CUR.TIME')
                    print(f"Found CUR.TIME header at line {idx}, column position {cur_time_column}")
                    break
                elif 'CUR_TIME' in line:
                    cur_time_index = idx
                    cur_time_column = line.index('CUR_TIME')
                    print(f"Found CUR_TIME header at line {idx}, column position {cur_time_column}")
                    break
            
            if cur_time_column is None or cur_time_index is None:
                print("CUR.TIME or CUR_TIME header not found in tool.t")
                return {}
            
            # Parse tool life data (skip 2 lines after header)
            for i, cur_time_line in enumerate(lines[cur_time_index + 2:]):
                tool_number = str(i + 1)  # Tool numbers start from 1
                
                # Only process tools that are available
                if tool_number in available_tools:
                    try:
                        # Extract current time value from the column position
                        cur_time_value_str = cur_time_line[cur_time_column:].strip().split()[0]
                        cur_time_value = float(cur_time_value_str)
                        
                        if cur_time_value > 0:
                            tool_life_data[tool_number] = {
                                'current_time': cur_time_value,
                                'max_time': None,  # tool.t doesn't contain max time
                                'usage_percentage': None
                            }
                            print(f"Tool {tool_number}: Current time = {cur_time_value} minutes")
                        
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing tool {tool_number}: {e}")
                        continue
            
            print(f"Extracted tool life data for {len(tool_life_data)} tools")
            print("=== tool.t parsing complete ===\n")
            
            return tool_life_data
            
        except Exception as e:
            print(f"ERROR parsing {filename}: {e}")
            return {}
    
    def _check_tool_status_conservative(self, columns: List[str], full_line: str) -> Optional[str]:
        """
        Very conservative lock detection - only obvious indicators
        
        Args:
            columns: List of columns from the line
            full_line: Full line text
            
        Returns:
            Lock reason or None if not locked
        """
        # Only check for very explicit lock/broken text in the entire line
        line_upper = full_line.upper()
        
        # Only flag as locked if there are very clear text indicators
        obvious_lock_indicators = ['LOCKED', 'BROKEN', 'DISABLED', 'OUT_OF_SERVICE', 'FAULT']
        
        for indicator in obvious_lock_indicators:
            if indicator in line_upper:
                return f"text_indicator_{indicator}"
        
        # Default: assume available
        return None