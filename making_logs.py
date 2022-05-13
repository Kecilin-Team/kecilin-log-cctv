import os
import cv2
import time
import logging
import argparse
import pandas as pd
import numpy as np
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import tzlocal

def send_notif(message):
	url = F'https://api.telegram.org/bot2027464790:AAE4gstG6ZqmBZCR2xnPre6wFczRpiV4GsQ/sendMessage?chat_id=-526300571&text={message}'
	requests.get(url)

parser = argparse.ArgumentParser()
parser.add_argument('--force-restart', '-fr', default=('0',), type=str, nargs='+', help='set id of force restart')
parser.add_argument('-ifr', '--interval-fr', default=30, type=int, help='set interval of force restart')
parser.add_argument('-fnl', '--fn-log', default='logs/kecilin.log', type=str, help='set file name of log')
parser.add_argument('-sc', '--skip-cctv', default=False, action='store_true', help='hide confidences')
# parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')

opt = parser.parse_args()
print(opt)

logging.getLogger('apscheduler.executors.default').propagate = False
logging.getLogger('apscheduler.scheduler').propagate = False
logging.basicConfig(filename=opt.fn_log, level=logging.DEBUG)
logging.info('Kecilin logs is started')

if opt.interval_fr > 0:
	print('Force Restart Active')
	args = ' '.join(list(opt.force_restart))
	sched = BackgroundScheduler(daemon=True, timezone=str(tzlocal.get_localzone()))
	# sched = BlockingScheduler()
	# @sched.scheduled_job('interval', id='job_force_restart', seconds=opt.interval_fr)
	@sched.scheduled_job('interval', id='job_force_restart', minutes=opt.interval_fr)
	def force_restart_service():
		cmd = F"pm2 restart {args}" 
		os.system(cmd)

	sched.start()
else:
	print('Force Restart is not Active')

	
if not opt.skip_cctv:
	services = pd.read_csv('templates/services_list.csv', delimiter=',', header=0)
	services = np.array(services)	

while True:
	if opt.skip_cctv:
		print('Skipping CCTV')
	else:
		print('Log CCTV is running')
		for service in services:
			cap = cv2.VideoCapture(service[2])
			time.sleep(30)
			if not cap.isOpened():
				logging.error(F"{datetime.datetime.now()}, restarting {service[1]}")
				cmd = F"pm2 restart {service[1]}"
				os.system(cmd)
				send_notif(f'Kecilin-Compression-CCTV\nCompression not work normally\non this link {service[2]}\nTrying to restart service {service[1]}')
			cap = None

	time.sleep(30)


