import cv2
import mediapipe as mp
import numpy as np
import logging
import json

class EyeTracker:
    """Uses MediaPipe to detect face landmarks and determine gaze direction."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the eye tracker with MediaPipe models."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('EyeTracker')
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Face mesh with refined landmarks for accurate eye detection
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Landmark indices for eyes
        # Left eye landmarks (iris)
        self.LEFT_IRIS = [474, 475, 476, 477]
        # Right eye landmarks (iris)
        self.RIGHT_IRIS = [469, 470, 471, 472]
        # Left eye outline landmarks
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        # Right eye outline landmarks
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        
        self.logger.info("Eye tracker initialized")

    def process_frame(self, frame):
        """
        Process a frame to detect face and eyes.
        Returns whether the user is looking at the screen, 
        whether a face is detected, and a visualization frame for debugging.
        """
        if frame is None:
            return False, False, None
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width = frame.shape[:2]
        
        # Process the frame with MediaPipe Face Mesh
        results = self.face_mesh.process(rgb_frame)
        
        # Create a copy for visualization
        debug_frame = frame.copy()
        
        # Default: Not looking at screen
        looking_at_screen = False
        face_detected = False
        
        if results.multi_face_landmarks:
            face_detected = True
            for face_landmarks in results.multi_face_landmarks:
                # Draw face landmarks
                self.mp_drawing.draw_landmarks(
                    image=debug_frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                
                # Draw eye landmarks
                self.mp_drawing.draw_landmarks(
                    image=debug_frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style()
                )
                
                # Extract eye landmarks
                mesh_points = np.array([
                    [p.x * frame_width, p.y * frame_height]
                    for p in face_landmarks.landmark
                ], dtype=np.int32)
                
                # Get iris landmarks
                left_iris_points = mesh_points[self.LEFT_IRIS]
                right_iris_points = mesh_points[self.RIGHT_IRIS]
                
                # Calculate center of each iris
                left_iris_center = np.mean(left_iris_points, axis=0).astype(int)
                right_iris_center = np.mean(right_iris_points, axis=0).astype(int)
                
                # Draw iris centers
                cv2.circle(debug_frame, tuple(left_iris_center), 2, (0, 255, 0), -1)
                cv2.circle(debug_frame, tuple(right_iris_center), 2, (0, 255, 0), -1)
                
                # Get eye contours for position analysis
                left_eye_contour = mesh_points[self.LEFT_EYE]
                right_eye_contour = mesh_points[self.RIGHT_EYE]
                
                # Calculate eye contour centers
                left_eye_center = np.mean(left_eye_contour, axis=0).astype(int)
                right_eye_center = np.mean(right_eye_contour, axis=0).astype(int)
                
                # Draw eye contour centers
                cv2.circle(debug_frame, tuple(left_eye_center), 2, (255, 0, 0), -1)
                cv2.circle(debug_frame, tuple(right_eye_center), 2, (255, 0, 0), -1)
                
                # Calculate positions of iris relative to eye contours
                # This helps determine if looking left/right/center
                left_iris_x_ratio = (left_iris_center[0] - np.min(left_eye_contour[:, 0])) / (np.max(left_eye_contour[:, 0]) - np.min(left_eye_contour[:, 0]))
                right_iris_x_ratio = (right_iris_center[0] - np.min(right_eye_contour[:, 0])) / (np.max(right_eye_contour[:, 0]) - np.min(right_eye_contour[:, 0]))
                
                # Calculate y-position ratios (up/down gaze)
                left_iris_y_ratio = (left_iris_center[1] - np.min(left_eye_contour[:, 1])) / (np.max(left_eye_contour[:, 1]) - np.min(left_eye_contour[:, 1]))
                right_iris_y_ratio = (right_iris_center[1] - np.min(right_eye_contour[:, 1])) / (np.max(right_eye_contour[:, 1]) - np.min(right_eye_contour[:, 1]))
                
                # Simple thresholds for looking at screen (these can be fine-tuned)
                # Looking at screen if both irises are relatively centered
                # Widening the thresholds for multi-screen setup
                looking_left = left_iris_x_ratio < 0.25 and right_iris_x_ratio < 0.25
                looking_right = left_iris_x_ratio > 0.75 and right_iris_x_ratio > 0.75
                looking_up = left_iris_y_ratio < 0.25 and right_iris_y_ratio < 0.25
                looking_down = left_iris_y_ratio > 0.75 and right_iris_y_ratio > 0.75
                
                # Check if the user is looking at the screen
                looking_at_screen = not (looking_left or looking_right or looking_up or looking_down)
                
                # Draw gaze status
                status_text = "Looking at screen" if looking_at_screen else "Looking away"
                cv2.putText(debug_frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                             1, (0, 255, 0) if looking_at_screen else (0, 0, 255), 2)
                
                # Debug text
                cv2.putText(debug_frame, f"L: {left_iris_x_ratio:.2f}, {left_iris_y_ratio:.2f}", 
                           (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(debug_frame, f"R: {right_iris_x_ratio:.2f}, {right_iris_y_ratio:.2f}", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            # No face detected
            cv2.putText(debug_frame, "No face detected", (20, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return looking_at_screen, face_detected, debug_frame
    
    def __del__(self):
        """Clean up resources."""
        self.face_mesh.close()
        self.logger.info("Eye tracker resources released")


if __name__ == "__main__":
    # Test the eye tracker with camera input
    import camera
    
    cam = camera.Camera()
    eye_tracker = EyeTracker()
    
    if cam.start():
        print("Press 'q' to quit the test")
        while True:
            frame = cam.get_frame()
            if frame is not None:
                looking_at_screen, face_detected, debug_frame = eye_tracker.process_frame(frame)
                
                if debug_frame is not None:
                    cv2.imshow('Eye Tracker Test', debug_frame)
                
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("Failed to get frame, exiting...")
                break
                
        cam.stop()
        cv2.destroyAllWindows()
    else:
        print("Failed to start camera") 