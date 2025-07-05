# Material Removal Rate Calculation Feature - Implementation Plan

## Overview
Add a "Calculate Material Removal Rates" button between "Calculate Cycle Time" and "Create Job from File" in the Analysis tab. This feature will parse tool information from NC file comments and calculate material removal rates for each tool.

## Tool Comment Format Analysis
Based on the example: `SEM_06.35_P15-120_L19O25_0.00AL3 T9`

### Format Structure:
- **Tool Type** (3 letters): SEM, BAL, CHM, CHE, DRL
  - SEM = Square End Mill
  - BAL = Ball End Mill  
  - CHM = Chamfer
  - CHE = Lollipop End Mill
  - DRL = Drill
- **Diameter**: 06.35 (6.35mm)
- **Tool Holder**: P15-120
- **Flute Length**: L19 (19mm)
- **Stickout**: O25 (25mm from tool holder)
- **Corner Radius**: 0.00
- **Material/Flutes**: AL3 (3 flute, aluminum)
- **Tool Number**: T9

## Implementation Plan

### 1. Create Tool Information Parser Class

**File:** `GimmeDaTools/MLPS/services/tool_parser.py` (new file)

```python
class ToolInfo:
    def __init__(self):
        self.tool_number = None
        self.tool_type = None
        self.tool_type_name = None
        self.diameter = None
        self.tool_holder = None
        self.flute_length = None
        self.stickout = None
        self.corner_radius = None
        self.material_code = None
        self.flute_count = None

class ToolCommentParser:
    def __init__(self):
        self.tool_type_mapping = {
            'SEM': 'Square End Mill',
            'BAL': 'Ball End Mill',
            'CHM': 'Chamfer',
            'CHE': 'Lollipop End Mill',
            'DRL': 'Drill'
        }
    
    def parse_tool_comment(self, comment_line):
        # Parse format: SEM_06.35_P15-120_L19O25_0.00AL3 T9
        # Returns ToolInfo object or None if parsing fails
        pass
    
    def extract_all_tool_info(self, nc_file_path):
        # Parse entire NC file for tool comments
        # Returns dict {tool_number: ToolInfo}
        pass
```

### 2. Create Material Removal Rate Calculator

**File:** `GimmeDaTools/MLPS/services/material_removal_calculator.py` (new file)

```python
class MaterialRemovalCalculator:
    def __init__(self):
        pass
    
    def calculate_tool_mrr(self, tool_info, nc_movements):
        # Calculate Material Removal Rate for a specific tool
        # Parameters:
        # - tool_info: ToolInfo object with diameter, type, etc.
        # - nc_movements: List of movements for this tool from NC analysis
        # Returns: MRR data structure
        pass
    
    def analyze_nc_file_mrr(self, nc_file_path):
        # Complete MRR analysis for entire NC file
        # Returns: Dict of tool_number -> MRR results
        pass
```

### 3. Material Removal Rate Calculation Logic

#### Key Formulas:
1. **Cutting Speed (Vc)** = (π × Diameter × RPM) / 1000 [m/min]
2. **Feed per Tooth (fz)** = Feed Rate / (RPM × Number of Flutes) [mm/tooth]
3. **Material Removal Rate (Q)** = Depth of Cut × Width of Cut × Feed Rate [mm³/min]

#### Analysis Steps:
1. Parse tool comments to extract tool diameter and type
2. Analyze NC code movements for each tool:
   - Extract feed rates (F values)
   - Calculate cutting distances
   - Identify depth of cut from Z movements
   - Identify width of cut from X/Y movements
3. Calculate average MRR for each tool across all operations

### 4. Modify Analysis Tab UI

**File:** `GimmeDaTools/MLPS/ui/analysis_tab.py`

#### Changes Required:

1. **Add New Button** (line 235):
```python
# Change existing button line:
ttk.Button(button_frame, text="⏱️ Calculate Cycle Time", command=self.calculate_cycle_time).pack(side=tk.LEFT, padx=(0,10))
ttk.Button(button_frame, text="📊 Calculate Material Removal Rates", command=self.calculate_material_removal_rates).pack(side=tk.LEFT, padx=(0,10))
ttk.Button(button_frame, text="🗂️ Create Job from File", command=self.create_job_from_file).pack(side=tk.LEFT)
```

2. **Add New Method**:
```python
def calculate_material_removal_rates(self):
    """Calculate material removal rates for the current NC file"""
    nc_file = self.file_path_var.get()
    if not nc_file or not os.path.exists(nc_file):
        messagebox.showerror("Error", "Please select a valid NC file first")
        return
    
    self.update_status("Calculating material removal rates...")
    self.progress.start()
    
    # Use a separate thread to avoid blocking the UI
    self._start_background_task(lambda: self._calculate_mrr_task(nc_file))

def _calculate_mrr_task(self, nc_file):
    """Background task for calculating material removal rates"""
    try:
        from services.tool_parser import ToolCommentParser
        from services.material_removal_calculator import MaterialRemovalCalculator
        
        parser = ToolCommentParser()
        calculator = MaterialRemovalCalculator()
        
        # Parse tool information from comments
        tool_info = parser.extract_all_tool_info(nc_file)
        
        # Calculate MRR for each tool
        mrr_results = calculator.analyze_nc_file_mrr(nc_file)
        
        # Combine tool info with MRR results
        combined_data = {
            'tool_info': tool_info,
            'mrr_results': mrr_results,
            'file_name': os.path.basename(nc_file)
        }
        
        # Update UI in main thread
        self.frame.after(0, lambda: self._mrr_complete(combined_data))
        
    except Exception as e:
        # Update UI in main thread
        self.frame.after(0, lambda: self._mrr_error(str(e)))

def _mrr_complete(self, data):
    """Called when MRR calculation is complete"""
    self.progress.stop()
    self.update_status("Material removal rates calculated")
    
    # Show results in popup
    self.show_mrr_results(data)

def _mrr_error(self, error_msg):
    """Called when MRR calculation fails"""
    self.progress.stop()
    self.update_status("MRR calculation failed")
    messagebox.showerror("Calculation Error", f"Failed to calculate material removal rates:\n{error_msg}")

def show_mrr_results(self, data):
    """Show material removal rate results in a popup window"""
    # Create popup similar to cycle time results
    # Display tool information and MRR calculations
    pass
```

### 5. MRR Results Popup Window

#### Display Format:
```
====================================================================
MATERIAL REMOVAL RATE ANALYSIS
====================================================================
File: example.nc
Tools Analyzed: 5

TOOL ANALYSIS RESULTS:
--------------------------------------------------------------------
Tool T9 - Square End Mill (SEM)
  Diameter: 6.35 mm
  Tool Holder: P15-120
  Flute Length: 19 mm
  Material: AL3 (3 flute)
  
  Machining Operations:
  • Total Cutting Distance: 125.4 mm
  • Average Feed Rate: 800 mm/min
  • Average Depth of Cut: 2.5 mm
  • Average Width of Cut: 5.2 mm
  • Material Removal Rate: 10,400 mm³/min
  • Cutting Time: 9.4 seconds
  • Material Removed: 1,628 mm³

Tool T12 - Ball End Mill (BAL)
  Diameter: 3.00 mm
  Tool Holder: P10-80
  Flute Length: 15 mm
  Material: ST2 (2 flute)
  
  Machining Operations:
  • Total Cutting Distance: 78.2 mm
  • Average Feed Rate: 400 mm/min
  • Average Depth of Cut: 0.5 mm
  • Average Width of Cut: 2.8 mm
  • Material Removal Rate: 560 mm³/min
  • Cutting Time: 11.7 seconds
  • Material Removed: 109 mm³

SUMMARY:
--------------------------------------------------------------------
• Total Material Removed: 1,737 mm³
• Average MRR across all tools: 5,480 mm³/min
• Most Efficient Tool: T9 (10,400 mm³/min)
• Least Efficient Tool: T12 (560 mm³/min)
• Tools with High MRR (>5000): T9
• Tools with Low MRR (<1000): T12
```

### 6. Error Handling

#### Common Issues to Handle:
1. **Missing Tool Comments**: Tool numbers without corresponding comment information
2. **Invalid Comment Format**: Comments that don't match the expected pattern
3. **No Cutting Movements**: Tools that are called but never used for cutting
4. **Zero Feed Rates**: Invalid or missing feed rate data

#### Fallback Strategies:
1. Use default tool diameters for common tool numbers
2. Estimate MRR using generic formulas when tool info is incomplete
3. Display warnings for tools with insufficient data

### 7. Integration Points

#### Analysis Service Enhancement:
- Extend `_parse_nc_file()` to also extract tool comments
- Store tool comment data in analysis results
- Make tool information available to other parts of the system

#### Cycle Time Integration:
- Cross-reference MRR data with cycle time calculations
- Validate cutting efficiency against calculated times
- Identify potential optimization opportunities

### 8. Testing Strategy

#### Test Cases:
1. **Complete Tool Comments**: NC file with properly formatted tool comments
2. **Missing Comments**: NC file with some tools lacking comment information  
3. **Invalid Format**: Comments that don't match the expected pattern
4. **Mixed Tools**: File with different tool types (drills, end mills, etc.)
5. **Large Files**: Performance testing with files containing many tools

#### Test Data:
Create sample NC files with known tool configurations and expected MRR values for validation.

## User Interface Flow

1. User selects NC file
2. User clicks "📊 Calculate Material Removal Rates" button
3. System parses tool comments and NC movements
4. Progress indicator shows calculation status
5. Popup window displays detailed MRR analysis
6. User can save report to file
7. Results integrate with existing analysis data

## Benefits

1. **Production Planning**: Better understanding of machining efficiency
2. **Tool Selection**: Data-driven tool selection based on MRR performance
3. **Process Optimization**: Identify tools and operations for improvement
4. **Cost Analysis**: Calculate material removal costs per tool
5. **Quality Control**: Validate that tools are operating within expected parameters

## Future Enhancements

1. **MRR Optimization Suggestions**: Recommend feed/speed improvements
2. **Tool Life Integration**: Correlate MRR with tool wear data
3. **Cost Analysis**: Calculate cost per mm³ of material removed
4. **Benchmark Database**: Compare MRR against industry standards
5. **Real-time Monitoring**: Integration with machine monitoring systems