# from PIL import Image
import cv2
# import argparse
# import time
import numpy as np
from sklearn.cluster import DBSCAN


def camera_is_open(img, thres):
	# resize
	basewidth = 64
	# start_time = time.time()
	# img = Image.open(img)
	wpercent = (basewidth/float(img.shape[0]))
	hsize = int((float(img.shape[1])*float(wpercent)))
	img = cv2.resize(img, (basewidth,hsize), interpolation = cv2.INTER_AREA)
	# cv2.imshow('frame', img)
	# cv2.waitKey(0)
	# img = img.resize((basewidth,hsize), Image.ANTIALIAS)

	# pixel_values = list(img)
	pixel_values =np.reshape(img.flatten(), (-1, 3))
	clustering = DBSCAN(eps=2, min_samples=2).fit(pixel_values)
	labels = len(set(clustering.labels_))
	print(labels)
	status = False if labels < thres else True
	return status



import os
import requests
from csv import writer


def append_list_as_row(file_name, list_of_elem):
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)

def post_data_api(url_api, form_data, form_files={}):
	
	files = {}
	for field in form_files:
		files[field]	 = open(form_files[field], 'rb') if form_files[field] else form_files[field]

	try:
		req = requests.post(url_api, data=form_data, files=files)
	except (requests.ConnectionError, requests.Timeout) as e:
		return 1000
	except Exception as e:
		print(e)
		return 400
	if req.status_code[0] == '2' :
		for field in form_files:
			if form_files[field] is not None:
				os.remove(form_files[field])

	return req.status_code