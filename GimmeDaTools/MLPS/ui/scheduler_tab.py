"""
Enhanced Scheduler Tab for Machine Shop Scheduler
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
from typing import Dict, List, Any, Optional, Callable

from models.job import Job
from models.part import Part
from models.machine import Machine
from models.machine_booking import MachineBooking
from models.activity_type import ActivityType
from models.scheduler_lock import SchedulerLock
from models.workpiece_priority import WorkpiecePriority
from utils.event_system import event_system


class SchedulerTab:
    """
    Scheduler tab for the Machine Shop Scheduler
    """
    def __init__(self, parent, scheduler_service, machine_service):
        """
        Initialize the scheduler tab
        
        Args:
            parent: Parent widget
            scheduler_service: SchedulerService instance
            machine_service: MachineService instance
        """
        self.parent = parent
        self.scheduler_service = scheduler_service
        self.machine_service = machine_service
        
        # Create frame
        self.frame = ttk.Frame(parent)
        
        # Enhanced services access
        self.booking_service = scheduler_service.get_booking_service()
        self.locking_service = scheduler_service.get_locking_service()
        self.time_granularity_manager = scheduler_service.get_time_granularity_manager()
        
        # State variables
        self.selected_week = self._get_current_week_start()
        self.selected_job = None
        self.dragged_part = None
        self.editing_part = None
        self.show_new_job_form = False
        self.show_booking_form = False
        self.show_priority_panel = False
        self.current_granularity = '1hr'
        
        # New job form variables
        self.new_job = {
            'name': tk.StringVar(),
            'machine_id': tk.StringVar(),
            'total_parts': tk.IntVar(value=1),
            'cycle_time': tk.DoubleVar(value=1.0),
            'start_date': tk.StringVar(value=datetime.now().strftime("%Y-%m-%d")),
            'start_hour': tk.IntVar(value=8),
            'start_minute': tk.IntVar(value=0)
        }
        
        # Scheduling options (mutually exclusive) - MUST be initialized BEFORE setup_ui()
        self.find_next_slot_var = tk.BooleanVar(value=False)
        self.optimize_schedule_var = tk.BooleanVar(value=False)
        
        # Setup UI components
        self.setup_ui()
        
        # Subscribe to events
        self._setup_event_handlers()
        
        # Initialize enhanced features
        self._initialize_enhanced_features()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main container with vertical layout
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Enhanced header section with granularity controls
        self._create_enhanced_header_section(main_container)
        
        # Machine stats section with booking indicators
        self._create_enhanced_machine_stats_section(main_container)
        
        # Jobs overview section with priority and lock indicators
        self._create_enhanced_jobs_overview_section(main_container)
        
        # Control panels container (forms and tools)
        self.controls_container = ttk.Frame(main_container)
        self.controls_container.pack(fill=tk.X, pady=(0, 10))
        
        # New job form (initially hidden)
        self.new_job_frame = ttk.LabelFrame(self.controls_container, text="Add New Job", padding=10)
        self._create_enhanced_new_job_form(self.new_job_frame)
        
        # Machine booking form (initially hidden)
        self.booking_form_frame = ttk.LabelFrame(self.controls_container, text="Book Machine Time", padding=10)
        self._create_booking_form(self.booking_form_frame)
        
        # Priority management panel (initially hidden)
        self.priority_panel_frame = ttk.LabelFrame(self.controls_container, text="Manage Priorities", padding=10)
        self._create_priority_panel(self.priority_panel_frame)
        
        # Enhanced schedule section with granularity support
        self._create_enhanced_schedule_section(main_container)
        
        # Enhanced panels (initially hidden)
        self.job_details_panel = None
        self.lock_management_panel = None
        
    def _create_header_section(self, parent):
        """Create the header section with title and week navigation"""
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title and week navigation
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(title_frame, text="Machine Shop Scheduler", font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Week navigation
        week_frame = ttk.Frame(title_frame)
        week_frame.pack(side=tk.RIGHT)
        
        # Previous week button
        prev_week_btn = ttk.Button(
            week_frame, 
            text="←", 
            command=self._previous_week,
            width=3
        )
        prev_week_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Week display
        self.week_label = ttk.Label(week_frame, text="", font=('Arial', 10))
        self.week_label.pack(side=tk.LEFT, padx=5)
        self._update_week_label()
        
        # Next week button
        next_week_btn = ttk.Button(
            week_frame, 
            text="→", 
            command=self._next_week,
            width=3
        )
        next_week_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Today button
        today_btn = ttk.Button(
            week_frame, 
            text="Today", 
            command=self._go_to_today,
            width=8
        )
        today_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Add job button
        add_job_btn = ttk.Button(
            week_frame, 
            text="+ Add Job", 
            command=self._toggle_new_job_form
        )
        add_job_btn.pack(side=tk.LEFT, padx=(20, 0))
        
    def _create_machine_stats_section(self, parent):
        """Create the machine stats section with utilization cards"""
        self.stats_frame = ttk.LabelFrame(parent, text="Machine Utilization", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create a grid for machine cards
        self.stats_grid = ttk.Frame(self.stats_frame)
        self.stats_grid.pack(fill=tk.X)
        
        # Populate machine stats
        self._update_machine_stats()
        
    def _create_jobs_overview_section(self, parent):
        """Create the jobs overview section with job buttons"""
        self.jobs_frame = ttk.LabelFrame(parent, text="Active Jobs", padding=10)
        self.jobs_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create a frame for job buttons
        self.jobs_buttons_frame = ttk.Frame(self.jobs_frame)
        self.jobs_buttons_frame.pack(fill=tk.X)
        
        # Populate job buttons
        self._update_jobs_overview()
        
    def _create_new_job_form(self, parent):
        """Create the new job form"""
        # Grid for form fields
        form_grid = ttk.Frame(parent)
        form_grid.pack(fill=tk.X, pady=5)
        
        # Job name
        ttk.Label(form_grid, text="Job Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(form_grid, textvariable=self.new_job['name'], width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Machine selection
        ttk.Label(form_grid, text="Initial Machine:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        machine_combo = ttk.Combobox(form_grid, textvariable=self.new_job['machine_id'], width=20)
        machine_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Update machine options
        machines = self.machine_service.get_all_machines()
        machine_options = [(m.machine_id, f"{m.name} ({m.machine_id})") for m in machines.values()]
        machine_combo['values'] = [m[1] for m in machine_options]
        machine_combo.bind('<<ComboboxSelected>>', lambda e: self.new_job['machine_id'].set(machine_options[machine_combo.current()][0]))
        
        # Total parts
        ttk.Label(form_grid, text="Number of Parts:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(form_grid, from_=1, to=100, textvariable=self.new_job['total_parts'], width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Cycle time
        ttk.Label(form_grid, text="Cycle Time (min/part):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(form_grid, from_=0.1, to=1000, increment=0.1, textvariable=self.new_job['cycle_time'], width=10).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Start date
        ttk.Label(form_grid, text="Start Date:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(form_grid, textvariable=self.new_job['start_date'], width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Start time
        ttk.Label(form_grid, text="Start Time:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        time_frame = ttk.Frame(form_grid)
        time_frame.grid(row=2, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.new_job['start_hour'], width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.new_job['start_minute'], width=5).pack(side=tk.LEFT)
        
        # Total time calculation
        self.total_time_label = ttk.Label(form_grid, text="")
        self.total_time_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Update total time when values change
        self.new_job['total_parts'].trace_add('write', self._update_total_time)
        self.new_job['cycle_time'].trace_add('write', self._update_total_time)
        self._update_total_time()
        
        # Scheduling Options section
        schedule_frame = ttk.LabelFrame(parent, text="Intelligent Scheduling", padding=10)
        schedule_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(schedule_frame, text="Override manual start time with intelligent scheduling:",
                 font=('Arial', 9)).pack(anchor=tk.W)
        
        # Create scheduling checkboxes (mutually exclusive)
        schedule_options_frame = ttk.Frame(schedule_frame)
        schedule_options_frame.pack(fill=tk.X, pady=(5, 0))
        
        find_slot_cb = ttk.Checkbutton(schedule_options_frame,
                                      text="🔍 Find Next Available Time Slot",
                                      variable=self.find_next_slot_var,
                                      command=self._on_find_slot_toggle)
        find_slot_cb.pack(anchor=tk.W, pady=2)
        
        optimize_cb = ttk.Checkbutton(schedule_options_frame,
                                     text="⚡ Optimize Production Schedule",
                                     variable=self.optimize_schedule_var,
                                     command=self._on_optimize_toggle)
        optimize_cb.pack(anchor=tk.W, pady=2)
        
        # Help text
        ttk.Label(schedule_frame,
                 text="• Find Next Available: Finds machine with earliest available time + required tools\n"
                      "• Optimize Schedule: Uses advanced algorithms to fit job optimally (when available)",
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Button(button_frame, text="Add Job", command=self._add_job).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self._toggle_new_job_form).pack(side=tk.LEFT)
        
    def _create_schedule_section(self, parent):
        """Create the schedule section with the weekly calendar"""
        schedule_frame = ttk.LabelFrame(parent, text="Weekly Schedule", padding=10)
        schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas with scrollbars for the schedule
        self.schedule_canvas = tk.Canvas(schedule_frame, bg="white")
        x_scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.HORIZONTAL, command=self.schedule_canvas.xview)
        y_scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=self.schedule_canvas.yview)
        
        self.schedule_canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        
        # Layout scrollbars and canvas
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas for the schedule content
        self.schedule_content = ttk.Frame(self.schedule_canvas)
        self.schedule_canvas.create_window((0, 0), window=self.schedule_content, anchor=tk.NW)
        
        # Configure the canvas to resize with the content
        self.schedule_content.bind("<Configure>", lambda e: self.schedule_canvas.configure(
            scrollregion=self.schedule_canvas.bbox("all"),
            width=max(self.schedule_content.winfo_reqwidth(), self.schedule_canvas.winfo_width()),
            height=max(self.schedule_content.winfo_reqheight(), self.schedule_canvas.winfo_height())
        ))
        
        # Populate the schedule
        self._update_schedule()
        
    def _update_machine_stats(self):
        """Update the machine stats display"""
        # Clear existing stats
        for widget in self.stats_grid.winfo_children():
            widget.destroy()
            
        # Get machines
        machines = self.machine_service.get_all_machines()
        if not machines:
            ttk.Label(self.stats_grid, text="No machines configured. Add machines in the Machine Management tab.").grid(row=0, column=0)
            return
            
        # Create a card for each machine
        for i, (machine_id, machine) in enumerate(machines.items()):
            # Calculate utilization
            utilization = self.scheduler_service.get_machine_utilization(machine_id, self.selected_week)
            
            # Create card frame
            card = ttk.Frame(self.stats_grid, padding=10)
            card.grid(row=i // 6, column=i % 6, padx=5, pady=5, sticky=tk.W)
            
            # Machine name
            ttk.Label(card, text=machine.name, font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            
            # Machine type
            ttk.Label(card, text=machine.machine_type, font=('Arial', 8)).pack(anchor=tk.W)
            
            # Utilization
            ttk.Label(card, text=f"Utilization: {utilization:.1f}%").pack(anchor=tk.W, pady=(5, 0))
            
            # Progress bar
            progress = ttk.Progressbar(card, value=utilization, maximum=100, length=100)
            progress.pack(anchor=tk.W, pady=(2, 0))
            
    def _update_jobs_overview(self):
        """Update the jobs overview display"""
        # Clear existing job buttons
        for widget in self.jobs_buttons_frame.winfo_children():
            widget.destroy()
            
        # Get jobs
        jobs = self.scheduler_service.get_all_jobs()
        if not jobs:
            ttk.Label(self.jobs_buttons_frame, text="No jobs scheduled. Click '+ Add Job' to create a new job.").pack(anchor=tk.W)
            return
            
        # Create a button for each job
        for job_id, job in jobs.items():
            # Get job parts
            job_parts = self.scheduler_service.get_job_parts(job_id)
            completed_parts = sum(1 for part in job_parts if part.status == 'completed')
            in_progress_parts = sum(1 for part in job_parts if part.status == 'in-progress')
            
            # Create job frame with button and indicator
            job_frame = tk.Frame(self.jobs_buttons_frame)
            job_frame.pack(side=tk.LEFT, padx=(0, 5), pady=5)
            
            # Determine button style based on job status
            button_bg = job.color
            button_relief = tk.RAISED
            status_indicator = ""
            
            if hasattr(job, 'status'):
                if job.status == 'locked':
                    button_relief = tk.SUNKEN
                    status_indicator = "🔒"
                elif job.status == 'error':
                    button_bg = '#dc3545'  # Red for errors
                    status_indicator = "❌"
                elif job.status == 'completed':
                    button_bg = '#28a745'  # Green for completed
                    status_indicator = "✅"
                elif job.status == 'paused':
                    button_bg = '#6c757d'  # Gray for paused
                    status_indicator = "⏸️"
            
            # Create job button with custom styling
            job_button = tk.Button(
                job_frame,
                text=f"{status_indicator}{job.name} ({completed_parts}/{job.total_parts})",
                bg=button_bg,
                fg="white",
                relief=button_relief,
                borderwidth=1,
                padx=10,
                pady=5,
                font=('Arial', 9, 'bold'),
                command=lambda j=job: self._show_job_details(j)
            )
            job_button.pack(side=tk.TOP)
            
            # Check if job is synced with JMS
            is_synced = hasattr(self, 'jms_service') and self.jms_service and \
                        job.job_id in getattr(self.jms_service, 'job_order_mappings', {})
            
            # Add JMS indicator if synced
            if is_synced:
                tk.Label(
                    job_frame,
                    text="JMS",
                    bg="#3b82f6",
                    fg="white",
                    font=('Arial', 7, 'bold'),
                    padx=3,
                    pady=0
                ).pack(side=tk.TOP, fill=tk.X)
            
            # Add indicator for in-progress parts
            if in_progress_parts > 0:
                job_button.config(relief=tk.SUNKEN)
                
    def _update_schedule(self):
        """Update the schedule display"""
        # Clear existing schedule
        for widget in self.schedule_content.winfo_children():
            widget.destroy()
            
        # Get machines and week days
        machines = self.machine_service.get_all_machines()
        week_days = self._get_week_days()
        
        # Create header row with days
        header_frame = ttk.Frame(self.schedule_content)
        header_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        # Machine column header
        machine_header = ttk.Label(header_frame, text="Machine", font=('Arial', 10, 'bold'), width=15)
        machine_header.grid(row=0, column=0, sticky=tk.NSEW, padx=1, pady=1)
        
        # Day column headers
        for i, day in enumerate(week_days):
            day_frame = ttk.Frame(header_frame)
            day_frame.grid(row=0, column=i+1, sticky=tk.NSEW, padx=1, pady=1)
            
            # Format day header
            day_name = day.strftime("%a %d %b")
            is_today = day.date() == datetime.now().date()
            
            day_label = ttk.Label(
                day_frame, 
                text=day_name + (" (Today)" if is_today else ""),
                font=('Arial', 10, 'bold'),
                background="#e6f0ff" if is_today else "#f0f0f0",
                anchor=tk.CENTER,
                width=24
            )
            day_label.pack(fill=tk.X)
            
            # Hour labels
            hours_frame = ttk.Frame(day_frame)
            hours_frame.pack(fill=tk.X)
            
            for hour in range(24):
                hour_label = ttk.Label(
                    hours_frame,
                    text=f"{hour:02d}",
                    width=2,
                    anchor=tk.CENTER,
                    background="#f8f8f8"
                )
                hour_label.pack(side=tk.LEFT)
        
        # Create machine rows
        for i, (machine_id, machine) in enumerate(machines.items()):
            row_frame = ttk.Frame(self.schedule_content)
            row_frame.grid(row=i+1, column=0, sticky=tk.NSEW)
            
            # Machine name
            machine_label = ttk.Label(
                row_frame, 
                text=machine.name,
                font=('Arial', 9),
                background="#f0f0f0",
                width=15
            )
            machine_label.grid(row=0, column=0, sticky=tk.NSEW, padx=1, pady=1)
            
            # Day cells
            for j, day in enumerate(week_days):
                day_start = int(day.timestamp() * 1000)
                
                # Create day container
                day_frame = ttk.Frame(row_frame)
                day_frame.grid(row=0, column=j+1, sticky=tk.NSEW, padx=1, pady=1)
                
                # Create hour slots
                day_canvas = tk.Canvas(day_frame, height=80, bg="white", highlightthickness=0)
                day_canvas.pack(fill=tk.X)
                
                # Draw hour lines
                for hour in range(24):
                    x = hour * 24  # 24 pixels per hour
                    day_canvas.create_line(x, 0, x, 80, fill="#e0e0e0")
                
                # Get parts for this day and machine
                day_parts = self.scheduler_service.get_parts_for_day(machine_id, day_start)
                
                # Draw parts
                for part in day_parts:
                    job = self.scheduler_service.get_job(part.job_id)
                    if not job:
                        continue
                        
                    # Calculate position and size
                    part_start = part.start_time
                    day_end = day_start + 24 * 60 * 60 * 1000
                    
                    # Skip parts that are completely outside this day
                    if part_start >= day_end:
                        continue
                        
                    # Calculate start offset in pixels (24 pixels per hour)
                    start_offset = (part_start - day_start) / (1000 * 60 * 60) * 24
                    
                    # Calculate width in pixels
                    width = (job.cycle_time / 60) * 24  # Convert minutes to hours, then to pixels
                    
                    # Ensure part is visible if it starts before this day
                    if start_offset < 0:
                        width += start_offset  # Reduce width by the negative offset
                        start_offset = 0
                        
                    # Ensure part doesn't extend beyond day
                    if start_offset + width > 24 * 24:  # 24 hours * 24 pixels
                        width = 24 * 24 - start_offset
                        
                    # Create part block
                    part_frame = tk.Frame(
                        day_canvas,
                        bg=job.color,
                        bd=1,
                        relief=tk.RAISED
                    )
                    
                    # Position the part on the canvas
                    part_id = day_canvas.create_window(
                        start_offset,
                        4,
                        window=part_frame,
                        anchor=tk.NW,
                        width=width,
                        height=72,
                        tags=(f"part_{part.part_id}")
                    )
                    
                    # Part number indicator
                    part_num = tk.Label(
                        part_frame,
                        text=str(part.part_number),
                        bg="#3b82f6",
                        fg="white",
                        font=('Arial', 8, 'bold'),
                        width=2,
                        height=1,
                        bd=1,
                        relief=tk.RAISED
                    )
                    part_num.place(x=-8, y=-8)
                    
                    # Part info
                    if width > 50:  # Only show text if there's enough space
                        part_label = tk.Label(
                            part_frame,
                            text=f"{job.name}\nPart {part.part_number}/{job.total_parts}",
                            bg=job.color,
                            fg="white",
                            font=('Arial', 7),
                            justify=tk.LEFT,
                            anchor=tk.NW,
                            padx=3
                        )
                        part_label.pack(anchor=tk.NW, fill=tk.X)
                        
                        # Status indicator
                        status_frame = tk.Frame(part_frame)
                        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=3, pady=2)
                        
                        status_text = "WIP" if part.status == 'in-progress' else "est" if part.estimate else "conf"
                        status_bg = "#22c55e" if part.status == 'in-progress' else "#fbbf24" if part.estimate else "#3b82f6"
                        
                        status_label = tk.Label(
                            status_frame,
                            text=status_text,
                            bg=status_bg,
                            fg="white",
                            font=('Arial', 6),
                            padx=2,
                            pady=0
                        )
                        status_label.pack(side=tk.LEFT)
                    
                    # Make part draggable
                    self._make_part_draggable(day_canvas, part_id, part)
                    
                # Make day cell a drop target
                self._make_day_cell_droppable(day_canvas, machine_id, day_start)
                
        # Update canvas scroll region
        self.schedule_content.update_idletasks()
        self.schedule_canvas.configure(scrollregion=self.schedule_canvas.bbox("all"))
        
    def _make_part_draggable(self, canvas, item_id, part):
        """Make a part draggable on the canvas"""
        def on_drag_start(event):
            # Store the item and its original position
            canvas.drag_data = {
                "item_id": item_id,
                "part": part,
                "x": event.x,
                "y": event.y
            }
            
            # Change cursor to indicate dragging
            canvas.config(cursor="fleur")
            
            # Raise the item to the top
            canvas.tag_raise(item_id)
            
        def on_drag_motion(event):
            if canvas.drag_data:
                # Calculate the movement
                dx = event.x - canvas.drag_data["x"]
                
                # Move the item
                canvas.move(canvas.drag_data["item_id"], dx, 0)
                
                # Update the drag position
                canvas.drag_data["x"] = event.x
                
        def on_drag_end(event):
            if canvas.drag_data:
                # Reset cursor
                canvas.config(cursor="")
                
                # Clear drag data
                canvas.drag_data = None
                
        # Bind events to the canvas item
        canvas.tag_bind(item_id, "<ButtonPress-1>", on_drag_start)
        canvas.tag_bind(item_id, "<B1-Motion>", on_drag_motion)
        canvas.tag_bind(item_id, "<ButtonRelease-1>", on_drag_end)
        
        # Initialize drag data
        canvas.drag_data = None
        
    def _make_day_cell_droppable(self, canvas, machine_id, day_start):
        """Make a day cell a drop target for parts"""
        def on_drop(event):
            if canvas.drag_data and canvas.drag_data["part"]:
                # Calculate the drop time
                hour = event.x // 24  # 24 pixels per hour
                drop_time = day_start + hour * 60 * 60 * 1000  # Convert to milliseconds
                
                # Move the part
                part = canvas.drag_data["part"]
                self.scheduler_service.move_part(part.part_id, machine_id, drop_time)
                
                # Update the schedule
                self._update_schedule()
                
        # Bind drop event to the canvas
        canvas.bind("<ButtonRelease-1>", on_drop)
        
    def _show_job_details(self, job):
        """Show the job details panel"""
        # If panel already exists, destroy it
        if self.job_details_panel:
            self.job_details_panel.destroy()
            
        # Create new panel
        self.job_details_panel = tk.Frame(self.frame, bg="white", bd=2, relief=tk.RAISED)
        self.job_details_panel.place(relx=1.0, rely=0, anchor=tk.NE, width=300, relheight=1.0)
        
        # Store selected job
        self.selected_job = job
        
        # Job header
        header_frame = tk.Frame(self.job_details_panel, bg="white", padx=10, pady=10)
        header_frame.pack(fill=tk.X)
        
        # Job title
        title_label = tk.Label(
            header_frame,
            text=job.name,
            font=('Arial', 14, 'bold'),
            fg=job.color,
            bg="white",
            anchor=tk.W
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button
        close_btn = tk.Button(
            header_frame,
            text="×",
            font=('Arial', 14),
            bg="white",
            bd=0,
            command=self._close_job_details
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Check if JMS service is available
        has_jms = hasattr(self, 'jms_service') and self.jms_service
        
        # Check if job is synced with JMS
        is_synced = has_jms and job.job_id in getattr(self.jms_service, 'job_order_mappings', {})
        
        # JMS sync status
        if has_jms:
            jms_frame = tk.Frame(header_frame, bg="white")
            jms_frame.pack(side=tk.RIGHT, padx=10)
            
            if is_synced:
                jms_label = tk.Label(
                    jms_frame,
                    text="JMS Synced",
                    bg="#22c55e",
                    fg="white",
                    font=('Arial', 8),
                    padx=5,
                    pady=2
                )
                jms_label.pack(side=tk.LEFT)
            else:
                jms_btn = tk.Button(
                    jms_frame,
                    text="Push to JMS",
                    bg="#3b82f6",
                    fg="white",
                    font=('Arial', 8),
                    padx=5,
                    pady=2,
                    bd=0,
                    command=lambda: self._sync_job_to_jms(job)
                )
                jms_btn.pack(side=tk.LEFT)
        
        # Job info
        info_frame = tk.Frame(self.job_details_panel, bg="white", padx=10, pady=5)
        info_frame.pack(fill=tk.X)
        
        tk.Label(
            info_frame,
            text=f"Total Parts: {job.total_parts}",
            bg="white",
            anchor=tk.W
        ).pack(fill=tk.X)
        
        tk.Label(
            info_frame,
            text=f"Cycle Time: {job.cycle_time} min/part",
            bg="white",
            anchor=tk.W
        ).pack(fill=tk.X)
        
        tk.Label(
            info_frame,
            text=f"Total Time: {job.total_parts * job.cycle_time:.1f} min ({job.total_parts * job.cycle_time / 60:.1f} hours)",
            bg="white",
            anchor=tk.W
        ).pack(fill=tk.X)
        
        # Show job status
        if hasattr(job, 'status'):
            status_colors = {
                'active': 'green',
                'locked': 'orange',
                'error': 'red',
                'completed': 'blue',
                'paused': 'gray'
            }
            status_color = status_colors.get(job.status, 'black')
            tk.Label(
                info_frame,
                text=f"Status: {job.status.upper()}",
                bg="white",
                fg=status_color,
                font=('Arial', 10, 'bold'),
                anchor=tk.W
            ).pack(fill=tk.X)
        
        # Machine distribution
        machine_frame = tk.LabelFrame(self.job_details_panel, text="Machine Distribution", bg="white", padx=10, pady=5)
        machine_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Get parts by machine
        job_parts = self.scheduler_service.get_job_parts(job.job_id)
        machine_counts = {}
        for part in job_parts:
            if part.machine_id:
                machine = self.machine_service.get_machine(part.machine_id)
                if machine:
                    machine_name = machine.name
                    machine_counts[machine_name] = machine_counts.get(machine_name, 0) + 1
        
        # Show machine distribution
        for machine_name, count in machine_counts.items():
            tk.Label(
                machine_frame,
                text=f"{machine_name}: {count} parts",
                bg="white",
                anchor=tk.W
            ).pack(fill=tk.X)
            
        # Parts list
        parts_frame = tk.LabelFrame(self.job_details_panel, text="Parts Schedule", bg="white", padx=10, pady=5)
        parts_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create scrollable frame for parts
        parts_canvas = tk.Canvas(parts_frame, bg="white", highlightthickness=0)
        parts_scrollbar = ttk.Scrollbar(parts_frame, orient=tk.VERTICAL, command=parts_canvas.yview)
        
        parts_canvas.configure(yscrollcommand=parts_scrollbar.set)
        parts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        parts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        parts_scrollable = tk.Frame(parts_canvas, bg="white")
        parts_canvas.create_window((0, 0), window=parts_scrollable, anchor=tk.NW)
        
        # Configure the canvas to resize with the content
        parts_scrollable.bind("<Configure>", lambda e: parts_canvas.configure(
            scrollregion=parts_canvas.bbox("all")
        ))
        
        # Sort parts by start time
        sorted_parts = sorted(job_parts, key=lambda p: p.start_time)
        
        # Display parts
        for i, part in enumerate(sorted_parts):
            machine = self.machine_service.get_machine(part.machine_id) if part.machine_id else None
            machine_name = machine.name if machine else "Unassigned"
            
            # Create part frame
            part_frame = tk.Frame(parts_scrollable, bg="white", bd=1, relief=tk.GROOVE)
            part_frame.pack(fill=tk.X, pady=2)
            
            # Part header
            header_frame = tk.Frame(part_frame, bg=job.color)
            header_frame.pack(fill=tk.X)
            
            tk.Label(
                header_frame,
                text=f"Part {part.part_number}/{job.total_parts}",
                bg=job.color,
                fg="white",
                font=('Arial', 8, 'bold'),
                padx=5,
                pady=2
            ).pack(side=tk.LEFT)
            
            status_text = "In Progress" if part.status == 'in-progress' else "Completed" if part.status == 'completed' else "Scheduled"
            tk.Label(
                header_frame,
                text=status_text,
                bg=job.color,
                fg="white",
                font=('Arial', 8),
                padx=5,
                pady=2
            ).pack(side=tk.RIGHT)
            
            # Part details
            details_frame = tk.Frame(part_frame, bg="white", padx=5, pady=2)
            details_frame.pack(fill=tk.X)
            
            # Format start time
            start_datetime = datetime.fromtimestamp(part.start_time / 1000)
            start_time_str = start_datetime.strftime("%Y-%m-%d %H:%M")
            
            tk.Label(
                details_frame,
                text=f"Machine: {machine_name}",
                bg="white",
                anchor=tk.W
            ).pack(fill=tk.X)
            
            tk.Label(
                details_frame,
                text=f"Start: {start_time_str}",
                bg="white",
                anchor=tk.W
            ).pack(fill=tk.X)
            
            # Add buttons for part actions
            button_frame = tk.Frame(part_frame, bg="white")
            button_frame.pack(fill=tk.X, pady=2)
            
            if part.status == 'scheduled':
                tk.Button(
                    button_frame,
                    text="Start",
                    command=lambda p=part: self._start_part(p),
                    font=('Arial', 8),
                    padx=5,
                    pady=1
                ).pack(side=tk.LEFT, padx=2)
            elif part.status == 'in-progress':
                tk.Button(
                    button_frame,
                    text="Complete",
                    command=lambda p=part: self._complete_part(p),
                    font=('Arial', 8),
                    padx=5,
                    pady=1
                ).pack(side=tk.LEFT, padx=2)
            
            # Edit button
            tk.Button(
                button_frame,
                text="Edit",
                command=lambda p=part: self._edit_part(p),
                font=('Arial', 8),
                padx=5,
                pady=1
            ).pack(side=tk.LEFT, padx=2)
            
            # Delete button
            tk.Button(
                button_frame,
                text="Delete",
                command=lambda p=part: self._delete_part(p),
                font=('Arial', 8),
                padx=5,
                pady=1
            ).pack(side=tk.LEFT, padx=2)
    
    def _get_current_week_start(self) -> int:
        """
        Get the start of the current week
        
        Returns:
            Start time of the current week in milliseconds
        """
        now = datetime.now()
        # Get the start of the week (Monday)
        start_of_week = now - timedelta(days=now.weekday())
        # Set time to 00:00:00
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        # Convert to milliseconds
        return int(start_of_week.timestamp() * 1000)
    
    def _get_week_days(self) -> List[datetime]:
        """
        Get the days of the selected week
        
        Returns:
            List of datetime objects for each day of the week
        """
        # Convert milliseconds to datetime
        week_start = datetime.fromtimestamp(self.selected_week / 1000)
        # Get all days of the week
        return [week_start + timedelta(days=i) for i in range(7)]
    
    def _update_week_label(self) -> None:
        """Update the week label with the selected week range"""
        week_days = self._get_week_days()
        start_date = week_days[0].strftime("%b %d")
        end_date = week_days[-1].strftime("%b %d, %Y")
        self.week_label.config(text=f"{start_date} - {end_date}")
    
    def _previous_week(self) -> None:
        """Go to the previous week"""
        self.selected_week -= 7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
        self._update_week_label()
        self._update_schedule()
        self._update_machine_stats()
    
    def _next_week(self) -> None:
        """Go to the next week"""
        self.selected_week += 7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
        self._update_week_label()
        self._update_schedule()
        self._update_machine_stats()
    
    def _go_to_today(self) -> None:
        """Go to the current week"""
        self.selected_week = self._get_current_week_start()
        self._update_week_label()
        self._update_schedule()
        self._update_machine_stats()
    
    def _toggle_new_job_form(self) -> None:
        """Toggle the visibility of the new job form"""
        if self.show_new_job_form:
            self.new_job_frame.pack_forget()
            self.show_new_job_form = False
        else:
            self.new_job_frame.pack(fill=tk.X, pady=(0, 10), after=self.jobs_frame)
            self.show_new_job_form = True
            
            # Reset form fields
            self.new_job['name'].set("")
            self.new_job['total_parts'].set(1)
            self.new_job['cycle_time'].set(1.0)
            self.new_job['start_date'].set(datetime.now().strftime("%Y-%m-%d"))
            self.new_job['start_hour'].set(8)
            self.new_job['start_minute'].set(0)
            
            # Update machine options
            machines = self.machine_service.get_all_machines()
            if machines:
                first_machine = list(machines.values())[0]
                self.new_job['machine_id'].set(first_machine.machine_id)
    
    def _update_total_time(self, *args) -> None:
        """Update the total time calculation in the new job form"""
        try:
            total_parts = self.new_job['total_parts'].get()
            cycle_time = self.new_job['cycle_time'].get()
            total_minutes = total_parts * cycle_time
            total_hours = total_minutes / 60
            
            self.total_time_label.config(
                text=f"Total Time: {total_minutes:.1f} min ({total_hours:.1f} hours)"
            )
        except (ValueError, tk.TclError):
            self.total_time_label.config(text="Total Time: Invalid input")
    
    def _on_find_slot_toggle(self):
        """Handle find next slot checkbox toggle (mutually exclusive)"""
        if self.find_next_slot_var.get():
            self.optimize_schedule_var.set(False)
    
    def _on_optimize_toggle(self):
        """Handle optimize schedule checkbox toggle (mutually exclusive)"""
        if self.optimize_schedule_var.get():
            self.find_next_slot_var.set(False)
    
    def _find_next_available_slot(self, job_name, total_parts, cycle_time):
        """
        Find the next available time slot for a job
        
        Args:
            job_name: Name of the job
            total_parts: Number of parts
            cycle_time: Cycle time per part in minutes
            
        Returns:
            Tuple of (machine_id, start_timestamp, start_date, start_hour, start_minute)
        """
        machines = self.machine_service.get_all_machines()
        if not machines:
            return None, None, None, None, None
        
        # Calculate job duration in milliseconds
        job_duration_ms = int(total_parts * cycle_time * 60 * 1000)
        
        # Start search from current time
        search_start = int(datetime.now().timestamp() * 1000)
        
        best_slot = None
        best_start_time = float('inf')
        
        # Check each machine
        for machine_id, machine in machines.items():
            # Get all parts scheduled on this machine
            all_parts = self.scheduler_service.get_all_parts()
            machine_parts = [p for p in all_parts.values() if p.machine_id == machine_id]
            
            # Sort by start time
            machine_parts.sort(key=lambda p: p.start_time)
            
            # Find gaps in the schedule
            current_time = search_start
            
            for part in machine_parts:
                # Check if there's a gap before this part
                if part.start_time - current_time >= job_duration_ms:
                    # Found a slot
                    if current_time < best_start_time:
                        best_start_time = current_time
                        best_slot = (machine_id, current_time)
                    break
                
                # Move past this part
                job = self.scheduler_service.get_job(part.job_id)
                if job:
                    part_duration = int(job.cycle_time * 60 * 1000)
                    current_time = max(current_time, part.start_time + part_duration)
            else:
                # No conflicting parts, or we can schedule after the last part
                if current_time < best_start_time:
                    best_start_time = current_time
                    best_slot = (machine_id, current_time)
        
        if best_slot:
            machine_id, start_timestamp = best_slot
            start_datetime = datetime.fromtimestamp(start_timestamp / 1000)
            return (
                machine_id,
                start_timestamp,
                start_datetime.strftime("%Y-%m-%d"),
                start_datetime.hour,
                start_datetime.minute
            )
        
        return None, None, None, None, None
    
    def _optimize_production_schedule(self, job_name, total_parts, cycle_time):
        """
        Optimize production schedule placement (placeholder for advanced algorithm)
        
        Args:
            job_name: Name of the job
            total_parts: Number of parts
            cycle_time: Cycle time per part in minutes
            
        Returns:
            Tuple of (machine_id, start_timestamp, start_date, start_hour, start_minute)
        """
        # For now, use the same logic as find_next_available_slot
        # In the future, this could implement more sophisticated algorithms like:
        # - Machine utilization balancing
        # - Tool change minimization
        # - Rush order prioritization
        # - Setup time optimization
        
        return self._find_next_available_slot(job_name, total_parts, cycle_time)
    
    def _add_job(self) -> None:
        """Add a new job from the form data"""
        try:
            # Validate inputs
            name = self.new_job['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Job name is required")
                return
                
            machine_id = self.new_job['machine_id'].get()
            if not machine_id:
                messagebox.showerror("Error", "Machine selection is required")
                return
                
            total_parts = self.new_job['total_parts'].get()
            cycle_time = self.new_job['cycle_time'].get()
            start_date = self.new_job['start_date'].get()
            start_hour = self.new_job['start_hour'].get()
            start_minute = self.new_job['start_minute'].get()
            
            # Handle intelligent scheduling
            original_machine = machine_id
            original_date = start_date
            original_hour = start_hour
            original_minute = start_minute
            
            if self.find_next_slot_var.get():
                # Find next available slot
                opt_machine, opt_timestamp, opt_date, opt_hour, opt_minute = self._find_next_available_slot(
                    name, total_parts, cycle_time
                )
                if opt_machine:
                    machine_id = opt_machine
                    start_date = opt_date
                    start_hour = opt_hour
                    start_minute = opt_minute
            elif self.optimize_schedule_var.get():
                # Optimize production schedule
                opt_machine, opt_timestamp, opt_date, opt_hour, opt_minute = self._optimize_production_schedule(
                    name, total_parts, cycle_time
                )
                if opt_machine:
                    machine_id = opt_machine
                    start_date = opt_date
                    start_hour = opt_hour
                    start_minute = opt_minute
            
            # Create the job with parts
            job = self.scheduler_service.create_job_with_parts(
                name=name,
                machine_id=machine_id,
                total_parts=total_parts,
                cycle_time=cycle_time,
                start_date=start_date,
                start_hour=start_hour,
                start_minute=start_minute
            )
            
            # Show scheduling feedback
            if self.find_next_slot_var.get() or self.optimize_schedule_var.get():
                feedback_msg = f"Job '{name}' created successfully!\n\n"
                
                if self.find_next_slot_var.get():
                    if machine_id != original_machine:
                        feedback_msg += f"🔍 Intelligent Scheduling: Moved from {original_machine} to {machine_id}\n"
                    scheduled_time = f"{start_date} {start_hour:02d}:{start_minute:02d}"
                    original_time = f"{original_date} {original_hour:02d}:{original_minute:02d}"
                    if scheduled_time != original_time:
                        feedback_msg += f"🔍 Optimized Time: {original_time} → {scheduled_time}\n"
                elif self.optimize_schedule_var.get():
                    if machine_id != original_machine:
                        feedback_msg += f"⚡ Production Optimization: Moved from {original_machine} to {machine_id}\n"
                    scheduled_time = f"{start_date} {start_hour:02d}:{start_minute:02d}"
                    original_time = f"{original_date} {original_hour:02d}:{original_minute:02d}"
                    if scheduled_time != original_time:
                        feedback_msg += f"⚡ Optimized Time: {original_time} → {scheduled_time}\n"
                
                feedback_msg += "\nJob has been added to the schedule."
                messagebox.showinfo("Job Created", feedback_msg)
            
            # Hide the form
            self._toggle_new_job_form()
            
            # Update the UI
            self._update_jobs_overview()
            self._update_schedule()
            self._update_machine_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create job: {str(e)}")
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for scheduler events"""
        event_system.subscribe("job_added", lambda job: self._update_ui())
        event_system.subscribe("job_updated", lambda job: self._update_ui())
        event_system.subscribe("job_deleted", lambda job_id: self._update_ui())
        event_system.subscribe("part_added", lambda part: self._update_ui())
        event_system.subscribe("part_updated", lambda part: self._update_ui())
        event_system.subscribe("part_deleted", lambda part_id: self._update_ui())
        event_system.subscribe("part_moved", lambda part, old_machine_id, old_start_time: self._update_ui())
        event_system.subscribe("scheduler_data_loaded", lambda jobs, parts: self._update_ui())
    
    def _update_ui(self) -> None:
        """Update all UI components"""
        self._update_jobs_overview()
        self._update_schedule()
        self._update_machine_stats()
        
        # If job details panel is open, refresh it
        if self.job_details_panel and self.selected_job:
            job = self.scheduler_service.get_job(self.selected_job.job_id)
            if job:
                self._show_job_details(job)
            else:
                self._close_job_details()
    
    def _close_job_details(self) -> None:
        """Close the job details panel"""
        if self.job_details_panel:
            self.job_details_panel.destroy()
            self.job_details_panel = None
            self.selected_job = None
    
    def _start_part(self, part) -> None:
        """Mark a part as in-progress"""
        part.status = 'in-progress'
        part.estimate = False
        self.scheduler_service.update_part(part)
        self._update_ui()
    
    def _complete_part(self, part) -> None:
        """Mark a part as completed"""
        part.status = 'completed'
        self.scheduler_service.update_part(part)
        self._update_ui()
    
    def _edit_part(self, part) -> None:
        """Open a dialog to edit a part"""
        # This would typically open a dialog to edit the part
        # For simplicity, we'll just toggle the estimate flag
        part.estimate = not part.estimate
        self.scheduler_service.update_part(part)
        self._update_ui()
    
    def _delete_part(self, part) -> None:
        """Delete a part"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Part {part.part_number}?"):
            self.scheduler_service.delete_part(part.part_id)
            self._update_ui()
    
    def set_jms_service(self, jms_service) -> None:
        """
        Set the JMS service
        
        Args:
            jms_service: JMSService instance
        """
        self.jms_service = jms_service
        
        # Check if JMS service is available and working
        if self.jms_service and not hasattr(self.jms_service, 'client'):
            self.jms_service = None
            
        self._update_ui()
    
    def _sync_job_to_jms(self, job) -> None:
        """
        Synchronize a job to JMS
        
        Args:
            job: Job to synchronize
        """
        # Check if JMS is available
        try:
            from services.jms.jms_auth import REQUESTS_AVAILABLE
            if not REQUESTS_AVAILABLE:
                messagebox.showerror("JMS Error",
                                    "JMS integration requires the 'requests' package.\n"
                                    "Please install it using pip: pip install requests")
                return
        except ImportError:
            messagebox.showerror("JMS Error", "JMS integration is not available")
            return
            
        if not hasattr(self, 'jms_service') or not self.jms_service:
            messagebox.showerror("JMS Error", "JMS integration is not enabled")
            return
            
        try:
            # Show progress
            self.parent.config(cursor="wait")
            self.parent.update()
            
            # Sync job to JMS
            order_id = self.jms_service.sync_job_to_jms(job)
            
            # Show success message
            messagebox.showinfo("JMS Sync", f"Job '{job.name}' successfully synchronized to JMS (Order ID: {order_id})")
            
            # Update UI
            self._update_ui()
        except Exception as e:
            messagebox.showerror("JMS Error", str(e))
        finally:
            # Reset cursor
            self.parent.config(cursor="")
    
    # Enhanced UI Methods for New Features
    
    def _initialize_enhanced_features(self) -> None:
        """Initialize enhanced features and load default data"""
        try:
            # Set initial granularity
            self.time_granularity_manager.set_granularity(self.current_granularity)
            
            # Load activity types if not already loaded
            activity_types = self.booking_service.get_all_activity_types()
            if not activity_types:
                # Initialize with defaults
                defaults = ActivityType.create_default_types()
                for activity_type in defaults.values():
                    self.booking_service.create_activity_type(activity_type)
            
            event_system.publish("enhanced_features_initialized")
        except Exception as e:
            event_system.publish("error", f"Failed to initialize enhanced features: {str(e)}")
    
    def _create_enhanced_header_section(self, parent):
        """Create enhanced header with granularity controls"""
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title and main controls
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(title_frame, text="Machine Shop Scheduler", font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Right side controls container
        controls_frame = ttk.Frame(title_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        # Time granularity selector
        granularity_frame = ttk.LabelFrame(controls_frame, text="Time Scale", padding=5)
        granularity_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.granularity_var = tk.StringVar(value=self.current_granularity)
        granularity_combo = ttk.Combobox(
            granularity_frame,
            textvariable=self.granularity_var,
            values=['5min', '15min', '30min', '1hr'],
            state='readonly',
            width=8
        )
        granularity_combo.pack(side=tk.LEFT, padx=2)
        granularity_combo.bind('<<ComboboxSelected>>', self._on_granularity_changed)
        
        # Zoom buttons
        zoom_frame = ttk.Frame(granularity_frame)
        zoom_frame.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(zoom_frame, text="🔍+", width=4, command=self._zoom_in).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="🔍-", width=4, command=self._zoom_out).pack(side=tk.LEFT, padx=1)
        
        # Week navigation
        week_frame = ttk.Frame(controls_frame)
        week_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(week_frame, text="←", command=self._previous_week, width=3).pack(side=tk.LEFT, padx=1)
        
        self.week_label = ttk.Label(week_frame, text="", font=('Arial', 10))
        self.week_label.pack(side=tk.LEFT, padx=5)
        self._update_week_label()
        
        ttk.Button(week_frame, text="→", command=self._next_week, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(week_frame, text="Today", command=self._go_to_today, width=6).pack(side=tk.LEFT, padx=(5, 0))
        
        # Action buttons
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(side=tk.LEFT)
        
        ttk.Button(action_frame, text="+ Job", command=self._toggle_new_job_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="📅 Book", command=self._toggle_booking_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="🔒 Locks", command=self._toggle_lock_management).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="⭐ Priority", command=self._toggle_priority_panel).pack(side=tk.LEFT, padx=2)
    
    def _create_enhanced_machine_stats_section(self, parent):
        """Create enhanced machine stats with booking indicators"""
        self.stats_frame = ttk.LabelFrame(parent, text="Machine Status & Utilization", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create a grid for machine cards
        self.stats_grid = ttk.Frame(self.stats_frame)
        self.stats_grid.pack(fill=tk.X)
        
        # Populate enhanced machine stats
        self._update_enhanced_machine_stats()
    
    def _create_enhanced_jobs_overview_section(self, parent):
        """Create enhanced jobs overview with priority and lock indicators"""
        self.jobs_frame = ttk.LabelFrame(parent, text="Active Jobs", padding=10)
        self.jobs_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Jobs filter and sort controls
        controls_frame = ttk.Frame(self.jobs_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(controls_frame, text="Filter:").pack(side=tk.LEFT)
        
        self.job_filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.job_filter_var,
            values=['all', 'critical', 'high', 'normal', 'low', 'rush', 'locked'],
            state='readonly',
            width=10
        )
        filter_combo.pack(side=tk.LEFT, padx=(5, 10))
        filter_combo.bind('<<ComboboxSelected>>', self._on_job_filter_changed)
        
        ttk.Label(controls_frame, text="Sort:").pack(side=tk.LEFT)
        
        self.job_sort_var = tk.StringVar(value="priority")
        sort_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.job_sort_var,
            values=['priority', 'name', 'due_date', 'created'],
            state='readonly',
            width=10
        )
        sort_combo.pack(side=tk.LEFT, padx=(5, 0))
        sort_combo.bind('<<ComboboxSelected>>', self._on_job_sort_changed)
        
        # Create scrollable frame for job buttons
        self.jobs_canvas = tk.Canvas(self.jobs_frame, height=120)
        jobs_scrollbar = ttk.Scrollbar(self.jobs_frame, orient=tk.HORIZONTAL, command=self.jobs_canvas.xview)
        self.jobs_canvas.configure(xscrollcommand=jobs_scrollbar.set)
        
        jobs_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.jobs_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.jobs_buttons_frame = ttk.Frame(self.jobs_canvas)
        self.jobs_canvas.create_window((0, 0), window=self.jobs_buttons_frame, anchor=tk.NW)
        
        # Populate enhanced job buttons
        self._update_enhanced_jobs_overview()
    
    def _create_enhanced_new_job_form(self, parent):
        """Create enhanced new job form with priority options"""
        # Original form elements
        self._create_new_job_form(parent)
        
        # Add priority section
        priority_frame = ttk.LabelFrame(parent, text="Job Priority", padding=10)
        priority_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Priority level
        ttk.Label(priority_frame, text="Priority Level:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.new_job_priority_var = tk.StringVar(value="normal")
        priority_combo = ttk.Combobox(
            priority_frame,
            textvariable=self.new_job_priority_var,
            values=['critical', 'high', 'normal', 'low'],
            state='readonly'
        )
        priority_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Rush order checkbox
        self.rush_order_var = tk.BooleanVar()
        ttk.Checkbutton(
            priority_frame,
            text="Rush Order",
            variable=self.rush_order_var
        ).grid(row=0, column=2, sticky=tk.W, padx=10, pady=2)
        
        # Due date
        ttk.Label(priority_frame, text="Due Date (optional):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.due_date_var = tk.StringVar()
        ttk.Entry(priority_frame, textvariable=self.due_date_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Priority notes
        ttk.Label(priority_frame, text="Notes:").grid(row=1, column=2, sticky=tk.W, padx=10, pady=2)
        
        self.priority_notes_var = tk.StringVar()
        ttk.Entry(priority_frame, textvariable=self.priority_notes_var, width=30).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
    
    def _create_booking_form(self, parent):
        """Create machine booking form"""
        # Machine selection
        ttk.Label(parent, text="Machine:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.booking_machine_var = tk.StringVar()
        machine_combo = ttk.Combobox(parent, textvariable=self.booking_machine_var, width=20)
        machine_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Update machine options
        machines = self.machine_service.get_all_machines()
        machine_options = [f"{m.name} ({m.machine_id})" for m in machines.values()]
        machine_combo['values'] = machine_options
        
        # Activity type selection
        ttk.Label(parent, text="Activity:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.booking_activity_var = tk.StringVar()
        activity_combo = ttk.Combobox(parent, textvariable=self.booking_activity_var, width=20)
        activity_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Update activity options
        activity_types = self.booking_service.get_all_activity_types()
        activity_options = [(t.type_id, f"{t.icon} {t.name}") for t in activity_types.values()]
        activity_combo['values'] = [opt[1] for opt in activity_options]
        activity_combo.bind('<<ComboboxSelected>>',
                           lambda e: self.booking_activity_var.set(activity_options[activity_combo.current()][0]))
        
        # Date and time
        ttk.Label(parent, text="Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.booking_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(parent, textvariable=self.booking_date_var, width=12).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(parent, text="Start Time:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        time_frame = ttk.Frame(parent)
        time_frame.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        self.booking_hour_var = tk.IntVar(value=8)
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.booking_hour_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.booking_minute_var = tk.IntVar(value=0)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.booking_minute_var, width=5).pack(side=tk.LEFT)
        
        # Duration
        ttk.Label(parent, text="Duration (min):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.booking_duration_var = tk.IntVar(value=60)
        ttk.Spinbox(parent, from_=5, to=480, textvariable=self.booking_duration_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Description
        ttk.Label(parent, text="Description:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.booking_description_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.booking_description_var, width=30).grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Create Booking", command=self._create_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Check Conflicts", command=self._check_booking_conflicts).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._toggle_booking_form).pack(side=tk.LEFT, padx=5)
    
    def _create_priority_panel(self, parent):
        """Create priority management panel"""
        # Job selection
        ttk.Label(parent, text="Select Job:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.priority_job_var = tk.StringVar()
        job_combo = ttk.Combobox(parent, textvariable=self.priority_job_var, width=30)
        job_combo.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Update job options
        jobs = self.scheduler_service.get_all_jobs()
        job_options = [(j.job_id, j.name) for j in jobs.values()]
        job_combo['values'] = [opt[1] for opt in job_options]
        job_combo.bind('<<ComboboxSelected>>', self._on_priority_job_selected)
        
        # Priority controls
        ttk.Label(parent, text="Priority Level:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.priority_level_var = tk.StringVar(value="normal")
        priority_combo = ttk.Combobox(
            parent,
            textvariable=self.priority_level_var,
            values=['critical', 'high', 'normal', 'low'],
            state='readonly'
        )
        priority_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Rush order
        self.priority_rush_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Rush Order", variable=self.priority_rush_var).grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Due date
        ttk.Label(parent, text="Due Date:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.priority_due_date_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.priority_due_date_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Update Priority", command=self._update_job_priority).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Bulk Operations", command=self._show_bulk_priority_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self._toggle_priority_panel).pack(side=tk.LEFT, padx=5)
    
    def _create_enhanced_schedule_section(self, parent):
        """Create enhanced schedule section with granularity support"""
        schedule_frame = ttk.LabelFrame(parent, text="Weekly Schedule", padding=10)
        schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        # Schedule controls
        controls_frame = ttk.Frame(schedule_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # View options
        ttk.Label(controls_frame, text="View:").pack(side=tk.LEFT)
        
        self.schedule_view_var = tk.StringVar(value="timeline")
        view_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.schedule_view_var,
            values=['timeline', 'gantt', 'calendar'],
            state='readonly',
            width=10
        )
        view_combo.pack(side=tk.LEFT, padx=(5, 10))
        view_combo.bind('<<ComboboxSelected>>', self._on_schedule_view_changed)
        
        # Show/hide options
        self.show_bookings_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="Show Bookings", variable=self.show_bookings_var,
                       command=self._update_schedule).pack(side=tk.LEFT, padx=10)
        
        self.show_locks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="Show Locks", variable=self.show_locks_var,
                       command=self._update_schedule).pack(side=tk.LEFT, padx=10)
        
        # Granularity info
        self.granularity_info_label = ttk.Label(controls_frame, text="", font=('Arial', 8))
        self.granularity_info_label.pack(side=tk.RIGHT)
        self._update_granularity_info()
        
        # Create enhanced schedule canvas
        self.schedule_canvas = tk.Canvas(schedule_frame, bg="white")
        x_scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.HORIZONTAL, command=self.schedule_canvas.xview)
        y_scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=self.schedule_canvas.yview)
        
        self.schedule_canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        
        # Layout scrollbars and canvas
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create enhanced schedule content
        self.schedule_content = ttk.Frame(self.schedule_canvas)
        self.schedule_canvas.create_window((0, 0), window=self.schedule_content, anchor=tk.NW)
        
        # Configure canvas resizing
        self.schedule_content.bind("<Configure>", self._on_schedule_content_configure)
        
        # Populate the enhanced schedule
        self._update_enhanced_schedule()
    
    # Enhanced Event Handlers and UI Logic
    
    def _on_granularity_changed(self, event=None) -> None:
        """Handle granularity selection change"""
        new_granularity = self.granularity_var.get()
        if new_granularity != self.current_granularity:
            self.current_granularity = new_granularity
            self.time_granularity_manager.set_granularity(new_granularity)
            self._update_granularity_info()
            self._update_enhanced_schedule()
            event_system.publish("granularity_changed", new_granularity)
    
    def _zoom_in(self) -> None:
        """Zoom in to finer granularity"""
        granularities = ['1hr', '30min', '15min', '5min']
        current_index = granularities.index(self.current_granularity)
        if current_index < len(granularities) - 1:
            new_granularity = granularities[current_index + 1]
            self.granularity_var.set(new_granularity)
            self._on_granularity_changed()
    
    def _zoom_out(self) -> None:
        """Zoom out to coarser granularity"""
        granularities = ['1hr', '30min', '15min', '5min']
        current_index = granularities.index(self.current_granularity)
        if current_index > 0:
            new_granularity = granularities[current_index - 1]
            self.granularity_var.set(new_granularity)
            self._on_granularity_changed()
    
    def _update_granularity_info(self) -> None:
        """Update granularity information display"""
        info = self.time_granularity_manager.get_granularity_info()
        text = f"Scale: {info['display_name']} | {info['slots_per_day']} slots/day"
        self.granularity_info_label.config(text=text)
    
    def _toggle_booking_form(self) -> None:
        """Toggle machine booking form visibility"""
        if self.show_booking_form:
            self.booking_form_frame.pack_forget()
            self.show_booking_form = False
        else:
            # Hide other forms first
            if self.show_new_job_form:
                self._toggle_new_job_form()
            if self.show_priority_panel:
                self._toggle_priority_panel()
            
            self.booking_form_frame.pack(fill=tk.X, pady=5)
            self.show_booking_form = True
    
    def _toggle_priority_panel(self) -> None:
        """Toggle priority management panel visibility"""
        if self.show_priority_panel:
            self.priority_panel_frame.pack_forget()
            self.show_priority_panel = False
        else:
            # Hide other forms first
            if self.show_new_job_form:
                self._toggle_new_job_form()
            if self.show_booking_form:
                self._toggle_booking_form()
            
            self.priority_panel_frame.pack(fill=tk.X, pady=5)
            self.show_priority_panel = True
    
    def _toggle_lock_management(self) -> None:
        """Toggle lock management panel"""
        if self.lock_management_panel:
            self.lock_management_panel.destroy()
            self.lock_management_panel = None
        else:
            self._show_lock_management_panel()
    
    def _create_booking(self) -> None:
        """Create a new machine booking"""
        try:
            # Get machine ID from selection
            machine_selection = self.booking_machine_var.get()
            if not machine_selection:
                messagebox.showerror("Error", "Please select a machine")
                return
            
            # Extract machine ID (format: "Name (ID)")
            machine_id = machine_selection.split('(')[1].rstrip(')')
            
            # Get activity type ID
            activity_type_id = self.booking_activity_var.get()
            if not activity_type_id:
                messagebox.showerror("Error", "Please select an activity type")
                return
            
            # Parse date and time
            date_str = self.booking_date_var.get()
            hour = self.booking_hour_var.get()
            minute = self.booking_minute_var.get()
            
            # Create datetime
            date_parts = date_str.split('-')
            booking_datetime = datetime(
                int(date_parts[0]), int(date_parts[1]), int(date_parts[2]),
                hour, minute, 0, 0
            )
            start_time = int(booking_datetime.timestamp() * 1000)
            
            # Create booking
            booking = self.booking_service.create_booking(
                machine_id=machine_id,
                activity_type_id=activity_type_id,
                start_time=start_time,
                duration=self.booking_duration_var.get(),
                description=self.booking_description_var.get(),
                created_by="user"
            )
            
            messagebox.showinfo("Success", f"Booking created: {booking.booking_id}")
            
            # Check and resolve conflicts if needed
            conflicts = self.scheduler_service.check_booking_conflicts_for_all_jobs()
            if conflicts:
                if messagebox.askyesno("Conflicts Found",
                                     f"Found {len(conflicts)} job conflicts. Resolve automatically?"):
                    self._resolve_all_booking_conflicts()
            
            # Refresh UI
            self._update_enhanced_schedule()
            self._toggle_booking_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create booking: {str(e)}")
    
    def _check_booking_conflicts(self) -> None:
        """Check for booking conflicts without creating"""
        try:
            # Get booking parameters
            machine_selection = self.booking_machine_var.get()
            if not machine_selection:
                messagebox.showerror("Error", "Please select a machine")
                return
            
            machine_id = machine_selection.split('(')[1].rstrip(')')
            date_str = self.booking_date_var.get()
            hour = self.booking_hour_var.get()
            minute = self.booking_minute_var.get()
            duration = self.booking_duration_var.get()
            
            # Create datetime
            date_parts = date_str.split('-')
            booking_datetime = datetime(
                int(date_parts[0]), int(date_parts[1]), int(date_parts[2]),
                hour, minute, 0, 0
            )
            start_time = int(booking_datetime.timestamp() * 1000)
            end_time = start_time + (duration * 60 * 1000)
            
            # Check machine availability
            is_available = self.booking_service.get_machine_availability(machine_id, start_time, duration)
            
            # Get conflicting parts
            all_parts = self.scheduler_service.get_all_parts()
            conflicting_parts = []
            
            for part in all_parts.values():
                if part.machine_id != machine_id:
                    continue
                
                job = self.scheduler_service.get_job(part.job_id)
                if not job:
                    continue
                
                part_end = part.start_time + (job.cycle_time * 60 * 1000)
                
                if part.start_time < end_time and part_end > start_time:
                    conflicting_parts.append((part, job))
            
            # Show results
            if is_available and not conflicting_parts:
                messagebox.showinfo("No Conflicts", "Machine is available for the requested time.")
            else:
                conflict_msg = f"Conflicts found:\n"
                if not is_available:
                    conflict_msg += "- Machine has existing bookings\n"
                if conflicting_parts:
                    conflict_msg += f"- {len(conflicting_parts)} production jobs would be affected\n"
                    for part, job in conflicting_parts[:5]:  # Show first 5
                        conflict_msg += f"  • {job.name} part {part.part_number}\n"
                
                messagebox.showwarning("Conflicts Detected", conflict_msg)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check conflicts: {str(e)}")
    
    def _update_job_priority(self) -> None:
        """Update selected job priority"""
        try:
            job_selection = self.priority_job_var.get()
            if not job_selection:
                messagebox.showerror("Error", "Please select a job")
                return
            
            # Find job by name
            jobs = self.scheduler_service.get_all_jobs()
            selected_job = None
            for job in jobs.values():
                if job.name == job_selection:
                    selected_job = job
                    break
            
            if not selected_job:
                messagebox.showerror("Error", "Selected job not found")
                return
            
            # Parse due date if provided
            due_date = None
            due_date_str = self.priority_due_date_var.get().strip()
            if due_date_str:
                try:
                    due_date_dt = datetime.strptime(due_date_str, "%Y-%m-%d")
                    due_date = int(due_date_dt.timestamp() * 1000)
                except ValueError:
                    messagebox.showerror("Error", "Invalid due date format. Use YYYY-MM-DD")
                    return
            
            # Update priority
            priority = self.scheduler_service.set_job_priority(
                job_id=selected_job.job_id,
                priority_level=self.priority_level_var.get(),
                rush_order=self.priority_rush_var.get(),
                due_date=due_date
            )
            
            messagebox.showinfo("Success", f"Priority updated for {selected_job.name}")
            
            # Refresh UI
            self._update_enhanced_jobs_overview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update priority: {str(e)}")
    
    def _on_priority_job_selected(self, event=None) -> None:
        """Handle job selection in priority panel"""
        job_selection = self.priority_job_var.get()
        if not job_selection:
            return
        
        # Find job and load current priority
        jobs = self.scheduler_service.get_all_jobs()
        for job in jobs.values():
            if job.name == job_selection:
                priority = self.scheduler_service.get_job_priority(job.job_id)
                
                if priority:
                    self.priority_level_var.set(priority.priority_level)
                    self.priority_rush_var.set(priority.rush_order)
                    if priority.due_date:
                        due_date_str = datetime.fromtimestamp(priority.due_date / 1000).strftime("%Y-%m-%d")
                        self.priority_due_date_var.set(due_date_str)
                else:
                    # Set defaults from job
                    self.priority_level_var.set(job.priority_level)
                    self.priority_rush_var.set(job.rush_order)
                break
    
    def _on_job_filter_changed(self, event=None) -> None:
        """Handle job filter change"""
        self._update_enhanced_jobs_overview()
    
    def _on_job_sort_changed(self, event=None) -> None:
        """Handle job sort change"""
        self._update_enhanced_jobs_overview()
    
    def _on_schedule_view_changed(self, event=None) -> None:
        """Handle schedule view change"""
        self._update_enhanced_schedule()
    
    def _on_schedule_content_configure(self, event) -> None:
        """Handle schedule content resize"""
        self.schedule_canvas.configure(
            scrollregion=self.schedule_canvas.bbox("all"),
            width=max(self.schedule_content.winfo_reqwidth(), self.schedule_canvas.winfo_width()),
            height=max(self.schedule_content.winfo_reqheight(), self.schedule_canvas.winfo_height())
        )
    
    def _update_enhanced_machine_stats(self) -> None:
        """Update enhanced machine stats with booking information"""
        # Clear existing stats
        for widget in self.stats_grid.winfo_children():
            widget.destroy()
        
        # Get machines
        machines = self.machine_service.get_all_machines()
        if not machines:
            ttk.Label(self.stats_grid, text="No machines configured.").grid(row=0, column=0)
            return
        
        # Create enhanced cards for each machine
        for i, (machine_id, machine) in enumerate(machines.items()):
            # Calculate utilization
            utilization = self.scheduler_service.get_machine_utilization(machine_id, self.selected_week)
            
            # Get bookings for this week
            week_end = self.selected_week + (7 * 24 * 60 * 60 * 1000)
            bookings = self.booking_service.get_machine_bookings(machine_id, self.selected_week, week_end)
            booking_hours = sum(b.duration for b in bookings) / 60
            
            # Create enhanced card frame
            card = ttk.Frame(self.stats_grid, padding=10, relief=tk.RIDGE)
            card.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky=tk.W)
            
            # Machine name with status indicator
            name_frame = ttk.Frame(card)
            name_frame.pack(fill=tk.X)
            
            ttk.Label(name_frame, text=machine.name, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            
            # Status indicators
            indicators_frame = ttk.Frame(name_frame)
            indicators_frame.pack(side=tk.RIGHT)
            
            # Check if machine has active bookings
            current_time = int(datetime.now().timestamp() * 1000)
            active_bookings = [b for b in bookings if b.start_time <= current_time <= b.get_end_time()]
            
            if active_bookings:
                activity_type = self.booking_service.get_activity_type(active_bookings[0].activity_type_id)
                status_text = activity_type.icon if activity_type else "🔧"
                ttk.Label(indicators_frame, text=status_text, font=('Arial', 12)).pack(side=tk.RIGHT, padx=2)
            
            # Check for locked jobs
            jobs_on_machine = [j for j in self.scheduler_service.get_all_jobs().values()
                             if any(p.machine_id == machine_id for p in self.scheduler_service.get_job_parts(j.job_id))]
            locked_jobs = [j for j in jobs_on_machine if self.locking_service.is_job_locked(j.job_id)]
            
            if locked_jobs:
                ttk.Label(indicators_frame, text="🔒", font=('Arial', 10)).pack(side=tk.RIGHT, padx=2)
            
            # Machine type
            ttk.Label(card, text=machine.machine_type, font=('Arial', 8)).pack(anchor=tk.W)
            
            # Utilization
            util_frame = ttk.Frame(card)
            util_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Label(util_frame, text=f"Production: {utilization:.1f}%").pack(anchor=tk.W)
            ttk.Label(util_frame, text=f"Bookings: {booking_hours:.1f}h").pack(anchor=tk.W)
            
            # Progress bars
            prod_progress = ttk.Progressbar(card, value=utilization, maximum=100, length=120)
            prod_progress.pack(anchor=tk.W, pady=(2, 0))
            
            booking_util = (booking_hours / (7 * 24)) * 100
            booking_progress = ttk.Progressbar(card, value=booking_util, maximum=100, length=120)
            booking_progress.pack(anchor=tk.W, pady=(2, 0))
    
    def _update_enhanced_jobs_overview(self) -> None:
        """Update enhanced jobs overview with filtering and sorting"""
        # Clear existing job buttons
        for widget in self.jobs_buttons_frame.winfo_children():
            widget.destroy()
        
        # Get and filter jobs
        all_jobs = self.scheduler_service.get_all_jobs()
        filtered_jobs = self._filter_jobs(all_jobs)
        sorted_jobs = self._sort_jobs(filtered_jobs)
        
        if not sorted_jobs:
            ttk.Label(self.jobs_buttons_frame, text="No jobs match the current filter.").pack(anchor=tk.W)
            return
        
        # Create enhanced job buttons
        for i, job in enumerate(sorted_jobs):
            self._create_enhanced_job_button(job, i)
        
        # Update canvas scroll region
        self.jobs_buttons_frame.update_idletasks()
        self.jobs_canvas.configure(scrollregion=self.jobs_canvas.bbox("all"))
    
    def _filter_jobs(self, jobs: Dict[str, Job]) -> List[Job]:
        """Filter jobs based on current filter setting"""
        filter_value = self.job_filter_var.get()
        
        if filter_value == "all":
            return list(jobs.values())
        elif filter_value in ["critical", "high", "normal", "low"]:
            return [job for job in jobs.values() if job.priority_level == filter_value]
        elif filter_value == "rush":
            return [job for job in jobs.values() if job.rush_order]
        elif filter_value == "locked":
            return [job for job in jobs.values() if self.locking_service.is_job_locked(job.job_id)]
        else:
            return list(jobs.values())
    
    def _sort_jobs(self, jobs: List[Job]) -> List[Job]:
        """Sort jobs based on current sort setting"""
        sort_value = self.job_sort_var.get()
        
        if sort_value == "priority":
            return sorted(jobs, key=lambda j: j.workpiece_priority, reverse=True)
        elif sort_value == "name":
            return sorted(jobs, key=lambda j: j.name)
        elif sort_value == "due_date":
            return sorted(jobs, key=lambda j: self._get_job_due_date(j) or float('inf'))
        elif sort_value == "created":
            return sorted(jobs, key=lambda j: j.created_at, reverse=True)
        else:
            return jobs
    
    def _get_job_due_date(self, job: Job) -> Optional[int]:
        """Get job due date from priority information"""
        priority = self.scheduler_service.get_job_priority(job.job_id)
        return priority.due_date if priority else None
    
    def _create_enhanced_job_button(self, job: Job, index: int) -> None:
        """Create an enhanced job button with priority and lock indicators"""
        # Get job parts for completion status
        job_parts = self.scheduler_service.get_job_parts(job.job_id)
        completed_parts = sum(1 for part in job_parts if part.status == 'completed')
        in_progress_parts = sum(1 for part in job_parts if part.status == 'in-progress')
        
        # Create job frame
        job_frame = tk.Frame(self.jobs_buttons_frame)
        job_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Determine button style and indicators
        button_bg = job.color
        status_indicators = []
        
        # Priority indicator
        priority_icons = {'critical': '🔴', 'high': '🟡', 'normal': '🟢', 'low': '🔵'}
        status_indicators.append(priority_icons.get(job.priority_level, '⚪'))
        
        # Rush order indicator
        if job.rush_order:
            status_indicators.append('⚡')
        
        # Lock indicators
        scheduler_locked = self.locking_service.is_job_locked(job.job_id)
        jms_locked = job.status == 'locked'
        
        if scheduler_locked and jms_locked:
            status_indicators.append('🔐')
        elif scheduler_locked:
            status_indicators.append('🔒')
        elif jms_locked:
            status_indicators.append('🏭')
        
        # Due date indicator
        priority = self.scheduler_service.get_job_priority(job.job_id)
        if priority and priority.is_overdue():
            status_indicators.append('⏰')
        
        # Create job button
        indicators_text = ''.join(status_indicators)
        button_text = f"{indicators_text} {job.name}\n({completed_parts}/{job.total_parts})"
        
        job_button = tk.Button(
            job_frame,
            text=button_text,
            bg=button_bg,
            fg="white",
            relief=tk.RAISED,
            borderwidth=2,
            padx=10,
            pady=8,
            font=('Arial', 9, 'bold'),
            command=lambda j=job: self._show_enhanced_job_details(j),
            justify=tk.CENTER
        )
        job_button.pack()
        
        # Add context menu
        self._add_job_context_menu(job_button, job)
        
        # JMS sync indicator
        is_synced = hasattr(self, 'jms_service') and self.jms_service and \
                   job.job_id in getattr(self.jms_service, 'job_order_mappings', {})
        
        if is_synced:
            jms_label = tk.Label(
                job_frame,
                text="JMS",
                bg="#3b82f6",
                fg="white",
                font=('Arial', 7, 'bold'),
                padx=3,
                pady=1
            )
            jms_label.pack(fill=tk.X)
    
    def _add_job_context_menu(self, widget: tk.Widget, job: Job) -> None:
        """Add context menu to job button"""
        context_menu = tk.Menu(widget, tearoff=0)
        
        context_menu.add_command(label="📋 Job Details", command=lambda: self._show_enhanced_job_details(job))
        context_menu.add_separator()
        
        # Priority options
        priority_menu = tk.Menu(context_menu, tearoff=0)
        for level in ['critical', 'high', 'normal', 'low']:
            priority_menu.add_command(
                label=f"Set {level.title()}",
                command=lambda l=level: self._quick_set_priority(job, l)
            )
        context_menu.add_cascade(label="⭐ Priority", menu=priority_menu)
        
        # Lock options
        if self.locking_service.is_job_locked(job.job_id):
            context_menu.add_command(label="🔓 Unlock", command=lambda: self._toggle_job_lock(job))
        else:
            context_menu.add_command(label="🔒 Lock", command=lambda: self._toggle_job_lock(job))
        
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ Delete", command=lambda: self._delete_job_with_confirmation(job))
        
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        widget.bind("<Button-3>", show_context_menu)  # Right click
    
    def _update_enhanced_schedule(self) -> None:
        """Update the enhanced schedule display"""
        # Clear existing schedule
        for widget in self.schedule_content.winfo_children():
            widget.destroy()
        
        # Get view mode
        view_mode = self.schedule_view_var.get()
        
        if view_mode == "timeline":
            self._render_timeline_view()
        elif view_mode == "gantt":
            self._render_gantt_view()
        elif view_mode == "calendar":
            self._render_calendar_view()
        
        # Update canvas scroll region
        self.schedule_content.update_idletasks()
        self.schedule_canvas.configure(scrollregion=self.schedule_canvas.bbox("all"))
    
    def _render_timeline_view(self) -> None:
        """Render the timeline view with enhanced granularity"""
        machines = self.machine_service.get_all_machines()
        week_days = self._get_week_days()
        
        # Calculate dimensions based on granularity
        granularity_info = self.time_granularity_manager.get_granularity_info()
        day_width = granularity_info['day_width_pixels']
        
        # Create header
        self._create_timeline_header(week_days, day_width)
        
        # Create machine rows
        for i, (machine_id, machine) in enumerate(machines.items()):
            self._create_enhanced_machine_row(machine, i + 1, week_days, day_width)
    
    def _create_timeline_header(self, week_days, day_width) -> None:
        """Create enhanced timeline header"""
        header_frame = ttk.Frame(self.schedule_content)
        header_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        # Machine column header
        machine_header = ttk.Label(header_frame, text="Machine", font=('Arial', 10, 'bold'), width=15)
        machine_header.grid(row=0, column=0, sticky=tk.NSEW, padx=1, pady=1)
        
        # Day headers with granularity-aware time slots
        for i, day in enumerate(week_days):
            day_frame = ttk.Frame(header_frame)
            day_frame.grid(row=0, column=i + 1, sticky=tk.NSEW, padx=1, pady=1)
            
            # Day label
            day_name = day.strftime("%a %d %b")
            is_today = day.date() == datetime.now().date()
            
            day_label = ttk.Label(
                day_frame,
                text=day_name + (" (Today)" if is_today else ""),
                font=('Arial', 10, 'bold'),
                background="#e6f0ff" if is_today else "#f0f0f0",
                anchor=tk.CENTER
            )
            day_label.pack(fill=tk.X)
            
            # Time slot labels based on granularity
            time_labels = self.time_granularity_manager.get_visible_time_labels(day)
            
            if len(time_labels) <= 24:  # Show all labels for coarse granularity
                time_frame = ttk.Frame(day_frame)
                time_frame.pack(fill=tk.X)
                
                for time_dt, label, pixel_pos in time_labels[::max(1, len(time_labels)//12)]:  # Show max 12 labels
                    time_label = ttk.Label(
                        time_frame,
                        text=label,
                        font=('Arial', 7),
                        anchor=tk.CENTER,
                        width=4
                    )
                    time_label.pack(side=tk.LEFT)
    
    def _create_enhanced_machine_row(self, machine, row_index, week_days, day_width) -> None:
        """Create enhanced machine row with bookings and lock indicators"""
        row_frame = ttk.Frame(self.schedule_content)
        row_frame.grid(row=row_index, column=0, sticky=tk.NSEW)
        
        # Machine name with status indicators
        machine_cell = ttk.Frame(row_frame)
        machine_cell.grid(row=0, column=0, sticky=tk.NSEW, padx=1, pady=1)
        
        # Machine name
        name_label = ttk.Label(machine_cell, text=machine.name, font=('Arial', 9, 'bold'))
        name_label.pack(anchor=tk.W)
        
        # Machine type
        type_label = ttk.Label(machine_cell, text=machine.machine_type, font=('Arial', 7))
        type_label.pack(anchor=tk.W)
        
        # Status indicators
        indicators = []
        
        # Check for active bookings
        current_time = int(datetime.now().timestamp() * 1000)
        active_bookings = [b for b in self.booking_service.get_machine_bookings(machine.machine_id)
                          if b.start_time <= current_time <= b.get_end_time()]
        if active_bookings:
            indicators.append("🔧")
        
        # Check for locked jobs
        jobs_on_machine = [j for j in self.scheduler_service.get_all_jobs().values()
                          if any(p.machine_id == machine.machine_id for p in self.scheduler_service.get_job_parts(j.job_id))]
        locked_jobs = [j for j in jobs_on_machine if self.locking_service.is_job_locked(j.job_id)]
        if locked_jobs:
            indicators.append("🔒")
        
        if indicators:
            indicator_label = ttk.Label(machine_cell, text=' '.join(indicators), font=('Arial', 8))
            indicator_label.pack(anchor=tk.W)
        
        # Day cells with enhanced rendering
        for j, day in enumerate(week_days):
            self._create_enhanced_day_cell(machine, day, row_frame, j + 1, day_width)
    
    def _create_enhanced_day_cell(self, machine, day, parent_frame, column, day_width) -> None:
        """Create enhanced day cell with bookings and parts"""
        day_start = int(day.timestamp() * 1000)
        day_end = day_start + (24 * 60 * 60 * 1000)
        
        # Create day container
        day_frame = ttk.Frame(parent_frame)
        day_frame.grid(row=0, column=column, sticky=tk.NSEW, padx=1, pady=1)
        
        # Create canvas for this day
        day_canvas = tk.Canvas(day_frame, width=day_width, height=80, bg="white", highlightthickness=0)
        day_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw time grid based on granularity
        self._draw_granularity_grid(day_canvas, day, day_width)
        
        # Render bookings if enabled
        if self.show_bookings_var.get():
            self._render_machine_bookings(day_canvas, machine.machine_id, day_start, day_end, day_width)
        
        # Render job parts
        self._render_job_parts(day_canvas, machine.machine_id, day_start, day_end, day_width)
        
        # Make day cell a drop target
        self._make_enhanced_day_cell_droppable(day_canvas, machine.machine_id, day_start, day_width)
    
    def _draw_granularity_grid(self, canvas, day, day_width) -> None:
        """Draw time grid based on current granularity"""
        time_slots = self.time_granularity_manager.get_time_slots(day)
        pixels_per_slot = self.time_granularity_manager.get_pixels_per_granularity_unit()
        
        for i, slot_time in enumerate(time_slots):
            x = i * pixels_per_slot
            
            # Draw grid lines
            line_color = "#e0e0e0"
            if slot_time.hour == 0:  # Midnight - thicker line
                line_color = "#b0b0b0"
                canvas.create_line(x, 0, x, 80, fill=line_color, width=2)
            elif slot_time.minute == 0:  # Hour boundaries
                line_color = "#d0d0d0"
                canvas.create_line(x, 0, x, 80, fill=line_color, width=1)
            else:  # Sub-hour boundaries
                canvas.create_line(x, 0, x, 80, fill=line_color, width=1)
    
    def _render_machine_bookings(self, canvas, machine_id, day_start, day_end, day_width) -> None:
        """Render machine bookings on the timeline"""
        bookings = self.booking_service.get_machine_bookings(machine_id, day_start, day_end)
        
        for booking in bookings:
            activity_type = self.booking_service.get_activity_type(booking.activity_type_id)
            
            # Calculate position and size
            start_offset = max(0, (booking.start_time - day_start) / (1000 * 60))  # minutes from day start
            duration_minutes = booking.duration
            end_offset = start_offset + duration_minutes
            
            # Convert to pixels
            start_x = self.time_granularity_manager.calculate_pixel_offset(start_offset)
            width = self.time_granularity_manager.calculate_pixel_width(duration_minutes)
            
            # Ensure booking is visible within day bounds
            if start_x < 0:
                width += start_x
                start_x = 0
            if start_x + width > day_width:
                width = day_width - start_x
            
            if width > 0:
                # Create booking block
                booking_color = activity_type.color if activity_type else "#6b7280"
                
                # Background block
                canvas.create_rectangle(
                    start_x, 2, start_x + width, 78,
                    fill=booking_color,
                    outline=booking_color,
                    width=2,
                    tags=f"booking_{booking.booking_id}"
                )
                
                # Activity icon/text if space allows
                if width > 30 and activity_type:
                    canvas.create_text(
                        start_x + width/2, 40,
                        text=f"{activity_type.icon}\n{activity_type.name[:8]}",
                        fill="white",
                        font=('Arial', 8, 'bold'),
                        justify=tk.CENTER,
                        tags=f"booking_{booking.booking_id}"
                    )
    
    def _render_job_parts(self, canvas, machine_id, day_start, day_end, day_width) -> None:
        """Render job parts on the timeline with enhanced visual indicators"""
        day_parts = self.scheduler_service.get_parts_for_day(machine_id, day_start)
        
        for part in day_parts:
            job = self.scheduler_service.get_job(part.job_id)
            if not job:
                continue
            
            # Calculate position and size
            start_offset = max(0, (part.start_time - day_start) / (1000 * 60))  # minutes from day start
            duration_minutes = job.cycle_time
            
            # Convert to pixels
            start_x = self.time_granularity_manager.calculate_pixel_offset(start_offset)
            width = self.time_granularity_manager.calculate_pixel_width(duration_minutes)
            
            # Ensure part is visible within day bounds
            if start_x < 0:
                width += start_x
                start_x = 0
            if start_x + width > day_width:
                width = day_width - start_x
            
            if width > 5:  # Only render if visible
                self._render_single_job_part(canvas, part, job, start_x, width)
    
    def _render_single_job_part(self, canvas, part, job, start_x, width) -> None:
        """Render a single job part with enhanced indicators"""
        # Determine part styling
        part_color = job.color
        border_color = part_color
        
        # Lock indicators
        if self.show_locks_var.get():
            scheduler_locked = self.locking_service.is_job_locked(job.job_id)
            jms_locked = job.status == 'locked'
            
            if scheduler_locked:
                border_color = "#dc2626"  # Red border for scheduler lock
            elif jms_locked:
                border_color = "#1d4ed8"  # Blue border for JMS lock
        
        # Priority styling
        if job.priority_level == 'critical':
            border_color = "#dc2626"  # Red
        elif job.rush_order:
            border_color = "#f59e0b"  # Amber
        
        # Create main part block
        y_offset = 15 if job.priority_level in ['critical', 'high'] else 25
        height = 50 if job.priority_level in ['critical', 'high'] else 40
        
        part_id = canvas.create_rectangle(
            start_x, y_offset, start_x + width, y_offset + height,
            fill=part_color,
            outline=border_color,
            width=2,
            tags=f"part_{part.part_id}"
        )
        
        # Part number indicator
        if width > 20:
            number_bg = "#3b82f6" if not part.estimate else "#fbbf24"
            canvas.create_oval(
                start_x - 6, y_offset - 6, start_x + 14, y_offset + 14,
                fill=number_bg,
                outline="white",
                width=2,
                tags=f"part_{part.part_id}"
            )
            
            canvas.create_text(
                start_x + 4, y_offset + 4,
                text=str(part.part_number),
                fill="white",
                font=('Arial', 8, 'bold'),
                tags=f"part_{part.part_id}"
            )
        
        # Job name and status if space allows
        if width > 50:
            canvas.create_text(
                start_x + width/2, y_offset + height/2,
                text=f"{job.name}\nPart {part.part_number}/{job.total_parts}",
                fill="white",
                font=('Arial', 7, 'bold'),
                justify=tk.CENTER,
                tags=f"part_{part.part_id}"
            )
        
        # Status indicators
        indicators = []
        if part.status == 'in-progress':
            indicators.append("▶️")
        elif part.status == 'completed':
            indicators.append("✅")
        
        if job.rush_order:
            indicators.append("⚡")
        
        if indicators and width > 30:
            canvas.create_text(
                start_x + width - 10, y_offset + 10,
                text=''.join(indicators),
                font=('Arial', 8),
                tags=f"part_{part.part_id}"
            )
        
        # Make part draggable
        self._make_enhanced_part_draggable(canvas, part_id, part)
    
    def _make_enhanced_part_draggable(self, canvas, item_id, part) -> None:
        """Enhanced part dragging with lock checking"""
        def on_drag_start(event):
            # Check if part can be moved
            can_move, reason = self.scheduler_service.can_move_part(part.part_id)
            if not can_move:
                messagebox.showwarning("Cannot Move", f"Part cannot be moved: {reason}")
                return
            
            canvas.drag_data = {
                "item_id": item_id,
                "part": part,
                "x": event.x,
                "y": event.y
            }
            canvas.config(cursor="fleur")
            canvas.tag_raise(item_id)
        
        def on_drag_motion(event):
            if hasattr(canvas, 'drag_data') and canvas.drag_data:
                dx = event.x - canvas.drag_data["x"]
                canvas.move(canvas.drag_data["item_id"], dx, 0)
                canvas.drag_data["x"] = event.x
        
        def on_drag_end(event):
            if hasattr(canvas, 'drag_data') and canvas.drag_data:
                canvas.config(cursor="")
                canvas.drag_data = None
        
        canvas.tag_bind(item_id, "<ButtonPress-1>", on_drag_start)
        canvas.tag_bind(item_id, "<B1-Motion>", on_drag_motion)
        canvas.tag_bind(item_id, "<ButtonRelease-1>", on_drag_end)
    
    def _make_enhanced_day_cell_droppable(self, canvas, machine_id, day_start, day_width) -> None:
        """Enhanced drop handling with granularity snapping"""
        def on_drop(event):
            if hasattr(canvas, 'drag_data') and canvas.drag_data and canvas.drag_data["part"]:
                # Calculate drop time with granularity snapping
                drop_offset_minutes = (event.x / day_width) * (24 * 60)  # Convert pixel to minutes
                drop_time = day_start + (drop_offset_minutes * 60 * 1000)  # Convert to milliseconds
                
                # Snap to current granularity
                snapped_time = self.time_granularity_manager.snap_to_grid(drop_time)
                
                # Move part with enhanced checking
                part = canvas.drag_data["part"]
                success, message = self.scheduler_service.move_part_with_lock_check(
                    part.part_id, machine_id, snapped_time
                )
                
                if not success:
                    messagebox.showerror("Move Failed", message)
                
                # Update schedule
                self._update_enhanced_schedule()
        
        canvas.bind("<ButtonRelease-1>", on_drop)
    
    def _render_gantt_view(self) -> None:
        """Render Gantt chart view (placeholder)"""
        placeholder = ttk.Label(self.schedule_content, text="Gantt View - Coming Soon", font=('Arial', 16))
        placeholder.pack(expand=True)
    
    def _render_calendar_view(self) -> None:
        """Render calendar view (placeholder)"""
        placeholder = ttk.Label(self.schedule_content, text="Calendar View - Coming Soon", font=('Arial', 16))
        placeholder.pack(expand=True)
    
    # Additional Helper Methods
    
    def _quick_set_priority(self, job: Job, priority_level: str) -> None:
        """Quick set job priority from context menu"""
        try:
            self.scheduler_service.set_job_priority(job.job_id, priority_level)
            self._update_enhanced_jobs_overview()
            messagebox.showinfo("Success", f"Set {job.name} priority to {priority_level}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set priority: {str(e)}")
    
    def _toggle_job_lock(self, job: Job) -> None:
        """Toggle job lock status"""
        try:
            if self.locking_service.is_job_locked(job.job_id):
                self.locking_service.remove_scheduler_lock(job.job_id)
                messagebox.showinfo("Success", f"Unlocked {job.name}")
            else:
                self.locking_service.apply_scheduler_lock(job.job_id, locked_by="user")
                messagebox.showinfo("Success", f"Locked {job.name}")
            
            self._update_enhanced_jobs_overview()
            self._update_enhanced_schedule()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle lock: {str(e)}")
    
    def _delete_job_with_confirmation(self, job: Job) -> None:
        """Delete job with confirmation dialog"""
        if messagebox.askyesno("Confirm Delete",
                              f"Delete job '{job.name}' and all {job.total_parts} parts?"):
            try:
                self.scheduler_service.delete_job(job.job_id)
                self._update_enhanced_jobs_overview()
                self._update_enhanced_schedule()
                messagebox.showinfo("Success", f"Deleted job {job.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete job: {str(e)}")
    
    def _show_enhanced_job_details(self, job: Job) -> None:
        """Show enhanced job details panel"""
        # Enhanced version of the existing job details panel
        self._show_job_details(job)
    
    def _show_lock_management_panel(self) -> None:
        """Show lock management panel"""
        self.lock_management_panel = tk.Toplevel(self.parent)
        self.lock_management_panel.title("Lock Management")
        self.lock_management_panel.geometry("600x400")
        
        # Lock statistics
        stats_frame = ttk.LabelFrame(self.lock_management_panel, text="Lock Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats = self.locking_service.get_statistics()
        ttk.Label(stats_frame, text=f"Total Active Locks: {stats['total_active_locks']}").pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"Arrangement Locks: {stats['arrangement_locks']}").pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"Full Edit Locks: {stats['full_edit_locks']}").pack(anchor=tk.W)
        
        # Active locks list
        locks_frame = ttk.LabelFrame(self.lock_management_panel, text="Active Locks", padding=10)
        locks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for locks
        columns = ("Job", "Type", "User", "Expires", "Reason")
        locks_tree = ttk.Treeview(locks_frame, columns=columns, show='headings')
        
        for col in columns:
            locks_tree.heading(col, text=col)
            locks_tree.column(col, width=100)
        
        # Populate locks
        active_locks = self.locking_service.get_all_locks()
        for lock in active_locks.values():
            job = self.scheduler_service.get_job(lock.job_id)
            job_name = job.name if job else lock.job_id
            
            expires_text = "Never" if lock.expires_at is None else str(lock.get_remaining_time_minutes()) + " min"
            
            locks_tree.insert('', 'end', values=(
                job_name,
                lock.lock_type,
                lock.locked_by,
                expires_text,
                lock.reason
            ))
        
        locks_tree.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        button_frame = ttk.Frame(self.lock_management_panel)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Unlock Selected",
                  command=lambda: self._unlock_selected_jobs(locks_tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Unlock All Mine",
                  command=lambda: self._unlock_all_user_jobs()).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh",
                  command=lambda: self._refresh_lock_panel()).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close",
                  command=self.lock_management_panel.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _show_bulk_priority_dialog(self) -> None:
        """Show bulk priority operations dialog"""
        bulk_dialog = tk.Toplevel(self.parent)
        bulk_dialog.title("Bulk Priority Operations")
        bulk_dialog.geometry("500x300")
        
        # Job selection
        selection_frame = ttk.LabelFrame(bulk_dialog, text="Select Jobs", padding=10)
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Priority operation
        operation_frame = ttk.LabelFrame(bulk_dialog, text="Priority Operation", padding=10)
        operation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(operation_frame, text="Set Priority Level:").pack(side=tk.LEFT)
        
        bulk_priority_var = tk.StringVar(value="normal")
        ttk.Combobox(operation_frame, textvariable=bulk_priority_var,
                    values=['critical', 'high', 'normal', 'low']).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(operation_frame, text="Apply to Selected",
                  command=lambda: self._apply_bulk_priority(bulk_priority_var.get())).pack(side=tk.LEFT, padx=10)
        
        # Close button
        ttk.Button(bulk_dialog, text="Close", command=bulk_dialog.destroy).pack(pady=10)