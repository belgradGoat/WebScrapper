"""
Scheduler Tab for Machine Shop Scheduler
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
from typing import Dict, List, Any, Optional, Callable

from models.job import Job
from models.part import Part
from models.machine import Machine
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
        
        # State variables
        self.selected_week = self._get_current_week_start()
        self.selected_job = None
        self.dragged_part = None
        self.editing_part = None
        self.show_new_job_form = False
        
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
        
        # Setup UI components
        self.setup_ui()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main container with vertical layout
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header section
        self._create_header_section(main_container)
        
        # Machine stats section
        self._create_machine_stats_section(main_container)
        
        # Jobs overview section
        self._create_jobs_overview_section(main_container)
        
        # New job form (initially hidden)
        self.new_job_frame = ttk.LabelFrame(main_container, text="Add New Job", padding=10)
        self._create_new_job_form(self.new_job_frame)
        
        # Schedule section
        self._create_schedule_section(main_container)
        
        # Job details panel (initially hidden)
        self.job_details_panel = None
        
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
            
            # Create job button with custom styling
            job_button = tk.Button(
                job_frame,
                text=f"{job.name} ({completed_parts}/{job.total_parts})",
                bg=job.color,
                fg="white",
                relief=tk.RAISED,
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
            
            # Create the job with parts
            self.scheduler_service.create_job_with_parts(
                name=name,
                machine_id=machine_id,
                total_parts=total_parts,
                cycle_time=cycle_time,
                start_date=start_date,
                start_hour=start_hour,
                start_minute=start_minute
            )
            
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
        self._update_ui()
    
    def _sync_job_to_jms(self, job) -> None:
        """
        Synchronize a job to JMS
        
        Args:
            job: Job to synchronize
        """
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