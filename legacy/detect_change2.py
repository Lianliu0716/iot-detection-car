# Based on https://github.com/tensorflow/examples/blob/master/lite/examples/object_detection/raspberry_pi/README.md
import re
import time
import datetime
import cv2
from tflite_runtime.interpreter import Interpreter
import numpy as np
import pcar as motor #car pwm to move
import sqlite3
import led as led
import os

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

def load_labels(path):#='labels.txt'
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels

def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = np.expand_dims((image-255)/255, axis=0)


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor


def detect_objects(interpreter, image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()
  # Get all output details
  boxes = get_output_tensor(interpreter, 1)
  classes = get_output_tensor(interpreter, 3)
  scores = get_output_tensor(interpreter, 0)
  count = int(get_output_tensor(interpreter, 2))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
          'bounding_box': boxes[i],
          'class_id': classes[i],
          'score': scores[i]
      }
      results.append(result)
  return results

def init(num,flag,tflag):
    num=[2]
    flag=True
    tflag=True

def main():
    labels = load_labels('labels.txt')
    interpreter = Interpreter('detect.tflite')
    interpreter.allocate_tensors()
    _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    temp="L"#上次微調紀錄
    num=[2]
    flag=True
    tflag=True
    while cap.isOpened():
        ret, frame = cap.read()
        img = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (320,320))
        res = detect_objects(interpreter, img, 0.8)
        print(res)
        
        if res=="[]":#not detecting
          if temp=="L": motor.turnRight(0.1,53)
          elif temp=="R": motor.turnLeft(0.1,53)
          elif temp=="N": motor.turnRight(0.1,53)
          time.sleep(0.1)
        
        for result in res:
            ymin, xmin, ymax, xmax = result['bounding_box']
            
            if result['score'] > 0.5:##detect
              if tflag==True:
                start = time.time()
                tflag=False
            
              cx = (xmin + xmax) / 2
              cy = (ymin + ymax) / 2
            
              if result['class_id']==2 or result['class_id']==3 :#框
                cv2.rectangle(frame,(int(max(1,xmin * CAMERA_WIDTH)), int(max(1, ymin * CAMERA_HEIGHT))),(int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH)), int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))),(0,255,0),3)
                frame=cv2.circle(frame, (int(cx*CAMERA_WIDTH),int(cy*CAMERA_HEIGHT)), radius=5, color=(0,0,255), thickness=-1)
              else: 
                cv2.rectangle(frame,(int(max(1,xmin * CAMERA_WIDTH)), int(max(1, ymin * CAMERA_HEIGHT))),(int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH)), int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))),(255,0,0),3)
              cv2.putText(frame,labels[int(result['class_id'])],(int(xmin), int(min(ymax, CAMERA_HEIGHT-20))), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA) 
            
              if result['class_id']==0 or result['class_id']==1 and flag==True:#detect LorR
                num[int(result['class_id'])]+=1
                if abs(num[0]-num[1])>5:
                  flag=False

              #矯正
              if cx < 0.40: 
                print("L")
                motor.turnLeft(0.1,53)
                time.sleep(0.1)
                temp="L"
                cango=False
              elif cx > 0.60:
                print("R")
                motor.turnRight(0.1,53)
                time.sleep(0.1)
                temp="R"
                cango=False
              else:
                cango=True
              
              #轉彎
              if cango==True:
                if result['class_id']==2:#FORWARD
                  if 0.13<ymin and ymin<0.18 and 0.68<ymax and ymax<0.74:
                    if num[0]>num[1]:
                      detect_id=1 #紀錄
                      #led.Lled()
                      #os.system('omxplayer -o local -p leftturn.mp3 > /dev/null 2>&1')
                      motor.turnleft_90()
                    else:
                      detect_id=2 #紀錄
                      #led.Rled()
                      #os.system('omxplayer -o local -p rightturn.mp3 > /dev/null 2>&1')
                      motor.turnright_90()
                    end = time.time()
                    print(end-start)
                    init(num,flag,tflag)
                    #
                  else: #往前或往後
                    if ymin<0.13 :
                        print("B")
                        motor.backward(0.1,75)
                        time.sleep(0.1)
                    elif ymin>0.18 :
                        print("F")
                        motor.forward(0.1,73)
                        time.sleep(0.1)

                if result['class_id']==3:#STOP
                  if ymin<0.09:
                    #motor.turnback_180()
                    end = time.time()
                    print("GET THE END")
                    print(end-start)
                    init(num,flag,tflag)
                    return#
                    #runback() #跑回原點
                  else: #往前或往後 讓ymin=0.25~0.35 ymax=0.65~0.75
                    if ymin<0 :
                        print("B")
                        motor.backward(0.1,75)
                        time.sleep(0.1)
                    elif ymin>0.14 :
                        print("F")
                        motor.forward(0.1,80)
                        time.sleep(0.1)

        cv2.imshow('Pi Feed', frame)

        if cv2.waitKey(10) & 0xFF ==ord('q'):
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    
#0.17400467, 0.38056988, 0.72134906, 0.549706
#0.63126916, 0.54723966, 0.86433405, 0.62833524