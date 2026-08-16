import RPi.GPIO as GPIO
import time
LED_PIN = [15,22]
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN[0], GPIO.OUT)
GPIO.setup(LED_PIN[1], GPIO.OUT)

def Rled():
    for i in range(0,3):
        GPIO.output(LED_PIN[0], GPIO.LOW)
        GPIO.output(LED_PIN[1], GPIO.HIGH)
        time.sleep(1)

def Lled():
    for i in range(0,3):
        GPIO.output(LED_PIN[1], GPIO.LOW)
        GPIO.output(LED_PIN[0], GPIO.HIGH)
        time.sleep(1)

def ledstop():
    GPIO.output(LED_PIN[1], GPIO.LOW)
    GPIO.output(LED_PIN[0], GPIO.LOW)
    time.sleep(0.2)
