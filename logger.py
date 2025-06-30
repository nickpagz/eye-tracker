import json
import logging
import time
from datetime import datetime
import os


class EyeLogger:
    """Records gaze sessions and break events."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the logger with configuration settings."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set up logging for debug
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('EyeLogger')
        
        # Check if logging is enabled
        self.log_enabled = self.config.get('log_data', False)
        if not self.log_enabled:
            self.logger.info("Data logging is disabled in config")
            return
        
        # Log file path
        self.log_file = self.config.get('log_file', 'eye_tracker_logs.json')
        
        # Session stats
        self.session_start_time = time.time()
        self.total_gaze_time = 0
        self.total_break_time = 0
        self.break_count = 0
        self.current_gaze_start = None
        self.current_break_start = None
        
        # Initialize or load log file
        self._init_log_file()
        
        self.logger.info(f"EyeLogger initialized, logging to {self.log_file}")
    
    def _init_log_file(self):
        """Initialize or load the log file."""
        if not self.log_enabled:
            return
            
        # Check if the log file exists
        if not os.path.exists(self.log_file):
            # Create a new log file with initial structure
            initial_data = {
                "sessions": [],
                "total_stats": {
                    "total_gaze_time": 0,
                    "total_break_time": 0,
                    "total_break_count": 0,
                    "first_session": datetime.now().isoformat(),
                    "last_session": None
                }
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
                
            self.logger.info(f"Created new log file: {self.log_file}")
    
    def start_gaze(self):
        """Record the start of a gaze period."""
        if not self.log_enabled:
            return
            
        if self.current_gaze_start is None:
            self.current_gaze_start = time.time()
            if self.current_break_start is not None:
                # Calculate break time
                break_duration = time.time() - self.current_break_start
                self.total_break_time += break_duration
                self.current_break_start = None
    
    def end_gaze(self):
        """Record the end of a gaze period."""
        if not self.log_enabled:
            return
            
        if self.current_gaze_start is not None:
            # Calculate gaze time
            gaze_duration = time.time() - self.current_gaze_start
            self.total_gaze_time += gaze_duration
            self.current_gaze_start = None
            
            # Start break period
            self.current_break_start = time.time()
    
    def log_break(self):
        """Record a break event."""
        if not self.log_enabled:
            return
            
        self.break_count += 1
        self.logger.info(f"Break #{self.break_count} logged")
    
    def save_session(self):
        """Save the current session data to the log file."""
        if not self.log_enabled:
            return
            
        # Calculate final stats if needed
        if self.current_gaze_start is not None:
            self.end_gaze()
            
        # Prepare session data
        session_end_time = time.time()
        session_duration = session_end_time - self.session_start_time
        
        session_data = {
            "date": datetime.now().isoformat(),
            "session_duration": session_duration,
            "gaze_time": self.total_gaze_time,
            "break_time": self.total_break_time,
            "break_count": self.break_count,
            "avg_gaze_duration": self.total_gaze_time / max(1, self.break_count) if self.break_count > 0 else self.total_gaze_time
        }
        
        try:
            # Load existing log data
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            # Update the log data
            log_data["sessions"].append(session_data)
            log_data["total_stats"]["total_gaze_time"] += self.total_gaze_time
            log_data["total_stats"]["total_break_time"] += self.total_break_time
            log_data["total_stats"]["total_break_count"] += self.break_count
            log_data["total_stats"]["last_session"] = datetime.now().isoformat()
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            self.logger.info(f"Session logged successfully to {self.log_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving session log: {str(e)}")
    
    def get_session_stats(self):
        """Return the current session statistics."""
        if not self.log_enabled:
            return {
                "logging_enabled": False
            }
            
        return {
            "logging_enabled": True,
            "session_duration": time.time() - self.session_start_time,
            "gaze_time": self.total_gaze_time,
            "break_time": self.total_break_time,
            "break_count": self.break_count
        }


if __name__ == "__main__":
    # Test the logger
    print("Testing eye logger...")
    
    # Enable logging in config by temporarily modifying it
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    original_log_setting = config.get('log_data', False)
    config['log_data'] = True
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    try:
        logger = EyeLogger()
        
        # Simulate some gaze and break periods
        print("Simulating gaze period (5 seconds)...")
        logger.start_gaze()
        time.sleep(5)
        logger.end_gaze()
        
        print("Logging a break...")
        logger.log_break()
        time.sleep(2)
        
        print("Simulating another gaze period (3 seconds)...")
        logger.start_gaze()
        time.sleep(3)
        logger.end_gaze()
        
        print("Logging another break...")
        logger.log_break()
        
        # Save the session
        logger.save_session()
        
        # Print session stats
        stats = logger.get_session_stats()
        print("\nSession Stats:")
        for key, value in stats.items():
            print(f"{key}: {value}")
            
        # Check if log file exists and contains data
        if os.path.exists(logger.log_file):
            print(f"\nLog file created: {logger.log_file}")
            with open(logger.log_file, 'r') as f:
                log_data = json.load(f)
                print(f"Number of sessions logged: {len(log_data['sessions'])}")
        else:
            print("Log file was not created")
            
    finally:
        # Restore original config
        config['log_data'] = original_log_setting
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2) 