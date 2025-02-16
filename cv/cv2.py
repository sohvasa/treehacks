import requests
from PIL import Image
import torch
import cv2
import numpy as np
import time


from transformers import OwlViTProcessor, OwlViTForObjectDetection

processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")

# Initialize webcam
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if not ret:
    raise RuntimeError("Could not read from webcam")

# Convert BGR to RGB and then to PIL Image
rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
image = Image.fromarray(rgb_frame)

texts = [["a bottle", "a notebook"]]
inputs = processor(text=texts, images=image, return_tensors="pt")
outputs = model(**inputs)

# Get image dimensions
target_sizes = torch.Tensor([image.size[::-1]])
width = float(target_sizes[0][1])
height = float(target_sizes[0][0])

# Send move command to the robot
def send_move_command(direction, speed):
    print('sending move command')
    print(direction, speed)
    try:
        response = requests.post(
            'http://10.19.179.61:5000/move',
            headers={'Content-Type': 'application/json'},
            json={'direction': direction, 'speed': speed}
        )
        # Check if the request was successful (status code 2xx)
        response.raise_for_status()
    except requests.RequestException as error:
        print('Movement command error:', error)

# Process initial detection
results = processor.post_process_object_detection(outputs=outputs, target_sizes=target_sizes, threshold=0.1)
boxes, scores, labels = results[0]["boxes"], results[0]["scores"], results[0]["labels"]

# Main detection loop
for i in range(10):
    # Get a new frame and process it
    ret, frame = cap.read()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb_frame)
    
    # Run detection
    inputs = processor(text=texts, images=image, return_tensors="pt")
    outputs = model(**inputs)
    results = processor.post_process_object_detection(outputs=outputs, target_sizes=target_sizes, threshold=0.1)
    boxes, scores, labels = results[0]["boxes"], results[0]["scores"], results[0]["labels"]

    # Process each detection
    for box, score, label in zip(boxes, scores, labels):
        box = [round(i, 2) for i in box.tolist()]
        
        # Calculate center x coordinate and object width
        center_x = (box[2] + box[0]) / 2
        obj_width = box[2] - box[0]
        relative_width = obj_width / width  # Calculate relative width
        
        print(f"Detected {texts[0][label]} with confidence {round(score.item(), 3)}")
        print(f"Center X: {center_x:.2f}, Width: {obj_width:.2f}")
        print(f"Relative width: {relative_width:.2f}")
        print(f"Image dimensions - Width: {width:.2f}, Height: {height:.2f}")

        # First handle forward/stop based on object width
        if relative_width > 0.4:  # Object is too close
            print('STOP - Object too close')
            send_move_command("stop", 0)
        else:
            # Then handle left/right steering
            if center_x > 3*width/4:
                print("LEFT")
                send_move_command("right", 15)
                send_move_command("backward", 5)
            elif center_x < width/4:
                print('RIGHT')
                send_move_command("left", 15)
                send_move_command("backward", 5)
            elif center_x > width/2 + 0.06*width:
                print('left')
                send_move_command("right", 12)
                send_move_command("backward", 5)
            elif center_x < width/2 - 0.06*width:
                print('right')
                send_move_command("left", 12)
                send_move_command("backward", 5)
            else:
                print('forward')
                send_move_command("backward", 15)  
            
            time.sleep(1)
            send_move_command("stop", 0)
            # Move fseorward slowly when centered
    
    time.sleep(0.1)

# Release the webcam
cap.release()
