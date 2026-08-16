# Based on https://github.com/tensorflow/examples/blob/master/lite/examples/object_detection/raspberry_pi/README.md
import re
import time
import datetime
import cv2
from tflite_runtime.interpreter import Interpreter
import numpy as np
import pwm_motor as motor #car pwm to move
import sqlite3

conn = sqlite3.connect("myDB.db") 
cursor = conn.cursor()

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
num_in_sql=start_num=1
cursor.execute("select id from user")
records = cursor.fetchone()
if records!=None: num_in_sql=start_num=records #繼上次儲存過後最後一個id

def load_labels(path='labels.txt'):
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

def savetosql(start,end,detect_id,do):
  t0 = end-start
  t1 = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#ex. >>> 2022-07-21 14:29:22
  print(do+t1+" 儲存進SQL: 耗時"+t0+"秒")
  sql = "INSERT INTO customers (id, nowtime, seconds, detectid) VALUES (%d, %s,%.10f,%d)"
  val = (num_in_sql, t1, t0, detect_id)
  cursor.execute(sql, val)
  num_in_sql+=1
  conn.commit()

def timecoculate(time):
  hour = time // 3600
  minute = (time - hour *3600) //60
  second = time - hour *3600 - minute * 60
  str=hour+'時'+minute+'分'+second+'秒'
  return str

#left:1 right:2 forward:3 stop:4
#left:0 right:1 forward:2 stop:3
def main():
    labels = load_labels()
    interpreter = Interpreter('detect.tflite')
    interpreter.allocate_tensors()
    _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']

    cap = cv2.VideoCapture(0)
    detect_id=0

    while cap.isOpened():
        ret, frame = cap.read()
        img = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (320,320))
        res = detect_objects(interpreter, img, 0.8)
        print(res)

        num=[3]
        flag=True
        tflag=True
        for result in res:
            ymin, xmin, ymax, xmax = result['bounding_box']
            xmin = int(max(1,xmin * CAMERA_WIDTH))
            xmax = int(min(CAMERA_WIDTH, xmax * CAMERA_WIDTH))
            ymin = int(max(1, ymin * CAMERA_HEIGHT))
            ymax = int(min(CAMERA_HEIGHT, ymax * CAMERA_HEIGHT))
            
            cv2.rectangle(frame,(xmin, ymin),(xmax, ymax),(0,255,0),3)
            cv2.putText(frame,labels[int(result['class_id'])],(xmin, min(ymax, CAMERA_HEIGHT-20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),2,cv2.LINE_AA) 
            
            if result['score'] > 0.5:#detect
              if(tflag):
                start = time.time()
                tflag=False

              if result['class_id'] !=3 and flag==True:#detect left&right #90度要轉左或右 紀錄 如差3就確認是哪邊
                num[result['class_id']]+=1
                if abs(num[1]-num[2])>3:
                  flag=False
              else: #detect forward&stop
                cx = (xmin + xmax) / 2
                cy = (ymin + ymax) / 2
                frame = cv2.circle(frame, (int(cx*CAMERA_WIDTH),int(cy*CAMERA_HEIGHT)), radius=5, color=(0,0,255), thickness=-1)
                
                #矯正
                if cx < 0.35: 
                    motor.turnLeft()
                elif cx > 0.65:
                    motor.turnRight()
                
                #轉彎
                if result['class_id']==2:
                  if 0.25<ymin and ymin<0.35 and 0.65<ymax and ymax<0.75:
                    if num[1]>num[2]:
                      detect_id=1#紀錄
                      motor.turnleft_90()
                    else:
                      detect_id=2 #紀錄
                      motor.turnright_90()
                    end = time.time()
                    tflag=True
                    savetosql(start,end,detect_id,do="轉彎")#存
                  else: #往前或往後 讓ymin=0.25~0.35 ymax=0.65~0.75
                    if ymin<0.25 and ymax>0.75:
                        motor.backward(0.1,70)
                        time.sleep(0.1)
                    elif ymin>0.35 and ymax<0.65:
                        motor.forward(0.1,70)
                        time.sleep(0.1)
                else:                
                  if 0.25<ymin and ymin<0.35 and 0.65<ymax and ymax<0.75:
                    motor.turnback_180()
                    end = time.time()
                    tflag=True
                    savetosql(start,end,detect_id,do="終點")#存
                    #runback() #跑回原點
                  else: #往前或往後 讓ymin=0.25~0.35 ymax=0.65~0.75
                    if ymin<0.25 and ymax>0.75:
                        motor.backward(0.1,70)
                        time.sleep(0.1)
                    elif ymin>0.35 and ymax<0.65:
                        motor.forward(0.1,70)
                        time.sleep(0.1)

        cv2.imshow('Pi Feed', frame)

        if cv2.waitKey(10) & 0xFF ==ord('q'):
            cap.release()
            cursor.close()
            cv2.destroyAllWindows()

def runback():
  record = cursor.execute('SELECT id,seconds,detectid FROM car')
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