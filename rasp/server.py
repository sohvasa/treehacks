import RPi.GPIO as GPIO
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging  # Add this import

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the Motor class
class Motor:
    def __init__(self, in1, in2, en):
        logger.debug(f"Initializing motor with pins: in1={in1}, in2={in2}, en={en}")
        self.in1 = in1
        self.in2 = in2
        self.en = en
        try:
            GPIO.setup(self.in1, GPIO.OUT)
            GPIO.setup(self.in2, GPIO.OUT)
            GPIO.setup(self.en, GPIO.OUT)
            logger.debug(f"GPIO setup successful for pins: {in1}, {in2}, {en}")
            self.pwm = GPIO.PWM(self.en, 1000)
            self.pwm.start(0)
            logger.debug("PWM initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up motor: {str(e)}")
            raise

    def set_speed(self, speed, forward=True):
        try:
            logger.debug(f"Setting speed to {speed}, forward={forward}")
            GPIO.output(self.in1, GPIO.HIGH if forward else GPIO.LOW)
            GPIO.output(self.in2, GPIO.LOW if forward else GPIO.HIGH)
            self.pwm.ChangeDutyCycle(abs(speed))
            logger.debug("Speed set successfully")
        except Exception as e:
            logger.error(f"Error setting speed: {str(e)}")
            raise

    def stop(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)  # Stop the motor

# Initialize GPIO
try:
    logger.debug("Initializing GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    logger.debug("GPIO initialized successfully")
except Exception as e:
    logger.error(f"Error initializing GPIO: {str(e)}")
    raise

# Define motors with BCM GPIO pin numbers
try:
    logger.info("Creating motor instances...")
    front_left_motor = Motor(27, 17, 22)
    front_right_motor = Motor(10, 9, 11)
    rear_left_motor = Motor(5, 6, 13)
    rear_right_motor = Motor(26, 19, 21)
    logger.info("All motors initialized successfully")
except Exception as e:
    logger.error(f"Error creating motors: {str(e)}")
    raise

def move_forward(speed):
    front_left_motor.set_speed(speed, True)
    front_right_motor.set_speed(speed, True)
    rear_left_motor.set_speed(speed, True)
    rear_right_motor.set_speed(speed, True)
    print(f"Moving forward at speed: {speed}")
                                   
def move_backward(speed):
    front_left_motor.set_speed(speed, False)
    front_right_motor.set_speed(speed, False)
    rear_left_motor.set_speed(speed, False)
    rear_right_motor.set_speed(speed, False)
    print(f"Moving backward at speed: {speed}")

def turn_right(speed):
    front_left_motor.set_speed(speed, False)
    front_right_motor.set_speed(speed, True)
    rear_left_motor.set_speed(speed, False)
    rear_right_motor.set_speed(speed, True)
    print(f"Turning right at speed: {speed}")

def turn_left(speed):
    front_left_motor.set_speed(speed, True)
    front_right_motor.set_speed(speed, False)
    rear_left_motor.set_speed(speed, True)
    rear_right_motor.set_speed(speed, False)
    print(f"Turning left at speed: {speed}")

def stop_all_motors():
    front_left_motor.stop()
    front_right_motor.stop()
    rear_left_motor.stop()
    rear_right_motor.stop()
    print("All motors stopped.")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route('/move', methods=['POST'])
def handle_move():
    logger.info('Received POST request to /move')
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        
        if not data or 'speed' not in data or 'direction' not in data:
            logger.error("Missing speed or direction in request")
            return jsonify({'error': 'Missing speed or direction'}), 400
        
        speed = int(data['speed'])
        direction = data['direction'].lower()
        logger.debug(f"Processing movement: direction={direction}, speed={speed}")

        if not (0 <= speed <= 100):
            return jsonify({'error': 'Speed must be between 0 and 100'}), 400

        if direction == "center" or speed <= 10:
            stop_all_motors()
        elif direction == "forward":
            move_backward(speed) # the directions are reversed
        elif direction == "backward":
            move_forward(speed)
        elif direction == "left":
            turn_left(speed)
        elif direction == "right":
            turn_right(speed)
        else:
            return jsonify({'error': 'Invalid direction'}), 400

        return jsonify({'status': 'success', 'message': f'Moving {direction} at speed {speed}'})

    except Exception as e:
        logger.error(f"Error in handle_move: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def handle_stop():
    try:
        stop_all_motors()
        return jsonify({'status': 'success', 'message': 'All motors stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def cleanup():
    stop_all_motors()
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        # Register cleanup handler
        import atexit
        atexit.register(cleanup)
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        cleanup()