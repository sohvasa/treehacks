import RPi.GPIO as GPIO
import time
from flask import Flask, jsonify, request
import subprocess
import os

# Define the Motor class
class Motor:
    def __init__(self, in1, in2, en):
        self.in1 = in1
        self.in2 = in2
        self.en = en
        GPIO.setup(self.in1, GPIO.OUT)
        GPIO.setup(self.in2, GPIO.OUT)
        GPIO.setup(self.en, GPIO.OUT)
        self.pwm = GPIO.PWM(self.en, 1000)  # Set PWM frequency to 1kHz
        self.pwm.start(0)  # Initialize PWM with 0% duty cycle

    def set_speed(self, speed, forward=True):
        GPIO.output(self.in1, GPIO.HIGH if forward else GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW if forward else GPIO.HIGH)
        self.pwm.ChangeDutyCycle(abs(speed))  # Set PWM duty cycle

    def stop(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)  # Stop the motor

# Initialize GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setwarnings(False)

# Define motors with BCM GPIO pin numbers
front_left_motor = Motor(27, 17, 22)   # GPIO17, GPIO27, GPIO22
front_right_motor = Motor(10, 9, 11)   # GPIO10, GPIO9, GPIO11
rear_left_motor = Motor(5, 6, 13)      # GPIO5, GPIO6, GPIO13
rear_right_motor = Motor(26, 19, 21)   # GPIO19, GPIO26, GPIO21

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

def turn_left(speed):
    front_left_motor.set_speed(speed, False)
    front_right_motor.set_speed(speed, True)
    rear_left_motor.set_speed(speed, False)
    rear_right_motor.set_speed(speed, True)
    print(f"Turning left at speed: {speed}")

def turn_right(speed):
    front_left_motor.set_speed(speed, True)
    front_right_motor.set_speed(speed, False)
    rear_left_motor.set_speed(speed, True)
    rear_right_motor.set_speed(speed, False)
    print(f"Turning right at speed: {speed}")

def stop_all_motors():
    front_left_motor.stop()
    front_right_motor.stop()
    rear_left_motor.stop()
    rear_right_motor.stop()
    print("All motors stopped.")

# Initialize Flask app
app = Flask(__name__)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COMMAND_SCRIPT = os.path.join(SCRIPT_DIR, 'send_command.sh')

# Make sure the script is executable
subprocess.run(['chmod', '+x', COMMAND_SCRIPT])

def send_move_command(direction, speed):
    try:
        result = subprocess.run(
            [COMMAND_SCRIPT, direction, str(speed)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error sending command: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception sending command: {e}")
        return False

@app.route('/move', methods=['POST'])
def handle_move():
    try:
        data = request.get_json()
        if not data or 'speed' not in data or 'direction' not in data:
            return jsonify({'error': 'Missing speed or direction'}), 400
        
        direction = data['direction'].lower()
        speed = int(data['speed'])

        if not (0 <= speed <= 100):
            return jsonify({'error': 'Speed must be between 0 and 100'}), 400

        success = send_move_command(direction, speed)
        if not success:
            return jsonify({'error': 'Failed to send movement command'}), 500

        return jsonify({
            'status': 'success',
            'message': f'Moving {direction} at speed {speed}'
        })

    except Exception as e:
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