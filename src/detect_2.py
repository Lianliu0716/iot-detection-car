from flask import Flask,render_template
import sqlite3
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

conn = sqlite3.connect("myDB.db") 
cursor = conn.cursor()

num_in_sql = 1
start_num=num_in_sql
cursor.execute('select id from IOT')    
Ans3= cursor.fetchall()
if Ans3!=[]:
    records=Ans3[len(Ans3)-1][0]
else:
    records=None

if records!=None: 
    num_in_sql=records+1
    start_num=records+1


def load_labels(path):
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

def init(num,temp2,temp):
    num[0]=0
    num[1]=0
    temp2[0]=0
    temp2[1]=0
    temp[0]=0
    temp[1]=0
    temp[2]=0

def record(temp2,cx):
    temp2[0]=temp2[1]
    temp2[1]=cx

def big(temp):
    value=temp[0]
    m=0
    for i in range(1,3):
        if value<temp[i]:
            m=i
            value=temp[i]
    return m

def savetosql(start,end,detect_id):
  global num_in_sql
  t0 = end-start
  t1 = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  sql = "INSERT INTO IOT (id, nowtime, seconds, detectid) VALUES (?,?,?,?)"
  val = (num_in_sql, t1, t0,detect_id)
  cursor.execute(sql, val)
  num_in_sql=num_in_sql+1
  conn.commit()

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
    cap.set(cv2.CAP_PROP_FPS, 50)
    
    temp=[0,0,0]#上次微調紀錄
    temp2=[0,0]
    temp1=0
    num=[0,0]
    flag=True
    tflag=True
    er=4
    while cap.isOpened():

        ret, frame = cap.read()
        img = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (320,320))
        res = detect_objects(interpreter, img, 0.8)
        res2 = detect_objects(interpreter2, img, 0.8)
        er-=1
        if len(res) == 0:#not detecting
          if len(res2) != 0: motor.turnRight(0.1,50)  
          else:
            if big(temp)==1: 
                motor.turnLeft(0.1,50)
                time.sleep(0.1)
            elif big(temp)==0 : 
                motor.turnRight(0.1,50)
                time.sleep(0.1)
            elif big(temp)==2: 
                motor.backward(0.14,55)
                time.sleep(0.1)
                for i in range(0,3):
                    ret, frame = cap.read()
                if temp2[1]-temp2[0]>=0: 
                    motor.turnRight(0.1,55) 
                elif temp2[1]-temp2[0]<0: 
                    motor.turnLeft(0.14,55)
                time.sleep(0.1)
            

        for r in res2:#left right
          if flag==True:
            ymin, xmin, ymax, xmax = r['bounding_box']
            cv2.rectangle(frame,(int(max(1,xmin * CAMERA_WIDTH)), int(max(1, ymin * CAMERA_HEIGHT))),(int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH)), int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))),(255,0,0),3)
            cv2.putText(frame,labels2[int(r['class_id'])],(int(xmin), int(min(ymax, CAMERA_HEIGHT-20))), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA) 
            if r['class_id']==0:num[0]+=1
            elif r['class_id']==1:num[1]+=1
            if abs(num[0]-num[1])>0:
              flag=False

        for result in res:#forward stop
            ymin, xmin, ymax, xmax = result['bounding_box']
            
            if result['score'] > 0.5:
              if tflag==True:
                start = time.time()
                tflag=False

              cx = (xmin + xmax) / 2
              cy = (ymin + ymax) / 2
              cv2.rectangle(frame,(int(max(1,xmin * CAMERA_WIDTH)), int(max(1, ymin * CAMERA_HEIGHT))),(int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH)), int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))),(0,255,0),3)
              frame=cv2.circle(frame, (int(cx*CAMERA_WIDTH),int(cy*CAMERA_HEIGHT)), radius=5, color=(0,0,255), thickness=-1)
              cv2.putText(frame,labels[int(result['class_id'])],(int(xmin), int(min(ymax, CAMERA_HEIGHT-20))), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA) 

              #矯正
              temp1=cx
              if cx < 0.3: 
                motor.turnLeft(0.1,57)
                temp[0]+=1
                cango=False
              elif cx > 0.7:
                motor.turnRight(0.1,57)
                temp[1]+=1
                cango=False
              else:
                cango=True
              
              #轉彎
              if cango==True:
                dis = distance.get_distance()
                temp[2]+=1
                record(temp2,cx)
                if result['class_id']==0:#FORWARD
                  if dis<28 and 20<dis:#ymin<0.13
                    if num[0]>num[1]:
                      detect_id=0 #紀錄
                      led.Lled()
                      led.ledstop()
                      os.system('omxplayer -o local -p leftturn.mp3 > /dev/null 2>&1')
                      motor.turnleft_90(0.75,90)
                    else:
                      detect_id=1 #紀錄
                      led.Rled()
                      led.ledstop()
                      os.system('omxplayer -o local -p rightturn.mp3 > /dev/null 2>&1')
                      motor.turnright_90(0.75,75)
                    
                    end = time.time()
                    if er<=0:savetosql(start,end,detect_id)#存
                    er=4
                    time.sleep(3)
                    for i in range(0,5):
                        ret, frame = cap.read()
                    init(num,temp2,temp)
                    flag=tflag=True
                    
                  else: #往前或往後
                    if ymin<-0.05 or dis<20:
                        motor.backward(0.1,55)
                    if dis>34 :
                        motor.forward(0.2,85)
                        for i in range(0,3):
                            ret, frame = cap.read()
                    else:
                        motor.forward(0.1,60)
                    

                elif result['class_id']==1:#STOP
                  if dis<15 and dis>12 or ymin<0.12:#0.09 
                    end = time.time()
                    os.system('omxplayer -o local -p end.mp3 > /dev/null 2>&1')
                    detect_id=2
                    if er<0:savetosql(start,end,detect_id)#存
                    er=4
                    init(num,temp2,temp)
                    flag=tflag=True
                    #runback() 
                    return
                  else: #往前或往後 
                    if ymin<0 or dis<12:
                        motor.backward(0.1,45)
                    if dis>20:
                        motor.forward(0.2,85)
                        for i in range(0,3):
                            ret, frame = cap.read()
                    else: motor.forward(0.1,65)

        cv2.imshow('Pi Feed', frame)
        if cv2.waitKey(10) & 0xFF ==ord('q'):
            cap.release()
            cv2.destroyAllWindows()

def runback():
  record = cursor.execute('SELECT id,seconds,detectid FROM IOT')
  motor.forword(record[num_in_sql][2],70)
  k=num_in_sql-1
  while k>=start_num:
    if record[k][2]==1:
      motor.turnleft_90()
    elif record[k][2]==2:
      motor.turnright_90()
    motor.forword(record[num_in_sql][2],70)
    k-=1

if __name__ == "__main__":
    main()
    


              