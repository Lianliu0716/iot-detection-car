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
import distance as distance

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

def init(num,flag,tflag,temp2):
    num=[0,0]
    flag=True
    tflag=True
    temp2=[0,0]

def record(temp2,cx):
    temp2[0]=temp2[1]
    temp2[1]=cx


def main():
    labels = load_labels('labels.txt')
    labels2 = load_labels('labels2.txt')
    interpreter = Interpreter('detect.tflite')
    interpreter2 = Interpreter('detect2.tflite')
    interpreter.allocate_tensors()
    interpreter2.allocate_tensors()
    _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']
    _, input_height, input_width, _ = interpreter2.get_input_details()[0]['shape']
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    temp="L"#上次微調紀錄
    temp2=[0,0]
    num=[0,0]
    flag=True
    tflag=True
    while cap.isOpened():
        ret, frame = cap.read()
        img = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (320,320))
        res = detect_objects(interpreter, img, 0.8)
        res2 = detect_objects(interpreter2, img, 0.8)
            
        if len(res) == 0:#not detecting
          if len(res2) != 0: motor.turnRight(0.1,35)  
          else:
            if temp=="R": motor.turnLeft(0.1,35)
            elif temp=="L": motor.turnRight(0.1,35)
            else: 
                motor.backward(0.1,55)
                if temp2[1]-temp2[0]>=0: motor.turnRight(0.1,50) 
                elif temp2[1]-temp2[0]<0: motor.turnLeft(0.1,50)
            

        for r in res2:#left right
          if flag==True:
            ymin, xmin, ymax, xmax = r['bounding_box']
            cv2.rectangle(frame,(int(max(1,xmin * CAMERA_WIDTH)), int(max(1, ymin * CAMERA_HEIGHT))),(int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH)), int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))),(255,0,0),3)
            cv2.putText(frame,labels2[int(r['class_id'])],(int(xmin), int(min(ymax, CAMERA_HEIGHT-20))), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA) 
            if r['class_id']==0:num[0]+=1
            elif r['class_id']==1:num[1]+=1
            if abs(num[0]-num[1])>5:
              flag=False

        for result in res:#forward stop
            ymin, xmin, ymax, xmax = result['bounding_box']
            
            if result['score'] > 0.5:##detect
              if tflag==True:
                start = time.time()
                tflag=False

              cx = (xmin + xmax) / 2
              cy = (ymin + ymax) / 2
              cv2.rectangle(frame,(int(max(1,xmin * CAMERA_WIDTH)), int(max(1, ymin * CAMERA_HEIGHT))),(int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH)), int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))),(0,255,0),3)
              #frame=cv2.circle(frame, (int(cx*CAMERA_WIDTH),int(cy*CAMERA_HEIGHT)), radius=5, color=(0,0,255), thickness=-1)
              cv2.putText(frame,labels[int(result['class_id'])],(int(xmin), int(min(ymax, CAMERA_HEIGHT-20))), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA) 

              #矯正
              time.sleep(1)
              if cx < 0.25: 
                motor.turnLeft(0.1,50)
                temp="L"
                cango=False
              elif cx > 0.75:
                motor.turnRight(0.1,50)
                temp="R"
                cango=False
              else:
                cango=True
              
              #轉彎
              if cango==True:
                dis = distance.get_distance()
                if result['class_id']==0:#FORWARD
                  if dis<35 and 32<dis:#ymin<0.13
                    if num[0]>num[1]:
                      detect_id=1 #紀錄
                      motor.turnleft_90()
                    else:
                      detect_id=2 #紀錄
                      motor.turnright_90()
                    end = time.time()
                    print(end-start)
                    init(num,flag,tflag,temp2)
                    #
                  else: #往前或往後
                    if ymin<-0.05 or dis<32:
                        motor.backward(0.1,45)
                    if dis>45 :
                        motor.forward(0.2,85)
                    else:
                        motor.forward(0.1,55)

                elif result['class_id']==1:#STOP
                  temp=""
                  record(temp2,cx)
                  if dis<15 and dis>12 or ymin<0.12:#0.09 
                    #motor.turnback_180()
                    end = time.time()
                    print("GET THE END")
                    print(end-start)
                    init(num,flag,tflag,temp2)
                    return#
                    #runback() #跑回原點
                  else: #往前或往後 讓ymin=0.25~0.35 ymax=0.65~0.75
                    if ymin<0 or dis<12:
                        motor.backward(0.1,45)
                    if dis>20:
                        motor.forward(0.2,85)
                    else: motor.forward(0.1,55)

        cv2.imshow('Pi Feed', frame)
        if cv2.waitKey(10) & 0xFF ==ord('q'):
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    
#0.17400467, 0.38056988, 0.72134906, 0.549706
#0.63126916, 0.54723966, 0.86433405, 0.62833524

#[{'bounding_box': array([-0.00337499,  0.7402246 ,  0.6409261 ,  0.96179473], dtype=float32), 'class_id': 0.0, 'score': 0.9919177}]
"""
if result['class_id']==0:#FORWARD
                  if ymax-ymin>=0.5:#ymin<0.13
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
                    init(num,flag,tflag,temp2)
                    #
                  else: #往前或往後
                    if ymin<-0.05 :
                        motor.backward(0.1,45)
                    if ymin>0.15:
                        motor.forward(0.2,85)
                    else:
                        motor.forward(0.1,35)

                if result['class_id']==1:#STOP
                  temp=""
                  record(temp2,cx)
                  if ymin<0.12:#0.09
                    #motor.turnback_180()
                    end = time.time()
                    print("GET THE END")
                    print(end-start)
                    init(num,flag,tflag,temp2)
                    return#
                    #runback() #跑回原點
                  else: #往前或往後 讓ymin=0.25~0.35 ymax=0.65~0.75
                    if ymin<0 :
                        motor.backward(0.1,45)
                    if ymin>0.16 :
                        motor.forward(0.2,85)
                    else: motor.forward(0.1,45)
"""