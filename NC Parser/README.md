# NC File G-code Parser and 3D Visualizer

A Python tool for reading NC files with G-code, extracting machining information, and generating 3D point cloud visualizations of the machining process.

## Features

- **G-code Parsing**: Parse standard G-code commands (G00, G01, G02, G03, M-codes)
- **Tool Path Calculation**: Generate interpolated tool paths with configurable resolution
- **3D Visualization**: Multiple visualization backends (matplotlib, plotly, Open3D)
- **Point Cloud Generation**: Create 3D point clouds representing tool paths and machined parts
- **Material Removal Simulation**: Simulate material removal during machining
- **Export Capabilities**: Export point clouds and meshes in various formats
- **Analysis Tools**: Generate statistics and analysis plots for G-code programs

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

- `numpy`: Mathematical operations and arrays
- `matplotlib`: 2D/3D plotting and animation
- `open3d`: Advanced 3D point cloud processing
- `plotly`: Interactive 3D visualizations
- `pandas`: Data manipulation (optional)
- `regex`: Advanced pattern matching

## Usage

### Basic Usage

```bash
# Process an NC file with default settings
python main.py your_file.nc

# Create and process a sample file
python main.py --create-sample

# Use different visualization backend
python main.py your_file.nc --backend plotly

# Export results to files
python main.py your_file.nc --export output_folder
```

### Advanced Options

```bash
# Custom tool diameter and resolution
python main.py your_file.nc --tool-diameter 3.0 --resolution 0.05

# Skip visualizations (processing only)
python main.py your_file.nc --no-viz --export results
```

### Programmatic Usage

```python
from src.gcode_parser import GCodeParser
from src.path_calculator import PathCalculator
from src.point_cloud import PointCloudGenerator
from src.visualizer import Visualizer

# Initialize components
parser = GCodeParser()
calculator = PathCalculator(resolution=0.1)
point_cloud_gen = PointCloudGenerator()
visualizer = Visualizer(backend='matplotlib')

# Process NC file
commands = parser.parse_file('your_file.nc')
path_points = calculator.calculate_tool_path(commands)
tool_path_pcd = point_cloud_gen.create_from_path(path_points)

# Visualize
visualizer.plot_tool_path(path_points)
visualizer.plot_point_cloud(tool_path_pcd)
```

## Project Structure

```
NC Parser/
├── src/
│   ├── __init__.py
│   ├── gcode_parser.py      # G-code parsing functionality
│   ├── path_calculator.py   # Tool path and material removal calculations
│   ├── point_cloud.py       # Point cloud generation and manipulation
│   └── visualizer.py        # 3D visualization components
├── tests/
│   ├── test_parser.py       # Unit tests for parser
│   └── test_calculator.py   # Unit tests for calculator
├── examples/
│   └── sample.nc           # Sample NC file for testing
├── requirements.txt        # Python dependencies
├── main.py                # Main application entry point
└── README.md              # This file
```

## Supported G-code Commands

### Movement Commands
- `G00`: Rapid positioning
- `G01`: Linear interpolation (cutting moves)
- `G02`: Clockwise circular interpolation
- `G03`: Counter-clockwise circular interpolation

### Machine Commands
- `M03/M04`: Spindle on (clockwise/counter-clockwise)
- `M05`: Spindle off
- `M06`: Tool change
- `M30`: Program end

### Coordinate Systems
- `G90`: Absolute positioning
- `G91`: Incremental positioning
- `G17/G18/G19`: Plane selection

## Visualization Modes

### 1. Tool Path Visualization
- 3D line plot showing the complete tool path
- Start/end point markers
- Support for multiple backends

### 2. Point Cloud Visualization
- Dense point clouds representing machined geometry
- Tool path point clouds
- Material removal simulation

### 3. Analysis Plots
- XY path plots
- Z-height profiles
- Feed rate analysis
- Command distribution charts

## Export Formats

### Point Clouds
- `.ply`: Polygon file format
- `.pcd`: Point Cloud Data format
- `.xyz`: ASCII point format

### Meshes
- `.stl`: Stereolithography format
- `.obj`: Wavefront OBJ format
- `.ply`: Polygon format with mesh data

## Examples

### Sample NC File
A sample NC file is included that demonstrates:
- Basic linear moves
- Circular interpolation
- Multiple cutting depths
- Pocket machining operations

### Use Cases

1. **Machining Verification**: Verify tool paths before actual machining
2. **Process Visualization**: Understand complex 3D machining operations
3. **Quality Control**: Analyze machining programs for potential issues
4. **Training**: Educational tool for learning CNC programming
5. **Reverse Engineering**: Extract geometry information from NC files

## Algorithm Details

### Path Interpolation
- Linear moves are interpolated based on configurable resolution
- Circular arcs use trigonometric interpolation
- Maintains tool position tracking throughout the program

### Material Removal Simulation
- Uses tool diameter to calculate material removal volume
- Generates point clouds representing removed material
- Simulates final part geometry

### Point Cloud Processing
- Density-based point cloud generation
- Noise simulation for realistic visualization
- Mesh reconstruction using Poisson surface reconstruction

## Performance Considerations

- **Resolution**: Lower resolution values create more points but higher accuracy
- **Tool Diameter**: Affects material removal calculation complexity
- **File Size**: Large NC files may require processing time optimization
- **Memory Usage**: Point cloud density affects memory requirements

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Visualization Issues**: Try different backends
   ```bash
   python main.py file.nc --backend plotly
   ```

3. **Large Files**: Reduce resolution for better performance
   ```bash
   python main.py file.nc --resolution 0.5
   ```

### Error Messages

- `No valid G-code commands found`: Check file format and content
- `No tool path points generated`: Verify G-code contains movement commands
- `Visualization backend not available`: Install required visualization libraries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## Future Enhancements

- Support for more G-code variants
- Real-time machining simulation
- Collision detection
- Integration with CAM software
- Web-based interface
- Multi-tool support
- Surface finish analysis
