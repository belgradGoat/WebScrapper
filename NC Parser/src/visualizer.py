import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Optional, Tuple, Dict, Any
from gcode_parser import GCodeCommand

# Open3D is optional
OPEN3D_AVAILABLE = False
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False


class Visualizer:
    """3D visualization for G-code tool paths and point clouds."""
    
    def __init__(self, backend: str = 'matplotlib'):
        """
        Initialize visualizer.
        
        Args:
            backend: Visualization backend ('matplotlib', 'plotly', 'open3d')
        """
        self.backend = backend
        self.fig = None
        self.ax = None
        
    def plot_tool_path(self, path_points: List[np.ndarray], 
                      title: str = "Tool Path Visualization",
                      show_start_end: bool = True) -> None:
        """
        Plot tool path in 3D.
        
        Args:
            path_points: List of 3D points representing tool path
            title: Plot title
            show_start_end: Whether to highlight start and end points
        """
        if not path_points:
            print("No path points to visualize")
            return
        
        points_array = np.array(path_points)
        
        if self.backend == 'matplotlib':
            self._plot_path_matplotlib(points_array, title, show_start_end)
        elif self.backend == 'plotly':
            self._plot_path_plotly(points_array, title, show_start_end)
        elif self.backend == 'open3d' and OPEN3D_AVAILABLE:
            self._plot_path_open3d(points_array, title)
        else:
            print(f"Backend '{self.backend}' not available, falling back to matplotlib")
            self._plot_path_matplotlib(points_array, title, show_start_end)
    
    def _plot_path_matplotlib(self, points: np.ndarray, title: str, show_start_end: bool):
        """Plot using matplotlib."""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot the path
        ax.plot(points[:, 0], points[:, 1], points[:, 2], 
                'b-', linewidth=1, alpha=0.7, label='Tool Path')
        
        if show_start_end and len(points) > 0:
            # Start point (green)
            ax.scatter(points[0, 0], points[0, 1], points[0, 2], 
                      c='green', s=100, marker='o', label='Start')
            
            # End point (red)
            ax.scatter(points[-1, 0], points[-1, 1], points[-1, 2], 
                      c='red', s=100, marker='s', label='End')
        
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        ax.set_title(title)
        ax.legend()
        
        # Equal aspect ratio
        self._set_equal_aspect_3d(ax, points)
        
        plt.tight_layout()
        plt.show()
    
    def _plot_path_plotly(self, points: np.ndarray, title: str, show_start_end: bool):
        """Plot using plotly."""
        fig = go.Figure()
        
        # Add path line
        fig.add_trace(go.Scatter3d(
            x=points[:, 0], y=points[:, 1], z=points[:, 2],
            mode='lines',
            line=dict(color='blue', width=3),
            name='Tool Path'
        ))
        
        if show_start_end and len(points) > 0:
            # Start point
            fig.add_trace(go.Scatter3d(
                x=[points[0, 0]], y=[points[0, 1]], z=[points[0, 2]],
                mode='markers',
                marker=dict(color='green', size=8),
                name='Start'
            ))
            
            # End point
            fig.add_trace(go.Scatter3d(
                x=[points[-1, 0]], y=[points[-1, 1]], z=[points[-1, 2]],
                mode='markers',
                marker=dict(color='red', size=8, symbol='square'),
                name='End'
            ))
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title='X (mm)',
                yaxis_title='Y (mm)',
                zaxis_title='Z (mm)',
                aspectmode='cube'
            ),
            width=800,
            height=600
        )
        
        fig.show()
    
    def _plot_path_open3d(self, points: np.ndarray, title: str):
        """Plot using Open3D (if available)."""
        if not OPEN3D_AVAILABLE:
            print("Open3D not available, falling back to matplotlib")
            self._plot_path_matplotlib(points, title, True)
            return
        
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Color points based on sequence (blue to red gradient)
        colors = np.zeros((len(points), 3))
        for i in range(len(points)):
            ratio = i / max(len(points) - 1, 1)
            colors[i] = [ratio, 0, 1 - ratio]  # Blue to red
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # Create line set for path
        lines = [[i, i + 1] for i in range(len(points) - 1)]
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(points)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        line_set.colors = o3d.utility.Vector3dVector([[0, 0, 1] for _ in lines])
        
        # Visualize
        o3d.visualization.draw_geometries([pcd, line_set], window_name=title)
    
    def plot_point_cloud(self, pcd: Any,
                         title: str = "Point Cloud") -> None:
        """
        Plot point cloud.
        
        Args:
            pcd: Point cloud data (format depends on type)
            title: Plot title
        """
        if OPEN3D_AVAILABLE and hasattr(pcd, 'points'):
            # Open3D point cloud
            o3d.visualization.draw_geometries([pcd], window_name=title)
        else:
            print(f"Point cloud visualization with {self.backend} not fully implemented yet")
    
    def plot_multiple_clouds(self, point_clouds: List[Any],
                           colors: Optional[List[str]] = None,
                           title: str = "Multiple Point Clouds") -> None:
        """
        Plot multiple point clouds.
        
        Args:
            point_clouds: List of point clouds
            colors: Optional list of colors for each cloud
            title: Plot title
        """
        if not point_clouds:
            return
        
        if OPEN3D_AVAILABLE and all(hasattr(pcd, 'points') for pcd in point_clouds):
            o3d.visualization.draw_geometries(point_clouds, window_name=title)
        else:
            print(f"Multiple point cloud visualization with {self.backend} not fully implemented yet")
    
    def plot_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Plot G-code statistics.
        
        Args:
            stats: Dictionary containing statistics
        """
        if self.backend == 'matplotlib':
            self._plot_stats_matplotlib(stats)
        elif self.backend == 'plotly':
            self._plot_stats_plotly(stats)
    
    def _plot_stats_matplotlib(self, stats: Dict[str, Any]):
        """Plot statistics using matplotlib."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('G-code Analysis Statistics', fontsize=16)
        
        # Command counts
        if 'command_counts' in stats:
            commands = list(stats['command_counts'].keys())
            counts = list(stats['command_counts'].values())
            
            ax1.bar(commands, counts, color=['red', 'blue', 'green', 'orange'][:len(commands)])
            ax1.set_title('Command Distribution')
            ax1.set_xlabel('G-code Commands')
            ax1.set_ylabel('Count')
            ax1.tick_params(axis='x', rotation=45)
        
        # Movement statistics
        if 'total_distance' in stats:
            distances = {
                'Total Distance': stats.get('total_distance', 0),
                'Rapid Distance': stats.get('rapid_distance', 0),
                'Feed Distance': stats.get('feed_distance', 0)
            }
            
            ax2.bar(distances.keys(), distances.values(), color=['purple', 'cyan', 'yellow'])
            ax2.set_title('Movement Statistics')
            ax2.set_ylabel('Distance (mm)')
            ax2.tick_params(axis='x', rotation=45)
        
        # Feed rates
        if 'feed_rates' in stats and stats['feed_rates']:
            ax3.hist(stats['feed_rates'], bins=20, alpha=0.7, color='orange')
            ax3.set_title('Feed Rate Distribution')
            ax3.set_xlabel('Feed Rate (mm/min)')
            ax3.set_ylabel('Frequency')
        
        # Processing time info
        if 'processing_time' in stats:
            time_data = {
                'Parse Time': stats.get('parse_time', 0),
                'Calculate Time': stats.get('calc_time', 0),
                'Visualize Time': stats.get('viz_time', 0)
            }
            
            ax4.pie(time_data.values(), labels=time_data.keys(), autopct='%1.1f%%')
            ax4.set_title('Processing Time Breakdown')
        
        plt.tight_layout()
        plt.show()
    
    def _plot_stats_plotly(self, stats: Dict[str, Any]):
        """Plot statistics using plotly."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Command Distribution', 'Movement Statistics', 
                          'Feed Rate Distribution', 'Processing Time'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "histogram"}, {"type": "pie"}]]
        )
        
        # Command counts
        if 'command_counts' in stats:
            commands = list(stats['command_counts'].keys())
            counts = list(stats['command_counts'].values())
            
            fig.add_trace(go.Bar(x=commands, y=counts, name="Commands"), row=1, col=1)
        
        # Movement statistics
        if 'total_distance' in stats:
            distances = {
                'Total': stats.get('total_distance', 0),
                'Rapid': stats.get('rapid_distance', 0),
                'Feed': stats.get('feed_distance', 0)
            }
            
            fig.add_trace(go.Bar(x=list(distances.keys()), y=list(distances.values()), 
                               name="Distances"), row=1, col=2)
        
        # Feed rates
        if 'feed_rates' in stats and stats['feed_rates']:
            fig.add_trace(go.Histogram(x=stats['feed_rates'], name="Feed Rates"), row=2, col=1)
        
        # Processing time
        if 'processing_time' in stats:
            time_data = {
                'Parse': stats.get('parse_time', 0),
                'Calculate': stats.get('calc_time', 0),
                'Visualize': stats.get('viz_time', 0)
            }
            
            fig.add_trace(go.Pie(labels=list(time_data.keys()), values=list(time_data.values()),
                               name="Processing Time"), row=2, col=2)
        
        fig.update_layout(height=800, title_text="G-code Analysis Statistics")
        fig.show()
    
    def _set_equal_aspect_3d(self, ax, points: np.ndarray):
        """Set equal aspect ratio for 3D plot."""
        # Get the range for each axis
        x_range = points[:, 0].max() - points[:, 0].min()
        y_range = points[:, 1].max() - points[:, 1].min()
        z_range = points[:, 2].max() - points[:, 2].min()
        
        # Find the maximum range
        max_range = max(x_range, y_range, z_range)
        
        # Get the center of each axis
        x_center = (points[:, 0].max() + points[:, 0].min()) / 2
        y_center = (points[:, 1].max() + points[:, 1].min()) / 2
        z_center = (points[:, 2].max() + points[:, 2].min()) / 2
        
        # Set the limits
        ax.set_xlim(x_center - max_range/2, x_center + max_range/2)
        ax.set_ylim(y_center - max_range/2, y_center + max_range/2)
        ax.set_zlim(z_center - max_range/2, z_center + max_range/2)
    
    def export_plot(self, filename: str, format: str = 'png', dpi: int = 300):
        """
        Export current plot to file.
        
        Args:
            filename: Output filename
            format: File format ('png', 'pdf', 'svg')
            dpi: Resolution for raster formats
        """
        if self.fig:
            self.fig.savefig(filename, format=format, dpi=dpi, bbox_inches='tight')
            print(f"Plot exported to {filename}")
        else:
            print("No active plot to export")
