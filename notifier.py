import tkinter as tk
from tkinter import ttk
import threading
import logging
import json
import time
import subprocess
import sys
import os


class Notifier:
    """Handles break notifications and visual alerts."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the notifier with configuration settings."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('Notifier')
        
        self.use_sound = self.config.get('use_sound_notifications', True)
        self.break_duration = self.config.get('min_break_duration_seconds', 20)
        
        # Break window references
        self.break_window = None
        self.break_timer_label = None
        self.break_thread = None
        self.stop_break_thread = threading.Event()
        
        self.logger.info("Notifier initialized")
    
    def show_break_notification(self):
        """Show a system notification for taking a break."""
        try:
            # Use osascript for macOS notifications instead of plyer
            if sys.platform == 'darwin':
                title = '20-20-20 Eye Break Reminder'
                message = 'Time to look 20 feet away for 20 seconds!'
                
                script = f'''
                display notification "{message}" with title "{title}"
                '''
                
                subprocess.run(['osascript', '-e', script])
                
                # Optional sound notification
                if self.use_sound:
                    subprocess.run(['osascript', '-e', 'beep 2'])
                
                self.logger.info("Break notification displayed (macOS)")
            else:
                # For other platforms, try to use plyer as a fallback
                try:
                    from plyer import notification
                    notification.notify(
                        title='20-20-20 Eye Break Reminder',
                        message='Time to look 20 feet away for 20 seconds!',
                        app_name='EyeBreak',
                        timeout=10
                    )
                    self.logger.info("Break notification displayed (plyer)")
                except Exception as e:
                    self.logger.error(f"Plyer notification failed: {str(e)}")
                    # If plyer fails, just log it - the break window will still appear
                
        except Exception as e:
            self.logger.error(f"Error showing notification: {str(e)}")
    
    def show_break_window(self, on_complete_callback=None):
        """
        Display a break window with countdown timer.
        
        Args:
            on_complete_callback: Function to call when break is complete
        """
        # If there's already a break window, don't create another one
        if self.break_window is not None:
            self.logger.warning("Break window already exists")
            return
        
        try:
            # Create the break window
            self.break_window = tk.Toplevel()
            self.break_window.title("Eye Break Time!")
            
            # Set window properties
            self.break_window.attributes('-topmost', True)
            
            # Get screen dimensions
            screen_width = self.break_window.winfo_screenwidth()
            screen_height = self.break_window.winfo_screenheight()
            
            # Calculate window size (1/4 of screen)
            window_width = screen_width // 3
            window_height = screen_height // 3
            
            # Calculate position (centered)
            position_x = (screen_width - window_width) // 2
            position_y = (screen_height - window_height) // 2
            
            # Set window size and position
            self.break_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
            
            # Create a frame with padding
            main_frame = ttk.Frame(self.break_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Header label
            header_label = ttk.Label(
                main_frame, 
                text="Time for an eye break!",
                font=("Arial", 20, "bold")
            )
            header_label.pack(pady=(0, 20))
            
            # Instructions label
            instructions_label = ttk.Label(
                main_frame,
                text="Look at something 20 feet away for 20 seconds.\nThis helps reduce eye strain.",
                font=("Arial", 14),
                justify="center"
            )
            instructions_label.pack(pady=(0, 30))
            
            # Timer label
            self.break_timer_label = ttk.Label(
                main_frame,
                text=f"Remaining: {self.break_duration} seconds",
                font=("Arial", 16)
            )
            self.break_timer_label.pack(pady=(0, 30))
            
            # Skip button
            skip_button = ttk.Button(
                main_frame, 
                text="Skip Break", 
                command=self._close_break_window
            )
            skip_button.pack()
            
            # Start the countdown timer in a separate thread
            self.stop_break_thread.clear()
            self.break_thread = threading.Thread(
                target=self._countdown_timer, 
                args=(on_complete_callback,)
            )
            self.break_thread.daemon = True
            self.break_thread.start()
            
            # Handle window close event
            self.break_window.protocol("WM_DELETE_WINDOW", self._close_break_window)
            
            self.logger.info("Break window displayed")
            
        except Exception as e:
            self.logger.error(f"Error showing break window: {str(e)}")
            # Ensure cleanup in case of error
            self._close_break_window()
    
    def _countdown_timer(self, on_complete_callback=None):
        """Run the countdown timer for the break window."""
        remaining_seconds = self.break_duration
        
        while remaining_seconds > 0 and not self.stop_break_thread.is_set():
            # Update the timer label
            if self.break_timer_label and self.break_window:
                self.break_window.after(0, lambda s=remaining_seconds: 
                                           self.break_timer_label.config(
                                               text=f"Remaining: {s} seconds"))
            
            # Wait for one second
            time.sleep(1)
            remaining_seconds -= 1
        
        # Close the break window when done
        if not self.stop_break_thread.is_set():
            # Break completed normally
            self.logger.info("Break countdown completed")
            if on_complete_callback:
                on_complete_callback()
            
            if self.break_window:
                self.break_window.after(0, self._close_break_window)
    
    def _close_break_window(self):
        """Close the break window and clean up resources."""
        # Stop the countdown thread
        self.stop_break_thread.set()
        
        # Destroy the window if it exists
        if self.break_window:
            self.break_window.destroy()
            self.break_window = None
            self.break_timer_label = None
            self.logger.info("Break window closed")


if __name__ == "__main__":
    # Test the notifier
    print("Testing notification...")
    notifier = Notifier()
    
    # Test system notification
    notifier.show_break_notification()
    
    # Test break window
    def on_break_complete():
        print("Break completed!")
    
    print("Displaying break window...")
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    notifier.show_break_window(on_complete_callback=on_break_complete)
    
    # Keep the main thread running
    root.mainloop() 