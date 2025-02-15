import RPi.GPIO as GPIO
import time

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

def main():
    try:
        print("Tank drive initialized. Enter commands:")
        print("MOVE <speed> <direction> - e.g., MOVE 50 forward")
        print("STOP - to stop all motors")

        while True:
            command = input("> ").strip()

            if command.startswith("MOVE"):
                parts = command.split()
                if len(parts) == 3:
                    try:
                        speed = int(parts[1])
                        direction = parts[2].lower()

                        if direction == "forward":
                            move_forward(speed)
                        elif direction == "backward":
                            move_backward(speed)
                        elif direction == "left":
                            turn_right(speed)
                        elif direction == "right":
                            turn_left(speed)
                        else:
                            print("Invalid direction. Use 'forward', 'backward', 'left', or 'right'.")
                    except ValueError:
                        print("Invalid speed. Enter a number between 0 and 100.")
                else:
                    print("Invalid command format. Use 'MOVE <speed> <direction>'.")
            elif command == "STOP":
                stop_all_motors()
            else:
                print("Invalid command. Use 'MOVE <speed> <direction>' or 'STOP'.")

    except KeyboardInterrupt:
        print("\nStopping all motors and cleaning up.")
        stop_all_motors()
        GPIO.cleanup()

if __name__ == "__main__":
    main()