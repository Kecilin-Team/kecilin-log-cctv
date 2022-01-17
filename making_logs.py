import os
import cv2
import time
import logging
import pandas as pd
import numpy as np
import datetime

services = pd.read_csv('templates/services_list.csv', delimiter=',', header=0)
services = np.array(services)

logging.basicConfig(filename='logs/kecilin.log', level=logging.DEBUG)
# logging.debug('This message should go to the log file')
# logging.info('So should this')
# logging.warning('And this, too')
# logging.error('And non-ASCII stuff, too, like Øresund and Malmö')

logging.info('Kecilin logs is started')


while True:
	for service in services:
		cap = cv2.VideoCapture(service[2])
		if not cap.isOpened():
			logging.error(F"{datetime.datetime.now()}, restarting {service[1]}")
			cmd = F"pm2 restart {service[1]}"
			print(cmd)


	time.sleep(60)


