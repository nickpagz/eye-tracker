import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import cv2
import time
import threading
import sys
import os
import json
import logging
import atexit
import signal

# Import custom modules
from camera import Camera
from eye_tracker import EyeTracker
from gaze_timer import GazeTimer
from notifier import Notifier
from logger import EyeLogger


class EyeBreakApp:
    """Main application that integrates all components for the 20-20-20 rule."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the application with configuration settings."""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('EyeBreakApp')
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Create main tkinter window
        self.root = tk.Tk()
        self.root.title("20-20-20 Eye Break Reminder")
        self.root.withdraw()  # Hide the main window
        
        # Initialize components
        self.camera = Camera(config_path)
        self.eye_tracker = EyeTracker(config_path)
        self.gaze_timer = GazeTimer(config_path)
        self.notifier = Notifier(config_path)
        self.eye_logger = EyeLogger(config_path)
        
        # App state
        self.running = True
        self.break_triggered = False
        self.debug_mode = False
        self.debug_window = None
        self.debug_frame = None
        
        # Setup system tray icon (if on macos)
        self._setup_tray()
        
        # Setup break completion callback
        self.break_completed_callback = self._on_break_completed
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.logger.info("EyeBreak application initialized")
    
    def _setup_tray(self):
        """Set up the system tray icon and menu."""
        # Create a simple menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="Toggle Debug Mode", command=self._toggle_debug)
        file_menu.add_command(label="Take a Break Now", command=self._take_break_now)
        file_menu.add_command(label="Reset Timer", command=self._reset_timer)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.cleanup)
        
        # This could be improved to use an actual tray icon with a third-party library
        # but for simplicity we use a minimal window approach
        
        # Create a minimal window for control
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Eye Break Control")
        self.control_window.geometry("300x200")
        self.control_window.protocol("WM_DELETE_WINDOW", self._hide_control_window)
        
        # Add some controls
        frame = ttk.Frame(self.control_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="20-20-20 Eye Break Reminder", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Running in background").pack()
        
        # Status display
        self.status_var = tk.StringVar(value="Status: Monitoring...")
        ttk.Label(frame, textvariable=self.status_var).pack(pady=(10, 0))
        
        # Timer display
        self.timer_var = tk.StringVar(value="Time: 00:00")
        ttk.Label(frame, textvariable=self.timer_var).pack()
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Debug", command=self._toggle_debug).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Break Now", command=self._take_break_now).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.cleanup).pack(side=tk.LEFT, padx=5)
        
        self.control_window.withdraw()  # Hide until needed
    
    def _hide_control_window(self):
        """Hide the control window instead of closing it."""
        self.control_window.withdraw()
    
    def _toggle_debug(self):
        """Toggle debug mode to show/hide the webcam feed."""
        self.debug_mode = not self.debug_mode
        
        if self.debug_mode:
            # Create debug window if it doesn't exist
            if self.debug_window is None:
                self.debug_window = tk.Toplevel(self.root)
                self.debug_window.title("Eye Tracker Debug")
                self.debug_window.protocol("WM_DELETE_WINDOW", self._toggle_debug)
                
                # Create a label for displaying the video feed
                self.debug_frame = tk.Label(self.debug_window)
                self.debug_frame.pack()
                
                self.logger.info("Debug mode enabled")
        else:
            # Close debug window if it exists
            if self.debug_window is not None:
                self.debug_window.destroy()
                self.debug_window = None
                self.debug_frame = None
                
                self.logger.info("Debug mode disabled")
    
    def _take_break_now(self):
        """Manually trigger a break."""
        self.break_triggered = True
        self.gaze_timer.reset()
        self.logger.info("Break manually triggered")
        self._show_break()
    
    def _reset_timer(self):
        """Reset the gaze timer."""
        self.gaze_timer.reset()
        self.logger.info("Timer reset")
        self.status_var.set("Status: Timer reset")
    
    def _on_break_completed(self):
        """Handle the break completion event."""
        self.break_triggered = False
        self.eye_logger.log_break()
        self.gaze_timer.reset()
        self.logger.info("Break completed")
    
    def _show_break(self):
        """Show the break notification and window."""
        self.notifier.show_break_notification()
        self.notifier.show_break_window(on_complete_callback=self.break_completed_callback)
    
    def _update_ui(self, looking_at_screen, face_detected, break_needed, in_break, remaining_break_time, gaze_time):
        """Update the UI based on the current state."""
        # Update status text
        if in_break:
            status = f"Status: Taking a break ({int(remaining_break_time)}s remaining)"
        elif break_needed:
            status = "Status: Break needed!"
        elif not face_detected:
            status = "Status: No face detected"
        elif looking_at_screen:
            status = "Status: Looking at screen"
        else:
            status = "Status: Looking away"
        
        self.status_var.set(status)
        
        # Update timer display
        self.timer_var.set(f"Time: {self.gaze_timer.get_formatted_gaze_time()}")
        
        # Update debug window if it exists
        if self.debug_mode and self.debug_window and self.debug_frame and hasattr(self, 'debug_image'):
            # Convert OpenCV image to PhotoImage
            img = cv2.cvtColor(self.debug_image, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (640, 480))
            img = tk.PhotoImage(data=cv2.imencode('.ppm', img)[1].tobytes())
            
            # Update label with new image
            self.debug_frame.config(image=img)
            self.debug_frame.image = img  # Keep a reference to prevent garbage collection
    
    def _signal_handler(self, sig, frame):
        """Handle signal interrupts."""
        self.logger.info(f"Received signal {sig}, shutting down.")
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources and save session data."""
        if hasattr(self, 'running') and self.running:
            self.running = False
            
            # Cleanup resources
            if hasattr(self, 'camera'):
                self.camera.stop()
                
            # Save session data
            if hasattr(self, 'eye_logger'):
                self.eye_logger.save_session()
                
            # Destroy tkinter windows
            if hasattr(self, 'root') and self.root:
                self.root.quit()
                
            self.logger.info("Application cleaned up")
            
            # Exit the program
            sys.exit(0)
    
    def run(self):
        """Run the application main loop."""
        # Start the camera
        if not self.camera.start():
            self.logger.error("Failed to start camera. Exiting.")
            tk.messagebox.showerror("Error", "Failed to start the camera. Please check your webcam.")
            return
        
        # Start the UI update loop in a separate thread
        ui_thread = threading.Thread(target=self._ui_loop)
        ui_thread.daemon = True
        ui_thread.start()
        
        # Show control window and notification on startup
        self.control_window.deiconify()
        
        # Start the tkinter main loop
        self.root.mainloop()
    
    def _ui_loop(self):
        """Background thread for updating UI and processing frames."""
        while self.running:
            # Get frame from camera
            frame = self.camera.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Process frame with eye tracker
            looking_at_screen, face_detected, debug_frame = self.eye_tracker.process_frame(frame)
            
            # Store debug frame for UI updates
            self.debug_image = debug_frame
            
            # For timer purposes: 
            # - When face is detected and looking at screen: looking_at_screen = True
            # - When face is detected but not looking at screen: looking_at_screen = False
            # - When no face is detected, treat it the same as not looking at screen
            effective_looking_at_screen = looking_at_screen and face_detected
            
            # Update the eye logger based on gaze state (only when face is detected)
            if effective_looking_at_screen:
                self.eye_logger.start_gaze()
            else:
                self.eye_logger.end_gaze()
            
            # Update the gaze timer - use our effective value that treats "no face" as "not looking"
            break_needed, in_break, remaining_break_time, gaze_time = self.gaze_timer.update(effective_looking_at_screen)
            
            # Check if we need to show a break notification
            if break_needed and not self.break_triggered and not in_break:
                self.break_triggered = True
                self._show_break()
            
            # Update UI
            if self.root:
                self.root.after(100, lambda: self._update_ui(
                    looking_at_screen, face_detected, break_needed, in_break, remaining_break_time, gaze_time
                ))
            
            # Sleep to reduce CPU usage
            time.sleep(0.05)


if __name__ == "__main__":
    print("Starting 20-20-20 Eye Break Reminder...")
    print("Press Ctrl+C to exit")
    
    app = EyeBreakApp()
    app.run() 