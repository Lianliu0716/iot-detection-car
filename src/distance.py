import time
import RPi.GPIO as GPIO

trigger_pin = 23
echo_pin = 24

GPIO.setmode(GPIO.BOARD)
GPIO.setup(trigger_pin,GPIO.OUT)
GPIO.setup(echo_pin,GPIO.IN)

'''
TRIG 負責發射超聲波，Echo 負責接收超聲波

'''
def send_trigger_pulse():
    #傳送超聲波，一直髮
    GPIO.output(trigger_pin,1)
    # 為了防止錯誤，因為緊接著就需要把發射端置為高電平
    time.sleep(0.0001)
    #發射端置為高電平
    GPIO.output(trigger_pin,0)

'''
ECHO 負責接收超聲波
'''
def wait_for_echo(value,timeout):
    count = timeout
    #通過該程式碼持續獲取ECHO的狀態
    while GPIO.input(echo_pin)!= value and count>0:
        count = count-1

'''
計算距離
'''
def get_distance():
    # 發射
    send_trigger_pulse()
    # 接收高電平 1/True
    wait_for_echo(True,10000)
    # 等待
    start = time.time()
    #接收低電平
    wait_for_echo(False,10000)
    finish = time.time()
    pulse_len = finish-start
    distance_cm = pulse_len/0.000058
    return distance_cm
'''
while True:
    print("cm = %f"%get_distance())
   #dis=get_distance()
   #if dis<=30:

    time.sleep(1)'''