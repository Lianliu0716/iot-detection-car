#pcar
import RPi.GPIO as GPIO
import time
import readchar


Motor_R1_Pin = 16
Motor_R2_Pin = 18
Motor_L1_Pin = 11#11
Motor_L2_Pin = 13#13
#t = 0.1
#dc = 50


GPIO.setmode(GPIO.BOARD)
GPIO.setup(Motor_R1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_R2_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L2_Pin, GPIO.OUT, initial=GPIO.LOW)

pwm_r1 = GPIO.PWM(Motor_R1_Pin, 500)
pwm_r2 = GPIO.PWM(Motor_R2_Pin, 500)
pwm_l1 = GPIO.PWM(Motor_L1_Pin, 500)
pwm_l2 = GPIO.PWM(Motor_L2_Pin, 500)
pwm_r1.start(0)
pwm_r2.start(0)
pwm_l1.start(0)
pwm_l2.start(0)

def turnback_180():
    turnleft_90()
    turnleft_90()

def turnleft_90(t,dc):#左轉90度
    pwm_r1.ChangeDutyCycle(dc+10)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def turnright_90(t,dc):#右轉90度
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def stop():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)

def forward(t,dc):
    pwm_r1.ChangeDutyCycle(dc)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def backward(t,dc):
    pwm_r1.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(dc)
    time.sleep(t)
    stop()

def turnLeft(t,dc):
    pwm_r1.ChangeDutyCycle(dc)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def turnRight(t,dc):
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()


def cleanup():
    stop()
    pwm_r1.stop()
    pwm_r2.stop()
    pwm_l1.stop()
    pwm_l2.stop()
    GPIO.cleanup()

'''if __name__ == "__main__":

    print("Press 'q' to quit...")

    while True:
        ch = readchar.readkey()

        if ch == 'w':
            forward(0.2,60)

        elif ch == 's':
            backward(0.2,60)

        elif ch == 'd':
            turnRight(0.2,60)

        elif ch == 'a':
            turnLeft(0.2,60)

        elif ch=='r':
             forward(0.2,60)
             forward(0.2,60)

        elif ch == 'q':
            print("\nQuit")
            cleanup()
            quit()'''
           