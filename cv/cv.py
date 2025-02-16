import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import cv2
import numpy as np
from typing import List
import io
import warnings
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time

# Suppress warnings and configure logging
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('absl').setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

class GeminiVisionAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the Gemini Vision Analyzer with your API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.webpage_url = "http://localhost:7860"

    def send_objects_and_capture(self, objects_list: List[str]) -> np.ndarray:
        """
        Sends a list of objects to the webpage and captures the resulting image.
        
        Args:
            objects_list (List[str]): List of detected objects
        
        Returns:
            np.ndarray: Screenshot as an OpenCV image, or None if failed
        """
        driver = None
        try:
            # Configure Firefox options
            firefox_options = Options()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            
            # Initialize Firefox driver with explicit geckodriver path
            service = Service(executable_path='/usr/local/bin/geckodriver')
            driver = webdriver.Firefox(service=service, options=firefox_options)
            
            # Navigate to the page
            print("Accessing webpage...")
            driver.get(self.webpage_url)
            
            # Wait for the page to load
            time.sleep(2)
            
            # Find the text input field and send the objects list
            text_input = driver.find_element(By.TAG_NAME, "textarea")
            formatted_text = "\n".join(objects_list)
            text_input.clear()
            text_input.send_keys(formatted_text)
            
            # Wait for the image to update
            time.sleep(2)
            
            # Take a screenshot
            print("Capturing screenshot...")
            screenshot = driver.get_screenshot_as_png()
            
            # Convert screenshot to OpenCV format
            nparr = np.frombuffer(screenshot, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return img
            
        except Exception as e:
            print(f"Error in send_objects_and_capture: {str(e)}")
            return None
            
        finally:
            if driver:
                driver.quit()

    def capture_and_analyze(self, interval: float = 5.0) -> List[str]:
        """
        Capture images from webcam at regular intervals and analyze them for objects.
        
        Args:
            interval (float): Time between captures in seconds (default: 5.0)
        
        Returns:
            List of detected objects in the image
        """
        cap = None
        try:
            # Initialize webcam with specific properties for Mac
            cap = cv2.VideoCapture(0)
            
            # Set camera properties for Continuity Camera
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            if not cap.isOpened():
                raise Exception("Could not open webcam")

            print(f"Capturing images every {interval} seconds. Press Ctrl+C to stop...")
            
            last_capture_time = 0
            while True:
                # Read frame from webcam
                ret, frame = cap.read()
                if not ret:
                    raise Exception("Could not read frame")

                current_time = time.time()
                if current_time - last_capture_time >= interval:
                    print("Capturing and analyzing image...")
                    # Convert frame to PIL Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Create the prompt for object detection
                    prompt = """Please analyze this image and provide a list of all visible objects.
                               Return only the objects, one per line, without any additional text or numbers.
                               Be specific but concise."""
                    
                    # Generate response from Gemini
                    response = self.model.generate_content([prompt, pil_image])
                    
                    # Process the response into a list and remove duplicates while preserving order
                    seen = set()
                    objects = []
                    for obj in response.text.split('\n'):
                        obj = obj.strip()
                        if obj and obj not in seen:
                            seen.add(obj)
                            objects.append(obj)
                    
                    # After getting the objects list, send to webpage and capture
                    if objects:  # Only if objects were detected
                        screenshot = self.send_objects_and_capture(objects) # use the web tool to get bounding boxes
        
                        if screenshot is not None:
                            # Save or display the screenshot as needed
                            cv2.imwrite("output.png", screenshot)
                    
                    print(f"Detected objects: {objects}")
                    last_capture_time = current_time
            
        except KeyboardInterrupt:
            print("\nStopping capture...")
            return []
        except Exception as e:
            print(f"Error capturing/analyzing image: {str(e)}")
            return []
        finally:
            # Ensure webcam is released
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()

def main():
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set the GEMINI_API_KEY environment variable")
    
    analyzer = GeminiVisionAnalyzer(api_key)
    important_objects = analyzer.capture_and_analyze()
    print(important_objects)
    return important_objects

if __name__ == "__main__":
    # Suppress GRPC warning
    import os
    os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
    
    detected_objects = main()
    if detected_objects:
        print(detected_objects)