# Import packages
import os
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import tensorflow as tf
import argparse
import sys

# Set up camera constants
# IM_WIDTH = 1280
# IM_HEIGHT = 720
IM_WIDTH = 640    # Use smaller resolution for
IM_HEIGHT = 480   # slightly faster framerate #480

# Select camera type (if user enters --usbcam when calling this script,
# a USB webcam will be used)
camera_type = 'usb'
parser = argparse.ArgumentParser()
parser.add_argument('--usbcam', help='Use a USB webcam instead of picamera', action='store_true')
args = parser.parse_args()
if args.usbcam:
    camera_type = 'usb'

# This is needed since the working directory is the object_detection folder.
sys.path.append('..')###

# Import utilites
from utils import label_map_util
from utils import visualization_utils as vis_util

#MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09'#path
MODEL_NAME='savemodel_2'
CWD_PATH = os.getcwd()

# for object detection.
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,'saved_model.pb')###(path,dir,)
# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,'data','arrowhead_label_map.pbtxt')###(path,dir,)
# Number of classes the object detector can identify
NUM_CLASSES = 14###

## Load the label map.
# Label maps map indices to category names, so that when the convolution
# network predicts `5`, we know that this corresponds to `airplane`.
# Here we use internal utility functions, but anything that returns a
# dictionary mapping integers to appropriate string labels would be fine
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


# Load the Tensorflow model into memory.
detection_graph = tf.compat.v1.Graph()
"""
with detection_graph.as_default():
    od_graph_def = tf.compat.v1.GraphDef()
    with tf.io.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

    sess = tf.compat.v1.Session(graph=detection_graph)
""" 

from tensorflow.python.saved_model import tag_constants
with tf.Session() as sess:
	#根据tag_constants.SERVING标签找到对应的计算图
    meta_graph_def = tf.saved_model.loader.load(sess, [tag_constants.SERVING],'/home/pi/models/research/object_detection/savemodel_2')
    # 从meta_graph_def中取出SignatureDef对象
    signature = meta_graph_def.signature_def
    
    # signature find tensor name 
    #x = signature['my_signature'].inputs['input_x'].name
    #result = signature['my_signature'].outputs['output'].name
    #y = sess.run(result, feed_dict={x: 5})#
    #print(y)       

    # Define input and output tensors (i.e. data) for the object detection classifier
    # Input tensor is the image
    image_tensor = signature['serving_default'].inputs['input'].name

    # Output tensors are the detection boxes, scores, and classes
    # Each box represents a part of the image where a particular object was detected
    detection = signature['serving_default'].outputs['output'].name


    # Initialize frame rate calculation #frame rate 
    frame_rate_calc = 1
    freq = cv2.getTickFrequency()
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Initialize USB webcam feed
    camera = cv2.VideoCapture(0, cv2.CAP_V4L) #match camera 
    ret = camera.set(3,IM_WIDTH) # video width
    ret = camera.set(4,IM_HEIGHT) # video height

    while(True):

        t1 = cv2.getTickCount()

        # Acquire frame and expand frame dimensions to have shape: [1, None, None, 3]
        # i.e. a single-column array, where each item in the column has the pixel RGB value
        ret, frame = camera.read()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_expanded = np.expand_dims(frame_rgb, axis=0)
        frame_expanded = frame_expanded.reshape((1,3,480,640))
        """if len(frame_expanded.shape)<3 :
            a,w, h = frame_expanded.shape
            ret = np.empty((w, h, 3), dtype=np.uint8)
            ret[:, :, 2] =  ret[:, :, 1] =  ret[:, :, 0] =  frame_expanded
            frame_expanded=ret 
        """
        # Perform the actual detection by running the model with the image as input
        (detection_result) = sess.run(
            [detection],
            feed_dict={image_tensor: frame_expanded})   #執行 (輸出,image_tensor)  

        highest_probability_index = np.argmax(predictions)
        print('Classified as: ' + labels[highest_probability_index])
        #print(detection_result)
        cv2.imshow('frame',frame)
        '''
        # Draw the results of the detection (aka 'visulaize the results')
        vis_util.visualize_boxes_and_labels_on_image_array(
            frame,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            category_index,
            use_normalized_coordinates=True,
            line_thickness=8,
            min_score_thresh=0.3)

        #print(np.squeeze(boxes)[:5])
        #print((boxes[0][:10]))
        # print(np.squeeze(classes))
        # print(np.squeeze(scores))
        # print(category_index)

        cv2.putText(frame,"FPS: {0:.2f}".format(frame_rate_calc),(30,50),font,1,(255,255,0),2,cv2.LINE_AA)
        
            for i in range(10): 
            if boxes[0][i][1]<0.5 and boxes[0][i][0]>0.5 and boxes[0][i][2]>0.5 and boxes[0][i][3]<0.5 :
                #cv2.rectangle(frame, (0,0.5), (0.5,1), (0,0,255), 2)
                hei,wid,cha=frame.shape # 讀取尺寸和 channel數量
                cv2.rectangle(frame,(0,int(hei/2)),(int(wid/2),hei),(0,0,255),2)
        # All the results have been drawn on the frame, so it's time to display it.


        cv2.imshow('Object detector', frame)
        '''
        t2 = cv2.getTickCount()
        time1 = (t2-t1)/freq
        frame_rate_calc = 1/time1

        # Press 'q' to quit
        if cv2.waitKey(1) == ord('q'):
            break

    camera.release()
cv2.destroyAllWindows()