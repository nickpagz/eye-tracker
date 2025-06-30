import cv2
import logging
import json

class Camera:
    """Handle webcam access and frame capture."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the camera with configuration settings."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.camera = None
        self.camera_index = self.config.get('camera_index', 0)
        self.is_running = False
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('Camera')
    
    def start(self):
        """Start the camera."""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                self.logger.error(f"Failed to open camera with index {self.camera_index}")
                return False
            
            self.is_running = True
            self.logger.info("Camera started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error starting camera: {str(e)}")
            return False
    
    def stop(self):
        """Stop the camera and release resources."""
        if self.camera and self.is_running:
            self.camera.release()
            self.is_running = False
            self.logger.info("Camera stopped")
    
    def get_frame(self):
        """Capture and return a frame from the camera."""
        if not self.is_running:
            self.logger.warning("Attempted to get frame from stopped camera")
            return None
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                self.logger.warning("Failed to grab frame")
                return None
            
            # Flip horizontally for a more mirror-like view
            frame = cv2.flip(frame, 1)
            return frame
        except Exception as e:
            self.logger.error(f"Error capturing frame: {str(e)}")
            return None

    def __del__(self):
        """Clean up resources when object is deleted."""
        self.stop()


if __name__ == "__main__":
    # Simple test for the camera module
    camera = Camera()
    if camera.start():
        print("Press 'q' to quit the test")
        while True:
            frame = camera.get_frame()
            if frame is not None:
                cv2.imshow('Camera Test', frame)
                
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("Failed to get frame, exiting...")
                break
                
        camera.stop()
        cv2.destroyAllWindows()
    else:
        print("Failed to start camera") 