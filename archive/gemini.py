import time
import base64
import requests
import cv2
import numpy as np
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === Gemini Flash 1.5 API Configuration (replace with your actual values) ===
API_ENDPOINT = "https://api.geminiflash.com/v1/flash1.5/detect"
API_KEY = os.getenv("GEMINI_API_KEY")

# === The webpage that contains your <video> element ===
WEBPAGE_URL = "http://192.168.55.1:7860"

def call_gemini_flash(image):
    """
    Encodes the image as JPEG, sends it to the Gemini Flash 1.5 API, and returns the JSON response.
    """
    ret, buffer = cv2.imencode('.jpg', image)
    if not ret:
        print("Failed to encode image.")
        return None

    img_base64 = base64.b64encode(buffer).decode('utf-8')
    payload = {
        "image": img_base64,
        "max_detections": 12  # Limit to up to 12 major objects
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error calling Gemini Flash API:", e)
        return None

def capture_video_frame(driver, video_css_selector="video"):
    """
    Executes JavaScript to draw the current frame of a <video> element to an off-screen <canvas>,
    then returns the image as an OpenCV (BGR) image array.

    video_css_selector: the CSS selector to find your <video> element.
    """
    # JavaScript snippet:
    # 1. Locate the <video> element
    # 2. Create an off-screen <canvas> the same size as the video
    # 3. Draw the video frame onto the canvas
    # 4. Return the canvas as a base64-encoded JPEG image
    js_script = f"""
        var video = document.querySelector('{video_css_selector}');
        if (!video) {{
            return null;
        }}
        var canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/jpeg');
    """
    data_url = driver.execute_script(js_script)
    if data_url is None:
        print("No video element found or couldn't capture frame.")
        return None

    # data_url should look like: "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
    # We strip off the "data:image/jpeg;base64," prefix and decode the remainder.
    header, encoded = data_url.split(',', 1)
    if not encoded:
        return None

    img_data = base64.b64decode(encoded)
    # Convert the raw bytes to a NumPy array and then to an OpenCV image
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame

def main():
    # === Setup Selenium / Chrome Options (headless optional) ===
    chrome_options = Options()
    # Uncomment if you want to run headless (no visible browser window):
    # chrome_options.add_argument("--headless")

    # Provide the path to your ChromeDriver if needed, e.g.:
    # service = ChromeService(executable_path="/usr/local/bin/chromedriver")
    service = ChromeService()

    # Create the WebDriver instance
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Increase the initial wait time
    time.sleep(10)  # Wait 10 seconds instead of 5

    # You can also add a retry mechanism
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            driver.get(WEBPAGE_URL)
            break
        except Exception as e:
            print(f"Connection attempt {retry_count + 1} failed: {e}")
            retry_count += 1
            time.sleep(5)

    try:
        while True:
            # Capture the current frame from the video element
            frame = capture_video_frame(driver, video_css_selector="video")
            if frame is None:
                print("Failed to capture frame from webpage. Exiting loop.")
                break

            # Send the frame to Gemini Flash 1.5 for detection
            result = call_gemini_flash(frame)
            if result is None:
                print("Skipping frame due to API error.")
                time.sleep(2)
                continue

            # Extract detection results
            detections = result.get("detections", [])
            summary = result.get("summary", "No summary available.")

            # Draw bounding boxes and labels
            for det in detections:
                box = det.get("box", [])
                score = det.get("score", 0)
                label = det.get("label", "")
                if len(box) == 4:
                    x_min, y_min, x_max, y_max = map(int, box)
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label}: {score:.2f}", (x_min, max(y_min - 10, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Overlay the summary on the frame
            cv2.putText(frame, summary, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2, cv2.LINE_AA)

            # Show the frame
            cv2.imshow("Scraped Video Frame with Gemini Flash", frame)

            # Exit when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Throttle the loop a bit (e.g., 2 FPS)
            time.sleep(0.5)

    finally:
        driver.quit()
        cv2.destroyAllWindows()

def send_objects_and_capture(objects_list, driver_path=None):
    """
    Sends a list of objects to the webpage and captures the resulting image.
    
    Args:
        objects_list (list): List of detected objects
        driver_path (str, optional): Path to ChromeDriver executable
    
    Returns:
        numpy.ndarray: Screenshot as an OpenCV image, or None if failed
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)  # Set a standard resolution
        
        # Navigate to the page
        print("Accessing webpage...")
        driver.get(WEBPAGE_URL)
        
        # Wait for the text input to be present
        time.sleep(2)  # Initial wait for page load
        
        # Find the text input field and send the objects list
        text_input = driver.find_element(By.TAG_NAME, "textarea")
        formatted_text = "\n".join(objects_list)  # Convert list to newline-separated string
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
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
