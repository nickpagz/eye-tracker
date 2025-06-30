import time
import logging
import json
from datetime import datetime, timedelta

class GazeTimer:
    """Tracks screen gaze time and manages break notifications."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the gaze timer with settings from config."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('GazeTimer')
        
        # Main timer settings from config
        self.max_screen_time_minutes = self.config.get('max_screen_time_minutes', 20)
        self.min_break_duration_seconds = self.config.get('min_break_duration_seconds', 20)
        self.off_screen_threshold_seconds = self.config.get('off_screen_threshold_seconds', 10)
        
        # Convert to seconds for internal use
        self.max_screen_time_seconds = self.max_screen_time_minutes * 60
        
        # Timer state
        self.gaze_start_time = None
        self.away_start_time = None
        self.continuous_gaze_time = 0
        self.break_needed = False
        self.in_break = False
        self.break_start_time = None
        
        self.logger.info(f"GazeTimer initialized with {self.max_screen_time_minutes} min screen time, "
                          f"{self.min_break_duration_seconds} sec break duration, "
                          f"{self.off_screen_threshold_seconds} sec off-screen threshold")
    
    def update(self, looking_at_screen):
        """
        Update the timer based on current gaze state.
        Returns a tuple of (break_needed, in_break, remaining_break_time, current_gaze_time)
        """
        current_time = time.time()
        
        # If currently in a break, check if it's complete
        if self.in_break:
            # Already in a break, check if it's complete
            if current_time - self.break_start_time >= self.min_break_duration_seconds:
                self.logger.info("Break completed")
                self.in_break = False
                self.break_needed = False
                self.continuous_gaze_time = 0
                self.gaze_start_time = None if not looking_at_screen else current_time
                self.away_start_time = current_time if not looking_at_screen else None
            else:
                remaining_break_time = self.min_break_duration_seconds - (current_time - self.break_start_time)
                return self.break_needed, self.in_break, remaining_break_time, self.continuous_gaze_time
        
        if looking_at_screen:
            # User is looking at the screen
            if self.away_start_time is not None:
                # We were away but now looking at screen again - reset away timer
                self.away_start_time = None
                
            if self.gaze_start_time is None:
                # Start of a new gaze period
                self.gaze_start_time = current_time
                self.logger.debug("Starting new gaze period")
            
            # Calculate continuous gaze time
            if self.break_needed:
                # Break is needed but user is still looking at screen
                self.continuous_gaze_time = self.max_screen_time_seconds
            else:
                elapsed = current_time - self.gaze_start_time
                self.continuous_gaze_time = elapsed
                
                # Check if max screen time reached
                if elapsed >= self.max_screen_time_seconds and not self.break_needed:
                    self.break_needed = True
                    self.logger.info(f"Break needed after {elapsed:.1f} seconds of continuous gaze")
        else:
            # User is looking away from the screen
            if self.away_start_time is None:
                # Just started looking away
                self.away_start_time = current_time
                self.logger.debug("User looked away")
            
            # Keep tracking continuous gaze time when looking away temporarily
            # Only reset when threshold is met or during a break
            
            # Check if looking away long enough to be considered a break
            away_time = current_time - self.away_start_time
            
            if away_time >= self.off_screen_threshold_seconds:
                # Been looking away long enough to count as a break
                if self.break_needed and not self.in_break:
                    # User is taking a break after notification
                    self.in_break = True
                    self.break_start_time = self.away_start_time
                    self.logger.info("Break started")
                elif not self.break_needed:
                    # Reset gaze timer since user took a natural break
                    self.gaze_start_time = None
                    self.continuous_gaze_time = 0
                    self.logger.debug(f"Gaze timer reset after {away_time:.1f} seconds away")
                # If break_needed and in_break, maintain the current state
            else:
                # Looking away but not long enough to reset timer
                # Maintain the current gaze_start_time and continuous_gaze_time
                self.logger.debug(f"Looking away for {away_time:.1f}s (threshold: {self.off_screen_threshold_seconds}s)")
        
        # Calculate remaining break time if in a break
        remaining_break_time = 0
        if self.in_break:
            elapsed_break_time = current_time - self.break_start_time
            remaining_break_time = max(0, self.min_break_duration_seconds - elapsed_break_time)
        
        return self.break_needed, self.in_break, remaining_break_time, self.continuous_gaze_time
    
    def start_break(self):
        """Manually start a break period."""
        if not self.in_break:
            self.in_break = True
            self.break_start_time = time.time()
            self.logger.info("Break started manually")
    
    def reset(self):
        """Reset all timers."""
        self.gaze_start_time = None
        self.away_start_time = None
        self.continuous_gaze_time = 0
        self.break_needed = False
        self.in_break = False
        self.break_start_time = None
        self.logger.info("GazeTimer reset")

    def get_formatted_gaze_time(self):
        """Return the current continuous gaze time as mm:ss string."""
        minutes, seconds = divmod(int(self.continuous_gaze_time), 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_formatted_break_time(self):
        """Return the remaining break time as ss string."""
        if not self.in_break:
            return "00"
        
        current_time = time.time()
        elapsed_break_time = current_time - self.break_start_time
        remaining_seconds = max(0, int(self.min_break_duration_seconds - elapsed_break_time))
        return f"{remaining_seconds:02d}"


if __name__ == "__main__":
    # Simple test for the GazeTimer
    import time
    
    timer = GazeTimer()
    
    print("Simulating looking at screen for 5 seconds...")
    start_time = time.time()
    while time.time() - start_time < 5:
        break_needed, in_break, remaining_break, gaze_time = timer.update(True)
        time.sleep(0.1)
        print(f"Gaze time: {timer.get_formatted_gaze_time()}, Break needed: {break_needed}")
    
    print("\nSimulating looking away for 3 seconds (below threshold)...")
    start_time = time.time()
    while time.time() - start_time < 3:
        break_needed, in_break, remaining_break, gaze_time = timer.update(False)
        time.sleep(0.1)
        print(f"Gaze time: {timer.get_formatted_gaze_time()}, Break needed: {break_needed}")
    
    print("\nSimulating looking at screen for 3 more seconds...")
    start_time = time.time()
    while time.time() - start_time < 3:
        break_needed, in_break, remaining_break, gaze_time = timer.update(True)
        time.sleep(0.1)
        print(f"Gaze time: {timer.get_formatted_gaze_time()}, Break needed: {break_needed}")
    
    print("\nSimulating looking away for 15 seconds (above threshold, should reset timer)...")
    start_time = time.time()
    while time.time() - start_time < 15:
        break_needed, in_break, remaining_break, gaze_time = timer.update(False)
        time.sleep(0.1)
        print(f"Gaze time: {timer.get_formatted_gaze_time()}, Break needed: {break_needed}")
    
    print("\nGaze timer should be reset. Simulating looking at screen again...")
    start_time = time.time()
    while time.time() - start_time < 3:
        break_needed, in_break, remaining_break, gaze_time = timer.update(True)
        time.sleep(0.1)
        print(f"Gaze time: {timer.get_formatted_gaze_time()}, Break needed: {break_needed}") 