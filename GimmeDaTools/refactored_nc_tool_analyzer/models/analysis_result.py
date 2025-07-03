"""
Analysis Result model for NC Tool Analyzer
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FValueError:
    """Represents an F-value error in the NC file"""
    line: int
    value: float
    text: str


@dataclass
class StockDimensions:
    """Represents the stock dimensions from the NC file"""
    width: float
    height: float
    depth: float


@dataclass
class MachineCompatibility:
    """Represents the compatibility of a machine with an NC file"""
    machine_id: str
    machine_name: str
    machine_type: str
    location: str
    matching_tools: List[str]
    missing_tools: List[str]
    locked_required_tools: List[str]
    match_percentage: int
    total_physical_tools: int
    total_locked_tools: int
    last_updated: str


class AnalysisResult:
    """
    Represents the result of analyzing an NC file
    """
    def __init__(
        self,
        file_name: str,
        tool_numbers: List[str],
        cutter_comp_info: Dict[str, str] = None,
        preset_values: List[float] = None,
        f_value_errors: List[FValueError] = None,
        dimensions: Optional[StockDimensions] = None,
        machine_analysis: List[MachineCompatibility] = None,
        debug_info: List[str] = None,
        download_info: str = None
    ):
        """
        Initialize an analysis result
        
        Args:
            file_name: Name of the analyzed NC file
            tool_numbers: List of tool numbers found in the NC file
            cutter_comp_info: Information about cutter compensation for each tool
            preset_values: List of preset values found in the NC file
            f_value_errors: List of F-value errors found in the NC file
            dimensions: Stock dimensions from the NC file
            machine_analysis: List of machine compatibility results
            debug_info: Debug information from the analysis
            download_info: Information about tool data download
        """
        self.file_name = file_name
        self.tool_numbers = tool_numbers
        self.cutter_comp_info = cutter_comp_info or {}
        self.preset_values = preset_values or []
        self.f_value_errors = f_value_errors or []
        self.dimensions = dimensions
        self.machine_analysis = machine_analysis or []
        self.debug_info = debug_info or []
        self.download_info = download_info
        
    @property
    def total_tools(self) -> int:
        """
        Get the total number of tools required by the NC file
        
        Returns:
            Total number of tools
        """
        return len(self.tool_numbers)
    
    @property
    def best_machine(self) -> Optional[MachineCompatibility]:
        """
        Get the best matching machine for this NC file
        
        Returns:
            The machine with the highest match percentage or None if no machines
        """
        if not self.machine_analysis:
            return None
        return max(self.machine_analysis, key=lambda m: m.match_percentage)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the analysis result to a dictionary for serialization
        
        Returns:
            Dictionary representation of the analysis result
        """
        dimensions_dict = None
        if self.dimensions:
            dimensions_dict = {
                'width': self.dimensions.width,
                'height': self.dimensions.height,
                'depth': self.dimensions.depth
            }
            
        f_value_errors_list = []
        for error in self.f_value_errors:
            f_value_errors_list.append({
                'line': error.line,
                'value': error.value,
                'text': error.text
            })
            
        machine_analysis_list = []
        for machine in self.machine_analysis:
            machine_analysis_list.append({
                'machine_id': machine.machine_id,
                'machine_name': machine.machine_name,
                'machine_type': machine.machine_type,
                'location': machine.location,
                'matching_tools': machine.matching_tools,
                'missing_tools': machine.missing_tools,
                'locked_required_tools': machine.locked_required_tools,
                'match_percentage': machine.match_percentage,
                'total_physical_tools': machine.total_physical_tools,
                'total_locked_tools': machine.total_locked_tools,
                'last_updated': machine.last_updated
            })
            
        return {
            'file_name': self.file_name,
            'tool_numbers': self.tool_numbers,
            'cutter_comp_info': self.cutter_comp_info,
            'preset_values': self.preset_values,
            'f_value_errors': f_value_errors_list,
            'dimensions': dimensions_dict,
            'total_tools': self.total_tools,
            'machine_analysis': machine_analysis_list,
            'debug_info': self.debug_info,
            'download_info': self.download_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """
        Create an analysis result from a dictionary
        
        Args:
            data: Dictionary representation of an analysis result
            
        Returns:
            AnalysisResult instance
        """
        dimensions = None
        if data.get('dimensions'):
            dimensions = StockDimensions(
                width=data['dimensions'].get('width', 0.0),
                height=data['dimensions'].get('height', 0.0),
                depth=data['dimensions'].get('depth', 0.0)
            )
            
        f_value_errors = []
        for error_data in data.get('f_value_errors', []):
            f_value_errors.append(FValueError(
                line=error_data.get('line', 0),
                value=error_data.get('value', 0.0),
                text=error_data.get('text', '')
            ))
            
        machine_analysis = []
        for machine_data in data.get('machine_analysis', []):
            machine_analysis.append(MachineCompatibility(
                machine_id=machine_data.get('machine_id', ''),
                machine_name=machine_data.get('machine_name', ''),
                machine_type=machine_data.get('machine_type', ''),
                location=machine_data.get('location', ''),
                matching_tools=machine_data.get('matching_tools', []),
                missing_tools=machine_data.get('missing_tools', []),
                locked_required_tools=machine_data.get('locked_required_tools', []),
                match_percentage=machine_data.get('match_percentage', 0),
                total_physical_tools=machine_data.get('total_physical_tools', 0),
                total_locked_tools=machine_data.get('total_locked_tools', 0),
                last_updated=machine_data.get('last_updated', '')
            ))
            
        return cls(
            file_name=data.get('file_name', ''),
            tool_numbers=data.get('tool_numbers', []),
            cutter_comp_info=data.get('cutter_comp_info', {}),
            preset_values=data.get('preset_values', []),
            f_value_errors=f_value_errors,
            dimensions=dimensions,
            machine_analysis=machine_analysis,
            debug_info=data.get('debug_info', []),
            download_info=data.get('download_info')
        )