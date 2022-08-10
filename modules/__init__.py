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